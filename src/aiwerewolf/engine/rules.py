"""Pure rule functions — win checks, phase transitions, state updates."""

from __future__ import annotations

from dataclasses import replace

from schema.enums import Camp, DeathCause, Phase, Role, WinReason

from aiwerewolf.engine.state import GameState, PlayerState, WinResult

GOD_ROLES = frozenset({Role.SEER, Role.WITCH, Role.HUNTER, Role.IDIOT})

# Linear phase order for Phase 1 (skills resolved in later phases)
NIGHT_PHASES: tuple[Phase, ...] = (
    Phase.NIGHT_WOLF,
    Phase.NIGHT_WITCH,
    Phase.NIGHT_SEER,
    Phase.NIGHT_HUNTER,
    Phase.NIGHT_IDIOT,
)

DAY_PHASES_FIRST: tuple[Phase, ...] = (
    Phase.DAY_SHERIFF,
    Phase.DAY_ANNOUNCE,
    Phase.DAY_SPEECH,
    Phase.DAY_VOTE,
)

DAY_PHASES_LATER: tuple[Phase, ...] = (
    Phase.DAY_ANNOUNCE,
    Phase.DAY_SPEECH,
    Phase.DAY_VOTE,
)


def role_camp(role: Role) -> Camp:
    return Camp.WOLF if role == Role.WOLF else Camp.GOOD


def check_win(state: GameState) -> WinResult | None:
    """Return win result if game should end, else None."""
    wolves = state.living_wolves()
    gods = state.living_gods()
    villagers = state.living_villagers()

    if len(wolves) == 0:
        return WinResult(Camp.GOOD, WinReason.WOLVES_ELIMINATED)

    if len(gods) == 0:
        return WinResult(Camp.WOLF, WinReason.TU_BIAN_GODS)

    if len(villagers) == 0:
        return WinResult(Camp.WOLF, WinReason.TU_BIAN_VILLAGERS)

    return None


def check_max_rounds(state: GameState, max_rounds: int) -> WinResult | None:
    if state.round_number >= max_rounds and state.phase != Phase.GAME_OVER:
        return WinResult(Camp.GOOD, WinReason.MAX_ROUNDS_DRAW)
    return None


def apply_win_if_any(state: GameState, *, max_rounds: int | None = None) -> GameState:
    result = check_win(state)
    if result is None and max_rounds is not None:
        result = check_max_rounds(state, max_rounds)
    if result is not None:
        return state.with_winner(result)
    return state


def eliminate_player(
    state: GameState,
    player_id: int,
    *,
    cause: DeathCause = DeathCause.OTHER,
) -> GameState:
    """Mark player dead; clear sheriff badge if needed.

    Soul-state idiot cannot be killed by poison (rules.md A3).
    Wolf kill / vote may still eliminate soul-state idiot (追刀).
    """
    target = state.player(player_id)
    if cause == DeathCause.POISON and target.in_soul_state:
        raise ValueError("cannot poison soul-state idiot")

    new_sheriff_id = state.sheriff_id
    new_players: list[PlayerState] = []
    for p in state.players:
        if p.player_id == player_id:
            new_players.append(
                replace(p, alive=False, is_sheriff=False, in_soul_state=False)
            )
            if new_sheriff_id == player_id:
                new_sheriff_id = None
        else:
            new_players.append(p)
    return replace(state, players=tuple(new_players), sheriff_id=new_sheriff_id)


def _day_phases(state: GameState) -> tuple[Phase, ...]:
    need_sheriff = (
        not state.sheriff_election_forbidden
        and state.sheriff_id is None
        and (state.is_first_day or state.sheriff_election_retry)
    )
    if need_sheriff:
        return DAY_PHASES_FIRST
    if state.is_first_day:
        return (Phase.DAY_ANNOUNCE, Phase.DAY_SPEECH, Phase.DAY_VOTE)
    return DAY_PHASES_LATER


def next_phase(state: GameState) -> GameState:
    """Advance to the next phase in the standard cycle."""
    if state.phase == Phase.GAME_OVER:
        return state

    if state.self_destruct_today:
        return replace(
            state,
            phase=Phase.NIGHT_WOLF,
            self_destruct_today=False,
            day_votes=(),
            pk_candidates=(),
        )

    if state.phase == Phase.SETUP:
        return state.with_phase(Phase.NIGHT_WOLF, round_number=1)

    if state.phase in NIGHT_PHASES:
        idx = NIGHT_PHASES.index(state.phase)
        if idx + 1 < len(NIGHT_PHASES):
            return state.with_phase(NIGHT_PHASES[idx + 1])
        day = _day_phases(state)
        return state.with_phase(day[0])

    day = _day_phases(state)
    if state.phase in day:
        idx = day.index(state.phase)
        if idx + 1 < len(day):
            return state.with_phase(day[idx + 1])
        next_round = state.round_number + 1
        return state.with_phase(
            Phase.NIGHT_WOLF,
            round_number=next_round,
            is_first_day=False,
        )

    if state.phase == Phase.DAY_PK:
        return state.with_phase(
            Phase.NIGHT_WOLF,
            round_number=state.round_number + 1,
            is_first_day=False,
        )

    day = _day_phases(state)
    if state.phase == Phase.DAY_SHERIFF and state.phase not in day:
        return state.with_phase(day[0])

    raise ValueError(f"unsupported phase transition from {state.phase}")


def validate_phase_advance(state: GameState) -> tuple[bool, str]:
    if state.phase == Phase.GAME_OVER:
        return False, "game already over"
    if check_win(state) is not None:
        return False, "win condition already met"
    return True, ""
