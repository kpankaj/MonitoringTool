from __future__ import annotations

import html
from pathlib import Path
from string import Template

from monitoring_tool import config


def list_templates() -> list[str]:
    """Return HTML templates available to the folder configuration UI."""
    template_dir = config.EMAIL_TEMPLATE_DIR
    if not template_dir.is_dir():
        return []
    return sorted(path.name for path in template_dir.glob("*.html") if path.is_file())


def render_failure(template_name: str, report_row: dict, run_summary: str) -> str:
    """Render a configured failure template using escaped interface values."""
    template_path = _resolve_template(template_name)
    reasons = report_row.get("reasons") or ["An unspecified check failed."]
    reason_items = "".join(f"<li>{html.escape(str(reason))}</li>" for reason in reasons)
    values = {
        "interface_name": html.escape(str(report_row.get("tag_name", "Unknown"))),
        "status": html.escape(str(report_row.get("status", "Failed"))),
        "folder_path": html.escape(str(report_row.get("folder_path", ""))),
        "failure_reasons": reason_items,
        "run_summary": html.escape(run_summary),
    }
    return Template(template_path.read_text(encoding="utf-8")).safe_substitute(values)


def _resolve_template(template_name: str) -> Path:
    if not template_name or Path(template_name).name != template_name:
        raise ValueError("Invalid email template name")
    template_path = config.EMAIL_TEMPLATE_DIR / template_name
    if template_path.suffix.lower() != ".html" or not template_path.is_file():
        raise ValueError(f"Email template not found: {template_name}")
    return template_path
