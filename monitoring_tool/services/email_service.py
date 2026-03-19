import logging
import smtplib
from email.message import EmailMessage
from typing import Iterable

logger = logging.getLogger(__name__)


def send_failure_email(
    smtp_host: str,
    smtp_port: int,
    sender: str,
    recipients: Iterable[str],
    subject: str,
    body: str,
    username: str | None = None,
    password: str | None = None,
    use_starttls: bool = False,
    use_ssl: bool = False,
    delivery_method: str = "smtp",
) -> None:
    recipients_list = list(recipients)
    logger.info(
        "Sending failure email to %s recipient(s) using %s delivery",
        len(recipients_list),
        delivery_method,
    )
    message = EmailMessage()
    message["From"] = sender
    message["To"] = ", ".join(recipients_list)
    message["Subject"] = subject
    message.set_content(body)

    if delivery_method == "outlook_desktop":
        _send_email_with_outlook_desktop(recipients_list, subject, body)
        return

    smtp_client = smtplib.SMTP_SSL if use_ssl else smtplib.SMTP
    with smtp_client(smtp_host, smtp_port) as smtp:
        if use_starttls and not use_ssl:
            smtp.starttls()
        if username and password:
            smtp.login(username, password)
        smtp.send_message(message)


def _send_email_with_outlook_desktop(recipients: list[str], subject: str, body: str) -> None:
    try:
        import win32com.client  # type: ignore[import-not-found]
    except ImportError as exc:
        raise RuntimeError(
            "Outlook desktop delivery requires pywin32 (win32com.client). "
            "Install with: pip install pywin32"
        ) from exc

    try:
        outlook = win32com.client.Dispatch("Outlook.Application")
        mail_item = outlook.CreateItem(0)
        mail_item.To = "; ".join(recipients)
        mail_item.Subject = subject
        mail_item.Body = body
        mail_item.Send()
    except Exception as exc:  # noqa: BLE001
        raise RuntimeError(f"Failed to send email with Outlook desktop: {exc}") from exc
