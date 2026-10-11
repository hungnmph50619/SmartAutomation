import tempfile
import unittest
from pathlib import Path
from smartautomation.outcome_evidence import classify_process_outcome


class OutcomeEvidenceTests(unittest.TestCase):
    def test_zero_exit_does_not_verify_document(self):
        result=classify_process_outcome(0)
        self.assertEqual(result["process_status"],"exited_zero")
        self.assertFalse(result["task_verified"])

    def test_unicode_error_is_classified_not_marked_success(self):
        with tempfile.TemporaryDirectory() as directory:
            log=Path(directory)/"stderr.log"
            log.write_text("UnicodeEncodeError: 'charmap' codec can't encode character",encoding="utf-8")
            result=classify_process_outcome(1,log)
            self.assertEqual(result["reason_code"],"unicode_output_error")
            self.assertFalse(result["task_verified"])

    def test_other_nonzero_exit(self):
        result=classify_process_outcome(2)
        self.assertEqual(result["reason_code"],"ufo_process_nonzero_exit")
        self.assertFalse(result["task_verified"])


if __name__=="__main__":
    unittest.main()
