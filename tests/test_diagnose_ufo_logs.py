import importlib.util
import pathlib
import tempfile
import unittest

SCRIPT = pathlib.Path(__file__).resolve().parents[1] / "scripts" / "diagnose_ufo_logs.py"
spec = importlib.util.spec_from_file_location("diagnose_ufo_logs", SCRIPT)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class DiagnosticsTests(unittest.TestCase):
    def test_detects_known_ufo_failures_without_returning_secrets(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = pathlib.Path(tmp)
            (folder / "agent.log").write_text(
                "UIA control collection failed: object of type 'NoneType' has no len()\n"
                "LLM response parsing failed: Expecting ',' delimiter: line 8\n"
                "AppLLMInteractionStrategy failed\n"
                "API_KEY=do-not-print-me\n",
                encoding="utf-8",
            )
            result = module.scan(folder)
            self.assertEqual(result["uia_empty"], 1)
            self.assertEqual(result["json_parse"], 1)
            self.assertEqual(result["app_llm_failed"], 1)
            self.assertNotIn("do-not-print-me", str(result))

    def test_ignores_non_text_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = pathlib.Path(tmp)
            (folder / "screen.png").write_bytes(b"Blocked CLI command")
            self.assertEqual(module.scan(folder)["blocked_launch"], 0)


if __name__ == "__main__":
    unittest.main()
