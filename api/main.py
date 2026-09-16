import json
import logging
from typing import Annotated
from fastapi import FastAPI, Form, HTTPException, Response, status
from data.post_storage import (
    get_post_by_id,
    list_posts,
    update_post_status,
)
from services.linkedin_service import publish_post_to_linkedin
from services.slack_service import update_slack_message

# configure application logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("api_main")

# initialize fastapi app
app = FastAPI(
    title="LinkedIn Post Approval & Interactivity API",
    description="Handles Slack interactive button actions and manages LinkedIn publishing workflows.",
    version="1.0.0",
)

# health check endpoint
@app.get("/health")
def health_check() -> dict:
    return {"status": "healthy"}

# list all saved posts
@app.get("/posts")
def get_all_posts(status_filter: str | None = None) -> dict:
    records = list_posts()
    if status_filter:
        records = [
            post for post in records
            if post.get("status", "").lower() == status_filter.lower()
        ]

    # mask sensitive access tokens before returning
    sanitized_records = []
    for record in records:
        safe_copy = dict(record)
        if safe_copy.get("access_token"):
            safe_copy["access_token"] = safe_copy["access_token"][:10] + "..."
        sanitized_records.append(safe_copy)

    return {"total_count": len(sanitized_records), "posts": sanitized_records}

# retrieve a single post by id
@app.get("/posts/{post_id}")
def get_single_post(post_id: str) -> dict:
    record = get_post_by_id(post_id)
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Post '{post_id}' not found.",
        )

    safe_copy = dict(record)
    if safe_copy.get("access_token"):
        safe_copy["access_token"] = safe_copy["access_token"][:10] + "..."
    return safe_copy

# slack interactivity webhook endpoint
@app.post("/slack/interactions")
async def handle_slack_interactions(payload: Annotated[str, Form()]) -> Response:
    # parse the json payload sent by slack
    try:
        interaction_data = json.loads(payload)
    except (json.JSONDecodeError, TypeError) as parse_err:
        logger.error(f"failed to parse Slack interaction payload: {parse_err}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid JSON payload format.",
        )

    actions = interaction_data.get("actions", [])
    if not actions:
        logger.warning("received Slack interaction without any actions")
        return Response(status_code=status.HTTP_200_OK)

    primary_action = actions[0]
    action_id = primary_action.get("action_id")
    post_id = primary_action.get("value")
    response_url = interaction_data.get("response_url")

    logger.info(f"processing Slack action: '{action_id}' for post_id: '{post_id}'")

    if not post_id:
        logger.error("missing post_id in action value")
        return Response(status_code=status.HTTP_200_OK)

    # find post in storage
    post_record = get_post_by_id(post_id)
    if not post_record:
        logger.error(f"post with id '{post_id}' not found in storage")
        if response_url:
            update_slack_message(
                response_url=response_url,
                post_id=post_id,
                action_type="discarded",
                detail_message="Error: Post record not found in database.",
            )
        return Response(status_code=status.HTTP_200_OK)

    # handle approval action
    if action_id == "approve_linkedin_post":
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

    # handle discard action
    elif action_id == "discard_linkedin_post":
        update_post_status(
            post_id=post_id,
            status="rejected",
        )
        if response_url:
            update_slack_message(
                response_url=response_url,
                post_id=post_id,
                action_type="discarded",
                detail_message="Post has been marked as discarded.",
            )

    return Response(status_code=status.HTTP_200_OK)

# run uvicorn server directly if executed
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api.main:app", host="0.0.0.0", port=8000, reload=True)
