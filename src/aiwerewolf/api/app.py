"""FastAPI application."""

from __future__ import annotations

import logging
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from aiwerewolf.api.registry import GameRegistry
from aiwerewolf.api.routes import create_router
from schema.config import load_app_config

logger = logging.getLogger(__name__)


def create_app(
    *,
    config_dir: Path | None = None,
    repo_root: Path | None = None,
    serve_frontend: bool = True,
) -> FastAPI:
    root = repo_root or Path(__file__).resolve().parents[3]
    cfg_dir = config_dir or root / "Config"
    cfg = load_app_config(cfg_dir, use_secrets=True)
    registry = GameRegistry()
    app = FastAPI(title="AI Werewolf", version="0.1.0")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:5173",
            "http://127.0.0.1:5173",
            "http://localhost:8000",
            "http://127.0.0.1:8000",
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(create_router(registry, cfg, root))
    app.state.registry = registry
    app.state.config = cfg
    app.state.repo_root = root

    if serve_frontend:
        frontend_dist = root / "frontend" / "dist"
        if frontend_dist.is_dir():
            app.mount(
                "/",
                StaticFiles(directory=str(frontend_dist), html=True),
                name="frontend",
            )
            logger.info("Serving spectator UI from %s", frontend_dist)
        else:
            logger.warning(
                "frontend/dist not found — run: cd frontend && npm install && npm run build"
            )

    return app


app = create_app()
