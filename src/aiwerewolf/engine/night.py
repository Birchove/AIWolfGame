"""Night phase resolution — pure rules (rules.md order)."""

from __future__ import annotations

from dataclasses import replace

from schema.enums import DeathCause, Role

from aiwerewolf.engine.rules import apply_win_if_any, eliminate_player, role_camp
from aiwerewolf.engine.state import GameState, SeerCheckResult


def resolve_wolf_kill(state: GameState, target_id: int | None) -> GameState:
    """Record wolf kill target. None = empty kill (four wolves agree)."""
    if target_id is not None:
        target = state.player(target_id)
        if not target.alive:
            raise ValueError(f"wolf kill target {target_id} is not alive")
    return replace(state, wolf_kill_target=target_id)


def resolve_witch(
    state: GameState,
    *,
    use_antidote: bool = False,
    poison_target: int | None = None,
) -> GameState:
    """At most one bottle per night. Cannot self-save."""
    if use_antidote and poison_target is not None:
        raise ValueError("witch cannot use antidote and poison same night")
    if use_antidote and not state.witch_antidote_available:
        raise ValueError("witch antidote already used")
    if poison_target is not None and not state.witch_poison_available:
        raise ValueError("witch poison already used")

    new_state = state
    pending_deaths: list[tuple[int, DeathCause]] = []

    if use_antidote:
        if state.wolf_kill_target is None:
            raise ValueError("no wolf kill to save")
        witch = _find_role_player(state, Role.WITCH)
        if witch and state.wolf_kill_target == witch.player_id:
            raise ValueError("witch cannot self-save")
        new_state = replace(new_state, witch_antidote_available=False)

    if poison_target is not None:
        new_state = replace(new_state, witch_poison_available=False)
        poison_player = state.player(poison_target)
        if poison_player.alive:
            pending_deaths.append((poison_target, DeathCause.POISON))

    # Deaths from wolf kill unless saved (skip if already dead from prior round)
    if (
        state.wolf_kill_target is not None
        and not use_antidote
    ):
        target = state.player(state.wolf_kill_target)
        if target.alive:
            pending_deaths.append((state.wolf_kill_target, DeathCause.WOLF_KILL))

    for pid, cause in pending_deaths:
        new_state = eliminate_player(new_state, pid, cause=cause)

    return new_state


def resolve_seer_check(state: GameState, target_id: int) -> GameState:
    target = state.player(target_id)
    is_wolf = role_camp(target.role) == role_camp(Role.WOLF)
    check = SeerCheckResult(
        target_id=target_id,
        is_wolf=is_wolf,
        round_number=state.round_number,
    )
    return replace(state, seer_checks=state.seer_checks + (check,))


def check_hunter_status(state: GameState) -> GameState:
    """Set hunter_can_shoot if hunter was wolf-killed and not saved."""
    hunter = _find_role_player_any(state, Role.HUNTER)
    if hunter is None:
        return replace(state, hunter_can_shoot=False)
    was_wolf_target = state.wolf_kill_target == hunter.player_id
    hunter_dead = not hunter.alive
    can_shoot = was_wolf_target and hunter_dead
    return replace(state, hunter_can_shoot=can_shoot)


def _find_role_player_any(state: GameState, role: Role):
    for p in state.players:
        if p.role == role:
            return p
    return None


def confirm_idiot(state: GameState) -> GameState:
    """Idiot night wake — no state change in slice 1."""
    return state


def collect_death_announcements(state: GameState) -> GameState:
    dead_ids = tuple(
        sorted(p.player_id for p in state.players if not p.alive)
    )
    return replace(state, death_announcements=dead_ids)


def resolve_night(
    state: GameState,
    *,
    wolf_target: int | None,
    witch_antidote: bool = False,
    witch_poison: int | None = None,
    seer_target: int,
) -> GameState:
    """Full night pipeline: wolf → witch → seer → hunter → idiot → deaths → win."""
    s = resolve_wolf_kill(state, wolf_target)
    s = resolve_witch(s, use_antidote=witch_antidote, poison_target=witch_poison)
    s = resolve_seer_check(s, seer_target)
    s = check_hunter_status(s)
    s = confirm_idiot(s)
    s = collect_death_announcements(s)
    return apply_win_if_any(s)


def _find_role_player(state: GameState, role: Role):
    for p in state.players:
        if p.role == role and p.alive:
            return p
    return None
