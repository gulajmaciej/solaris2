from dataclasses import dataclass
from types import SimpleNamespace
from typing import Dict, Optional, Callable

from core.state import GameState
from core.engine import GameEngine
from core.earth import EarthState
from core.solaris import SolarisState, update_solaris_intensity

from agents.config import (
    AgentRegistry,
    AgentConfig,
    AgentGoal,
    PriorityLevel,
)
from agents.instrument_specialist import InstrumentSpecialistAgent
from agents.crew_officer import CrewOfficerAgent

from game.turn import run_turn
from game.endings import Ending, check_end_conditions
from game.decision import PlayerDecision
from mcp.context import set_session


Observer = Callable[[GameState, float, SolarisState], str]


DEFAULT_OBSERVERS: Dict[str, Observer] = {}


@dataclass
class TurnResult:
    state: GameState
    tension: float
    earth_pressure: float
    solaris_intensity: float
    drift_levels: Dict[str, float]
    reports: Dict[str, str]
    ending: Optional[Ending]


class SimulationRunner:
    def __init__(
        self,
        *,
        state: GameState | None = None,
        engine: GameEngine | None = None,
        earth: EarthState | None = None,
        solaris: SolarisState | None = None,
        registry: AgentRegistry | None = None,
        tension: float = 0.0,
        observers: Dict[str, Observer] | None = None,
        instrument_agent: InstrumentSpecialistAgent | None = None,
        crew_agent: CrewOfficerAgent | None = None,
        thread_id: str = "default",
        log_sink=None,
    ) -> None:
        self.state = state or GameState.initial()
        self.engine = engine or GameEngine()
        self.earth = earth or EarthState()
        self.solaris = solaris or SolarisState()
        self.registry = registry or self._default_registry()
        self.tension = tension
        self.thread_id = thread_id
        self.instrument_agent = instrument_agent or InstrumentSpecialistAgent(
            thread_id=f"{self.thread_id}:instrument_specialist",
            log_sink=log_sink,
        )
        self.crew_agent = crew_agent or CrewOfficerAgent(
            thread_id=f"{self.thread_id}:crew_officer",
            log_sink=log_sink,
        )
        base_observers = DEFAULT_OBSERVERS.copy()
        base_observers["instrument_specialist"] = self._observe_instrument
        base_observers["crew_officer"] = self._observe_crew
        self.observers = observers or base_observers

    def _observe_instrument(
        self,
        state: GameState,
        drift: float,
        solaris: SolarisState,
    ) -> str:
        return self.instrument_agent.observe(
            state,
            drift,
            solaris,
            thread_id=f"{self.thread_id}:instrument_specialist",
        )

    def _observe_crew(
        self,
        state: GameState,
        drift: float,
        solaris: SolarisState,
    ) -> str:
        return self.crew_agent.observe(
            state,
            drift,
            solaris,
            thread_id=f"{self.thread_id}:crew_officer",
        )

    def _default_registry(self) -> AgentRegistry:
        registry = AgentRegistry()
        registry.register_agent(
            "instrument_specialist",
            AgentConfig(
                goal=AgentGoal.MAXIMIZE_ANOMALY_DETECTION,
                priority=PriorityLevel.HIGH,
            ),
        )
        registry.register_agent(
            "crew_officer",
            AgentConfig(
                goal=AgentGoal.MINIMIZE_CREW_STRESS,
                priority=PriorityLevel.MEDIUM,
            ),
        )
        return registry

    def step(self, decisions: list[PlayerDecision]) -> TurnResult:
        def _set_mcp_context() -> None:
            set_session(
                SimpleNamespace(
                    state=self.state,
                    tension=self.tension,
                    earth=self.earth,
                    solaris=self.solaris,
                    registry=self.registry,
                )
            )

        _set_mcp_context()

        for agent_id in self.registry.configs:
            drift = self.registry.get_runtime(agent_id).drift
            if agent_id == "instrument_specialist":
                self.instrument_agent.act(
                    thread_id=f"{self.thread_id}:instrument_specialist",
                )
            elif agent_id == "crew_officer":
                self.crew_agent.act(
                    drift=drift,
                    thread_id=f"{self.thread_id}:crew_officer",
                )

        self.tension = run_turn(
            state=self.state,
            registry=self.registry,
            decisions=decisions,
            engine=self.engine,
            current_tension=self.tension,
            earth=self.earth,
        )

        update_solaris_intensity(
            solaris=self.solaris,
            tension=self.tension,
            earth_pressure=self.earth.pressure,
        )
        _set_mcp_context()

        reports: Dict[str, str] = {}
        for agent_id in self.registry.configs:
            observer = self.observers.get(agent_id)
            if not observer:
                continue
            drift = self.registry.get_runtime(agent_id).drift
            reports[agent_id] = observer(self.state, drift, self.solaris)

        drift_levels = {
            agent_id: runtime.drift
            for agent_id, runtime in self.registry.runtime.items()
        }

        ending = check_end_conditions(
            state=self.state,
            registry=self.registry,
            tension=self.tension,
        )

        return TurnResult(
            state=self.state,
            tension=self.tension,
            earth_pressure=self.earth.pressure,
            solaris_intensity=self.solaris.intensity,
            drift_levels=drift_levels,
            reports=reports,
            ending=ending,
        )
