"""Read-only assessment joining a CMIS candidate and existing UFO evaluator logs.

CMIS recordings and UFO runs are independent until an operator supplies an
explicit correlation. Without that correlation a UFO evaluation cannot label
individual CMIS clicks as successful or failed.
"""
from __future__ import annotations

import json
from pathlib import Path

from .cmis_candidate import inspect_candidate
from .cmis_evaluation import classify_evaluation


def assess_cmis_with_ufo(candidate_path: str | Path, ufo_log_folder: str | Path,
                         *, expected_session_id: str | None = None) -> dict:
    """Validate CMIS provenance and summarize UFO evidence without mutating either."""
    path = Path(candidate_path)
    inspected = inspect_candidate(path)
    if expected_session_id is not None and str(inspected["session_id"]).lower() != expected_session_id.lower():
        raise ValueError("CMIS session does not match the explicitly selected session")
    candidate = json.loads(path.read_text(encoding="utf-8"))
    evaluation = classify_evaluation(Path(ufo_log_folder))
    findings = []
    for step in candidate["observed_steps"]:
        findings.append({
            "action_id": step["source_action_id"],
            "observed_process": step.get("observed_process"),
            "human_decision": step["review_decision"],
            "automatic_status": "requires_review",
            "reason_code": "no_correlated_action_outcome",
        })
    return {
        "schema_version": 1,
        "format": "cmis_ufo_evidence_assessment",
        "source_session_id": inspected["session_id"],
        "candidate_file_sha256": inspected["candidate_file_sha256"],
        "ufo_evaluation": evaluation,
        "steps": findings,
        "independent_step_verification": False,
        "execution_allowed": False,
        "warning": "UFO run evidence is not correlated with CMIS actions; no click is automatically approved.",
    }
