"""Validate agent actions against PlayerView (targets, roles, phase)."""

from __future__ import annotations

from schema.agent import (
    ActionPayload,
    HunterShootAction,
    SeerCheckAction,
    VoteAction,
    WitchPoisonAction,
    WolfKillAction,
)
from schema.enums import Phase, Role

from aiwerewolf.protocol.dispatch import validate_phase_action
from aiwerewolf.protocol.views import PlayerView


def _wolf_ids(view: PlayerView) -> set[int]:
    if view.own_role != Role.WOLF:
        return set()
    return set(view.wolf_teammates) | {view.player_id}


def validate_action_for_view(view: PlayerView, action: ActionPayload) -> tuple[bool, str]:
    ok, reason = validate_phase_action(
        view.phase,
        view.own_role,
        action,
        hunter_can_shoot=view.hunter_can_shoot,
        sheriff_election_step=view.sheriff_election_step,
    )
    if not ok:
        return False, reason

    living = set(view.living_player_ids)

    if isinstance(action, WolfKillAction):
        if action.target_id is None:
            return True, ""
        if action.target_id not in living:
            return False, f"wolf_kill target {action.target_id} is not alive"
        if action.target_id in _wolf_ids(view):
            return False, "wolf_kill cannot target a wolf"
        return True, ""

    if isinstance(action, WitchPoisonAction):
        if action.target_id is None:
            return True, ""
        if action.target_id not in living:
            return False, f"poison target {action.target_id} is not alive"
        if action.target_id == view.player_id:
            return False, "witch cannot poison self"
        return True, ""

    if isinstance(action, SeerCheckAction):
        if action.target_id not in living:
            return False, f"seer_check target {action.target_id} is not alive"
        if action.target_id == view.player_id:
            return False, "seer cannot check self"
        return True, ""

    if isinstance(action, VoteAction):
        if action.target_id is None:
            return True, ""
        if action.target_id not in living:
            return False, f"vote target {action.target_id} is not alive"
        if view.phase == Phase.DAY_SHERIFF and view.sheriff_election_step == "vote":
            if view.is_sheriff_candidate or view.is_sheriff_withdrawn:
                return False, "警上/退水玩家不能投票"
            if action.target_id not in view.sheriff_candidates:
                return False, "只能投票给仍在警上的候选人"
        return True, ""

    if isinstance(action, HunterShootAction):
        if action.target_id is None:
            return True, ""
        if action.target_id not in living:
            return False, f"hunter_shoot target {action.target_id} is not alive"
        if action.target_id == view.player_id:
            return False, "hunter cannot shoot self"
        return True, ""

    return True, ""
