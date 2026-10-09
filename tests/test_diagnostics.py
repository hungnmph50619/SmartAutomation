from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from smartautomation.diagnostics import check_readiness
from smartautomation.ufo import UfoConfig

class DiagnosticsTests(unittest.TestCase):
    def test_probe_never_spawns_a_process(self):
        with tempfile.TemporaryDirectory() as temp:
            with patch("subprocess.Popen") as popen:
                result = check_readiness(UfoConfig(Path(temp)))
                popen.assert_not_called()
                self.assertFalse(result["ready_for_windows_validation"])
                self.assertTrue(any(x["name"] == "ufo_source" and not x["ok"] for x in result["checks"]))

    def test_report_is_json_serializable(self):
        import json
        json.dumps(check_readiness(UfoConfig(Path("missing-ufo"))))
