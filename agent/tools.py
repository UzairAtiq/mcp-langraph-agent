from contextlib import AsyncExitStack
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from langchain_mcp_adapters.client import MultiServerMCPClient
import sys


class MCPClient:

    #initializing the MCP client
    def __init__(self, server_module: str):
        self.server_module = server_module
        self.session: ClientSession | None = None
        self._stack = AsyncExitStack()

    async def connect(self):

        #setting the parameters to launch the MCP server
        params = StdioServerParameters(
            command=sys.executable,
            args=["-m", self.server_module],
        )

        #launching the server and creating the communication channel
        read, write = await self._stack.enter_async_context(
            stdio_client(params)
        )

        #creating the MCP session
        self.session = await self._stack.enter_async_context(
            ClientSession(read, write)
        )

        #initializing the MCP session
        await self.session.initialize()

    async def call_tool(self, name: str, args: dict):

        #calling the MCP tool
        result = await self.session.call_tool(name, args)

        #returning only the text content from the tool result
        return result.content[0].text

    async def close(self):

        #closing the MCP connection and cleaning up resources
        await self._stack.aclose()

async def get_langgraph_tools():

    #Settinng up the client
    client = MultiServerMCPClient(
        {
            #Mapping server names to configs
            "database": {
                "command": "python",
                "args": ["-m", "mcp_servers.db_server"],
                "transport": "stdio",
            },

            "slack": {
                "command": "python",
                "args": ["-m", "mcp_servers.slack_server"],
                "transport": "stdio",
            },
        }
    )
    #getting a list of all tools from the connected servers
    tools = await client.get_tools()

    #returning the tools list
    return tools