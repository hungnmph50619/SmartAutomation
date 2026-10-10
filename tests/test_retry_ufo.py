import unittest
from unittest.mock import patch
from smartautomation.jobs import Job, JobManager


class RetryTests(unittest.TestCase):
    def make_manager(self):
        with patch("smartautomation.jobs.EventStore"):
            manager = JobManager()
        manager._job = Job("job1", "failed", 1.0, request="Open application and create report")
        return manager

    def test_retry_needs_separate_confirmation(self):
        manager = self.make_manager()
        with self.assertRaises(PermissionError):
            manager.retry_from_failed("job1", "Word", False)

    def test_running_task_cannot_be_retried(self):
        manager = self.make_manager()
        manager._job.state = "running"
        with self.assertRaises(RuntimeError):
            manager.retry_from_failed("job1", "Word", True)

    def test_retry_uses_original_request_and_ufo_manager(self):
        manager = self.make_manager()
        with patch.object(manager, "start", return_value={"state":"running"}) as start:
            result = manager.retry_from_failed("job1", "Word", True)
        self.assertEqual(result["state"], "running")
        payload = start.call_args.args[0]
        self.assertIn("Start Menu", payload)
        self.assertIn("Open application and create report", payload)
        self.assertEqual(start.call_args.kwargs, {"confirmed": True})


if __name__ == "__main__":
    unittest.main()
