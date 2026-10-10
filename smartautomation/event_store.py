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
