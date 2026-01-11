from monitoring_tool import db
from monitoring_tool.services import filesystem_service


def list_fatal_events(tag_name: str) -> list[dict]:
    rows = db.query_all(
        "SELECT event_time, description FROM fatal_events WHERE tag_name = ? ORDER BY event_time DESC",
        [tag_name],
    )
    return [dict(row) for row in rows]


def list_process_reports(processes: list[dict]) -> list[dict]:
    reports = []
    for process in processes:
        tag_name = process["tag_name"]
        fatal_events = list_fatal_events(tag_name)
        file_check = filesystem_service.evaluate_folder(process["folder_path"])
        uc4_check_enabled = bool(process.get("check_uc4_file"))
        uc4_check = None
        uc4_folder_missing = (
            file_check.is_failed
            and file_check.reason
            and file_check.reason.startswith("Folder missing:")
        )
        if uc4_check_enabled and not uc4_folder_missing:
            uc4_check = filesystem_service.evaluate_uc4_file(process["folder_path"])

        reasons = []
        if fatal_events:
            reasons.append("Fatal event(s) recorded")
        if file_check.is_failed:
            reasons.append(file_check.reason or "Filesystem check failed")
        if uc4_check_enabled and uc4_check and uc4_check.is_failed:
            reasons.append(uc4_check.reason or "UC4 file check failed")

        if not uc4_check_enabled:
            uc4_status = "Not enabled"
        elif uc4_folder_missing:
            uc4_status = "Folder missing"
        elif uc4_check and uc4_check.is_failed:
            uc4_status = uc4_check.reason or "Failed"
        else:
            uc4_status = "OK"
            
        is_failed = bool(reasons)
        reports.append(
            {
                "tag_name": tag_name,
                "folder_path": process["folder_path"],
                "reasons": reasons,
                "fatal_events": fatal_events,
                "uc4_status": uc4_status,
                "status": "Failed" if is_failed else "Success",
                "status_class": "status-failed" if is_failed else "status-success",
            }
        )

    return reports

def list_failed_processes(processes: list[dict]) -> list[dict]:
    reports = list_process_reports(processes)
    return [report for report in reports if report["status"] == "Failed"]
