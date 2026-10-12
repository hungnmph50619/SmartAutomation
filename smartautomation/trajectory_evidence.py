"""Detect contradictions between UFO agent actions and evaluator claims.

Read-only assessment. EvaluationAgent text is never considered independent proof
of a Word document being saved.
"""
from __future__ import annotations
import json
from pathlib import Path

MAX_BYTES = 8 * 1024 * 1024


def assess_trajectory(log_folder: Path) -> dict:
    response = log_folder / "response.log"
    evaluation = log_folder / "evaluation.log"
    result = {"trajectory_status": "unknown", "evaluator_claims_success": False,
              "evaluator_conflict": False, "document_verified": False}
    if not response.is_file() or response.is_symlink() or response.stat().st_size > MAX_BYTES:
        return result
    try:
        lines = response.read_text(encoding="utf-8", errors="replace").splitlines()
        steps = [json.loads(line) for line in lines if line.strip()]
        if not steps:
            return result
        actions = [a for step in steps for a in step.get("action", []) if isinstance(a, dict)]
        failures = [a for a in actions if isinstance(a.get("result"),dict)
                    and str(a["result"].get("status","")).lower() == "failure"]
        terminal = steps[-1]
        terminal_text = str(terminal.get("result","")).lower()
        no_action = terminal.get("function_call") == "no_action"
        completed_actions = [a for a in actions if a.get("function") not in ("no_action", None)
                             and isinstance(a.get("result"), dict)
                             and str(a["result"].get("status","")).lower() == "success"]
        result["trajectory_status"] = ("reported_failure" if no_action and
              any(x in terminal_text for x in ("task failed", "no document was created", "could not be located", "could not be launched"))
              else ("action_failures" if failures and not completed_actions else "requires_review"))
        if evaluation.is_file() and not evaluation.is_symlink() and evaluation.stat().st_size <= MAX_BYTES:
            evaluations = [json.loads(line) for line in evaluation.read_text(encoding="utf-8",errors="replace").splitlines() if line.strip()]
            result["evaluator_claims_success"] = any(str(item.get("complete","")).lower() == "yes" for item in evaluations)
        result["evaluator_conflict"] = result["evaluator_claims_success"] and result["trajectory_status"] in ("reported_failure", "action_failures")
        return result
    except (OSError, ValueError, TypeError, AttributeError):
        return result
