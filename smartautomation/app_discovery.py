"""Read-only, generic discovery of Windows Start Menu applications.

No arbitrary command execution and no bypass of UFO launch restrictions.
Candidates require user confirmation and an approved launch pathway.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys


def discover_start_apps(timeout: int = 12) -> list[dict[str, str]]:
    if sys.platform != "win32":
        return []
    script = (
        "$ErrorActionPreference='Stop';"
        "$apps=Get-StartApps | Select-Object Name,AppID;"
        "ConvertTo-Json -InputObject @($apps) -Compress -Depth 3"
    )
    result = subprocess.run(
        ["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", script],
        capture_output=True, text=True, timeout=timeout, check=True,
        encoding="utf-8", errors="replace",
    )
    data = json.loads(result.stdout)
    if isinstance(data, dict):
        data = [data]
    return [
        {"name": str(item["Name"]), "app_id": str(item["AppID"]), "source": "windows_start"}
        for item in data if isinstance(item, dict) and item.get("Name") and item.get("AppID")
    ]


def find_app(query: str, apps: list[dict[str, str]]) -> list[dict[str, str]]:
    if not isinstance(query, str) or not query.strip():
        return []
    needle = query.casefold().strip()
    return sorted(
        (a for a in apps if needle in a["name"].casefold()),
        key=lambda a: (a["name"].casefold() != needle, len(a["name"]), a["name"].casefold()),
    )[:20]
