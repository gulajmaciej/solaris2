from langchain_ollama import ChatOllama
from langchain.agents import Tool, initialize_agent, AgentType

from mcp.server import MCPServer


def build_agent():
    server = MCPServer()

    tools = []
    for name, schema in server.list_tools().items():
        tools.append(
            Tool(
                name=name,
                description=schema["description"],
                func=lambda args, n=name: server.call_tool(n, args),
            )
        )

    model = ChatOllama(
        model="qwen2.5:7b",
        temperature=0.0,
    )

    return initialize_agent(
        tools=tools,
        llm=model,
        agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
        verbose=True,
    )
