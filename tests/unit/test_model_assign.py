"""Per-player model assignment."""

from schema.config import AppConfig, LLMConfig
from schema.enums import Role

from aiwerewolf.agents.model_assign import assign_player_profiles
from aiwerewolf.engine.setup import create_game


def test_wolves_get_distinct_models_when_pool_large_enough() -> None:
    state = create_game(seed=0)
    cfg = AppConfig(
        llm=LLMConfig(
            model="deepseek-chat",
            model_pool=[
                "deepseek-chat",
                "deepseek-reasoner",
                "deepseek-v4-flash",
                "deepseek-v4-pro",
            ],
            assign_models_per_player=True,
            diversify_within_camp=True,
        )
    )
    profiles = assign_player_profiles(state.players, cfg, seed=0)
    wolf_models = {
        profiles[p.player_id].model for p in state.players if p.role == Role.WOLF
    }
    assert len(wolf_models) == 4
    assert len(set(wolf_models)) == 4


def test_profiles_vary_sampling_params() -> None:
    state = create_game(seed=3)
    cfg = AppConfig(llm=LLMConfig(assign_models_per_player=False))
    profiles = assign_player_profiles(state.players, cfg, seed=3)
    temps = {profiles[i].temperature for i in range(1, 13)}
    assert len(temps) > 1
    nonces = {profiles[i].prompt_nonce for i in range(1, 13)}
    assert len(nonces) == 12


def test_empty_model_pool_falls_back_to_default() -> None:
    state = create_game(seed=1)
    cfg = AppConfig(llm=LLMConfig(model="fallback-model", model_pool=[]))
    profiles = assign_player_profiles(state.players, cfg, seed=1)
    assert all(p.model == "fallback-model" for p in profiles.values())
