import tempfile
import unittest
from pathlib import Path

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

    def test_evaluate_folder_with_subdirectory_success(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            Path(tmp_dir, 'nested-dir').mkdir()
            result = filesystem_service.evaluate_folder(tmp_dir)

        self.assertFalse(result.is_failed)
        self.assertIsNone(result.reason)

    def test_evaluate_uc4_file_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            result = filesystem_service.evaluate_uc4_file(tmp_dir)

        self.assertTrue(result.is_failed)
        self.assertEqual(result.reason, 'Missing UC4 trigger file containing: _trigger_')

    def test_evaluate_uc4_file_with_matching_file_success(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            Path(tmp_dir, 'job_trigger_20240102.xml').write_text('ok')
            result = filesystem_service.evaluate_uc4_file(tmp_dir)

        self.assertFalse(result.is_failed)
        self.assertIsNone(result.reason)

    def test_evaluate_uc4_file_with_prefixed_matching_file_success(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            Path(tmp_dir, 'MAM_AI_612_trigger_20260317073719.xml').write_text('ok')
            result = filesystem_service.evaluate_uc4_file(tmp_dir)

        self.assertFalse(result.is_failed)
        self.assertIsNone(result.reason)

    def test_evaluate_uc4_file_with_previous_dated_timestamp_success(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            Path(tmp_dir, 'MAM_CI_935_trigger_20260602142515.xml').write_text('ok')
            result = filesystem_service.evaluate_uc4_file(tmp_dir)

        self.assertFalse(result.is_failed)
        self.assertIsNone(result.reason)


if __name__ == '__main__':
    unittest.main()
