from langchain_ollama import ChatOllama
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.config import get_stream_writer

from agents.langgraph_state import InstrumentAgentState
from mcp.server import MCPServer


# ------------------ RUNTIME DEPENDENCIES ------------------

llm = ChatOllama(
    model="qwen2.5:7b",
    temperature=0.0,
)

mcp = MCPServer()

# ------------------ CREW COUPLING CONSTANTS ------------------

CREW_STRESS_CONFIDENCE_COEFF = 0.1
CREW_FATIGUE_THRESHOLD = 0.6
CREW_FATIGUE_CONTRADICTION_STEP = 1


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


def read_context(state: InstrumentAgentState) -> InstrumentAgentState:
    """
    Reads the current world context needed for tool decisions.
    """
    state["visited_nodes"].append("read_context")
    _emit_event(
        agent="instrument_specialist",
        node="read_context",
        event="node_start",
        phase=state["phase"],
    )

    ocean = mcp.call_tool("read_ocean_state", {})
    crew = mcp.call_tool("read_crew_state", {})
    system = mcp.call_tool("read_system_state", {})

    state["ocean_activity"] = ocean["activity"]
    state["ocean_instability"] = ocean["instability"]
    state["crew_fatigue"] = crew["fatigue"]
    state["station_power_level"] = system["station_power_level"]
    state["tension"] = system["tension"]
    state["solaris_intensity"] = system["solaris_intensity"]

    _emit_event(
        agent="instrument_specialist",
        node="read_context",
        event="node_end",
        phase=state["phase"],
        data={
            "ocean_activity": state["ocean_activity"],
            "ocean_instability": state["ocean_instability"],
            "crew_fatigue": state["crew_fatigue"],
            "station_power_level": state["station_power_level"],
            "tension": state["tension"],
        },
    )
    return state


def decide_tool(state: InstrumentAgentState) -> InstrumentAgentState:
    """
    Deterministic tool selection based on current context.
    """
    state["visited_nodes"].append("decide_tool")
    _emit_event(
        agent="instrument_specialist",
        node="decide_tool",
        event="node_start",
        phase=state["phase"],
    )

    tool = None
    reason = ""

    if state["ocean_instability"] >= 0.6:
        tool = "calibrate_filters"
        reason = "ocean_instability>=0.6"
    elif (
        state["ocean_activity"] <= 0.35
        and state["station_power_level"] >= 0.4
    ):
        tool = "boost_measurement_frequency"
        reason = "ocean_activity<=0.35 and station_power_level>=0.4"
    elif (
        state["ocean_activity"] >= 0.35
        and state["ocean_instability"] <= 0.45
    ):
        tool = "adjust_sensor_sensitivity"
        reason = "ocean_activity>=0.35 and ocean_instability<=0.45"
    elif state["crew_fatigue"] >= 0.6:
        tool = "calibrate_filters"
        reason = "crew_fatigue>=0.6"

    state["tool_decision"] = tool
    state["tool_reason"] = reason

    _emit_event(
        agent="instrument_specialist",
        node="decide_tool",
        event="decision",
        phase=state["phase"],
        data={
            "tool": tool,
            "reason": reason,
        },
    )
    _emit_event(
        agent="instrument_specialist",
        node="decide_tool",
        event="node_end",
        phase=state["phase"],
    )
    return state


def apply_tool(state: InstrumentAgentState) -> InstrumentAgentState:
    """
    Applies the selected tool through MCP.
    """
    state["visited_nodes"].append("apply_tool")
    _emit_event(
        agent="instrument_specialist",
        node="apply_tool",
        event="node_start",
        phase=state["phase"],
    )

    tool = state.get("tool_decision")
    if tool:
        _emit_event(
            agent="instrument_specialist",
            node="apply_tool",
            event="tool_call",
            phase=state["phase"],
            data={"tool": tool},
        )
        result = mcp.call_tool(tool, {})
        state["tool_applied"] = True
        _emit_event(
            agent="instrument_specialist",
            node="apply_tool",
            event="tool_result",
            phase=state["phase"],
            data={"tool": tool, "result": result},
        )
    else:
        state["tool_applied"] = False

    _emit_event(
        agent="instrument_specialist",
        node="apply_tool",
        event="node_end",
        phase=state["phase"],
        data={"tool_applied": state["tool_applied"]},
    )
    return state


def observe(state: InstrumentAgentState) -> InstrumentAgentState:
    """
    Perceptual node.
    Interprets raw sensor data and produces a linguistic observation.
    """
    _emit_event(
        agent="instrument_specialist",
        node="observe",
        event="node_start",
        phase=state["phase"],
    )
    state["visited_nodes"].append("observe")

    data = mcp.call_tool("read_ocean_state", {})

    prompt = f"""
You are analyzing sensor data from an alien ocean.

DATA:
- activity: {data['activity']}
- instability: {data['instability']}

Current hypothesis:
"{state['hypothesis']}"

Form a concise observation.
"""

    observation = llm.invoke(prompt).content.strip()
    state["last_observation"] = observation
    _emit_event(
        agent="instrument_specialist",
        node="observe",
        event="node_end",
        phase=state["phase"],
        data={"observation": observation},
    )
    return state


def update_hypothesis(state: InstrumentAgentState) -> InstrumentAgentState:
    """
    Hypothesis revision node.
    Proposes a new hypothesis AND evaluates its semantic relation
    to the previous one.
    """
    _emit_event(
        agent="instrument_specialist",
        node="update_hypothesis",
        event="node_start",
        phase=state["phase"],
    )
    state["visited_nodes"].append("update_hypothesis")

    # --- STEP 1: PROPOSE NEW HYPOTHESIS (LANGUAGE TASK) ---

    hypothesis_prompt = f"""
Based on the observation below, update your hypothesis.

Observation:
"{state['last_observation']}"

Current hypothesis:
"{state['hypothesis']}"

Rules:
- If observation contradicts the hypothesis, produce a DIFFERENT hypothesis.
- If consistent, RESTATE the hypothesis.
- Output ONE short sentence.
"""

    new_hypothesis = llm.invoke(hypothesis_prompt).content.strip()

    # --- STEP 2: ASSESS SEMANTIC RELATION (META-COGNITION) ---

    relation_prompt = f"""
You are evaluating the relationship between two hypotheses.

OLD hypothesis:
"{state['hypothesis']}"

NEW hypothesis:
"{new_hypothesis}"

Classify the relationship as ONE of:
- CONSISTENT
- CONTRADICTS

Respond with exactly ONE word.
"""

    relation = llm.invoke(relation_prompt).content.strip().upper()

    # --- STEP 3: UPDATE COGNITIVE STATE (DETERMINISTIC MECHANISM) ---

    if relation == "CONTRADICTS":
        state["contradictions"] += 1
        state["confidence"] *= 0.9
    else:
        state["confidence"] = min(1.0, state["confidence"] + 0.1)

    state["hypothesis"] = new_hypothesis
    _emit_event(
        agent="instrument_specialist",
        node="update_hypothesis",
        event="node_end",
        phase=state["phase"],
        data={
            "hypothesis": new_hypothesis,
            "confidence": state["confidence"],
            "contradictions": state["contradictions"],
        },
    )
    return state


def apply_crew_context(state: InstrumentAgentState) -> InstrumentAgentState:
    """
    Applies crew condition to instrument confidence and contradictions.
    """
    _emit_event(
        agent="instrument_specialist",
        node="apply_crew_context",
        event="node_start",
        phase=state["phase"],
    )
    state["visited_nodes"].append("apply_crew_context")

    crew = mcp.call_tool("read_crew_state", {})
    stress = crew["stress"]
    fatigue = crew["fatigue"]
    prev_confidence = state["confidence"]
    prev_contradictions = state["contradictions"]

    # Stress reduces confidence
    state["confidence"] *= max(
        0.0,
        1.0 - (stress * CREW_STRESS_CONFIDENCE_COEFF),
    )

    # Fatigue increases contradictions past a threshold
    if fatigue >= CREW_FATIGUE_THRESHOLD:
        state["contradictions"] += CREW_FATIGUE_CONTRADICTION_STEP

    state["confidence"] = max(0.0, min(1.0, state["confidence"]))
    state["crew_stress"] = stress
    state["crew_fatigue"] = fatigue
    state["crew_confidence_delta"] = round(
        state["confidence"] - prev_confidence,
        4,
    )
    state["crew_contradiction_delta"] = (
        state["contradictions"] - prev_contradictions
    )
    _emit_event(
        agent="instrument_specialist",
        node="apply_crew_context",
        event="node_end",
        phase=state["phase"],
        data={
            "crew_stress": stress,
            "crew_fatigue": fatigue,
            "confidence_delta": state["crew_confidence_delta"],
            "contradiction_delta": state["crew_contradiction_delta"],
        },
    )
    return state


def evaluate_concern(state: InstrumentAgentState) -> str:
    """
    Routing function.
    Decides whether the agent escalates concern or ends the cycle.
    """
    if state["confidence"] > 0.6 and state["contradictions"] >= 2:
        state["last_route"] = "flag"
        return "flag"

    state["last_route"] = "end"
    return "end"


def flag_event(state: InstrumentAgentState) -> InstrumentAgentState:
    """
    Institutional signal node.
    Emits a concern signal without modifying cognitive state.
    """
    _emit_event(
        agent="instrument_specialist",
        node="flag_event",
        event="node_start",
        phase=state["phase"],
    )
    state["visited_nodes"].append("flag_event")

    mcp.call_tool(
        "flag_event",
        {"key": "instrument_concern", "value": True},
    )
    _emit_event(
        agent="instrument_specialist",
        node="flag_event",
        event="node_end",
        phase=state["phase"],
        data={"flag": "instrument_concern", "value": True},
    )
    return state


# ------------------ GRAPH DEFINITION ------------------

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
