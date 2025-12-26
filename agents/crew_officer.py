from langchain_ollama import ChatOllama
from core.state import GameState
from core.solaris import SolarisState


model = ChatOllama(
    model="qwen2.5:7b",
    temperature=0.6,
)


def observe(
    state: GameState,
    drift: float,
    solaris: SolarisState,
) -> str:
    prompt = f"""
You are a crew officer assessing human condition aboard a remote station.

FACTUAL DATA:
- Crew stress level: {state.crew.stress}
- Crew fatigue level: {state.crew.fatigue}

COGNITIVE CONTEXT:
- Your personal cognitive drift: {drift:.2f}
- Solaris distortion field intensity: {solaris.intensity:.2f}

RULES:
- Do NOT invent new crew members.
- Do NOT describe physical hallucinations directly.
- Let Solaris subtly influence emotional interpretation.

Describe the crew condition.
"""

    response = model.invoke(prompt).content.strip()

    if response.startswith("```"):
        response = response.replace("```", "").strip()

    return response
