import unittest
from datetime import datetime
from unittest.mock import patch

from monitoring_tool.services import filesystem_service, monitoring_service, query_service


class MonitoringServiceTests(unittest.TestCase):
    def test_scheduled_check_requires_query(self) -> None:
        process = {
            "tag_name": "job-a",
            "scheduled_time": "08:00",
            "check_query": "",
            "folder_path": "/tmp",
        }
        now = datetime(2024, 1, 1, 9, 0, 0)

        with patch(
            "monitoring_tool.services.monitoring_service.process_service.list_processes",
            return_value=[process],
        ), patch(
            "monitoring_tool.services.monitoring_service.report_service.record_run"
        ) as record_run:
            monitoring_service.run_monitoring_cycle(now=now)

        record_run.assert_called_once()
        args = record_run.call_args.kwargs
        self.assertEqual(args["tag_name"], "job-a")
        self.assertEqual(args["status"], "Failed")
        self.assertIn("Scheduled time set without a database query", args["reasons"])
        self.assertEqual(args["check_type"], "db_query")

    def test_scheduled_check_skips_before_time(self) -> None:
        process = {
            "tag_name": "job-b",
            "scheduled_time": "23:59",
            "check_query": "select 1",
            "folder_path": "/tmp",
        }
        now = datetime(2024, 1, 1, 10, 0, 0)

        with patch(
            "monitoring_tool.services.monitoring_service.process_service.list_processes",
            return_value=[process],
        ), patch(
            "monitoring_tool.services.monitoring_service.report_service.record_run"
        ) as record_run:
            monitoring_service.run_monitoring_cycle(now=now)

        record_run.assert_not_called()

    def test_scheduled_check_invalid_time_records_failure(self) -> None:
        process = {
            "tag_name": "job-c",
            "scheduled_time": "invalid",
            "check_query": "select 1",
            "folder_path": "/tmp",
        }
        now = datetime(2024, 1, 1, 10, 0, 0)

        with patch(
            "monitoring_tool.services.monitoring_service.process_service.list_processes",
            return_value=[process],
        ), patch(
            "monitoring_tool.services.monitoring_service.report_service.record_run"
        ) as record_run:
            monitoring_service.run_monitoring_cycle(now=now)

        record_run.assert_called_once()
        args = record_run.call_args.kwargs
        self.assertEqual(args["tag_name"], "job-c")
        self.assertEqual(args["status"], "Failed")
        self.assertIn("Invalid scheduled time format: invalid", args["reasons"])

    def test_scheduled_check_runs_once_per_day(self) -> None:
        process = {
            "tag_name": "job-d",
            "scheduled_time": "08:00",
            "check_query": "select 1",
            "folder_path": "/tmp",
        }
        now = datetime(2024, 1, 1, 9, 0, 0)
        latest_run = {"run_time": "2024-01-01 08:00:00"}

        with patch(
            "monitoring_tool.services.monitoring_service.process_service.list_processes",
            return_value=[process],
        ), patch(
            "monitoring_tool.services.monitoring_service.report_service.get_latest_run",
            return_value=latest_run,
        ), patch(
            "monitoring_tool.services.monitoring_service.report_service.record_run"
        ) as record_run:
            monitoring_service.run_monitoring_cycle(now=now)

        record_run.assert_not_called()

    def test_filesystem_check_with_missing_folder_skips_uc4(self) -> None:
        process = {
            "tag_name": "job-e",
            "folder_path": "/missing",
            "check_uc4_file": True,
        }
        now = datetime(2024, 1, 1, 9, 0, 0)
        file_result = filesystem_service.FileCheckResult(True, "Folder missing: /missing")

        with patch(
            "monitoring_tool.services.monitoring_service.process_service.list_processes",
            return_value=[process],
        ), patch(
            "monitoring_tool.services.monitoring_service.filesystem_service.evaluate_folder",
            return_value=file_result,
        ), patch(
            "monitoring_tool.services.monitoring_service.filesystem_service.evaluate_uc4_file"
        ) as evaluate_uc4_file, patch(
            "monitoring_tool.services.monitoring_service.report_service.record_run"
        ) as record_run:
            monitoring_service.run_monitoring_cycle(now=now)

        evaluate_uc4_file.assert_not_called()
        args = record_run.call_args.kwargs
        self.assertEqual(args["status"], "Failed")
        self.assertEqual(args["uc4_status"], "Folder missing")

    def test_filesystem_check_with_uc4_failure(self) -> None:
        process = {
            "tag_name": "job-f",
            "folder_path": "/tmp",
            "check_uc4_file": True,
        }
        now = datetime(2024, 1, 1, 9, 0, 0)
        folder_result = filesystem_service.FileCheckResult(False, None)
        uc4_result = filesystem_service.FileCheckResult(True, "Missing UC4 file: uc4.flag")

        with patch(
            "monitoring_tool.services.monitoring_service.process_service.list_processes",
            return_value=[process],
        ), patch(
            "monitoring_tool.services.monitoring_service.filesystem_service.evaluate_folder",
            return_value=folder_result,
        ), patch(
            "monitoring_tool.services.monitoring_service.filesystem_service.evaluate_uc4_file",
            return_value=uc4_result,
        ), patch(
            "monitoring_tool.services.monitoring_service.report_service.record_run"
        ) as record_run:
            monitoring_service.run_monitoring_cycle(now=now)

        args = record_run.call_args.kwargs
        self.assertEqual(args["status"], "Failed")
        self.assertIn("Missing UC4 file: uc4.flag", args["reasons"])
        self.assertEqual(args["uc4_status"], "Missing UC4 file: uc4.flag")

    def test_filesystem_check_success_without_uc4(self) -> None:
        process = {
            "tag_name": "job-g",
            "folder_path": "/tmp",
            "check_uc4_file": False,
        }
        now = datetime(2024, 1, 1, 9, 0, 0)
        folder_result = filesystem_service.FileCheckResult(False, None)

        with patch(
            "monitoring_tool.services.monitoring_service.process_service.list_processes",
            return_value=[process],
        ), patch(
            "monitoring_tool.services.monitoring_service.filesystem_service.evaluate_folder",
            return_value=folder_result,
        ), patch(
            "monitoring_tool.services.monitoring_service.report_service.record_run"
        ) as record_run:
            monitoring_service.run_monitoring_cycle(now=now)

        args = record_run.call_args.kwargs
        self.assertEqual(args["status"], "Success")
        self.assertEqual(args["uc4_status"], "Not enabled")


class QueryServiceTests(unittest.TestCase):
    def test_query_requires_select(self) -> None:
        result = query_service.evaluate_query("update table set value=1")
        self.assertTrue(result.is_failed)
        self.assertEqual(result.reason, "Only SELECT queries are supported")

    def test_query_missing(self) -> None:
        result = query_service.evaluate_query("   ")
        self.assertTrue(result.is_failed)
        self.assertEqual(result.reason, "Missing query for scheduled check")

    def test_query_error_propagates(self) -> None:
        with patch(
            "monitoring_tool.services.query_service.db.query_all",
            side_effect=RuntimeError("boom"),
        ):
            result = query_service.evaluate_query("select 1")

        self.assertTrue(result.is_failed)
        self.assertEqual(result.reason, "Query failed: boom")

    def test_query_no_rows_fails(self) -> None:
        with patch("monitoring_tool.services.query_service.db.query_all", return_value=[]):
            result = query_service.evaluate_query("select 1")

        self.assertTrue(result.is_failed)
        self.assertEqual(result.reason, "Query returned no rows")

    def test_query_with_rows_succeeds(self) -> None:
        with patch("monitoring_tool.services.query_service.db.query_all", return_value=[{"id": 1}]):
            result = query_service.evaluate_query("select 1")

        self.assertFalse(result.is_failed)
        self.assertIsNone(result.reason)


if __name__ == "__main__":
    unittest.main()
