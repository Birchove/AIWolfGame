"""Shared enumerations (serialization + engine alignment)."""

from enum import StrEnum


class Role(StrEnum):
    WOLF = "wolf"
    SEER = "seer"
    WITCH = "witch"
    HUNTER = "hunter"
    IDIOT = "idiot"
    VILLAGER = "villager"


class Camp(StrEnum):
    WOLF = "wolf"
    GOOD = "good"


class Phase(StrEnum):
    SETUP = "setup"
    NIGHT_WOLF = "night_wolf"
    NIGHT_WITCH = "night_witch"
    NIGHT_SEER = "night_seer"
    NIGHT_HUNTER = "night_hunter"
    NIGHT_IDIOT = "night_idiot"
    DAY_SHERIFF = "day_sheriff"
    DAY_ANNOUNCE = "day_announce"
    DAY_SPEECH = "day_speech"
    DAY_VOTE = "day_vote"
    DAY_PK = "day_pk"
    GAME_OVER = "game_over"


class WinReason(StrEnum):
    WOLVES_ELIMINATED = "wolves_eliminated"
    TU_BIAN_GODS = "tu_bian_gods"
    TU_BIAN_VILLAGERS = "tu_bian_villagers"
    MAX_ROUNDS_DRAW = "max_rounds_draw"


class DeathCause(StrEnum):
    WOLF_KILL = "wolf_kill"
    POISON = "poison"
    VOTE = "vote"
    HUNTER_SHOOT = "hunter_shoot"
    OTHER = "other"
