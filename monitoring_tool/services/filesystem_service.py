import logging
from dataclasses import dataclass
from pathlib import Path


logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class FileCheckResult:
    is_failed: bool
    reason: str | None


def evaluate_folder(folder_path: str) -> FileCheckResult:
    logger.debug("Checking folder path %s", folder_path)
    folder = Path(folder_path)
    if not folder.exists():
        return FileCheckResult(True, f"Folder missing: {folder_path}")

    if any(child.is_file() for child in folder.iterdir()):
        return FileCheckResult(True, "Folder is not empty")

    return FileCheckResult(False, None)


def evaluate_uc4_file(folder_path: str) -> FileCheckResult:
    logger.debug("Checking UC4 file in folder %s", folder_path)
    folder = Path(folder_path)
    if not folder.exists():
        return FileCheckResult(True, f"Folder missing: {folder_path}")

    expected_pattern = "_trigger_"
    has_expected_file = any(
        child.is_file()
        and child.suffix.lower() == ".xml"
        and expected_pattern in child.stem
        for child in folder.iterdir()
    )
    if not has_expected_file:
        return FileCheckResult(True, f"Missing UC4 trigger file containing: {expected_pattern}")

    return FileCheckResult(False, None)
