"""Sheriff election sub-flow integration."""

from schema.agent import AgentTurnOutput, PassAction, SheriffRunAction, VoteAction
from schema.enums import Phase

from aiwerewolf.engine.loop import GameLoop
from aiwerewolf.engine.setup import create_game
from aiwerewolf.logging.recorder import Recorder
from aiwerewolf.agents.base import Agent
from aiwerewolf.protocol.views import PlayerView


class _SheriffScriptAgent(Agent):
    def __init__(self, player_id: int, script: list) -> None:
        self._player_id = player_id
        self._script = list(script)

    @property
    def model_name(self) -> str:
        return "Script"

    def act(self, view: PlayerView) -> AgentTurnOutput:
        action = self._script.pop(0) if self._script else PassAction()
        return AgentTurnOutput(
            model=self.model_name,
            player_id=view.player_id,
            role=str(view.own_role),
            speech=f"P{view.player_id} speech",
            action=action,
        )


def test_sheriff_election_logs_nominate_and_result() -> None:
    rec = Recorder(game_id="sheriff-flow")
    agents: dict[int, Agent] = {
        i: _SheriffScriptAgent(i, [PassAction()])
        for i in range(1, 13)
    }
    agents[5] = _SheriffScriptAgent(5, [SheriffRunAction(), PassAction(), PassAction()])
    agents[6] = _SheriffScriptAgent(6, [SheriffRunAction(), PassAction(), PassAction()])
    agents[9] = _SheriffScriptAgent(
        9, [PassAction(), PassAction(), VoteAction(target_id=5)]
    )
    agents[10] = _SheriffScriptAgent(
        10, [PassAction(), PassAction(), VoteAction(target_id=5)]
    )

    state = create_game(seed=0)
    state = state.with_phase(Phase.DAY_SHERIFF)
    loop = GameLoop(agents, max_rounds=5, recorder=rec)
    loop.run(seed=0)
    types = [e.type for e in rec.event_log.events]
    assert "sheriff_nominate" in types
    assert "sheriff_nomination_complete" in types
    assert "sheriff_vote_result" in types or any(
        e.type == "sheriff_elected" for e in rec.event_log.events
    )
