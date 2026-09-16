import asyncio
import sys
from agent.tools import MCPClient
from mcp_servers.db_server import lookup_customer
from mcp_servers.slack_server import send_slack_message
from mcp_servers.linkedin_post_generator import (
    get_post_details,
    list_all_generated_posts,
)

# test database mcp tool
def test_db_tool_direct():
    customer = lookup_customer(1)
    assert isinstance(customer, dict)
    assert "name" in customer or "error" in customer

# test slack mcp tool for sending a message
def test_send_slack_message_direct():
    result = send_slack_message("Automated test message from MCP server test suite.")
    assert isinstance(result, dict)
    assert "status" in result or "error" in result

# retrieve customer by id and post their status directly to slack
def lookup_and_notify_slack(customer_id: int) -> dict:
    customer = lookup_customer(customer_id)

    # handle lookup failure case
    if not customer or "error" in customer:
        error_message = f"Customer with ID {customer_id} could not be found."
        slack_result = send_slack_message(error_message)
        return {
            "success": False,
            "customer_id": customer_id,
            "customer": customer,
            "slack_response": slack_result,
        }

    # format customer details into a readable notification message
    notification_text = (
        f"Customer Details:\n"
        f"• ID: {customer.get('id')}\n"
        f"• Name: {customer.get('name')}\n"
        f"• Email: {customer.get('email')}\n"
        f"• Company: {customer.get('company')}\n"
        f"• Status: {customer.get('status')}"
    )

    slack_result = send_slack_message(notification_text)

    return {
        "success": True,
        "customer_id": customer_id,
        "customer": customer,
        "slack_response": slack_result,
    }

# test customer lookup and slack notification pipeline
def test_lookup_and_notify_slack():
    result = lookup_and_notify_slack(1)
    assert isinstance(result, dict)
    assert "slack_response" in result
    assert "customer_id" in result

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
