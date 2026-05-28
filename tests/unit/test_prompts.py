"""Prompt builder tests."""

from pathlib import Path

from schema.config import load_app_config
from schema.enums import Role

from aiwerewolf.prompts import build_system_prompt


def test_full_game_guide_in_system_prompt() -> None:
    root = Path(__file__).resolve().parents[2]
    cfg = load_app_config(root / "Config", use_secrets=False)
    prompt = build_system_prompt(cfg, repo_root=root, role=Role.WOLF, player_id=1)
    assert "硬规则" in prompt
    assert "参考百科" in prompt
    assert "狼" in prompt
    assert "public_speeches" in prompt
    # Scoped guide — not necessarily entire game_guide file
    full = (root / cfg.prompts.game_guide_file).read_text(encoding="utf-8")
    assert len(prompt) < len(full) + 8000
