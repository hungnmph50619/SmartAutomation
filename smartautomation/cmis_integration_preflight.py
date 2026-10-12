"""R40 integration preflight: reuse SmartAutomation's existing trust and observation modules.

No desktop control, no new event store, and no duplicated planning engine.
"""
from __future__ import annotations

from pathlib import Path

from smartautomation.cmis_candidate import inspect_candidate
from smartautomation.cmis_approval import inspect_approval


def inspect_cmis_integration(candidate_path: str | Path,
                             approval_path: str | Path | None = None) -> dict:
    """Inspect candidate provenance, delegating validation to existing R35/R36 modules."""
    candidate = inspect_candidate(candidate_path)
    result = {
        "candidate": candidate,
        "approval_status": "not_provided",
        "knowledge_usable_as_evidence": False,
        "execution_allowed": False,
        "desktop_actions_executed": False,
        "operator_backend": "microsoft_ufo",
        "existing_modules": {
            "events": "smartautomation.event_store.EventStore",
            "progress": "smartautomation.progress.summarize",
            "outcome": "smartautomation.outcome_evidence.classify_process_outcome",
            "recovery": "smartautomation.recovery.recommend_apps",
            "failure_breaker": "smartautomation.failure_breaker.detect_repetition",
            "retrieval": "smartautomation.cmis_retrieval.retrieve_evidence",
        },
    }
    if approval_path is not None:
        inspected = inspect_approval(candidate_path, approval_path)
        result["approval_status"] = "evidence_approved"
        result["knowledge_usable_as_evidence"] = inspected["evidence_approved"]
    return result
