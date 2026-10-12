import json
import tempfile
import unittest
from pathlib import Path
from smartautomation.cmis_approval import approve_evidence
from smartautomation.cmis_integration_preflight import inspect_cmis_integration


class ReusePreflightTests(unittest.TestCase):
    def test_uses_existing_approval_without_execution(self):
        with tempfile.TemporaryDirectory() as directory:
            candidate = Path(directory) / "candidate.json"
            approval = Path(directory) / "approval.json"
            candidate.write_text(json.dumps({
                "schema_version": 1,
                "format": "cmis_smartautomation_candidate",
                "knowledge_id": "11111111-1111-1111-1111-111111111111",
                "source_session_id": "22222222-2222-2222-2222-222222222222",
                "knowledge_sha256": "A" * 64,
                "approval_state": "requires_independent_verification",
                "execution_allowed": False,
                "observed_steps": [{
                    "source_action_id": "33333333-3333-3333-3333-333333333333",
                    "review_decision": "confirmed",
                    "business_outcome": "unknown",
                }]
            }), encoding="utf-8")
            pending = inspect_cmis_integration(candidate)
            self.assertEqual(pending["approval_status"], "not_provided")
            self.assertFalse(pending["knowledge_usable_as_evidence"])
            self.assertFalse(pending["execution_allowed"])
            approve_evidence(candidate, approval, "Reviewer", "Read-only review")
            reviewed = inspect_cmis_integration(candidate, approval)
            self.assertTrue(reviewed["knowledge_usable_as_evidence"])
            self.assertFalse(reviewed["desktop_actions_executed"])
            self.assertEqual(reviewed["operator_backend"], "microsoft_ufo")
            self.assertIn("smartautomation.event_store", reviewed["existing_modules"]["events"])
            with self.assertRaises(ValueError):
                inspect_cmis_integration(candidate, Path(directory) / "missing.json")
            candidate.write_text(candidate.read_text(encoding="utf-8") + " ", encoding="utf-8")
            with self.assertRaises(ValueError):
                inspect_cmis_integration(candidate, approval)


if __name__ == "__main__":
    unittest.main()
