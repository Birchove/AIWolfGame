# Phase 6 — 验收记录

**状态：完成**（Claude Code review 已采纳）

## 交付物

| 模块 | 说明 |
|------|------|
| `agents/llm/client.py` | OpenAI-compatible JSON mode client |
| `agents/llm/graph.py` | LangGraph: observe → llm → parse → validate → fallback |
| `agents/llm/agent.py` | `LLMAgent(Agent)` |
| `agents/llm/view_format.py` | `format_player_view` + `allowed_actions_for_phase` |
| `agents/human.py` | `HumanAgent` — stdin / injectable `input_fn` |
| `agents/factory.py` | `build_agents(mode=llm|random|human)` |
| `prompts/builder.py` | 输出要求含 **json** 关键字（OpenAI json_object） |
| `main.py` | `--mode` / `--seed` / GameLoop 接线 |
| `schema/config.py` | `LLMConfig.base_url` |
| `PlayerView` | `wolf_negotiation_round` / `wolf_prior_votes` 狼队协商反馈 |

## CC 采纳

- Slice 1 先加 `base_url` + view_format
- `PHASE_ALLOWED_ACTIONS` 与 dispatch 共享，prompt 生成 action 示例
- 狼队协商：`GameLoop` 每轮写入 `wolf_negotiation_votes`，狼人 view 可见上轮票型
- JSON mode：`json_object` + system prompt 含 "json"
- 非法 action：重试 1 次 → `PassAction` 兜底
- Phase 6 用 `llm.api_key`；`ProvidersConfig` 留 Phase 7+

## CC 留 Phase 7+

- 警长夜间死亡移徽 agent 协议
- `IdiotRevealAction` 清理
- 完整 event 流 / replay

## 验收

```bash
pip install -e ".[dev,agents]"
pytest tests/ -q                    # 103 passed
python main.py --mode random --count 3
python main.py --count 1            # 需 Config/secrets.yaml
```
