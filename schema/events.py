"""Structured game events for logging / replay / API."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class GameEvent(BaseModel):
    """Flat append-only log entry — JSONL-friendly."""

    seq: int
    timestamp: str
    game_id: str
    visibility: str  # public | god_only | private:{player_id}
    type: str
    phase: str | None = None
    round: int | None = None
    player_id: int | None = None
    payload: dict[str, Any] = Field(default_factory=dict)


# Backward-compatible aliases (Phase 7 flat model supersedes nested public/private)
PublicEvent = GameEvent
PrivateEvent = GameEvent
