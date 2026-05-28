"""Agents that always wolf-kill a fixed target — for engine kill-path tests."""

from __future__ import annotations

from schema.agent import AgentTurnOutput, PassAction, WolfKillAction
from schema.enums import Phase, Role

from aiwerewolf.agents.base import Agent
from aiwerewolf.protocol.views import PlayerView


class WolfKillAgent(Agent):
    def __init__(self, player_id: int, *, kill_target: int = 9) -> None:
        self._player_id = player_id
        self._kill_target = kill_target

    @property
    def model_name(self) -> str:
        return "WolfKillAgent"

    def act(self, view: PlayerView) -> AgentTurnOutput:
        if view.own_role == Role.WOLF and view.phase == Phase.NIGHT_WOLF:
            tgt = self._kill_target
            if tgt in view.living_player_ids and tgt not in view.wolf_teammates:
                action = WolfKillAction(target_id=tgt)
            else:
                action = WolfKillAction(
                    target_id=next(
                        pid
                        for pid in view.living_player_ids
                        if pid not in view.wolf_teammates and pid != view.player_id
                    )
                )
        else:
            action = PassAction()
        return AgentTurnOutput(
            model=self.model_name,
            player_id=view.player_id,
            role=str(view.own_role),
            speech="",
            demeanor="",
            action=action,
        )


def wolf_kill_agents(*, kill_target: int = 9) -> dict[int, WolfKillAgent]:
    return {i: WolfKillAgent(i, kill_target=kill_target) for i in range(1, 13)}
