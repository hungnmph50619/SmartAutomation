"""Conservative adapter for existing UFO EvaluationAgent evidence.

EvaluationAgent opinions are advisory. Independent verification is required
before any task can be marked as verified success.
"""
from __future__ import annotations

import json
from pathlib import Path

from .trajectory_evidence import assess_trajectory

MAX_LOG_BYTES = 8 * 1024 * 1024


def classify_evaluation(log_folder: Path, *, independent_success: bool = False) -> dict:
    """Return a review recommendation; never grant execution approval."""
    trajectory = assess_trajectory(log_folder)
    evaluator = "unknown"
    evaluation_path = log_folder / "evaluation.log"
    if evaluation_path.is_file() and not evaluation_path.is_symlink() and evaluation_path.stat().st_size <= MAX_LOG_BYTES:
        try:
            rows = [json.loads(line) for line in evaluation_path.read_text(encoding="utf-8").splitlines() if line.strip()]
            if rows:
                raw = str(rows[-1].get("complete", "unsure")).strip().lower()
                evaluator = raw if raw in {"yes", "no", "unsure"} else "unknown"
        except (OSError, ValueError, AttributeError, TypeError):
            evaluator = "unknown"

    failure = trajectory["trajectory_status"] in {"reported_failure", "action_failures"}
    contradiction = bool(trajectory["evaluator_conflict"])
    if failure or evaluator == "no":
        status = "failure_evidence"
        reason = "The evaluator or execution log reports failure; inspect the actual result."
    elif independent_success and evaluator == "yes" and not contradiction:
        status = "verified_success"
        reason = "Independent outcome evidence agrees with the evaluator."
    else:
        status = "requires_review"
        reason = "The evaluator opinion or recorded actions alone do not verify task completion."
    return {
        "status": status,
        "reason": reason,
        "evaluator_complete": evaluator,
        "trajectory_status": trajectory["trajectory_status"],
        "evaluator_conflict": contradiction,
        "independent_success": bool(independent_success),
        "execution_allowed": False,
    }
