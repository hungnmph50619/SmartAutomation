"""Strictly scoped read-only UFO task screenshot access."""
from __future__ import annotations
from pathlib import Path
import re

TASK = re.compile(r"^smartautomation-[0-9a-f]{8}$")
IMAGE = re.compile(r"^action_[A-Za-z0-9_]+\.png$")


def list_images(root: Path, task: str) -> list[dict]:
    folder = _folder(root, task)
    if not folder.is_dir():
        return []
    images = [p for p in folder.iterdir() if p.is_file() and not p.is_symlink() and IMAGE.fullmatch(p.name)]
    return [{"name": p.name, "modified": p.stat().st_mtime} for p in sorted(images, key=lambda x: (x.stat().st_mtime, x.name))]


def _folder(root: Path, task: str) -> Path:
    if not TASK.fullmatch(task):
        raise ValueError("Invalid task identifier")
    folder = root / "logs" / task
    if folder.is_symlink():
        raise ValueError("Symlinked task directory forbidden")
    return folder


def image_file(root: Path, task: str, name: str) -> Path:
    folder = _folder(root, task)
    if not IMAGE.fullmatch(name):
        raise ValueError("Invalid screenshot filename")
    path = folder / name
    if not path.is_file() or path.is_symlink():
        raise FileNotFoundError("Screenshot not found")
    if path.stat().st_size > 30 * 1024 * 1024:
        raise ValueError("Screenshot exceeds limit")
    return path
