"""Night resolution tests (Phase 3 slice 1)."""

import pytest

from aiwerewolf.engine import (
    check_hunter_status,
    resolve_night,
    resolve_seer_check,
    resolve_witch,
    resolve_wolf_kill,
)
from schema.enums import Role
from tests.fixtures.scenarios import state_from_roles, standard_twelve_player_roles


def _state(**kwargs):
    return state_from_roles(standard_twelve_player_roles(), **kwargs)


def test_wolf_kill_sets_target() -> None:
    s = resolve_wolf_kill(_state(), 5)
    assert s.wolf_kill_target == 5


def test_wolf_empty_kill_allowed() -> None:
    s = resolve_wolf_kill(_state(), None)
    assert s.wolf_kill_target is None


def test_witch_antidote_saves_wolf_target() -> None:
    s = resolve_wolf_kill(_state(), 9)
    s = resolve_witch(s, use_antidote=True)
    assert s.player(9).alive
    assert s.witch_antidote_available is False


def test_witch_cannot_use_both_bottles_same_night() -> None:
    s = resolve_wolf_kill(_state(), 9)
    with pytest.raises(ValueError, match="cannot use antidote and poison"):
        resolve_witch(s, use_antidote=True, poison_target=10)


def test_witch_poison_kills_player() -> None:
    s = resolve_witch(_state(), poison_target=9)
    assert not s.player(9).alive
    assert s.witch_poison_available is False


def test_poison_cannot_kill_soul_state_idiot() -> None:
    s = _state(soul={8})
    with pytest.raises(ValueError, match="poison"):
        resolve_witch(s, poison_target=8)


def test_seer_check_records_correct_camp() -> None:
    s = resolve_seer_check(_state(), 1)
    assert s.seer_checks[-1].is_wolf is True
    s2 = resolve_seer_check(_state(), 9)
    assert s2.seer_checks[-1].is_wolf is False


def test_hunter_can_shoot_when_wolf_killed_not_saved() -> None:
    s = resolve_wolf_kill(_state(), 7)
    s = resolve_witch(s)
    s = check_hunter_status(s)
    assert s.hunter_can_shoot is True


def test_hunter_cannot_shoot_when_poisoned() -> None:
    s = resolve_witch(_state(), poison_target=7)
    s = check_hunter_status(s)
    assert s.hunter_can_shoot is False


def test_resolve_night_pipeline() -> None:
    s = resolve_night(
        _state(),
        wolf_target=9,
        witch_antidote=False,
        witch_poison=None,
        seer_target=1,
    )
    assert not s.player(9).alive
    assert len(s.seer_checks) == 1
    assert 9 in s.death_announcements
