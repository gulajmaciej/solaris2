import random


CONF_ORDER = ["high", "medium", "low"]


class SolarisPerceptionDisruptor:
    """
    Non-agent.
    Distorts perception, not reality.
    """

    def __init__(self, influence: float = 0.15):
        self.influence = influence

    def _degrade(self, conf: str) -> str:
        if conf in CONF_ORDER:
            i = CONF_ORDER.index(conf)
            return CONF_ORDER[min(i + 1, 2)]
        return conf

    def apply(self, observations: list):
        debug = []

        for obs in observations:
            if random.random() < self.influence:
                old = obs["confidence"]
                obs["confidence"] = self._degrade(old)
                debug.append(
                    f"{obs['agent_id']} confidence {old} -> {obs['confidence']}"
                )

        return observations, debug
