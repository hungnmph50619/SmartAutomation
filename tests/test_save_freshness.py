import tempfile
import unittest
from pathlib import Path
from smartautomation.save_target import snapshot_saved_target, assess_saved_target


class SaveFreshnessTests(unittest.TestCase):
    def test_stale_existing_file_is_not_new_task_output(self):
        with tempfile.TemporaryDirectory() as d:
            target=Path(d)/"report.docx"
            target.write_bytes(b"old")
            before=snapshot_saved_target(target)
            result=assess_saved_target(target,before=before,require_fresh=True)
            self.assertFalse(result["save_target_verified"])
            self.assertEqual(result["save_target_status"],"preexisting_file_unchanged")

    def test_changed_file_is_accepted_as_path_evidence(self):
        with tempfile.TemporaryDirectory() as d:
            target=Path(d)/"report.docx"
            target.write_bytes(b"old")
            before=snapshot_saved_target(target)
            target.write_bytes(b"replacement with different length")
            result=assess_saved_target(target,before=before,require_fresh=True)
            self.assertTrue(result["save_target_verified"])

    def test_created_file_is_accepted_as_path_evidence(self):
        with tempfile.TemporaryDirectory() as d:
            target=Path(d)/"report.docx"
            before=snapshot_saved_target(target)
            target.write_bytes(b"new")
            self.assertTrue(assess_saved_target(target,before=before,require_fresh=True)["save_target_verified"])

    def test_missing_file_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            target=Path(d)/"report.docx"
            self.assertFalse(assess_saved_target(target,before=None,require_fresh=True)["save_target_verified"])


if __name__=="__main__":
    unittest.main()
