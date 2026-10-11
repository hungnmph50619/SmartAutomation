import tempfile
import unittest
from pathlib import Path

from smartautomation.hardware_capability import classify_hardware_server


class HardwareCapabilityTests(unittest.TestCase):
    def test_missing_source_not_approved(self):
        with tempfile.TemporaryDirectory() as path:
            result=classify_hardware_server(Path(path))
            self.assertFalse(result["desktop_control_verified"])

    def test_known_dummy_implementation(self):
        with tempfile.TemporaryDirectory() as path:
            file=Path(path)/"ufo/client/mcp/http_servers/hardware_mcp_server.py"
            file.parent.mkdir(parents=True)
            file.write_text('def create_hardware_mcp_server():\n    """Mock hardware tools (dummy only)."""\n    async def click_mouse(): pass\n    async def type_text(): pass\n    async def press_hotkey(): pass\n',encoding="utf-8")
            result=classify_hardware_server(Path(path))
            self.assertEqual(result["status"],"mock_server")
            self.assertFalse(result["desktop_control_verified"])


if __name__=="__main__":
    unittest.main()
