from __future__ import annotations

import json

from monitoring_tool import db


def list_fatal_events(tag_name: str) -> list[dict]:
    rows = db.query_all(
        "SELECT event_time, description FROM fatal_events WHERE tag_name = ? ORDER BY event_time DESC",
        [tag_name],
    )
    return [dict(row) for row in rows]


def list_process_reports(processes: list[dict]) -> list[dict]:
    reports = []
    latest_runs = _list_latest_runs()

    for process in processes:
        tag_name = process["tag_name"]
        fatal_events = list_fatal_events(tag_name)
        run = latest_runs.get(tag_name)

        reasons = []
        if run:
            reasons.extend(run["reasons"])
        if fatal_events:
            reasons.append("Fatal event(s) recorded")

        if run:
            status = run["status"]
            status_class = run["status_class"]
            uc4_status = run["uc4_status"]
            last_run_time = run["run_time"]
        else:
            status = "Pending"
            status_class = "status-pending"
            uc4_status = "Not yet run"
            last_run_time = None

        if fatal_events and status != "Failed":
            status = "Failed"
            status_class = "status-failed"

        reports.append(
            {
                "tag_name": tag_name,
                "folder_path": process["folder_path"],
                "reasons": reasons,
                "fatal_events": fatal_events,
                "uc4_status": uc4_status,
                "status": status,
                "status_class": status_class,
                "last_run_time": last_run_time,
            }
        )

    return reports

def list_failed_processes(processes: list[dict]) -> list[dict]:
    reports = list_process_reports(processes)
    return [report for report in reports if report["status"] == "Failed"]


def record_run(
    tag_name: str,
    status: str,
    reasons: list[str],
    uc4_status: str,
    check_type: str,
    run_time: str | None = None,
) -> None:
    serialized_reasons = json.dumps(reasons)
    if run_time is None:
        db.execute(
            "INSERT INTO process_runs (tag_name, status, reasons, uc4_status, check_type) "
            "VALUES (?, ?, ?, ?, ?)",
            [tag_name, status, serialized_reasons, uc4_status, check_type],
        )
        return

    db.execute(
        "INSERT INTO process_runs (tag_name, run_time, status, reasons, uc4_status, check_type) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        [tag_name, run_time, status, serialized_reasons, uc4_status, check_type],
    )


def get_latest_run(tag_name: str) -> dict | None:
    rows = db.query_all(
        "SELECT id, tag_name, run_time, status, reasons, uc4_status, check_type "
        "FROM process_runs WHERE tag_name = ? ORDER BY run_time DESC, id DESC LIMIT 1",
        [tag_name],
    )
    if not rows:
        return None
    row = dict(rows[0])
    return _normalize_run(row)


def _list_latest_runs() -> dict[str, dict]:
    rows = db.query_all(
        "SELECT pr.id, pr.tag_name, pr.run_time, pr.status, pr.reasons, pr.uc4_status, pr.check_type "
        "FROM process_runs pr "
        "JOIN (SELECT tag_name, MAX(id) AS max_id FROM process_runs GROUP BY tag_name) latest "
        "ON pr.id = latest.max_id"
    )
    latest_runs = {}
    for row in rows:
        run = _normalize_run(dict(row))
        latest_runs[run["tag_name"]] = run
    return latest_runs


def _normalize_run(run: dict) -> dict:
    reasons = json.loads(run.get("reasons") or "[]")
    status = run.get("status", "Pending")
    status_class = "status-failed" if status == "Failed" else "status-success"
    return {
        "id": run["id"],
        "tag_name": run["tag_name"],
        "run_time": run.get("run_time"),
        "status": status,
        "status_class": status_class,
        "reasons": reasons,
        "uc4_status": run.get("uc4_status") or "Not available",
        "check_type": run.get("check_type"),
    }
