from typing import Dict, Any

from api.state import SESSION


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
        return {
            "turn": SESSION.state.turn,
            "tension": SESSION.tension,
            "earth_pressure": SESSION.earth.pressure,
            "solaris_intensity": SESSION.solaris.intensity,
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
        return {
            "activity": SESSION.state.ocean.activity,
            "instability": SESSION.state.ocean.instability,
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
        return {
            "stress": SESSION.state.crew.stress,
            "fatigue": SESSION.state.crew.fatigue,
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
        SESSION.state.flags[arguments["key"]] = arguments["value"]
        return {"status": "ok"}


# -------- REGISTRY --------

TOOL_REGISTRY = {
    ReadSystemState.name: ReadSystemState(),
    ReadOceanState.name: ReadOceanState(),
    ReadCrewState.name: ReadCrewState(),
    FlagEvent.name: FlagEvent(),
}
