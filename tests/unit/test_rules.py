"""Phase transition and rule helper tests."""

from schema.enums import Phase

from aiwerewolf.engine import (
    apply_win_if_any,
    create_game,
    eliminate_player,
    next_phase,
    role_camp,
    validate_phase_advance,
)
from schema.enums import Camp, Role

from tests.fixtures.scenarios import state_from_roles, standard_twelve_player_roles


def test_role_camp() -> None:
    assert role_camp(Role.WOLF) == Camp.WOLF
    assert role_camp(Role.SEER) == Camp.GOOD


def test_next_phase_setup_to_night_wolf() -> None:
    state = create_game(seed=0)
    nxt = next_phase(state)
    assert nxt.phase == Phase.NIGHT_WOLF
    assert nxt.round_number == 1


def test_full_day_night_cycle_first_day() -> None:
    state = create_game(seed=0)
    state = next_phase(state)
    expected = [
        Phase.NIGHT_WOLF,
        Phase.NIGHT_WITCH,
        Phase.NIGHT_SEER,
        Phase.NIGHT_HUNTER,
        Phase.NIGHT_IDIOT,
        Phase.DAY_SHERIFF,
        Phase.DAY_ANNOUNCE,
        Phase.DAY_SPEECH,
        Phase.DAY_VOTE,
        Phase.NIGHT_WOLF,
    ]
    phases = [state.phase]
    for _ in range(len(expected) - 1):
        state = next_phase(state)
        phases.append(state.phase)
    assert phases == expected
    assert state.is_first_day is False
    assert state.round_number == 2


def test_second_day_skips_sheriff_election() -> None:
    state = create_game(seed=0)
    for _ in range(10):
        state = next_phase(state)
    assert state.phase == Phase.NIGHT_WOLF
    assert state.round_number == 2
    state = next_phase(state)
    assert state.phase == Phase.NIGHT_WITCH
    state = next_phase(state)
    assert state.phase == Phase.NIGHT_SEER
    # After night, should go to DAY_ANNOUNCE (not DAY_SHERIFF)
    for _ in range(3):
        state = next_phase(state)
    assert state.phase == Phase.DAY_ANNOUNCE


def test_apply_win_sets_game_over() -> None:
    roles = standard_twelve_player_roles()
    state = state_from_roles(roles)
    for wid in (1, 2, 3, 4):
        state = eliminate_player(state, wid)
    final = apply_win_if_any(state)
    assert final.phase == Phase.GAME_OVER
    assert final.winner == Camp.GOOD


def test_validate_phase_advance_blocks_when_over() -> None:
    roles = standard_twelve_player_roles()
    state = state_from_roles(roles, phase=Phase.GAME_OVER)
    ok, msg = validate_phase_advance(state)
    assert not ok
    assert "over" in msg
