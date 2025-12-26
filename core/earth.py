from dataclasses import dataclass
from agents.config import AgentRegistry


@dataclass
class EarthState:
    """
    Institutional oversight state.
    Earth is NOT an agent.
    It reacts deterministically to system instability.
    """
    pressure: float = 0.2


# --- tuning constants ---
HIGH_TENSION_THRESHOLD = 0.7
LOW_TENSION_THRESHOLD = 0.2

PRESSURE_INCREASE = 0.05
PRESSURE_DECREASE = 0.03

DRIFT_SENSITIVITY = 0.4


def update_earth_pressure(
    *,
    earth: EarthState,
    registry: AgentRegistry,
    tension: float,
) -> None:
    avg_drift = (
        sum(rt.drift for rt in registry.runtime.values())
        / len(registry.runtime)
    )

    if tension >= HIGH_TENSION_THRESHOLD:
        earth.pressure += PRESSURE_INCREASE
    elif tension <= LOW_TENSION_THRESHOLD:
        earth.pressure -= PRESSURE_DECREASE

    earth.pressure += avg_drift * DRIFT_SENSITIVITY * 0.02

    earth.pressure = max(0.0, min(1.0, earth.pressure))
