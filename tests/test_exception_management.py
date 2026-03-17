import unittest
from datetime import datetime
from unittest.mock import patch

from monitoring_tool.app import create_app
from monitoring_tool.services import monitoring_service


class AppExceptionManagementTests(unittest.TestCase):
    def test_unhandled_exception_renders_error_page(self) -> None:
        with patch('monitoring_tool.app.monitoring_service.start_scheduler'):
            app = create_app()

        @app.route('/boom')
        def boom():
            raise RuntimeError('unexpected')

        client = app.test_client()
        response = client.get('/boom')

        self.assertEqual(response.status_code, 500)
        self.assertIn(b'An unexpected error occurred. Please contact support.', response.data)


class MonitoringExceptionManagementTests(unittest.TestCase):
    def test_monitoring_cycle_records_fatal_event_when_process_fails(self) -> None:
        process = {
            'tag_name': 'job-exception',
            'folder_path': '/tmp',
            'check_uc4_file': False,
            'check_query': '',
        }
        now = datetime(2024, 1, 1, 9, 0, 0)

        with patch(
            'monitoring_tool.services.monitoring_service.process_service.list_processes',
            return_value=[process],
        ), patch(
            'monitoring_tool.services.monitoring_service._run_filesystem_check',
            side_effect=RuntimeError('disk issue'),
        ), patch(
            'monitoring_tool.services.monitoring_service.report_service.record_fatal_event',
        ) as record_fatal_event:
            monitoring_service.run_monitoring_cycle(now=now)

        record_fatal_event.assert_called_once()
        args = record_fatal_event.call_args.args
        self.assertEqual(args[0], 'job-exception')
        self.assertIn('disk issue', args[1])


class ReportsRouteTests(unittest.TestCase):
    def test_run_all_checks_returns_json_for_ajax_request(self) -> None:
        with patch('monitoring_tool.app.monitoring_service.start_scheduler'):
            app = create_app()

        client = app.test_client()
        with patch('monitoring_tool.app.monitoring_service.run_monitoring_cycle') as run_cycle, patch(
            'monitoring_tool.app.process_service.list_processes',
            return_value=[{'tag_name': 'job-1'}],
        ), patch(
            'monitoring_tool.app.report_service.list_process_reports',
            return_value=[
                {
                    'tag_name': 'job-1',
                    'folder_path': '/tmp',
                    'reasons': [],
                    'fatal_events': [],
                    'uc4_status': 'Not enabled',
                    'status': 'Success',
                    'status_class': 'status-success',
                }
            ],
        ):
            response = client.post(
                '/reports/run-checks',
                headers={'X-Requested-With': 'XMLHttpRequest', 'Accept': 'application/json'},
            )

        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertEqual(payload['message'], 'All configured process checks completed. Report refreshed with latest statuses.')
        self.assertEqual(payload['report_rows'][0]['tag_name'], 'job-1')
        run_cycle.assert_called_once_with(force_run=True)


if __name__ == '__main__':
    unittest.main()
