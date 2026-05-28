"""Build agent prompts — rules + role-scoped game_guide + PlayerView."""

from __future__ import annotations

from pathlib import Path

from schema.config import AppConfig
from schema.enums import Role

from aiwerewolf.prompts.game_guide_sections import build_role_scoped_game_guide
from aiwerewolf.prompts.role_guide import build_role_action_guide


def load_text(repo_root: Path, relative: str) -> str:
    path = repo_root / relative
    return path.read_text(encoding="utf-8")


def build_system_prompt(
    cfg: AppConfig,
    *,
    repo_root: Path,
    role: Role,
    player_id: int,
    persona: str = "",
    prompt_nonce: str = "",
) -> str:
    """System prompt: full rules + scoped game_guide + role-specific soft guide."""
    rules = load_text(repo_root, cfg.prompts.rules_file)
    guide = ""
    if cfg.prompts.inject_full_game_guide:
        guide = load_text(repo_root, cfg.prompts.game_guide_file)
    elif cfg.prompts.inject_role_scoped_guide:
        guide = build_role_scoped_game_guide(
            repo_root=repo_root,
            guide_file=cfg.prompts.game_guide_file,
            role=role,
        )

    role_guide = build_role_action_guide(role)
    persona_block = f"\n## 你的人格（本局固定，必须体现）\n{persona}\n" if persona else ""
    nonce_block = (
        f"\n## 实例标识（勿引用）\n{prompt_nonce}\n" if prompt_nonce else ""
    )

    return f"""你是 {player_id} 号玩家，本局身份：{role.value}（仅你自己知道，按规则决定是否公开）。
{persona_block}{nonce_block}
## 硬规则（必须遵守）
{rules}

## 参考百科 — game_guide（推理对手用，不是你的行动脚本）
以下内容描述人类常见打法，**仅供你推断他人可能行为**。
- 不要机械照抄攻略中的「标准操作」
- 必须结合 user 消息中的 **public_speeches**（公开发言与神态 emoji）、**wolf_team_speeches**（仅狼可见）、当前阶段与 allowed_actions
- 用 **reasoning** 字段写下你的局势判断后再决定 speech 与 action
- **禁止复述**队友或对手的原话；用你的人格和口吻重新表达
- 若 wolf_team_speeches 中已有队友方案，你可以同意或提出不同刀口/分工，不要全员复读同一套话术

{guide}

## 你的角色行动倾向（软性参考，可偏离）
{role_guide}

## 输出要求
你必须返回 **JSON 对象**（json 格式），字段：
- model, player_id, role, speech, demeanor, demeanor_emojis, reasoning, action

### 公开字段（其他玩家可见）
- **speech**：本轮公开发言（狼夜协商时对队友说话也写入 speech，仅狼可见）
- **demeanor_emojis**：1 个或多个 emoji 组合表达神态（如 😏、🤔😰；无特殊情绪用 ["😐"]）

### 仅写入日志（其他玩家不可见）
- **demeanor**：完整神态动作描写
- **reasoning**：**角色内心理活动**（局势判断与盘算，禁止写 AI/JSON/上局游戏 等元叙述）

### 其他
- **role** 仅写入你的私有视角
- action 必须是当前阶段 allowed_actions 之一
- 狼人夜晚：先与队友 **speech 商议**（刀口、白天谁跳、是否倒钩），再 action.type=wolf_kill 投票；target 须为 living_player_ids 中的非狼
- 警长狼自爆时 action 须含 transfer_to
"""
