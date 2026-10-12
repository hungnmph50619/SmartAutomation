"""Local SQLite event timeline, never stores request text, screenshots or credentials."""
from __future__ import annotations

import json
from contextlib import contextmanager
import os
from pathlib import Path
import sqlite3
import threading
import time

ALLOWED_EVENTS = frozenset({
    "created", "running", "stopping", "stopped", "finished", "failed",
    "timeout", "heartbeat", "discovery", "no_progress",
})


class EventStore:
    def __init__(self, path: Path | None = None):
        self.path = path or Path(os.environ.get(
            "SMARTAUTOMATION_EVENTS_DB", str(Path.home() / ".smartautomation" / "events.db")
        ))
        self._lock = threading.RLock()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as conn:
            conn.execute("""CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                job_id TEXT NOT NULL,
                timestamp REAL NOT NULL,
                kind TEXT NOT NULL,
                metadata TEXT NOT NULL
            )""")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_events_job ON events(job_id,id)")
            conn.execute("""CREATE TABLE IF NOT EXISTS output_checkpoints (
                job_id TEXT PRIMARY KEY,
                timestamp REAL NOT NULL,
                output_status TEXT NOT NULL,
                recovery_reason TEXT NOT NULL
            )""")

    @contextmanager
    def _connect(self):
        connection = sqlite3.connect(self.path, timeout=10)
        try:
            with connection:
                yield connection
        finally:
            connection.close()

    def emit(self, job_id: str, kind: str, metadata: dict | None = None) -> None:
        if kind not in ALLOWED_EVENTS:
            raise ValueError("Unsupported event kind")
        safe = {}
        for key, value in (metadata or {}).items():
            if key in {"returncode", "elapsed_seconds", "step_count", "reason_code"} and isinstance(value, (int, float, str)):
                safe[key] = value
        with self._lock, self._connect() as conn:
            conn.execute(
                "INSERT INTO events(job_id,timestamp,kind,metadata) VALUES (?,?,?,?)",
                (job_id, time.time(), kind, json.dumps(safe)),
            )

    def list_events(self, job_id: str, limit: int = 100) -> list[dict]:
        with self._lock, self._connect() as conn:
            rows = conn.execute(
                "SELECT timestamp,kind,metadata FROM events WHERE job_id=? ORDER BY id DESC LIMIT ?",
                (job_id, min(max(limit, 1), 500)),
            ).fetchall()
        return [{"timestamp": t, "kind": k, "metadata": json.loads(m)} for t, k, m in reversed(rows)]

    def save_output_checkpoint(self, job_id: str, output_status: str, recovery_reason: str) -> None:
        """Persist only bounded evidence codes, never file paths or request content."""
        allowed_statuses = {"verified", "content_not_specified", "path_only",
                            "failed", "no_explicit_target"}
        allowed_reasons = {"output_verified", "target_unknown", "target_missing_or_stale",
                           "invalid_output_package", "content_mismatch",
                           "insufficient_output_evidence"}
        if not isinstance(job_id, str) or not (1 <= len(job_id) <= 80):
            raise ValueError("Invalid checkpoint job ID")
        if output_status not in allowed_statuses or recovery_reason not in allowed_reasons:
            raise ValueError("Unsupported checkpoint evidence code")
        with self._lock, self._connect() as conn:
            conn.execute(
                """INSERT INTO output_checkpoints(job_id,timestamp,output_status,recovery_reason)
                   VALUES(?,?,?,?)
                   ON CONFLICT(job_id) DO UPDATE SET timestamp=excluded.timestamp,
                   output_status=excluded.output_status, recovery_reason=excluded.recovery_reason""",
                (job_id, time.time(), output_status, recovery_reason),
            )

    def load_output_checkpoint(self, job_id: str) -> dict | None:
        """A checkpoint is evidence for review, NOT permission to resume UFO."""
        with self._lock, self._connect() as conn:
            row = conn.execute(
                "SELECT timestamp,output_status,recovery_reason FROM output_checkpoints WHERE job_id=?",
                (job_id,),
            ).fetchone()
        if row is None:
            return None
        return {"job_id": job_id, "timestamp": row[0], "output_status": row[1],
                "recovery_reason": row[2], "can_auto_resume": False}
