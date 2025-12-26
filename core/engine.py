from typing import List

from core.state import GameState
from core.actions import apply_action
from agents.planner import AgentPlan


class GameEngine:
    """
    Deterministic game engine.
    Executes agent plans against the world state.
    """

    def execute_plans(
        self,
        *,
        state: GameState,
        plans: List[AgentPlan],
    ) -> None:
        """
        Execute all planned actions in order of agent priority.
        """

        # sort plans by priority (HIGH first)
        sorted_plans = sorted(
            plans,
            key=lambda p: p.priority.value,
            reverse=True,
        )

        for plan in sorted_plans:
            for action in plan.actions:
                apply_action(state=state, action=action)
