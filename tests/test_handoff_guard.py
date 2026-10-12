import tempfile
import unittest
from pathlib import Path

from smartautomation.handoff_guard import detect_uninitialized_ui_loop


class HandoffGuardTests(unittest.TestCase):
    def test_repeated_ui_error_detected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "response.log").write_text(
                ("UI state not initialized. Please select an application window first.\n" * 3),
                encoding="utf-8",
            )
            result = detect_uninitialized_ui_loop(root)
            self.assertTrue(result["detected"])
            self.assertEqual(result["reason_code"], "repeated_ui_state_not_initialized")
            self.assertEqual(result["occurrences"], 3)

    def test_one_failure_does_not_stop(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "response.log").write_text("UI state not initialized", encoding="utf-8")
            self.assertFalse(detect_uninitialized_ui_loop(root)["detected"])

    def test_missing_or_symlink_log_fails_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.assertFalse(detect_uninitialized_ui_loop(root)["detected"])

    def test_other_failures_are_not_ui_loop(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "response.log").write_text("WinError 2\n" * 10, encoding="utf-8")
            self.assertFalse(detect_uninitialized_ui_loop(root)["detected"])


if __name__ == "__main__":
    unittest.main()
