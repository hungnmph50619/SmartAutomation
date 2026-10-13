import unittest
from smartautomation.step_evidence import output_step_evidence


class StepEvidenceMappingTests(unittest.TestCase):
    def test_content_failure_keeps_validated_target_and_package(self):
        result = output_step_evidence({
            "save_target_verified": False,
            "save_target_status": "docx_content_mismatch",
            "package_valid": True,
            "content_verified": False,
            "content_check_status": "content_mismatch",
        })
        self.assertEqual(result, [
            ("target", "verified", "target_fresh"),
            ("docx_package", "verified", "package_valid"),
            ("docx_content", "failed", "verification_failed"),
        ])

    def test_missing_target_cannot_assert_any_downstream_step(self):
        result = output_step_evidence({"save_target_status": "missing_target_file"})
        self.assertEqual(result[0], ("target", "failed", "verification_failed"))
        self.assertEqual(result[1][1], "unknown")
        self.assertEqual(result[2][1], "unknown")

    def test_unchecked_content_is_unknown_not_verified(self):
        result = output_step_evidence({
            "save_target_status": "file_exists_at_requested_path",
            "package_valid": True,
            "content_check_status": "not_specified",
        })
        self.assertEqual(result[2], ("docx_content", "unknown", "evidence_missing"))


if __name__ == "__main__":
    unittest.main()
