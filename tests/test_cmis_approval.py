import json
import tempfile
import unittest
from pathlib import Path
from smartautomation.cmis_approval import approve_evidence, inspect_approval


class ApprovalTests(unittest.TestCase):
    def test_approval_bound_to_bytes_and_never_executes(self):
        with tempfile.TemporaryDirectory() as root:
            candidate = Path(root) / "candidate.json"
            approval = Path(root) / "approval.json"
            record = {
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
            candidate.write_text(json.dumps(record), encoding="utf-8")
            result = approve_evidence(candidate, approval, "Reviewer", "Confirmed evidence only")
            self.assertFalse(result["execution_allowed"])
            self.assertTrue(inspect_approval(candidate, approval)["evidence_approved"])
            with self.assertRaises(FileExistsError):
                approve_evidence(candidate, approval, "Reviewer", "Again")
            record["observed_steps"].append(dict(record["observed_steps"][0]))
            candidate.write_text(json.dumps(record), encoding="utf-8")
            with self.assertRaises(ValueError):
                inspect_approval(candidate, approval)

    def test_reject_incomplete_evidence(self):
        with tempfile.TemporaryDirectory() as root:
            candidate = Path(root) / "candidate.json"
            payload = {
                "schema_version": 1, "format": "cmis_smartautomation_candidate",
                "knowledge_id": "11111111-1111-1111-1111-111111111111",
                "source_session_id": "22222222-2222-2222-2222-222222222222",
                "knowledge_sha256": "A" * 64, "approval_state": "requires_independent_verification",
                "execution_allowed": False,
                "observed_steps": [{
                    "source_action_id": "33333333-3333-3333-3333-333333333333",
                    "review_decision": "rejected", "business_outcome": "unknown"
                }],
            }
            candidate.write_text(json.dumps(payload), encoding="utf-8")
            with self.assertRaises(ValueError):
                approve_evidence(candidate, Path(root) / "approval.json", "Reviewer", "Reason")
