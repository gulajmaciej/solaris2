from dataclasses import dataclass, field
from typing import List


@dataclass
class InstrumentAgentState:
    """
    Explicit cognitive state of the instrument specialist.
    """
    hypothesis: str = "No coherent pattern detected"
    confidence: float = 0.3
    contradictions: int = 0
    last_observation: str = ""

    # --- DEBUG / TRACE ---
    visited_nodes: List[str] = field(default_factory=list)
    last_route: str | None = None
