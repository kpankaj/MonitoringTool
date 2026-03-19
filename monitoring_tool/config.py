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
SMTP_USERNAME = os.getenv("SMTP_USERNAME", "").strip()
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "").strip()
SMTP_USE_STARTTLS = os.getenv("SMTP_USE_STARTTLS", "false").strip().lower() in {"1", "true", "yes", "on"}
SMTP_USE_SSL = os.getenv("SMTP_USE_SSL", "false").strip().lower() in {"1", "true", "yes", "on"}

# Outlook defaults (optional convenience mode)
OUTLOOK_SMTP_ENABLED = os.getenv("OUTLOOK_SMTP_ENABLED", "false").strip().lower() in {"1", "true", "yes", "on"}
OUTLOOK_SMTP_HOST = os.getenv("OUTLOOK_SMTP_HOST", "smtp.office365.com")
OUTLOOK_SMTP_PORT = int(os.getenv("OUTLOOK_SMTP_PORT", "587"))

FLASK_SECRET = os.getenv("FLASK_SECRET", "monitoring-tool-secret")

# Optional SQL Server connection used by scheduled check queries.
# Example:
# DRIVER={ODBC Driver 18 for SQL Server};SERVER=tcp:sql-host,1433;DATABASE=Monitoring;UID=user;PWD=pass;Encrypt=yes;TrustServerCertificate=yes
SQLSERVER_CONNECTION_STRING = os.getenv("MONITORING_SQLSERVER_CONNECTION_STRING", "").strip()
SQLSERVER_QUERY_TIMEOUT_SECONDS = int(os.getenv("MONITORING_SQLSERVER_QUERY_TIMEOUT_SECONDS", "30"))

LOG_PATH = Path(os.getenv("MONITORING_LOG_PATH", Path.cwd() / "monitoring_tool.log"))
LOG_LEVEL = os.getenv("MONITORING_LOG_LEVEL", "INFO").upper()
