# Phase 7 — 验收记录

**状态：完成**（Claude Code review 已采纳）

## 交付物

| 模块 | 说明 |
|------|------|
| `schema/events.py` | 扁平 `GameEvent`（type + payload + visibility） |
| `logging/log.py` | `EventLog` 容器 |
| `logging/builder.py` | 从 state/output 构建 payload |
| `logging/recorder.py` | `Recorder` — 12+ record 方法 |
| `logging/storage.py` | JSONL 读写 |
| `logging/replay.py` | `replay_events(mode=public\|god\|private:N)` |
| `engine/loop.py` | 可选 `recorder=` hooks |
| `api/app.py` | FastAPI + WS |
| `api/registry.py` | 内存对局注册表 |
| `api/runner.py` | `run_in_executor` 后台对局 |
| `main.py` | `--record logs/game.jsonl` |

## CC 采纳

- 15+ 事件类型（vote_cast/result、hunter_shoot、seer_check、wolf_negotiation 等）
- 夜间 agent_turn 无 public 条目；private 含 role+action
- 狼协商 local list → god_only 事件
- `BackgroundTasks` + `run_in_executor`（API 不阻塞 event loop）
- `logging/builder.py` 命名（非 events.py 冲突）
- `private:N` replay 含 public + 该玩家 private

## 非目标（Phase 8）

- 从事件完整重建 GameState
- React UI

## 验收

```bash
pip install -e ".[dev,agents,api]"
pytest tests/ -q                    # 117 passed
python main.py --mode random --record logs/demo.jsonl --count 1
python -m aiwerewolf.api.server     # POST /games, WS /ws/games/{id}
```
