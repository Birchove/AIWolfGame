"""Agent factory tests."""

from pathlib import Path

from schema.config import load_app_config

from aiwerewolf.agents.factory import build_agents
from aiwerewolf.agents.llm.agent import LLMAgent


def test_build_llm_agents() -> None:
    repo = Path(__file__).resolve().parents[2]
    cfg = load_app_config(repo / "Config", use_secrets=True)
    agents = build_agents(cfg, repo_root=repo)
    assert len(agents) == 12
    assert all(isinstance(a, LLMAgent) for a in agents.values())
