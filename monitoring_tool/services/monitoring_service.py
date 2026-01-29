from __future__ import annotations

import threading
from datetime import datetime

from monitoring_tool.services import filesystem_service, process_service, query_service, report_service

_scheduler_thread: threading.Thread | None = None
_stop_event = threading.Event()


def start_scheduler(interval_seconds: int = 600) -> None:
    global _scheduler_thread
    if _scheduler_thread and _scheduler_thread.is_alive():
        return

    _scheduler_thread = threading.Thread(
        target=_run_scheduler, args=(interval_seconds,), daemon=True
    )
    _scheduler_thread.start()


def _run_scheduler(interval_seconds: int) -> None:
    while not _stop_event.is_set():
        run_monitoring_cycle()
        _stop_event.wait(interval_seconds)


def run_monitoring_cycle(now: datetime | None = None) -> None:
    current_time = now or datetime.now()
    processes = process_service.list_processes()
    for process in processes:
        tag_name = process["tag_name"]
        scheduled_time = (process.get("scheduled_time") or "").strip()
        check_query = (process.get("check_query") or "").strip()

        if scheduled_time:
            if not check_query:
                _record_failed_run(
                    tag_name,
                    ["Scheduled time set without a database query"],
                    check_type="db_query",
                    run_time=current_time,
                )
                continue

            if not _should_run_scheduled_check(tag_name, scheduled_time, current_time):
                continue

            query_result = query_service.evaluate_query(check_query)
            reasons = []
            if query_result.is_failed:
                reasons.append(query_result.reason or "Database query check failed")
            status = "Failed" if reasons else "Success"
            report_service.record_run(
                tag_name=tag_name,
                status=status,
                reasons=reasons,
                uc4_status="Not applicable",
                check_type="db_query",
                run_time=_format_run_time(current_time),
            )
            continue

        _run_filesystem_check(process, current_time)


def _run_filesystem_check(process: dict, current_time: datetime) -> None:
    tag_name = process["tag_name"]
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

    status = "Failed" if reasons else "Success"
    report_service.record_run(
        tag_name=tag_name,
        status=status,
        reasons=reasons,
        uc4_status=uc4_status,
        check_type="filesystem",
        run_time=_format_run_time(current_time),
    )


def _should_run_scheduled_check(tag_name: str, scheduled_time: str, now: datetime) -> bool:
    try:
        scheduled = datetime.strptime(scheduled_time, "%H:%M").time()
    except ValueError:
        _record_failed_run(
            tag_name,
            [f"Invalid scheduled time format: {scheduled_time}"],
            check_type="db_query",
            run_time=now,
        )
        return False

    if now.time() < scheduled:
        return False

    latest_run = report_service.get_latest_run(tag_name)
    if latest_run and latest_run.get("run_time"):
        last_run = datetime.fromisoformat(latest_run["run_time"])
        if last_run.date() == now.date():
            return False

    return True


def _record_failed_run(
    tag_name: str, reasons: list[str], check_type: str, run_time: datetime
) -> None:
    report_service.record_run(
        tag_name=tag_name,
        status="Failed",
        reasons=reasons,
        uc4_status="Not applicable",
        check_type=check_type,
        run_time=_format_run_time(run_time),
    )


def _format_run_time(current_time: datetime) -> str:
    return current_time.replace(microsecond=0).isoformat(sep=" ")
