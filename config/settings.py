import json
import os
from pathlib import Path
from dotenv import load_dotenv

# load environment variables from .env file in project root
load_dotenv()

# base project directory
BASE_DIR = Path(__file__).resolve().parent.parent

# groq llm configuration
GROQ_API_KEY = os.getenv("GROQ_API_KEY") or os.getenv("GROK_API_KEY")
GROQ_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")

# database and slack configuration
DATABASE_URL = os.getenv("CONNECTION_STRING_SUPABASE")
SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL")

# langfuse observability configuration
LANGFUSE_SECRET_KEY = os.getenv("LANGFUSE_SECRET_KEY")
LANGFUSE_PUBLIC_KEY = os.getenv("LANGFUSE_PUBLIC_KEY")
LANGFUSE_BASE_URL = os.getenv("LANGFUSE_BASE_URL")

# storage path for posts
POSTS_STORAGE_PATH = os.getenv(
    "POSTS_STORAGE_PATH",
    str(BASE_DIR / "data" / "posts.json")
)

# helper function to load linkedin access token from file or env
def get_linkedin_access_token() -> str | None:
    # check explicit environment variable first
    token_from_env = os.getenv("LINKEDIN_ACCESS_TOKEN")
    if token_from_env:
        return token_from_env.strip()

    # fallback to local .linkedin_token file
    token_file_path = BASE_DIR / ".linkedin_token"
    if token_file_path.exists():
        token_content = token_file_path.read_text(encoding="utf-8").strip()
        if token_content:
            return token_content

    return None

# helper function to extract person urn from LINKEDIN_PROFILE_ID or LINKEDIN_PERSON_URN
def get_linkedin_person_urn() -> str | None:
    # check explicit person urn in environment
    direct_urn = os.getenv("LINKEDIN_PERSON_URN")
    if direct_urn:
        return direct_urn.strip()

    # check profile id dictionary variable in environment
    raw_profile_id = os.getenv("LINKEDIN_PROFILE_ID")
    if raw_profile_id:
        try:
            profile_data = json.loads(raw_profile_id)
            if isinstance(profile_data, dict):
                sub_identifier = profile_data.get("sub") or profile_data.get("id")
                if sub_identifier:
                    return f"urn:li:person:{sub_identifier}"
        except (json.JSONDecodeError, TypeError):
            cleaned_id = raw_profile_id.strip()
            if cleaned_id.startswith("urn:li:person:"):
                return cleaned_id
            return f"urn:li:person:{cleaned_id}"

    return None

LINKEDIN_ACCESS_TOKEN = get_linkedin_access_token()
LINKEDIN_PERSON_URN = get_linkedin_person_urn()