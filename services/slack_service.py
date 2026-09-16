import logging
import requests
from config.settings import SLACK_WEBHOOK_URL
from data.post_storage import get_post_by_id, update_post_status
from services.linkedin_service import publish_post_to_linkedin

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

# record human button decision from slack webhook into storage
def record_slack_decision(
    action_id: str,
    post_id: str,
    response_url: str | None = None,
) -> dict:
    post_record = get_post_by_id(post_id)
    if not post_record:
        return {"success": False, "error": f"Post '{post_id}' not found."}

    decision_status = "approved" if action_id == "approve_linkedin_post" else "discarded"
    update_post_status(
        post_id=post_id,
        status=decision_status,
        extra_data={"response_url": response_url, "decision_action": action_id},
    )
    return {
        "success": True,
        "post_id": post_id,
        "decision": decision_status,
        "response_url": response_url,
    }

# execute the actual linkedin publish or discard based on recorded decision
def execute_post_decision(post_id: str) -> dict:
    post_record = get_post_by_id(post_id)
    if not post_record:
        return {"success": False, "error": f"Post '{post_id}' not found."}

    current_status = post_record.get("status")
    response_url = post_record.get("response_url")

    # if user approved the post, publish to linkedin
    if current_status == "approved":
        content = post_record.get("content", "")
        token = post_record.get("access_token")
        profile_id = post_record.get("profile_id")

        publish_result = publish_post_to_linkedin(
            content=content,
            access_token=token,
            person_urn=profile_id,
        )

        if publish_result.get("success"):
            post_urn = publish_result.get("post_urn", "published")
            update_post_status(
                post_id=post_id,
                status="published",
                extra_data={"linkedin_response": publish_result},
            )
            if response_url:
                update_slack_message(
                    response_url=response_url,
                    post_id=post_id,
                    action_type="approved",
                    detail_message=f"Published successfully to LinkedIn ({post_urn})",
                )
            return {
                "success": True,
                "status": "published",
                "post_id": post_id,
                "publish_result": publish_result,
            }
        else:
            error_message = publish_result.get("error", "Unknown error")
            update_post_status(
                post_id=post_id,
                status="publish_failed",
                extra_data={"linkedin_response": publish_result},
            )
            if response_url:
                update_slack_message(
                    response_url=response_url,
                    post_id=post_id,
                    action_type="approved",
                    detail_message=f"Failed to publish to LinkedIn: {error_message}",
                )
            return {
                "success": False,
                "status": "publish_failed",
                "post_id": post_id,
                "error": error_message,
            }

    # if user discarded the post, mark rejected without publishing
    elif current_status in ("discarded", "rejected"):
        update_post_status(post_id=post_id, status="rejected")
        if response_url:
            update_slack_message(
                response_url=response_url,
                post_id=post_id,
                action_type="discarded",
                detail_message="Post has been marked as discarded.",
            )
        return {"success": True, "status": "rejected", "post_id": post_id}

    # if post has already been published
    elif current_status == "published":
        return {
            "success": True,
            "status": "published",
            "post_id": post_id,
            "publish_result": post_record.get("linkedin_response"),
        }

    return {"success": False, "error": f"Post '{post_id}' is in unhandled state: '{current_status}'"}

# convenience function to record and immediately execute action
def process_slack_action(
    action_id: str,
    post_id: str,
    response_url: str | None = None,
) -> dict:
    record_result = record_slack_decision(action_id=action_id, post_id=post_id, response_url=response_url)
    if not record_result.get("success"):
        return record_result
    return execute_post_decision(post_id=post_id)
