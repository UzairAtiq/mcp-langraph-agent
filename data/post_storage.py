import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from config.constants import PostStatus
from config.settings import POSTS_STORAGE_PATH

# ensure parent directory and storage file exist
def _ensure_storage_directory() -> Path:
    storage_path = Path(POSTS_STORAGE_PATH)
    storage_path.parent.mkdir(parents=True, exist_ok=True)
    if not storage_path.exists():
        storage_path.write_text("{}", encoding="utf-8")
    return storage_path

# load all saved posts from json file
def load_all_posts() -> dict[str, dict]:
    storage_path = _ensure_storage_directory()
    try:
        content = storage_path.read_text(encoding="utf-8").strip()
        if not content:
            return {}
        return json.loads(content)
    except (json.JSONDecodeError, OSError):
        return {}

# write posts dictionary back to json file
def _save_all_posts(posts: dict[str, dict]) -> None:
    storage_path = _ensure_storage_directory()
    storage_path.write_text(json.dumps(posts, indent=2), encoding="utf-8")

# generate a sequential unique post id
def generate_next_post_id() -> str:
    posts = load_all_posts()
    existing_count = len(posts) + 1
    short_uuid = uuid.uuid4().hex[:6]
    return f"post_{existing_count}_{short_uuid}"

# save a new post record to storage
def save_post_record(
    post_id: str,
    content: str,
    profile_id: str,
    access_token: str,
    status: str | PostStatus = PostStatus.PENDING,
) -> dict:
    posts = load_all_posts()
    timestamp = datetime.now(timezone.utc).isoformat()

    # construct full post record
    post_record = {
        "post_id": post_id,
        "content": content,
        "profile_id": profile_id,
        "access_token": access_token,
        "status": status.value if isinstance(status, PostStatus) else str(status),
        "created_at": timestamp,
        "updated_at": timestamp,
        "linkedin_response": None,
    }

    posts[post_id] = post_record
    _save_all_posts(posts)
    return post_record

# retrieve a single post record by its id
def get_post_by_id(post_id: str) -> dict | None:
    posts = load_all_posts()
    return posts.get(post_id)

# update the status and optional extra data for an existing post
def update_post_status(
    post_id: str,
    status: str | PostStatus,
    extra_data: dict | None = None,
) -> dict | None:
    posts = load_all_posts()
    post_record = posts.get(post_id)

    # return none if post does not exist
    if not post_record:
        return None

    # update status and timestamp
    post_record["status"] = status.value if isinstance(status, PostStatus) else str(status)
    post_record["updated_at"] = datetime.now(timezone.utc).isoformat()

    # merge extra fields if provided
    if extra_data:
        for key, value in extra_data.items():
            post_record[key] = value

    posts[post_id] = post_record
    _save_all_posts(posts)
    return post_record

# return all post records as a list
def list_posts() -> list[dict]:
    posts = load_all_posts()
    return list(posts.values())
