"""GameState and PlayerState tests."""

from dataclasses import FrozenInstanceError

import pytest
from schema.enums import Phase, Role

from aiwerewolf.engine import create_game, eliminate_player
from tests.fixtures.scenarios import state_from_roles, standard_twelve_player_roles


def test_create_game_has_twelve_players() -> None:
    state = create_game(seed=42)
    assert len(state.players) == 12
    assert state.phase == Phase.SETUP
    roles = [p.role for p in state.players]
    assert roles.count(Role.WOLF) == 4
    assert roles.count(Role.VILLAGER) == 4


def test_game_state_is_frozen() -> None:
    state = create_game(seed=1)
    with pytest.raises(FrozenInstanceError):
        state.phase = Phase.NIGHT_WOLF  # type: ignore[misc]


def test_living_players_excludes_dead() -> None:
    roles = standard_twelve_player_roles()
    state = state_from_roles(roles, alive=set(range(1, 12)))
    assert len(state.living_players()) == 11


def test_soul_state_idiot_counts_as_alive() -> None:
    roles = standard_twelve_player_roles()
    state = state_from_roles(roles, soul={8})
    idiot = state.player(8)
    assert idiot.in_soul_state
    assert idiot.counts_as_alive_for_win()


def test_eliminate_player_clears_sheriff() -> None:
    roles = standard_twelve_player_roles()
    state = state_from_roles(roles, sheriff_id=5)
    new_state = eliminate_player(state, 5)
    assert not new_state.player(5).alive
    assert new_state.sheriff_id is None
    assert new_state.sheriff_badge_pending_from == 5
