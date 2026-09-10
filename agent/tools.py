from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
import sys

#setting the parameters to launch the server 
server_params = StdioServerParameters(
    command=sys.executable,
    args=["-m" , "mcp_servers.db_server"],
)


async def get_mcp_tools():
    
    #launching the server process as a subprocess
    async with stdio_client(server_params) as (read, write):

        #initializing the session 
        async with ClientSession(read, write) as session:
            await session.initialize()

            #getting tools from the server
            result = await session.list_tools()

            return result.tools


  