"""Persona assignment and prompt injection."""

from pathlib import Path

from schema.config import AppConfig
from schema.enums import Role

from aiwerewolf.agents.persona import assign_personas
from aiwerewolf.engine.setup import create_game
from aiwerewolf.prompts.builder import build_system_prompt
from aiwerewolf.prompts.role_guide import build_role_action_guide
from aiwerewolf.protocol.visibility import Visibility


def test_assign_personas_deterministic_by_seed() -> None:
    a = assign_personas(seed=42)
    b = assign_personas(seed=42)
    c = assign_personas(seed=99)
    assert a == b
    assert a != c
    assert len(a) == 12
    assert all(isinstance(v, str) and v for v in a.values())


def test_persona_flows_to_player_view() -> None:
    state = create_game(seed=7)
    view = Visibility.for_player(state, 1)
    assert view.persona
    assert view.persona == state.persona_for(1)


def test_persona_in_system_prompt() -> None:
    repo = Path(__file__).resolve().parents[2]
    cfg = AppConfig()
    persona = assign_personas(seed=0)[5]
    prompt = build_system_prompt(
        cfg,
        repo_root=repo,
        role=Role.SEER,
        player_id=5,
        persona=persona,
    )
    assert persona in prompt
    assert "你的人格" in prompt


def test_role_guide_in_system_prompt() -> None:
    repo = Path(__file__).resolve().parents[2]
    cfg = AppConfig()
    guide = build_role_action_guide(Role.WOLF)
    prompt = build_system_prompt(
        cfg, repo_root=repo, role=Role.WOLF, player_id=1
    )
    assert guide.strip() in prompt


def test_game_guide_framed_as_reference_not_script() -> None:
    repo = Path(__file__).resolve().parents[2]
    cfg = AppConfig()
    prompt = build_system_prompt(
        cfg, repo_root=repo, role=Role.VILLAGER, player_id=9
    )
    assert "参考百科" in prompt
    assert "不是你的行动脚本" in prompt
    assert "不要机械照抄" in prompt
    assert "public_speeches" in prompt
