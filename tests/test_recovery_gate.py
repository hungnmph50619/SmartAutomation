import unittest
from smartautomation.recovery_gate import evaluate_gate


class GateTests(unittest.TestCase):
    def test_repeated_error_requires_review_not_auto_resume(self):
        result = evaluate_gate({"circuit_breaker": {"state":"suspected_repeat","reason_code":"launch_not_found"}}, "running")
        self.assertEqual(result.state, "review")
        self.assertFalse(result.can_auto_resume)

    def test_slow_loading_is_only_observed(self):
        result = evaluate_gate({"warning": "no_recent_evidence"}, "running")
        self.assertEqual(result.state, "observe")
        self.assertFalse(result.can_auto_resume)

    def test_finished_tasks_are_not_interrupted(self):
        result = evaluate_gate({"circuit_breaker":{"state":"suspected_repeat"}}, "finished")
        self.assertEqual(result.state, "inactive")


if __name__ == "__main__":
    unittest.main()
