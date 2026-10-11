import unittest
from types import SimpleNamespace
from smartautomation.tool_contract import ToolDiscoveryError, validate_list_tools


class ToolContractTests(unittest.TestCase):
    def test_valid_result(self):
        tools = validate_list_tools([SimpleNamespace(status="success", result=[{"tool_name": "click", "description": "Click"}])])
        self.assertEqual(tools[0]["tool_name"], "click")

    def test_rejects_string_connection_error(self):
        with self.assertRaises(ToolDiscoveryError) as cm:
            validate_list_tools([SimpleNamespace(status="error", result="Client failed to connect")])
        self.assertEqual(cm.exception.reason, "list_tools_command_failed")

    def test_rejects_string_even_when_status_claims_success(self):
        with self.assertRaises(ToolDiscoveryError) as cm:
            validate_list_tools([SimpleNamespace(status="success", result="Client failed to connect")])
        self.assertEqual(cm.exception.reason, "unexpected_tools_payload_type")

    def test_rejects_missing_or_bad_entries(self):
        for payload in (None, [], ["error"], [{"name": "click"}]):
            with self.subTest(payload=payload), self.assertRaises(ToolDiscoveryError):
                validate_list_tools([{"status": "success", "result": payload}])

    def test_rejects_missing_dispatch_result(self):
        with self.assertRaises(ToolDiscoveryError):
            validate_list_tools([])


if __name__ == "__main__":
    unittest.main()
