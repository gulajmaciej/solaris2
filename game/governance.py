from agents.config import AgentGoal, PriorityLevel
from game.decision import PlayerDecision
from core.earth import EarthState


def apply_earth_constraints(
    *,
    decision: PlayerDecision,
    earth: EarthState,
) -> PlayerDecision:
    """
    Institutional constraints applied to player decisions.
    Earth does NOT change the world directly.
    It constrains governance.
    """

    # Soft constraints
    if earth.pressure >= 0.5:
        if decision.goal == AgentGoal.MAXIMIZE_ANOMALY_DETECTION:
            decision.priority = PriorityLevel.LOW

    # Hard constraints
    if earth.pressure >= 0.75:
        if decision.goal in {
            AgentGoal.MAXIMIZE_ANOMALY_DETECTION,
            AgentGoal.REDUCE_DATA_UNCERTAINTY,
        }:
            decision.goal = AgentGoal.STABILIZE_MEASUREMENT_BASELINES
            decision.priority = PriorityLevel.LOW

    return decision
