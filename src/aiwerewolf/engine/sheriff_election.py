"""Sheriff election helpers."""

from __future__ import annotations

from aiwerewolf.engine.state import GameState


def sheriff_speech_order(state: GameState) -> list[int]:
    """警上玩家从 1 号顺时针发言（仅仍在警上的候选人）。"""
    living = {p.player_id for p in state.living_players()}
    cands = [pid for pid in sorted(state.sheriff_candidates) if pid in living]
    if not cands:
        return []
    order: list[int] = []
    for offset in range(12):
        pid = ((offset % 12) + 1)
        if pid in cands:
            order.append(pid)
    return order


def sheriff_voter_ids(state: GameState) -> list[int]:
    """警下玩家：未上警且未退水，可投票。"""
    blocked = set(state.sheriff_candidates) | set(state.sheriff_withdrawn)
    return sorted(
        p.player_id
        for p in state.living_players()
        if p.player_id not in blocked and not p.in_soul_state
    )
