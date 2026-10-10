import unittest
from smartautomation.failure_breaker import detect_repetition


class CircuitTests(unittest.TestCase):
    def test_three_repeated_failure_lines_trigger_advisory(self):
        result = detect_repetition("file not found\nfile not found\nfile not found")
        self.assertEqual(result["state"], "suspected_repeat")
        self.assertEqual(result["reason_code"], "launch_not_found")
        self.assertEqual(result["action"], "review_and_replan")

    def test_loading_does_not_trigger(self):
        self.assertEqual(detect_repetition("Loading Word...\nWaiting 60 seconds...")["state"], "clear")

    def test_mixed_errors_not_mislabeled_as_repeated(self):
        self.assertEqual(detect_repetition("file not found\naccess denied\nblocked by security policies")["state"], "clear")

    def test_single_log_line_not_three_attempts(self):
        self.assertEqual(detect_repetition("file not found; file not found; file not found")["state"], "clear")


if __name__ == "__main__":
    unittest.main()
