import tempfile
import unittest
from pathlib import Path

from smartautomation.event_store import EventStore


class OutputCheckpointTests(unittest.TestCase):
    def test_checkpoint_survives_reopening_database(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "events.db"
            EventStore(path).save_output_checkpoint("job-123", "failed", "content_mismatch")
            evidence = EventStore(path).load_output_checkpoint("job-123")
            self.assertEqual(evidence["output_status"], "failed")
            self.assertEqual(evidence["recovery_reason"], "content_mismatch")
            self.assertFalse(evidence["can_auto_resume"])

    def test_repeated_checkpoint_updates_same_job(self):
        with tempfile.TemporaryDirectory() as folder:
            store = EventStore(Path(folder) / "events.db")
            store.save_output_checkpoint("job-123", "failed", "content_mismatch")
            store.save_output_checkpoint("job-123", "verified", "output_verified")
            self.assertEqual(store.load_output_checkpoint("job-123")["output_status"], "verified")
            self.assertIsNone(store.load_output_checkpoint("unknown"))

    def test_step_checkpoints_survive_restart_and_preserve_verified_steps(self):
        with tempfile.TemporaryDirectory() as folder:
            db = Path(folder) / "events.db"
            store = EventStore(db)
            store.save_step_checkpoint("job-1", "A", "verified", "target_fresh")
            store.save_step_checkpoint("job-1", "B", "verified", "content_matched")
            store.save_step_checkpoint("job-1", "C", "failed", "verification_failed")
            rows = EventStore(db).list_step_checkpoints("job-1")
            self.assertEqual([row["status"] for row in rows], ["verified", "verified", "failed"])
            self.assertTrue(all(not row["can_auto_resume"] for row in rows))
            with self.assertRaises(ValueError):
                store.save_step_checkpoint("job-1", "A", "failed", "verification_failed")
            self.assertEqual(EventStore(db).list_step_checkpoints("job-1")[0]["status"], "verified")

    def test_step_evidence_rejects_unsupported_or_sensitive_inputs(self):
        with tempfile.TemporaryDirectory() as folder:
            store = EventStore(Path(folder) / "events.db")
            with self.assertRaises(ValueError):
                store.save_step_checkpoint("job", "../secret", "verified", "target_fresh")
            with self.assertRaises(ValueError):
                store.save_step_checkpoint("job", "A", "verified", "evidence_missing")
            with self.assertRaises(ValueError):
                store.save_step_checkpoint("job", "B", "failed", "content_matched")

    def test_rejects_arbitrary_sensitive_metadata(self):
        with tempfile.TemporaryDirectory() as folder:
            store = EventStore(Path(folder) / "events.db")
            with self.assertRaises(ValueError):
                store.save_output_checkpoint("job-123", "secret path", "content_mismatch")
            with self.assertRaises(ValueError):
                store.save_output_checkpoint("job-123", "failed", "free-form-secret")


if __name__ == "__main__":
    unittest.main()
