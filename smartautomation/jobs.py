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
from pathlib import Path

from smartautomation.ufo import UfoConfig, build_command
from smartautomation.event_store import EventStore
from smartautomation.telemetry import trace_phase
from smartautomation.outcome_evidence import classify_process_outcome
from smartautomation.trajectory_evidence import assess_trajectory
from smartautomation.window_discovery import discover_visible_processes, guide_existing_window
from smartautomation.handoff_guard import detect_uninitialized_ui_loop
from smartautomation.launch_capabilities import discover_launch_context, guide_application_launch
from smartautomation.save_target import requested_save_target, assess_saved_target, guide_save_target, snapshot_saved_target

MAX_SECONDS = 900


def ufo_process_environment(base: dict[str, str] | None = None) -> dict[str, str]:
    """Set UTF-8 child output without changing the parent or UFO logic."""
    env = dict(os.environ if base is None else base)
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONUTF8"] = "1"
    return env



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
    save_target: Path | None = field(default=None, repr=False)
    save_target_before: tuple[int, int, int] | None = field(default=None, repr=False)


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
            job = Job(str(uuid.uuid4()), "starting", time.time(), request=request.strip(),
                      save_target=requested_save_target(request.strip()))
            job.save_target_before = snapshot_saved_target(job.save_target)
            self._job = job
            self.events.emit(job.id, "created")
            # Generic read-only hints; UFO remains the sole desktop actor.
            # This is advisory until upstream action selection is verified live.
            guided_request = guide_existing_window(request.strip(), discover_visible_processes())
            guided_request = guide_application_launch(
                guided_request, discover_launch_context(request.strip())
            )
            guided_request = guide_save_target(guided_request, job.save_target)
            command = build_command(config, "smartautomation-" + job.id[:8], guided_request)
            try:
                log_dir = Path(os.environ.get('SMARTAUTOMATION_PROCESS_LOGS', str(Path.home() / '.smartautomation' / 'process_logs')))
                log_dir.mkdir(parents=True, exist_ok=True)
                log_base = 'smartautomation-' + job.id[:8]
                # UFO owns all OS interactions. Never use a shell or log model output here.
                with open(log_dir / (log_base + '.stdout.log'), 'ab') as out, open(log_dir / (log_base + '.stderr.log'), 'ab') as err:
                    job.process = subprocess.Popen(
                        command,
                        cwd=str(config.root),
                        stdin=subprocess.DEVNULL,
                        stdout=out,
                        stderr=err,
                        env=ufo_process_environment(),
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
        guard_reason = None
        deadline = time.monotonic() + MAX_SECONDS
        with trace_phase("ufo.process.wait", job_id=job.id, phase="running"):
            while True:
                try:
                    rc = job.process.wait(timeout=min(3, max(0.1, deadline - time.monotonic())))
                    break
                except subprocess.TimeoutExpired:
                    folder = UfoConfig.from_environment().root / "logs" / ("smartautomation-" + job.id[:8])
                    guard = detect_uninitialized_ui_loop(folder)
                    if guard["detected"]:
                        guard_reason = guard["reason_code"]
                        self.events.emit(job.id, "handoff_guard_triggered",
                                         {"reason_code": guard_reason, "occurrences": guard["occurrences"]})
                        self._terminate_tree(job.process)
                        rc = job.process.wait()
                        break
                    if time.monotonic() >= deadline:
                        with self._lock:
                            job.stop_requested = True
                            job.state = "stopping"
                            self.events.emit(job.id, "timeout")
                            job.detail = "Time limit reached: stopping UFO"
                        self._terminate_tree(job.process)
                        rc = job.process.wait()
                        break
        with self._lock:
            job.returncode = rc
            job.state = "failed" if guard_reason else ("stopped" if job.stop_requested else ("finished" if rc == 0 else "failed"))
            process_dir = Path(os.environ.get("SMARTAUTOMATION_PROCESS_LOGS", str(Path.home() / ".smartautomation" / "process_logs")))
            stderr_path = process_dir / ("smartautomation-" + job.id[:8] + ".stderr.log")
            outcome = classify_process_outcome(rc, stderr_path)
            trajectory = assess_trajectory(UfoConfig.from_environment().root / "logs" / ("smartautomation-" + job.id[:8]))
            saved = assess_saved_target(job.save_target, before=job.save_target_before, require_fresh=True)
            if job.save_target and not saved["save_target_verified"] and not job.stop_requested:
                job.state = "failed"
            job.detail = ("Requested output file missing or empty at target path; task not verified" if job.save_target and not saved["save_target_verified"] and not job.stop_requested else
                          ("UFO UI handoff loop detected; task stopped before further failed actions" if guard_reason else
                          ("UFO evaluator contradicted by failed actions; task not verified"
                          if trajectory["evaluator_conflict"] else
                          ("UFO process exited; task not independently verified"
                           if rc == 0 else "UFO process failed; see diagnostic ZIP"))))
            self.events.emit(job.id, job.state, {"returncode": rc, **outcome, **trajectory, "handoff_failure": guard_reason, **saved})

    def retry_from_failed(self, job_id: str, app_name: str, confirmed: bool) -> dict:
        """Start a NEW approved UFO job, never execute desktop commands here."""
        if not confirmed:
            raise PermissionError("Separate confirmation required for retry")
        if not app_name or len(app_name) > 100 or any(ord(ch) < 32 for ch in app_name):
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
