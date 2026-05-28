"""Single-round day speech and last-words-only announce."""

from dataclasses import replace

from schema.agent import AgentTurnOutput, SpeechOrderAction
from schema.enums import DeathCause, Phase

from aiwerewolf.engine.loop import GameLoop
from tests.fixtures.pass_agent import PassAgent
from tests.fixtures.scenarios import standard_twelve_player_roles, state_from_roles


class _SheriffOrderAgent(PassAgent):
    def __init__(self, player_id: int, calls: list[int]) -> None:
        super().__init__(player_id)
        self._calls = calls

    def act(self, view):
        self._calls.append(view.player_id)
        if view.must_set_speech_order:
            return AgentTurnOutput(
                model=self.model_name,
                player_id=view.player_id,
                role=str(view.own_role),
                speech="",
                demeanor="",
                action=SpeechOrderAction(side="right", first_speaker_id=9),
            )
        return super().act(view)


class _RecordingAgent(PassAgent):
    def __init__(self, player_id: int, calls: list[int]) -> None:
        super().__init__(player_id)
        self._calls = calls

    def act(self, view):
        self._calls.append(view.player_id)
        return super().act(view)


def test_day_announce_only_dead_with_last_words_speak() -> None:
    calls: list[int] = []
    agents = {i: _RecordingAgent(i, calls) for i in range(1, 13)}
    loop = GameLoop(agents, max_rounds=1)
    state = state_from_roles(
        standard_twelve_player_roles(),
        phase=Phase.DAY_ANNOUNCE,
        round_number=1,
        alive=set(range(1, 13)) - {3, 7},
        death_announcements=(3, 7),
        pending_death_announcements=(3, 7),
    )
    state = replace(
        state,
        death_records=(
            (3, DeathCause.WOLF_KILL, 1),
            (7, DeathCause.WOLF_KILL, 1),
        ),
    )
    loop._day_announce(state)
    assert calls == [3, 7]


def test_day_announce_no_deaths_skips_agents() -> None:
    calls: list[int] = []
    agents = {i: _RecordingAgent(i, calls) for i in range(1, 13)}
    loop = GameLoop(agents, max_rounds=1)
    state = state_from_roles(
        standard_twelve_player_roles(),
        phase=Phase.DAY_ANNOUNCE,
        death_announcements=(),
    )
    next_state = loop._day_announce(state)
    assert calls == []
    assert next_state.phase == Phase.DAY_SPEECH


def test_day_speech_one_round_all_living() -> None:
    calls: list[int] = []
    agents = {i: _RecordingAgent(i, calls) for i in range(1, 13)}
    loop = GameLoop(agents, max_rounds=1)
    state = state_from_roles(
        standard_twelve_player_roles(),
        phase=Phase.DAY_SPEECH,
        sheriff_id=None,
        death_announcements=(),
    )
    loop._day_speeches(state)
    assert len(calls) == 12
    assert len(set(calls)) == 12


def test_sheriff_order_turn_not_counted_as_speech() -> None:
    calls: list[int] = []
    agents = {i: _RecordingAgent(i, calls) for i in range(1, 13)}
    agents[5] = _SheriffOrderAgent(5, calls)
    loop = GameLoop(agents, max_rounds=1)
    roles = standard_twelve_player_roles()
    state = state_from_roles(
        roles,
        phase=Phase.DAY_SPEECH,
        sheriff_id=5,
        alive=set(range(1, 13)),
    )
    # patch player 5 as sheriff
    from dataclasses import replace

    players = tuple(
        replace(p, is_sheriff=p.player_id == 5) for p in state.players
    )
    state = replace(state, players=players, sheriff_id=5)
    loop._day_speeches(state)
    assert calls[0] == 5
    assert calls[1] == 9
    assert calls.count(5) == 2  # order turn + speech at seat position
