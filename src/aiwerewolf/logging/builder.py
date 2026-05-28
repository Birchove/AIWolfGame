"""Build GameEvent payloads from engine state and agent output."""

from __future__ import annotations

from schema.agent import AgentTurnOutput
from schema.enums import Phase

from aiwerewolf.engine.state import GameState

_NIGHT_PHASES = frozenset(
    {
        Phase.NIGHT_WOLF,
        Phase.NIGHT_WITCH,
        Phase.NIGHT_SEER,
        Phase.NIGHT_HUNTER,
        Phase.NIGHT_IDIOT,
    }
)


def _emojis(output: AgentTurnOutput) -> list[str]:
    return list(output.demeanor_emojis or [])


def build_game_start_payload(state: GameState, *, seed: int | None) -> dict:
    return {
        "seed": seed,
        "roles": {p.player_id: p.role.value for p in state.players},
    }


def build_agent_turn_public(output: AgentTurnOutput, state: GameState) -> dict | None:
    if state.phase in _NIGHT_PHASES:
        return None
    return {
        "model": output.model,
        "player_id": output.player_id,
        "speech": output.speech,
        "demeanor_emojis": _emojis(output),
    }


def build_agent_turn_private(output: AgentTurnOutput, state: GameState) -> dict:
    return {
        "role": output.role,
        "speech": output.speech,
        "demeanor": output.demeanor,
        "demeanor_emojis": _emojis(output),
        "reasoning": output.reasoning,
        "action": output.action.model_dump(mode="json"),
        "phase": state.phase.value,
    }


def build_agent_turn_god(output: AgentTurnOutput, state: GameState) -> dict:
    """Full turn record for global game log / dossier."""
    return {
        "model": output.model,
        "player_id": output.player_id,
        "role": output.role,
        "phase": state.phase.value,
        "round": state.round_number,
        "speech": output.speech,
        "demeanor": output.demeanor,
        "demeanor_emojis": _emojis(output),
        "reasoning": output.reasoning,
        "action": output.action.model_dump(mode="json"),
    }


def build_wolf_negotiation_payload(rounds: list[dict]) -> dict:
    return {"rounds": rounds}


def build_wolf_consensus_payload(state: GameState, *, unanimous: bool) -> dict:
    return {
        "target_id": state.wolf_kill_target,
        "unanimous": unanimous,
    }


def build_witch_night_payload(
    *,
    antidote_used: bool,
    poison_target: int | None,
) -> dict:
    return {
        "antidote_used": antidote_used,
        "poison_target": poison_target,
    }


def build_seer_check_payload(state: GameState) -> dict | None:
    if not state.seer_checks:
        return None
    check = state.seer_checks[-1]
    return {
        "target_id": check.target_id,
        "is_wolf": check.is_wolf,
        "round_number": check.round_number,
    }


def build_death_announcements_payload(state: GameState) -> dict:
    return {"player_ids": list(state.death_announcements)}


def build_vote_result_payload(
    *,
    eliminated: int | None,
    pk_candidates: tuple[int, ...],
    tied: bool,
) -> dict:
    return {
        "eliminated": eliminated,
        "pk_candidates": list(pk_candidates),
        "tied": tied,
    }


def build_hunter_shoot_payload(shooter_id: int, target_id: int | None) -> dict:
    return {"shooter_id": shooter_id, "target_id": target_id}


def build_game_over_payload(result) -> dict:
    return {
        "winner": result.winner.value if result.winner else None,
        "win_reason": result.win_reason.value if result.win_reason else None,
        "round_count": result.round_count,
    }


def build_player_dossier(
    state: GameState,
    *,
    turns: list[dict],
    seed: int | None,
) -> dict:
    """End-of-game summary for frontend god view."""
    by_player: dict[int, dict] = {
        p.player_id: {
            "player_id": p.player_id,
            "role": p.role.value,
            "alive": p.alive,
            "is_sheriff": p.is_sheriff,
            "in_soul_state": p.in_soul_state,
            "speech_count": 0,
            "turns": [],
        }
        for p in state.players
    }
    for turn in turns:
        pid = turn.get("player_id")
        if pid in by_player:
            by_player[pid]["turns"].append(turn)
            if turn.get("speech"):
                by_player[pid]["speech_count"] += 1
    return {
        "seed": seed,
        "winner": state.winner.value if state.winner else None,
        "win_reason": state.win_reason.value if state.win_reason else None,
        "round_count": state.round_number,
        "players": [by_player[i] for i in sorted(by_player)],
    }
