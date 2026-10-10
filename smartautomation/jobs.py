"""Single-job Windows UFO process manager.

No application automation is implemented here. Only the official UFO CLI executes
desktop operations. Start is disabled by default and requires explicit consent.
"""
from __future__ import annotations

import os
import subprocess
import sys
import threading
import time
import uuid
from dataclasses import dataclass, field

from smartautomation.ufo import UfoConfig, build_command

MAX_SECONDS = 900


@dataclass
class Job:
    id: str
    state: str
    started_at: float
    process: subprocess.Popen | None = field(default=None, repr=False)
    detail: str = ""
    returncode: int | None = None
    stop_requested: bool = False


class JobManager:
    def __init__(self):
        self._lock = threading.RLock()
        self._job: Job | None = None

    def snapshot(self) -> dict:
        with self._lock:
            job = self._job
            if job is None:
                return {"state": "idle", "job_id": None, "detail": "No task"}
            return {
                "state": job.state,
                "job_id": job.id,
                "detail": job.detail,
                "returncode": job.returncode,
                "started_at": job.started_at,
            }

    def start(self, request: str, confirmed: bool) -> dict:
        if not confirmed:
            raise PermissionError("Explicit confirmation is required")
        if os.environ.get("SMARTAUTOMATION_EXECUTION_ENABLED", "").lower() != "true":
            raise PermissionError("Desktop execution is disabled by default")
        if sys.platform != "win32":
            raise OSError("Windows desktop session required")
        if not 1 <= len(request.strip()) <= 2000:
            raise ValueError("Request length must be 1..2000")
        config = UfoConfig.from_environment()
        if config.validate():
            raise RuntimeError("UFO source is not configured")
        if not os.path.isfile(config.python):
            raise RuntimeError("Configured UFO Python executable not found")

        with self._lock:
            if self._job and self._job.state in {"starting", "running", "stopping"}:
                raise RuntimeError("Another desktop task is already running")
            job = Job(str(uuid.uuid4()), "starting", time.time())
            self._job = job
            command = build_command(config, "smartautomation-" + job.id[:8], request.strip())
            try:
                # UFO owns all OS interactions. Never use a shell or log model output here.
                job.process = subprocess.Popen(
                    command,
                    cwd=str(config.root),
                    stdin=subprocess.DEVNULL,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,
                )
            except Exception:
                self._job = None
                raise
            job.state = "running"
            job.detail = "UFO running; details remain in UFO's local logs"
            thread = threading.Thread(target=self._watch, args=(job,), daemon=True)
            thread.start()
            return self.snapshot()

    def _watch(self, job: Job):
        assert job.process is not None
        try:
            rc = job.process.wait(timeout=MAX_SECONDS)
        except subprocess.TimeoutExpired:
            with self._lock:
                job.stop_requested = True
                job.state = "stopping"
                job.detail = "Time limit reached: stopping UFO"
            self._terminate_tree(job.process)
            rc = job.process.wait()
        with self._lock:
            job.returncode = rc
            job.state = "stopped" if job.stop_requested else ("finished" if rc == 0 else "failed")
            job.detail = "UFO process exited; check UFO logs for independently verified outcome"

    @staticmethod
    def _terminate_tree(process: subprocess.Popen):
        if process.poll() is not None:
            return
        if sys.platform == "win32":
            subprocess.run(
                ["taskkill", "/PID", str(process.pid), "/T", "/F"],
                capture_output=True,
                timeout=15,
                check=False,
            )
        else:
            process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()

    def stop(self, job_id: str) -> dict:
        with self._lock:
            job = self._job
            if not job or job.id != job_id:
                raise LookupError("Task not found")
            if job.state not in {"starting", "running", "stopping"}:
                return self.snapshot()
            job.stop_requested = True
            job.state = "stopping"
            job.detail = "Stop requested; terminating UFO process tree"
            process = job.process
        if process is not None:
            self._terminate_tree(process)
        return self.snapshot()


manager = JobManager()
