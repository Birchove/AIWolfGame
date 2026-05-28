"""Sheriff badge transfer on death — no re-election."""

from dataclasses import replace

import pytest
from schema.enums import DeathCause, Phase

from aiwerewolf.engine import eliminate_player, transfer_sheriff_badge
from aiwerewolf.engine.day import cast_day_vote
from aiwerewolf.engine.interaction import has_last_words
from tests.fixtures.scenarios import standard_twelve_player_roles, state_from_roles


def test_eliminate_sheriff_sets_pending_not_election() -> None:
    from dataclasses import replace as dataclass_replace

    from aiwerewolf.engine.rules import _day_phases

    s = state_from_roles(
        standard_twelve_player_roles(),
        phase=Phase.NIGHT_IDIOT,
        sheriff_id=5,
        is_first_day=False,
        sheriff_elected_once=True,
    )
    s = dataclass_replace(s, players=tuple(
        dataclass_replace(p, is_sheriff=(p.player_id == 5)) for p in s.players
    ))
    s = eliminate_player(s, 5, cause=DeathCause.WOLF_KILL)
    assert s.sheriff_id is None
    assert s.sheriff_badge_pending_from == 5
    assert Phase.DAY_SHERIFF not in _day_phases(s)


def test_transfer_rejects_dead_recipient() -> None:
    s = state_from_roles(
        standard_twelve_player_roles(),
        phase=Phase.DAY_ANNOUNCE,
        sheriff_id=None,
        alive=set(range(1, 13)) - {5, 9},
    )
    s = replace(s, sheriff_badge_pending_from=5)
    with pytest.raises(ValueError, match="living"):
        transfer_sheriff_badge(s, 5, 9)


def test_cast_day_vote_rejects_dead_target() -> None:
    s = state_from_roles(
        standard_twelve_player_roles(),
        phase=Phase.DAY_VOTE,
        alive=set(range(1, 13)) - {3},
    )
    with pytest.raises(ValueError, match="dead"):
        cast_day_vote(s, 4, 3)


def test_night_death_sheriff_no_last_words_after_first_night() -> None:
    s = state_from_roles(
        standard_twelve_player_roles(),
        phase=Phase.DAY_ANNOUNCE,
        round_number=2,
        is_first_day=False,
    )
    s = eliminate_player(s, 5, cause=DeathCause.WOLF_KILL)
    assert not has_last_words(s, 5)
