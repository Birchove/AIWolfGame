"""Replay and visibility filtering."""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

from schema.events import GameEvent

from aiwerewolf.logging.log import EventLog
from aiwerewolf.logging.storage import load_event_log


def visibility_matches(visibility: str, mode: str) -> bool:
    if mode == "god":
        return True
    if mode.startswith("private:"):
        if visibility == "public":
            return True
        if visibility == "god_only":
            return False
        if visibility.startswith("private:"):
            target = int(mode.split(":", 1)[1])
            owner = int(visibility.split(":", 1)[1])
            return target == owner
        return False
    if visibility == "public":
        return mode == "public"
    return False


def replay_events(
    log: EventLog,
    *,
    mode: str = "public",
) -> Iterator[GameEvent]:
    for event in log.events:
        if visibility_matches(event.visibility, mode):
            yield event


def public_timeline(log: EventLog) -> list[GameEvent]:
    return list(replay_events(log, mode="public"))


def load_and_replay(path: Path, *, mode: str = "public") -> list[GameEvent]:
    log = load_event_log(path)
    return list(replay_events(log, mode=mode))
