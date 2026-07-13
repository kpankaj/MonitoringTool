import logging
from dataclasses import dataclass
from datetime import date, timedelta

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




def _format_query_with_params(query: str, params: list) -> str:
    formatted_query = query
    for param in params:
        if isinstance(param, str):
            rendered_param = "'" + param.replace("'", "''") + "'"
        else:
            rendered_param = str(param)
        formatted_query = formatted_query.replace("?", rendered_param, 1)
    return formatted_query


def _fetch_all_rows(cursor) -> tuple[list[str], list]:
    """Fetch rows from the current and any subsequent result sets.

    Some SQL Server connections can surface an initial empty result set
    (for example from intermediate statements/triggers) before the
    expected SELECT result set. This helper walks through available
    result sets and accumulates rows from any set that has columns.
    """
    columns: list[str] = []
    rows = []

    while True:
        if cursor.description:
            if not columns:
                columns = [column[0] for column in cursor.description]
            rows.extend(cursor.fetchall())

        if not cursor.nextset():
            break

    return columns, rows


def list_log_event_details(
    tag_name: str | None = None,
    severity: str | None = None,
    period_from: date | None = None,
    period_to: date | None = None,
) -> list[dict]:
    logger.debug(
        "Fetching log event details for tag=%s severity=%s period_from=%s period_to=%s",
        tag_name,
        severity,
        period_from,
        period_to,
    )
    if not config.SQLSERVER_CONNECTION_STRING:
        raise RuntimeError("SQL Server connection is not configured.")

    import pyodbc

    period_from = period_from or date.today()
    period_to = period_to or period_from
    period_to_exclusive = period_to + timedelta(days=1)

    query = [
        "SELECT Tag AS tag, LogTimestamp AS log_timestamp, Severity AS severity, "
        "EventData AS event_data, [Exception] AS exception_text "
        "FROM LogEventDetails "
        "WHERE LogTimestamp >= ? AND LogTimestamp < ? "
    ]
    params: list[str | date] = [period_from, period_to_exclusive]

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
        logger.debug("Executing LogEventDetails query: %s", _format_query_with_params(final_query, params))
        # pyodbc expects each positional parameter as its own argument.
        # Passing the list directly can bind it as a single value, which
        # causes filters to behave incorrectly and may return zero rows.
        cursor.execute(final_query, *params)
        columns, rows = _fetch_all_rows(cursor)
        logger.debug("LogEventDetails query returned %d row(s)", len(rows))
        return [dict(zip(columns, row)) for row in rows]
