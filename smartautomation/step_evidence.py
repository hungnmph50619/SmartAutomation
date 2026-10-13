"""Map independent artifact checks into conservative step checkpoint evidence.

No UFO trajectory assertions count as independent verification.
"""
from __future__ import annotations


def output_step_evidence(result: dict) -> list[tuple[str, str, str]]:
    """Return deterministic step IDs, statuses and bounded evidence codes."""
    steps: list[tuple[str, str, str]] = []
    if result.get("save_target_status") in {"file_exists_at_requested_path", "docx_content_mismatch", "invalid_docx_package"}:
        steps.append(("target", "verified", "target_fresh"))
    elif result.get("save_target_status") in {
        "missing_target_file", "empty_target_file", "preexisting_file_unchanged"
    }:
        steps.append(("target", "failed", "verification_failed"))
    else:
        steps.append(("target", "unknown", "evidence_missing"))

    if result.get("package_valid") is True:
        steps.append(("docx_package", "verified", "package_valid"))
    elif result.get("package_status") in {
        "invalid_docx_package", "invalid_document_root", "unreadable_docx",
        "file_too_large", "document_xml_too_large"
    }:
        steps.append(("docx_package", "failed", "verification_failed"))
    else:
        steps.append(("docx_package", "unknown", "evidence_missing"))

    if result.get("content_verified") is True:
        steps.append(("docx_content", "verified", "content_matched"))
    elif result.get("content_check_status") == "content_mismatch":
        steps.append(("docx_content", "failed", "verification_failed"))
    else:
        steps.append(("docx_content", "unknown", "evidence_missing"))
    return steps
