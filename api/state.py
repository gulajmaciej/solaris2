from core.state import GameState
from core.engine import GameEngine
from core.earth import EarthState
from core.solaris import SolarisState

from agents.config import AgentRegistry
from agents.catalog import list_agent_specs


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
        for spec in list_agent_specs():
            self.registry.register_agent(spec.agent_id, spec.default_config)

        self.agents = {
            spec.agent_id: spec.agent_cls(
                thread_id=f"{self.thread_id}:{spec.agent_id}"
            )
            for spec in list_agent_specs()
        }


# SINGLETON (intentional for now)
SESSION = GameSession()
