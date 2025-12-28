from agents.langgraph_state import InstrumentAgentState
from agents.langgraph_instrument import build_instrument_graph


_graph = build_instrument_graph()
_state = InstrumentAgentState()


def observe(state, drift, solaris):
    global _state

    result = _graph.invoke(_state)

    # Reconstruct state from LangGraph dict
    _state = InstrumentAgentState(
        hypothesis=result.get("hypothesis", _state.hypothesis),
        confidence=result.get("confidence", _state.confidence),
        contradictions=result.get("contradictions", _state.contradictions),
        last_observation=result.get("last_observation", ""),
        visited_nodes=result.get("visited_nodes", []),
        last_route=result.get("last_route"),
    )

    return _state.last_observation


def debug_render() -> None:
    """
    Diagnostic-only visualization of the LangGraph agent.
    """
    print("\n--- INSTRUMENT AGENT (LangGraph DEBUG) ---")
    print("Visited nodes:")
    print("  " + " → ".join(_state.visited_nodes))

    print("\nLast routing decision:")
    print(f"  { _state.last_route }")

    print("\nHypothesis:")
    print(f"  {_state.hypothesis}")

    print("\nConfidence:")
    print(f"  {round(_state.confidence, 3)}")

    print("\nContradictions:")
    print(f"  {_state.contradictions}")

    print("\nLast observation:")
    print(f"  {_state.last_observation}")
    print("----------------------------------------")
