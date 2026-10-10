import logging
import requests
from config.settings import LINKEDIN_PERSON_URN, get_linkedin_access_token

# configure linkedin service logger
logger = logging.getLogger("linkedin_service")

# linkedin api endpoint constants
LINKEDIN_USERINFO_URL = "https://api.linkedin.com/v2/userinfo"
LINKEDIN_ME_URL = "https://api.linkedin.com/v2/me"
LINKEDIN_UGC_POST_URL = "https://api.linkedin.com/v2/ugcPosts"

# fetch the linkedin person urn using the access token
def fetch_linkedin_person_urn(access_token: str | None = None) -> str:
    # retrieve access token from argument or environment/file fallback
    token = access_token or get_linkedin_access_token()
    if not token:
        raise ValueError("LinkedIn access token is missing. Please authenticate first.")

    # check if direct person urn is already configured
    if LINKEDIN_PERSON_URN:
        return LINKEDIN_PERSON_URN.strip()

    headers = {"Authorization": f"Bearer {token}"}

    # try openid userinfo endpoint first
    try:
        response = requests.get(LINKEDIN_USERINFO_URL, headers=headers, timeout=10)
        if response.status_code == 200:
            payload = response.json()
            sub_id = payload.get("sub")
            if sub_id:
                return f"urn:li:person:{sub_id}"
    except requests.RequestException as err:
        logger.warning(f"failed to fetch person urn from userinfo endpoint: {err}")

    # fallback to /v2/me endpoint
    try:
        response = requests.get(LINKEDIN_ME_URL, headers=headers, timeout=10)
        if response.status_code == 200:
            payload = response.json()
            member_id = payload.get("id")
            if member_id:
                return f"urn:li:person:{member_id}"
    except requests.RequestException as err:
        logger.warning(f"failed to fetch member id from /v2/me endpoint: {err}")

    # raise error when all urn resolution methods fail
    raise RuntimeError("unable to resolve LinkedIn Person URN using provided access token")

# publish a text post to linkedin
def publish_post_to_linkedin(
    content: str,
    access_token: str | None = None,
    person_urn: str | None = None,
) -> dict:
    # retrieve access token from argument or configuration
    token = access_token or get_linkedin_access_token()
    if not token:
        raise ValueError("LinkedIn access token is missing. Cannot publish post.")

    # determine author urn using explicit parameter or dynamic lookup
    author_urn = person_urn or fetch_linkedin_person_urn(token)

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "X-Restli-Protocol-Version": "2.0.0",
    }

    payload = {
        "author": author_urn,
        "lifecycleState": "PUBLISHED",
        "specificContent": {
            "com.linkedin.ugc.ShareContent": {
                "shareCommentary": {"text": content},
                "shareMediaCategory": "NONE",
            }
        },
        "visibility": {
            "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
        },
    }

    try:
        # submit post payload to linkedin ugc posts endpoint
        response = requests.post(
            LINKEDIN_UGC_POST_URL,
            headers=headers,
            json=payload,
            timeout=15,
        )

        # handle successful response
        if response.status_code in (200, 201):
            response_json = response.json() if response.text else {}
            post_urn = response_json.get("id") or response.headers.get("x-restli-id", "")
            return {
                "success": True,
                "status": "published",
                "post_urn": post_urn,
                "author": author_urn,
                "response": response_json,
            }

        # handle api error response
        logger.error(f"LinkedIn publishing failed ({response.status_code}): {response.text}")
        return {
            "success": False,
            "status": "failed",
            "status_code": response.status_code,
            "error": response.text,
        }

    except requests.RequestException as err:
        # handle network and connection errors
        logger.error(f"network error while publishing post to LinkedIn: {err}")
        return {
            "success": False,
            "status": "failed",
            "error": str(err),
        }
