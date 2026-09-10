import os
import requests
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP
from config.settings import SLACK_WEBHOOK_URL 

#creating the mcp server
mcp = FastMCP("slack-server")

#defining the mcp tool for sending a slack message
@mcp.tool()
def send_slack_message(message: str) -> dict:
    """Send a message to the configured Slack channel via webhook."""

    #return error if the slack webhook url is not set
    if not SLACK_WEBHOOK_URL:
        return {"error": "SLACK_WEBHOOK_URL not set in .env"}

    try:
        #sending the message to slack
        response = requests.post(
            SLACK_WEBHOOK_URL,
            json={"text": message},
            timeout=5,
        )

        #return success if the message was sent
        if response.status_code == 200:
            return {"status": "sent", "message": message}

        #return error if slack returns an unsuccessful status
        else:
            return {
                "error": f"Slack returned status {response.status_code}",
                "details": response.text,
            }

    #return error if the request fails
    except requests.RequestException as e:
        return {"error": str(e)}


#start the mcp server when this file is run directly
if __name__ == "__main__":
    mcp.run()