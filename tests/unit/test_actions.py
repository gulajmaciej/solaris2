import pytest

from core.actions import apply_action
from core.state import GameState
from agents.planner import PlannedAction


@pytest.mark.unit
def test_apply_action_changes_state():
    state = GameState.initial()
    apply_action(state=state, action=PlannedAction.INCREASE_MEASUREMENT_FREQUENCY)
    assert state.ocean.activity > 0.2
    assert state.station.power_level < 0.95


@pytest.mark.unit
def test_apply_action_clamps_values():
    state = GameState.initial()
    state.ocean.activity = 0.99
    apply_action(state=state, action=PlannedAction.INCREASE_MEASUREMENT_FREQUENCY)
    assert 0.0 <= state.ocean.activity <= 1.0
