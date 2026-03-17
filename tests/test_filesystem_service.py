import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

from monitoring_tool.services import filesystem_service


class FilesystemServiceTests(unittest.TestCase):
    def test_evaluate_folder_missing(self) -> None:
        result = filesystem_service.evaluate_folder('/definitely/missing/path')
        self.assertTrue(result.is_failed)
        self.assertIn('Folder missing:', result.reason or '')

    def test_evaluate_folder_empty_success(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            result = filesystem_service.evaluate_folder(tmp_dir)

        self.assertFalse(result.is_failed)
        self.assertIsNone(result.reason)

    def test_evaluate_folder_non_empty_failure(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            Path(tmp_dir, 'any-file.txt').write_text('data')
            result = filesystem_service.evaluate_folder(tmp_dir)

        self.assertTrue(result.is_failed)
        self.assertEqual(result.reason, 'Folder is not empty')

    def test_evaluate_uc4_file_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            mocked_now = datetime(2024, 1, 2, 9, 0, 0)
            with patch('monitoring_tool.services.filesystem_service.datetime') as mock_datetime:
                mock_datetime.now.return_value = mocked_now
                mock_datetime.strftime = datetime.strftime
                result = filesystem_service.evaluate_uc4_file(tmp_dir)

        self.assertTrue(result.is_failed)
        self.assertEqual(result.reason, 'Missing UC4 trigger file containing: _trigger_20240102')

    def test_evaluate_uc4_file_with_matching_file_success(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            Path(tmp_dir, 'job_trigger_20240102.xml').write_text('ok')
            mocked_now = datetime(2024, 1, 2, 9, 0, 0)
            with patch('monitoring_tool.services.filesystem_service.datetime') as mock_datetime:
                mock_datetime.now.return_value = mocked_now
                mock_datetime.strftime = datetime.strftime
                result = filesystem_service.evaluate_uc4_file(tmp_dir)

        self.assertFalse(result.is_failed)
        self.assertIsNone(result.reason)

    def test_evaluate_uc4_file_with_prefixed_matching_file_success(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            Path(tmp_dir, 'MAM_AI_612_trigger_20260317073719.xml').write_text('ok')
            mocked_now = datetime(2026, 3, 17, 9, 0, 0)
            with patch('monitoring_tool.services.filesystem_service.datetime') as mock_datetime:
                mock_datetime.now.return_value = mocked_now
                mock_datetime.strftime = datetime.strftime
                result = filesystem_service.evaluate_uc4_file(tmp_dir)

        self.assertFalse(result.is_failed)
        self.assertIsNone(result.reason)


if __name__ == '__main__':
    unittest.main()
