from langchain_ollama import ChatOllama
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import InMemorySaver

from agents.langgraph_state import CrewOfficerState


# ------------------ RUNTIME DEPENDENCIES ------------------

llm = ChatOllama(
    model="qwen2.5:7b",
    temperature=0.6,
)


# ------------------ GRAPH NODES ------------------

def observe(state: CrewOfficerState) -> CrewOfficerState:
    """
    Observational node for crew condition.
    """
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
    return state


# ------------------ GRAPH DEFINITION ------------------

def build_crew_graph(*, checkpointer=None):
    graph = StateGraph(CrewOfficerState)

    graph.add_node("observe", observe)
    graph.set_entry_point("observe")
    graph.add_edge("observe", END)

    return graph.compile(checkpointer=checkpointer or InMemorySaver())
