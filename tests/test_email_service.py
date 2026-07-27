import sys
import types
import unittest
from unittest.mock import MagicMock, patch

from monitoring_tool.services import email_service


class EmailServiceTests(unittest.TestCase):
    def test_send_failure_email_uses_smtp_by_default(self) -> None:
        with patch("monitoring_tool.services.email_service.smtplib.SMTP") as smtp_client:
            smtp_instance = smtp_client.return_value.__enter__.return_value
            email_service.send_failure_email(
                smtp_host="localhost",
                smtp_port=25,
                sender="monitor@example.com",
                recipients=["ops@example.com"],
                subject="subject",
                body="body",
            )

        smtp_client.assert_called_once_with("localhost", 25)
        smtp_instance.send_message.assert_called_once()

    def test_send_failure_email_adds_html_alternative(self) -> None:
        with patch("monitoring_tool.services.email_service.smtplib.SMTP") as smtp_client:
            smtp_instance = smtp_client.return_value.__enter__.return_value
            email_service.send_failure_email(
                smtp_host="localhost",
                smtp_port=25,
                sender="monitor@example.com",
                recipients=["ops@example.com"],
                subject="failure",
                body="Plain-text fallback",
                html_body="<strong>Failure</strong>",
            )

        message = smtp_instance.send_message.call_args.args[0]
        self.assertTrue(message.is_multipart())
        self.assertEqual(message.get_body(preferencelist=("html",)).get_content().strip(), "<strong>Failure</strong>")

    def test_send_failure_email_uses_outlook_desktop_when_configured(self) -> None:
        mail_item = MagicMock()
        dispatch_client = MagicMock()
        dispatch_client.CreateItem.return_value = mail_item
        fake_win32_client = types.SimpleNamespace(Dispatch=MagicMock(return_value=dispatch_client))
        fake_win32_module = types.SimpleNamespace(client=fake_win32_client)

        with patch.dict(sys.modules, {"win32com": fake_win32_module, "win32com.client": fake_win32_client}):
            email_service.send_failure_email(
                smtp_host="",
                smtp_port=0,
                sender="monitor@example.com",
                recipients=["ops@example.com", "dev@example.com"],
                subject="subject",
                body="body",
                delivery_method="outlook_desktop",
            )

        fake_win32_client.Dispatch.assert_called_once_with("Outlook.Application")
        dispatch_client.CreateItem.assert_called_once_with(0)
        self.assertEqual(mail_item.To, "ops@example.com; dev@example.com")
        self.assertEqual(mail_item.Subject, "subject")
        self.assertEqual(mail_item.Body, "body")
        mail_item.Send.assert_called_once_with()


if __name__ == "__main__":
    unittest.main()
