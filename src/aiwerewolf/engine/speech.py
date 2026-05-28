"""Public / wolf-team speech log on GameState."""

from __future__ import annotations

from schema.agent import AgentTurnOutput
from schema.enums import Phase

from aiwerewolf.engine.state import GameState, SpeechRecord

_DAY_PUBLIC_PHASES = frozenset(
    {
        Phase.DAY_SHERIFF,
        Phase.DAY_ANNOUNCE,
        Phase.DAY_SPEECH,
        Phase.DAY_PK,
    }
)


def audience_for_phase(phase: Phase) -> str | None:
    if phase == Phase.NIGHT_WOLF:
        return "wolf_only"
    if phase in _DAY_PUBLIC_PHASES:
        return "public"
    return None


def append_speech(state: GameState, output: AgentTurnOutput) -> GameState:
    """Record speech + public demeanor emojis if this phase allows speech."""
    audience = audience_for_phase(state.phase)
    if audience is None:
        return state
    speech = (output.speech or "").strip()
    emojis = tuple(output.demeanor_emojis or ())
    if not speech and not emojis:
        return state
    record = SpeechRecord(
        player_id=output.player_id,
        round_number=state.round_number,
        phase=state.phase.value,
        speech=speech,
        demeanor_emojis=emojis,
        audience=audience,
    )
    return state.with_speech(record)
