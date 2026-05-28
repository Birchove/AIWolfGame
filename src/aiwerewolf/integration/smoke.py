"""Cross-module integration smoke (Phase 0-2)."""

from __future__ import annotations

from schema.enums import Phase

from aiwerewolf.engine import (
    apply_win_if_any,
    check_max_rounds,
    create_game,
    eliminate_player,
    next_phase,
    validate_phase_advance,
)
from aiwerewolf.protocol import Visibility
from schema.enums import DeathCause


def assert_visibility_invariants(state, *, label: str = "") -> None:
    """Every player view must not leak other roles."""
    for p in state.players:
        view = Visibility.for_player(state, p.player_id)
        assert view.own_role == p.role, f"{label} pid={p.player_id}"
        assert not hasattr(view, "players")
        if not p.alive:
            assert view.wolf_teammates == ()
            assert view.seer_checks == ()


def run_phase0_2_smoke(*, seeds: range | list[int] | None = None) -> None:
    seeds = list(seeds or range(3))
    for seed in seeds:
        state = create_game(seed=seed)
        assert len(state.players) == 12
        assert_visibility_invariants(state, label=f"seed={seed} setup")

        phases = 0
        while state.phase != Phase.GAME_OVER and phases < 20:
            ok, _ = validate_phase_advance(state)
            if not ok:
                break
            state = next_phase(state)
            assert_visibility_invariants(state, label=f"seed={seed} phase={state.phase}")
            phases += 1

        state = apply_win_if_any(state)
        assert_visibility_invariants(state, label=f"seed={seed} end")

    # Win path — eliminate all wolves (roles shuffled by seed)
    state = create_game(seed=0)
    for p in state.players:
        if p.is_wolf():
            state = eliminate_player(state, p.player_id, cause=DeathCause.WOLF_KILL)
    state = apply_win_if_any(state)
    assert state.phase == Phase.GAME_OVER

    # Max rounds
    state = create_game(seed=1)
    state = state.with_phase(Phase.NIGHT_WOLF, round_number=30)
    assert check_max_rounds(state, 30) is not None
