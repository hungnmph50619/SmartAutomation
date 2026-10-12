"""Bounded, read-only detection of repeated UFO UI initialization failures.

Does not perform Windows automation and does not claim it can repair UFO's
HostAgent->AppAgent handoff. Only inspects the current task's own response log.
"""
from __future__ import annotations

from pathlib import Path

ERROR_MARKER = b"ui state not initialized"
DEFAULT_THRESHOLD = 3
MAX_TAIL_BYTES = 4 * 1024 * 1024


def detect_uninitialized_ui_loop(folder: Path, threshold: int = DEFAULT_THRESHOLD) -> dict:
    response = folder / "response.log"
    report = {"detected": False, "reason_code": None, "occurrences": 0}
    if not 2 <= threshold <= 20 or not response.is_file() or response.is_symlink():
        return report
    try:
        with response.open("rb") as stream:
            stream.seek(max(0, response.stat().st_size - MAX_TAIL_BYTES))
            content = stream.read().lower()
    except OSError:
        return report
    occurrences = content.count(ERROR_MARKER)
    report["occurrences"] = occurrences
    if occurrences >= threshold:
        report.update({"detected": True, "reason_code": "repeated_ui_state_not_initialized"})
    return report
