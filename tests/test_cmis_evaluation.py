import json
import tempfile
import unittest
from pathlib import Path

from smartautomation.cmis_evaluation import classify_evaluation


class CmisEvaluationTests(unittest.TestCase):
    def test_claim_of_success_is_not_independent_verification(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)
            (path / "response.log").write_text(json.dumps({"action": [], "result": "done"}), encoding="utf-8")
            (path / "evaluation.log").write_text(json.dumps({"complete": "yes"}), encoding="utf-8")
            outcome = classify_evaluation(path)
            self.assertEqual(outcome["status"], "requires_review")
            self.assertFalse(outcome["execution_allowed"])

    def test_independent_evidence_and_evaluator_agree(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)
            (path / "response.log").write_text(json.dumps({"action": [], "result": "done"}), encoding="utf-8")
            (path / "evaluation.log").write_text(json.dumps({"complete": "yes"}), encoding="utf-8")
            outcome = classify_evaluation(path, independent_success=True)
            self.assertEqual(outcome["status"], "verified_success")
            self.assertFalse(outcome["execution_allowed"])

    def test_evaluator_contradiction_never_success(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)
            (path / "response.log").write_text(json.dumps({"action": [{"function": "click", "result": {"status": "failure"}}], "result": "failed"}), encoding="utf-8")
            (path / "evaluation.log").write_text(json.dumps({"complete": "yes"}), encoding="utf-8")
            outcome = classify_evaluation(path, independent_success=True)
            self.assertEqual(outcome["status"], "failure_evidence")

    def test_missing_evaluation_needs_review(self):
        with tempfile.TemporaryDirectory() as folder:
            outcome = classify_evaluation(Path(folder))
            self.assertEqual(outcome["status"], "requires_review")


if __name__ == "__main__":
    unittest.main()
