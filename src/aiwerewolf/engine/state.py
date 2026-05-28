"""Runtime game state — frozen dataclasses (engine internal)."""

from __future__ import annotations

from dataclasses import dataclass, replace

from schema.enums import Camp, Phase, Role, WinReason


@dataclass(frozen=True, slots=True)
class PlayerState:
    player_id: int
    role: Role
    alive: bool = True
    is_sheriff: bool = False
    in_soul_state: bool = False

    def is_wolf(self) -> bool:
        return self.role == Role.WOLF

    def is_god(self) -> bool:
        return self.role in {Role.SEER, Role.WITCH, Role.HUNTER, Role.IDIOT}

    def is_villager(self) -> bool:
        return self.role == Role.VILLAGER

    def counts_as_alive_for_win(self) -> bool:
        """Alive on field; soul-state idiot still counts as living good."""
        return self.alive


@dataclass(frozen=True, slots=True)
class WinResult:
    winner: Camp
    reason: WinReason


@dataclass(frozen=True, slots=True)
class SeerCheckResult:
    target_id: int
    is_wolf: bool
    round_number: int


@dataclass(frozen=True, slots=True)
class VoteRecord:
    voter_id: int
    target_id: int | None
    weight: float = 1.0


@dataclass(frozen=True, slots=True)
class SpeechRecord:
    """Public or wolf-only utterance visible to the appropriate audience."""

    player_id: int
    round_number: int
    phase: str
    speech: str
    demeanor_emojis: tuple[str, ...]
    audience: str  # "public" | "wolf_only"


@dataclass(frozen=True, slots=True)
class GameState:
    players: tuple[PlayerState, ...]
    phase: Phase
    round_number: int
    sheriff_id: int | None = None
    is_first_day: bool = True
    winner: Camp | None = None
    win_reason: WinReason | None = None
    wolf_kill_target: int | None = None
    witch_antidote_available: bool = True
    witch_poison_available: bool = True
    seer_checks: tuple[SeerCheckResult, ...] = ()
    hunter_can_shoot: bool = False
    death_announcements: tuple[int, ...] = ()
    # Day phase (Slice 2)
    sheriff_candidates: tuple[int, ...] = ()
    sheriff_withdrawn: tuple[int, ...] = ()
    sheriff_election_retry: bool = False
    sheriff_election_forbidden: bool = False
    sheriff_election_step: str = "nominate"  # nominate | speech | vote
    self_destruct_today: bool = False
    self_destruct_during_election: int = 0
    day_votes: tuple[VoteRecord, ...] = ()
    pk_candidates: tuple[int, ...] = ()
    wolf_negotiation_round: int = 0
    wolf_negotiation_votes: tuple[tuple[int, int | None], ...] = ()
    personas: tuple[tuple[int, str], ...] = ()
    speech_log: tuple[SpeechRecord, ...] = ()

    def living_players(self) -> tuple[PlayerState, ...]:
        return tuple(p for p in self.players if p.counts_as_alive_for_win())

    def living_wolves(self) -> tuple[PlayerState, ...]:
        return tuple(p for p in self.living_players() if p.is_wolf())

    def living_gods(self) -> tuple[PlayerState, ...]:
        return tuple(p for p in self.living_players() if p.is_god())

    def living_villagers(self) -> tuple[PlayerState, ...]:
        return tuple(p for p in self.living_players() if p.is_villager())

    def player(self, player_id: int) -> PlayerState:
        for p in self.players:
            if p.player_id == player_id:
                return p
        raise KeyError(f"player {player_id} not found")

    def with_speech(self, record: SpeechRecord) -> GameState:
        return replace(self, speech_log=self.speech_log + (record,))

    def persona_for(self, player_id: int) -> str:
        for pid, text in self.personas:
            if pid == player_id:
                return text
        return ""

    def with_phase(self, phase: Phase, **kwargs: object) -> GameState:
        return replace(self, phase=phase, **kwargs)

    def with_winner(self, result: WinResult) -> GameState:
        return replace(
            self,
            phase=Phase.GAME_OVER,
            winner=result.winner,
            win_reason=result.reason,
        )
