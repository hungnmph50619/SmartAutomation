import tempfile
import unittest
from pathlib import Path
from smartautomation.windows_ui_capability import inspect_windows_ui


class WindowsUICapabilityTests(unittest.TestCase):
    def test_missing_source_fails_closed(self):
        with tempfile.TemporaryDirectory() as d:
            result = inspect_windows_ui(Path(d))
            self.assertFalse(result["implementation_detected"])
            self.assertFalse(result["live_windows_verified"])

    def test_expected_real_ui_factories_detected_without_claiming_live_success(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            path = root / "ufo/client/mcp/local_servers/ui_mcp_server.py"
            path.parent.mkdir(parents=True)
            path.write_text(
                "def create_host_action_mcp_server():\n"
                " def select_application_window(): pass\n"
                "def create_app_action_mcp_server():\n"
                " def click_input(): pass\n"
                " def keyboard_input(): pass\n"
                " def set_edit_text(): pass\n"
                "def create_data_mcp_server():\n"
                " def get_desktop_app_target_info(): pass\n"
                " def capture_desktop_screenshot(): pass\n",
                encoding="utf-8",
            )
            result = inspect_windows_ui(root)
            self.assertTrue(result["implementation_detected"])
            self.assertFalse(result["live_windows_verified"])

    def test_missing_keyboard_tool_is_not_ready(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "ufo/client/mcp/local_servers/ui_mcp_server.py"
            path.parent.mkdir(parents=True)
            path.write_text("def create_app_action_mcp_server():\n def click_input(): pass\n", encoding="utf-8")
            self.assertFalse(inspect_windows_ui(Path(d))["implementation_detected"])


if __name__ == "__main__":
    unittest.main()
