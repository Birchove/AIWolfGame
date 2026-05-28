"""Per-player LLM model and sampling profiles — camp-aware diversity."""

from __future__ import annotations

import hashlib
import random
from dataclasses import dataclass

from schema.config import AppConfig
from schema.enums import Role

from aiwerewolf.agents.base import Agent
from aiwerewolf.engine.state import GameState, PlayerState


@dataclass(frozen=True, slots=True)
class PlayerLLMProfile:
    model: str
    temperature: float
    top_p: float
    frequency_penalty: float
    presence_penalty: float
    prompt_nonce: str


def _distinct_assign(
    player_ids: list[int],
    pool: list[str],
    rng: random.Random,
) -> dict[int, str]:
    if not player_ids:
        return {}
    if len(pool) >= len(player_ids):
        chosen = rng.sample(pool, len(player_ids))
    else:
        shuffled = pool[:]
        rng.shuffle(shuffled)
        chosen = [shuffled[i % len(shuffled)] for i in range(len(player_ids))]
    return dict(zip(sorted(player_ids), chosen))


def assign_player_profiles(
    players: tuple[PlayerState, ...],
    cfg: AppConfig,
    *,
    seed: int,
    game_id: str = "",
) -> dict[int, PlayerLLMProfile]:
    """Assign model + sampling params; diversify within wolf/good camps."""
    pool = [m for m in cfg.llm.model_pool if m.strip()] or [cfg.llm.model]
    rng = random.Random(seed)

    wolves = [p.player_id for p in players if p.role == Role.WOLF]
    goods = [p.player_id for p in players if p.role != Role.WOLF]

    models: dict[int, str] = {}
    if cfg.llm.assign_models_per_player and cfg.llm.diversify_within_camp:
        models.update(_distinct_assign(wolves, pool, rng))
        goods_pool = pool[:]
        rng.shuffle(goods_pool)
        models.update(_distinct_assign(goods, goods_pool, rng))
    elif cfg.llm.assign_models_per_player:
        shuffled = pool[:]
        rng.shuffle(shuffled)
        for i, p in enumerate(sorted(players, key=lambda x: x.player_id)):
            models[p.player_id] = shuffled[i % len(shuffled)]
    else:
        for p in players:
            models[p.player_id] = cfg.llm.model

    profiles: dict[int, PlayerLLMProfile] = {}
    for p in players:
        pid = p.player_id
        nonce_src = f"{game_id}:{seed}:{pid}:{p.role.value}"
        nonce = hashlib.sha256(nonce_src.encode()).hexdigest()[:16]
        t_spread = cfg.llm.temperature_jitter
        p_spread = cfg.llm.top_p_jitter
        f_spread = cfg.llm.frequency_penalty_jitter
        phase = (pid * 17 + seed) % 11
        spread_idx = phase
        temperature = min(
            1.5,
            max(0.1, cfg.llm.temperature + (spread_idx - 5) * t_spread / 5),
        )
        top_p = min(1.0, max(0.5, cfg.llm.top_p + ((pid * 3 + seed) % 7 - 3) * p_spread / 3))
        freq = min(
            1.2,
            max(0.0, cfg.llm.frequency_penalty + ((pid * 13 + seed) % 11) * f_spread / 10),
        )
        pres = min(
            0.8,
            max(0.0, cfg.llm.presence_penalty + ((pid * 5 + seed) % 3) * 0.05),
        )
        profiles[pid] = PlayerLLMProfile(
            model=models[pid],
            temperature=temperature,
            top_p=top_p,
            frequency_penalty=freq,
            presence_penalty=pres,
            prompt_nonce=nonce,
        )
    return profiles


def bind_agents_for_game(
    agents: dict[int, Agent],
    state: GameState,
    cfg: AppConfig,
    *,
    seed: int,
) -> dict[int, PlayerLLMProfile]:
    from aiwerewolf.agents.llm.agent import LLMAgent

    profiles = assign_player_profiles(
        state.players,
        cfg,
        seed=seed,
        game_id=getattr(state, "game_id", "") or str(seed),
    )
    for pid, profile in profiles.items():
        agent = agents.get(pid)
        if isinstance(agent, LLMAgent):
            agent.bind_game(profile)
    return profiles
