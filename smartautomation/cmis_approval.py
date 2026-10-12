"""Independent, digest-bound CMIS human approval; approval never authorizes desktop execution."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
from uuid import UUID
from smartautomation.cmis_candidate import inspect_candidate


def approve_evidence(candidate_path: str | Path, output_path: str | Path,
                     reviewer: str, rationale: str) -> dict:
    candidate = Path(candidate_path)
    verdict = inspect_candidate(candidate)
    if not 1 <= len(reviewer.strip()) <= 120 or not 1 <= len(rationale.strip()) <= 2000:
        raise ValueError("reviewer and rationale are required")
    data = json.loads(candidate.read_text(encoding="utf-8"))
    steps = data["observed_steps"]
    if not steps or any(step["review_decision"] != "confirmed" for step in steps):
        raise ValueError("all steps must be explicitly confirmed")
    knowledge_id = str(UUID(data["knowledge_id"]))
    session_id = str(UUID(data["source_session_id"]))
    payload = {
        "schema_version": 1,
        "format": "cmis_human_evidence_approval",
        "knowledge_id": knowledge_id,
        "source_session_id": session_id,
        "candidate_sha256": verdict["candidate_file_sha256"],
        "reviewer": reviewer.strip(),
        "rationale": rationale.strip(),
        "approval_state": "evidence_approved_only",
        "execution_allowed": False,
        "independent_runtime_verification_required": True,
    }
    dest = Path(output_path)
    if dest.exists():
        raise FileExistsError("approval cannot overwrite an existing decision")
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return payload


def inspect_approval(candidate_path: str | Path, approval_path: str | Path) -> dict:
    verdict = inspect_candidate(candidate_path)
    approval = json.loads(Path(approval_path).read_text(encoding="utf-8"))
    if (approval.get("format") != "cmis_human_evidence_approval"
            or approval.get("schema_version") != 1
            or approval.get("candidate_sha256") != verdict["candidate_file_sha256"]
            or approval.get("knowledge_id") != verdict["knowledge_id"]
            or approval.get("source_session_id") != verdict["session_id"]
            or approval.get("approval_state") != "evidence_approved_only"
            or approval.get("execution_allowed") is not False
            or approval.get("independent_runtime_verification_required") is not True):
        raise ValueError("approval does not match the immutable candidate")
    return {"evidence_approved": True, "execution_allowed": False,
            "desktop_actions_executed": False, "candidate_sha256": verdict["candidate_file_sha256"]}
