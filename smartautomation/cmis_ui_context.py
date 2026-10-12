"""Read-only UI control-type matching: never reconstruct click targets."""
from __future__ import annotations


def compare_ui_hierarchy(recorded: dict, observed: dict) -> dict:
    fields = ("ui_control_type", "ui_parent_control_type", "ui_grandparent_control_type")
    if not isinstance(recorded, dict) or not isinstance(observed, dict):
        raise ValueError("UI context objects required")
    if not all(isinstance(recorded.get(k), str) and recorded[k].strip()
               and isinstance(observed.get(k), str) and observed[k].strip()
               for k in fields[:1]):
        return {"status": "insufficient_ui_context", "matches": False,
                "action_suggestion": None, "execution_allowed": False}
    comparable = [k for k in fields if isinstance(recorded.get(k), str)
                  and recorded[k].strip() and isinstance(observed.get(k), str)
                  and observed[k].strip()]
    matched = all(recorded[k].casefold() == observed[k].casefold() for k in comparable)
    return {"status": "control_type_evidence_only" if matched else "different_ui_context",
            "matches": matched, "compared_fields": comparable,
            "action_suggestion": None, "execution_allowed": False}
