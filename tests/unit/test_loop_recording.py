"""GameLoop + Recorder integration."""

from schema.enums import Phase

from aiwerewolf.engine.loop import GameLoop
from aiwerewolf.logging.recorder import Recorder
from aiwerewolf.logging.replay import replay_events
from tests.fixtures.pass_agent import pass_agents


def test_loop_recording_produces_game_over() -> None:
    rec = Recorder(game_id="loop-test")
    loop = GameLoop(pass_agents(), max_rounds=20, recorder=rec)
    result = loop.run(seed=7)
    types = [e.type for e in rec.event_log.events]
    assert "game_start" in types
    assert "game_over" in types
    assert result.winner is not None


def test_public_replay_has_no_roles() -> None:
    rec = Recorder(game_id="loop-test")
    loop = GameLoop(pass_agents(), max_rounds=15, recorder=rec)
    loop.run(seed=8)
    public = list(replay_events(rec.event_log, mode="public"))
    text = str([e.model_dump() for e in public])
    assert "game_start" not in [e.type for e in public]
    assert '"roles"' not in text


def test_jsonl_roundtrip(tmp_path) -> None:
    from aiwerewolf.logging.storage import load_event_log

    path = tmp_path / "game.jsonl"
    rec = Recorder(game_id="persist", output_path=path)
    loop = GameLoop(pass_agents(), max_rounds=10, recorder=rec)
    loop.run(seed=9)
    loaded = load_event_log(path)
    god_events = [e for e in rec.event_log.events if e.visibility == "god_only"]
    assert len(loaded.events) == len(god_events)
    assert all(e.visibility == "god_only" for e in loaded.events)
    assert any(e.type == "game_over" for e in rec.event_log.events)
    assert loaded.events[-1].type == "player_dossier"
