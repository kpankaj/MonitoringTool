from monitoring_tool import db
from monitoring_tool.services import filesystem_service


def list_fatal_events(tag_name: str) -> list[dict]:
    rows = db.query_all(
        "SELECT event_time, description FROM fatal_events WHERE tag_name = ? ORDER BY event_time DESC",
        [tag_name],
    )
    return [dict(row) for row in rows]


def list_failed_processes(processes: list[dict]) -> list[dict]:
    failed = []
    for process in processes:
        tag_name = process["tag_name"]
        fatal_events = list_fatal_events(tag_name)
        file_check = filesystem_service.evaluate_folder(process["folder_path"])

        reasons = []
        if fatal_events:
            reasons.append("Fatal event(s) recorded")
        if file_check.is_failed:
            reasons.append(file_check.reason or "Filesystem check failed")

        if reasons:
            failed.append(
                {
                    "tag_name": tag_name,
                    "folder_path": process["folder_path"],
                    "reasons": reasons,
                    "fatal_events": fatal_events,
                }
            )

    return failed
