"""Validate CMIS Recorder candidate files as evidence, never executable automation."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path


def inspect_candidate(path: str | Path) -> dict:
    file = Path(path)
    if file.stat().st_size > 10_000_000:
        raise ValueError("candidate too large")
    data = json.loads(file.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("candidate must be an object")
    if data.get("format") != "cmis_smartautomation_candidate" or data.get("schema_version") != 1:
        raise ValueError("unsupported candidate schema")
    if data.get("execution_allowed") is not False:
        raise ValueError("candidate execution must be explicitly disabled")
    if data.get("approval_state") != "requires_independent_verification":
        raise ValueError("unexpected approval state")
    if not isinstance(data.get("observed_steps"), list):
        raise ValueError("missing observed steps")
    for step in data["observed_steps"]:
        if not isinstance(step, dict) or step.get("review_decision") not in (
            "confirmed", "rejected", "uncertain", "unreviewed"
        ):
            raise ValueError("invalid evidence step")
        if step.get("business_outcome") != "unknown":
            raise ValueError("cannot accept inferred business outcome")
    digest = data.get("knowledge_sha256", "")
    if not isinstance(digest, str) or len(digest) != 64 or any(
        c not in "0123456789abcdefABCDEF" for c in digest
    ):
        raise ValueError("missing source digest")
    return {
        "format": data["format"],
        "knowledge_id": data.get("knowledge_id"),
        "session_id": data.get("source_session_id"),
        "step_count": len(data["observed_steps"]),
        "candidate_file_sha256": hashlib.sha256(file.read_bytes()).hexdigest().upper(),
        "verification": "requires_independent_verification",
        "execution_allowed": False,
        "desktop_actions_executed": False,
    }
