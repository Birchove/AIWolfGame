"""Replay visibility filter tests."""

from schema.events import GameEvent

from aiwerewolf.logging.log import EventLog
from aiwerewolf.logging.replay import replay_events


def _event(seq: int, visibility: str, type: str = "x") -> GameEvent:
    return GameEvent(
        seq=seq,
        timestamp="2025-01-01T00:00:00+00:00",
        game_id="g1",
        visibility=visibility,
        type=type,
        payload={},
    )


def test_public_mode_strips_private_and_god() -> None:
    log = EventLog(
        "g1",
        [
            _event(1, "public", "phase_change"),
            _event(2, "god_only", "game_start"),
            _event(3, "private:3", "agent_turn"),
        ],
    )
    public = list(replay_events(log, mode="public"))
    assert len(public) == 1
    assert public[0].type == "phase_change"


def test_private_player_filter() -> None:
    log = EventLog(
        "g1",
        [
            _event(1, "private:3", "agent_turn"),
            _event(2, "private:5", "agent_turn"),
            _event(3, "public", "speech"),
        ],
    )
    p3 = list(replay_events(log, mode="private:3"))
    assert len(p3) == 2
    assert all(
        e.visibility == "public" or e.visibility == "private:3" for e in p3
    )


def test_god_mode_includes_all() -> None:
    log = EventLog(
        "g1",
        [
            _event(1, "public"),
            _event(2, "god_only"),
            _event(3, "private:1"),
        ],
    )
    assert len(list(replay_events(log, mode="god"))) == 3
