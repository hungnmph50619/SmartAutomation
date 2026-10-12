"""Read-only generic inventory of visible desktop application processes.

No window focus, application launch, or automation takes place here.
"""
from __future__ import annotations
import json
import subprocess
import sys


def discover_visible_processes(timeout: int = 6) -> list[str]:
    if sys.platform != "win32":
        return []
    script = (
        "$ErrorActionPreference='Stop';"
        "$p=Get-Process | Where-Object {$_.MainWindowHandle -ne 0 -and $_.MainWindowTitle};"
        "ConvertTo-Json -InputObject @($p | Select-Object -ExpandProperty ProcessName) -Compress"
    )
    try:
        result = subprocess.run(
            ["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", script],
            capture_output=True, text=True, encoding="utf-8", errors="replace",
            timeout=timeout, check=True,
        )
        data = json.loads(result.stdout)
    except (OSError, subprocess.TimeoutExpired, subprocess.CalledProcessError, ValueError):
        return []
    if isinstance(data, str):
        data = [data]
    if not isinstance(data, list):
        return []
    # Process names are untrusted data. Only short, ordinary executable names
    # are retained, and no window titles or document names are sent to the LLM.
    return sorted({s for s in data if isinstance(s, str) and 1 <= len(s) <= 60
                   and all(ch.isascii() and (ch.isalnum() or ch in "._-") for ch in s)})[:40]


def guide_existing_window(request: str, processes: list[str], max_length: int = 2000) -> str:
    """Add general, bounded tool-selection advice, never an OS command."""
    guidance = (
        "Truoc khi mo ung dung hay chay shell, quan sat cac cua so hien co "
        "bang UICollector/get_desktop_app_info va chon cua so dung qua "
        "HostUIExecutor/select_application_window. Chi mo ung dung neu da "
        "xac minh khong co cua so phu hop; neu lenh bi chan, khong lap lai "
        "hoac vuot qua chinh sach. Dung AppUIExecutor cho UI, "
        "kiem tra ket qua thuc te. "
    )
    if processes:
        guidance += "Tien trinh co cua so (goi y, KHONG phai bang chung cua so muc tieu): " + ", ".join(processes[:15]) + ". "
    available = max_length - len(request) - 2
    if available < len(guidance):
        return request
    return guidance + "\n" + request
