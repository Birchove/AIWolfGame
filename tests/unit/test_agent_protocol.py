"""Agent protocol and dispatch tests."""

import pytest
from schema.enums import Phase, Role

from aiwerewolf.engine import create_game, next_phase
from aiwerewolf.protocol import Visibility, apply_action, validate_phase_action
from aiwerewolf.protocol.views import PlayerView
from schema.agent import (
    AgentTurnOutput,
    PassAction,
    SeerCheckAction,
    VoteAction,
    WolfKillAction,
)
from tests.fixtures.pass_agent import PassAgent, pass_agents
from tests.fixtures.scenarios import state_from_roles, standard_twelve_player_roles


def _view(*, player_id: int = 1, **kwargs) -> PlayerView:
    state = state_from_roles(standard_twelve_player_roles(), **kwargs)
    return Visibility.for_player(state, player_id)


def test_agent_turn_output_schema_roundtrip() -> None:
    out = AgentTurnOutput(
        model="test",
        player_id=1,
        role="wolf",
        speech="hi",
        demeanor="calm",
        action=WolfKillAction(target_id=5),
    )
    data = out.model_dump()
    restored = AgentTurnOutput.model_validate(data)
    assert restored.action.type == "wolf_kill"


def test_pass_agent_returns_pass() -> None:
    agent = PassAgent(1)
    view = _view(phase=Phase.NIGHT_WOLF, player_id=1)
    out = agent.act(view)
    assert isinstance(out.action, PassAction)
    assert out.model == "PassAgent"


def test_pass_agents_dict_has_twelve() -> None:
    agents = pass_agents()
    assert len(agents) == 12
    assert all(isinstance(a, PassAgent) for a in agents.values())


def test_dispatcher_rejects_wrong_phase_action() -> None:
    ok, _ = validate_phase_action(Phase.DAY_VOTE, Role.SEER, SeerCheckAction(target_id=1))
    assert not ok
    ok2, _ = validate_phase_action(Phase.DAY_VOTE, Role.VILLAGER, VoteAction(target_id=1))
    assert ok2


def test_apply_action_wolf_kill_updates_state() -> None:
    state = state_from_roles(standard_twelve_player_roles(), phase=Phase.NIGHT_WOLF)
    out = AgentTurnOutput(
        model="t",
        player_id=1,
        role="wolf",
        action=WolfKillAction(target_id=9),
    )
    new_state = apply_action(state, out)
    assert new_state.wolf_kill_target == 9


def test_full_night_pass_pipeline_no_crash() -> None:
    state = create_game(seed=0)
    state = next_phase(state)
    agent_by_id = pass_agents()

    for phase in (
        Phase.NIGHT_WOLF,
        Phase.NIGHT_WITCH,
        Phase.NIGHT_SEER,
        Phase.NIGHT_HUNTER,
        Phase.NIGHT_IDIOT,
    ):
        state = state.with_phase(phase)
        for p in state.players:
            if not p.alive:
                continue
            view = Visibility.for_player(state, p.player_id)
            out = agent_by_id[p.player_id].act(view)
            try:
                state = apply_action(state, out)
            except ValueError:
                pass
    assert state.round_number >= 1
