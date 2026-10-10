"""Conservative, advisory failure circuit breaker for UFO log evidence.

Signals only; it does not interrupt UFO or alter commands. A breaker may
become actionable only when UFO exposes an approved per-action hook.
"""
from __future__ import annotations
from collections import deque
import re

_PATTERNS = {
    "launch_not_found": re.compile(r"(?i)(file not found|not recognized as (?:an|a) (?:internal|external) command|no such file or directory)"),
    "launch_blocked": re.compile(r"(?i)(command blocked by security policy|blocked by security policies)"),
    "access_denied": re.compile(r"(?i)(access denied|permission denied)"),
}
# A new physical log line is weak evidence of a separate attempt. Alert only.
MIN_MATCHING_LINES = 3


def detect_repetition(log_tail: str, threshold: int = MIN_MATCHING_LINES) -> dict:
    if threshold < 2:
        raise ValueError("threshold must be >= 2")
    recent: deque[str] = deque(maxlen=threshold)
    for line in log_tail.splitlines():
        # Avoid double-counting a single line that names several errors.
        category = next((key for key, pattern in _PATTERNS.items() if pattern.search(line)), None)
        if category is None:
            continue
        recent.append(category)
        if len(recent) == threshold and len(set(recent)) == 1:
            return {"state": "suspected_repeat", "reason_code": category,
                    "count": threshold, "action": "review_and_replan"}
    return {"state": "clear", "reason_code": None, "count": 0, "action": None}
