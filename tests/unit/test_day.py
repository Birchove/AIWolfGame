"""Day phase tests (Phase 3 slice 2 — CC checklist)."""

import pytest
from schema.enums import Phase, Role

from aiwerewolf.engine import (
    cast_day_vote,
    cast_sheriff_vote,
    eliminate_player,
    next_phase,
    nominate_for_sheriff,
    resolve_day_vote,
    resolve_hunter_shoot,
    resolve_pk_vote,
    resolve_sheriff_election,
    resolve_sheriff_pk,
    transfer_sheriff_badge,
    withdraw_sheriff_candidacy,
    wolf_self_destruct,
)
from schema.enums import DeathCause
from tests.fixtures.scenarios import state_from_roles, standard_twelve_player_roles


def _state(**kwargs):
    return state_from_roles(standard_twelve_player_roles(), phase=Phase.DAY_SHERIFF, **kwargs)


def test_sheriff_election_simple_winner() -> None:
    s = _state()
    s = nominate_for_sheriff(s, 5)
    s = cast_sheriff_vote(s, 9, 5)
    s = cast_sheriff_vote(s, 10, 5)
    s = resolve_sheriff_election(s)
    assert s.sheriff_id == 5
    assert s.player(5).is_sheriff


def test_sheriff_election_pk_then_winner() -> None:
    s = _state()
    for pid in (5, 6):
        s = nominate_for_sheriff(s, pid)
    s = cast_sheriff_vote(s, 9, 5)
    s = cast_sheriff_vote(s, 10, 6)
    s = resolve_sheriff_election(s)
    assert s.phase == Phase.DAY_PK
    assert s.pk_candidates == (5, 6)
    s = cast_sheriff_vote(s, 11, 5)
    s = cast_sheriff_vote(s, 12, 5)
    s = resolve_sheriff_pk(s)
    assert s.sheriff_id == 5


def test_sheriff_election_pk_tie_loses_badge() -> None:
    s = _state()
    for pid in (5, 6):
        s = nominate_for_sheriff(s, pid)
    s = cast_sheriff_vote(s, 9, 5)
    s = cast_sheriff_vote(s, 10, 6)
    s = resolve_sheriff_election(s)
    s = cast_sheriff_vote(s, 11, 5)
    s = cast_sheriff_vote(s, 12, 6)
    s = resolve_sheriff_pk(s)
    assert s.sheriff_id is None


def test_sheriff_candidate_withdraw_cannot_vote() -> None:
    s = _state()
    s = nominate_for_sheriff(s, 5)
    s = nominate_for_sheriff(s, 6)
    s = withdraw_sheriff_candidacy(s, 6)
    with pytest.raises(ValueError, match="withdrawn"):
        cast_sheriff_vote(s, 6, 5)


def test_sheriff_1_5_vote_in_day_vote() -> None:
    s = state_from_roles(standard_twelve_player_roles(), phase=Phase.DAY_VOTE, sheriff_id=5)
    s = _assign_sheriff_via_players(s, 5)
    s = cast_day_vote(s, 5, 1)
    s = cast_day_vote(s, 9, 1)
    winner, tied = _tally(s.day_votes)
    assert tied == ()
    assert winner == 1


def test_sheriff_badge_transfer_on_death() -> None:
    s = state_from_roles(standard_twelve_player_roles(), sheriff_id=5)
    s = _assign_sheriff_via_players(s, 5)
    s = transfer_sheriff_badge(s, 5, 9)
    assert s.sheriff_id == 9
    assert s.player(9).is_sheriff
    assert not s.player(5).is_sheriff


def test_wolf_self_destruct_skips_day() -> None:
    s = state_from_roles(standard_twelve_player_roles(), phase=Phase.DAY_SPEECH)
    s = cast_day_vote(s, 9, 1)
    s = wolf_self_destruct(s, 1)
    assert s.self_destruct_today is True
    assert s.day_votes == ()
    s = next_phase(s)
    assert s.phase == Phase.NIGHT_WOLF
    assert not s.self_destruct_today


def test_wolf_self_destruct_as_sheriff_must_transfer() -> None:
    s = _state()
    s = nominate_for_sheriff(s, 1)
    s = cast_sheriff_vote(s, 9, 1)
    s = resolve_sheriff_election(s)
    with pytest.raises(ValueError, match="transfer"):
        wolf_self_destruct(s, 1)
    s = wolf_self_destruct(s, 1, transfer_to=9)
    assert not s.player(1).alive
    assert s.sheriff_id == 9


def test_two_self_destructs_forbid_sheriff_election() -> None:
    s = _state()
    s = nominate_for_sheriff(s, 1)
    s = wolf_self_destruct(s, 1)
    assert s.sheriff_election_retry is True
    s = state_from_roles(
        standard_twelve_player_roles(),
        phase=Phase.DAY_SHERIFF,
        sheriff_election_retry=True,
        self_destruct_during_election=1,
    )
    s = nominate_for_sheriff(s, 2)
    s = wolf_self_destruct(s, 2)
    assert s.sheriff_election_forbidden is True


def test_day_vote_eliminates_winner() -> None:
    s = state_from_roles(standard_twelve_player_roles(), phase=Phase.DAY_VOTE)
    for pid in range(5, 13):
        s = cast_day_vote(s, pid, 1)
    s = resolve_day_vote(s)
    assert not s.player(1).alive


def test_day_vote_pk_tie_peace_day() -> None:
    s = state_from_roles(standard_twelve_player_roles(), phase=Phase.DAY_VOTE)
    s = cast_day_vote(s, 5, 1)
    s = cast_day_vote(s, 6, 2)
    s = resolve_day_vote(s)
    assert s.phase == Phase.DAY_PK
    s = cast_day_vote(s, 7, 1)
    s = cast_day_vote(s, 8, 2)
    s = resolve_pk_vote(s)
    assert s.player(1).alive and s.player(2).alive


def test_idiot_reveal_on_vote_immune_soul_state() -> None:
    s = state_from_roles(standard_twelve_player_roles(), phase=Phase.DAY_VOTE)
    for pid in range(5, 13):
        if pid == 8:
            continue
        s = cast_day_vote(s, pid, 8)
    s = resolve_day_vote(s)
    idiot = s.player(8)
    assert idiot.alive
    assert idiot.in_soul_state


def test_hunter_shoot_after_vote_death() -> None:
    s = state_from_roles(standard_twelve_player_roles(), phase=Phase.DAY_VOTE)
    for pid in range(5, 13):
        if pid == 7:
            continue
        s = cast_day_vote(s, pid, 7)
    s = resolve_day_vote(s)
    assert s.hunter_can_shoot
    s = resolve_hunter_shoot(s, 7, 1)
    assert not s.player(1).alive


def _assign_sheriff_via_players(state, sheriff_id: int):
    from dataclasses import replace

    players = tuple(
        replace(p, is_sheriff=(p.player_id == sheriff_id)) for p in state.players
    )
    return replace(state, players=players, sheriff_id=sheriff_id)


def _tally(votes):
    from aiwerewolf.engine.day import _tally_votes

    return _tally_votes(votes)
