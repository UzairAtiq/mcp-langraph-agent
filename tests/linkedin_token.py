import json
import os
import sys
from pathlib import Path
import requests
from dotenv import load_dotenv

# resolve project root directory and env path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
ENV_FILE_PATH = PROJECT_ROOT / ".env"

# load environment variables from project root .env
load_dotenv(dotenv_path=ENV_FILE_PATH)

# read oauth credentials from environment
CLIENT_ID = os.getenv("LINKEDIN_CLIENT_ID")
CLIENT_SECRET = os.getenv("LINKEDIN_CLIENT_SECRET")
REDIRECT_URI = os.getenv("LINKEDIN_REDIRECT_URI", "http://localhost:8000/callback")

# linkedin oauth and userinfo endpoints
TOKEN_URL = "https://www.linkedin.com/oauth/v2/accessToken"
USERINFO_URL = "https://api.linkedin.com/v2/userinfo"

# update or append key-value pairs in project root .env file
def update_env_file(updates: dict[str, str]) -> None:
    existing_lines = []
    if ENV_FILE_PATH.exists():
        existing_lines = ENV_FILE_PATH.read_text(encoding="utf-8").splitlines()

    updated_keys = set()
    new_lines = []

    for line in existing_lines:
        stripped_line = line.strip()
        # preserve empty lines and comments
        if not stripped_line or stripped_line.startswith("#"):
            new_lines.append(line)
            continue

        key_value = stripped_line.split("=", 1)
        current_key = key_value[0].strip()

        if current_key in updates:
            new_lines.append(f"{current_key}={updates[current_key]}")
            updated_keys.add(current_key)
        else:
            new_lines.append(line)

    # append any new keys that were not present in existing file
    for key, value in updates.items():
        if key not in updated_keys:
            new_lines.append(f"{key}={value}")

    ENV_FILE_PATH.write_text("\n".join(new_lines) + "\n", encoding="utf-8")

# fetch user profile information using access token
def fetch_user_profile(access_token: str) -> dict:
    headers = {"Authorization": f"Bearer {access_token}"}
    try:
        response = requests.get(USERINFO_URL, headers=headers, timeout=10)
        if response.status_code == 200:
            return response.json()
        print(f"warning: userinfo endpoint returned status {response.status_code}: {response.text}")
        return {}
    except requests.RequestException as err:
        print(f"warning: failed to request user profile: {err}")
        return {}

# exchange authorization code for access token and update environment
def exchange_code_for_token(code: str) -> bool:
    if not CLIENT_ID or not CLIENT_SECRET:
        print(f"ERROR: LINKEDIN_CLIENT_ID or LINKEDIN_CLIENT_SECRET missing from {ENV_FILE_PATH}")
        return False

    request_payload = {
        "grant_type": "authorization_code",
        "code": code.strip(),
        "redirect_uri": REDIRECT_URI,
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
    }

    try:
        response = requests.post(
            TOKEN_URL,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            data=request_payload,
            timeout=15,
        )
    except requests.RequestException as err:
        print(f"network error during token exchange: {err}")
        return False

    try:
        token_payload = response.json()
    except ValueError:
        print(f"non-json response received: {response.text}")
        return False

    if "access_token" not in token_payload:
        print("token exchange failed:")
        print(f"  error: {token_payload.get('error')}")
        print(f"  description: {token_payload.get('error_description')}")
        return False

    access_token = token_payload["access_token"]
    expires_in = token_payload.get("expires_in")
    scopes = token_payload.get("scope")

    print("\n✅ SUCCESS: Access token received.")
    print(f"  Token Preview: {access_token[:10]}...{access_token[-4:]}")
    print(f"  Expires In: {expires_in} seconds")
    print(f"  Scopes Granted: {scopes}")

    # fetch user profile details to resolve sub id
    profile_details = fetch_user_profile(access_token=access_token)
    sub_identifier = profile_details.get("sub", "")
    person_urn = f"urn:li:person:{sub_identifier}" if sub_identifier else ""

    # prepare env updates dictionary
    env_updates = {
        "LINKEDIN_ACCESS_TOKEN": access_token,
    }

    if profile_details:
        # store profile dictionary in LINKEDIN_PROFILE_ID
        env_updates["LINKEDIN_PROFILE_ID"] = json.dumps(profile_details)
        if person_urn:
            env_updates["LINKEDIN_PERSON_URN"] = person_urn
            print(f"  Profile ID (sub): {sub_identifier}")
            print(f"  Person URN: {person_urn}")

    # automatically update .env file in project root
    update_env_file(env_updates)
    print(f"✅ Automatically updated {ENV_FILE_PATH} with access token and profile info.")

    # also save backup .linkedin_token file
    token_backup_file = PROJECT_ROOT / ".linkedin_token"
    token_backup_file.write_text(access_token, encoding="utf-8")
    print(f"✅ Token backup written to {token_backup_file}.")

    return True

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python tests/linkedin_token.py <authorization_code>")
        print("Example: python tests/linkedin_token.py AQT...")
        sys.exit(1)

    auth_code = sys.argv[1]
    success = exchange_code_for_token(auth_code)
    if not success:
        sys.exit(1)