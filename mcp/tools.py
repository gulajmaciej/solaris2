from typing import Dict, Any

def _get_session():
    from api.state import SESSION
    return SESSION


class MCPTool:
    name: str

    def schema(self) -> Dict[str, Any]:
        raise NotImplementedError

    def execute(self, arguments: Dict[str, Any]) -> Any:
        raise NotImplementedError


# -------- READ TOOLS --------

class ReadSystemState(MCPTool):
    name = "read_system_state"

    def schema(self):
        return {
            "name": self.name,
            "description": "Read current system metrics",
            "input_schema": {},
        }

    def execute(self, arguments):
        session = _get_session()
        return {
            "turn": session.state.turn,
            "tension": session.tension,
            "earth_pressure": session.earth.pressure,
            "solaris_intensity": session.solaris.intensity,
        }


class ReadOceanState(MCPTool):
    name = "read_ocean_state"

    def schema(self):
        return {
            "name": self.name,
            "description": "Read ocean measurements",
            "input_schema": {},
        }

    def execute(self, arguments):
        session = _get_session()
        return {
            "activity": session.state.ocean.activity,
            "instability": session.state.ocean.instability,
        }


class ReadCrewState(MCPTool):
    name = "read_crew_state"

    def schema(self):
        return {
            "name": self.name,
            "description": "Read crew condition",
            "input_schema": {},
        }

    def execute(self, arguments):
        session = _get_session()
        return {
            "stress": session.state.crew.stress,
            "fatigue": session.state.crew.fatigue,
        }


# -------- WRITE (LIMITED) --------

class FlagEvent(MCPTool):
    name = "flag_event"

    def schema(self):
        return {
            "name": self.name,
            "description": "Flag an internal observation for later analysis",
            "input_schema": {
                "type": "object",
                "properties": {
                    "key": {"type": "string"},
                    "value": {"type": "boolean"},
                },
                "required": ["key", "value"],
            },
        }

    def execute(self, arguments):
        session = _get_session()
        session.state.flags[arguments["key"]] = arguments["value"]
        return {"status": "ok"}


# -------- REGISTRY --------

TOOL_REGISTRY = {
    ReadSystemState.name: ReadSystemState(),
    ReadOceanState.name: ReadOceanState(),
    ReadCrewState.name: ReadCrewState(),
    FlagEvent.name: FlagEvent(),
}
