"""LLMAgent — LangGraph-backed Agent implementation."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from schema.config import AppConfig

from aiwerewolf.agents.base import Agent
from aiwerewolf.agents.llm.client import chat_completion, resolve_base_url
from aiwerewolf.agents.llm.graph import build_agent_graph
from aiwerewolf.agents.model_assign import PlayerLLMProfile
from aiwerewolf.prompts.builder import build_system_prompt
from aiwerewolf.protocol.views import PlayerView
from schema.agent import AgentTurnOutput


class LLMAgent(Agent):
    def __init__(
        self,
        *,
        player_id: int,
        cfg: AppConfig,
        repo_root: Path,
        graph: Any | None = None,
    ) -> None:
        self._player_id = player_id
        self._cfg = cfg
        self._repo_root = repo_root
        self._base_url = resolve_base_url(cfg.llm.provider, cfg.llm.base_url)
        self._graph = graph or build_agent_graph(self._chat)
        self._profile: PlayerLLMProfile | None = None

    def bind_game(self, profile: PlayerLLMProfile) -> None:
        self._profile = profile

    @property
    def model_name(self) -> str:
        if self._profile is not None:
            return self._profile.model
        return self._cfg.llm.model

    def act(self, view: PlayerView) -> AgentTurnOutput:
        nonce = self._profile.prompt_nonce if self._profile else ""
        system_prompt = build_system_prompt(
            self._cfg,
            repo_root=self._repo_root,
            role=view.own_role,
            player_id=view.player_id,
            persona=view.persona,
            prompt_nonce=nonce,
        )
        result = self._graph.invoke(
            {
                "view": view,
                "system_prompt": system_prompt,
                "user_message": "",
                "raw_response": "",
                "output": None,
                "error": "",
                "retry_count": 0,
                "model_name": self.model_name,
            }
        )
        output = result["output"]
        assert output is not None
        return output

    def _chat(self, *, system_prompt: str, user_message: str) -> str:
        llm = self._cfg.llm
        if self._profile is not None:
            temperature = self._profile.temperature
            top_p = self._profile.top_p
            frequency_penalty = self._profile.frequency_penalty
            presence_penalty = self._profile.presence_penalty
            model = self._profile.model
        else:
            temperature = llm.temperature
            top_p = llm.top_p
            frequency_penalty = llm.frequency_penalty
            presence_penalty = llm.presence_penalty
            model = llm.model
        return chat_completion(
            base_url=self._base_url,
            api_key=self._cfg.llm_api_key(),
            model=model,
            system_prompt=system_prompt,
            user_message=user_message,
            temperature=temperature,
            top_p=top_p,
            frequency_penalty=frequency_penalty,
            presence_penalty=presence_penalty,
            timeout_sec=self._cfg.agents.default_timeout_sec,
        )
