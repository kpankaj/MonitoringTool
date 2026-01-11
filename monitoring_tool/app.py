from __future__ import annotations

import os

from flask import Flask, redirect, render_template, request, flash, url_for

from monitoring_tool import db
from monitoring_tool.services import email_service, process_service, report_service


def create_app() -> Flask:
    app = Flask(__name__)
    app.secret_key = os.getenv("FLASK_SECRET", "monitoring-tool-secret")

    @app.route("/")
    def index():
        return redirect(url_for("configure"))

    @app.route("/configure", methods=["GET", "POST"])
    def configure():
        if request.method == "POST":
            tag_name = request.form.get("tag_name", "").strip()
            folder_path = request.form.get("folder_path", "").strip()
            email = request.form.get("email", "").strip()

            if tag_name and folder_path:
                try:
                    process_service.add_process(tag_name, folder_path)
                    flash(f"Added process {tag_name}.", "success")
                except Exception as exc:  # noqa: BLE001
                    flash(f"Failed to add process: {exc}", "error")
            if email:
                process_service.add_recipient(email)
                flash(f"Added recipient {email}.", "success")

            return redirect(url_for("configure"))

        processes = process_service.list_processes()
        recipients = process_service.list_recipients()
        return render_template("configure.html", processes=processes, recipients=recipients)

    @app.route("/reports", methods=["GET", "POST"])
    def reports():
        processes = process_service.list_processes()
        failed = report_service.list_failed_processes(processes)

        if request.method == "POST":
            recipients = process_service.list_recipients()
            if not recipients:
                flash("No recipients configured.", "error")
                return redirect(url_for("reports"))

            smtp_host = os.getenv("SMTP_HOST", "localhost")
            smtp_port = int(os.getenv("SMTP_PORT", "25"))
            sender = os.getenv("SMTP_SENDER", "monitoring@example.com")
            subject = "MonitoringTool Failure Report"
            body = _format_failure_email(failed)

            try:
                email_service.send_failure_email(
                    smtp_host=smtp_host,
                    smtp_port=smtp_port,
                    sender=sender,
                    recipients=recipients,
                    subject=subject,
                    body=body,
                )
                flash("Notification email sent.", "success")
            except Exception as exc:  # noqa: BLE001
                flash(f"Failed to send email: {exc}", "error")

            return redirect(url_for("reports"))

        return render_template("reports.html", failed=failed)

    return app



def _format_failure_email(failed: list[dict]) -> str:
    if not failed:
        return "All monitored processes are healthy."

    lines = ["The following processes failed:"]
    for process in failed:
        lines.append(f"- {process['tag_name']} ({process['folder_path']}):")
        for reason in process["reasons"]:
            lines.append(f"  * {reason}")
    return "\n".join(lines)


if __name__ == "__main__":
    db.init_db()
    app = create_app()
    app.run(host="0.0.0.0", port=5000, debug=True)
