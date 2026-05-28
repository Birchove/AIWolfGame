"""Re-export action types from agent module for clarity."""

from schema.agent import (
    ActionPayload,
    HunterShootAction,
    IdiotRevealAction,
    PassAction,
    SeerCheckAction,
    SelfDestructAction,
    SpeechAction,
    VoteAction,
    WitchPoisonAction,
    WitchSaveAction,
    WolfKillAction,
)

__all__ = [
    "ActionPayload",
    "HunterShootAction",
    "IdiotRevealAction",
    "PassAction",
    "SeerCheckAction",
    "SelfDestructAction",
    "SpeechAction",
    "VoteAction",
    "WitchPoisonAction",
    "WitchSaveAction",
    "WolfKillAction",
]
