import sqlite3
from pathlib import Path
from typing import Iterable


DB_PATH = '/Users/kpankaj_1/MonitoringTool/monitoring_tool.db'
SCHEMA_STATEMENTS = """
CREATE TABLE IF NOT EXISTS processes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tag_name TEXT NOT NULL UNIQUE,
    folder_path TEXT NOT NULL,
    check_uc4_file INTEGER NOT NULL DEFAULT 0,
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
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def init_db() -> None:
    schema = _load_schema()
    with get_connection() as connection:
        connection.executescript(schema)


def _load_schema() -> str:
    #schema_path = Path(__file__).resolve().parent.parent / "scripts" / "schema.sql"
    schema_path = "/Users/kpankaj_1/MonitoringTool/monitoring_tool/scripts/schema.sql"
    print(schema_path)
    return schema_path.read_text(encoding="utf-8")


def query_all(query: str, params: Iterable | None = None) -> list[sqlite3.Row]:
    with get_connection() as connection:
        cursor = connection.execute(query, params or [])
        return cursor.fetchall()


def execute(query: str, params: Iterable | None = None) -> None:
    with get_connection() as connection:
        connection.execute(query, params or [])
        connection.commit()


def ensure_schema() -> None:
    with get_connection() as connection:
        connection.executescript(SCHEMA_STATEMENTS)
        _ensure_column(connection, "processes", "scheduled_time", "TEXT")
        _ensure_column(connection, "processes", "check_query", "TEXT")


def _ensure_column(connection: sqlite3.Connection, table: str, column: str, definition: str) -> None:
    cursor = connection.execute(f"PRAGMA table_info({table})")
    columns = {row[1] for row in cursor.fetchall()}
    if column not in columns:
        connection.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")
        connection.commit()
