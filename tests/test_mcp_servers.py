import asyncio
import sys
from agent.tools import MCPClient
from mcp_servers.db_server import lookup_customer
from mcp_servers.slack_server import send_slack_message
from mcp_servers.linkedin_post_generator import get_post_details, list_all_generated_posts

# test database mcp tool
def test_db_tool_direct():
    customer = lookup_customer(1)
    assert isinstance(customer, dict)
    assert "name" in customer or "error" in customer

# test linkedin post generator mcp tools
def test_linkedin_post_generator_tools_direct():
    post_list_result = list_all_generated_posts()
    assert isinstance(post_list_result, dict)
    assert "posts" in post_list_result
    assert "total_count" in post_list_result

    details = get_post_details("non_existent_id_999")
    assert isinstance(details, dict)
    assert details["found"] is False

# test standalone mcp client connection to a server
async def run_mcp_client_test():
    client = MCPClient("mcp_servers.slack_server")
    try:
        await client.connect()
        assert client.session is not None
    finally:
        await client.close()

def test_mcp_client_connection():
    asyncio.run(run_mcp_client_test())
