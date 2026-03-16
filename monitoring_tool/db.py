import logging
import sqlite3
from typing import Iterable

from monitoring_tool import config

DB_PATH = config.DB_PATH
logger = logging.getLogger(__name__)

SCHEMA_STATEMENTS = """
CREATE TABLE IF NOT EXISTS processes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tag_name TEXT NOT NULL UNIQUE,
    folder_path TEXT NOT NULL,
    check_uc4_file INTEGER NOT NULL DEFAULT 0,
    uc4_folder_path TEXT,
    scheduled_time TEXT,
    check_query TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS fatal_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tag_name TEXT NOT NULL,
    event_time TEXT NOT NULL DEFAULT (datetime('now')),
    description TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS notification_recipients (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS process_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tag_name TEXT NOT NULL,
    run_time TEXT NOT NULL DEFAULT (datetime('now')),
    status TEXT NOT NULL,
    reasons TEXT NOT NULL,
    uc4_status TEXT NOT NULL,
    check_type TEXT NOT NULL
);
"""


def get_connection() -> sqlite3.Connection:
    logger.debug("Opening database connection to %s", config.DB_PATH)
    connection = sqlite3.connect(str(config.DB_PATH))
    connection.row_factory = sqlite3.Row
    return connection


def init_db() -> None:
    logger.info("Initializing database schema from %s", config.SCHEMA_PATH)
    schema = config.SCHEMA_PATH.read_text(encoding="utf-8")
    with get_connection() as connection:
        connection.executescript(schema)


def query_all(query: str, params: Iterable | None = None) -> list[sqlite3.Row]:
    logger.debug("Executing query_all: %s | params=%s", query, params or [])
    with get_connection() as connection:
        cursor = connection.execute(query, params or [])
        return cursor.fetchall()


def execute(query: str, params: Iterable | None = None) -> None:
    logger.debug("Executing statement: %s | params=%s", query, params or [])
    with get_connection() as connection:
        connection.execute(query, params or [])
        connection.commit()


def ensure_schema() -> None:
    logger.info("Ensuring database schema and required columns")
    with get_connection() as connection:
        connection.executescript(SCHEMA_STATEMENTS)
        _ensure_column(connection, "processes", "uc4_folder_path", "TEXT")
        _ensure_column(connection, "processes", "scheduled_time", "TEXT")
        _ensure_column(connection, "processes", "check_query", "TEXT")


def _ensure_column(connection: sqlite3.Connection, table: str, column: str, definition: str) -> None:
    cursor = connection.execute(f"PRAGMA table_info({table})")
    columns = {row[1] for row in cursor.fetchall()}
    if column not in columns:
        logger.info("Adding missing column %s.%s", table, column)
        connection.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")
        connection.commit()
