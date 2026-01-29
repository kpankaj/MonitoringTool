from dataclasses import dataclass

from monitoring_tool import db


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
        rows = db.query_all(normalized)
    except Exception as exc:  # noqa: BLE001
        return QueryCheckResult(True, f"Query failed: {exc}")

    if not rows:
        return QueryCheckResult(True, "Query returned no rows")

    return QueryCheckResult(False, None)
