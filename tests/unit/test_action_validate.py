"""Action target validation tests."""

from schema.agent import (
    HunterShootAction,
    PassAction,
    SeerCheckAction,
    VoteAction,
    WitchPoisonAction,
    WolfKillAction,
)
from schema.enums import Phase, Role

from aiwerewolf.protocol.action_validate import validate_action_for_view
from aiwerewolf.protocol.views import PlayerView


def _view(**kwargs) -> PlayerView:
    defaults = dict(
        player_id=1,
        own_role=Role.WOLF,
        phase=Phase.NIGHT_WOLF,
        round_number=1,
        is_alive=True,
        is_sheriff=False,
        in_soul_state=False,
        living_player_ids=(5, 6, 7, 8, 9),
        dead_player_ids=(1, 2, 3, 4),
        sheriff_id=None,
        public_events=(),
        wolf_teammates=(2, 3, 4),
    )
    defaults.update(kwargs)
    return PlayerView(**defaults)


def test_wolf_kill_valid_target() -> None:
    ok, _ = validate_action_for_view(_view(), WolfKillAction(target_id=9))
    assert ok


def test_wolf_kill_rejects_teammate() -> None:
    ok, reason = validate_action_for_view(_view(), WolfKillAction(target_id=2))
    assert not ok
    assert "wolf" in reason.lower()


def test_wolf_kill_rejects_dead_target() -> None:
    ok, _ = validate_action_for_view(_view(), WolfKillAction(target_id=1))
    assert not ok


def test_seer_check_rejects_self() -> None:
    view = _view(
        player_id=5,
        own_role=Role.SEER,
        phase=Phase.NIGHT_SEER,
        wolf_teammates=(),
    )
    ok, _ = validate_action_for_view(view, SeerCheckAction(target_id=5))
    assert not ok


def test_witch_poison_valid() -> None:
    view = _view(
        player_id=6,
        own_role=Role.WITCH,
        phase=Phase.NIGHT_WITCH,
        wolf_teammates=(),
    )
    ok, _ = validate_action_for_view(view, WitchPoisonAction(target_id=9))
    assert ok


def test_hunter_shoot_when_active() -> None:
    view = _view(
        player_id=7,
        own_role=Role.HUNTER,
        phase=Phase.DAY_VOTE,
        hunter_can_shoot=True,
        wolf_teammates=(),
    )
    ok, _ = validate_action_for_view(view, HunterShootAction(target_id=9))
    assert ok


def test_vote_abstain_ok() -> None:
    view = _view(
        player_id=9,
        own_role=Role.VILLAGER,
        phase=Phase.DAY_VOTE,
        wolf_teammates=(),
    )
    ok, _ = validate_action_for_view(view, VoteAction(target_id=None))
    assert ok


def test_pass_always_ok_for_wrong_role_at_night() -> None:
    view = _view(own_role=Role.VILLAGER, phase=Phase.NIGHT_WOLF)
    ok, _ = validate_action_for_view(view, PassAction())
    assert ok
