import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from smartautomation.integration_preflight import collect
from smartautomation.ufo import UfoConfig


class IntegrationPreflightTests(unittest.TestCase):
    def test_read_only_report_without_windows(self):
        with tempfile.TemporaryDirectory() as temp:
            config = UfoConfig(Path(temp))
            with patch("smartautomation.integration_preflight.UfoConfig.from_environment",return_value=config), patch("smartautomation.integration_preflight.sys.platform","linux"):
                report = collect("Word")
            self.assertFalse(report["ufo_detected"])
            self.assertFalse(report["desktop_actions_executed"])
            self.assertEqual(report["discovery_status"],"windows_required")

    def test_windows_discovery_mocked(self):
        with tempfile.TemporaryDirectory() as temp:
            config = UfoConfig(Path(temp))
            with patch("smartautomation.integration_preflight.UfoConfig.from_environment",return_value=config), patch("smartautomation.integration_preflight.sys.platform","win32"), patch("smartautomation.integration_preflight.discover_start_apps", return_value=[{"name":"Word","app_id":"office.word","source":"windows_start"}]):
                report = collect("Word")
            self.assertEqual(report["applications"][0]["app_id"],"office.word")
            self.assertFalse(report["desktop_actions_executed"])


if __name__ == "__main__":
    unittest.main()
