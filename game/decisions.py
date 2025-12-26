from enum import Enum
from core.actions import PlayerAction


class PlayerDecision(Enum):
    INTENSIFY_RESEARCH = PlayerAction.INTENSIFY_RESEARCH
    STABILIZE_CREW = PlayerAction.STABILIZE_CREW
    OBSERVE_ONLY = PlayerAction.OBSERVE_ONLY

    @staticmethod
    def available(earth_pressure: float) -> list["PlayerDecision"]:
        decisions = [
            PlayerDecision.INTENSIFY_RESEARCH,
            PlayerDecision.STABILIZE_CREW,
            PlayerDecision.OBSERVE_ONLY,
        ]

        if earth_pressure >= 0.3:
            decisions.remove(PlayerDecision.INTENSIFY_RESEARCH)

        if earth_pressure >= 0.6:
            if PlayerDecision.OBSERVE_ONLY in decisions:
                decisions.remove(PlayerDecision.OBSERVE_ONLY)

        if earth_pressure >= 0.85:
            decisions = [PlayerDecision.STABILIZE_CREW]

        return decisions

    @staticmethod
    def from_input(value: str, available: list["PlayerDecision"]):
        mapping = {str(i + 1): d for i, d in enumerate(available)}
        return mapping.get(value)
