# Project Restructure — Cursor × Claude Code

**日期**：Phase 1 前架构调整  
**结论**：采纳用户指定布局 + CC 建议的边界分层。

## 布局

| 路径 | 职责 |
|------|------|
| `Config/` | 用户可编辑配置；`secrets.yaml` gitignore |
| `schema/` | Pydantic I/O 契约（config、agent 输出、events） |
| `src/aiwerewolf/` | 引擎/runtime（内部可用 frozen dataclass，Phase 1+） |
| `tests/` | pytest 单元测试 |
| `main.py` | 生产主流程（读 secrets） |
| `main_demo.py` | 集成冒烟（不读 secrets，RandomAgent Phase 5+） |

## Config 加载链

`Config/default.yaml` → `Config/secrets.yaml`（可选，浅合并）→ 环境变量 `AIWEREWOLF_LLM_API_KEY`

## schema vs engine

- **schema/**：边界序列化/校验（Pydantic）
- **engine/**：运行时热路径（dataclass，Phase 1 起）
- 不在 game loop 热路径中双向混用

## Agent Prompt

- `game_guide.md` **全文**注入每个 Agent system prompt（`inject_full_game_guide: true`）
- 信息隔离靠 `PlayerView`，**不需要**多个 API Key

## CC 备注

- `main_demo.py` 是 CLI 冒烟，复杂集成仍可放 `tests/integration/`（Phase 5+）
- 全文 game_guide token 成本较高，Phase 6 可考虑 prompt caching
