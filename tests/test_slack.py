import asyncio
from agent.tools import MCPClient

async def test():
    client = MCPClient("mcp_servers.slack_server")
    await client.connect()
    result = await client.call_tool("send_slack_message", {"message": "Hello"})
    print(result)
    await client.close()

asyncio.run(test())