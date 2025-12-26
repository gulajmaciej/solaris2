from dataclasses import dataclass
from enum import Enum
from typing import Dict


class AgentGoal(Enum):
    # Instrument Specialist goals
    MAXIMIZE_ANOMALY_DETECTION = "maximize_anomaly_detection"
    STABILIZE_MEASUREMENT_BASELINES = "stabilize_measurement_baselines"
    REDUCE_DATA_UNCERTAINTY = "reduce_data_uncertainty"

    # Crew Officer goals
    MINIMIZE_CREW_STRESS = "minimize_crew_stress"
    MAINTAIN_OPERATIONAL_EFFICIENCY = "maintain_operational_efficiency"
    PRESERVE_CREW_COHESION = "preserve_crew_cohesion"


class PriorityLevel(Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3


@dataclass
class AgentConfig:
    """
    Configuration describing *what* the agent is optimizing
    and *how important* it is relative to other agents.

    This is NOT world state.
    This is NOT agent memory.
    This is a managerial / governance layer.
    """
    goal: AgentGoal
    priority: PriorityLevel


@dataclass
class AgentRuntimeState:
    """
    Runtime-only state of an agent.

    This is deliberately separated from:
    - GameState (world)
    - AgentConfig (intentions)
    """
    drift: float = 0.0


class AgentRegistry:
    """
    Central registry holding configurations and runtime state
    for all agents.

    This is a thin data container, NOT a manager.
    """

    def __init__(self):
        self.configs: Dict[str, AgentConfig] = {}
        self.runtime: Dict[str, AgentRuntimeState] = {}

    def register_agent(
        self,
        agent_id: str,
        config: AgentConfig,
    ) -> None:
        self.configs[agent_id] = config
        self.runtime[agent_id] = AgentRuntimeState()

    def set_goal(
        self,
        agent_id: str,
        goal: AgentGoal,
    ) -> None:
        if agent_id not in self.configs:
            raise KeyError(f"Agent '{agent_id}' not registered")

        self.configs[agent_id].goal = goal

    def set_priority(
        self,
        agent_id: str,
        priority: PriorityLevel,
    ) -> None:
        if agent_id not in self.configs:
            raise KeyError(f"Agent '{agent_id}' not registered")

        self.configs[agent_id].priority = priority

    def get_config(self, agent_id: str) -> AgentConfig:
        return self.configs[agent_id]

    def get_runtime(self, agent_id: str) -> AgentRuntimeState:
        return self.runtime[agent_id]
