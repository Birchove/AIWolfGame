"""JSONL persistence for event logs."""

from __future__ import annotations

import json
from pathlib import Path

from schema.events import GameEvent

from aiwerewolf.logging.log import EventLog


def append_event(path: Path, event: GameEvent) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(event.model_dump_json() + "\n")


def write_event_log(path: Path, log: EventLog, *, god_only: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    events = log.events
    if god_only:
        events = [e for e in events if e.visibility == "god_only"]
    with path.open("w", encoding="utf-8") as f:
        for event in events:
            f.write(event.model_dump_json() + "\n")


def load_event_log(path: Path) -> EventLog:
    events: list[GameEvent] = []
    game_id = ""
    with path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            event = GameEvent.model_validate_json(line)
            if not game_id:
                game_id = event.game_id
            events.append(event)
    return EventLog(game_id or "unknown", events)
