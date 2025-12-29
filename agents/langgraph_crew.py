from langchain_ollama import ChatOllama
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.config import get_stream_writer

from agents.langgraph_state import CrewOfficerState
from mcp.server import MCPServer


# ------------------ RUNTIME DEPENDENCIES ------------------

llm = ChatOllama(
    model="qwen2.5:7b",
    temperature=0.6,
)

mcp = MCPServer()


# ------------------ GRAPH NODES ------------------

def _emit_event(
    *,
    agent: str,
    node: str,
    event: str,
    phase: str,
    data: dict | None = None,
) -> None:
    writer = get_stream_writer()
    if not writer:
        return

    payload = {
        "agent": agent,
        "node": node,
        "event": event,
        "phase": phase,
    }
    if data:
        payload["data"] = data

    writer(payload)


def read_context(state: CrewOfficerState) -> CrewOfficerState:
    """
    Reads the current world context needed for tool decisions.
    """
    state["visited_nodes"].append("read_context")
    _emit_event(
        agent="crew_officer",
        node="read_context",
        event="node_start",
        phase=state["phase"],
    )

    crew = mcp.call_tool("read_crew_state", {})
    system = mcp.call_tool("read_system_state", {})

    state["crew_stress"] = crew["stress"]
    state["crew_fatigue"] = crew["fatigue"]
    state["tension"] = system["tension"]
    state["solaris_intensity"] = system["solaris_intensity"]

    _emit_event(
        agent="crew_officer",
        node="read_context",
        event="node_end",
        phase=state["phase"],
        data={
            "crew_stress": state["crew_stress"],
            "crew_fatigue": state["crew_fatigue"],
            "tension": state["tension"],
            "solaris_intensity": state["solaris_intensity"],
        },
    )
    return state


def decide_tool(state: CrewOfficerState) -> CrewOfficerState:
    """
    Deterministic tool selection based on current context.
    """
    state["visited_nodes"].append("decide_tool")
    _emit_event(
        agent="crew_officer",
        node="decide_tool",
        event="node_start",
        phase=state["phase"],
    )

    tool = None
    reason = ""

    if state["crew_stress"] >= 0.6 or state["crew_fatigue"] >= 0.6:
        tool = "initiate_rest_protocol"
        reason = "crew_stress>=0.6 or crew_fatigue>=0.6"
    elif (
        state["crew_stress"] >= 0.45
        and state["solaris_intensity"] >= 0.5
    ):
        tool = "reduce_information_flow"
        reason = "crew_stress>=0.45 and solaris_intensity>=0.5"
    elif state["crew_stress"] <= 0.35 and state["crew_fatigue"] <= 0.35:
        tool = "enforce_procedures"
        reason = "crew_stress<=0.35 and crew_fatigue<=0.35"
    elif state["tension"] >= 0.7 and state["drift"] >= 0.5:
        tool = "report_alarm_to_earth"
        reason = "tension>=0.7 and drift>=0.5"
    elif state["tension"] <= 0.25 and state["crew_stress"] <= 0.3:
        tool = "report_stabilization_to_earth"
        reason = "tension<=0.25 and crew_stress<=0.3"

    state["tool_decision"] = tool
    state["tool_reason"] = reason

    _emit_event(
        agent="crew_officer",
        node="decide_tool",
        event="decision",
        phase=state["phase"],
        data={
            "tool": tool,
            "reason": reason,
        },
    )
    _emit_event(
        agent="crew_officer",
        node="decide_tool",
        event="node_end",
        phase=state["phase"],
    )
    return state


def apply_tool(state: CrewOfficerState) -> CrewOfficerState:
    """
    Applies the selected tool through MCP.
    """
    state["visited_nodes"].append("apply_tool")
    _emit_event(
        agent="crew_officer",
        node="apply_tool",
        event="node_start",
        phase=state["phase"],
    )

    tool = state.get("tool_decision")
    if tool:
        _emit_event(
            agent="crew_officer",
            node="apply_tool",
            event="tool_call",
            phase=state["phase"],
            data={"tool": tool},
        )
        result = mcp.call_tool(tool, {})
        state["tool_applied"] = True
        _emit_event(
            agent="crew_officer",
            node="apply_tool",
            event="tool_result",
            phase=state["phase"],
            data={"tool": tool, "result": result},
        )
    else:
        state["tool_applied"] = False

    _emit_event(
        agent="crew_officer",
        node="apply_tool",
        event="node_end",
        phase=state["phase"],
        data={"tool_applied": state["tool_applied"]},
    )
    return state


def observe(state: CrewOfficerState) -> CrewOfficerState:
    """
    Observational node for crew condition.
    """
    _emit_event(
        agent="crew_officer",
        node="observe",
        event="node_start",
        phase=state["phase"],
    )
    state["visited_nodes"].append("observe")

    prompt = f"""
You are a crew officer assessing human condition aboard a remote station.

FACTUAL DATA:
- Crew stress level: {state['crew_stress']}
- Crew fatigue level: {state['crew_fatigue']}

COGNITIVE CONTEXT:
- Your personal cognitive drift: {state['drift']:.2f}
- Solaris distortion field intensity: {state['solaris_intensity']:.2f}

RULES:
- Do NOT invent new crew members.
- Do NOT describe physical hallucinations directly.
- Let Solaris subtly influence emotional interpretation.

Describe the crew condition.
"""

    response = llm.invoke(prompt).content.strip()

    if response.startswith("```"):
        response = response.replace("```", "").strip()

    state["last_observation"] = response
    _emit_event(
        agent="crew_officer",
        node="observe",
        event="node_end",
        phase=state["phase"],
        data={"observation": response},
    )
    return state


# ------------------ GRAPH DEFINITION ------------------

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
