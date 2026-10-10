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
from smartautomation.event_store import EventStore
from smartautomation.telemetry import trace_phase

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
    request: str = field(default="", repr=False)


class JobManager:
    def __init__(self):
        self._lock = threading.RLock()
        self.events = EventStore()
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
            job = Job(str(uuid.uuid4()), "starting", time.time(), request=request.strip())
            self._job = job
            self.events.emit(job.id, "created")
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
                self.events.emit(job.id, "failed", {"reason_code": "spawn_failed"})
                self._job = None
                raise
            job.state = "running"
            self.events.emit(job.id, "running")
            job.detail = "UFO running; details remain in UFO's local logs"
            thread = threading.Thread(target=self._watch, args=(job,), daemon=True)
            thread.start()
            return self.snapshot()

    def _watch(self, job: Job):
        assert job.process is not None
        try:
            with trace_phase("ufo.process.wait", job_id=job.id, phase="running"):
                rc = job.process.wait(timeout=MAX_SECONDS)
        except subprocess.TimeoutExpired:
            with self._lock:
                job.stop_requested = True
                job.state = "stopping"
                self.events.emit(job.id, "timeout")
                job.detail = "Time limit reached: stopping UFO"
            self._terminate_tree(job.process)
            rc = job.process.wait()
        with self._lock:
            job.returncode = rc
            job.state = "stopped" if job.stop_requested else ("finished" if rc == 0 else "failed")
            job.detail = "UFO process exited; check UFO logs for independently verified outcome"
            self.events.emit(job.id, job.state, {"returncode": rc})

    def retry_from_failed(self, job_id: str, app_name: str, confirmed: bool) -> dict:
        """Start a NEW approved UFO job, never execute desktop commands here."""
        if not confirmed:
            raise PermissionError("Separate confirmation required for retry")
        if not app_name or len(app_name) > 100 or any(ch in app_name for ch in "\\r\\n\\x00"):
            raise ValueError("Invalid application name")
        with self._lock:
            previous = self._job
            if previous is None or previous.id != job_id:
                raise LookupError("Previous task not found")
            if previous.state != "failed":
                raise RuntimeError("Recovery retry allowed only after a failed task")
            original = previous.request
            if not original:
                raise RuntimeError("Original task request unavailable")
            instruction = (
                "Lưu ý phục hồi ứng dụng: thử mở ứng dụng qua giao diện Windows Start Menu, "
                "không lặp lại lệnh shell từng thất bại, không vô hiệu hóa chính sách bảo mật; "
                "xác minh cửa sổ đã mở trước khi thao tác. "
                "Ứng dụng được xác nhận: " + app_name + ". "
            )
            if len(instruction + original) > 2000:
                raise ValueError("Task request too long for safe retry")
            # start() takes the same RLock and again enforces explicit opt-in.
            return self.start(instruction + original, confirmed=True)

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
            self.events.emit(job.id, "stopping")
            job.detail = "Stop requested; terminating UFO process tree"
            process = job.process
        if process is not None:
            self._terminate_tree(process)
        return self.snapshot()


manager = JobManager()
