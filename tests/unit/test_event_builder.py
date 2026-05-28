"""Event builder tests."""

from schema.agent import AgentTurnOutput, WolfKillAction
from schema.enums import Phase

from aiwerewolf.agents.llm.view_format import view_to_dict
from aiwerewolf.logging import builder
from aiwerewolf.protocol.views import PlayerView
from schema.enums import Role
from tests.fixtures.scenarios import standard_twelve_player_roles, state_from_roles


def _view(phase: Phase) -> PlayerView:
    return PlayerView(
        player_id=1,
        own_role=Role.WOLF,
        phase=phase,
        round_number=1,
        is_alive=True,
        is_sheriff=False,
        in_soul_state=False,
        living_player_ids=(1, 2, 3),
        dead_player_ids=(),
        sheriff_id=None,
        public_events=(),
    )


def test_night_agent_turn_public_is_none() -> None:
    output = AgentTurnOutput(
        model="m",
        player_id=1,
        role="wolf",
        speech="secret",
        demeanor="x",
        action=WolfKillAction(target_id=2),
    )
    state = state_from_roles(
        standard_twelve_player_roles(), phase=Phase.NIGHT_WOLF
    )
    assert builder.build_agent_turn_public(output, state) is None


def test_day_agent_turn_public_has_speech() -> None:
    output = AgentTurnOutput(
        model="m",
        player_id=1,
        role="wolf",
        speech="hi",
        demeanor="calm",
        demeanor_emojis=["😏", "🤔"],
        action=WolfKillAction(target_id=2),
    )
    state = state_from_roles(
        standard_twelve_player_roles(), phase=Phase.DAY_SPEECH
    )
    public = builder.build_agent_turn_public(output, state)
    assert public is not None
    assert public["speech"] == "hi"
    assert public["demeanor_emojis"] == ["😏", "🤔"]


def test_view_to_dict_no_game_state() -> None:
    data = view_to_dict(_view(Phase.DAY_VOTE))
    assert "GameState" not in str(data)
    assert "players" not in data
