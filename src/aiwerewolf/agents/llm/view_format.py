"""Serialize PlayerView and allowed actions for LLM user messages."""

from __future__ import annotations

import json
from dataclasses import asdict
from typing import Any

from schema.agent import PassAction
from schema.enums import Phase, Role

from aiwerewolf.engine.state import SpeechRecord
from aiwerewolf.protocol.action_validate import validate_action_for_view
from aiwerewolf.protocol.dispatch import PHASE_ALLOWED_ACTIONS
from aiwerewolf.protocol.views import PlayerView

_ACTION_EXAMPLES: dict[str, dict[str, Any]] = {
    "pass": PassAction().model_dump(),
    "speech": {"type": "speech", "speech": "...", "demeanor": ""},
    "vote": {"type": "vote", "target_id": 1},
    "sheriff_run": {"type": "sheriff_run"},
    "sheriff_withdraw": {"type": "sheriff_withdraw"},
    "wolf_kill": {"type": "wolf_kill", "target_id": 1},
    "self_destruct": {
        "type": "self_destruct",
        "last_words": "...",
        "transfer_to": None,
    },
    "hunter_shoot": {"type": "hunter_shoot", "target_id": None},
    "witch_save": {"type": "witch_save", "use_antidote": True},
    "witch_poison": {"type": "witch_poison", "target_id": 1},
    "seer_check": {"type": "seer_check", "target_id": 1},
}


def _enum_to_value(obj: Any) -> Any:
    if hasattr(obj, "value"):
        return obj.value
    if isinstance(obj, dict):
        return {k: _enum_to_value(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_enum_to_value(x) for x in obj]
    return obj


def view_to_dict(view: PlayerView) -> dict[str, Any]:
    return _enum_to_value(asdict(view))


def _format_speech_record(rec: SpeechRecord) -> dict[str, Any]:
    emojis = "".join(rec.demeanor_emojis) if rec.demeanor_emojis else ""
    return {
        "player_id": rec.player_id,
        "round": rec.round_number,
        "phase": rec.phase,
        "speech": rec.speech,
        "demeanor_emojis": list(rec.demeanor_emojis),
        "demeanor_display": emojis,
    }


def allowed_actions_for_view(view: PlayerView) -> list[dict[str, Any]]:
    if view.hunter_can_shoot and view.own_role == Role.HUNTER:
        return [_ACTION_EXAMPLES["hunter_shoot"], _ACTION_EXAMPLES["pass"]]

    required_role = {
        Phase.NIGHT_WOLF: Role.WOLF,
        Phase.NIGHT_WITCH: Role.WITCH,
        Phase.NIGHT_SEER: Role.SEER,
    }.get(view.phase)
    if required_role is not None and view.own_role != required_role:
        return [_ACTION_EXAMPLES["pass"]]

    if view.phase == Phase.DAY_SHERIFF:
        step = view.sheriff_election_step or "nominate"
        if step == "nominate":
            return [
                _ACTION_EXAMPLES["sheriff_run"],
                _ACTION_EXAMPLES["pass"],
                _ACTION_EXAMPLES["self_destruct"],
            ]
        if step == "speech":
            if view.is_sheriff_candidate:
                return [
                    _ACTION_EXAMPLES["speech"],
                    _ACTION_EXAMPLES["sheriff_withdraw"],
                    _ACTION_EXAMPLES["pass"],
                    _ACTION_EXAMPLES["self_destruct"],
                ]
            return [_ACTION_EXAMPLES["pass"]]
        if step == "vote":
            if view.is_sheriff_voter:
                return [
                    _ACTION_EXAMPLES["vote"],
                    _ACTION_EXAMPLES["pass"],
                    _ACTION_EXAMPLES["self_destruct"],
                ]
            return [_ACTION_EXAMPLES["pass"]]

    allowed_types = PHASE_ALLOWED_ACTIONS.get(view.phase, frozenset({"pass"}))
    return [_ACTION_EXAMPLES[t] for t in sorted(allowed_types) if t in _ACTION_EXAMPLES]


def allowed_actions_for_phase(
    phase: Phase,
    role: Role,
    *,
    hunter_can_shoot: bool = False,
    sheriff_election_step: str = "nominate",
    is_sheriff_candidate: bool = False,
    is_sheriff_voter: bool = False,
) -> list[dict[str, Any]]:
    view = PlayerView(
        player_id=1,
        own_role=role,
        phase=phase,
        round_number=1,
        is_alive=True,
        is_sheriff=False,
        in_soul_state=False,
        living_player_ids=tuple(range(1, 13)),
        dead_player_ids=(),
        sheriff_id=None,
        public_events=(),
        hunter_can_shoot=hunter_can_shoot,
        sheriff_election_step=sheriff_election_step,
        is_sheriff_candidate=is_sheriff_candidate,
        is_sheriff_voter=is_sheriff_voter,
    )
    return allowed_actions_for_view(view)


def format_player_view(view: PlayerView) -> str:
    view_dict = view_to_dict(view)
    # Transcripts are duplicated in dedicated sections for LLM readability.
    view_dict.pop("public_speeches", None)
    view_dict.pop("wolf_team_speeches", None)

    payload: dict[str, Any] = {
        "view": view_dict,
        "public_speeches": [
            _format_speech_record(s) for s in view.public_speeches
        ],
        "allowed_actions": allowed_actions_for_view(view),
    }
    if view.phase == Phase.DAY_SHERIFF:
        payload["sheriff_election"] = {
            "step": view.sheriff_election_step,
            "candidates": list(view.sheriff_candidates),
            "withdrawn": list(view.sheriff_withdrawn),
            "you_are_candidate": view.is_sheriff_candidate,
            "you_can_vote": view.is_sheriff_voter,
        }
        step = view.sheriff_election_step
        if step == "nominate":
            payload["sheriff_hint"] = "上警: action=sheriff_run；不上警: pass（警下）"
        elif step == "speech":
            payload["sheriff_hint"] = "仅警上玩家发言；可 sheriff_withdraw 退水（退水后不可投票）"
        elif step == "vote":
            payload["sheriff_hint"] = "仅警下玩家 vote 给仍在警上的候选人"
    if view.wolf_team_speeches:
        payload["wolf_team_speeches"] = [
            _format_speech_record(s) for s in view.wolf_team_speeches
        ]
    if view.wolf_prior_votes:
        payload["wolf_negotiation_hint"] = (
            "狼队协商 — 上一轮刀口投票: "
            + ", ".join(
                f"玩家{wid}→{tgt if tgt is not None else '空刀'}"
                for wid, tgt in view.wolf_prior_votes
            )
        )
    if view.is_sheriff and view.own_role == Role.WOLF:
        payload["sheriff_wolf_hint"] = "自爆时 action 须含 transfer_to 指定移徽目标"
    if view.phase == Phase.NIGHT_WOLF and view.own_role == Role.WOLF:
        payload["wolf_night_hint"] = (
            "先 speech 与队友商议刀口与白天分工，再 wolf_kill 投票。"
            "阅读 wolf_team_speeches，可同意或提出不同方案；"
            "禁止复读队友原话，用你的人格重新表述。"
        )
    if view.phase in {Phase.DAY_SPEECH, Phase.DAY_PK}:
        recent = view.public_speeches[-2:]
        if recent:
            ids = ", ".join(str(s.player_id) for s in recent)
            payload["day_speech_hint"] = (
                f"前几位发言者：{ids}。"
                "不要简单附和「我同意X号」；用你的人格提出独立判断或追问。"
            )
    payload["diversity_hint"] = (
        "你的 speech 须体现本局人格，避免与其他玩家雷同；"
        "不要套用攻略模板句。"
    )
    return json.dumps(payload, ensure_ascii=False, indent=2)


def validate_output_for_view(view: PlayerView, output) -> tuple[bool, str]:
    return validate_action_for_view(view, output.action)
