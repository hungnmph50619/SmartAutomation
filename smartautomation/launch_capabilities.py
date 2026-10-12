"""Read-only app capability hints to help UFO plan a generic Windows launch.

This module NEVER launches apps: Microsoft UFO remains the only desktop actor.
OS-discovered identities are evidence, not instructions or shell commands.
"""
from __future__ import annotations

import re
from collections.abc import Callable

from smartautomation.app_discovery import discover_start_apps


def discover_launch_context(
    request: str,
    discovery: Callable[[], list[dict[str, str]]] = discover_start_apps,
    *,
    max_candidates: int = 5,
) -> list[dict[str, str]]:
    """Match only literal application name tokens in the user request."""
    if not request.strip():
        return []
    try:
        apps = discovery()
    except (OSError, ValueError, RuntimeError, TimeoutError):
        return []
    if not isinstance(apps, list):
        return []
    text = request.casefold()
    matches = []
    for app in apps:
        if not isinstance(app, dict):
            continue
        name = app.get("name")
        appid = app.get("app_id")
        if not isinstance(name, str) or not isinstance(appid, str):
            continue
        name = name.strip()
        if not (3 <= len(name) <= 70 and 1 <= len(appid) <= 200):
            continue
        # Exact known app name, not a vague two-letter substring or executable guess.
        if not re.search(r"(?<!\w)" + re.escape(name.casefold()) + r"(?!\w)", text):
            continue
        # Never inject raw untrusted AppID into model instructions.
        if any(ord(ch) < 32 for ch in name + appid):
            continue
        matches.append({"name": name, "source": "windows_start", "available": True})
        if len(matches) >= max_candidates:
            break
    return matches


def guide_application_launch(request: str, candidates: list[dict[str, str]], *, max_length: int = 2000) -> str:
    """Append bounded generic UI launch strategy if it fits UFO CLI input budget."""
    guidance = (
        "Neu chua tim thay cua so ung dung dich, KHONG ket luan that bai hay hoan thanh ngay. "
        "Hay dung cac cong cu UFO de tim ung dung qua Windows Start Menu, mo no qua UI hop le, "
        "doi cua so xuat hien, quan sat lai va chon bang HostUIExecutor truoc khi dung AppUIExecutor. "
        "Khong doan ten lenh shell, khong vuot qua policy; neu mo that bai, thu con duong UI khac, "
        "xac minh tung buoc va bao that bai neu khong co bang chung. "
    )
    if candidates:
        names = ", ".join(c["name"] for c in candidates[:5])
        guidance += "Windows Start Apps phat hien ten ung dung co trong yeu cau (chi la goi y): " + names + ". "
    if len(request) + len(guidance) + 1 > max_length:
        return request
    return guidance + "\n" + request
