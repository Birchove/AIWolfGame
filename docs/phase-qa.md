# Phase 0-2 QA — Cursor × Claude Code

**日期**：2026-05-28  
**结论**：CONDITIONAL PASS → 修复后 **PASS**，可进入 Phase 3

## CC 发现 & 修复状态

| 项 | 严重度 | 状态 |
|----|--------|------|
| BUG1 DAY_PK 未清 `is_first_day` | Blocker | ✅ 已修 |
| BUG2 灵魂态白痴被毒 | Blocker | ✅ `eliminate_player(cause=POISON)` 拒绝 |
| GAP1 缺 Phase3 action 类型 | Blocker | ✅ Witch/Seer/Idiot actions |
| GAP2 Config/default.yaml 缺失 | High | ✅ 已恢复 |
| GAP3 test_config 路径错误 | Medium | ✅ `parents[2]` |

## 新增

- `src/aiwerewolf/integration/smoke.py` — 跨模块冒烟
- `tests/unit/test_integration_smoke.py` — CC 建议的补充测试
- `main_demo.py` — 调用真实 integration smoke

## 验收

```bash
pytest tests/ -q
python main_demo.py
```
