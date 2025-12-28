from dataclasses import dataclass
from agents.config import AgentRegistry


@dataclass
class EarthState:
    """
    Institutional oversight state.
    Earth is NOT an agent.
    It reacts deterministically to system instability,
    with memory and delayed response (hysteresis).
    """
    pressure: float = 0.2


# --- tuning constants ---
HIGH_TENSION_THRESHOLD = 0.7
LOW_TENSION_THRESHOLD = 0.2

PRESSURE_INCREASE = 0.05
PRESSURE_DECREASE = 0.03

DRIFT_SENSITIVITY = 0.4

# --- hysteresis configuration ---
HIGH_TENSION_STREAK_REQUIRED = 3
LOW_TENSION_STREAK_REQUIRED = 4

STREAK_DECAY = 1  # how fast streaks decay when tension is neutral


def update_earth_pressure(
    *,
    earth: EarthState,
    registry: AgentRegistry,
    tension: float,
) -> None:
    """
    Update Earth pressure with hysteresis.
    Earth reacts to sustained trends, not single-turn impulses.
    """

    # --- init memory in registry flags ---
    flags = registry.flags

    high_streak = flags.get("earth_high_tension_streak", 0)
    low_streak = flags.get("earth_low_tension_streak", 0)

    # --- update streaks based on tension ---
    if tension >= HIGH_TENSION_THRESHOLD:
        high_streak += 1
        low_streak = 0

    elif tension <= LOW_TENSION_THRESHOLD:
        low_streak += 1
        high_streak = 0

    else:
        # neutral zone → decay streaks slowly
        high_streak = max(0, high_streak - STREAK_DECAY)
        low_streak = max(0, low_streak - STREAK_DECAY)

    # --- apply pressure changes ONLY if streaks persist ---
    if high_streak >= HIGH_TENSION_STREAK_REQUIRED:
        earth.pressure += PRESSURE_INCREASE
        high_streak = 0  # reset after reaction

    elif low_streak >= LOW_TENSION_STREAK_REQUIRED:
        earth.pressure -= PRESSURE_DECREASE
        low_streak = 0  # reset after reaction

    # --- drift influence (slow, continuous) ---
    if registry.runtime:
        avg_drift = (
            sum(rt.drift for rt in registry.runtime.values())
            / len(registry.runtime)
        )
        earth.pressure += avg_drift * DRIFT_SENSITIVITY * 0.02

    # --- clamp pressure ---
    earth.pressure = max(0.0, min(1.0, earth.pressure))

    # --- persist memory ---
    flags["earth_high_tension_streak"] = high_streak
    flags["earth_low_tension_streak"] = low_streak
