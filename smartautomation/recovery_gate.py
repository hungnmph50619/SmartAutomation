"""Read-only gate evaluating whether a UFO run needs manual review.

No live UFO action is intercepted. A future in-process middleware integration
must separately prove hook compatibility before enabling action-level blocking.
"""
from __future__ import annotations
from dataclasses import dataclass


@dataclass(frozen=True)
class GateDecision:
    state: str
    reason: str
    can_auto_resume: bool = False


def evaluate_gate(progress: dict, job_state: str) -> GateDecision:
    if job_state not in {"running", "starting", "stopping"}:
        return GateDecision("inactive", "job_not_running")
    circuit = progress.get("circuit_breaker") or {}
    if circuit.get("state") == "suspected_repeat":
        return GateDecision("review", str(circuit.get("reason_code") or "repeated_failure"))
    if progress.get("warning") == "no_recent_evidence":
        return GateDecision("observe", "no_recent_evidence_not_proven_hang")
    return GateDecision("ok", "no_confirmed_repeat")
