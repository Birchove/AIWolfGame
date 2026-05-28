"""Agent-facing view types — frozen dataclasses (not Pydantic)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from schema.enums import Phase, Role

from aiwerewolf.engine.state import SeerCheckResult, SpeechRecord

__all__ = [
    "PlayerView",
    "PublicEventSummary",
    "SeerCheckResult",
    "SpeechRecord",
]


@dataclass(frozen=True, slots=True)
class PublicEventSummary:
    event_type: str
    round_number: int
    phase: str
    player_id: int | None = None
    extra: tuple[tuple[str, Any], ...] | None = None


@dataclass(frozen=True, slots=True)
class PlayerView:
    """Filtered slice of game state for one agent — never contains GameState."""

    player_id: int
    own_role: Role
    phase: Phase
    round_number: int
    is_alive: bool
    is_sheriff: bool
    in_soul_state: bool

    living_player_ids: tuple[int, ...]
    dead_player_ids: tuple[int, ...]
    sheriff_id: int | None
    public_events: tuple[PublicEventSummary, ...]

    wolf_teammates: tuple[int, ...] = ()
    seer_checks: tuple[SeerCheckResult, ...] = ()
    witch_night_death: int | None = None
    witch_antidote_available: bool = True
    witch_poison_available: bool = True
    wolf_negotiation_round: int = 0
    wolf_prior_votes: tuple[tuple[int, int | None], ...] = ()
    hunter_can_shoot: bool = False
    sheriff_election_step: str = "nominate"
    sheriff_candidates: tuple[int, ...] = ()
    sheriff_withdrawn: tuple[int, ...] = ()
    is_sheriff_candidate: bool = False
    is_sheriff_withdrawn: bool = False
    is_sheriff_voter: bool = False
    must_set_speech_order: bool = False
    speech_order_pending: bool = False
    must_transfer_sheriff_badge: bool = False
    may_give_last_words: bool = False
    persona: str = ""
    public_speeches: tuple[SpeechRecord, ...] = ()
    wolf_team_speeches: tuple[SpeechRecord, ...] = ()

    def can_act(self) -> bool:
        return self.is_alive
