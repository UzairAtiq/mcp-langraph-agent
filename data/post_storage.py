import json
import logging
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from config.constants import PostStatus
from config.settings import POSTS_STORAGE_PATH
from data.db import (
    get_postgres_connection,
    get_sqlite_connection,
    init_database_tables,
)

# configure post storage logger
logger = logging.getLogger("post_storage")

# ensure parent directories exist for json fallback
def _ensure_json_file() -> Path:
    storage_path = Path(POSTS_STORAGE_PATH)
    storage_path.parent.mkdir(parents=True, exist_ok=True)
    if not storage_path.exists():
        storage_path.write_text("{}", encoding="utf-8")
    return storage_path

# initialize posts table in database
def init_posts_db() -> None:
    init_database_tables()

# load all saved posts from json file fallback
def _load_posts_from_json() -> dict[str, dict[str, Any]]:
    json_path = _ensure_json_file()
    try:
        content = json_path.read_text(encoding="utf-8").strip()
        if not content:
            return {}
        return json.loads(content)
    except (json.JSONDecodeError, OSError):
        return {}

# save posts dictionary to json file fallback
def _save_posts_to_json(posts: dict[str, dict[str, Any]]) -> None:
    json_path = _ensure_json_file()
    json_path.write_text(json.dumps(posts, indent=2), encoding="utf-8")

# generate a sequential unique post id
def generate_next_post_id() -> str:
    posts = list_posts()
    count = len(posts) + 1
    short_uuid = uuid.uuid4().hex[:6]
    return f"post_{count}_{short_uuid}"

# save a new post record to persistent storage
def save_post_record(
    post_id: str,
    content: str,
    profile_id: str,
    access_token: str,
    status: str | PostStatus = PostStatus.PENDING,
) -> dict[str, Any]:
    init_posts_db()
    now_iso = datetime.now(timezone.utc).isoformat()
    status_str = status.value if isinstance(status, PostStatus) else str(status)

    record = {
        "post_id": post_id,
        "content": content,
        "profile_id": profile_id,
        "access_token": access_token,
        "status": status_str,
        "created_at": now_iso,
        "updated_at": now_iso,
        "linkedin_response": None,
        "response_url": None,
        "decision_action": None,
    }

    # persist to postgres if available
    conn = get_postgres_connection()
    if conn:
        try:
            with conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        INSERT INTO posts (
                            post_id, content, profile_id, access_token, status,
                            created_at, updated_at, linkedin_response, response_url, decision_action
                        )
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (post_id) DO UPDATE SET
                            content = EXCLUDED.content,
                            profile_id = EXCLUDED.profile_id,
                            access_token = EXCLUDED.access_token,
                            status = EXCLUDED.status,
                            updated_at = EXCLUDED.updated_at,
                            linkedin_response = EXCLUDED.linkedin_response,
                            response_url = EXCLUDED.response_url,
                            decision_action = EXCLUDED.decision_action;
                        """,
                        (
                            post_id,
                            content,
                            profile_id,
                            access_token,
                            status_str,
                            now_iso,
                            now_iso,
                            None,
                            None,
                            None,
                        ),
                    )
            return record
        except Exception as err:
            logger.warning(f"failed to save post to postgres, falling back to sqlite: {err}")

    # persist to sqlite
    try:
        with get_sqlite_connection() as sqlite_conn:
            sqlite_conn.execute(
                """
                INSERT INTO posts (
                    post_id, content, profile_id, access_token, status,
                    created_at, updated_at, linkedin_response, response_url, decision_action
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(post_id) DO UPDATE SET
                    content = excluded.content,
                    profile_id = excluded.profile_id,
                    access_token = excluded.access_token,
                    status = excluded.status,
                    updated_at = excluded.updated_at,
                    linkedin_response = excluded.linkedin_response,
                    response_url = excluded.response_url,
                    decision_action = excluded.decision_action;
                """,
                (
                    post_id,
                    content,
                    profile_id,
                    access_token,
                    status_str,
                    now_iso,
                    now_iso,
                    None,
                    None,
                    None,
                ),
            )
            sqlite_conn.commit()
        return record
    except Exception as err:
        logger.warning(f"failed to save post to sqlite, saving to json file: {err}")

    # fallback to json file
    json_posts = _load_posts_from_json()
    json_posts[post_id] = record
    _save_posts_to_json(json_posts)
    return record

# retrieve single post record by id
def get_post_by_id(post_id: str) -> dict[str, Any] | None:
    init_posts_db()
    conn = get_postgres_connection()
    if conn:
        try:
            with conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        SELECT post_id, content, profile_id, access_token, status,
                               created_at, updated_at, linkedin_response, response_url, decision_action
                        FROM posts
                        WHERE post_id = %s;
                        """,
                        (post_id,),
                    )
                    row = cur.fetchone()
                    if row:
                        parsed_response = json.loads(row[7]) if row[7] else None
                        return {
                            "post_id": row[0],
                            "content": row[1],
                            "profile_id": row[2],
                            "access_token": row[3],
                            "status": row[4],
                            "created_at": row[5],
                            "updated_at": row[6],
                            "linkedin_response": parsed_response,
                            "response_url": row[8],
                            "decision_action": row[9],
                        }
        except Exception as err:
            logger.warning(f"failed to fetch post from postgres: {err}")

    # check sqlite
    try:
        with get_sqlite_connection() as sqlite_conn:
            cur = sqlite_conn.cursor()
            cur.execute(
                """
                SELECT post_id, content, profile_id, access_token, status,
                       created_at, updated_at, linkedin_response, response_url, decision_action
                FROM posts
                WHERE post_id = ?;
                """,
                (post_id,),
            )
            row = cur.fetchone()
            if row:
                parsed_response = json.loads(row[7]) if row[7] else None
                return {
                    "post_id": row[0],
                    "content": row[1],
                    "profile_id": row[2],
                    "access_token": row[3],
                    "status": row[4],
                    "created_at": row[5],
                    "updated_at": row[6],
                    "linkedin_response": parsed_response,
                    "response_url": row[8],
                    "decision_action": row[9],
                }
    except Exception as err:
        logger.warning(f"failed to fetch post from sqlite: {err}")

    # check json fallback
    json_posts = _load_posts_from_json()
    return json_posts.get(post_id)

# update post status and extra metadata
def update_post_status(
    post_id: str,
    status: str | PostStatus,
    extra_data: dict[str, Any] | None = None,
) -> dict[str, Any] | None:
    init_posts_db()
    record = get_post_by_id(post_id)
    if not record:
        return None

    status_str = status.value if isinstance(status, PostStatus) else str(status)
    now_iso = datetime.now(timezone.utc).isoformat()
    record["status"] = status_str
    record["updated_at"] = now_iso

    if extra_data:
        for key, val in extra_data.items():
            record[key] = val

    linkedin_resp_str = json.dumps(record.get("linkedin_response")) if record.get("linkedin_response") else None
    response_url = record.get("response_url")
    decision_action = record.get("decision_action")

    conn = get_postgres_connection()
    if conn:
        try:
            with conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        UPDATE posts
                        SET status = %s,
                            updated_at = %s,
                            linkedin_response = %s,
                            response_url = COALESCE(%s, response_url),
                            decision_action = COALESCE(%s, decision_action)
                        WHERE post_id = %s;
                        """,
                        (status_str, now_iso, linkedin_resp_str, response_url, decision_action, post_id),
                    )
            return record
        except Exception as err:
            logger.warning(f"failed to update post in postgres: {err}")

    # update sqlite
    try:
        with get_sqlite_connection() as sqlite_conn:
            sqlite_conn.execute(
                """
                UPDATE posts
                SET status = ?,
                    updated_at = ?,
                    linkedin_response = ?,
                    response_url = COALESCE(?, response_url),
                    decision_action = COALESCE(?, decision_action)
                WHERE post_id = ?;
                """,
                (status_str, now_iso, linkedin_resp_str, response_url, decision_action, post_id),
            )
            sqlite_conn.commit()
        return record
    except Exception as err:
        logger.warning(f"failed to update post in sqlite: {err}")

    # fallback to json
    json_posts = _load_posts_from_json()
    json_posts[post_id] = record
    _save_posts_to_json(json_posts)
    return record

# list all saved post records
def list_posts() -> list[dict[str, Any]]:
    init_posts_db()
    conn = get_postgres_connection()
    if conn:
        try:
            with conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        SELECT post_id, content, profile_id, access_token, status,
                               created_at, updated_at, linkedin_response, response_url, decision_action
                        FROM posts
                        ORDER BY created_at DESC;
                        """
                    )
                    rows = cur.fetchall()
                    if rows:
                        posts = []
                        for row in rows:
                            parsed_response = json.loads(row[7]) if row[7] else None
                            posts.append(
                                {
                                    "post_id": row[0],
                                    "content": row[1],
                                    "profile_id": row[2],
                                    "access_token": row[3],
                                    "status": row[4],
                                    "created_at": row[5],
                                    "updated_at": row[6],
                                    "linkedin_response": parsed_response,
                                    "response_url": row[8],
                                    "decision_action": row[9],
                                }
                            )
                        return posts
        except Exception as err:
            logger.warning(f"failed to list posts from postgres: {err}")

    # check sqlite
    try:
        with get_sqlite_connection() as sqlite_conn:
            cur = sqlite_conn.cursor()
            cur.execute(
                """
                SELECT post_id, content, profile_id, access_token, status,
                       created_at, updated_at, linkedin_response, response_url, decision_action
                FROM posts
                ORDER BY created_at DESC;
                """
            )
            rows = cur.fetchall()
            if rows:
                posts = []
                for row in rows:
                    parsed_response = json.loads(row[7]) if row[7] else None
                    posts.append(
                        {
                            "post_id": row[0],
                            "content": row[1],
                            "profile_id": row[2],
                            "access_token": row[3],
                            "status": row[4],
                            "created_at": row[5],
                            "updated_at": row[6],
                            "linkedin_response": parsed_response,
                            "response_url": row[8],
                            "decision_action": row[9],
                        }
                    )
                return posts
    except Exception as err:
        logger.warning(f"failed to list posts from sqlite: {err}")

    # fallback to json
    json_posts = _load_posts_from_json()
    return list(json_posts.values())
