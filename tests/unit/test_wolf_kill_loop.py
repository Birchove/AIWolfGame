"""Wolf kill integration through GameLoop."""

from aiwerewolf.engine.loop import GameLoop
from tests.fixtures.kill_agent import wolf_kill_agents


def test_unanimous_wolf_kill_eliminates_target() -> None:
    loop = GameLoop(wolf_kill_agents(kill_target=9), max_rounds=3)
    result = loop.run(seed=0)
    assert not result.state.player(9).alive


def test_wolf_kill_survives_second_night() -> None:
    """Regression: killing dead target must not crash the game loop."""
    loop = GameLoop(wolf_kill_agents(kill_target=9), max_rounds=5)
    result = loop.run(seed=0)
    assert result.state.phase.value == "game_over" or result.round_count >= 2
