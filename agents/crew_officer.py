import json
from typing import Callable

from langgraph.checkpoint.memory import InMemorySaver

from agents.langgraph_state import CrewOfficerState, default_crew_state
from agents.langgraph_crew import build_crew_graph
from core.state import GameState
from core.solaris import SolarisState


class CrewOfficerAgent:
    def __init__(
        self,
        *,
        checkpointer=None,
        thread_id: str = "crew_officer",
        log_sink: Callable[[dict], None] | None = None,
    ) -> None:
        self._checkpointer = checkpointer or InMemorySaver()
        self._graph = build_crew_graph(checkpointer=self._checkpointer)
        self._thread_id = thread_id
        self._log_sink = log_sink

    def _config(self, *, thread_id: str | None = None) -> dict:
        return {"configurable": {"thread_id": thread_id or self._thread_id}}

    def _get_state(self, *, thread_id: str | None = None) -> CrewOfficerState:
        try:
            snapshot = self._graph.get_state(self._config(thread_id=thread_id))
        except Exception:
            return default_crew_state()
        if snapshot and snapshot.values:
            return snapshot.values
        return default_crew_state()

    def _run_graph(
        self,
        *,
        phase: str,
        drift: float | None = None,
        thread_id: str | None = None,
    ) -> CrewOfficerState:
        current = self._get_state(thread_id=thread_id)
        current["phase"] = phase
        if drift is not None:
            current["drift"] = drift

        last_values: CrewOfficerState | None = None
        for mode, chunk in self._graph.stream(
            current,
            config=self._config(thread_id=thread_id),
            stream_mode=["custom", "values"],
        ):
            if mode == "custom":
                if self._log_sink:
                    self._log_sink(chunk)
                else:
                    print(json.dumps(chunk, ensure_ascii=True), flush=True)
            elif mode == "values":
                last_values = chunk

        return last_values or current

    def act(
        self,
        *,
        drift: float,
        thread_id: str | None = None,
    ) -> None:
        self._run_graph(phase="tool", drift=drift, thread_id=thread_id)

    def observe(
        self,
        state: GameState,
        drift: float,
        solaris: SolarisState,
        *,
        thread_id: str | None = None,
    ) -> str:
        result = self._run_graph(phase="observe", drift=drift, thread_id=thread_id)
        return result.get("last_observation", "")

    def debug_render(self, *, thread_id: str | None = None) -> None:
        state = self._get_state(thread_id=thread_id)

        print("\n--- CREW OFFICER (LangGraph DEBUG) ---")
        print("Visited nodes:")
        print("  " + " ƒÅ' ".join(state["visited_nodes"]))

        print("\nCrew snapshot:")
        print(f"  stress={state['crew_stress']:.2f}")
        print(f"  fatigue={state['crew_fatigue']:.2f}")

        print("\nCognitive context:")
        print(f"  drift={state['drift']:.2f}")
        print(f"  solaris_intensity={state['solaris_intensity']:.2f}")

        print("\nLast observation:")
        print(f"  {state['last_observation']}")
        print("----------------------------------------")
