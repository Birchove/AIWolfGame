"""Map AgentTurnOutput actions to engine functions."""

from __future__ import annotations

from schema.agent import (
    ActionPayload,
    HunterShootAction,
    PassAction,
    SeerCheckAction,
    SelfDestructAction,
    SheriffRunAction,
    SheriffTransferAction,
    SheriffWithdrawAction,
    SpeechAction,
    SpeechOrderAction,
    VoteAction,
    WitchPoisonAction,
    WitchSaveAction,
    WolfKillAction,
)
from schema.enums import Phase, Role

from aiwerewolf.engine.day import (
    cast_day_vote,
    cast_sheriff_vote,
    nominate_for_sheriff,
    resolve_hunter_shoot,
    transfer_sheriff_badge,
    withdraw_sheriff_candidacy,
    wolf_self_destruct,
)
from aiwerewolf.engine.night import (
    check_hunter_status,
    confirm_idiot,
    resolve_seer_check,
    resolve_witch,
    resolve_wolf_kill,
)
from dataclasses import replace

from aiwerewolf.engine.state import GameState
from schema.agent import AgentTurnOutput

# action.type -> allowed phases (shared with view_format for LLM prompts)
PHASE_ALLOWED_ACTIONS: dict[Phase, frozenset[str]] = {
    Phase.NIGHT_WOLF: frozenset({"wolf_kill", "pass"}),
    Phase.NIGHT_WITCH: frozenset({"witch_save", "witch_poison", "pass"}),
    Phase.NIGHT_SEER: frozenset({"seer_check", "pass"}),
    Phase.NIGHT_HUNTER: frozenset({"pass"}),
    Phase.NIGHT_IDIOT: frozenset({"pass"}),
    Phase.DAY_SHERIFF: frozenset(
        {"sheriff_run", "sheriff_withdraw", "speech", "vote", "self_destruct", "pass"}
    ),
    Phase.DAY_ANNOUNCE: frozenset({"speech", "sheriff_transfer", "self_destruct", "pass"}),
    Phase.DAY_SPEECH: frozenset({"speech", "speech_order", "self_destruct", "pass"}),
    Phase.DAY_VOTE: frozenset({"vote", "self_destruct", "pass"}),
    Phase.DAY_PK: frozenset({"speech", "vote", "self_destruct", "pass"}),
}

_ROLE_PHASE: dict[Phase, Role | None] = {
    Phase.NIGHT_WOLF: Role.WOLF,
    Phase.NIGHT_WITCH: Role.WITCH,
    Phase.NIGHT_SEER: Role.SEER,
    Phase.NIGHT_HUNTER: Role.HUNTER,
    Phase.NIGHT_IDIOT: Role.IDIOT,
}


def validate_phase_action(
    phase: Phase,
    role: Role,
    action: ActionPayload,
    *,
    hunter_can_shoot: bool = False,
    sheriff_election_step: str = "nominate",
    player_id: int = 0,
    state_sheriff_id: int | None = None,
    speech_order_pending: bool = False,
    sheriff_badge_pending_from: int | None = None,
) -> tuple[bool, str]:
    if hunter_can_shoot and role == Role.HUNTER:
        if isinstance(action, HunterShootAction):
            return True, ""
        return False, "hunter must shoot or decline when ability active"

    required = _ROLE_PHASE.get(phase)
    if required is not None and role != required:
        if isinstance(action, PassAction):
            return True, ""
        return False, f"role {role} cannot act in {phase}"

    allowed = PHASE_ALLOWED_ACTIONS.get(phase)
    if allowed is None:
        return isinstance(action, PassAction), "unknown phase"
    if action.type not in allowed:
        return False, f"action {action.type} not allowed in {phase}"

    if phase == Phase.DAY_SHERIFF:
        step = sheriff_election_step or "nominate"
        if step == "nominate":
            if isinstance(action, (SheriffRunAction, PassAction, SelfDestructAction)):
                return True, ""
            return False, "nominate step: use sheriff_run to 上警 or pass to stay 警下"
        if step == "speech":
            if isinstance(
                action, (SpeechAction, SheriffWithdrawAction, SelfDestructAction, PassAction)
            ):
                return True, ""
            return False, "speech step: only 警上 candidates may speech or sheriff_withdraw"
        if step == "vote":
            if isinstance(action, (VoteAction, SelfDestructAction, PassAction)):
                return True, ""
            return False, "vote step: 警下 players vote for a candidate"
    if phase == Phase.DAY_ANNOUNCE and sheriff_badge_pending_from == player_id:
        if isinstance(
            action, (SpeechAction, SheriffTransferAction, PassAction)
        ):
            return True, ""
        return False, "pending sheriff: last words and/or sheriff_transfer"
    if phase == Phase.DAY_ANNOUNCE and isinstance(action, SheriffTransferAction):
        return False, "only pending sheriff may transfer badge"
    if phase == Phase.DAY_SPEECH and speech_order_pending:
        if player_id != state_sheriff_id:
            if isinstance(action, PassAction):
                return True, ""
            return False, "wait for sheriff to set speech order"
        if isinstance(action, (SpeechOrderAction, PassAction, SelfDestructAction)):
            return True, ""
        return False, "sheriff must speech_order (left/right) or pass for default"
    if phase == Phase.DAY_SPEECH and isinstance(action, SpeechOrderAction):
        return False, "speech order already set"
    return True, ""


def apply_action(state: GameState, output: AgentTurnOutput) -> GameState:
    """Apply one agent turn; validates phase/role before dispatch."""
    player = state.player(output.player_id)
    action = output.action

    if player.role == Role.HUNTER and state.hunter_can_shoot:
        if isinstance(action, HunterShootAction):
            ok, reason = validate_phase_action(
                state.phase, player.role, action, hunter_can_shoot=True
            )
            if not ok:
                raise ValueError(reason)
            return resolve_hunter_shoot(state, output.player_id, action.target_id)

    ok, reason = validate_phase_action(
        state.phase,
        player.role,
        action,
        sheriff_election_step=state.sheriff_election_step,
        player_id=output.player_id,
        state_sheriff_id=state.sheriff_id,
        speech_order_pending=state.speech_order_pending,
        sheriff_badge_pending_from=state.sheriff_badge_pending_from,
    )
    if not ok:
        raise ValueError(reason)

    phase = state.phase

    if isinstance(action, PassAction):
        if phase == Phase.NIGHT_HUNTER:
            return check_hunter_status(state)
        if phase == Phase.NIGHT_IDIOT:
            return confirm_idiot(state)
        return state

    if isinstance(action, SpeechAction):
        return state

    if phase == Phase.DAY_SPEECH and isinstance(action, SpeechOrderAction):
        return replace(
            state,
            speech_order_side=action.side,
            speech_first_speaker_id=action.first_speaker_id,
            speech_order_pending=False,
        )

    if phase == Phase.NIGHT_WOLF and isinstance(action, WolfKillAction):
        return resolve_wolf_kill(state, action.target_id)

    if phase == Phase.NIGHT_WITCH:
        if isinstance(action, WitchSaveAction):
            return resolve_witch(state, use_antidote=action.use_antidote)
        if isinstance(action, WitchPoisonAction):
            return resolve_witch(state, poison_target=action.target_id)

    if phase == Phase.NIGHT_SEER and isinstance(action, SeerCheckAction):
        return resolve_seer_check(state, action.target_id)

    if phase == Phase.DAY_SHERIFF:
        step = state.sheriff_election_step or "nominate"
        if isinstance(action, SelfDestructAction):
            return wolf_self_destruct(
                state, output.player_id, transfer_to=action.transfer_to
            )
        if step == "nominate":
            if isinstance(action, SheriffRunAction):
                return nominate_for_sheriff(state, output.player_id)
            return state
        if step == "speech":
            if isinstance(action, SheriffWithdrawAction):
                return withdraw_sheriff_candidacy(state, output.player_id)
            return state
        if step == "vote" and isinstance(action, VoteAction):
            if action.target_id is not None:
                return cast_sheriff_vote(
                    state, output.player_id, action.target_id
                )
        return state

    if phase in {Phase.DAY_ANNOUNCE, Phase.DAY_SPEECH}:
        if isinstance(action, SelfDestructAction):
            return wolf_self_destruct(
                state, output.player_id, transfer_to=action.transfer_to
            )
        if isinstance(action, SheriffTransferAction):
            pending = state.sheriff_badge_pending_from
            if pending is None:
                raise ValueError("no pending sheriff badge to transfer")
            return transfer_sheriff_badge(state, pending, action.transfer_to)
        return state

    if phase in {Phase.DAY_VOTE, Phase.DAY_PK}:
        if isinstance(action, SelfDestructAction):
            return wolf_self_destruct(
                state, output.player_id, transfer_to=action.transfer_to
            )
        if isinstance(action, VoteAction):
            return cast_day_vote(state, output.player_id, action.target_id)

    return state
