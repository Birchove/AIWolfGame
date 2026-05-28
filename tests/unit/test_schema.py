"""Pydantic schema validation tests."""

import pytest
from pydantic import ValidationError

from schema.agent import AgentTurnOutput, PassAction
from schema.config import AppConfig


def test_agent_turn_output_minimal() -> None:
    out = AgentTurnOutput(
        model="gpt-4o",
        player_id=3,
        role="seer",
        speech="我是好人",
        demeanor="平静环视",
        action=PassAction(),
    )
    assert out.player_id == 3
    assert out.action.type == "pass"


def test_app_config_defaults() -> None:
    cfg = AppConfig()
    assert cfg.board.wolves == 4
    assert cfg.llm.provider == "openai"


def test_agent_turn_output_invalid_player_id() -> None:
    with pytest.raises(ValidationError):
        AgentTurnOutput(model="x", player_id=0, role="wolf")
