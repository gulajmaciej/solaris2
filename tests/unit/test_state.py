import pytest

from core.state import GameState


@pytest.mark.unit
def test_initial_state_defaults():
    state = GameState.initial()
    assert state.turn == 1
    assert state.ocean.activity == 0.2
    assert state.crew.stress == 0.1
    assert state.station.power_level == 0.95


@pytest.mark.unit
def test_next_turn_increments():
    state = GameState.initial()
    state.next_turn()
    assert state.turn == 2
