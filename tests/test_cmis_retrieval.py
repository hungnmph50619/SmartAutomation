import json
import tempfile
import unittest
from pathlib import Path
from smartautomation.cmis_approval import approve_evidence
from smartautomation.cmis_retrieval import retrieve_evidence


class RetrievalTests(unittest.TestCase):
    def test_requires_approved_bytes_and_fresh_grounding(self):
        with tempfile.TemporaryDirectory() as root:
            candidate = Path(root) / "candidate.json"
            approval = Path(root) / "approval.json"
            data = {
                "schema_version": 1, "format": "cmis_smartautomation_candidate",
                "knowledge_id": "11111111-1111-1111-1111-111111111111",
                "source_session_id": "22222222-2222-2222-2222-222222222222",
                "knowledge_sha256": "A" * 64,
                "approval_state": "requires_independent_verification",
                "execution_allowed": False,
                "observed_steps": [{
                    "source_action_id": "33333333-3333-3333-3333-333333333333",
                    "review_decision": "confirmed", "business_outcome": "unknown"
                }],
            }
            candidate.write_text(json.dumps(data), encoding="utf-8")
            approve_evidence(candidate, approval, "Reviewer", "Checked evidence")
            no_context = retrieve_evidence(candidate, approval, {})
            self.assertEqual(no_context["status"], "insufficient_current_observation")
            observed = retrieve_evidence(candidate, approval, {"observed_process": "notepad.exe"})
            self.assertEqual(observed["matches"], [])
            self.assertFalse(observed["execution_allowed"])
            self.assertTrue(observed["requires_fresh_grounding"])
            data["observed_steps"].append(data["observed_steps"][0])
            candidate.write_text(json.dumps(data), encoding="utf-8")
            with self.assertRaises(ValueError):
                retrieve_evidence(candidate, approval, {"observed_process": "notepad.exe"})


if __name__ == "__main__":
    unittest.main()
