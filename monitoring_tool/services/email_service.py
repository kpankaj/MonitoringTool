import smtplib
from email.message import EmailMessage
from typing import Iterable


def send_failure_email(
    smtp_host: str,
    smtp_port: int,
    sender: str,
    recipients: Iterable[str],
    subject: str,
    body: str,
) -> None:
    message = EmailMessage()
    message["From"] = sender
    message["To"] = ", ".join(recipients)
    message["Subject"] = subject
    message.set_content(body)

    with smtplib.SMTP(smtp_host, smtp_port) as smtp:
        smtp.send_message(message)
