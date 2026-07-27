import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from monitoring_tool.services import email_template_service


class EmailTemplateServiceTests(unittest.TestCase):
    def test_lists_only_html_templates_and_renders_escaped_values(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            template_dir = Path(directory)
            (template_dir / "failure.html").write_text(
                "$interface_name|$folder_path|<ul>$failure_reasons</ul>|$run_summary",
                encoding="utf-8",
            )
            (template_dir / "notes.txt").write_text("ignore", encoding="utf-8")
            with patch.object(email_template_service.config, "EMAIL_TEMPLATE_DIR", template_dir):
                self.assertEqual(email_template_service.list_templates(), ["failure.html"])
                rendered = email_template_service.render_failure(
                    "failure.html",
                    {
                        "tag_name": "orders <prod>",
                        "folder_path": "/inbox?a=1&b=2",
                        "status": "Failed",
                        "reasons": ["bad <file>"],
                    },
                    "1 process failed",
                )

        self.assertIn("orders &lt;prod&gt;", rendered)
        self.assertIn("bad &lt;file&gt;", rendered)
        self.assertNotIn("bad <file>", rendered)

    def test_rejects_paths_outside_template_directory(self) -> None:
        with self.assertRaises(ValueError):
            email_template_service.render_failure("../secret.html", {}, "")


if __name__ == "__main__":
    unittest.main()
