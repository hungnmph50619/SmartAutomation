import json
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

from smartautomation.export_diagnostics import export
from smartautomation.ufo import UfoConfig


class OversizedDiagnosticTests(unittest.TestCase):
    def test_large_request_does_not_block_other_evidence(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            ufo = base / "UFO"
            task = "smartautomation-1234abcd"
            folder = ufo / "logs" / task
            folder.mkdir(parents=True)
            (folder / "request.log").write_text("large", encoding="utf-8")
            (folder / "response.log").write_text("action evidence", encoding="utf-8")
            with patch("smartautomation.export_diagnostics.MAX_FILE_BYTES", 8), patch(
                "smartautomation.export_diagnostics.UfoConfig.from_environment",
                return_value=UfoConfig(ufo)
            ):
                path = export(task, desktop=base)
            with zipfile.ZipFile(path) as archive:
                names = archive.namelist()
                self.assertIn("response.log", names)
                self.assertNotIn("request.log", names)
                manifest = json.loads(archive.read("EXPORT-MANIFEST.json"))
                self.assertTrue(manifest["partial"])
                self.assertEqual(manifest["skipped"][0]["path"], "request.log")
                self.assertEqual(manifest["skipped"][0]["reason"], "file_size_limit")


if __name__ == "__main__":
    unittest.main()
