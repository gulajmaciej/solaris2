from dataclasses import dataclass, field
from typing import Dict


# --------------------------------------------------
# SUBSTATES
# --------------------------------------------------

@dataclass
class OceanState:
    activity: float = 0.2
    instability: float = 0.1


@dataclass
class CrewState:
    stress: float = 0.1
    fatigue: float = 0.0


@dataclass
class StationState:
    integrity: float = 1.0
    power_level: float = 0.95


# --------------------------------------------------
# GAME STATE
# --------------------------------------------------

@dataclass
class GameState:
    turn: int
    ocean: OceanState
    crew: CrewState
    station: StationState
    flags: Dict[str, bool] = field(default_factory=dict)

    @classmethod
    def initial(cls) -> "GameState":
        """
        Factory method creating the initial game state.
        Centralized on purpose.
        """
        return cls(
            turn=1,
            ocean=OceanState(),
            crew=CrewState(),
            station=StationState(),
            flags={},
        )

    def next_turn(self) -> None:
        self.turn += 1
