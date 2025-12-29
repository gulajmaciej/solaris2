from typing import Dict, Any

from agents.planner import PlannedAction
from core.actions import apply_action
from mcp.context import get_session


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
        session = get_session()
        return {
            "turn": session.state.turn,
            "tension": session.tension,
            "earth_pressure": session.earth.pressure,
            "solaris_intensity": session.solaris.intensity,
            "station_power_level": session.state.station.power_level,
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
        session = get_session()
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
        session = get_session()
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
        session = get_session()
        session.state.flags[arguments["key"]] = arguments["value"]
        return {"status": "ok"}


class CalibrateFilters(MCPTool):
    name = "calibrate_filters"

    def schema(self):
        return {
            "name": self.name,
            "description": "Stabilize measurements by aggressive filtering",
            "input_schema": {},
        }

    def execute(self, arguments):
        session = get_session()
        apply_action(
            state=session.state,
            action=PlannedAction.FILTER_DATA_AGGRESSIVELY,
        )
        return {"status": "ok"}


class BoostMeasurementFrequency(MCPTool):
    name = "boost_measurement_frequency"

    def schema(self):
        return {
            "name": self.name,
            "description": "Increase measurement frequency",
            "input_schema": {},
        }

    def execute(self, arguments):
        session = get_session()
        apply_action(
            state=session.state,
            action=PlannedAction.INCREASE_MEASUREMENT_FREQUENCY,
        )
        return {"status": "ok"}


class AdjustSensorSensitivity(MCPTool):
    name = "adjust_sensor_sensitivity"

    def schema(self):
        return {
            "name": self.name,
            "description": "Adjust sensor sensitivity",
            "input_schema": {},
        }

    def execute(self, arguments):
        session = get_session()
        apply_action(
            state=session.state,
            action=PlannedAction.ADJUST_SENSOR_SENSITIVITY,
        )
        return {"status": "ok"}


class RestProtocol(MCPTool):
    name = "initiate_rest_protocol"

    def schema(self):
        return {
            "name": self.name,
            "description": "Initiate crew rest protocol",
            "input_schema": {},
        }

    def execute(self, arguments):
        session = get_session()
        apply_action(
            state=session.state,
            action=PlannedAction.INITIATE_REST_PROTOCOL,
        )
        return {"status": "ok"}


class ReduceInfoFlow(MCPTool):
    name = "reduce_information_flow"

    def schema(self):
        return {
            "name": self.name,
            "description": "Reduce information flow to the crew",
            "input_schema": {},
        }

    def execute(self, arguments):
        session = get_session()
        apply_action(
            state=session.state,
            action=PlannedAction.REDUCE_INFORMATION_FLOW,
        )
        return {"status": "ok"}


class EnforceProcedures(MCPTool):
    name = "enforce_procedures"

    def schema(self):
        return {
            "name": self.name,
            "description": "Enforce operational procedures",
            "input_schema": {},
        }

    def execute(self, arguments):
        session = get_session()
        apply_action(
            state=session.state,
            action=PlannedAction.ENFORCE_PROCEDURES,
        )
        return {"status": "ok"}


class ReportAlarmToEarth(MCPTool):
    name = "report_alarm_to_earth"

    def schema(self):
        return {
            "name": self.name,
            "description": "Report instability to Earth oversight",
            "input_schema": {},
        }

    def execute(self, arguments):
        session = get_session()
        session.earth.pressure = max(
            0.0,
            min(1.0, session.earth.pressure + 0.02),
        )
        return {"status": "ok"}


class ReportStabilizingToEarth(MCPTool):
    name = "report_stabilization_to_earth"

    def schema(self):
        return {
            "name": self.name,
            "description": "Report stabilization to Earth oversight",
            "input_schema": {},
        }

    def execute(self, arguments):
        session = get_session()
        session.earth.pressure = max(
            0.0,
            min(1.0, session.earth.pressure - 0.02),
        )
        return {"status": "ok"}


# -------- REGISTRY --------

TOOL_REGISTRY = {
    ReadSystemState.name: ReadSystemState(),
    ReadOceanState.name: ReadOceanState(),
    ReadCrewState.name: ReadCrewState(),
    FlagEvent.name: FlagEvent(),
    CalibrateFilters.name: CalibrateFilters(),
    BoostMeasurementFrequency.name: BoostMeasurementFrequency(),
    AdjustSensorSensitivity.name: AdjustSensorSensitivity(),
    RestProtocol.name: RestProtocol(),
    ReduceInfoFlow.name: ReduceInfoFlow(),
    EnforceProcedures.name: EnforceProcedures(),
    ReportAlarmToEarth.name: ReportAlarmToEarth(),
    ReportStabilizingToEarth.name: ReportStabilizingToEarth(),
}
