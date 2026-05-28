"""Daytime speech order — sheriff picks left/right anchor per rules.md."""

from __future__ import annotations

from aiwerewolf.engine.state import GameState


def _living_clockwise_ring(living: set[int]) -> list[int]:
    return [pid for offset in range(12) if (pid := ((offset % 12) + 1)) in living]


def _start_from_anchor(anchor: int, living: set[int], *, clockwise: bool) -> int:
    for step in range(1, 13):
        if clockwise:
            pid = ((anchor - 1 + step) % 12) + 1
        else:
            pid = ((anchor - 1 - step) % 12) + 1
        if pid in living:
            return pid
    raise ValueError("no living players")


def _ring_from_start(ring: list[int], start: int, *, clockwise: bool) -> list[int]:
    n = len(ring)
    idx = ring.index(start)
    if clockwise:
        return [ring[(idx + k) % n] for k in range(n)]
    return [ring[(idx - k) % n] for k in range(n)]


def day_speech_order(
    state: GameState,
    *,
    side: str = "right",
    first_speaker_id: int | None = None,
) -> list[int]:
    """One full speech round: living players once, sheriff-indicated direction."""
    living = {p.player_id for p in state.living_players()}
    ring = _living_clockwise_ring(living)
    if not ring:
        return []

    clockwise = side != "left"
    if first_speaker_id is not None and first_speaker_id in living:
        start = first_speaker_id
        return _ring_from_start(ring, start, clockwise=clockwise)

    deaths = state.death_announcements
    if state.sheriff_id is None:
        anchor = 1
        if anchor in living:
            start = anchor
        else:
            start = _start_from_anchor(anchor, living, clockwise=True)
        return _ring_from_start(ring, start, clockwise=True)

    if len(deaths) == 1:
        anchor = deaths[0]
    else:
        anchor = state.sheriff_id

    start = _start_from_anchor(anchor, living, clockwise=clockwise)
    if start not in ring:
        start = ring[0]
    return _ring_from_start(ring, start, clockwise=clockwise)
