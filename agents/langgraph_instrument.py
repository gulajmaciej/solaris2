from langchain_ollama import ChatOllama
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import InMemorySaver

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

def observe(state: InstrumentAgentState) -> InstrumentAgentState:
    """
    Perceptual node.
    Interprets raw sensor data and produces a linguistic observation.
    """
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
    return state


def update_hypothesis(state: InstrumentAgentState) -> InstrumentAgentState:
    """
    Hypothesis revision node.
    Proposes a new hypothesis AND evaluates its semantic relation
    to the previous one.
    """
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
    return state


def apply_crew_context(state: InstrumentAgentState) -> InstrumentAgentState:
    """
    Applies crew condition to instrument confidence and contradictions.
    """
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
    state["visited_nodes"].append("flag_event")

    mcp.call_tool(
        "flag_event",
        {"key": "instrument_concern", "value": True},
    )
    return state


# ------------------ GRAPH DEFINITION ------------------

def build_instrument_graph(*, checkpointer=None):
    graph = StateGraph(InstrumentAgentState)

    graph.add_node("observe", observe)
    graph.add_node("update_hypothesis", update_hypothesis)
    graph.add_node("apply_crew_context", apply_crew_context)
    graph.add_node("flag_event", flag_event)

    graph.set_entry_point("observe")
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
