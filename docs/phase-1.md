# Phase 1 — 验收记录

**状态：完成**

## 交付物

| 模块 | 说明 |
|------|------|
| `engine/state.py` | `GameState`, `PlayerState`, `WinResult`（frozen dataclass） |
| `engine/setup.py` | `create_game`, `assign_roles`, 12 人预女猎白牌堆 |
| `engine/rules.py` | `check_win`, `next_phase`, `eliminate_player`, `apply_win_if_any` |
| `tests/fixtures/scenarios.py` | 确定性局面 fixture |
| `tests/unit/test_state.py` | 状态与 immutable |
| `tests/unit/test_win.py` | 屠边 / 狼全灭 / 灵魂态白痴 |
| `tests/unit/test_rules.py` | 阶段流转、首日后跳过警长竞选 |

## 验收

```bash
pytest tests/ -q   # 24 passed
```

## 下一步

Phase 2 — `Visibility.for_player` / `PlayerView` + 防泄露测试
