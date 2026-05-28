# Phase 5 — 验收记录

**状态：完成**（Claude Code review 已采纳 P0/P1 修复）

## 交付物

| 模块 | 说明 |
|------|------|
| `engine/loop.py` | `GameLoop.run()` — 全阶段驱动 |
| `main_demo.py` | 100 局 RandomAgent 回归 |
| `tests/unit/test_game_loop.py` | 单局 + 100 局 + 可见性/死讯测试 |

## CC 采纳

- 狼刀：四狼投票协商（最多 5 轮），一致则生效；否则 plurality，仍平票则空刀
- 女巫：解析 `WitchSaveAction`/`WitchPoisonAction` 后 `resolve_witch()`；非法则 fallback
- `collect_death_announcements()` 在 `NIGHT_IDIOT` 后、`DAY_ANNOUNCE` 前调用
- 白天任意阶段允许 `SelfDestructAction`；警长狼自爆须 `transfer_to`
- `GameLoop` 从 `engine/__init__` 移出，避免与 `protocol` 循环 import
- 每阶段后 `apply_win_if_any(max_rounds)`

## CC 留 Phase 6

- 警长死亡移徽协议（`eliminate_player` 时 agent 指定目标）
- `IdiotRevealAction` 清理或接入 dispatch
- 事件流扩展（投票/验人）→ Phase 7 EventLog

## 验收

```bash
pytest tests/ -q
python main_demo.py
```
