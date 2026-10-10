"""Read-only progress sensor for UFO's existing per-task log directory.

This does NOT drive mouse or keyboard, and deliberately does not turn missing
screen captures into evidence that an application has hung.
"""
from __future__ import annotations

from pathlib import Path
import re
import time

TASK_RE = re.compile(r"^smartautomation-[0-9a-f]{8}$")
IMAGE_RE = re.compile(r"^action_[A-Za-z0-9_]+\.png$")
from smartautomation.failure_breaker import detect_repetition
MAX_TAIL = 24000


def summarize(root: Path, task: str, now: float | None = None) -> dict:
    if not TASK_RE.fullmatch(task):
        raise ValueError("Invalid task identifier")
    directory = root / "logs" / task
    if not directory.is_dir() or directory.is_symlink():
        return {"step_count": 0, "latest_image": None, "last_activity": None,
                "seconds_since_activity": None, "warning": None,
                "circuit_breaker": detect_repetition("")}
    files = [p for p in directory.iterdir() if p.is_file() and not p.is_symlink()]
    images = [p for p in files if IMAGE_RE.fullmatch(p.name)]
    latest = max(images, key=lambda p: p.stat().st_mtime, default=None)
    relevant = [p for p in files if p.name in {"response.log","request.log","output.md","evaluation.log"} or IMAGE_RE.fullmatch(p.name)]
    last = max((p.stat().st_mtime for p in relevant), default=None)
    age = max(0, int((now if now is not None else time.time()) - last)) if last is not None else None
    warning = "no_recent_evidence" if age is not None and age >= 60 else None

    circuit = detect_repetition("")
    response = directory / "response.log"
    if response.is_file() and response.stat().st_size <= 8_000_000:
        with response.open("rb") as handle:
            handle.seek(max(0, response.stat().st_size - MAX_TAIL))
            raw = handle.read(MAX_TAIL)
        text = raw.decode("utf-8", errors="replace")
        circuit = detect_repetition(text)

    return {
        "step_count": len(images),
        "latest_image": latest.name if latest else None,
        "last_activity": last,
        "seconds_since_activity": age,
        "warning": "repeated_launch_error" if circuit["state"] == "suspected_repeat" else warning,
        "circuit_breaker": circuit,
    }
