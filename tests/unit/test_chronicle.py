"""Chronicle formatter tests."""

from schema.agent import AgentTurnOutput, PassAction, SpeechAction
from schema.enums import Phase

from aiwerewolf.logging.chronicle import format_god_chronicle, write_god_chronicle
from aiwerewolf.logging.recorder import Recorder
from tests.fixtures.scenarios import standard_twelve_player_roles, state_from_roles


def test_chronicle_includes_reasoning_and_demeanor() -> None:
    rec = Recorder(game_id="chronicle-test")
    state = state_from_roles(
        standard_twelve_player_roles(), phase=Phase.DAY_SPEECH
    )
    rec.record_game_start(state, seed=1)
    output = AgentTurnOutput(
        model="test",
        player_id=3,
        role="villager",
        speech="我是好人",
        demeanor="环视全场",
        demeanor_emojis=["👀", "😐"],
        reasoning="P5 发言太划水，先记一笔",
        action=SpeechAction(speech="我是好人"),
    )
    rec.record_agent_turn(state, output)
    text = format_god_chronicle(rec.event_log)
    assert "心理:" in text
    assert "P5 发言太划水" in text
    assert "神态:" in text
    assert "环视全场" in text
    assert "发言:" in text


def test_write_chronicle_file(tmp_path) -> None:
    rec = Recorder(game_id="f", output_path=tmp_path / "game.jsonl")
    state = state_from_roles(
        standard_twelve_player_roles(), phase=Phase.DAY_SPEECH
    )
    rec.record_game_start(state, seed=0)
    rec.flush()
    chronicle = tmp_path / "game.chronicle.txt"
    assert chronicle.is_file()
    assert "开局" in chronicle.read_text(encoding="utf-8")
