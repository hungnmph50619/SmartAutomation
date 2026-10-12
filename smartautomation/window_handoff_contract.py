"""Conservative verifier for UFO HostAgent window selection results.

This is a contract used to validate a future upstream handoff integration.
It never guesses a window from a process name or a model statement.
"""
from __future__ import annotations
from collections.abc import Mapping


def verify_window_selection(function_name: str, result: object, expected_target_id: str | None) -> dict:
    base = {"handoff_allowed": False, "reason": "unverified_window_selection"}
    if function_name != "select_application_window":
        return {**base, "reason": "wrong_host_action"}
    if not expected_target_id or not expected_target_id.strip():
        return {**base, "reason": "missing_target_identity"}
    if not isinstance(result, list) or not result:
        return {**base, "reason": "missing_selection_result"}
    item = result[0]
    status = item.get("status") if isinstance(item, Mapping) else getattr(item, "status", None)
    payload = item.get("result") if isinstance(item, Mapping) else getattr(item, "result", None)
    status = str(getattr(status, "value", status)).lower()
    if status not in ("success", "resultstatus.success"):
        return {**base, "reason": "selection_command_failed"}
    if not isinstance(payload, Mapping):
        return {**base, "reason": "missing_window_payload"}
    window = payload.get("window_info")
    if not isinstance(window, Mapping) or not str(payload.get("root_name") or "").strip():
        return {**base, "reason": "missing_selected_window"}
    return {"handoff_allowed": True, "reason": "host_window_selection_verified"}
