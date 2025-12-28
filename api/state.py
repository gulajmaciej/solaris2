from core.state import GameState
from core.engine import GameEngine
from core.earth import EarthState
from core.solaris import SolarisState

from agents.config import (
    AgentRegistry,
    AgentConfig,
    AgentGoal,
    PriorityLevel,
)
from agents.instrument_specialist import InstrumentSpecialistAgent
from agents.crew_officer import CrewOfficerAgent


class GameSession:
    """
    Shared in-memory game session.
    Used by:
    - FastAPI (player turns)
    - MCP Server (agent tools)
    """

    def __init__(self):
        self.thread_id = "api"
        self.state = GameState.initial()
        self.tension = 0.0
        self.earth = EarthState()
        self.solaris = SolarisState()
        self.engine = GameEngine()

        self.registry = AgentRegistry()
        self.registry.register_agent(
            "instrument_specialist",
            AgentConfig(
                goal=AgentGoal.MAXIMIZE_ANOMALY_DETECTION,
                priority=PriorityLevel.HIGH,
            ),
        )
        self.registry.register_agent(
            "crew_officer",
            AgentConfig(
                goal=AgentGoal.MINIMIZE_CREW_STRESS,
                priority=PriorityLevel.MEDIUM,
            ),
        )

        self.instrument_agent = InstrumentSpecialistAgent(
            thread_id=f"{self.thread_id}:instrument_specialist"
        )
        self.crew_agent = CrewOfficerAgent(
            thread_id=f"{self.thread_id}:crew_officer"
        )


# SINGLETON (intentional for now)
SESSION = GameSession()
