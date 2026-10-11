import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from smartautomation.hardware_mcp_preflight import hardware_endpoint, probe


class HardwareMcpPreflightTests(unittest.TestCase):
    def make_root(self, base: Path, host="localhost", port=8006):
        folder=base/"config"/"ufo"
        folder.mkdir(parents=True)
        (folder/"mcp.yaml").write_text(
            "HostAgent:\n  default:\n    action: []\n"
            "HardwareAgent:\n  default:\n    action:\n"
            "      - namespace: HardwareExecutor\n"
            "        type: http\n"
            f"        host: '{host}'\n        port: {port}\n        path: '/mcp'\n"
            "LinuxAgent:\n  default: {}\n", encoding="utf-8"
        )
        return base

    def test_hardware_endpoint_detected(self):
        with tempfile.TemporaryDirectory() as tmp:
            endpoint=hardware_endpoint(self.make_root(Path(tmp)))
            self.assertEqual(endpoint["port"],8006)
            self.assertEqual(endpoint["status"],"configured")

    def test_nonlocal_endpoint_never_probed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=self.make_root(Path(tmp),host="example.org")
            with patch("smartautomation.hardware_mcp_preflight.socket.create_connection") as connect:
                result=probe(root)
            connect.assert_not_called()
            self.assertEqual(result["tcp_status"],"not_tested")

    def test_connection_refused_is_not_mcp_success(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=self.make_root(Path(tmp))
            with patch("smartautomation.hardware_mcp_preflight.socket.create_connection",side_effect=ConnectionRefusedError()):
                result=probe(root)
            self.assertEqual(result["tcp_status"],"not_reachable")
            self.assertFalse(result["mcp_verified"])

    def test_listening_tcp_does_not_prove_mcp(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=self.make_root(Path(tmp))
            with patch("smartautomation.hardware_mcp_preflight.socket.create_connection") as connect:
                result=probe(root)
            connect.assert_called_once()
            self.assertEqual(result["tcp_status"],"listening")
            self.assertFalse(result["mcp_verified"])


if __name__=="__main__":
    unittest.main()
