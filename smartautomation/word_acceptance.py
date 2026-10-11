"""Read-only acceptance assessment of Microsoft UFO Word diagnostics.

This does not claim a successful document merely because UFO exited with code 0.
The operator should review the generated document separately.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
from smartautomation.ufo import UfoConfig
from smartautomation.progress import summarize


def assess(task: str, root: Path | None = None) -> dict:
    root = root or UfoConfig.from_environment().root
    progress = summarize(root, task)
    folder = root / "logs" / task
    output = folder / "output.md"
    summary = ""
    if output.is_file() and not output.is_symlink():
        summary = output.read_text(encoding="utf-8", errors="replace")[:100000]
    markers = ["file not found", "blocked by security", "could not be launched",
               "no document was created", "task failed"]
    failures = [marker for marker in markers if marker in summary.casefold()]
    return {
        "task": task,
        "screenshots": progress["step_count"],
        "last_activity": progress["last_activity"],
        "warning": progress["warning"],
        "reported_failures": failures,
        "ufo_report_present": bool(summary),
        "document_verified": False,
        "assessment": "reported_failure" if failures else "requires_document_review",
        "next_step": "inspect_screenshots_and_output_document",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--task", required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = json.dumps(assess(args.task), ensure_ascii=False, indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(report, encoding="utf-8")
        print("Saved:", args.output)
    else:
        print(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
