import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from smartautomation.ufo import UfoConfig, build_command, launch

class UfoFoundationTests(unittest.TestCase):
    def test_missing_source_is_detected(self):
        with tempfile.TemporaryDirectory() as temp:
            self.assertTrue(UfoConfig(Path(temp)).validate())

    def test_build_command_uses_upstream_ufo_not_legacy_automation(self):
        cfg = UfoConfig(Path("C:/UFO"), "python")
        cmd = build_command(cfg, "demo", "Open Notepad")
        self.assertEqual(cmd, ["python", "-m", "ufo", "--task", "demo", "--mode", "normal", "--request", "Open Notepad"])

    def test_empty_request_rejected(self):
        with self.assertRaises(ValueError):
            build_command(UfoConfig(Path(".")), "demo", "")

    def test_dry_run_never_starts_subprocess(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "ufo").mkdir()
            (root / "ufo" / "ufo.py").touch()
            with patch("smartautomation.ufo.subprocess.Popen") as popen:
                self.assertEqual(launch(UfoConfig(root), "demo", "open notepad"), 0)
                popen.assert_not_called()

    def test_execution_opt_in_required(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "ufo").mkdir()
            (root / "ufo" / "ufo.py").touch()
            with patch.dict(os.environ, {"SMARTAUTOMATION_EXECUTION_ENABLED": "false"}):
                with self.assertRaises(PermissionError):
                    launch(UfoConfig(root), "demo", "open notepad", execute=True)

if __name__ == "__main__":
    unittest.main()
