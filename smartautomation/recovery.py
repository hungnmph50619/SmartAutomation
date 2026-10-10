"""Safe recovery recommendations. Never executes or modifies UFO."""
from __future__ import annotations
from smartautomation.app_discovery import find_app


def recommend_apps(query: str, apps: list[dict], failure: dict) -> dict:
    if failure.get("state") != "suspected_repeat":
        return {"status": "not_needed", "candidates": [], "next_step": None}
    code = failure.get("reason_code")
    if code not in {"launch_not_found", "launch_blocked"}:
        return {"status": "manual_review", "candidates": [], "next_step": "inspect_ufo_logs"}
    if code == "launch_blocked":
        # A different application lookup must never be mistaken for permission to
        # override the upstream UFO command security policy.
        return {"status": "security_policy_review", "candidates": [], "next_step": "review_ufo_policy"}
    candidates = find_app(query, apps) if query.strip() else []
    return {
        "status": "candidate_found" if candidates else "manual_review",
        "candidates": candidates[:5],
        "next_step": "confirm_application_then_retry_via_ufo" if candidates else "inspect_application_installation",
    }


def recovery_instructions(candidate: dict, failure: dict) -> dict:
    """Return a user-reviewable instruction, not a command to the operating system.

    AppIDs are discovery evidence, never shell commands. A new UFO job needs
    explicit opt-in through the existing job-start route.
    """
    if failure.get("state") != "suspected_repeat" or failure.get("reason_code") != "launch_not_found":
        return {"status": "not_allowed", "instruction": None}
    name = candidate.get("name", "")
    app_id = candidate.get("app_id", "")
    if not isinstance(name, str) or not isinstance(app_id, str):
        return {"status": "not_allowed", "instruction": None}
    if not (1 <= len(name) <= 100 and 1 <= len(app_id) <= 250):
        return {"status": "not_allowed", "instruction": None}
    # App discovery values can contain misleading text: only pass inert
    # identity to the user, never interpolate uncontrolled values into a prompt.
    return {
        "status": "review_required",
        "instruction": (
            "Mở ứng dụng đã được người dùng xác nhận thông qua giao diện Windows Start Menu. "
            "Không thử lại lệnh shell đã thất bại, không bỏ qua chính sách bảo mật. "
            "Sau khi mở, xác minh cửa sổ ứng dụng đúng trước khi thực hiện công việc."
        ),
        "application": {"name": name, "app_id": app_id},
    }
