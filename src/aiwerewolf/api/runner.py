"""Background game runner for API."""

from __future__ import annotations

import asyncio
from functools import partial

from schema.config import AppConfig

from aiwerewolf.agents.factory import build_agents
from aiwerewolf.api.registry import GameRegistry, GameSession
from aiwerewolf.engine.loop import GameLoop
from aiwerewolf.logging.recorder import Recorder
from schema.events import GameEvent


def _sync_push(loop: asyncio.AbstractEventLoop, registry: GameRegistry, game_id: str, event: GameEvent) -> None:
    asyncio.run_coroutine_threadsafe(registry.broadcast(game_id, event), loop)


async def run_game_in_background(
    *,
    registry: GameRegistry,
    cfg: AppConfig,
    repo_root,
    game_id: str,
    seed: int,
) -> None:
    loop = asyncio.get_running_loop()

    def on_event(event: GameEvent) -> None:
        _sync_push(loop, registry, game_id, event)

    log_dir = repo_root / cfg.logging.output_dir
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / f"{game_id}.jsonl"

    recorder = Recorder(
        game_id=game_id,
        on_event=on_event,
        output_path=log_path,
    )
    session = GameSession(game_id=game_id, recorder=recorder)
    await registry.create(session)

    agents = build_agents(cfg, repo_root=repo_root)
    game_loop = GameLoop(
        agents, max_rounds=cfg.game.max_rounds, recorder=recorder, cfg=cfg
    )

    try:
        result = await loop.run_in_executor(
            None, partial(game_loop.run, seed=seed)
        )
        await registry.mark_complete(game_id, result)
    except Exception as exc:
        await registry.mark_failed(game_id, str(exc))
    finally:
        await registry.close_subscribers(game_id)
