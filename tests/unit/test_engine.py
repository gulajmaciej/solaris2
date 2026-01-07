import pytest

from agents.config import AgentGoal, PriorityLevel
from agents.planner import AgentPlan, PlannedAction
from core.engine import GameEngine
from core.state import GameState


@pytest.mark.unit
def test_execute_plans_respects_priority_order():
    state = GameState.initial()
    state.ocean.activity = 0.99

    high_plan = AgentPlan(
        agent_id="high",
        goal=AgentGoal.MAXIMIZE_ANOMALY_DETECTION,
        priority=PriorityLevel.HIGH,
        actions=[PlannedAction.INCREASE_MEASUREMENT_FREQUENCY],
    )
    low_plan = AgentPlan(
        agent_id="low",
        goal=AgentGoal.STABILIZE_MEASUREMENT_BASELINES,
        priority=PriorityLevel.LOW,
        actions=[PlannedAction.FILTER_DATA_AGGRESSIVELY],
    )

    engine = GameEngine()
    engine.execute_plans(state=state, plans=[low_plan, high_plan])

    assert state.ocean.activity == 0.98
