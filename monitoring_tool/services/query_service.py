import logging
from dataclasses import dataclass

from monitoring_tool import config, db

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class QueryCheckResult:
    is_failed: bool
    reason: str | None


def evaluate_query(query: str) -> QueryCheckResult:
    logger.debug("Evaluating query health check")
    normalized = query.strip()
    if not normalized:
        return QueryCheckResult(True, "Missing query for scheduled check")

    if not normalized.lower().startswith("select"):
        return QueryCheckResult(True, "Only SELECT queries are supported")

    try:
        rows = _run_query(normalized)
    except Exception as exc:  # noqa: BLE001
        logger.exception("Query execution failed")
        return QueryCheckResult(True, f"Query failed: {exc}")

    if not rows:
        return QueryCheckResult(True, "Query returned no rows")

    return QueryCheckResult(False, None)


def _run_query(query: str):
    logger.debug("Running query using %s", "SQL Server" if config.SQLSERVER_CONNECTION_STRING else "SQLite")
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




def _format_query_with_params(query: str, params: list[str]) -> str:
    formatted_query = query
    for param in params:
        if isinstance(param, str):
            rendered_param = "'" + param.replace("'", "''") + "'"
        else:
            rendered_param = str(param)
        formatted_query = formatted_query.replace("?", rendered_param, 1)
    return formatted_query

def list_log_event_details(tag_name: str | None = None, severity: str | None = None) -> list[dict]:
    logger.debug("Fetching log event details for tag=%s severity=%s", tag_name, severity)
    print(f"[DEBUG] list_log_event_details called with tag_name={tag_name!r}, severity={severity!r}")
    if not config.SQLSERVER_CONNECTION_STRING:
        raise RuntimeError("SQL Server connection is not configured.")

    import pyodbc

    query = [
        "SELECT Tag AS tag, LogTimestamp AS log_timestamp, Severity AS severity, "
        "EventData AS event_data, [Exception] AS exception_text "
        "FROM LogEventDetails "
        "WHERE LogTimestamp >= CAST(GETDATE() AS date) "
    ]
    params: list[str] = []

    if severity:
        query.append("AND UPPER(Severity) = ? ")
        params.append(severity.strip().upper())

    if tag_name:
        query.append("AND UPPER(Tag) = ? ")
        params.append(tag_name.strip().upper())

    query.append(
        "ORDER BY LogTimestamp DESC"
    )

    with pyodbc.connect(
        config.SQLSERVER_CONNECTION_STRING,
        timeout=config.SQLSERVER_QUERY_TIMEOUT_SECONDS,
    ) as connection:
        cursor = connection.cursor()
        final_query = "".join(query)
        print(f"[DEBUG] Executing LogEventDetails query: {_format_query_with_params(final_query, params)}")
        # pyodbc expects each positional parameter as its own argument.
        # Passing the list directly can bind it as a single value, which
        # causes filters to behave incorrectly and may return zero rows.
        cursor.execute(final_query, *params)
        columns = [column[0] for column in cursor.description]
        rows = cursor.fetchall()
        print(f"[DEBUG] SQL returned {len(rows)} row(s) with columns={columns}")
        if rows:
            print(f"[DEBUG] First row preview: {dict(zip(columns, rows[0]))}")
        return [dict(zip(columns, row)) for row in rows]
