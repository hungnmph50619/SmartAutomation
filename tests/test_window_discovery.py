import unittest
from unittest.mock import patch, Mock
from smartautomation.window_discovery import discover_visible_processes, guide_existing_window


class WindowDiscoveryTests(unittest.TestCase):
    def test_generic_ui_first_guidance(self):
        value=guide_existing_window("Edit current spreadsheet",["EXCEL","chrome"])
        self.assertIn("get_desktop_app_info", value)
        self.assertIn("select_application_window", value)
        self.assertIn("EXCEL", value)
        self.assertTrue(value.endswith("Edit current spreadsheet"))

    def test_does_not_overflow_task(self):
        request="x"*1970
        self.assertEqual(guide_existing_window(request, ["WINWORD"]), request)

    def test_no_windows_does_not_infer_target(self):
        result=guide_existing_window("Edit a document", [])
        self.assertNotIn("WINWORD", result)
        self.assertIn("Edit a document", result)

    def test_non_windows_returns_empty(self):
        with patch("smartautomation.window_discovery.sys.platform","linux"):
            self.assertEqual(discover_visible_processes(),[])

    def test_untrusted_process_names_rejected(self):
        with patch("smartautomation.window_discovery.sys.platform","win32"), patch(
            "smartautomation.window_discovery.subprocess.run",
            return_value=Mock(stdout='["WINWORD","EXCEL","hello;bad","WINWORD"]')
        ):
            self.assertEqual(discover_visible_processes(),["EXCEL","WINWORD"])


if __name__=="__main__":
    unittest.main()
