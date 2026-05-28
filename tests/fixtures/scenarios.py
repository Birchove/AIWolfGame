"""Deterministic GameState fixtures for unit tests."""

from __future__ import annotations

from schema.enums import Phase, Role

from aiwerewolf.engine.setup import assign_roles
from aiwerewolf.engine.state import GameState, PlayerState, SeerCheckResult


def make_players(
    roles: dict[int, Role],
    *,
    alive: set[int] | None = None,
    sheriff_id: int | None = None,
    soul: set[int] | None = None,
) -> tuple[PlayerState, ...]:
    alive = alive if alive is not None else set(roles)
    soul = soul or set()
    players: list[PlayerState] = []
    for pid in sorted(roles):
        players.append(
            PlayerState(
                player_id=pid,
                role=roles[pid],
                alive=pid in alive,
                is_sheriff=pid == sheriff_id,
                in_soul_state=pid in soul,
            )
        )
    return tuple(players)


def state_from_roles(
    roles: dict[int, Role],
    *,
    phase: Phase = Phase.NIGHT_WOLF,
    round_number: int = 1,
    is_first_day: bool = True,
    alive: set[int] | None = None,
    sheriff_id: int | None = None,
    soul: set[int] | None = None,
    wolf_kill_target: int | None = None,
    seer_checks: tuple[SeerCheckResult, ...] = (),
    hunter_can_shoot: bool = False,
    death_announcements: tuple[int, ...] = (),
    self_destruct_during_election: int = 0,
    sheriff_election_retry: bool = False,
) -> GameState:
    return GameState(
        players=make_players(
            roles, alive=alive, sheriff_id=sheriff_id, soul=soul
        ),
        phase=phase,
        round_number=round_number,
        is_first_day=is_first_day,
        sheriff_id=sheriff_id,
        wolf_kill_target=wolf_kill_target,
        seer_checks=seer_checks,
        hunter_can_shoot=hunter_can_shoot,
        death_announcements=death_announcements,
        self_destruct_during_election=self_destruct_during_election,
        sheriff_election_retry=sheriff_election_retry,
    )


def standard_twelve_player_roles() -> dict[int, Role]:
    """Player 1-4 wolves, 5-8 gods, 9-12 villagers."""
    roles: dict[int, Role] = {}
    for i in range(1, 5):
        roles[i] = Role.WOLF
    for i, r in zip(range(5, 9), [Role.SEER, Role.WITCH, Role.HUNTER, Role.IDIOT]):
        roles[i] = r
    for i in range(9, 13):
        roles[i] = Role.VILLAGER
    return roles


def fresh_game(seed: int = 0) -> GameState:
    order = list(standard_twelve_player_roles().values())
    return assign_roles(order, seed=seed)
