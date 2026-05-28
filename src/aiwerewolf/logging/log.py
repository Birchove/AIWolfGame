"""Event log container."""

from __future__ import annotations

from schema.events import GameEvent


class EventLog:
    def __init__(self, game_id: str, events: list[GameEvent] | None = None) -> None:
        self.game_id = game_id
        self.events: list[GameEvent] = list(events or [])

    def __len__(self) -> int:
        return len(self.events)
