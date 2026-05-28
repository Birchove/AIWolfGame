"""FastAPI routes."""

from __future__ import annotations

import uuid
from pathlib import Path
from typing import Literal

from fastapi import APIRouter, BackgroundTasks, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel

from aiwerewolf.api.registry import GameRegistry, GameStatus
from aiwerewolf.api.runner import run_game_in_background
from aiwerewolf.logging.replay import replay_events, visibility_matches
from schema.config import AppConfig


class CreateGameRequest(BaseModel):
    seed: int = 0


class CreateGameResponse(BaseModel):
    game_id: str


def create_router(
    registry: GameRegistry,
    cfg: AppConfig,
    repo_root: Path,
) -> APIRouter:
    router = APIRouter()

    @router.get("/health")
    async def health() -> dict:
        llm_ready = cfg.llm_ready()
        agents_ok = True
        agents_error = ""
        if llm_ready:
            try:
                import openai  # noqa: F401
                import langgraph  # noqa: F401
            except ImportError as exc:
                agents_ok = False
                agents_error = str(exc)
        return {
            "status": "ok",
            "llm_ready": llm_ready and agents_ok,
            "llm_configured": llm_ready,
            "agents_installed": agents_ok,
            "agents_error": agents_error,
            "provider": cfg.llm.provider,
            "model": cfg.llm.model,
            "base_url": cfg.llm.base_url or None,
        }

    @router.post("/games", response_model=CreateGameResponse)
    async def create_game(
        body: CreateGameRequest,
        background_tasks: BackgroundTasks,
    ) -> CreateGameResponse:
        if not cfg.llm_ready():
            raise HTTPException(
                status_code=400,
                detail="LLM api_key not configured in Config/secrets.yaml",
            )
        try:
            import openai  # noqa: F401
            import langgraph  # noqa: F401
        except ImportError as exc:
            raise HTTPException(
                status_code=400,
                detail=f"LLM dependencies missing — pip install -e '.[spectator]': {exc}",
            ) from exc
        game_id = str(uuid.uuid4())
        background_tasks.add_task(
            run_game_in_background,
            registry=registry,
            cfg=cfg,
            repo_root=repo_root,
            game_id=game_id,
            seed=body.seed,
        )
        return CreateGameResponse(game_id=game_id)

    @router.get("/games/{game_id}/events")
    async def get_events(
        game_id: str,
        visibility: Literal["public", "god"] = "public",
    ) -> list[dict]:
        session = await registry.get(game_id)
        if session is None:
            raise HTTPException(status_code=404, detail="game not found")
        events = list(replay_events(session.event_log, mode=visibility))
        return [e.model_dump(mode="json") for e in events]

    @router.get("/games/{game_id}")
    async def get_game(game_id: str) -> dict:
        session = await registry.get(game_id)
        if session is None:
            raise HTTPException(status_code=404, detail="game not found")
        payload = {
            "game_id": game_id,
            "status": session.status.value,
            "event_count": len(session.event_log),
        }
        if session.result is not None:
            payload["winner"] = (
                session.result.winner.value if session.result.winner else None
            )
        if session.error:
            payload["error"] = session.error
        return payload

    @router.websocket("/ws/games/{game_id}")
    async def ws_game(websocket: WebSocket, game_id: str) -> None:
        view = websocket.query_params.get("view", "public")
        if view not in {"public", "god"}:
            await websocket.close(code=4400, reason="view must be public or god")
            return
        session = await registry.get(game_id)
        if session is None:
            await websocket.close(code=4404)
            return
        await websocket.accept()
        queue = registry.subscribe(session)
        try:
            for event in replay_events(session.event_log, mode=view):
                await websocket.send_json(event.model_dump(mode="json"))
            while session.status == GameStatus.RUNNING:
                event = await queue.get()
                if event is None:
                    break
                if visibility_matches(event.visibility, view):
                    await websocket.send_json(event.model_dump(mode="json"))
        except WebSocketDisconnect:
            pass
        finally:
            if queue in session.subscribers:
                session.subscribers.remove(queue)

    return router
