from __future__ import annotations

import logging

from flask import Flask, redirect, render_template, request, flash, url_for, jsonify
from werkzeug.exceptions import HTTPException

from monitoring_tool import config, db
from monitoring_tool.logging_setup import configure_logging
from monitoring_tool.services import email_service, monitoring_service, process_service, report_service


logger = logging.getLogger(__name__)


def _render_error_page(message: str, status_code: int = 500):
    return render_template("error.html", message=message), status_code


def _register_error_handlers(app: Flask) -> None:
    @app.errorhandler(HTTPException)
    def handle_http_exception(exc: HTTPException):
        logger.exception("HTTP error encountered: %s", exc)
        return _render_error_page(exc.description or "An unexpected error occurred.", status_code=exc.code or 500)

    @app.errorhandler(Exception)
    def handle_unexpected_exception(exc: Exception):
        logger.exception("Unhandled exception encountered")
        return _render_error_page("An unexpected error occurred. Please contact support.", status_code=500)


def create_app() -> Flask:
    configure_logging()
    logger.info("Creating Flask application")
    app = Flask(__name__)
    app.secret_key = config.FLASK_SECRET
    db.ensure_schema()
    logger.info("Database schema ensured")
    monitoring_service.start_scheduler()
    logger.info("Monitoring scheduler started")

    _register_error_handlers(app)

    @app.route("/")
    def index():
        logger.debug("Index route accessed; redirecting to reports")
        return redirect(url_for("reports"))

    @app.route("/recipients", methods=["GET", "POST"])
    def recipients():
        if request.method == "POST":
            email = request.form.get("email", "").strip()
            if email:
                logger.info("Adding recipient %s", email)
                process_service.add_recipient(email)
                flash(f"Added recipient {email}.", "success")
            return redirect(url_for("recipients"))

        recipients_list = process_service.list_recipients()
        return render_template("recipients.html", recipients=recipients_list)

    @app.route("/recipients/delete", methods=["POST"])
    def delete_recipient():
        email = request.form.get("email", "").strip()
        if email:
            logger.info("Removing recipient %s", email)
            process_service.remove_recipient(email)
            flash(f"Removed recipient {email}.", "success")
        return redirect(url_for("recipients"))
    
    @app.route("/configure", methods=["GET", "POST"])
    def configure():
        if request.method == "POST":
            tag_name = request.form.get("tag_name", "").strip()

            if tag_name:
                try:
                    logger.info("Adding tag %s", tag_name)
                    process_service.add_tag(tag_name)
                    flash(f"Added tag {tag_name}.", "success")
                except Exception as exc:  # noqa: BLE001
                    logger.exception("Failed to add tag %s", tag_name)
                    flash(f"Failed to add tag: {exc}", "error")

            return redirect(url_for("configure"))

        tags = process_service.list_tags()
        return render_template("configure.html", tags=tags)

    @app.route("/folders", methods=["GET", "POST"])
    def folders():
        if request.method == "POST":
            editing_tag = request.form.get("editing_tag", "").strip()
            tag_name = request.form.get("tag_name", "").strip()
            folder_path = request.form.get("folder_path", "").strip()
            check_uc4_file = request.form.get("check_uc4_file") == "on"
            uc4_folder_path = request.form.get("uc4_folder_path", "").strip()
            scheduled_time = request.form.get("scheduled_time", "").strip()
            check_query = request.form.get("check_query", "").strip()
            existing_tags = set(process_service.list_tags())

            if not tag_name or not folder_path:
                flash("Tag name and folder path are required.", "error")
                return redirect(url_for("folders"))

            if tag_name not in existing_tags:
                flash(f"Unknown tag {tag_name}. Add it on the Configure page first.", "error")
                return redirect(url_for("folders"))

            if check_uc4_file and not uc4_folder_path:
                flash("UC4 folder path is required when UC4 check is enabled.", "error")
                return redirect(url_for("folders"))

            logger.info("Saving folder config for tag %s", tag_name)
            process_service.set_folder(
                tag_name=tag_name,
                folder_path=folder_path,
                check_uc4_file=check_uc4_file,
                uc4_folder_path=uc4_folder_path or None,
                scheduled_time=scheduled_time or None,
                check_query=check_query or None,
            )
            message_prefix = "Updated" if editing_tag else "Saved"
            flash(f"{message_prefix} folder for {tag_name}.", "success")
            return redirect(url_for("folders"))

        tags = process_service.list_tags()
        folders = process_service.list_folder_configs()
        edit_tag = request.args.get("edit_tag", "").strip()
        edit_folder = next((folder for folder in folders if folder["tag_name"] == edit_tag), None)
        return render_template("folders.html", tags=tags, folders=folders, edit_folder=edit_folder)


    @app.route("/configure/delete", methods=["POST"])
    def delete_tag():
        tag_name = request.form.get("tag_name", "").strip()
        if tag_name:
            logger.info("Removing tag %s", tag_name)
            process_service.remove_tag(tag_name)
            flash(f"Removed tag {tag_name}.", "success")
        return redirect(url_for("configure"))

    @app.route("/folders/delete", methods=["POST"])
    def delete_folder():
        tag_name = request.form.get("tag_name", "").strip()
        if tag_name:
            logger.info("Clearing folder config for tag %s", tag_name)
            process_service.clear_folder(tag_name)
            flash(f"Removed folder for {tag_name}.", "success")
        return redirect(url_for("folders"))

    @app.route("/reports", methods=["GET"])
    def reports():
        processes = process_service.list_processes()
        report_rows = report_service.list_process_reports(processes)
        return render_template("reports.html", report_rows=report_rows)

    @app.route("/reports/run-checks", methods=["POST"])
    def run_all_checks():
        logger.info("Manual run checks requested")
        monitoring_service.run_monitoring_cycle(force_run=True)
        success_message = "All configured process checks completed. Report refreshed with latest statuses."

        expects_json = (
            request.headers.get("X-Requested-With") == "XMLHttpRequest"
            or request.accept_mimetypes.best == "application/json"
        )
        if expects_json:
            processes = process_service.list_processes()
            report_rows = report_service.list_process_reports(processes)
            return jsonify({"message": success_message, "report_rows": report_rows})

        flash(success_message, "success")
        return redirect(url_for("reports"))

    @app.route("/reports/errors", methods=["GET"])
    def report_errors():
        tag_name = request.args.get("tag_name", "").strip()
        if not tag_name:
            return jsonify({"error": "tag_name is required"}), 400

        logger.debug("Fetching fatal events for %s", tag_name)
        fatal_events = report_service.list_fatal_events(tag_name)
        return jsonify({"tag_name": tag_name, "fatal_events": fatal_events})

    @app.route("/reports/interface", methods=["GET"])
    def interface_failure():
        tag_name = request.args.get("tag_name", "").strip()
        if not tag_name:
            flash("Select a failed interface to view its details.", "error")
            return redirect(url_for("reports"))

        logger.debug("Fetching fatal events for %s", tag_name)
        fatal_events = report_service.list_fatal_events(tag_name)
        return render_template(
            "interface_failure.html",
            tag_name=tag_name,
            fatal_events=fatal_events,
        )

    @app.route("/reports/notify", methods=["GET", "POST"])
    def notify_report():
        processes = process_service.list_processes()
        report_rows = report_service.list_process_reports(processes)
        failed = [row for row in report_rows if row["status"] == "Failed"]
        recipients_list = process_service.list_recipients()
        selected_recipients = recipients_list
        message = ""
        
        if request.method == "POST":
            selected_recipients = request.form.getlist("recipients")
            message = request.form.get("message", "").strip()

            if not recipients_list:
                flash("No recipients configured.", "error")
                return redirect(url_for("reports"))
                return redirect(url_for("notify_report"))

            if not selected_recipients:
                flash("Select at least one recipient.", "error")
                return render_template(
                    "notify_report.html",
                    recipients=recipients_list,
                    selected_recipients=selected_recipients,
                    message=message,
                )

            if not message:
                flash("Message is required.", "error")
                return render_template(
                    "notify_report.html",
                    recipients=recipients_list,
                    selected_recipients=selected_recipients,
                    message=message,
                )
            
            smtp_host = config.SMTP_HOST
            smtp_port = config.SMTP_PORT
            sender = config.SMTP_SENDER
            subject = "MonitoringTool Failure Report"
            body = f"{message}\n\n{_format_failure_email(failed)}"

            try:
                logger.info("Sending notification email to %s recipient(s)", len(selected_recipients))
                email_service.send_failure_email(
                    smtp_host=smtp_host,
                    smtp_port=smtp_port,
                    sender=sender,
                    recipients=selected_recipients,
                    subject=subject,
                    body=body,
                )
                flash("Notification email sent.", "success")
                return redirect(url_for("reports"))
            except Exception as exc:  # noqa: BLE001
                logger.exception("Failed to send notification email")
                flash(f"Failed to send email: {exc}", "error")


        return render_template(
            "notify_report.html",
            recipients=recipients_list,
            selected_recipients=selected_recipients,
            message=message,
        )

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
    #db.init_db()
    app = create_app()
    logger.info("Starting Flask development server")
    app.run(host="0.0.0.0", port=5000, debug=True)
