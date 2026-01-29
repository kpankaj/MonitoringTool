from __future__ import annotations

import os
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
REPO_ROOT = BASE_DIR.parent

DB_PATH = Path(os.getenv("MONITORING_DB_PATH", REPO_ROOT / "monitoring_tool.db"))
SCHEMA_PATH = Path(os.getenv("MONITORING_SCHEMA_PATH", BASE_DIR / "scripts" / "schema.sql"))

SMTP_HOST = os.getenv("SMTP_HOST", "localhost")
SMTP_PORT = int(os.getenv("SMTP_PORT", "25"))
SMTP_SENDER = os.getenv("SMTP_SENDER", "monitoring@example.com")

FLASK_SECRET = os.getenv("FLASK_SECRET", "monitoring-tool-secret")
