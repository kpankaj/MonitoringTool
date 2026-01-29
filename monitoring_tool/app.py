from __future__ import annotations

from flask import Flask, redirect, render_template, request, flash, url_for, jsonify

from monitoring_tool import config, db
from monitoring_tool.services import email_service, monitoring_service, process_service, report_service


def create_app() -> Flask:
    app = Flask(__name__)
    app.secret_key = config.FLASK_SECRET
    db.ensure_schema()
    monitoring_service.start_scheduler()

    @app.route("/")
    def index():
        return redirect(url_for("reports"))

    @app.route("/recipients", methods=["GET", "POST"])
    def recipients():
        if request.method == "POST":
            email = request.form.get("email", "").strip()
            if email:
                process_service.add_recipient(email)
                flash(f"Added recipient {email}.", "success")
            return redirect(url_for("recipients"))

        recipients_list = process_service.list_recipients()
        return render_template("recipients.html", recipients=recipients_list)

    @app.route("/recipients/delete", methods=["POST"])
    def delete_recipient():
        email = request.form.get("email", "").strip()
        if email:
            process_service.remove_recipient(email)
            flash(f"Removed recipient {email}.", "success")
        return redirect(url_for("recipients"))
    
    @app.route("/configure", methods=["GET", "POST"])
    def configure():
        if request.method == "POST":
            tag_name = request.form.get("tag_name", "").strip()

            if tag_name:
                try:
                    process_service.add_tag(tag_name)
                    flash(f"Added tag {tag_name}.", "success")
                except Exception as exc:  # noqa: BLE001
                    flash(f"Failed to add tag: {exc}", "error")

            return redirect(url_for("configure"))

        tags = process_service.list_tags()
        return render_template("configure.html", tags=tags)

    @app.route("/folders", methods=["GET", "POST"])
    def folders():
        if request.method == "POST":
            tag_name = request.form.get("tag_name", "").strip()
            folder_path = request.form.get("folder_path", "").strip()
            check_uc4_file = request.form.get("check_uc4_file") == "on"
            scheduled_time = request.form.get("scheduled_time", "").strip()
            check_query = request.form.get("check_query", "").strip()
            existing_tags = set(process_service.list_tags())

            if not tag_name or not folder_path:
                flash("Tag name and folder path are required.", "error")
                return redirect(url_for("folders"))

            if tag_name not in existing_tags:
                flash(f"Unknown tag {tag_name}. Add it on the Configure page first.", "error")
                return redirect(url_for("folders"))

            if scheduled_time and not check_query:
                flash("A database query is required when scheduling a daily check time.", "error")
                return redirect(url_for("folders"))

            if check_query and not scheduled_time:
                flash("A daily check time is required when providing a database query.", "error")
                return redirect(url_for("folders"))

            process_service.set_folder(
                tag_name=tag_name,
                folder_path=folder_path,
                check_uc4_file=check_uc4_file,
                scheduled_time=scheduled_time or None,
                check_query=check_query or None,
            )
            flash(f"Saved folder for {tag_name}.", "success")
            return redirect(url_for("folders"))

        tags = process_service.list_tags()
        folders = process_service.list_folder_configs()
        return render_template("folders.html", tags=tags, folders=folders)


    @app.route("/configure/delete", methods=["POST"])
    def delete_tag():
        tag_name = request.form.get("tag_name", "").strip()
        if tag_name:
            process_service.remove_tag(tag_name)
            flash(f"Removed tag {tag_name}.", "success")
        return redirect(url_for("configure"))

    @app.route("/folders/delete", methods=["POST"])
    def delete_folder():
        tag_name = request.form.get("tag_name", "").strip()
        if tag_name:
            process_service.clear_folder(tag_name)
            flash(f"Removed folder for {tag_name}.", "success")
        return redirect(url_for("folders"))

    @app.route("/reports", methods=["GET"])
    def reports():
        processes = process_service.list_processes()
        report_rows = report_service.list_process_reports(processes)
        return render_template("reports.html", report_rows=report_rows)

    @app.route("/reports/errors", methods=["GET"])
    def report_errors():
        tag_name = request.args.get("tag_name", "").strip()
        if not tag_name:
            return jsonify({"error": "tag_name is required"}), 400

        fatal_events = report_service.list_fatal_events(tag_name)
        return jsonify({"tag_name": tag_name, "fatal_events": fatal_events})

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
    app.run(host="0.0.0.0", port=5000, debug=True)
