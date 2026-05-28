"""Speech log and transcript visibility."""

from schema.agent import AgentTurnOutput, PassAction
from schema.enums import Phase, Role

from aiwerewolf.engine.speech import append_speech, audience_for_phase
from aiwerewolf.engine.state import SpeechRecord
from aiwerewolf.protocol.visibility import Visibility
from tests.fixtures.scenarios import state_from_roles, standard_twelve_player_roles


def test_audience_for_day_and_wolf_night() -> None:
    assert audience_for_phase(Phase.DAY_SPEECH) == "public"
    assert audience_for_phase(Phase.NIGHT_WOLF) == "wolf_only"
    assert audience_for_phase(Phase.NIGHT_WITCH) is None


def test_append_speech_public_day() -> None:
    state = state_from_roles(standard_twelve_player_roles(), phase=Phase.DAY_SPEECH)
    output = AgentTurnOutput(
        model="test",
        player_id=9,
        role=Role.VILLAGER,
        speech="我站边5号",
        demeanor_emojis=["🤔"],
        action=PassAction(),
    )
    state = append_speech(state, output)
    assert len(state.speech_log) == 1
    rec = state.speech_log[0]
    assert rec.audience == "public"
    assert rec.speech == "我站边5号"
    assert rec.demeanor_emojis == ("🤔",)


def test_wolf_sees_team_speeches_not_public_only() -> None:
    roles = standard_twelve_player_roles()
    state = state_from_roles(roles, phase=Phase.NIGHT_WOLF)
    wolf_rec = SpeechRecord(
        player_id=1,
        round_number=1,
        phase=Phase.NIGHT_WOLF.value,
        speech="刀6",
        demeanor_emojis=("😏",),
        audience="wolf_only",
    )
    pub_rec = SpeechRecord(
        player_id=9,
        round_number=1,
        phase=Phase.DAY_SPEECH.value,
        speech="好人牌",
        demeanor_emojis=("😐",),
        audience="public",
    )
    state = state.with_speech(wolf_rec).with_speech(pub_rec)

    wolf_view = Visibility.for_player(state, 1)
    villager_view = Visibility.for_player(state, 9)

    assert len(wolf_view.public_speeches) == 1
    assert wolf_view.public_speeches[0].speech == "好人牌"
    assert len(wolf_view.wolf_team_speeches) == 1
    assert wolf_view.wolf_team_speeches[0].speech == "刀6"

    assert len(villager_view.public_speeches) == 1
    assert villager_view.wolf_team_speeches == ()


def test_format_player_view_includes_speech_transcript() -> None:
    from aiwerewolf.agents.llm.view_format import format_player_view

    state = state_from_roles(standard_twelve_player_roles(), phase=Phase.DAY_SPEECH)
    rec = SpeechRecord(
        player_id=5,
        round_number=1,
        phase=Phase.DAY_SPEECH.value,
        speech="我是预言家",
        demeanor_emojis=("😤",),
        audience="public",
    )
    state = state.with_speech(rec)
    view = Visibility.for_player(state, 9)
    text = format_player_view(view)
    assert "我是预言家" in text
    assert "demeanor_display" in text
    assert "😤" in text
