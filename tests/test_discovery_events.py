import tempfile
from pathlib import Path
import unittest
from smartautomation.app_discovery import find_app
from smartautomation.event_store import EventStore
from smartautomation.telemetry import trace_phase


class DiscoveryAndEventTests(unittest.TestCase):
    def test_find_app_exact_before_partial(self):
        apps = [{"name":"Word Preview","app_id":"one"},{"name":"Word","app_id":"two"}]
        self.assertEqual(find_app("Word",apps)[0]["app_id"],"two")

    def test_does_not_store_sensitive_metadata(self):
        with tempfile.TemporaryDirectory() as folder:
            store = EventStore(Path(folder)/"events.db")
            store.emit("job1","failed",{"returncode":1,"api_key":"private","request":"confidential"})
            item = store.list_events("job1")[0]
            self.assertEqual(item["metadata"],{"returncode":1})
            self.assertNotIn("private",str(item))

    def test_unrecognized_event_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            with self.assertRaises(ValueError):
                EventStore(Path(folder)/"events.db").emit("job1","shell_launch",{})

    def test_telemetry_is_optional(self):
        with trace_phase("job.status",job_id="example"):
            pass


if __name__ == "__main__":
    unittest.main()
