"""Deterministic player personas — one per seat, stable across a game."""

from __future__ import annotations

import random

_PERSONA_POOL: tuple[str, ...] = (
    "逻辑缜密、措辞克制，倾向先听后说",
    "发言激进、喜欢带节奏，但偶尔过度自信",
    "表面划水、实则观察，关键轮次才表态",
    "情绪外露、用语夸张，容易站边也容易被带偏",
    "擅长盘狼坑、喜欢追问细节",
    "保守稳健、不轻易亮身份，更信票型与发言一致性",
    "爱用反逻辑、常提出冷门假设",
    "发言简短、信息密度高，不喜欢重复他人观点",
    "善于伪装成平民，话术圆滑",
    "正义感强、对可疑行为零容忍",
    "擅长倒钩式发言，表面中立实则站队",
    "新手气质、偶尔口误，但直觉有时很准",
    "老练玩家口吻，爱引用票型和位置学",
    "话痨型，发言长但逻辑链完整",
    "沉默寡言，开口必是关键信息",
    "怀疑一切对跳，习惯要求对方自证",
    "擅长煽情拉票，语气真诚",
    "冷静分析型，很少带情绪词",
    "爱开玩笑缓和气氛，但投票很果断",
    "固执己见，一旦站边很难被说服",
)


def assign_personas(*, seed: int | None = None, count: int = 12) -> dict[int, str]:
    """Return player_id -> persona description for seats 1..count."""
    rng = random.Random(seed)
    pool = list(_PERSONA_POOL)
    rng.shuffle(pool)
    return {i + 1: pool[i % len(pool)] for i in range(count)}
