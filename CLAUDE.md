# CLAUDE.md — AIWolfGame

本文件是 **Cursor Agent 与 Claude Code 的共享协作文档**，对项目全知。任何 Phase 开始前先读本文件 + 对应 `docs/` 章节；Phase 结束后更新「Current Phase」节。

---

## Project Overview

**AI 狼人杀** — 基于多 Agent 协作的多智能体博弈系统。课题核心：在严格信息隔离下，各角色 Agent 拥有独立目标、策略与行动空间，完成推理、发言与决策；对局引擎驱动回合流转与胜负裁决，输出结构化日志实现全程可观测。

| 项 | 说明 |
|----|------|
| 板子 | 12 人 **预女猎白**：4 狼 / 4 神（预言家、女巫、猎人、白痴）/ 4 平民 |
| 规则真相源 | [`rules.md`](rules.md) — 实现 **严格** 按此执行 |
| Agent 攻略 | [`game_guide.md`](game_guide.md) — **全文**注入每个 Agent system prompt（不裁剪），用于推理对手策略 |
| Agent 框架 | **LangGraph** — 图编排；engine 按 phase 唤醒节点 |
| 开发原则 | **TDD** — 每 Phase 不破坏已有测试 |
| 当前 Phase | **8 完成** — 全链路可观测（见 docs/phase-0 … phase-8.md） |

### 用户补充要求（必须遵守）

1. **信息管理**：法官全知；其余玩家 **仅** 能接触规则允许的信息。Agent **永不** 接收 `GameState`，仅 `PlayerView`。
2. **Agent 每轮结构化输出**（至少包含）：
   - `model` — 当前模型名（日志/观战可见）
   - `player_id` — **公开**
   - `role` — 本局身份（**私有**；写入私有日志，不广播给其他 Agent）
   - `speech` — 发言内容，**公开**
   - `demeanor` — 神态/动作，**公开**
   - `action` — 投票/技能等（按规则决定公开时机）
3. **文件管理**：模块分卷、互不干扰（见 Repository Layout）。
4. **观战 UI**（加分项）：GodView（法官全知）+ PublicView（迷雾）；纯 AI 或人机混战。
5. **协作**：Cursor 与 Claude Code 每 Phase 协商后实施（见 Collaboration Protocol）。
6. **配置**：用户可编辑项集中在 [`Config/`](Config/)；API Key 放 `Config/secrets.yaml`（gitignore），可安全 push GitHub。
7. **入口**：[`main.py`](main.py) 生产主流程；[`main_demo.py`](main_demo.py) 集成冒烟；单元测试在 [`tests/`](tests/)。
8. **数据结构**：Pydantic 模型在 [`schema/`](schema/)；引擎内部 runtime 类型在 `src/aiwerewolf/engine/`（Phase 1+）。
9. **LLM API**：信息隔离 **不依赖** 多个 API；同一 provider 即可，隔离靠 `PlayerView` + 独立会话。

### Agent Prompt 组成（Phase 6）

```
system = rules.md（硬约束）
       + game_guide.md（全文，inject_full_game_guide: true）
       + 输出 JSON  schema 说明
user   = 当前 PlayerView（该玩家可见的公开+私有信息）
```

- **不裁剪** game_guide：每个 Agent 需了解各阵营/角色可能策略。
- 攻略中守卫/狼王等 **不可当作本板子机制** 使用（rules.md 为准）。

### 进阶方向（基础版不实现，须预留扩展点）

| 方向 | 扩展方式 |
|------|----------|
| 1. 通用 Agent | 替换 `agents/` 实现；`engine/` + `protocol/` 不变 |
| 2. 评测 + 复盘 + Leaderboard | 消费 `logging/` 事件流 + `docs/event-schema.md` |
| 3. 自进化 Agent | 对局日志 → 分析 pipeline → prompt/策略版本化 → 再对局 |

---

## Repository Layout

```
AIWolfGame/
├── CLAUDE.md                    # ← 本文件（项目全知协作契约）
├── main.py                      # 生产主流程（读 Config/secrets.yaml）
├── main_demo.py                 # 集成冒烟（不读 secrets）
├── rules.md / game_guide.md
├── pyproject.toml
├── .gitignore                   # Config/secrets.yaml, logs/, ...
├── Config/                      # 用户配置（大写 C，按用户约定）
│   ├── default.yaml             # 可 commit 的默认配置
│   ├── secrets.yaml.example     # 模板
│   └── secrets.yaml             # gitignore — API Key 等
├── schema/                      # Pydantic I/O 契约
│   ├── config.py                # AppConfig + load_app_config()
│   ├── enums.py                 # Role, Phase, Camp, ...
│   ├── agent.py                 # AgentTurnOutput
│   ├── actions.py               # ActionPayload union
│   └── events.py                # GameEvent（日志/API）
├── docs/
├── src/aiwerewolf/
│   ├── engine/                  # 状态机、Rules（内部 dataclass，Phase 1+）
│   ├── roles/
│   ├── protocol/                # Visibility.for_player → PlayerView
│   ├── agents/                  # LangGraph
│   ├── prompts/                 # build_system_prompt（全文 game_guide）
│   ├── logging/
│   └── api/
├── frontend/
└── tests/                       # pytest 单元测试
    └── unit/
```

**分卷原则**

- `Config/` + `schema/config.py`：配置加载与校验
- `schema/`：边界 Pydantic 模型（config、agent 输出、events）
- `engine/` + `protocol/`：规则与信息隔离，**零 LLM 依赖**
- `agents/`：LangGraph；`prompts/` 构建 system prompt
- `main.py` / `main_demo.py`：薄入口，逻辑在 package 内

---

## Commands

```bash
pip install -e ".[dev]"

# 单元测试
pytest tests/

# 集成冒烟（不读 secrets）
python main_demo.py

# 生产主流程（读 Config/secrets.yaml 或 AIWEREWOLF_LLM_API_KEY）
python main.py
python main.py --config-dir Config --count 1
```

**Config 首次使用：**

```bash
copy Config\secrets.yaml.example Config\secrets.yaml   # Windows
# 编辑 Config/secrets.yaml 填入 api_key，该文件已在 .gitignore
```

Claude Code 在 WSL 中调用：`wsl --cd <RepoRoot> bash -lc "claude --print"`（RepoRoot 用 Windows 路径，勿硬编码盘符）。

---

## Code Style

- Python **3.11+**；type hints；**Pydantic v2** 用于 `schema/` 边界模型
- 引擎 runtime 状态（Phase 1+）用 **frozen dataclass**，不全部换成 Pydantic
- `pathlib.Path`；`logging` 替代 `print`
- 用户可配置项在 **`Config/`**，由 `schema.config.load_app_config()` 加载

---

## Architecture

### 数据流

```
GameState (法官全知，仅 engine)
    │
    ├─► Visibility.for_player(state, id) ──► PlayerView ──► Agent.act() ──► Action
    │
    ├─► Rules.validate_action / resolve / check_win
    │
    └─► Recorder.record(event) ──► EventLog ──► Replay / Spectator UI
```

### 核心边界

| 边界 | 输入 | 输出 |
|------|------|------|
| `Rules.validate_action(state, action)` | GameState, Action | bool + reason |
| `Rules.check_win(state)` | GameState | WinState \| None |
| `Visibility.for_player(state, player_id)` | GameState, int | PlayerView |
| `Agent.act(view)` | PlayerView | Action |
| `Recorder.record(event)` | GameEvent | append-only |

### 阶段流转

```
Night:  WolfTeam(vote_kill) → Witch(potion?) → Seer(check) → Hunter(status) → Idiot(confirm)
  ↓
Day:    [SheriffElection] → death_announce → speeches → vote → [PK?] → elimination
  ↓
Win check → continue or end
```

**狼人自爆**：白天任意时刻（含警长竞选、PK）可自爆 → 立即终止当天白天、**放逐投票作废** → 若自爆者为警长须先移徽 → 30s 遗言 **或** 夜间指刀（二选一）→ 天黑。

**狼人夜间刀口**：四狼讨论协商；**不允许平票**（平票则法官要求重议）；**空刀须四狼全体同意**。

**夜间结算顺序**（写入 `Rules.resolve_night()`，与 rules.md 一致）：

狼刀 → 女巫（解/毒，每晚最多一瓶，不可自救；**对灵魂状态白痴无效**）→ 预言家查验 → 猎人状态告知 → 白痴确认 → 检胜

**胜负同时触发**（rules.md「同时结算优先级」）：狼刀致死 → 检胜 → 猎人等死亡技能 → 再检胜

### 信息可见性（详见 docs/visibility.md）

| 信息 | 狼 | 预 | 女 | 猎 | 白 | 民 | 死者 |
|------|----|----|----|----|----|----|------|
| 自己的 role | Y | Y | Y | Y | Y | Y | Y |
| 狼队友 | Y | — | — | — | — | — | — |
| 验人结果 | — | Y | — | — | — | — | — |
| 昨夜刀口（救前） | — | — | Y | — | — | — | — |
| 猎人可开枪状态 | — | — | — | Y | — | — | — |
| 公开白天事件 | Y | Y | Y | Y | Y | Y | Y |
| 他人 role | — | — | — | — | — | — | — |

- **DeadView**：仅公开事件，**不能** 行动，**不能** 看全知 GameState
- **SpectatorView**：GodView（全知）或 PublicView（迷雾），可配置

### LangGraph Agent

- 每玩家一个子图；engine 按 `Phase` 唤醒
- 节点：`observe(view)` → `reason` → `emit_structured_output` → `validate_action`
- 狼人额外 `WolfTeamNode`（`WolfTeamView`，仅狼可见）
- LangGraph state **禁止** 挂载 `GameState`
- 狼队协商：四狼讨论；平票则法官要求重议（**不随机**）；空刀须四狼一致

### 观战 UI（Phase 8）

- **GodView**：全部身份、夜间行动、私有信息
- **PublicView**：等同存活玩家视野
- FastAPI + WebSocket 推送 EventLog；React 圆桌 UI
- 支持纯 AI 对战 / 人机混战（HumanAgent 实现同一接口）

---

## Confirmed Boundary Rules（Phase 0.5 已写入 rules.md）

| ID | 结论 |
|----|------|
| A1 | 狼刀**不允许平票**；平票则法官要求四狼重议；**空刀须四狼全体同意**；夜间可互相讨论 |
| A2 | 警长投票为字面 **1.5 票** |
| A3 | 白痴灵魂态**不可**被女巫毒 |
| A5 | 狼可当警长；警长死亡**须移徽**；自爆主要影响白天流程（跳过剩余白天/竞选） |
| A6 | 猎人开枪 **optional**（可不带人） |
| A7 | 自爆立即终止白天，**当天投票作废** |
| A8 | 狼刀→检胜→猎人技能→再检胜 |
| A10 | 无警长时从 1 号顺时针发言；AI 局不用「分钟相加」 |
| A11 | 第一夜无警长；第一个白天：天亮→警长竞选→公布死讯→发言投票 |
| A12 | 首夜不存在警长；**警长任意方式死亡均须移徽**（无遗言夜死于确认时移徽） |
| A13 | 本板子不含守卫/狼王；rules.md 已删除狼王 tips |

---

## TDD Phase Roadmap

| Phase | 内容 | 验收 |
|-------|------|------|
| 0 | CLAUDE.md + 骨架 + pyproject | import + pytest smoke |
| 0.5 | rules.md 歧义修订 | checklist |
| 1 | GameState, Phase, Rules, 胜负 | test_rules, test_win |
| 2 | Visibility / PlayerView | test_visibility 防泄露 |
| 3 | 角色技能、警长、自爆、白痴 | test_roles + fixtures |
| 4 | Protocol + RandomAgent | test_agent_protocol |
| 5 | GameLoop 集成 | 100 局 Random 无 crash |
| 6 | LangGraph + LLM Agent | 结构化输出合规 |
| 7 | EventLog + Replay + API | 回放一致 |
| 8 | React 观战 UI | God/Public 切换 |

---

## Collaboration Protocol (Cursor ↔ Claude Code)

1. **Phase 开始前**：Cursor 起草 `docs/phase-N.md` → Claude Code 只读 review → 双方敲定
2. **实现**：Cursor 写代码 + 测试
3. **Phase 结束**：Claude Code 验收 review → 更新本文件「Current Phase」
4. **rules.md 变更**：用户确认 → 同步 engine + tests

Claude Code 职责：架构 review、边界 case 审查、验收；**默认不直接改文件**（用户明确要求除外）。

---

## Key Files to Read Before Editing

| 任务 | 先读 |
|------|------|
| 规则/胜负/阶段 | rules.md |
| Agent prompt / 战术 | game_guide.md |
| 信息隔离 | docs/visibility.md |
| 日志/复盘/评测 | schema/events.py + docs/event-schema.md |
| 模块边界 | docs/architecture.md |

---

## Do Not

- 不向 Agent 泄露 `GameState` 或其他玩家的 `role`
- 不引入 rules.md 未定义的机制（**守卫、狼王** 等；**空刀** 仅当四狼全体同意时允许）
- 不在 Phase N 破坏 Phase N-1 已有测试
- 不让观战 UI 写入或影响对局逻辑
- game_guide 中「铜水/守卫/狼王」等 **不可** 当作本板子机制实现
- 不将 `Config/secrets.yaml` 或真实 API Key commit 到 Git

---

## Risks & Mitigations

| 风险 | 缓解 |
|------|------|
| LLM 结构化输出失败 | JSON mode + 重试一次 + Random 兜底 |
| 狼队协商死锁 | 法官要求重议；引擎可设最大协商轮次后判无效刀口 |
| 信息泄露 | test_visibility 为 CI 门禁 |
| LLM 成本 | RandomAgent 回归；LLM 仅 Phase 6+ |
| 对局过长 | 最大轮次上限（如 30 昼/夜） |
