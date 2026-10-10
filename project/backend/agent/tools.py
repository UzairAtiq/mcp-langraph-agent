import sys
from contextlib import AsyncExitStack
from langchain_mcp_adapters.client import MultiServerMCPClient
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# standalone utility for testing single mcp servers in isolation
class MCPClient:
    def __init__(self, server_module: str) -> None:
        self.server_module = server_module
        self.session: ClientSession | None = None
        self._stack = AsyncExitStack()

    async def connect(self) -> None:
        # configure stdio server parameters with python executable
        params = StdioServerParameters(
            command=sys.executable,
            args=["-m", self.server_module],
        )

        # establish stdio read and write channels
        read_stream, write_stream = await self._stack.enter_async_context(
            stdio_client(params)
        )

        # initialize client session and handshake
        self.session = await self._stack.enter_async_context(
            ClientSession(read_stream, write_stream)
        )
        await self.session.initialize()

    async def call_tool(self, name: str, args: dict) -> str:
        # verify active session before invoking tool
        if not self.session:
            raise RuntimeError("MCPClient is not connected. Call connect() first.")

        result = await self.session.call_tool(name, args)
        return result.content[0].text

    async def close(self) -> None:
        # close all active async context managers and streams
        await self._stack.aclose()

# fetch all tools across registered mcp servers for langgraph agent
async def get_langgraph_tools() -> list:
    # configure all mcp servers with stdio transport
    client = MultiServerMCPClient(
        {
            "database": {
                "command": sys.executable,
                "args": ["-m", "mcp_servers.db_server"],
                "transport": "stdio",
            },
            "slack": {
                "command": sys.executable,
                "args": ["-m", "mcp_servers.slack_server"],
                "transport": "stdio",
            },
            "linkedin_post_generator": {
                "command": sys.executable,
                "args": ["-m", "mcp_servers.linkedin_post_generator"],
                "transport": "stdio",
            },
        }
    )

    # retrieve converted langchain structured tools from all active servers
    tools = await client.get_tools()
    return tools