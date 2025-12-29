from dataclasses import dataclass
from types import SimpleNamespace
from typing import Dict, Optional, Callable

from core.state import GameState
from core.engine import GameEngine
from core.earth import EarthState
from core.solaris import SolarisState, update_solaris_intensity

from agents.config import AgentRegistry
from agents.catalog import list_agent_specs, get_agent_spec

from game.turn import run_turn
from game.endings import Ending, check_end_conditions
from game.decision import PlayerDecision
from mcp.context import set_session


Observer = Callable[..., str]


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
        agents: Dict[str, object] | None = None,
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
        self.agents = agents or {
            spec.agent_id: spec.agent_cls(
                thread_id=f"{self.thread_id}:{spec.agent_id}",
                log_sink=log_sink,
            )
            for spec in list_agent_specs()
        }
        base_observers = DEFAULT_OBSERVERS.copy()
        for spec in list_agent_specs():
            base_observers[spec.agent_id] = self._observe_agent
        self.observers = observers or base_observers

    def _observe_agent(
        self,
        state: GameState,
        drift: float,
        solaris: SolarisState,
        *,
        agent_id: str,
    ) -> str:
        spec = get_agent_spec(agent_id)
        agent = self.agents[agent_id]
        return spec.observe(
            agent,
            state,
            drift,
            solaris,
            f"{self.thread_id}:{agent_id}",
        )

    def _default_registry(self) -> AgentRegistry:
        registry = AgentRegistry()
        for spec in list_agent_specs():
            registry.register_agent(spec.agent_id, spec.default_config)
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
            spec = get_agent_spec(agent_id)
            agent = self.agents[agent_id]
            spec.act(agent, drift, f"{self.thread_id}:{agent_id}")

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
            reports[agent_id] = observer(
                self.state,
                drift,
                self.solaris,
                agent_id=agent_id,
            )

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
