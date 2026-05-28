"""Initial board setup."""

from __future__ import annotations

import random

from schema.enums import Phase, Role

from aiwerewolf.agents.persona import assign_personas
from aiwerewolf.engine.state import GameState, PlayerState

STANDARD_ROLE_COUNTS: dict[Role, int] = {
    Role.WOLF: 4,
    Role.SEER: 1,
    Role.WITCH: 1,
    Role.HUNTER: 1,
    Role.IDIOT: 1,
    Role.VILLAGER: 4,
}


def standard_role_deck() -> list[Role]:
    deck: list[Role] = []
    for role, count in STANDARD_ROLE_COUNTS.items():
        deck.extend([role] * count)
    return deck


def assign_roles(roles: list[Role], *, seed: int | None = None) -> GameState:
    if len(roles) != 12:
        raise ValueError(f"expected 12 roles, got {len(roles)}")
    ordered = list(roles)
    if seed is not None:
        rng = random.Random(seed)
        rng.shuffle(ordered)
    players = tuple(
        PlayerState(player_id=i + 1, role=ordered[i]) for i in range(12)
    )
    persona_map = assign_personas(seed=seed)
    personas = tuple(sorted(persona_map.items()))
    return GameState(
        players=players,
        phase=Phase.SETUP,
        round_number=0,
        is_first_day=True,
        personas=personas,
    )


def create_game(*, seed: int | None = None) -> GameState:
    return assign_roles(standard_role_deck(), seed=seed)
