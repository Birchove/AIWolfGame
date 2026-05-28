"""Human-readable god-view chronicle from event log."""

from __future__ import annotations

from pathlib import Path

from schema.events import GameEvent

from aiwerewolf.logging.log import EventLog

_NIGHT_PHASE_PREFIXES = (
    "night_wolf",
    "night_witch",
    "night_seer",
    "night_hunter",
    "night_idiot",
)

_PHASE_LABELS: dict[str, str] = {
    "night_wolf": "狼人行动",
    "night_witch": "女巫行动",
    "night_seer": "预言家验人",
    "night_hunter": "猎人状态",
    "night_idiot": "白痴确认",
    "day_sheriff": "警长竞选",
    "day_announce": "死亡公布/遗言",
    "day_speech": "白天发言",
    "day_vote": "放逐投票",
    "day_pk": "PK 发言/投票",
    "game_over": "游戏结束",
}


def _section_label(round_num: int | None, phase: str | None) -> str:
    r = round_num if round_num is not None else "?"
    if phase and any(phase.startswith(p) for p in _NIGHT_PHASE_PREFIXES):
        return f"第 {r} 天 · 夜晚 · {_PHASE_LABELS.get(phase, phase)}"
    if phase:
        return f"第 {r} 天 · 白天 · {_PHASE_LABELS.get(phase, phase)}"
    return f"第 {r} 天"


def _format_action(action: dict) -> str:
    if not action:
        return "pass"
    atype = action.get("type", "?")
    if atype == "wolf_kill":
        t = action.get("target_id")
        return f"狼刀 → P{t}" if t is not None else "空刀"
    if atype == "witch_save":
        return "女巫解药" if action.get("use_antidote") else "女巫不救"
    if atype == "witch_poison":
        t = action.get("target_id")
        return f"女巫毒 → P{t}" if t is not None else "女巫不毒"
    if atype == "seer_check":
        return f"验人 → P{action.get('target_id')}"
    if atype == "vote":
        t = action.get("target_id")
        return f"投票 → P{t}" if t is not None else "弃票"
    if atype == "hunter_shoot":
        t = action.get("target_id")
        return f"猎人开枪 → P{t}" if t is not None else "猎人不开枪"
    if atype == "self_destruct":
        return "狼人自爆"
    if atype == "speech":
        return "发言"
    return atype


def _format_turn_block(payload: dict) -> list[str]:
    lines: list[str] = []
    pid = payload.get("player_id", "?")
    role = payload.get("role", "?")
    emojis = payload.get("demeanor_emojis") or []
    emoji_str = "".join(emojis) if emojis else ""
    header = f"[P{pid} · {role}]"
    if emoji_str:
        header += f" {emoji_str}"
    lines.append(header)
    if payload.get("speech"):
        lines.append(f"  发言: {payload['speech']}")
    if payload.get("demeanor"):
        lines.append(f"  神态: {payload['demeanor']}")
    if payload.get("reasoning"):
        lines.append(f"  心理: {payload['reasoning']}")
    action = payload.get("action")
    if action:
        lines.append(f"  行动: {_format_action(action)}")
    return lines


def _format_event_line(event: GameEvent) -> list[str]:
    p = event.payload
    t = event.type

    if t == "agent_turn_full":
        return _format_turn_block(p)

    if t == "wolf_consensus":
        tgt = p.get("target_id")
        unan = "一致" if p.get("unanimous") else "非一致"
        tgt_s = f"P{tgt}" if tgt is not None else "空刀"
        return [f"  ▶ 狼刀共识 ({unan}): {tgt_s}"]

    if t == "witch_night":
        parts = []
        if p.get("antidote_used"):
            parts.append("使用解药")
        if p.get("poison_target") is not None:
            parts.append(f"毒 P{p['poison_target']}")
        if not parts:
            parts.append("未用药")
        return [f"  ▶ 女巫: {', '.join(parts)}"]

    if t == "night_death":
        return [f"  ▶ 夜间死亡: P{p.get('player_id')}"]

    if t == "seer_check":
        wolf = "狼" if p.get("is_wolf") else "好人"
        return [f"  ▶ 验人 P{p.get('target_id')}: {wolf}"]

    if t == "death":
        cause = p.get("cause", "死亡")
        return [f"  ▶ 死亡: P{p.get('player_id')} ({cause})"]

    if t == "vote_result":
        if p.get("tied"):
            pk = p.get("pk_candidates") or []
            return [f"  ▶ 平票 PK: {pk}"]
        elim = p.get("eliminated")
        return [f"  ▶ 投票出局: P{elim}" if elim else "  ▶ 平安日"]

    if t in {"sheriff_elected", "sheriff_proclaimed"}:
        msg = p.get("message") or f"P{p.get('player_id')} 当选警长"
        return [f"  ▶ 🎖 {msg}"]

    if t == "sheriff_nominate":
        return [f"  ▶ {p.get('message', '')}"]

    if t == "sheriff_nomination_complete":
        return [f"  ▶ {p.get('message', '')}"]

    if t == "sheriff_withdraw":
        return [f"  ▶ {p.get('message', '')}"]

    if t == "sheriff_vote_result":
        return [f"  ▶ {p.get('message', '')}"]

    if t == "hunter_shoot":
        tgt = p.get("target_id")
        return [
            f"  ▶ 猎人 P{p.get('shooter_id')} 开枪 → P{tgt}"
            if tgt is not None
            else f"  ▶ 猎人 P{p.get('shooter_id')} 不开枪"
        ]

    if t == "self_destruct":
        return [f"  ▶ 自爆: P{p.get('player_id')}"]

    if t == "idiot_reveal":
        return [f"  ▶ 白痴翻牌: P{p.get('player_id')}"]

    if t == "wolf_negotiation_round":
        rounds = p.get("rounds") or []
        lines = ["  ▶ 狼队协商:"]
        for rnd in rounds:
            votes = rnd.get("votes") or []
            parts = [
                f"P{v.get('wolf_id')}→{('P'+str(v['target_id'])) if v.get('target_id') is not None else '空'}"
                for v in votes
            ]
            lines.append(f"    第{rnd.get('round', '?')}轮: {', '.join(parts)}")
        return lines

    if t == "game_over":
        return [
            f"═══ 游戏结束: {p.get('winner')} 胜 ({p.get('win_reason')}) ═══"
        ]

    if t == "game_start":
        roles = p.get("roles") or {}
        role_line = ", ".join(f"P{k}={v}" for k, v in sorted(roles.items(), key=lambda x: int(x[0])))
        return [f"═══ 开局 seed={p.get('seed')} ═══", role_line, ""]

    return []


def format_god_chronicle(log: EventLog) -> str:
    """Render god-view timeline grouped by round and phase."""
    lines: list[str] = []
    current_section: str | None = None

    god_types = {
        "game_start",
        "agent_turn_full",
        "wolf_negotiation_round",
        "wolf_consensus",
        "witch_night",
        "night_death",
        "seer_check",
        "death",
        "vote_result",
        "sheriff_elected",
        "sheriff_nominate",
        "sheriff_nomination_complete",
        "sheriff_withdraw",
        "sheriff_speech_complete",
        "sheriff_vote_result",
        "hunter_shoot",
        "self_destruct",
        "game_over",
    }

    for event in log.events:
        if event.visibility != "god_only" and event.type not in {
            "death",
            "vote_result",
            "sheriff_elected",
            "hunter_shoot",
            "self_destruct",
            "idiot_reveal",
            "game_over",
            "seer_check",
        }:
            continue
        if event.type not in god_types:
            continue

        if event.type == "agent_turn_full":
            section = _section_label(event.round, event.phase)
            if section != current_section:
                if lines and lines[-1] != "":
                    lines.append("")
                lines.append(f"--- {section} ---")
                current_section = section

        block = _format_event_line(event)
        if block:
            lines.extend(block)
            if event.type == "agent_turn_full":
                lines.append("")

    return "\n".join(lines).strip() + "\n"


def write_god_chronicle(jsonl_path: Path, log: EventLog) -> Path:
    """Write readable chronicle next to JSONL (same stem, .chronicle.txt)."""
    out = jsonl_path.with_suffix(".chronicle.txt")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(format_god_chronicle(log), encoding="utf-8")
    return out
