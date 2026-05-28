"""Information isolation — single choke-point for agent-facing views."""

from __future__ import annotations

from schema.enums import Phase, Role

from aiwerewolf.engine.interaction import has_last_words, may_act_in_phase
from aiwerewolf.engine.state import GameState
from aiwerewolf.protocol.views import PlayerView, PublicEventSummary, SeerCheckResult


class Visibility:
    @staticmethod
    def for_player(state: GameState, player_id: int) -> PlayerView:
        player = state.player(player_id)
        living_ids = tuple(p.player_id for p in state.living_players())
        dead_ids = tuple(p.player_id for p in state.players if not p.alive)
        public_events = _derive_public_events(state)

        wolf_teammates: tuple[int, ...] = ()
        seer_checks: tuple[SeerCheckResult, ...] = ()
        witch_night_death: int | None = None
        witch_antidote_available = True
        witch_poison_available = True
        wolf_negotiation_round: int = 0
        wolf_prior_votes: tuple[tuple[int, int | None], ...] = ()
        hunter_can_shoot = False
        wolf_team_speeches: tuple = ()

        public_speeches = tuple(
            s for s in state.speech_log if s.audience == "public"
        )

        sheriff_candidates: tuple[int, ...] = ()
        sheriff_withdrawn: tuple[int, ...] = ()
        sheriff_election_step = state.sheriff_election_step
        is_sheriff_candidate = False
        is_sheriff_withdrawn = False
        is_sheriff_voter = False

        if state.phase == Phase.DAY_SHERIFF and player.counts_as_alive_for_win():
            sheriff_candidates = state.sheriff_candidates
            sheriff_withdrawn = state.sheriff_withdrawn
            is_sheriff_candidate = player_id in sheriff_candidates
            is_sheriff_withdrawn = player_id in sheriff_withdrawn
            if sheriff_election_step == "vote":
                blocked = set(sheriff_candidates) | set(sheriff_withdrawn)
                is_sheriff_voter = (
                    player_id not in blocked and not player.in_soul_state
                )

        if player.counts_as_alive_for_win():
            if player.role == Role.WOLF:
                wolf_teammates = tuple(
                    p.player_id
                    for p in state.players
                    if p.is_wolf() and p.player_id != player_id
                )
                wolf_team_speeches = tuple(
                    s for s in state.speech_log if s.audience == "wolf_only"
                )
                if state.phase == Phase.NIGHT_WOLF:
                    wolf_negotiation_round = state.wolf_negotiation_round
                    wolf_prior_votes = state.wolf_negotiation_votes
            if player.role == Role.SEER:
                seer_checks = state.seer_checks
            if player.role == Role.WITCH and state.phase == Phase.NIGHT_WITCH:
                witch_night_death = state.wolf_kill_target
                witch_antidote_available = state.witch_antidote_available
                witch_poison_available = state.witch_poison_available
            if player.role == Role.HUNTER:
                hunter_can_shoot = state.hunter_can_shoot

        return PlayerView(
            player_id=player_id,
            own_role=player.role,
            phase=state.phase,
            round_number=state.round_number,
            is_alive=player.alive,
            is_sheriff=player.is_sheriff,
            in_soul_state=player.in_soul_state,
            living_player_ids=living_ids,
            dead_player_ids=dead_ids,
            sheriff_id=state.sheriff_id,
            public_events=public_events,
            wolf_teammates=wolf_teammates,
            seer_checks=seer_checks,
            witch_night_death=witch_night_death,
            witch_antidote_available=witch_antidote_available,
            witch_poison_available=witch_poison_available,
            wolf_negotiation_round=wolf_negotiation_round,
            wolf_prior_votes=wolf_prior_votes,
            hunter_can_shoot=hunter_can_shoot,
            persona=state.persona_for(player_id),
            public_speeches=public_speeches,
            wolf_team_speeches=wolf_team_speeches,
            sheriff_election_step=sheriff_election_step,
            sheriff_candidates=sheriff_candidates,
            sheriff_withdrawn=sheriff_withdrawn,
            is_sheriff_candidate=is_sheriff_candidate,
            is_sheriff_withdrawn=is_sheriff_withdrawn,
            is_sheriff_voter=is_sheriff_voter,
            must_set_speech_order=(
                state.phase == Phase.DAY_SPEECH
                and state.speech_order_pending
                and state.sheriff_id == player_id
                and player.alive
            ),
            speech_order_pending=state.speech_order_pending,
            must_transfer_sheriff_badge=(
                state.sheriff_badge_pending_from == player_id
            ),
            may_give_last_words=(
                state.phase == Phase.DAY_ANNOUNCE
                and has_last_words(state, player_id)
            ),
        )


def _derive_public_events(state: GameState) -> tuple[PublicEventSummary, ...]:
    events: list[PublicEventSummary] = []
    phase_str = state.phase.value
    for pid in state.death_announcements:
        events.append(
            PublicEventSummary(
                event_type="player_died",
                round_number=state.round_number,
                phase=phase_str,
                player_id=pid,
            )
        )
    if state.sheriff_id is not None:
        events.append(
            PublicEventSummary(
                event_type="sheriff_elected",
                round_number=state.round_number,
                phase=phase_str,
                player_id=state.sheriff_id,
            )
        )
    return tuple(events)
