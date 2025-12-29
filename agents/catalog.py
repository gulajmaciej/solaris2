from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Dict, Iterable

from agents.config import AgentConfig, AgentGoal, PriorityLevel
from agents.instrument_specialist import InstrumentSpecialistAgent
from agents.crew_officer import CrewOfficerAgent

ActFn = Callable[[object, float | None, str], None]
ObserveFn = Callable[[object, object, float, object, str], str]


@dataclass(frozen=True)
class AgentSpec:
    agent_id: str
    agent_cls: type
    default_config: AgentConfig
    allowed_goals: set[AgentGoal]
    act: ActFn
    observe: ObserveFn


def _instrument_act(agent: InstrumentSpecialistAgent, drift: float | None, thread_id: str) -> None:
    agent.act(thread_id=thread_id)


def _instrument_observe(
    agent: InstrumentSpecialistAgent,
    state,
    drift: float,
    solaris,
    thread_id: str,
) -> str:
    return agent.observe(state, drift, solaris, thread_id=thread_id)


def _crew_act(agent: CrewOfficerAgent, drift: float | None, thread_id: str) -> None:
    if drift is None:
        drift = 0.0
    agent.act(drift=drift, thread_id=thread_id)


def _crew_observe(
    agent: CrewOfficerAgent,
    state,
    drift: float,
    solaris,
    thread_id: str,
) -> str:
    return agent.observe(state, drift, solaris, thread_id=thread_id)


_CATALOG: Dict[str, AgentSpec] = {
    "instrument_specialist": AgentSpec(
        agent_id="instrument_specialist",
        agent_cls=InstrumentSpecialistAgent,
        default_config=AgentConfig(
            goal=AgentGoal.MAXIMIZE_ANOMALY_DETECTION,
            priority=PriorityLevel.HIGH,
        ),
        allowed_goals={
            AgentGoal.MAXIMIZE_ANOMALY_DETECTION,
            AgentGoal.STABILIZE_MEASUREMENT_BASELINES,
            AgentGoal.REDUCE_DATA_UNCERTAINTY,
        },
        act=_instrument_act,
        observe=_instrument_observe,
    ),
    "crew_officer": AgentSpec(
        agent_id="crew_officer",
        agent_cls=CrewOfficerAgent,
        default_config=AgentConfig(
            goal=AgentGoal.MINIMIZE_CREW_STRESS,
            priority=PriorityLevel.MEDIUM,
        ),
        allowed_goals={
            AgentGoal.MINIMIZE_CREW_STRESS,
            AgentGoal.MAINTAIN_OPERATIONAL_EFFICIENCY,
            AgentGoal.PRESERVE_CREW_COHESION,
        },
        act=_crew_act,
        observe=_crew_observe,
    ),
}


def get_agent_spec(agent_id: str) -> AgentSpec:
    return _CATALOG[agent_id]


def list_agent_specs() -> Iterable[AgentSpec]:
    return _CATALOG.values()
