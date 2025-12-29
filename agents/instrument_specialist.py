import json
from typing import Callable

from langgraph.checkpoint.memory import InMemorySaver

from agents.langgraph_state import (
    InstrumentAgentState,
    default_instrument_state,
)
from agents.langgraph_instrument import build_instrument_graph


class InstrumentSpecialistAgent:
    def __init__(
        self,
        *,
        checkpointer=None,
        thread_id: str = "instrument_specialist",
        log_sink: Callable[[dict], None] | None = None,
    ) -> None:
        self._checkpointer = checkpointer or InMemorySaver()
        self._graph = build_instrument_graph(
            checkpointer=self._checkpointer,
        )
        self._thread_id = thread_id
        self._log_sink = log_sink

    def _config(self, *, thread_id: str | None = None) -> dict:
        return {"configurable": {"thread_id": thread_id or self._thread_id}}

    def _get_state(self, *, thread_id: str | None = None) -> InstrumentAgentState:
        try:
            snapshot = self._graph.get_state(self._config(thread_id=thread_id))
        except Exception:
            return default_instrument_state()
        if snapshot and snapshot.values:
            return snapshot.values
        return default_instrument_state()

    def _run_graph(
        self,
        *,
        phase: str,
        thread_id: str | None = None,
    ) -> InstrumentAgentState:
        current = self._get_state(thread_id=thread_id)
        current["phase"] = phase

        last_values: InstrumentAgentState | None = None
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

    def act(self, *, thread_id: str | None = None) -> None:
        self._run_graph(phase="tool", thread_id=thread_id)

    def observe(self, state, drift, solaris, *, thread_id: str | None = None) -> str:
        result = self._run_graph(phase="observe", thread_id=thread_id)
        return result.get("last_observation", "")

    def debug_render(self, *, thread_id: str | None = None) -> None:
        """
        Diagnostic-only visualization of the LangGraph agent.
        """
        state = self._get_state(thread_id=thread_id)

        print("\n--- INSTRUMENT AGENT (LangGraph DEBUG) ---")
        print("Visited nodes:")
        print("  " + " ƒÅ' ".join(state["visited_nodes"]))

        print("\nLast routing decision:")
        print(f"  {state['last_route']}")

        print("\nHypothesis:")
        print(f"  {state['hypothesis']}")

        print("\nConfidence:")
        print(f"  {round(state['confidence'], 3)}")

        print("\nContradictions:")
        print(f"  {state['contradictions']}")

        print("\nLast observation:")
        print(f"  {state['last_observation']}")

        if (
            state["crew_confidence_delta"] != 0.0
            or state["crew_contradiction_delta"] != 0
        ):
            print("\nCrew context:")
            print(
                "  "
                f"stress={state['crew_stress']:.2f}, "
                f"fatigue={state['crew_fatigue']:.2f}, "
                f"confidence_delta={state['crew_confidence_delta']:+.4f}, "
                f"contradiction_delta={state['crew_contradiction_delta']:+d}"
            )
        print("----------------------------------------")
