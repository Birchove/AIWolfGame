"""Configuration models — validates Config/*.yaml."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field


class WolfKillConfig(BaseModel):
    tie_allowed: bool = False
    empty_allowed: bool = True
    max_negotiation_rounds: int = 10


class GameConfig(BaseModel):
    max_rounds: int = 30
    sheriff_vote_weight: float = 1.5
    wolf_kill: WolfKillConfig = Field(default_factory=WolfKillConfig)


class BoardConfig(BaseModel):
    players: int = 12
    wolves: int = 4
    gods: list[str] = Field(default_factory=lambda: ["seer", "witch", "hunter", "idiot"])
    villagers: int = 4


class AgentsConfig(BaseModel):
    default_timeout_sec: int = 60
    response_jitter_ms: list[int] = Field(default_factory=lambda: [0, 500])


class LLMConfig(BaseModel):
    provider: str = "openai"
    model: str = "gpt-4o"
    base_url: str = ""
    temperature: float = 0.7
    top_p: float = 0.95
    frequency_penalty: float = 0.3
    presence_penalty: float = 0.0
    temperature_jitter: float = 0.15
    top_p_jitter: float = 0.06
    frequency_penalty_jitter: float = 0.15
    api_key: str = ""
    # Per-seat model pool — same api_key, mixed models for diversity
    model_pool: list[str] = Field(default_factory=list)
    assign_models_per_player: bool = True
    diversify_within_camp: bool = True


class ProvidersConfig(BaseModel):
    openai: dict[str, str] = Field(default_factory=lambda: {"api_key": ""})
    anthropic: dict[str, str] = Field(default_factory=lambda: {"api_key": ""})
    deepseek: dict[str, str] = Field(default_factory=lambda: {"api_key": ""})


class PromptsConfig(BaseModel):
    rules_file: str = "rules.md"
    game_guide_file: str = "game_guide.md"
    inject_full_game_guide: bool = False
    inject_role_scoped_guide: bool = True


class LoggingConfig(BaseModel):
    format: str = "json"
    output_dir: str = "logs/"


class AppConfig(BaseModel):
    board: BoardConfig = Field(default_factory=BoardConfig)
    game: GameConfig = Field(default_factory=GameConfig)
    agents: AgentsConfig = Field(default_factory=AgentsConfig)
    llm: LLMConfig = Field(default_factory=LLMConfig)
    providers: ProvidersConfig = Field(default_factory=ProvidersConfig)
    prompts: PromptsConfig = Field(default_factory=PromptsConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)

    def llm_api_key(self) -> str:
        """Resolved API key: llm.api_key → providers.{provider}.api_key."""
        if self.llm.api_key.strip():
            return self.llm.api_key.strip()
        provider = self.llm.provider
        bucket: dict[str, str] = getattr(self.providers, provider, {})
        return (bucket.get("api_key") or "").strip()

    def llm_ready(self) -> bool:
        return bool(self.llm_api_key())


def _shallow_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    merged = dict(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = {**merged[key], **value}
        else:
            merged[key] = value
    return merged


def _load_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    with path.open(encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data if isinstance(data, dict) else {}


def load_app_config(
    config_dir: Path | None = None,
    *,
    use_secrets: bool = True,
) -> AppConfig:
    """Load Config/default.yaml, optional Config/secrets.yaml, then env override."""
    root = config_dir or Path("Config")
    data = _load_yaml(root / "default.yaml")
    if use_secrets:
        data = _shallow_merge(data, _load_yaml(root / "secrets.yaml"))
    env_key = os.environ.get("AIWEREWOLF_LLM_API_KEY")
    if env_key:
        llm = dict(data.get("llm", {}))
        llm["api_key"] = env_key
        data["llm"] = llm
    return AppConfig.model_validate(data)
