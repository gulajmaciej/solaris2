from enum import Enum
from typing import Optional
from agents.config import AgentRegistry
from core.state import GameState


class EndingType(Enum):
    INSTITUTIONAL_LOCK_IN = "institutional_lock_in"
    COGNITIVE_COLLAPSE = "cognitive_collapse"
    INSTITUTIONAL_TERMINATION = "institutional_termination"


class Ending:
    def __init__(self, ending_type: EndingType, reason: str):
        self.type = ending_type
        self.reason = reason


def check_end_conditions(
    *,
    state: GameState,
    registry: AgentRegistry,
    tension: float,
) -> Optional[Ending]:
    """
    Check whether the game has reached an end state.
    """

    avg_drift = (
        sum(rt.drift for rt in registry.runtime.values())
        / len(registry.runtime)
    )

    # --- Institutional Lock-In ---
    if tension < 0.1 and state.turn >= 6:
        return Ending(
            EndingType.INSTITUTIONAL_LOCK_IN,
            "The system has become stable and predictable, but no longer produces new understanding.",
        )

    # --- Cognitive Collapse ---
    if tension > 0.9 and avg_drift > 0.7:
        return Ending(
            EndingType.COGNITIVE_COLLAPSE,
            "Conflicting optimizations have destroyed the system's ability to reason coherently.",
        )

    # --- Institutional Termination ---
    if tension > 0.75 and state.turn >= 10:
        return Ending(
            EndingType.INSTITUTIONAL_TERMINATION,
            "External oversight determines the system is no longer controllable.",
        )

    return None
