from agents.planner import PlannedAction
from core.state import GameState


def apply_action(
    *,
    state: GameState,
    action: PlannedAction,
) -> None:
    """
    Deterministically apply a single planned action to the GameState.
    This function has NO randomness and NO LLM usage.
    """

    if action == PlannedAction.INCREASE_MEASUREMENT_FREQUENCY:
        state.ocean.activity += 0.05
        state.station.power_level -= 0.03

    elif action == PlannedAction.ADJUST_SENSOR_SENSITIVITY:
        state.ocean.activity += 0.03
        state.ocean.instability += 0.02
        state.station.power_level -= 0.02

    elif action == PlannedAction.FILTER_DATA_AGGRESSIVELY:
        state.ocean.instability -= 0.04
        state.ocean.activity -= 0.02

    elif action == PlannedAction.INITIATE_REST_PROTOCOL:
        state.crew.stress -= 0.05
        state.crew.fatigue -= 0.03
        state.station.power_level -= 0.02

    elif action == PlannedAction.REDUCE_INFORMATION_FLOW:
        state.crew.stress -= 0.03
        state.ocean.activity -= 0.03

    elif action == PlannedAction.ENFORCE_PROCEDURES:
        state.crew.stress += 0.02
        state.station.power_level -= 0.01

    # --- clamp values ---
    state.ocean.activity = max(0.0, min(1.0, state.ocean.activity))
    state.ocean.instability = max(0.0, min(1.0, state.ocean.instability))
    state.crew.stress = max(0.0, min(1.0, state.crew.stress))
    state.crew.fatigue = max(0.0, min(1.0, state.crew.fatigue))
    state.station.power_level = max(0.0, min(1.0, state.station.power_level))
