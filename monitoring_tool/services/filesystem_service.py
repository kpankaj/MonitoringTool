from dataclasses import dataclass
from pathlib import Path


SUCCESS_MARKER = "success.flag"
FAILURE_MARKER = "failure.flag"
UC4_MARKER = "uc4.flag"


@dataclass(frozen=True)
class FileCheckResult:
    is_failed: bool
    reason: str | None


def evaluate_folder(folder_path: str) -> FileCheckResult:
    folder = Path(folder_path)
    if not folder.exists():
        return FileCheckResult(True, f"Folder missing: {folder_path}")

    failure_file = folder / FAILURE_MARKER
    if failure_file.exists():
        return FileCheckResult(True, f"Failure marker found: {failure_file.name}")

    success_file = folder / SUCCESS_MARKER
    if not success_file.exists():
        return FileCheckResult(True, f"Missing success marker: {success_file.name}")

    return FileCheckResult(False, None)

def evaluate_uc4_file(folder_path: str) -> FileCheckResult:
    folder = Path(folder_path)
    if not folder.exists():
        return FileCheckResult(True, f"Folder missing: {folder_path}")

    uc4_file = folder / UC4_MARKER
    if not uc4_file.exists():
        return FileCheckResult(True, f"Missing UC4 file: {uc4_file.name}")

    return FileCheckResult(False, None)

