from fastapi import APIRouter
from typing import Dict, Any

from mcp.server import MCPServer

router = APIRouter(prefix="/mcp", tags=["mcp"])
server = MCPServer()


@router.get("/tools")
def list_tools():
    return server.list_tools()


@router.post("/call/{tool_name}")
def call_tool(tool_name: str, arguments: Dict[str, Any]):
    return server.call_tool(tool_name, arguments)
