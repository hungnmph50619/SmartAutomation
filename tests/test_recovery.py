import unittest
from smartautomation.recovery import recommend_apps, recovery_instructions


class RecoveryTests(unittest.TestCase):
    def test_recommends_installed_app_without_executing_it(self):
        apps = [{"name": "Word", "app_id": "office.word", "source": "windows_start"}]
        breaker = {"state": "suspected_repeat", "reason_code": "launch_not_found"}
        result = recommend_apps("Word", apps, breaker)
        self.assertEqual(result["status"], "candidate_found")
        self.assertEqual(result["candidates"][0]["app_id"], "office.word")
        self.assertEqual(result["next_step"], "confirm_application_then_retry_via_ufo")

    def test_retry_instruction_only_for_launch_not_found(self):
        candidate = {"name": "Word", "app_id": "office.word"}
        denied = {"state":"suspected_repeat","reason_code":"launch_blocked"}
        allowed = {"state":"suspected_repeat","reason_code":"launch_not_found"}
        self.assertEqual(recovery_instructions(candidate, denied)["status"], "not_allowed")
        self.assertEqual(recovery_instructions(candidate, allowed)["status"], "review_required")
        self.assertIn("Start Menu", recovery_instructions(candidate, allowed)["instruction"])

    def test_no_recovery_during_normal_wait(self):
        result = recommend_apps("Word", [{"name": "Word", "app_id": "word"}], {"state": "clear"})
        self.assertEqual(result["status"], "not_needed")

    def test_security_error_only_recommends_no_bypass(self):
        result = recommend_apps("Unknown", [], {"state": "suspected_repeat", "reason_code": "launch_blocked"})
        self.assertEqual(result["status"], "security_policy_review")


if __name__ == "__main__":
    unittest.main()
