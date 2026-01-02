from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import InMemorySaver

from agents.instrument_specialist.state import InstrumentAgentState
from agents.instrument_specialist.nodes import (
    read_context,
    decide_tool,
    apply_tool,
    observe,
    update_hypothesis,
    apply_crew_context,
    evaluate_concern,
    flag_event,
)


def build_instrument_graph(*, checkpointer=None):
    graph = StateGraph(InstrumentAgentState)

    graph.add_node("read_context", read_context)
    graph.add_node("decide_tool", decide_tool)
    graph.add_node("apply_tool", apply_tool)
    graph.add_node("observe", observe)
    graph.add_node("update_hypothesis", update_hypothesis)
    graph.add_node("apply_crew_context", apply_crew_context)
    graph.add_node("flag_event", flag_event)

    graph.set_entry_point("read_context")

    def route_after_context(state: InstrumentAgentState) -> str:
        return "decide_tool" if state["phase"] == "tool" else "observe"

    def route_after_tool(state: InstrumentAgentState) -> str:
        return "end" if state["phase"] == "tool" else "observe"

    graph.add_conditional_edges(
        "read_context",
        route_after_context,
        {
            "decide_tool": "decide_tool",
            "observe": "observe",
        },
    )

    graph.add_edge("decide_tool", "apply_tool")
    graph.add_conditional_edges(
        "apply_tool",
        route_after_tool,
        {
            "end": END,
            "observe": "observe",
        },
    )

    graph.add_edge("observe", "update_hypothesis")
    graph.add_edge("update_hypothesis", "apply_crew_context")

    graph.add_conditional_edges(
        "apply_crew_context",
        evaluate_concern,
        {
            "flag": "flag_event",
            "end": END,
        },
    )

    graph.add_edge("flag_event", END)

    return graph.compile(checkpointer=checkpointer or InMemorySaver())
