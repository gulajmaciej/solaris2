from langchain_ollama import ChatOllama
from core.state import GameState
from core.solaris import SolarisState


model = ChatOllama(
    model="qwen2.5:7b",
    temperature=0.7,
)


def observe(
    state: GameState,
    drift: float,
    solaris: SolarisState,
) -> str:
    prompt = f"""
You are an instrument specialist observing an alien ocean.

FACTUAL DATA:
- Ocean activity: {state.ocean.activity}
- Ocean instability: {state.ocean.instability}

COGNITIVE CONTEXT:
- Your personal cognitive drift: {drift:.2f}
- Solaris distortion field intensity: {solaris.intensity:.2f}

RULES:
- Do NOT invent events.
- Interpret data through your distorted perception.
- If distortion is high, your interpretation may feel symbolic, personal, or unsettling.

Describe what you observe.
"""

    response = model.invoke(prompt).content.strip()

    if response.startswith("```"):
        response = response.replace("```", "").strip()

    return response
