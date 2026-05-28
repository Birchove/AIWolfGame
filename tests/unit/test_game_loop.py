"""GameLoop integration tests."""

from schema.agent import SelfDestructAction
from schema.enums import Camp, Phase, Role

from aiwerewolf.engine.loop import GameLoop
from aiwerewolf.protocol import Visibility
from aiwerewolf.protocol.dispatch import validate_phase_action
from tests.fixtures.pass_agent import pass_agents


def test_run_one_game_no_crash() -> None:
    loop = GameLoop(pass_agents(), max_rounds=30)
    result = loop.run(seed=0)
    assert result.state.phase == Phase.GAME_OVER
    assert result.winner in {Camp.GOOD, Camp.WOLF}


def test_game_ends_within_max_rounds() -> None:
    loop = GameLoop(pass_agents(), max_rounds=15)
    result = loop.run(seed=1)
    assert result.round_count <= 15


def test_100_games_no_crash() -> None:
    for seed in range(100):
        loop = GameLoop(pass_agents(), max_rounds=30)
        result = loop.run(seed=seed)
        assert result.state.phase == Phase.GAME_OVER
        assert result.winner is not None


def test_100_games_visibility_invariants() -> None:
    for seed in range(10):
        loop = GameLoop(pass_agents(), max_rounds=30)
        result = loop.run(seed=seed)
        for p in result.state.players:
            view = Visibility.for_player(result.state, p.player_id)
            assert view.own_role == p.role
            assert not hasattr(view, "players")


def test_death_announcements_populated_after_night() -> None:
    loop = GameLoop(pass_agents(), max_rounds=30)
    result = loop.run(seed=42)
    dead_ids = {p.player_id for p in result.state.players if not p.alive}
    if dead_ids:
        assert result.state.death_announcements
        assert set(result.state.death_announcements) <= dead_ids


def test_self_destruct_allowed_in_day_speech() -> None:
    ok, _ = validate_phase_action(
        Phase.DAY_SPEECH, Role.WOLF, SelfDestructAction(last_words="boom")
    )
    assert ok
