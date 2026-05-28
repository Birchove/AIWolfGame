"""Agent action payloads (validated at engine boundary)."""

from typing import Literal

from pydantic import BaseModel, Field


class SpeechAction(BaseModel):
    type: Literal["speech"] = "speech"
    speech: str
    demeanor: str = ""


class VoteAction(BaseModel):
    type: Literal["vote"] = "vote"
    target_id: int | None = None  # None = abstain


class WolfKillAction(BaseModel):
    type: Literal["wolf_kill"] = "wolf_kill"
    target_id: int | None = None  # None = empty kill (all wolves agree)


class SelfDestructAction(BaseModel):
    type: Literal["self_destruct"] = "self_destruct"
    last_words: str = ""
    night_direct_kill: int | None = None
    transfer_to: int | None = None  # required when self-destructing sheriff wolf


class HunterShootAction(BaseModel):
    type: Literal["hunter_shoot"] = "hunter_shoot"
    target_id: int | None = None  # None = decline to shoot


class PassAction(BaseModel):
    type: Literal["pass"] = "pass"


class SheriffRunAction(BaseModel):
    type: Literal["sheriff_run"] = "sheriff_run"


class SheriffWithdrawAction(BaseModel):
    type: Literal["sheriff_withdraw"] = "sheriff_withdraw"


class WitchSaveAction(BaseModel):
    type: Literal["witch_save"] = "witch_save"
    use_antidote: bool = False


class WitchPoisonAction(BaseModel):
    type: Literal["witch_poison"] = "witch_poison"
    target_id: int | None = None  # None = skip poison


class SeerCheckAction(BaseModel):
    type: Literal["seer_check"] = "seer_check"
    target_id: int


class IdiotRevealAction(BaseModel):
    type: Literal["idiot_reveal"] = "idiot_reveal"
    reveal: bool = True


ActionPayload = (
    SpeechAction
    | VoteAction
    | WolfKillAction
    | SelfDestructAction
    | HunterShootAction
    | WitchSaveAction
    | WitchPoisonAction
    | SeerCheckAction
    | IdiotRevealAction
    | SheriffRunAction
    | SheriffWithdrawAction
    | PassAction
)


class AgentTurnOutput(BaseModel):
    """Structured agent output — see CLAUDE.md."""

    model: str = Field(description="LLM model name (log/spectator visible)")
    player_id: int = Field(ge=1, description="Public")
    role: str = Field(description="Private — not broadcast to other agents")
    speech: str = Field(default="", description="Public speech content")
    demeanor: str = Field(default="", description="Public demeanor/actions (full text, log)")
    demeanor_emojis: list[str] = Field(
        default_factory=list,
        description="Public emoji tags from LLM (1+ items, e.g. 😏🤔)",
    )
    reasoning: str = Field(
        default="",
        description="In-character player inner thoughts (心理活动/推理), not LLM meta-reasoning",
    )
    action: ActionPayload = Field(default_factory=PassAction)
