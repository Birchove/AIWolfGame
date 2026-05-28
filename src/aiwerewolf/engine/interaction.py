"""Who may act or be targeted — dead players excluded except rules.md exceptions."""

from __future__ import annotations

from schema.enums import DeathCause, Phase, Role

from aiwerewolf.engine.state import GameState


def death_cause_for(state: GameState, player_id: int) -> DeathCause | None:
    for pid, cause, _rnd in state.death_records:
        if pid == player_id:
            return cause
    return None


def death_round_for(state: GameState, player_id: int) -> int | None:
    for pid, _cause, rnd in state.death_records:
        if pid == player_id:
            return rnd
    return None


def has_last_words(state: GameState, player_id: int) -> bool:
    """rules.md — 首夜夜死有遗言；白天出局有遗言。"""
    player = state.player(player_id)
    if player.alive:
        return False
    cause = death_cause_for(state, player_id)
    if cause == DeathCause.VOTE:
        return True
    if cause in {DeathCause.WOLF_KILL, DeathCause.POISON, DeathCause.OTHER}:
        return death_round_for(state, player_id) == 1
    if cause == DeathCause.HUNTER_SHOOT:
        return True
    return False


def can_vote_target(state: GameState, target_id: int) -> bool:
    target = state.player(target_id)
    if not target.alive:
        return False
    if target.in_soul_state:
        return False
    return True


def can_receive_sheriff_badge(state: GameState, player_id: int) -> bool:
    player = state.player(player_id)
    return player.alive and not player.in_soul_state


def may_act_in_phase(state: GameState, player_id: int, phase: Phase) -> bool:
    player = state.player(player_id)
    if player_id == state.sheriff_badge_pending_from:
        return phase in {Phase.DAY_ANNOUNCE, Phase.DAY_SPEECH}
    if player.alive:
        if player.in_soul_state:
            return phase in {Phase.DAY_ANNOUNCE, Phase.DAY_SPEECH, Phase.DAY_PK}
        return True
    if phase == Phase.DAY_ANNOUNCE and has_last_words(state, player_id):
        return True
    return False
