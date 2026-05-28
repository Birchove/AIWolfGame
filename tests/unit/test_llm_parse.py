"""AgentTurnOutput JSON roundtrip for all action types."""

import json

from schema.agent import (
    AgentTurnOutput,
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


def test_all_action_types_roundtrip() -> None:
    cases = [
        PassAction(),
        SpeechAction(speech="hi"),
        VoteAction(target_id=2),
        WolfKillAction(target_id=3),
        SelfDestructAction(last_words="bye", transfer_to=4),
        HunterShootAction(target_id=5),
        WitchSaveAction(use_antidote=True),
        WitchPoisonAction(target_id=6),
        SeerCheckAction(target_id=7),
        IdiotRevealAction(reveal=True),
    ]
    for action in cases:
        out = AgentTurnOutput(
            model="test",
            player_id=1,
            role="wolf",
            speech="",
            demeanor="",
            action=action,
        )
        parsed = AgentTurnOutput.model_validate_json(out.model_dump_json())
        assert parsed.action.type == action.type
