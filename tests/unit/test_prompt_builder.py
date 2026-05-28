"""Prompt builder tests."""

from pathlib import Path

from schema.config import AppConfig
from schema.enums import Role

from aiwerewolf.prompts.builder import build_system_prompt


def test_system_prompt_contains_json_and_scoped_guide() -> None:
    repo = Path(__file__).resolve().parents[2]
    cfg = AppConfig()
    prompt = build_system_prompt(
        cfg, repo_root=repo, role=Role.SEER, player_id=5, prompt_nonce="abc123"
    )
    assert "json" in prompt.lower()
    assert "5 号玩家" in prompt
    assert "预言家" in prompt or "seer" in prompt.lower()
    assert "abc123" in prompt
    if cfg.prompts.inject_role_scoped_guide:
        assert "术语" in prompt or "金水" in prompt
