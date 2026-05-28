# Phase 8 — 验收记录

**状态：完成**（Claude Code review 已采纳）

## 交付物

| 模块 | 说明 |
|------|------|
| `frontend/` | Vite + React + TS 观战 UI |
| `RoundTable` | 12 人 CSS 圆桌 |
| `EventFeed` | 实时事件流 |
| `ViewModeToggle` | Public / God 切换 |
| `GameSetup` | POST /games 开局 |
| `api/routes.py` | WS `?view=public\|god` 服务端过滤 |
| `api/app.py` | CORS (localhost:5173) |
| `logging/replay.py` | 导出 `visibility_matches` |

## CC 采纳

- **P0** 修复 WS 全量泄露：replay + live 均 filter
- CORS + Vite dev proxy 双路径
- EventFeed 先于 RoundTable 验证数据流
- `useSpectatorState` reducer 按 event type 增量更新
- 切换视角重连 WS 并重放 filtered 历史

## 验收

```bash
pytest tests/ -q                    # 119 passed
cd frontend && npm run build

# 终端1
python -m aiwerewolf.api.server
# 终端2
cd frontend && npm run dev
```

浏览器 http://localhost:5173 → 开始新局 → 切换上帝/公共视角。
