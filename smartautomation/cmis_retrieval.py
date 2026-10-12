"""Read-only evidence retrieval for a live planner, without replay or inferred goals."""
from __future__ import annotations
import json
from pathlib import Path
from smartautomation.cmis_approval import inspect_approval


def retrieve_evidence(candidate_path: str | Path, approval_path: str | Path,
                      current_observation: dict) -> dict:
    """Return provenance only when the independent approval matches source bytes.

    No stale coordinates, UI targets, or action suggestions cross this boundary.
    """
    verified = inspect_approval(candidate_path, approval_path)
    if not isinstance(current_observation, dict):
        raise ValueError("current observation required")
    process = current_observation.get("observed_process")
    if not isinstance(process, str) or not process.strip() or len(process) > 256:
        return {"status": "insufficient_current_observation", "matches": [],
                "execution_allowed": False, "desktop_actions_executed": False}
    data = json.loads(Path(candidate_path).read_text(encoding="utf-8"))
    if not isinstance(data.get("observed_steps"), list):
        raise ValueError("invalid observed steps")
    # Process equality provides provenance, never UI grounding or executable targets.
    matches = []
    for step in data["observed_steps"]:
        prior = step.get("observed_process")
        if (step.get("review_decision") == "confirmed"
                and isinstance(prior, str) and prior.strip()
                and prior.casefold() == process.strip().casefold()):
            matches.append({"source_action_id": step["source_action_id"],
                            "match_basis": "observed_process_only",
                            "action_suggestion": None})
    return {
        "status": "process_context_candidate_only" if matches else "no_grounded_context_match",
        "matches": matches,
        "reviewed_evidence_count": len(data["observed_steps"]),
        "source_sha256": verified["candidate_sha256"],
        "execution_allowed": False,
        "desktop_actions_executed": False,
        "requires_fresh_grounding": True,
    }
