import unittest
from smartautomation.export_diagnostics import redact


class ExportTests(unittest.TestCase):
    def test_redacts_credentials_but_preserves_debug_context(self):
        sample = 'API_KEY: "secret123"\nAuthorization: Bearer abc123\nAction: click Word\n'
        cleaned = redact(sample)
        self.assertNotIn("secret123", cleaned)
        self.assertNotIn("abc123", cleaned)
        self.assertIn("Action: click Word", cleaned)

    def test_preserves_non_sensitive_model_trace(self):
        sample = '{"agent":"HostAgent","action":"select_application_window"}'
        self.assertEqual(redact(sample), sample)


if __name__ == "__main__":
    unittest.main()
