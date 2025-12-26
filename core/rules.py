from core.state import GameState
from core.actions import PlayerAction


def apply_action(state: GameState, action: PlayerAction) -> None:
    """
    Deterministic world rules.
    No randomness, no interpretation.
    """

    if action == PlayerAction.INTENSIFY_RESEARCH:
        state.ocean.activity += 0.2
        state.ocean.instability += 0.1
        state.crew.stress += 0.1
        state.station.power_level -= 0.05

    elif action == PlayerAction.STABILIZE_CREW:
        state.crew.stress = max(0.0, state.crew.stress - 0.2)
        state.crew.fatigue = max(0.0, state.crew.fatigue - 0.1)
        state.ocean.activity += 0.05

    elif action == PlayerAction.OBSERVE_ONLY:
        state.ocean.activity += 0.05

    clamp_state(state)


def clamp_state(state: GameState) -> None:
    state.crew.stress = min(max(state.crew.stress, 0.0), 1.0)
    state.crew.fatigue = min(max(state.crew.fatigue, 0.0), 1.0)
    state.ocean.instability = min(max(state.ocean.instability, 0.0), 1.0)
    state.ocean.activity = min(max(state.ocean.activity, 0.0), 1.0)
    state.station.integrity = min(max(state.station.integrity, 0.0), 1.0)
    state.station.power_level = min(max(state.station.power_level, 0.0), 1.0)
