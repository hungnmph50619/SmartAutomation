import json
import tempfile
import unittest
from pathlib import Path
from smartautomation.trajectory_evidence import assess_trajectory


class TrajectoryEvidenceTests(unittest.TestCase):
    def test_evaluator_claim_contradicted_by_failed_actions(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            data=[
                {"action":[{"function":"run_shell","result":{"status":"failure"}}],"function_call":"run_shell","result":"launch attempt"},
                {"action":[{"function":"no_action","result":{"status":"none"}}],"function_call":"no_action","result":"The task failed because Word could not be launched. No document was created or saved."},
            ]
            (root/"response.log").write_text("\n".join(json.dumps(x) for x in data),encoding="utf-8")
            (root/"evaluation.log").write_text(json.dumps({"complete":"yes"}),encoding="utf-8")
            outcome=assess_trajectory(root)
            self.assertEqual(outcome["trajectory_status"],"reported_failure")
            self.assertTrue(outcome["evaluator_conflict"])
            self.assertFalse(outcome["document_verified"])

    def test_success_claim_is_never_document_verification(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            (root/"response.log").write_text(json.dumps({"action":[],"function_call":"no_action","result":"done"}),encoding="utf-8")
            (root/"evaluation.log").write_text(json.dumps({"complete":"yes"}),encoding="utf-8")
            outcome=assess_trajectory(root)
            self.assertFalse(outcome["evaluator_conflict"])
            self.assertFalse(outcome["document_verified"])

    def test_missing_logs_fail_closed(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertEqual(assess_trajectory(Path(d))["trajectory_status"],"unknown")


if __name__=="__main__":
    unittest.main()
