"""Visibility leak-prevention tests (Claude Code Phase 2 checklist)."""

from dataclasses import FrozenInstanceError

import pytest
from schema.enums import Phase, Role

from aiwerewolf.engine.state import GameState, SeerCheckResult
from aiwerewolf.protocol import PlayerView, Visibility
from tests.fixtures.scenarios import state_from_roles, standard_twelve_player_roles


def _view(pid: int, **kwargs) -> PlayerView:
    state = state_from_roles(standard_twelve_player_roles(), **kwargs)
    return Visibility.for_player(state, pid)


# --- mandatory negative tests ---


def test_wolf_sees_teammates() -> None:
    v = _view(1)
    assert v.wolf_teammates == (2, 3, 4)


def test_villager_has_no_wolf_teammates() -> None:
    v = _view(9)
    assert v.wolf_teammates == ()


def test_god_has_no_wolf_teammates() -> None:
    for pid in (5, 6, 7, 8):
        assert _view(pid).wolf_teammates == ()


def test_non_seer_has_no_checks() -> None:
    checks = (SeerCheckResult(9, False, 1),)
    for pid in range(1, 13):
        if pid == 5:
            continue
        v = _view(pid, seer_checks=checks)
        assert v.seer_checks == ()


def test_non_witch_has_no_night_death() -> None:
    v = _view(9, wolf_kill_target=6, phase=Phase.NIGHT_WITCH)
    assert v.witch_night_death is None


def test_non_hunter_cannot_shoot() -> None:
    v = _view(5, hunter_can_shoot=True)
    assert v.hunter_can_shoot is False


def test_no_player_view_exposes_other_roles() -> None:
    roles = standard_twelve_player_roles()
    state = state_from_roles(roles)
    forbidden = {"players", "other_roles", "all_roles", "game_state"}
    for pid in range(1, 13):
        view = Visibility.for_player(state, pid)
        for name in forbidden:
            assert not hasattr(view, name)
        assert view.own_role == roles[pid]


def test_no_gamestate_reference_on_view() -> None:
    view = _view(1)
    assert not isinstance(view, GameState)
    assert not hasattr(view, "players")


def test_dead_player_view_is_public_only() -> None:
    roles = standard_twelve_player_roles()
    alive = {i for i in range(1, 13) if i != 1}
    v = Visibility.for_player(
        state_from_roles(roles, alive=alive, wolf_kill_target=6, phase=Phase.NIGHT_WITCH,
                         seer_checks=(SeerCheckResult(9, False, 1),), hunter_can_shoot=True),
        1,
    )
    assert not v.is_alive
    assert v.wolf_teammates == ()
    assert v.seer_checks == ()
    assert v.witch_night_death is None
    assert v.hunter_can_shoot is False


# --- positive correctness ---


def test_view_has_correct_own_role() -> None:
    roles = standard_twelve_player_roles()
    state = state_from_roles(roles)
    for pid, role in roles.items():
        assert Visibility.for_player(state, pid).own_role == role


def test_view_living_dead_partition() -> None:
    roles = standard_twelve_player_roles()
    alive = {1, 2, 5, 9}
    v = _view(5, alive=alive)
    assert set(v.living_player_ids) == alive
    assert set(v.dead_player_ids) == {3, 4, 6, 7, 8, 10, 11, 12}
    assert set(v.living_player_ids).isdisjoint(v.dead_player_ids)


def test_seer_checks_accumulate() -> None:
    checks = (
        SeerCheckResult(9, False, 1),
        SeerCheckResult(2, True, 2),
    )
    v = _view(5, seer_checks=checks)
    assert len(v.seer_checks) == 2
    assert v.seer_checks[1].is_wolf is True


def test_witch_sees_night_death_only_in_witch_phase() -> None:
    during = _view(6, wolf_kill_target=9, phase=Phase.NIGHT_WITCH)
    assert during.witch_night_death == 9
    after = _view(6, wolf_kill_target=9, phase=Phase.NIGHT_SEER)
    assert after.witch_night_death is None


def test_sheriff_visible_to_all() -> None:
    state = state_from_roles(standard_twelve_player_roles(), sheriff_id=5)
    for pid in range(1, 13):
        assert Visibility.for_player(state, pid).sheriff_id == 5


# --- immutability ---


def test_player_view_is_frozen() -> None:
    v = _view(1)
    with pytest.raises(FrozenInstanceError):
        v.player_id = 2  # type: ignore[misc]


def test_player_view_collections_are_tuples() -> None:
    v = _view(1, seer_checks=(SeerCheckResult(9, False, 1),))
    assert isinstance(v.wolf_teammates, tuple)
    assert isinstance(v.seer_checks, tuple)
    assert isinstance(v.public_events, tuple)


def test_for_player_returns_new_object_per_call() -> None:
    state = state_from_roles(standard_twelve_player_roles())
    assert Visibility.for_player(state, 1) is not Visibility.for_player(state, 1)


# --- edge cases ---


def test_invalid_player_id_raises() -> None:
    state = state_from_roles(standard_twelve_player_roles())
    with pytest.raises(KeyError):
        Visibility.for_player(state, 99)


def test_game_over_view_obey_visibility() -> None:
    from schema.enums import Camp, WinReason
    from dataclasses import replace

    state = state_from_roles(standard_twelve_player_roles(), phase=Phase.GAME_OVER)
    state = replace(
        state,
        winner=Camp.GOOD,
        win_reason=WinReason.WOLVES_ELIMINATED,
    )
    v = Visibility.for_player(state, 9)
    assert v.wolf_teammates == ()
    assert v.seer_checks == ()


def test_soul_state_idiot_visibility() -> None:
    v = _view(8, soul={8})
    assert v.is_alive
    assert v.in_soul_state
    assert v.own_role == Role.IDIOT
