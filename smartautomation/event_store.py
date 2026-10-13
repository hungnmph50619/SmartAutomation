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
            conn.execute("""CREATE TABLE IF NOT EXISTS step_checkpoints (
                job_id TEXT NOT NULL,
                step_id TEXT NOT NULL,
                timestamp REAL NOT NULL,
                verification_status TEXT NOT NULL,
                evidence_code TEXT NOT NULL,
                PRIMARY KEY (job_id,step_id)
            )""")
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

    def save_step_checkpoint(self, job_id: str, step_id: str, status: str, evidence_code: str) -> None:
        """Store externally verified step evidence, never inferred UFO actions.

        A verified step cannot be silently downgraded. A later change in UI
        context requires a separate revalidation protocol, not blind replay.
        """
        allowed = {"verified", "failed", "unknown"}
        codes = {"content_matched", "target_fresh", "package_valid",
                 "verification_failed", "evidence_missing"}
        if not isinstance(job_id, str) or not 1 <= len(job_id) <= 80:
            raise ValueError("Invalid job ID")
        if not isinstance(step_id, str) or not 1 <= len(step_id) <= 80 or not all(
            c.isascii() and (c.isalnum() or c in "_-") for c in step_id
        ):
            raise ValueError("Invalid step ID")
        if status not in allowed or evidence_code not in codes:
            raise ValueError("Unsupported evidence")
        if (status == "verified") != (evidence_code in {"content_matched", "target_fresh", "package_valid"}):
            raise ValueError("Evidence does not support verification status")
        with self._lock, self._connect() as conn:
            prior = conn.execute(
                "SELECT verification_status FROM step_checkpoints WHERE job_id=? AND step_id=?",
                (job_id, step_id),
            ).fetchone()
            if prior and prior[0] == "verified" and status != "verified":
                raise ValueError("Verified step requires explicit revalidation")
            conn.execute(
                """INSERT INTO step_checkpoints(job_id,step_id,timestamp,verification_status,evidence_code)
                   VALUES(?,?,?,?,?)
                   ON CONFLICT(job_id,step_id) DO UPDATE SET timestamp=excluded.timestamp,
                   verification_status=excluded.verification_status,evidence_code=excluded.evidence_code""",
                (job_id, step_id, time.time(), status, evidence_code),
            )

    def list_step_checkpoints(self, job_id: str) -> list[dict]:
        """Read-only evidence; never grants permission to automatically resume."""
        with self._lock, self._connect() as conn:
            rows = conn.execute(
                """SELECT step_id,timestamp,verification_status,evidence_code
                   FROM step_checkpoints WHERE job_id=? ORDER BY step_id""",
                (job_id,),
            ).fetchall()
        return [
            {"step_id": step_id, "timestamp": timestamp, "status": status,
             "evidence_code": code, "can_auto_resume": False}
            for step_id, timestamp, status, code in rows
        ]
