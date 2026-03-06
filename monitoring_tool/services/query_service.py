from dataclasses import dataclass

from monitoring_tool import config, db


@dataclass(frozen=True)
class QueryCheckResult:
    is_failed: bool
    reason: str | None


def evaluate_query(query: str) -> QueryCheckResult:
    normalized = query.strip()
    if not normalized:
        return QueryCheckResult(True, "Missing query for scheduled check")

    if not normalized.lower().startswith("select"):
        return QueryCheckResult(True, "Only SELECT queries are supported")

    try:
        rows = _run_query(normalized)
    except Exception as exc:  # noqa: BLE001
        return QueryCheckResult(True, f"Query failed: {exc}")

    if not rows:
        return QueryCheckResult(True, "Query returned no rows")

    return QueryCheckResult(False, None)


def _run_query(query: str):
    if config.SQLSERVER_CONNECTION_STRING:
        return _query_sqlserver(query)

    return db.query_all(query)


def _query_sqlserver(query: str):
    import pyodbc

    with pyodbc.connect(
        config.SQLSERVER_CONNECTION_STRING,
        timeout=config.SQLSERVER_QUERY_TIMEOUT_SECONDS,
    ) as connection:
        cursor = connection.cursor()
        cursor.execute(query)
        return cursor.fetchmany(1)
