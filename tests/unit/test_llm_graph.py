"""Tests for LLM agent graph (mock client)."""

import json

from schema.agent import PassAction, VoteAction
from schema.enums import Phase, Role

from aiwerewolf.agents.llm.graph import build_agent_graph
from aiwerewolf.protocol.views import PlayerView


def _view() -> PlayerView:
    return PlayerView(
        player_id=3,
        own_role=Role.VILLAGER,
        phase=Phase.DAY_VOTE,
        round_number=1,
        is_alive=True,
        is_sheriff=False,
        in_soul_state=False,
        living_player_ids=(1, 2, 3),
        dead_player_ids=(),
        sheriff_id=None,
        public_events=(),
    )


def test_graph_parses_valid_json() -> None:
    calls: list[str] = []

    def mock_chat(*, system_prompt: str, user_message: str) -> str:
        calls.append(user_message)
        return json.dumps(
            {
                "model": "test",
                "player_id": 3,
                "role": "villager",
                "speech": "hello",
                "demeanor": "calm",
                "action": {"type": "vote", "target_id": 1},
            }
        )

    graph = build_agent_graph(mock_chat)
    result = graph.invoke(
        {
            "view": _view(),
            "system_prompt": "system json test",
            "user_message": "",
            "raw_response": "",
            "output": None,
            "error": "",
            "retry_count": 0,
            "model_name": "gpt-test",
        }
    )
    assert result["output"] is not None
    assert isinstance(result["output"].action, VoteAction)
    assert result["output"].model == "gpt-test"
    assert len(calls) == 1


def test_graph_retry_exhausted_returns_pass() -> None:
    def bad_chat(*, system_prompt: str, user_message: str) -> str:
        return json.dumps(
            {
                "model": "x",
                "player_id": 3,
                "role": "villager",
                "speech": "",
                "demeanor": "",
                "action": {"type": "wolf_kill", "target_id": 1},
            }
        )

    graph = build_agent_graph(bad_chat)
    result = graph.invoke(
        {
            "view": _view(),
            "system_prompt": "json",
            "user_message": "",
            "raw_response": "",
            "output": None,
            "error": "",
            "retry_count": 0,
            "model_name": "gpt-test",
        }
    )
    assert isinstance(result["output"].action, PassAction)
