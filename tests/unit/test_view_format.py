"""Tests for PlayerView serialization and action hints."""

import json

from schema.enums import Phase, Role

from aiwerewolf.agents.llm.view_format import (
    allowed_actions_for_phase,
    format_player_view,
    view_to_dict,
)
from aiwerewolf.protocol.dispatch import PHASE_ALLOWED_ACTIONS
from aiwerewolf.protocol.views import PlayerView


def _minimal_view(**kwargs) -> PlayerView:
    defaults = dict(
        player_id=1,
        own_role=Role.VILLAGER,
        phase=Phase.DAY_VOTE,
        round_number=1,
        is_alive=True,
        is_sheriff=False,
        in_soul_state=False,
        living_player_ids=(1, 2, 3),
        dead_player_ids=(),
        sheriff_id=None,
        public_events=(),
    )
    defaults.update(kwargs)
    return PlayerView(**defaults)


def test_view_to_dict_no_engine_leak() -> None:
    view = _minimal_view()
    data = view_to_dict(view)
    text = json.dumps(data)
    assert "GameState" not in text
    assert "players" not in data


def test_format_includes_allowed_actions() -> None:
    text = format_player_view(_minimal_view())
    payload = json.loads(text)
    assert "allowed_actions" in payload
    assert any(a["type"] == "vote" for a in payload["allowed_actions"])


def test_wolf_negotiation_hint_in_view() -> None:
    view = _minimal_view(
        own_role=Role.WOLF,
        phase=Phase.NIGHT_WOLF,
        wolf_prior_votes=((2, 5), (3, 9)),
        wolf_negotiation_round=2,
    )
    text = format_player_view(view)
    assert "狼队协商" in text
    assert "玩家2" in text


def test_phase_action_whitelist_matches_dispatch() -> None:
    role_by_phase = {
        Phase.NIGHT_WOLF: Role.WOLF,
        Phase.NIGHT_WITCH: Role.WITCH,
        Phase.NIGHT_SEER: Role.SEER,
        Phase.NIGHT_HUNTER: Role.HUNTER,
        Phase.NIGHT_IDIOT: Role.IDIOT,
    }
    for phase, types in PHASE_ALLOWED_ACTIONS.items():
        if phase == Phase.DAY_SHERIFF:
            continue  # step-specific; see test_sheriff_election_actions
        role = role_by_phase.get(phase, Role.VILLAGER)
        actions = allowed_actions_for_phase(phase, role)
        allowed_types = {a["type"] for a in actions}
        assert types == allowed_types


def test_sheriff_election_actions_by_step() -> None:
    nom = allowed_actions_for_phase(
        Phase.DAY_SHERIFF, Role.VILLAGER, sheriff_election_step="nominate"
    )
    assert {a["type"] for a in nom} == {"pass", "self_destruct", "sheriff_run"}

    speech = allowed_actions_for_phase(
        Phase.DAY_SHERIFF,
        Role.VILLAGER,
        sheriff_election_step="speech",
        is_sheriff_candidate=True,
    )
    assert "sheriff_withdraw" in {a["type"] for a in speech}

    vote = allowed_actions_for_phase(
        Phase.DAY_SHERIFF,
        Role.VILLAGER,
        sheriff_election_step="vote",
        is_sheriff_voter=True,
    )
    assert "vote" in {a["type"] for a in vote}
