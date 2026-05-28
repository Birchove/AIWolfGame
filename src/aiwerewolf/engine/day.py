"""Day phase resolution — sheriff, vote, self-destruct, idiot, hunter."""

from __future__ import annotations

from dataclasses import replace

from schema.enums import DeathCause, Phase, Role

from aiwerewolf.engine.rules import apply_win_if_any, eliminate_player
from aiwerewolf.engine.state import GameState, PlayerState, VoteRecord


def nominate_for_sheriff(state: GameState, player_id: int) -> GameState:
    player = state.player(player_id)
    if not player.alive:
        raise ValueError("dead player cannot nominate for sheriff")
    if state.sheriff_election_forbidden:
        raise ValueError("sheriff election forbidden")
    if player_id in state.sheriff_candidates:
        return state
    withdrawn = tuple(x for x in state.sheriff_withdrawn if x != player_id)
    candidates = tuple(sorted(set(state.sheriff_candidates + (player_id,))))
    return replace(state, sheriff_candidates=candidates, sheriff_withdrawn=withdrawn)


def withdraw_sheriff_candidacy(state: GameState, player_id: int) -> GameState:
    if player_id not in state.sheriff_candidates:
        raise ValueError("player is not a sheriff candidate")
    candidates = tuple(x for x in state.sheriff_candidates if x != player_id)
    withdrawn = tuple(sorted(set(state.sheriff_withdrawn + (player_id,))))
    return replace(state, sheriff_candidates=candidates, sheriff_withdrawn=withdrawn)


def cast_sheriff_vote(state: GameState, voter_id: int, target_id: int) -> GameState:
    voter = state.player(voter_id)
    if not voter.alive:
        raise ValueError("dead player cannot vote")
    if voter_id in state.sheriff_candidates:
        raise ValueError("active sheriff candidate cannot vote")
    if voter_id in state.sheriff_withdrawn:
        raise ValueError("withdrawn candidate cannot vote in sheriff election")
    if target_id not in state.sheriff_candidates:
        raise ValueError("target must be an active sheriff candidate")
    target = state.player(target_id)
    if not target.alive:
        raise ValueError("cannot vote for dead sheriff candidate")
    record = VoteRecord(voter_id=voter_id, target_id=target_id, weight=1.0)
    return replace(state, day_votes=state.day_votes + (record,))


def resolve_sheriff_election(state: GameState) -> GameState:
    winner, tied = _tally_votes(state.day_votes)
    cleared = replace(state, day_votes=(), sheriff_election_retry=False)
    if tied:
        return replace(
            cleared,
            pk_candidates=tied,
            phase=Phase.DAY_PK,
        )
    if winner is None:
        return cleared
    return _assign_sheriff(cleared, winner)


def resolve_sheriff_pk(state: GameState) -> GameState:
    winner, tied = _tally_votes(state.day_votes)
    cleared = replace(state, day_votes=(), pk_candidates=(), sheriff_election_retry=False)
    if tied or winner is None:
        return replace(cleared, sheriff_id=None, sheriff_election_forbidden=False)
    return _assign_sheriff(cleared, winner)


def cast_day_vote(state: GameState, voter_id: int, target_id: int | None) -> GameState:
    voter = state.player(voter_id)
    if not voter.alive:
        raise ValueError("dead player cannot vote")
    if voter.in_soul_state:
        raise ValueError("soul-state idiot cannot vote")
    weight = 1.5 if voter.is_sheriff else 1.0
    record = VoteRecord(voter_id=voter_id, target_id=target_id, weight=weight)
    return replace(state, day_votes=state.day_votes + (record,))


def resolve_day_vote(state: GameState) -> GameState:
    winner, tied = _tally_votes(state.day_votes)
    cleared = replace(state, day_votes=())
    if tied:
        return replace(cleared, pk_candidates=tied, phase=Phase.DAY_PK)
    if winner is None:
        return cleared
    return _resolve_elimination(cleared, winner)


def resolve_pk_vote(state: GameState) -> GameState:
    winner, tied = _tally_votes(state.day_votes)
    cleared = replace(state, day_votes=(), pk_candidates=())
    if tied or winner is None:
        return cleared
    return _resolve_elimination(cleared, winner)


def wolf_self_destruct(
    state: GameState,
    player_id: int,
    *,
    transfer_to: int | None = None,
) -> GameState:
    player = state.player(player_id)
    if player.role != Role.WOLF:
        raise ValueError("only wolves can self-destruct")
    if not player.alive:
        raise ValueError("dead wolf cannot self-destruct")

    s = state
    if player.is_sheriff or state.sheriff_id == player_id:
        if transfer_to is None:
            raise ValueError("sheriff wolf must transfer badge before self-destruct")
        s = transfer_sheriff_badge(s, player_id, transfer_to)

    s = eliminate_player(s, player_id, cause=DeathCause.OTHER)
    during_election = state.phase in {Phase.DAY_SHERIFF, Phase.DAY_PK}
    election_sd = (
        s.self_destruct_during_election + 1
        if during_election
        else s.self_destruct_during_election
    )
    forbidden = s.sheriff_election_forbidden or election_sd >= 2
    retry = during_election and election_sd == 1 and not forbidden

    s = replace(
        s,
        self_destruct_today=True,
        day_votes=(),
        pk_candidates=(),
        self_destruct_during_election=election_sd if during_election else s.self_destruct_during_election,
        sheriff_election_forbidden=forbidden,
        sheriff_election_retry=retry,
        sheriff_candidates=state.sheriff_candidates if during_election else (),
        sheriff_election_step="speech" if retry else state.sheriff_election_step,
    )
    return apply_win_if_any(s)


def idiot_reveal_on_vote(state: GameState, player_id: int) -> GameState:
    player = state.player(player_id)
    if player.role != Role.IDIOT:
        raise ValueError("only idiot can reveal on vote-out")
    if player.in_soul_state:
        raise ValueError("idiot already in soul state")
    new_players = tuple(
        replace(p, in_soul_state=True) if p.player_id == player_id else p
        for p in state.players
    )
    return replace(state, players=new_players, day_votes=())


def resolve_hunter_shoot(
    state: GameState,
    shooter_id: int,
    target_id: int | None,
) -> GameState:
    shooter = state.player(shooter_id)
    if shooter.role != Role.HUNTER:
        raise ValueError("only hunter can shoot")
    if not state.hunter_can_shoot:
        raise ValueError("hunter cannot shoot now")
    s = replace(state, hunter_can_shoot=False)
    if target_id is None:
        return s
    s = eliminate_player(s, target_id, cause=DeathCause.HUNTER_SHOOT)
    return apply_win_if_any(s)


def transfer_sheriff_badge(state: GameState, from_id: int, to_id: int) -> GameState:
    if state.sheriff_id != from_id:
        raise ValueError("from_id is not current sheriff")
    target = state.player(to_id)
    if not target.alive:
        raise ValueError("badge recipient must be alive")
    return _assign_sheriff(_clear_sheriff_flag(state, from_id), to_id)


def _resolve_elimination(state: GameState, player_id: int) -> GameState:
    target = state.player(player_id)
    if target.role == Role.IDIOT and not target.in_soul_state:
        s = idiot_reveal_on_vote(state, player_id)
        return apply_win_if_any(s)
    s = eliminate_player(state, player_id, cause=DeathCause.VOTE)
    if target.role == Role.HUNTER:
        s = replace(s, hunter_can_shoot=True)
    s = apply_win_if_any(s)
    return s


def _assign_sheriff(state: GameState, player_id: int) -> GameState:
    new_players = tuple(
        replace(p, is_sheriff=(p.player_id == player_id)) for p in state.players
    )
    return replace(
        state,
        players=new_players,
        sheriff_id=player_id,
        sheriff_candidates=(),
        sheriff_election_step="nominate",
    )


def _clear_sheriff_flag(state: GameState, player_id: int) -> GameState:
    new_players = tuple(
        replace(p, is_sheriff=False) if p.player_id == player_id else p
        for p in state.players
    )
    return replace(state, players=new_players, sheriff_id=None)


def _tally_votes(votes: tuple[VoteRecord, ...]) -> tuple[int | None, tuple[int, ...]]:
    if not votes:
        return None, ()
    scores: dict[int, float] = {}
    for v in votes:
        if v.target_id is None:
            continue
        scores[v.target_id] = scores.get(v.target_id, 0.0) + v.weight
    if not scores:
        return None, ()
    max_score = max(scores.values())
    top = tuple(sorted(pid for pid, s in scores.items() if s == max_score))
    if len(top) == 1:
        return top[0], ()
    return None, top


def _update_players(state: GameState, updates: dict[int, PlayerState]) -> GameState:
    new_players = tuple(updates.get(p.player_id, p) for p in state.players)
    return replace(state, players=new_players)
