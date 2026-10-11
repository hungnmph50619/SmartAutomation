import tempfile
import unittest
from pathlib import Path
from smartautomation.word_acceptance import assess

class WordAcceptanceTests(unittest.TestCase):
    def test_no_log_does_not_prove_success(self):
        with tempfile.TemporaryDirectory() as d:
            result=assess("smartautomation-a1b2c3d4",Path(d))
            self.assertFalse(result["document_verified"])
            self.assertEqual(result["assessment"],"requires_document_review")

    def test_varied_failure_wording_is_detected(self):
        examples = [
            "The task failed because Microsoft Word could not be launched.",
            "Failed to open Microsoft Word using winword.exe.",
            "Microsoft Word was unable to start.",
        ]
        for message in examples:
            with self.subTest(message=message), tempfile.TemporaryDirectory() as d:
                folder=Path(d)/"logs"/"smartautomation-a1b2c3d4"
                folder.mkdir(parents=True)
                (folder/"output.md").write_text(message, encoding="utf-8")
                result=assess("smartautomation-a1b2c3d4",Path(d))
                self.assertEqual(result["assessment"],"reported_failure")
                self.assertFalse(result["document_verified"])

    def test_prior_failure_is_detected(self):
        with tempfile.TemporaryDirectory() as d:
            folder=Path(d)/"logs"/"smartautomation-a1b2c3d4"
            folder.mkdir(parents=True)
            (folder/"output.md").write_text("Microsoft Word could not be launched. No document was created.",encoding="utf-8")
            result=assess("smartautomation-a1b2c3d4",Path(d))
            self.assertEqual(result["assessment"],"reported_failure")
            self.assertFalse(result["document_verified"])

if __name__=="__main__":
    unittest.main()
