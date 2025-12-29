from typing import List, TypedDict


class InstrumentAgentState(TypedDict):
    """
    Explicit cognitive state of the instrument specialist.
    """
    hypothesis: str
    confidence: float
    contradictions: int
    last_observation: str

    # --- DEBUG / TRACE ---
    visited_nodes: List[str]
    last_route: str | None
    crew_stress: float
    crew_fatigue: float
    crew_confidence_delta: float
    crew_contradiction_delta: int
    phase: str
    tool_decision: str | None
    tool_reason: str
    tool_applied: bool
    ocean_activity: float
    ocean_instability: float
    station_power_level: float
    tension: float
    solaris_intensity: float


def default_instrument_state() -> InstrumentAgentState:
    return {
        "hypothesis": "No coherent pattern detected",
        "confidence": 0.3,
        "contradictions": 0,
        "last_observation": "",
        "visited_nodes": [],
        "last_route": None,
        "crew_stress": 0.0,
        "crew_fatigue": 0.0,
        "crew_confidence_delta": 0.0,
        "crew_contradiction_delta": 0,
        "phase": "observe",
        "tool_decision": None,
        "tool_reason": "",
        "tool_applied": False,
        "ocean_activity": 0.0,
        "ocean_instability": 0.0,
        "station_power_level": 0.0,
        "tension": 0.0,
        "solaris_intensity": 0.0,
    }


class CrewOfficerState(TypedDict):
    """
    Explicit cognitive state of the crew officer.
    """
    crew_stress: float
    crew_fatigue: float
    drift: float
    solaris_intensity: float
    last_observation: str
    visited_nodes: List[str]
    tension: float
    phase: str
    tool_decision: str | None
    tool_reason: str
    tool_applied: bool


def default_crew_state() -> CrewOfficerState:
    return {
        "crew_stress": 0.0,
        "crew_fatigue": 0.0,
        "drift": 0.0,
        "solaris_intensity": 0.0,
        "last_observation": "",
        "visited_nodes": [],
        "tension": 0.0,
        "phase": "observe",
        "tool_decision": None,
        "tool_reason": "",
        "tool_applied": False,
    }
