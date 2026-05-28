"""LangGraph agent turn: observe → llm → parse → validate."""

from __future__ import annotations

from typing import Any, Callable, TypedDict

from schema.agent import AgentTurnOutput, PassAction, WolfKillAction
from schema.enums import Phase, Role

from aiwerewolf.agents.llm.view_format import format_player_view, validate_output_for_view
from aiwerewolf.protocol.views import PlayerView

_MAX_RETRIES = 1


class AgentGraphState(TypedDict):
    view: PlayerView
    system_prompt: str
    user_message: str
    raw_response: str
    output: AgentTurnOutput | None
    error: str
    retry_count: int
    model_name: str


def _observe(state: AgentGraphState) -> AgentGraphState:
    user_message = format_player_view(state["view"])
    if state.get("error"):
        user_message += (
            f"\n\nPrevious attempt failed: {state['error']}. "
            "Return valid JSON with an allowed action."
        )
    return {**state, "user_message": user_message, "error": ""}


def _make_call_llm(chat_fn: Callable[..., str]) -> Callable[[AgentGraphState], AgentGraphState]:
    def call_llm(state: AgentGraphState) -> AgentGraphState:
        raw = chat_fn(
            system_prompt=state["system_prompt"],
            user_message=state["user_message"],
        )
        return {**state, "raw_response": raw}

    return call_llm


def _parse(state: AgentGraphState) -> AgentGraphState:
    view = state["view"]
    try:
        output = AgentTurnOutput.model_validate_json(state["raw_response"])
        output = output.model_copy(
            update={
                "model": state["model_name"],
                "player_id": view.player_id,
                "role": str(view.own_role),
            }
        )
        return {**state, "output": output, "error": ""}
    except Exception as exc:
        return {**state, "output": None, "error": f"parse error: {exc}"}


def _validate(state: AgentGraphState) -> AgentGraphState:
    output = state.get("output")
    if output is None:
        return state
    ok, reason = validate_output_for_view(state["view"], output)
    if ok:
        return {**state, "error": ""}
    return {**state, "output": None, "error": reason}


def _should_retry(state: AgentGraphState) -> str:
    if state.get("output") is not None:
        return "done"
    if state.get("retry_count", 0) < _MAX_RETRIES:
        return "retry"
    return "done"


def _fallback(state: AgentGraphState) -> AgentGraphState:
    if state.get("output") is not None:
        return state
    view = state["view"]
    action = PassAction()
    if view.own_role == Role.WOLF and view.phase == Phase.NIGHT_WOLF:
        candidates = [
            pid
            for pid in view.living_player_ids
            if pid not in view.wolf_teammates and pid != view.player_id
        ]
        if candidates:
            action = WolfKillAction(target_id=candidates[0])
    return {
        **state,
        "output": AgentTurnOutput(
            model=state["model_name"],
            player_id=view.player_id,
            role=str(view.own_role),
            speech="",
            demeanor="",
            demeanor_emojis=["😐"],
            reasoning="",
            action=action,
        ),
    }


def _bump_retry(state: AgentGraphState) -> AgentGraphState:
    return {**state, "retry_count": state.get("retry_count", 0) + 1}


def build_agent_graph(chat_fn: Callable[..., str]) -> Any:
    try:
        from langgraph.graph import END, StateGraph
    except ImportError as exc:
        raise ImportError(
            "langgraph required — pip install -e '.[agents]'"
        ) from exc

    graph = StateGraph(AgentGraphState)
    graph.add_node("observe", _observe)
    graph.add_node("call_llm", _make_call_llm(chat_fn))
    graph.add_node("parse", _parse)
    graph.add_node("validate", _validate)
    graph.add_node("fallback", _fallback)
    graph.add_node("bump_retry", _bump_retry)

    graph.set_entry_point("observe")
    graph.add_edge("observe", "call_llm")
    graph.add_edge("call_llm", "parse")
    graph.add_edge("parse", "validate")
    graph.add_conditional_edges(
        "validate",
        _should_retry,
        {"retry": "bump_retry", "done": "fallback"},
    )
    graph.add_edge("bump_retry", "observe")
    graph.add_edge("fallback", END)
    return graph.compile()
