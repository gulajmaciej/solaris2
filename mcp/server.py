from typing import Dict, Any
from mcp.tools import TOOL_REGISTRY


class MCPServer:
    """
    MCP logical server.
    Can be extracted to separate process later.
    """

    def list_tools(self) -> Dict[str, Dict[str, Any]]:
        return {
            name: tool.schema()
            for name, tool in TOOL_REGISTRY.items()
        }

    def call_tool(self, name: str, arguments: Dict[str, Any]) -> Any:
        if name not in TOOL_REGISTRY:
            raise ValueError(f"Tool not found: {name}")
        return TOOL_REGISTRY[name].execute(arguments)
