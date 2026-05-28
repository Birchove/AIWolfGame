# Phase 3 — 验收记录

**状态：完成**（Slice 1 夜间 + Slice 2 白天，× Claude Code）

## Slice 1 — `engine/night.py`

狼刀 → 女巫 → 预言家 → 猎人状态 → 白痴 → 死讯 → 检胜

## Slice 2 — `engine/day.py`

| 功能 | 函数 |
|------|------|
| 警长竞选 | `nominate_for_sheriff`, `withdraw`, `cast_sheriff_vote`, `resolve_sheriff_election/pk` |
| 白天投票 | `cast_day_vote`（警长 1.5 票）, `resolve_day_vote`, `resolve_pk_vote` |
| 狼自爆 | `wolf_self_destruct`（警长须移徽，两狼自爆禁警长） |
| 白痴翻牌 | `idiot_reveal_on_vote` / `resolve_day_vote` 自动触发 |
| 猎人开枪 | `resolve_hunter_shoot` |
| 移徽 | `transfer_sheriff_badge` |

## GameState 新增字段

`sheriff_candidates`, `day_votes`, `pk_candidates`, `self_destruct_today`, `sheriff_election_retry/forbidden` 等

## 验收

```bash
pytest tests/ -q   # 73 passed
python main_demo.py
```

## 下一步

Phase 4 — Protocol + RandomAgent
