"""Agent interface."""

from __future__ import annotations

from abc import ABC, abstractmethod

from aiwerewolf.protocol.views import PlayerView
from schema.agent import AgentTurnOutput


class Agent(ABC):
    """One agent per player — receives PlayerView only, never GameState."""

    @property
    @abstractmethod
    def model_name(self) -> str:
        ...

    @abstractmethod
    def act(self, view: PlayerView) -> AgentTurnOutput:
        ...
