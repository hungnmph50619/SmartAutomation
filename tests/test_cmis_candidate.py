import json
import tempfile
import unittest
from pathlib import Path
from smartautomation.cmis_candidate import inspect_candidate


class CandidateContractTests(unittest.TestCase):
    def test_read_only_acceptance(self):
        with tempfile.TemporaryDirectory() as root:
            p = Path(root) / "candidate.json"
            p.write_text(json.dumps({
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
                    "business_outcome": "unknown"
                }]
            }), encoding="utf-8")
            result = inspect_candidate(p)
            self.assertEqual(result["step_count"], 1)
            self.assertFalse(result["execution_allowed"])
            self.assertFalse(result["desktop_actions_executed"])
            data = json.loads(p.read_text(encoding="utf-8"))
            data["execution_allowed"] = True
            p.write_text(json.dumps(data), encoding="utf-8")
            with self.assertRaises(ValueError):
                inspect_candidate(p)
            data["execution_allowed"] = False
            data["observed_steps"][0]["business_outcome"] = "success"
            p.write_text(json.dumps(data), encoding="utf-8")
            with self.assertRaises(ValueError):
                inspect_candidate(p)


if __name__ == "__main__":
    unittest.main()
