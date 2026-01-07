import pytest

from agents.config import AgentRegistry, AgentConfig, AgentGoal, PriorityLevel
from core.tension import compute_delta_tension, update_tension_and_drift


@pytest.mark.unit
def test_compute_delta_tension_positive_for_conflict():
    registry = AgentRegistry()
    registry.register_agent(
        "a",
        AgentConfig(
            AgentGoal.MAXIMIZE_ANOMALY_DETECTION,
            PriorityLevel.HIGH,
        ),
    )
    registry.register_agent(
        "b",
        AgentConfig(
            AgentGoal.MINIMIZE_CREW_STRESS,
            PriorityLevel.MEDIUM,
        ),
    )
    delta = compute_delta_tension(registry)
    assert delta > 0.0


@pytest.mark.unit
def test_update_tension_and_drift_updates_runtime():
    registry = AgentRegistry()
    registry.register_agent(
        "a",
        AgentConfig(
            AgentGoal.MAXIMIZE_ANOMALY_DETECTION,
            PriorityLevel.HIGH,
        ),
    )
    registry.register_agent(
        "b",
        AgentConfig(
            AgentGoal.MINIMIZE_CREW_STRESS,
            PriorityLevel.MEDIUM,
        ),
    )
    next_tension = update_tension_and_drift(
        registry=registry,
        current_tension=0.2,
    )
    assert 0.0 <= next_tension <= 1.0
    assert registry.runtime["a"].drift >= 0.0
