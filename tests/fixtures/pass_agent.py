"""Deterministic stub agent for unit tests (not used in production)."""

from __future__ import annotations

from schema.agent import AgentTurnOutput, PassAction, SheriffTransferAction, SpeechOrderAction

from aiwerewolf.agents.base import Agent
from aiwerewolf.protocol.views import PlayerView


class PassAgent(Agent):
    """Always passes — fast engine/protocol tests without LLM or RNG."""

    def __init__(self, player_id: int = 1) -> None:
        self._player_id = player_id

    @property
    def model_name(self) -> str:
        return "PassAgent"

    def act(self, view: PlayerView) -> AgentTurnOutput:
        action: PassAction | SpeechOrderAction | SheriffTransferAction = PassAction()
        if view.must_transfer_sheriff_badge:
            living = [pid for pid in view.living_player_ids if pid != view.player_id]
            if living:
                action = SheriffTransferAction(transfer_to=living[0])
        elif view.must_set_speech_order:
            action = SpeechOrderAction(side="right")
        return AgentTurnOutput(
            model=self.model_name,
            player_id=view.player_id,
            role=str(view.own_role),
            speech="",
            demeanor="neutral",
            action=action,
        )


def pass_agents() -> dict[int, PassAgent]:
    return {i: PassAgent(i) for i in range(1, 13)}
