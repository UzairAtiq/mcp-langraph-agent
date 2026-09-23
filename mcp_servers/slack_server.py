import requests
from config.settings import SLACK_WEBHOOK_URL
from mcp.server.fastmcp import FastMCP

# initialize slack mcp server
mcp = FastMCP("slack-server")

# mcp tool: send a message to slack via webhook
@mcp.tool()
def send_slack_message(message: str) -> dict:
    """Send a message to the configured Slack channel via webhook."""
    # return error if webhook url is missing
    if not SLACK_WEBHOOK_URL:
        return {"error": "SLACK_WEBHOOK_URL not set in .env"}

    try:
        # post message text to webhook
        response = requests.post(
            SLACK_WEBHOOK_URL,
            json={"text": message},
            timeout=5,
        )

        # return success status if message sent
        if response.status_code == 200:
            return {"status": "sent", "message": message}

        # return error response on non-200 status
        return {
            "error": f"Slack returned status {response.status_code}",
            "details": response.text,
        }

    except requests.RequestException as e:
        # return error if network request fails
        return {"error": str(e)}

# run server directly if executed
if __name__ == "__main__":
    mcp.run()