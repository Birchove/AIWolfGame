# AI Werewolf — Spectator UI

React 观战页：12 人圆桌 + 事件流；**公共视角** / **上帝视角** 切换。

## 开发

终端 1 — API：

```bash
pip install -e ".[dev,api]"
python -m aiwerewolf.api.server
```

终端 2 — 前端：

```bash
cd frontend
npm install
npm run dev
```

浏览器打开 http://localhost:5173 ，点击「开始新局」。

Vite 将 `/games`、`/ws` 代理到 `http://127.0.0.1:8000`。

## 构建

```bash
cd frontend
npm run build
```

产物在 `frontend/dist/`。

## 视角

| 模式 | WebSocket |
|------|-----------|
| 公共 | `/ws/games/{id}?view=public` |
| 上帝 | `/ws/games/{id}?view=god` |

公共视角不显示身份与夜间私密行动。
