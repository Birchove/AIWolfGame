"""Recorder unit tests."""

from schema.enums import Phase, Role

from aiwerewolf.logging.recorder import Recorder
from tests.fixtures.scenarios import standard_twelve_player_roles, state_from_roles


def test_seq_monotonic() -> None:
    rec = Recorder(game_id="test")
    state = state_from_roles(
        standard_twelve_player_roles(), phase=Phase.DAY_SPEECH
    )
    rec.record_phase_change(state)
    rec.record_phase_change(state)
    seqs = [e.seq for e in rec.event_log.events]
    assert seqs == [1, 2]


def test_game_start_is_god_only() -> None:
    rec = Recorder(game_id="test")
    state = state_from_roles(
        standard_twelve_player_roles(), phase=Phase.NIGHT_WOLF
    )
    rec.record_game_start(state, seed=42)
    start = rec.event_log.events[0]
    assert start.type == "game_start"
    assert start.visibility == "god_only"
    assert "roles" in start.payload


def test_jsonl_file_god_only() -> None:
    import tempfile
    from pathlib import Path

    from schema.agent import AgentTurnOutput, SpeechAction

    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "game.jsonl"
        rec = Recorder(game_id="test", output_path=path)
        state = state_from_roles(
            standard_twelve_player_roles(), phase=Phase.DAY_SPEECH
        )
        rec.record_phase_change(state)
        output = AgentTurnOutput(
            model="m",
            player_id=1,
            role="wolf",
            speech="hello",
            demeanor="calm",
            demeanor_emojis=["😐"],
            action=SpeechAction(speech="hello"),
        )
        rec.record_agent_turn(state, output)
        rec.flush()
        lines = path.read_text(encoding="utf-8").strip().splitlines()
        assert lines
        for line in lines:
            import json

            data = json.loads(line)
            assert data["visibility"] == "god_only"


def test_sheriff_proclaimed_god_and_public() -> None:
    rec = Recorder(game_id="test")
    state = state_from_roles(standard_twelve_player_roles())
    from aiwerewolf.engine.day import _assign_sheriff

    state = _assign_sheriff(state, 5)
    rec.record_sheriff_elected(state)
    types = {e.type: e.visibility for e in rec.event_log.events}
    assert types["sheriff_proclaimed"] == "god_only"
    assert types["sheriff_elected"] == "public"


def test_public_agent_turn_has_no_role() -> None:
    from schema.agent import AgentTurnOutput, SpeechAction

    rec = Recorder(game_id="test")
    state = state_from_roles(
        standard_twelve_player_roles(), phase=Phase.DAY_SPEECH
    )
    output = AgentTurnOutput(
        model="m",
        player_id=1,
        role="wolf",
        speech="hello",
        demeanor="calm",
        demeanor_emojis=["😐"],
        action=SpeechAction(speech="hello"),
    )
    rec.record_agent_turn(state, output)
    public = [e for e in rec.event_log.events if e.visibility == "public"]
    private = [e for e in rec.event_log.events if e.visibility.startswith("private")]
    assert public
    assert "role" not in public[0].payload
    assert private[0].payload["role"] == "wolf"
