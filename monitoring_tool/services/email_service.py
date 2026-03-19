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
) -> None:
    recipients_list = list(recipients)
    logger.info("Sending failure email to %s recipient(s) via %s:%s", len(recipients_list), smtp_host, smtp_port)
    message = EmailMessage()
    message["From"] = sender
    message["To"] = ", ".join(recipients_list)
    message["Subject"] = subject
    message.set_content(body)

    smtp_client = smtplib.SMTP_SSL if use_ssl else smtplib.SMTP
    with smtp_client(smtp_host, smtp_port) as smtp:
        if use_starttls and not use_ssl:
            smtp.starttls()
        if username and password:
            smtp.login(username, password)
        smtp.send_message(message)
