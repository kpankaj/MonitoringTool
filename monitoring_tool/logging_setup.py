from __future__ import annotations

import logging
from pathlib import Path

from monitoring_tool import config


def configure_logging() -> None:
    """Configure application logging once for both console and file output."""
    root_logger = logging.getLogger()
    if root_logger.handlers:
        return

    log_path = Path(config.LOG_PATH)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    )

    file_handler = logging.FileHandler(log_path, encoding="utf-8")
    file_handler.setFormatter(formatter)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    root_logger.setLevel(config.LOG_LEVEL)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)

    logging.getLogger(__name__).info("Logging configured with file output at %s", log_path)
