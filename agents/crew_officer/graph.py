from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import InMemorySaver

from agents.crew_officer.state import CrewOfficerState
from agents.crew_officer.nodes import (
    read_context,
    decide_tool,
    apply_tool,
    observe,
)


def build_crew_graph(*, checkpointer=None):
    graph = StateGraph(CrewOfficerState)

    graph.add_node("read_context", read_context)
    graph.add_node("decide_tool", decide_tool)
    graph.add_node("apply_tool", apply_tool)
    graph.add_node("observe", observe)
    graph.set_entry_point("read_context")

    def route_after_context(state: CrewOfficerState) -> str:
        return "decide_tool" if state["phase"] == "tool" else "observe"

    def route_after_tool(state: CrewOfficerState) -> str:
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

    graph.add_edge("observe", END)

    return graph.compile(checkpointer=checkpointer or InMemorySaver())
