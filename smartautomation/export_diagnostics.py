"""Export complete per-task UFO diagnostics to Windows Desktop.

Includes requests, model responses, images, traces and error logs. Removes
recognizable credential values from text files; screenshots are not redacted.
Never includes application configuration files or files outside the task folder.
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
MAX_FILE_BYTES = 50 * 1024 * 1024
MAX_ARCHIVE_INPUT_BYTES = 300 * 1024 * 1024
TEXT_SUFFIXES = {".log", ".md", ".txt", ".json", ".jsonl", ".csv", ".yaml", ".yml"}
EXCLUDED_NAMES = {"agents.yaml", ".env", "credentials.json", "token.json", "secrets.json", "api_keys.json"}
SECRET_PATTERNS = (
    re.compile(r'(?i)(["\x27]?(?:api[_-]?key|access[_-]?token|refresh[_-]?token|password|client_secret)["\x27]?\s*[:=]\s*["\x27]?)([^\s,"\x27}]+)'),
    re.compile(r"(?i)(Bearer\s+)[A-Za-z0-9._~+/-]+"),
    re.compile(r"AIza[0-9A-Za-z_-]{25,}"),
)


def redact(content: str) -> str:
    content = re.sub(r"(?im)^([ \\t]*Authorization\\s*[:=]\\s*)[^\\r\\n]+", r"\\1[REDACTED]", content)
    for pattern in SECRET_PATTERNS:
        if pattern.groups == 2:
            content = pattern.sub(lambda match: match.group(1) + "[REDACTED]", content)
        elif pattern.groups == 1:
            content = pattern.sub(lambda match: match.group(1) + "[REDACTED]", content)
        else:
            content = pattern.sub("[REDACTED]", content)
    return content


def export(task: str, desktop: Path | None = None) -> Path:
    if not TASK_PATTERN.fullmatch(task):
        raise ValueError("Invalid task ID")
    config = UfoConfig.from_environment()
    folder = config.root / "logs" / task
    if not folder.is_dir() or folder.is_symlink():
        raise FileNotFoundError("UFO task log directory not found")
    if desktop is None:
        desktop = Path(os.environ.get("USERPROFILE", str(Path.home()))) / "Desktop"
    if not desktop.is_dir():
        raise FileNotFoundError("Desktop folder not found")
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    destination = desktop / f"SmartAutomation-Diagnostic-{task[-8:]}-{stamp}.zip"
    selected = []
    total = 0
    for file in sorted(folder.rglob("*")):
        if not file.is_file() or file.is_symlink():
            continue
        rel = file.relative_to(folder)
        if any(part.startswith(".") or part.lower() in EXCLUDED_NAMES for part in rel.parts):
            continue
        size = file.stat().st_size
        if size > MAX_FILE_BYTES:
            raise ValueError(f"Diagnostic file exceeds size limit: {rel}")
        total += size
        if total > MAX_ARCHIVE_INPUT_BYTES:
            raise ValueError("Diagnostic bundle exceeds 300 MiB limit")
        selected.append((file, rel))
    if not selected:
        raise FileNotFoundError("No eligible diagnostic files")
    with zipfile.ZipFile(destination, "x", compression=zipfile.ZIP_DEFLATED) as archive:
        for file, rel in selected:
            if file.suffix.lower() in TEXT_SUFFIXES:
                data = file.read_text(encoding="utf-8", errors="replace")
                archive.writestr(str(rel).replace("\\", "/"), redact(data))
            else:
                archive.write(file, arcname=str(rel).replace("\\", "/"))
        archive.writestr("README-PRIVACY.txt",
                         "Complete per-task UFO logs, including request.log and response.log, are included.\n"
                         "Common credential patterns were redacted in text; this is not a guarantee.\n"
                         "Screenshots and other binary files are NOT redacted. Review before sharing.\n"
                         "Application configuration and credentials files are excluded.\n")
    return destination


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--task", required=True)
    args = parser.parse_args()
    try:
        print("Created:", export(args.task))
        print("Review images and logs before uploading to ChatGPT.")
        return 0
    except (OSError, ValueError) as exc:
        print(f"Export failed: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
