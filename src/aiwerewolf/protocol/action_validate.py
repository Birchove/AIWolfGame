"""Validate agent actions against PlayerView (targets, roles, phase)."""

from __future__ import annotations

from schema.agent import (
    ActionPayload,
    HunterShootAction,
    SeerCheckAction,
    SpeechOrderAction,
    SheriffTransferAction,
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
        player_id=view.player_id,
        state_sheriff_id=view.sheriff_id,
        speech_order_pending=view.speech_order_pending,
        sheriff_badge_pending_from=(
            view.player_id if view.must_transfer_sheriff_badge else None
        ),
    )
    if not ok:
        return False, reason

    if not view.is_alive and not view.in_soul_state:
        if view.must_transfer_sheriff_badge or view.may_give_last_words:
            pass
        else:
            return False, "dead player cannot act"

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

    if isinstance(action, SpeechOrderAction):
        if action.first_speaker_id is not None:
            if action.first_speaker_id not in living:
                return False, f"first_speaker_id {action.first_speaker_id} is not alive"
        return True, ""

    if isinstance(action, SheriffTransferAction):
        if action.transfer_to not in living:
            return False, f"transfer_to {action.transfer_to} is not alive"
        if action.transfer_to == view.player_id:
            return False, "cannot transfer badge to self"
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
