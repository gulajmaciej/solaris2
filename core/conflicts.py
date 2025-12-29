from typing import Dict, Tuple
from agents.config import AgentGoal


# Conflict scale:
# 0 = none, 1 = soft, 2 = structural, 3 = critical

CONFLICT_SCALE = 0.5

CONFLICT_MATRIX: Dict[Tuple[AgentGoal, AgentGoal], int] = {
    # Instrument Specialist vs Crew Officer
    (AgentGoal.MAXIMIZE_ANOMALY_DETECTION, AgentGoal.MINIMIZE_CREW_STRESS): 3,
    (AgentGoal.MAXIMIZE_ANOMALY_DETECTION, AgentGoal.MAINTAIN_OPERATIONAL_EFFICIENCY): 2,
    (AgentGoal.MAXIMIZE_ANOMALY_DETECTION, AgentGoal.PRESERVE_CREW_COHESION): 2,

    (AgentGoal.STABILIZE_MEASUREMENT_BASELINES, AgentGoal.MINIMIZE_CREW_STRESS): 1,
    (AgentGoal.STABILIZE_MEASUREMENT_BASELINES, AgentGoal.MAINTAIN_OPERATIONAL_EFFICIENCY): 0,
    (AgentGoal.STABILIZE_MEASUREMENT_BASELINES, AgentGoal.PRESERVE_CREW_COHESION): 1,

    (AgentGoal.REDUCE_DATA_UNCERTAINTY, AgentGoal.MINIMIZE_CREW_STRESS): 2,
    (AgentGoal.REDUCE_DATA_UNCERTAINTY, AgentGoal.MAINTAIN_OPERATIONAL_EFFICIENCY): 1,
    (AgentGoal.REDUCE_DATA_UNCERTAINTY, AgentGoal.PRESERVE_CREW_COHESION): 2,
}


def conflict_strength(goal_a: AgentGoal, goal_b: AgentGoal) -> float:
    """
    Symmetric conflict lookup.
    """
    if (goal_a, goal_b) in CONFLICT_MATRIX:
        return CONFLICT_MATRIX[(goal_a, goal_b)] * CONFLICT_SCALE
    if (goal_b, goal_a) in CONFLICT_MATRIX:
        return CONFLICT_MATRIX[(goal_b, goal_a)] * CONFLICT_SCALE
    return 0.0
