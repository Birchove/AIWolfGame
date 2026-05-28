"""Config loading tests."""

from pathlib import Path

from schema.config import load_app_config


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def test_load_default_config() -> None:
    cfg = load_app_config(repo_root() / "Config", use_secrets=False)
    assert cfg.board.players == 12
    assert cfg.game.wolf_kill.empty_allowed is True
    assert cfg.prompts.inject_role_scoped_guide is True
    assert len(cfg.llm.model_pool) >= 2


def test_load_default_yaml_file_exists() -> None:
    assert (repo_root() / "Config" / "default.yaml").is_file()


def test_env_overrides_api_key(monkeypatch) -> None:
    monkeypatch.setenv("AIWEREWOLF_LLM_API_KEY", "test-key-from-env")
    cfg = load_app_config(repo_root() / "Config", use_secrets=False)
    assert cfg.llm_api_key() == "test-key-from-env"


def test_provider_api_key_fallback() -> None:
    cfg = load_app_config(repo_root() / "Config", use_secrets=False)
    cfg = cfg.model_copy(
        update={
            "llm": cfg.llm.model_copy(update={"api_key": "", "provider": "openai"}),
            "providers": cfg.providers.model_copy(
                update={"openai": {"api_key": "from-provider"}}
            ),
        }
    )
    assert cfg.llm_api_key() == "from-provider"
    assert cfg.llm_ready()
