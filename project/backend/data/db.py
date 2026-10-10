import logging
import sqlite3
from pathlib import Path
from typing import Any
import psycopg
from config.settings import BASE_DIR, DATABASE_URL

# configure database logger
logger = logging.getLogger("db_storage")

# sqlite database path
SQLITE_DB_PATH = BASE_DIR / "data" / "app.db"

# tracking flag for postgres availability
_postgres_available = True if DATABASE_URL else False

# ensure directory for sqlite database exists
def ensure_sqlite_directory() -> Path:
    SQLITE_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    return SQLITE_DB_PATH

# connect to postgres with connection timeout, falling back gracefully
def get_postgres_connection() -> psycopg.Connection | None:
    global _postgres_available
    if not _postgres_available or not DATABASE_URL:
        return None
    try:
        return psycopg.connect(DATABASE_URL, connect_timeout=3)
    except Exception as err:
        logger.warning(f"PostgreSQL connection unavailable ({err}). Using SQLite fallback.")
        _postgres_available = False
        return None

# connect to sqlite database
def get_sqlite_connection() -> sqlite3.Connection:
    ensure_sqlite_directory()
    return sqlite3.connect(SQLITE_DB_PATH)

# check whether postgres is currently available
def is_postgres_active() -> bool:
    return _postgres_available and bool(DATABASE_URL)

# initialize all required database tables across active storage backend
def init_database_tables() -> None:
    # initialize postgres tables if available
    conn = get_postgres_connection()
    if conn:
        try:
            with conn:
                with conn.cursor() as cur:
                    # create tokens table
                    cur.execute(
                        """
                        CREATE TABLE IF NOT EXISTS linkedin_tokens (
                            id VARCHAR(50) PRIMARY KEY,
                            access_token TEXT NOT NULL,
                            refresh_token TEXT,
                            expires_at TIMESTAMP WITH TIME ZONE,
                            refresh_expires_at TIMESTAMP WITH TIME ZONE,
                            profile_id TEXT,
                            person_urn TEXT,
                            scope TEXT,
                            updated_at TIMESTAMP WITH TIME ZONE
                        );
                        """
                    )
                    # create posts table
                    cur.execute(
                        """
                        CREATE TABLE IF NOT EXISTS posts (
                            post_id VARCHAR(100) PRIMARY KEY,
                            content TEXT NOT NULL,
                            profile_id TEXT,
                            access_token TEXT,
                            status VARCHAR(50) NOT NULL,
                            created_at TEXT NOT NULL,
                            updated_at TEXT NOT NULL,
                            linkedin_response TEXT,
                            response_url TEXT,
                            decision_action TEXT
                        );
                        """
                    )
            return
        except Exception as err:
            logger.warning(f"failed to initialize postgres tables: {err}")

    # initialize sqlite fallback tables
    with get_sqlite_connection() as sqlite_conn:
        sqlite_conn.execute(
            """
            CREATE TABLE IF NOT EXISTS linkedin_tokens (
                id TEXT PRIMARY KEY,
                access_token TEXT NOT NULL,
                refresh_token TEXT,
                expires_at TEXT,
                refresh_expires_at TEXT,
                profile_id TEXT,
                person_urn TEXT,
                scope TEXT,
                updated_at TEXT
            );
            """
        )
        sqlite_conn.execute(
            """
            CREATE TABLE IF NOT EXISTS posts (
                post_id TEXT PRIMARY KEY,
                content TEXT NOT NULL,
                profile_id TEXT,
                access_token TEXT,
                status TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                linkedin_response TEXT,
                response_url TEXT,
                decision_action TEXT
            );
            """
        )
        sqlite_conn.commit()
