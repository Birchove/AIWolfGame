"""Integration smoke tests."""

import pytest
from schema.enums import DeathCause, Phase

from aiwerewolf.engine import eliminate_player, next_phase
from aiwerewolf.integration.smoke import run_phase0_2_smoke
from tests.fixtures.scenarios import state_from_roles, standard_twelve_player_roles


def test_phase0_2_smoke_module() -> None:
    run_phase0_2_smoke(seeds=[0, 1, 2])


def test_day_pk_clears_is_first_day() -> None:
    state = state_from_roles(
        standard_twelve_player_roles(),
        phase=Phase.DAY_PK,
        round_number=1,
        is_first_day=True,
    )
    nxt = next_phase(state)
    assert nxt.phase == Phase.NIGHT_WOLF
    assert nxt.is_first_day is False
    assert nxt.round_number == 2


def test_eliminate_soul_idiot_by_wolf_allowed() -> None:
    state = state_from_roles(standard_twelve_player_roles(), soul={8})
    state = eliminate_player(state, 8, cause=DeathCause.WOLF_KILL)
    assert not state.player(8).alive


def test_eliminate_soul_idiot_by_poison_rejected() -> None:
    state = state_from_roles(standard_twelve_player_roles(), soul={8})
    with pytest.raises(ValueError, match="poison"):
        eliminate_player(state, 8, cause=DeathCause.POISON)


def test_check_max_rounds_triggers() -> None:
    from aiwerewolf.engine import check_max_rounds

    state = state_from_roles(standard_twelve_player_roles(), round_number=30)
    result = check_max_rounds(state, 30)
    assert result is not None
    assert result.reason.value == "max_rounds_draw"
