"""Separate UFO process health from evidence of a completed desktop task.

This does not infer successful Word file creation from an agent's prose.
"""
from __future__ import annotations

from pathlib import Path


def classify_process_outcome(returncode: int, stderr_path: Path | None = None) -> dict:
    text = ""
    if stderr_path is not None and stderr_path.is_file() and not stderr_path.is_symlink():
        with stderr_path.open("rb") as stream:
            stream.seek(max(0, stderr_path.stat().st_size - 128_000))
            text = stream.read().decode("utf-8", errors="replace")
    if returncode != 0:
        reason = "unicode_output_error" if "UnicodeEncodeError" in text else "ufo_process_nonzero_exit"
        return {"process_status": "failed", "task_verified": False,
                "reason_code": reason, "verification_status": "not_verified"}
    return {"process_status": "exited_zero", "task_verified": False,
            "reason_code": "requires_independent_verification",
            "verification_status": "not_verified"}
