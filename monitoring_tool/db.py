import sqlite3
from pathlib import Path
from typing import Iterable


DB_PATH = '/Users/kpankaj_1/MonitoringTool/monitoring_tool.db'


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
