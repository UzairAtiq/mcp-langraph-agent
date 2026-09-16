import logging
import requests
from config.settings import SLACK_WEBHOOK_URL

# configure slack service logger
logger = logging.getLogger("slack_service")

# build slack block kit payload with approval buttons
def build_approval_blocks(post_id: str, content: str) -> list[dict]:
    return [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": "📝 New LinkedIn Post Approval Request",
                "emoji": True,
            },
        },
        {
            "type": "section",
            "fields": [
                {
                    "type": "mrkdwn",
                    "text": f"*Post ID:*\n`{post_id}`",
                },
                {
                    "type": "mrkdwn",
                    "text": "*Status:*\nPending Approval ⏳",
                },
            ],
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*Generated Content:*\n>>> {content}",
            },
        },
        {
            "type": "actions",
            "elements": [
                {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": "✅ Yes (Approve & Post)",
                        "emoji": True,
                    },
                    "style": "primary",
                    "value": post_id,
                    "action_id": "approve_linkedin_post",
                },
                {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": "❌ No (Discard)",
                        "emoji": True,
                    },
                    "style": "danger",
                    "value": post_id,
                    "action_id": "discard_linkedin_post",
                },
            ],
        },
    ]

# send a post approval request to slack via webhook
def send_approval_request(
    post_id: str,
    content: str,
    webhook_url: str | None = None,
) -> dict:
    url = webhook_url or SLACK_WEBHOOK_URL
    if not url:
        raise ValueError("SLACK_WEBHOOK_URL is not set. Please provide it in the .env file.")

    blocks = build_approval_blocks(post_id=post_id, content=content)
    fallback_text = f"LinkedIn Post Approval Request for ID: {post_id}"

    payload = {
        "text": fallback_text,
        "blocks": blocks,
    }

    try:
        response = requests.post(url, json=payload, timeout=10)
        if response.status_code == 200:
            return {
                "success": True,
                "status": "sent",
                "post_id": post_id,
            }
        else:
            logger.error(f"Slack webhook failed ({response.status_code}): {response.text}")
            return {
                "success": False,
                "status": "failed",
                "status_code": response.status_code,
                "error": response.text,
            }
    except requests.RequestException as err:
        logger.error(f"network error sending message to Slack: {err}")
        return {
            "success": False,
            "status": "failed",
            "error": str(err),
        }

# update the original slack message after user clicks an action button
def update_slack_message(
    response_url: str,
    post_id: str,
    action_type: str,
    detail_message: str = "",
) -> bool:
    if action_type == "approved":
        status_text = f"✅ *Post `{post_id}` was APPROVED and published to LinkedIn!*"
    else:
        status_text = f"❌ *Post `{post_id}` was DISCARDED by user.*"

    blocks = [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": status_text,
            },
        }
    ]

    if detail_message:
        blocks.append(
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"_{detail_message}_",
                },
            }
        )

    payload = {
        "replace_original": True,
        "text": status_text,
        "blocks": blocks,
    }

    try:
        response = requests.post(response_url, json=payload, timeout=10)
        return response.status_code == 200
    except requests.RequestException as err:
        logger.error(f"failed to update Slack message via response_url: {err}")
        return False
