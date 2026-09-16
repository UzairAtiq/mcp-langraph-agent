import asyncio
import time
from agent.tools import MCPClient
from config.settings import get_linkedin_access_token
from data.post_storage import (
    generate_next_post_id,
    get_post_by_id,
    save_post_record,
)
from mcp_servers.db_server import lookup_customer
from mcp_servers.linkedin_post_generator import (
    generate_and_request_approval,
    get_post_details,
    list_all_generated_posts,
    wait_for_approval_decision,
)
from mcp_servers.slack_server import send_slack_message
from services.groq_service import generate_linkedin_post_content
from services.linkedin_service import fetch_linkedin_person_urn
from services.slack_service import (
    execute_post_decision,
    send_approval_request,
)


# test database mcp tool
def test_db_lookup_customer():
    customer = lookup_customer(1)
    assert isinstance(customer, dict)
    assert "name" in customer or "error" in customer


# test slack mcp tool
def test_send_slack_message():
    result = send_slack_message("Automated test message from MCP server test suite.")
    assert isinstance(result, dict)
    assert "status" in result or "error" in result


# retrieve customer by id and post their status directly to slack
def lookup_and_notify_slack(customer_id: int) -> dict:
    customer = lookup_customer(customer_id)

    if not customer or "error" in customer:
        error_message = f"Customer with ID {customer_id} could not be found."
        slack_result = send_slack_message(error_message)
        return {
            "success": False,
            "customer_id": customer_id,
            "customer": customer,
            "slack_response": slack_result,
        }

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


# test linkedin post generator listing and detail tools
def test_linkedin_tools_read():
    posts_data = list_all_generated_posts()
    assert isinstance(posts_data, dict)
    assert "posts" in posts_data
    assert "total_count" in posts_data

    details = get_post_details("non_existent_id_999")
    assert isinstance(details, dict)
    assert details["found"] is False


# single unified live test: generate post, send to slack, wait for human decision, execute action, and save to storage
def test_live_slack_approval_and_publish_flow(timeout_seconds: int = 120) -> dict:
    topic = "AI Agents and Model Context Protocol in Production"
    print(f"\n[Live Flow] Generating LinkedIn post about: '{topic}'...")

    # step 1: resolve linkedin token and person urn
    access_token = get_linkedin_access_token()
    if not access_token:
        raise ValueError("LinkedIn access token not found. Please set LINKEDIN_ACCESS_TOKEN in .env or .linkedin_token.")

    person_urn = fetch_linkedin_person_urn(access_token=access_token)

    # step 2: generate post content with groq llm and unique identifier
    post_content = generate_linkedin_post_content(topic=topic)
    post_id = generate_next_post_id()

    # step 3: persist pending post record to storage so webhook and decision handlers can retrieve it
    save_post_record(
        post_id=post_id,
        content=post_content,
        profile_id=person_urn,
        access_token=access_token,
        status="pending",
    )

    # step 4: send block kit approval request with yes/no interactive buttons to slack
    slack_delivery = send_approval_request(
        post_id=post_id,
        content=post_content,
    )
    assert slack_delivery.get("success") is True, f"slack delivery failed: {slack_delivery.get('error')}"

    print(f"  ✓ Post `{post_id}` generated and delivered to Slack.")
    print(f"  👉 Please check your Slack channel and click either:")
    print(f"     • '✅ Yes (Approve & Post)' -> publishes live to LinkedIn")
    print(f"     • '❌ No (Discard)'          -> marks as rejected and updates storage")
    print(f"  ⏳ Waiting up to {timeout_seconds} seconds for your button click...\n")

    # step 5: poll storage for real human interaction received from slack webhook
    start_time = time.time()
    poll_interval_seconds = 2.0
    detected_status = None

    while time.time() - start_time < timeout_seconds:
        current_record = get_post_by_id(post_id)
        if current_record:
            status_value = current_record.get("status")
            if status_value in ("approved", "discarded", "published", "rejected", "publish_failed"):
                detected_status = status_value
                break
        time.sleep(poll_interval_seconds)

    assert detected_status is not None, f"timed out after {timeout_seconds}s waiting for Slack button click"
    print(f"  ✓ Slack response detected: '{detected_status}'")

    # step 6: pass post_id to execute_post_decision to retrieve post from storage and execute publish or discard
    decision_result = execute_post_decision(post_id=post_id)
    assert decision_result.get("success") is True, f"execution failed: {decision_result.get('error')}"

    # step 7: retrieve finalized post record from storage and report outcome
    final_post_details = get_post_details(post_id)
    assert final_post_details.get("found") is True
    final_record = final_post_details["post"]
    final_status = final_record.get("status")

    if final_status == "published":
        response_payload = final_record.get("linkedin_response", {})
        post_urn = response_payload.get("post_urn", "unknown")
        print(f"  🎉 Post `{post_id}` was APPROVED and published to LinkedIn! (URN: {post_urn})")
    elif final_status == "rejected":
        print(f"  🛑 Post `{post_id}` was DISCARDED and marked as rejected in database.")
    elif final_status == "publish_failed":
        print(f"  ⚠️ Post `{post_id}` was approved but publishing to LinkedIn failed.")
    else:
        print(f"  ℹ️ Post `{post_id}` finalized with status: '{final_status}'")

    return final_post_details


# test standalone mcp client connection to a server over stdio
async def _run_mcp_client_test():
    client = MCPClient("mcp_servers.slack_server")
    try:
        await client.connect()
        assert client.session is not None
    finally:
        await client.close()


def test_mcp_client_connection():
    asyncio.run(_run_mcp_client_test())


if __name__ == "__main__":
    print("Running MCP server automated unit tests...")

    print("\n1. Testing Database MCP tool...")
    test_db_lookup_customer()
    print("   ✓ lookup_customer passed")

    print("\n2. Testing Slack MCP tool...")
    test_send_slack_message()
    print("   ✓ send_slack_message passed")

    print("\n3. Testing DB + Slack pipeline...")
    test_lookup_and_notify_slack()
    print("   ✓ lookup_and_notify_slack passed")

    print("\n4. Testing LinkedIn read tools...")
    test_linkedin_tools_read()
    print("   ✓ list_all_generated_posts and get_post_details passed")

    print("\n5. Testing MCPClient stdio connection...")
    test_mcp_client_connection()
    print("   ✓ mcp_client_connection passed")

    print("\n🎉 Automated unit tests completed successfully!")
    print("\nTo run the live interactive human-approval test:")
    print("  1. Ensure FastAPI server is running: uvicorn api.main:app --port 8000")
    print("  2. Ensure ngrok is running: ngrok http 8000")
    print("  3. Run: python -c 'from tests.test_mcp_servers import test_live_slack_approval_and_publish_flow; test_live_slack_approval_and_publish_flow()'")