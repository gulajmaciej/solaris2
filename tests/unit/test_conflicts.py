import pytest

from agents.config import AgentGoal
from core.conflicts import conflict_strength


@pytest.mark.unit
def test_conflict_strength_symmetric():
    a = AgentGoal.MAXIMIZE_ANOMALY_DETECTION
    b = AgentGoal.MINIMIZE_CREW_STRESS
    assert conflict_strength(a, b) == conflict_strength(b, a)


@pytest.mark.unit
def test_conflict_strength_missing_pair_is_zero():
    a = AgentGoal.PRESERVE_CREW_COHESION
    b = AgentGoal.PRESERVE_CREW_COHESION
    assert conflict_strength(a, b) == 0.0
