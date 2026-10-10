import tempfile
import time
import unittest
from pathlib import Path
from smartautomation.progress import summarize


class ProgressTests(unittest.TestCase):
    def test_invalid_id_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(ValueError):
                summarize(Path(d), "../private")

    def test_no_log_is_not_a_hang(self):
        with tempfile.TemporaryDirectory() as d:
            result = summarize(Path(d), "smartautomation-1234abcd")
            self.assertIsNone(result["warning"])
            self.assertEqual(result["step_count"], 0)

    def test_detects_age_without_claiming_hang(self):
        with tempfile.TemporaryDirectory() as d:
            log = Path(d)/"logs"/"smartautomation-1234abcd"
            log.mkdir(parents=True)
            file = log/"action_step0.png"
            file.write_bytes(b"fake image")
            result = summarize(Path(d), "smartautomation-1234abcd", now=time.time()+100)
            self.assertEqual(result["step_count"], 1)
            self.assertEqual(result["warning"], "no_recent_evidence")


if __name__ == "__main__":
    unittest.main()
