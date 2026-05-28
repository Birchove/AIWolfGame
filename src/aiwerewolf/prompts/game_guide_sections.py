"""Extract role-scoped slices from game_guide.md — not full injection per agent."""

from __future__ import annotations

import re
from functools import lru_cache
from pathlib import Path

from schema.enums import Role

# h4 titles in game_guide.md (first block under ### 身份战术)
_IDENTITY_TITLES: dict[Role, str] = {
    Role.SEER: "预言家",
    Role.WITCH: "女巫",
    Role.HUNTER: "猎人",
    Role.IDIOT: "白痴",
    Role.WOLF: "狼人",
    Role.VILLAGER: "普通村民",
}

# Opponent intel: which other roles' tactics to include for inference
_OPPONENT_TITLES: dict[Role, tuple[str, ...]] = {
    Role.WOLF: ("预言家", "女巫", "猎人"),
    Role.SEER: ("狼人",),
    Role.WITCH: ("狼人", "预言家"),
    Role.HUNTER: ("狼人",),
    Role.IDIOT: ("狼人",),
    Role.VILLAGER: ("狼人", "预言家"),
}

_CAMP_WOLF_MARKER = "#### 狼人阵营"
_TERMS_MARKER = "### 狼人杀术语总结"
_GOOD_DETAIL_MARKER = "#### 好人阵营详解"


def _slice_h4(text: str, title: str, *, start_at: int = 0) -> str:
    pattern = re.compile(rf"^####\s+{re.escape(title)}\s*$", re.MULTILINE)
    match = pattern.search(text, start_at)
    if not match:
        return ""
    body_start = match.end()
    next_header = re.search(r"^#{2,4}\s+", text[body_start:], re.MULTILINE)
    body_end = body_start + next_header.start() if next_header else len(text)
    return text[body_start:body_end].strip()


def _slice_from_marker(text: str, marker: str, *, stop_markers: tuple[str, ...]) -> str:
    idx = text.find(marker)
    if idx < 0:
        return ""
    start = idx + len(marker)
    end = len(text)
    for stop in stop_markers:
        pos = text.find(stop, start)
        if pos >= 0:
            end = min(end, pos)
    return text[start:end].strip()


@lru_cache(maxsize=8)
def _load_guide_text(repo_root: str, relative: str) -> str:
    return (Path(repo_root) / relative).read_text(encoding="utf-8")


def build_role_scoped_game_guide(
    *,
    repo_root: Path,
    guide_file: str,
    role: Role,
) -> str:
    """Own-role tactics + opponent intel + terminology — not the full guide."""
    text = _load_guide_text(str(repo_root.resolve()), guide_file)
    parts: list[str] = []

    own_title = _IDENTITY_TITLES[role]
    own_block = _slice_h4(text, own_title)
    if own_block:
        parts.append(f"### 本身份常见打法（{own_title}）\n{own_block}")

    if role == Role.WOLF:
        camp = _slice_from_marker(
            text,
            _CAMP_WOLF_MARKER,
            stop_markers=(_GOOD_DETAIL_MARKER, _TERMS_MARKER),
        )
        if camp:
            parts.append(f"### 狼队阵营战术参考\n{camp}")
    elif role in {Role.SEER, Role.WITCH, Role.HUNTER, Role.IDIOT, Role.VILLAGER}:
        wolf_camp = _slice_from_marker(
            text,
            _CAMP_WOLF_MARKER,
            stop_markers=(_GOOD_DETAIL_MARKER, _TERMS_MARKER),
        )
        if wolf_camp:
            # Good players need wolf intel; trim very long camp section
            trimmed = wolf_camp[:3500] + ("…" if len(wolf_camp) > 3500 else "")
            parts.append(f"### 狼队可能战术（推理对手）\n{trimmed}")

    opp_blocks: list[str] = []
    for title in _OPPONENT_TITLES.get(role, ()):
        block = _slice_h4(text, title)
        if block:
            opp_blocks.append(f"#### {title}\n{block[:1200]}")
    if opp_blocks:
        parts.append("### 其他身份可能打法（推理对手）\n" + "\n\n".join(opp_blocks))

    terms = _slice_from_marker(text, _TERMS_MARKER, stop_markers=("### 参考资料",))
    if terms:
        parts.append(f"### 术语速查\n{terms[:2000]}")

    return "\n\n".join(parts)
