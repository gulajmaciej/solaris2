def update_drift(
    agent_state: dict,
    intensity: str,
    earth_pressure: float = 0.0,
):
    """
    Cognitive drift.
    Monotonic, slow, irreversible.
    """

    base = 0.01

    if intensity == "high":
        base += 0.02
    elif intensity == "medium":
        base += 0.01

    base += earth_pressure * 0.03

    agent_state["drift"] = min(
        1.0,
        agent_state.get("drift", 0.0) + base
    )
