from __future__ import annotations

import logging
import threading
from datetime import datetime

from monitoring_tool.services import filesystem_service, process_service, query_service, report_service

logger = logging.getLogger(__name__)

_scheduler_thread: threading.Thread | None = None
_stop_event = threading.Event()


def start_scheduler(interval_seconds: int = 600) -> None:
    global _scheduler_thread
    if _scheduler_thread and _scheduler_thread.is_alive():
        logger.debug("Scheduler thread already running")
        return

    _scheduler_thread = threading.Thread(
        target=_run_scheduler, args=(interval_seconds,), daemon=True
    )
    _scheduler_thread.start()
    logger.info("Scheduler started with interval %s seconds", interval_seconds)


def _run_scheduler(interval_seconds: int) -> None:
    while not _stop_event.is_set():
        logger.debug("Running scheduled monitoring cycle")
        try:
            run_monitoring_cycle()
        except Exception:  # noqa: BLE001
            logger.exception("Monitoring scheduler cycle failed")
        _stop_event.wait(interval_seconds)


def run_monitoring_cycle(now: datetime | None = None, force_run: bool = False) -> None:
    logger.info("Starting monitoring cycle (force_run=%s)", force_run)
    current_time = now or datetime.now()
    processes = process_service.list_processes()
    for process in processes:
        tag_name = process.get("tag_name", "unknown")
        logger.debug("Evaluating process %s", tag_name)
        try:
            scheduled_time = (process.get("scheduled_time") or "").strip()
            check_query = (process.get("check_query") or "").strip()

            if scheduled_time and not _should_run_scheduled_check(tag_name, scheduled_time, current_time):
                logger.debug(
                    "Skipping process %s because scheduled time gate is not satisfied (scheduled_time=%s)",
                    tag_name,
                    scheduled_time,
                )
                continue

            should_run_query = bool(check_query)

            _run_filesystem_check(process, current_time, check_query if should_run_query else None)
        except Exception as exc:  # noqa: BLE001
            logger.exception("Monitoring cycle failed for %s", tag_name)
            report_service.record_fatal_event(tag_name, f"Unexpected monitoring error: {exc}")


def _run_filesystem_check(process: dict, current_time: datetime, check_query: str | None = None) -> None:
    logger.debug("Running filesystem check for %s", process["tag_name"])
    tag_name = process["tag_name"]
    file_check = filesystem_service.evaluate_folder(process["folder_path"])
    uc4_check_enabled = bool(process.get("check_uc4_file"))
    uc4_check = None
    uc4_folder_path = (process.get("uc4_folder_path") or process["folder_path"]).strip()
    base_folder_missing = (
        file_check.is_failed
        and file_check.reason
        and file_check.reason.startswith("Folder missing:")
    )
    uc4_folder_missing = False
    if uc4_check_enabled:
        if uc4_folder_path == process["folder_path"] and base_folder_missing:
            uc4_folder_missing = True
        else:
            uc4_check = filesystem_service.evaluate_uc4_file(uc4_folder_path)
            uc4_folder_missing = (
                uc4_check.is_failed
                and uc4_check.reason
                and uc4_check.reason.startswith("Folder missing:")
            )

    reasons = []
    if file_check.is_failed:
        reasons.append(file_check.reason or "Filesystem check failed")
    if uc4_check_enabled and uc4_check and uc4_check.is_failed:
        reasons.append(uc4_check.reason or "UC4 file check failed")

    if check_query:
        query_result = query_service.evaluate_query(check_query)
        if query_result.is_failed:
            reasons.append(query_result.reason or "Database query check failed")

    if not uc4_check_enabled:
        uc4_status = "Not enabled"
    elif uc4_folder_missing:
        uc4_status = "Folder missing"
    elif uc4_check and uc4_check.is_failed:
        uc4_status = uc4_check.reason or "Failed"
    else:
        uc4_status = "OK"

    status = "Failed" if reasons else "Success"
    logger.info("Recording run result for %s with status %s", tag_name, status)
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
        logger.warning("Invalid scheduled_time for tag %s: %s", tag_name, scheduled_time)
        return False

    if now.time() < scheduled:
        return False

    latest_run = report_service.get_latest_run(tag_name)
    if latest_run and latest_run.get("run_time"):
        last_run = datetime.fromisoformat(latest_run["run_time"])
        if last_run.date() == now.date():
            return False

    return True



def _format_run_time(current_time: datetime) -> str:
    return current_time.replace(microsecond=0).isoformat(sep=" ")
