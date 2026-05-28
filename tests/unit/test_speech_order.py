"""Day speech order helpers."""

from schema.enums import Phase, Role

from aiwerewolf.engine.speech_order import day_speech_order
from tests.fixtures.scenarios import standard_twelve_player_roles, state_from_roles


def test_no_sheriff_clockwise_from_seat_one() -> None:
    state = state_from_roles(
        standard_twelve_player_roles(),
        phase=Phase.DAY_SPEECH,
        sheriff_id=None,
        death_announcements=(),
    )
    assert day_speech_order(state) == list(range(1, 13))


def test_sheriff_single_death_anchor() -> None:
    roles = standard_twelve_player_roles()
    state = state_from_roles(
        roles,
        phase=Phase.DAY_SPEECH,
        sheriff_id=5,
        alive=set(range(1, 13)) - {3},
        death_announcements=(3,),
    )
    order = day_speech_order(state, side="right")
    assert order[0] == 4
    assert set(order) == set(range(1, 13)) - {3}


def test_sheriff_left_from_self_on_peaceful_night() -> None:
    state = state_from_roles(
        standard_twelve_player_roles(),
        phase=Phase.DAY_SPEECH,
        sheriff_id=5,
        death_announcements=(),
    )
    order = day_speech_order(state, side="left")
    assert order[0] == 4
    assert len(order) == 12


def test_explicit_first_speaker_overrides_anchor() -> None:
    state = state_from_roles(
        standard_twelve_player_roles(),
        phase=Phase.DAY_SPEECH,
        sheriff_id=5,
        death_announcements=(3,),
    )
    order = day_speech_order(state, side="right", first_speaker_id=9)
    assert order[0] == 9
    assert len(order) == 12
