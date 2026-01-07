import pytest

from agents.config import AgentRegistry, AgentConfig, AgentGoal, PriorityLevel
from core.earth import (
    EarthState,
    update_earth_pressure,
    HIGH_TENSION_THRESHOLD,
    HIGH_TENSION_STREAK_REQUIRED,
)


@pytest.mark.unit
def test_earth_pressure_increases_after_high_streak():
    registry = AgentRegistry()
    registry.register_agent(
        "a",
        AgentConfig(
            AgentGoal.MAXIMIZE_ANOMALY_DETECTION,
            PriorityLevel.HIGH,
        ),
    )
    earth = EarthState(pressure=0.2)

    for _ in range(HIGH_TENSION_STREAK_REQUIRED):
        update_earth_pressure(
            earth=earth,
            registry=registry,
            tension=HIGH_TENSION_THRESHOLD,
        )

    assert earth.pressure >= 0.2
