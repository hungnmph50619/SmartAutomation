"""A small, non-invasive launcher for the official Microsoft UFO CLI.

No UI automation, planning, OCR or computer-operator engine is implemented here.
"""
from __future__ import annotations

import argparse
import os
from pathlib import Path
import subprocess
import sys
from dataclasses import dataclass

@dataclass(frozen=True)
class UfoConfig:
    root: Path
    python: str = sys.executable

    @classmethod
    def from_environment(cls) -> "UfoConfig":
        base = Path(__file__).resolve().parents[1]
        value = os.getenv("SMARTAUTOMATION_UFO_ROOT", "vendor/UFO")
        root = Path(value).expanduser()
        if not root.is_absolute():
            root = base / root
        return cls(root.resolve(), os.getenv("SMARTAUTOMATION_UFO_PYTHON", sys.executable))

    def validate(self) -> list[str]:
        problems = []
        if not (self.root / "ufo" / "__main__.py").is_file() and not (self.root / "ufo" / "ufo.py").is_file():
            problems.append("UFO source missing: run scripts/bootstrap-ufo.ps1 and follow upstream installation steps")
        return problems

def build_command(config: UfoConfig, task: str, request: str) -> list[str]:
    if not task.strip() or not request.strip():
        raise ValueError("task and request must not be empty")
    return [config.python, "-m", "ufo", "--task", task, "--mode", "normal", "--request", request]

def launch(config: UfoConfig, task: str, request: str, execute: bool = False, timeout_seconds: int = 600) -> int:
    issues = config.validate()
    if issues:
        raise RuntimeError("; ".join(issues))
    command = build_command(config, task, request)
    if not execute:
        print("DRY RUN: UFO installation found; no desktop actions performed.")
        print("Task:", task)
        print("Use --execute to authorize an actual local UFO run.")
        return 0
    if os.getenv("SMARTAUTOMATION_EXECUTION_ENABLED", "").lower() != "true":
        raise PermissionError("Execution disabled; set SMARTAUTOMATION_EXECUTION_ENABLED=true explicitly")
    if sys.platform != "win32":
        raise OSError("Desktop execution requires a local Windows session")
    if not 1 <= timeout_seconds <= 3600:
        raise ValueError("Timeout must be 1..3600 seconds")
    # Official UFO is the only automation implementation, launched as a child.
    process = subprocess.Popen(command, cwd=str(config.root))
    try:
        return process.wait(timeout=timeout_seconds)
    except (subprocess.TimeoutExpired, KeyboardInterrupt):
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()
        raise

def main() -> int:
    parser = argparse.ArgumentParser(description="SmartAutomation -> Microsoft UFO launcher")
    parser.add_argument("--task", required=True)
    parser.add_argument("--request", required=True)
    parser.add_argument("--execute", action="store_true", help="Explicitly allow UFO to act on this desktop")
    parser.add_argument("--timeout", type=int, default=600)
    args = parser.parse_args()
    try:
        return launch(UfoConfig.from_environment(), args.task, args.request, args.execute, args.timeout)
    except (RuntimeError, ValueError, PermissionError, OSError) as exc:
        print(f"SmartAutomation: {exc}", file=sys.stderr)
        return 2

if __name__ == "__main__":
    raise SystemExit(main())
