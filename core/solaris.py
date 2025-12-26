from dataclasses import dataclass


@dataclass
class SolarisState:
    """
    Cognitive distortion field.
    Solaris does not act.
    Solaris distorts meaning.
    """
    intensity: float = 0.0


def update_solaris_intensity(
    *,
    solaris: SolarisState,
    tension: float,
    earth_pressure: float,
) -> None:
    """
    Deterministic update of Solaris distortion.
    """

    base = (tension * 0.6) + (earth_pressure * 0.4)
    solaris.intensity = max(0.0, min(1.0, base))
