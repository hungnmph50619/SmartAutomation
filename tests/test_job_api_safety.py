import os
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient
from smartautomation.api import app
from smartautomation.jobs import JobManager


class JobSafetyTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_execution_disabled_by_default(self):
        with patch.dict(os.environ, {"SMARTAUTOMATION_EXECUTION_ENABLED": "false"}):
            r = self.client.post("/api/jobs", json={"request": "Open Notepad", "confirmed": True},
                                 headers={"origin": "http://127.0.0.1:5173"})
            self.assertEqual(r.status_code, 403)

    def test_confirmation_required(self):
        with patch.dict(os.environ, {"SMARTAUTOMATION_EXECUTION_ENABLED": "true"}):
            r = self.client.post("/api/jobs", json={"request": "Open Notepad", "confirmed": False},
                                 headers={"origin": "http://127.0.0.1:5173"})
            self.assertEqual(r.status_code, 403)

    def test_cross_origin_rejected_even_when_execution_disabled(self):
        r = self.client.post("/api/jobs", json={"request": "Open Notepad", "confirmed": True},
                             headers={"origin": "https://attacker.example"})
        self.assertEqual(r.status_code, 403)

    def test_snapshot_is_idle_initially(self):
        self.assertEqual(JobManager().snapshot()["state"], "idle")

    def test_stop_missing_job(self):
        with self.assertRaises(LookupError):
            JobManager().stop("no-such-id")

    def test_status_has_no_credential_data(self):
        r = self.client.get("/api/jobs/current")
        self.assertEqual(r.status_code, 200)
        self.assertNotIn("API_KEY", r.text)


if __name__ == "__main__":
    unittest.main()
