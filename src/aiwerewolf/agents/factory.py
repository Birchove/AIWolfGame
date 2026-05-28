"""Build LLM player agents from AppConfig."""

from __future__ import annotations

from pathlib import Path

from schema.config import AppConfig

from aiwerewolf.agents.base import Agent
from aiwerewolf.agents.llm.agent import LLMAgent


def build_agents(cfg: AppConfig, *, repo_root: Path) -> dict[int, Agent]:
    return {
        i: LLMAgent(player_id=i, cfg=cfg, repo_root=repo_root)
        for i in range(1, 13)
    }
