"""Create safe, read-only recovery recommendations from UFO failure evidence.

This module never launches programs or modifies upstream UFO configuration.
"""
from __future__ import annotations
from smartautomation.app_discovery import find_app


def recommend_apps(query: str, apps: list[dict], failure: dict) -> dict:
    if failure.get("state") != "suspected_repeat":
        return {"status": "not_needed", "candidates": [], "next_step": None}
    code = failure.get("reason_code")
    if code not in {"launch_not_found", "launch_blocked"}:
        return {"status": "manual_review", "candidates": [], "next_step": "inspect_ufo_logs"}
    candidates = find_app(query, apps) if query.strip() else []
    return {
        "status": "candidate_found" if candidates else "manual_review",
        "candidates": candidates[:5],
        "next_step": "confirm_application_then_retry_via_ufo" if candidates else "inspect_application_installation",
    }
