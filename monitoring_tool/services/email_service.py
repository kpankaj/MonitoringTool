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
) -> None:
    recipients_list = list(recipients)
    logger.info("Sending failure email to %s recipient(s) via %s:%s", len(recipients_list), smtp_host, smtp_port)
    message = EmailMessage()
    message["From"] = sender
    message["To"] = ", ".join(recipients_list)
    message["Subject"] = subject
    message.set_content(body)

    with smtplib.SMTP(smtp_host, smtp_port) as smtp:
        smtp.send_message(message)
