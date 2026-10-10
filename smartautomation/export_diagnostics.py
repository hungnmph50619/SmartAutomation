"""Export a UFO task's diagnostics to the Windows Desktop.

Privacy-first defaults: request.log and response.log are deliberately excluded
because model prompts can contain credentials or private text. Screenshots and
summaries still require user review before sharing.
"""
from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path
import os
import re
import sys
import zipfile

from smartautomation.ufo import UfoConfig

TASK_PATTERN = re.compile(r"^smartautomation-[a-f0-9]{8}$")
ALLOWED_NAMES = {"output.md", "evaluation.log"}
IMAGE_PATTERN = re.compile(r"^action_[a-zA-Z0-9_]+\.png$")
MAX_BYTES = 30 * 1024 * 1024


def export(task: str, desktop: Path | None = None) -> Path:
    if not TASK_PATTERN.fullmatch(task):
        raise ValueError("Invalid task ID")
    config = UfoConfig.from_environment()
    folder = config.root / "logs" / task
    if not folder.is_dir():
        raise FileNotFoundError("UFO task log directory not found")
    if desktop is None:
        desktop = Path(os.environ.get("USERPROFILE", str(Path.home()))) / "Desktop"
    if not desktop.is_dir():
        raise FileNotFoundError("Desktop folder not found")
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    destination = desktop / f"SmartAutomation-Diagnostic-{task[-8:]}-{stamp}.zip"
    # No recursion: only known UFO output files. No credentials/configuration files.
    selected = [p for p in folder.iterdir()
                if p.is_file() and not p.is_symlink()
                and (p.name in ALLOWED_NAMES or IMAGE_PATTERN.fullmatch(p.name))
                and p.stat().st_size <= MAX_BYTES]
    if not selected:
        raise FileNotFoundError("No eligible diagnostic files")
    with zipfile.ZipFile(destination, "x", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(selected):
            archive.write(path, arcname=path.name)
        archive.writestr("README-PRIVACY.txt",
                         "Screenshots and UFO evaluation may contain private information.\n"
                         "Review all included files before uploading to any chat.\n"
                         "request.log, response.log, agents.yaml and API keys are excluded.\n")
    return destination


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--task", required=True, help="Task log directory, e.g. smartautomation-bd705d27")
    args = parser.parse_args()
    try:
        print("Created:", export(args.task))
        print("Review images and text before uploading to ChatGPT.")
        return 0
    except (OSError, ValueError) as exc:
        print(f"Export failed: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
