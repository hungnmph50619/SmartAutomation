import unittest

from smartautomation.launch_capabilities import (
    discover_launch_context,
    guide_application_launch,
)


class LaunchCapabilityTests(unittest.TestCase):
    def test_find_exact_application_name_in_request(self):
        apps = [
            {"name": "Microsoft Word", "app_id": "Microsoft.Office.WINWORD.EXE.15"},
            {"name": "Calculator", "app_id": "Microsoft.WindowsCalculator"},
        ]
        matches = discover_launch_context(
            "Please open Microsoft Word and create a document",
            discovery=lambda: apps,
        )
        self.assertEqual(matches, [
            {"name": "Microsoft Word", "source": "windows_start", "available": True}
        ])

    def test_no_speculative_app_match(self):
        apps = [{"name": "Microsoft Word", "app_id": "office-app-id"}]
        self.assertEqual(discover_launch_context("Open Excel", discovery=lambda: apps), [])

    def test_discovery_failure_returns_empty(self):
        def broken():
            raise OSError("Discovery unavailable")
        self.assertEqual(discover_launch_context("Open Word", discovery=broken), [])

    def test_inert_hints_and_hard_length_limit(self):
        context = guide_application_launch(
            "Open Microsoft Word",
            [{"name": "Microsoft Word", "available": True, "source": "windows_start"}],
        )
        self.assertIn("Windows Start Apps", context)
        self.assertIn("HostUIExecutor", context)
        self.assertNotIn("Microsoft.Office.WINWORD.EXE.15", context)
        request = "a" * 1950
        self.assertEqual(guide_application_launch(request, []), request)

    def test_no_execution_side_effects(self):
        self.assertIn("Start Menu", guide_application_launch("Open Word", []))


if __name__ == "__main__":
    unittest.main()
