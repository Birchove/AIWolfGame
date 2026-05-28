"""Win condition tests."""

from schema.enums import Camp, Role, WinReason

from aiwerewolf.engine import check_win
from tests.fixtures.scenarios import state_from_roles, standard_twelve_player_roles


def test_good_wins_when_all_wolves_dead() -> None:
    roles = standard_twelve_player_roles()
    alive = {i for i in range(1, 13) if roles[i] != Role.WOLF}
    state = state_from_roles(roles, alive=alive)
    result = check_win(state)
    assert result is not None
    assert result.winner == Camp.GOOD
    assert result.reason == WinReason.WOLVES_ELIMINATED


def test_wolf_wins_tu_bian_gods() -> None:
    roles = standard_twelve_player_roles()
    alive = {i for i in range(1, 13) if roles[i] == Role.WOLF or roles[i] == Role.VILLAGER}
    state = state_from_roles(roles, alive=alive)
    result = check_win(state)
    assert result is not None
    assert result.winner == Camp.WOLF
    assert result.reason == WinReason.TU_BIAN_GODS


def test_wolf_wins_tu_bian_villagers() -> None:
    roles = standard_twelve_player_roles()
    alive = {i for i in range(1, 13) if roles[i] != Role.VILLAGER}
    state = state_from_roles(roles, alive=alive)
    result = check_win(state)
    assert result is not None
    assert result.winner == Camp.WOLF
    assert result.reason == WinReason.TU_BIAN_VILLAGERS


def test_no_winner_mid_game() -> None:
    state = state_from_roles(standard_twelve_player_roles())
    assert check_win(state) is None


def test_soul_idiot_prevents_tu_bian_gods() -> None:
    roles = standard_twelve_player_roles()
    alive = {1, 2, 3, 4, 8, 9, 10, 11, 12}
    state = state_from_roles(roles, alive=alive, soul={8})
    assert check_win(state) is None
