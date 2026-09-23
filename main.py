import json
import logging
import urllib.parse
import uuid
from typing import Annotated, Any
from fastapi import FastAPI, Form, HTTPException, Query, Response, status
from fastapi.responses import HTMLResponse, RedirectResponse
import requests
from config.constants import PostStatus
from config.settings import (
    DATABASE_URL,
    LINKEDIN_CLIENT_ID,
    LINKEDIN_CLIENT_SECRET,
    LINKEDIN_REDIRECT_URI,
    PORT,
    get_linkedin_person_urn,
)
from data.post_storage import (
    generate_next_post_id,
    get_post_by_id,
    list_posts,
    save_post_record,
)
from data.token_storage import (
    get_linkedin_token_record,
    get_valid_linkedin_access_token,
    refresh_linkedin_access_token,
    save_linkedin_token,
)
from services.groq_service import generate_linkedin_post_content
from services.linkedin_service import fetch_linkedin_person_urn
from services.slack_service import (
    execute_post_decision,
    record_slack_decision,
    send_approval_request,
)

# configure application logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("main_api")

# initialize fastapi app
app = FastAPI(
    title="LinkedIn Post Automation & Slack Approval API",
    description="Unified API service managing LinkedIn OAuth, automated token refreshes, Slack interactive approvals, and post publishing.",
    version="2.0.0",
)

# root dashboard endpoint
@app.get("/", response_class=HTMLResponse)
async def root_dashboard() -> str:
    token_record = get_linkedin_token_record()
    is_authenticated = bool(token_record and token_record.get("access_token"))
    person_urn = token_record.get("person_urn") if token_record else "Not configured"
    expires_at = token_record.get("expires_at") if token_record else "N/A"
    db_backend = "PostgreSQL" if DATABASE_URL else "SQLite (data/app.db)"

    return _render_dashboard_html(
        is_authenticated=is_authenticated,
        person_urn=person_urn,
        expires_at=expires_at,
        db_backend=db_backend,
    )

# health check endpoint for cloud hosts
@app.get("/health")
def health_check() -> dict[str, Any]:
    token_valid = bool(get_valid_linkedin_access_token())
    return {
        "status": "healthy",
        "service": "linkedin-slack-agent",
        "database": "postgresql" if DATABASE_URL else "sqlite",
        "linkedin_authenticated": token_valid,
    }

# linkedin oauth authorization redirect
@app.get("/linkedin/login")
def linkedin_login() -> RedirectResponse:
    if not LINKEDIN_CLIENT_ID:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="LINKEDIN_CLIENT_ID is not configured in environment.",
        )

    oauth_state = uuid.uuid4().hex
    params = {
        "response_type": "code",
        "client_id": LINKEDIN_CLIENT_ID,
        "redirect_uri": LINKEDIN_REDIRECT_URI,
        "state": oauth_state,
        "scope": "openid profile w_member_social email",
    }
    auth_url = f"https://www.linkedin.com/oauth/v2/authorization?{urllib.parse.urlencode(params)}"
    return RedirectResponse(url=auth_url)

# linkedin oauth callback endpoint
@app.get("/linkedin/callback", response_class=HTMLResponse)
async def linkedin_callback(
    code: str | None = Query(default=None),
    state: str | None = Query(default=None),
    error: str | None = Query(default=None),
    error_description: str | None = Query(default=None),
) -> HTMLResponse:
    if error:
        logger.error(f"LinkedIn OAuth error: {error} - {error_description}")
        return HTMLResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=_render_error_html(error_description or error),
        )

    if not code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Authorization code missing from LinkedIn callback.",
        )

    if not LINKEDIN_CLIENT_ID or not LINKEDIN_CLIENT_SECRET:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="LinkedIn client credentials not configured.",
        )

    # exchange authorization code for access and refresh tokens
    token_url = "https://www.linkedin.com/oauth/v2/accessToken"
    payload = {
        "grant_type": "authorization_code",
        "code": code.strip(),
        "redirect_uri": LINKEDIN_REDIRECT_URI,
        "client_id": LINKEDIN_CLIENT_ID,
        "client_secret": LINKEDIN_CLIENT_SECRET,
    }

    try:
        response = requests.post(
            token_url,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            data=payload,
            timeout=15,
        )
        token_data = response.json()
    except Exception as err:
        logger.error(f"failed during token exchange: {err}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to communicate with LinkedIn OAuth server: {err}",
        )

    if "access_token" not in token_data:
        err_msg = token_data.get("error_description") or token_data.get("error") or response.text
        logger.error(f"token exchange failed: {err_msg}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"LinkedIn token exchange failed: {err_msg}",
        )

    access_token = token_data["access_token"]
    refresh_token = token_data.get("refresh_token")
    expires_in = token_data.get("expires_in")
    refresh_expires_in = token_data.get("refresh_token_expires_in")
    scope = token_data.get("scope")

    # fetch user profile information
    user_name = "LinkedIn User"
    person_urn = ""
    profile_id_str = None

    try:
        userinfo_resp = requests.get(
            "https://api.linkedin.com/v2/userinfo",
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=10,
        )
        if userinfo_resp.status_code == 200:
            user_info = userinfo_resp.json()
            profile_id_str = json.dumps(user_info)
            user_name = user_info.get("name", user_name)
            sub = user_info.get("sub")
            if sub:
                person_urn = f"urn:li:person:{sub}"
    except Exception as err:
        logger.warning(f"failed to fetch userinfo in callback: {err}")

    # fallback to person urn resolver if openid sub is empty
    if not person_urn:
        try:
            person_urn = fetch_linkedin_person_urn(access_token=access_token)
        except Exception:
            person_urn = "urn:li:person:unknown"

    # save tokens and profile into persistent database
    save_linkedin_token(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=expires_in,
        refresh_expires_in=refresh_expires_in,
        profile_id=profile_id_str,
        person_urn=person_urn,
        scope=scope,
    )

    logger.info(f"successfully authenticated LinkedIn user: {user_name} ({person_urn})")

    return HTMLResponse(
        content=_render_callback_success_html(
            user_name=user_name,
            person_urn=person_urn,
            expires_in=expires_in,
            refresh_token=refresh_token,
        )
    )

# linkedin token metadata endpoint
@app.get("/linkedin/status")
def linkedin_status() -> dict[str, Any]:
    record = get_linkedin_token_record()
    if not record:
        return {
            "authenticated": False,
            "message": "No LinkedIn token found. Please visit /linkedin/login to authenticate.",
        }

    access_token = record.get("access_token", "")
    masked_token = f"{access_token[:8]}...{access_token[-4:]}" if len(access_token) > 12 else "present"

    return {
        "authenticated": True,
        "token_preview": masked_token,
        "person_urn": record.get("person_urn"),
        "expires_at": str(record.get("expires_at")),
        "refresh_token_available": bool(record.get("refresh_token")),
        "scope": record.get("scope"),
        "updated_at": str(record.get("updated_at")),
    }

# manual or programmatic token refresh endpoint
@app.post("/linkedin/refresh")
def refresh_token_endpoint() -> dict[str, Any]:
    result = refresh_linkedin_access_token()
    if not result.get("success"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.get("error", "Token refresh failed."),
        )
    return {"status": "refreshed", "message": "LinkedIn access token successfully refreshed."}

# slack interactive webhook endpoint
@app.post("/slack/interactions")
async def handle_slack_interactions(payload: Annotated[str, Form()]) -> Response:
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
        logger.warning("received Slack interaction without actions")
        return Response(status_code=status.HTTP_200_OK)

    primary_action = actions[0]
    action_id = primary_action.get("action_id", "")
    post_id = primary_action.get("value", "")
    response_url = interaction_data.get("response_url")

    logger.info(f"processing Slack action: '{action_id}' for post_id: '{post_id}'")

    if not post_id:
        return Response(status_code=status.HTTP_200_OK)

    # record decision in storage
    record_slack_decision(
        action_id=action_id,
        post_id=post_id,
        response_url=response_url,
    )

    # execute post decision immediately
    execute_result = execute_post_decision(post_id=post_id)
    logger.info(f"executed post decision for '{post_id}': {execute_result}")

    return Response(status_code=status.HTTP_200_OK)

# list all saved posts
@app.get("/posts")
def get_all_posts(status_filter: str | None = None) -> dict[str, Any]:
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

# retrieve single post by id
@app.get("/posts/{post_id}")
def get_single_post(post_id: str) -> dict[str, Any]:
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

# trigger post generation and slack approval request for testing
@app.post("/posts/generate")
def generate_post_endpoint(
    topic: str = Query(default="AI advancements and modern software engineering"),
) -> dict[str, Any]:
    token = get_valid_linkedin_access_token()
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="LinkedIn is not authenticated. Please visit /linkedin/login first.",
        )

    person_urn = get_linkedin_person_urn() or fetch_linkedin_person_urn(token)
    post_content = generate_linkedin_post_content(topic=topic)
    post_id = generate_next_post_id()

    save_post_record(
        post_id=post_id,
        content=post_content,
        profile_id=person_urn,
        access_token=token,
        status=PostStatus.PENDING,
    )

    slack_res = send_approval_request(
        post_id=post_id,
        content=post_content,
    )

    return {
        "success": True,
        "post_id": post_id,
        "person_urn": person_urn,
        "status": "pending_approval",
        "generated_content": post_content,
        "slack_delivery": slack_res,
        "message": "Post generated and sent to Slack for user approval.",
    }

# render dashboard html string
def _render_dashboard_html(
    is_authenticated: bool,
    person_urn: str,
    expires_at: Any,
    db_backend: str,
) -> str:
    auth_badge = (
        '<span style="color: #10b981; font-weight: bold; background: #ecfdf5; padding: 4px 10px; border-radius: 9999px;">Authenticated Active</span>'
        if is_authenticated
        else '<span style="color: #ef4444; font-weight: bold; background: #fef2f2; padding: 4px 10px; border-radius: 9999px;">Not Connected</span>'
    )
    return f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>LinkedIn Agent Service</title>
        <style>
            body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: #0f172a; color: #f8fafc; margin: 0; padding: 40px 20px; }}
            .container {{ max-width: 800px; margin: 0 auto; background: #1e293b; border-radius: 16px; padding: 32px; box-shadow: 0 10px 25px rgba(0,0,0,0.3); border: 1px solid #334155; }}
            h1 {{ color: #38bdf8; margin-top: 0; font-size: 28px; }}
            .status-card {{ background: #0f172a; border-radius: 10px; padding: 20px; margin: 20px 0; border: 1px solid #334155; }}
            .status-row {{ display: flex; justify-content: space-between; padding: 10px 0; border-bottom: 1px solid #1e293b; }}
            .status-row:last-child {{ border-bottom: none; }}
            .btn {{ display: inline-block; background: #0284c7; color: white; text-decoration: none; padding: 12px 24px; border-radius: 8px; font-weight: 600; margin-right: 12px; margin-top: 10px; transition: background 0.2s; }}
            .btn:hover {{ background: #0369a1; }}
            .btn-secondary {{ background: #334155; }}
            .btn-secondary:hover {{ background: #475569; }}
            .endpoint-list {{ background: #0f172a; border-radius: 10px; padding: 16px; font-family: monospace; font-size: 14px; margin-top: 20px; }}
            .endpoint-list div {{ padding: 6px 0; color: #94a3b8; }}
            .endpoint-list span {{ color: #38bdf8; font-weight: bold; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>LinkedIn Agent & Slack Interactivity Hub</h1>
            <p>Unified microservice handling automated content generation, Slack approvals, and LinkedIn publishing.</p>
            
            <div class="status-card">
                <div class="status-row">
                    <span>LinkedIn OAuth Status:</span>
                    {auth_badge}
                </div>
                <div class="status-row">
                    <span>Person URN:</span>
                    <span><code>{person_urn}</code></span>
                </div>
                <div class="status-row">
                    <span>Token Expiration:</span>
                    <span><code>{expires_at}</code></span>
                </div>
                <div class="status-row">
                    <span>Database Storage:</span>
                    <span><code>{db_backend}</code></span>
                </div>
            </div>

            <div>
                <a href="/linkedin/login" class="btn">Connect / Re-auth LinkedIn</a>
                <a href="/docs" class="btn btn-secondary">Interactive Swagger Docs</a>
                <a href="/posts" class="btn btn-secondary">View Posts JSON</a>
            </div>

            <h3>Available Endpoints</h3>
            <div class="endpoint-list">
                <div><span>GET  /health</span> - Service healthcheck for Render/Railway</div>
                <div><span>GET  /linkedin/login</span> - Starts 1-click LinkedIn OAuth flow</div>
                <div><span>GET  /linkedin/callback</span> - OAuth redirect endpoint</div>
                <div><span>GET  /linkedin/status</span> - Token validity and expiration metadata</div>
                <div><span>POST /linkedin/refresh</span> - Manually trigger token refresh</div>
                <div><span>POST /slack/interactions</span> - Slack Block Kit interactive buttons webhook</div>
                <div><span>GET  /posts</span> - List all generated posts</div>
                <div><span>POST /posts/generate</span> - Test trigger post generation & Slack approval</div>
            </div>
        </div>
    </body>
    </html>
    """

# render callback success html
def _render_callback_success_html(
    user_name: str,
    person_urn: str,
    expires_in: Any,
    refresh_token: Any,
) -> str:
    return f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>LinkedIn Authentication Successful</title>
        <style>
            body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: #0f172a; color: #f8fafc; display: flex; align-items: center; justify-content: center; min-height: 80vh; margin: 0; padding: 20px; }}
            .card {{ max-width: 500px; background: #1e293b; border-radius: 16px; padding: 32px; text-align: center; border: 1px solid #334155; box-shadow: 0 10px 25px rgba(0,0,0,0.3); }}
            .icon {{ font-size: 48px; margin-bottom: 16px; }}
            h2 {{ color: #38bdf8; margin: 0 0 12px 0; }}
            p {{ color: #94a3b8; line-height: 1.5; }}
            .details {{ background: #0f172a; padding: 14px; border-radius: 8px; font-family: monospace; font-size: 13px; text-align: left; margin: 20px 0; color: #cbd5e1; word-break: break-all; }}
            .btn {{ display: inline-block; background: #0284c7; color: white; text-decoration: none; padding: 12px 24px; border-radius: 8px; font-weight: 600; margin-top: 10px; }}
        </style>
    </head>
    <body>
        <div class="card">
            <div class="icon">🎉</div>
            <h2>LinkedIn Connected Successfully!</h2>
            <p>Your OAuth tokens have been securely saved to persistent database storage with automatic token refresh enabled.</p>
            <div class="details">
                <div><strong>User:</strong> {user_name}</div>
                <div><strong>Person URN:</strong> {person_urn}</div>
                <div><strong>Expires In:</strong> {expires_in} seconds</div>
                <div><strong>Refresh Token:</strong> {'Available (Auto-refresh on)' if refresh_token else 'Standard token'}</div>
            </div>
            <a href="/" class="btn">Return to Dashboard</a>
        </div>
    </body>
    </html>
    """

# render error html
def _render_error_html(error_message: str) -> str:
    return f"""
    <div style="font-family: sans-serif; padding: 40px; text-align: center; background: #0f172a; color: white; min-height: 50vh;">
        <h2 style="color: #ef4444;">❌ LinkedIn Authorization Failed</h2>
        <p style="color: #94a3b8;">{error_message}</p>
        <a href="/linkedin/login" style="padding: 10px 20px; background: #0284c7; color: white; text-decoration: none; border-radius: 6px; display: inline-block; margin-top: 15px;">Try Again</a>
    </div>
    """

# run server directly when executed
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=PORT, reload=True)
