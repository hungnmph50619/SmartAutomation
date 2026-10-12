"""Ground and independently verify explicit local save targets.

Only simple literal Desktop/Documents filenames are inferred. Never infer from
model hallucinations, and never search other folders to justify a wrong path.
"""
from __future__ import annotations

import os
import re
from pathlib import Path

FILENAME = re.compile(r"(?<![\\w.])([A-Za-z0-9][A-Za-z0-9_.-]{0,110}\\.(?:docx|xlsx|pptx|pdf|txt))\\b", re.I)


def requested_save_target(request: str, home: Path | None = None) -> Path | None:
    text = request.strip()
    files = FILENAME.findall(text)
    if len(files) != 1:
        return None
    name = files[0].strip()
    if name in (".", "..") or ".." in name or "/" in name or "\\" in name:
        return None
    # Require explicit folder; do not guess that any file request means Desktop.
    desktop = bool(re.search(r"\bdesktop\b|màn hình nền|man hinh nen", text, re.I))
    documents = bool(re.search(r"\bdocuments\b|tài liệu của tôi|tai lieu cua toi", text, re.I))
    if desktop == documents:
        return None
    root = home if home is not None else Path(os.environ.get("USERPROFILE",str(Path.home())))
    return root / ("Desktop" if desktop else "Documents") / name


def assess_saved_target(target: Path | None) -> dict:
    result = {"save_target_verified": False, "save_target_status": "unknown_target", "save_target_path": None}
    if target is None:
        return result
    result["save_target_path"] = str(target)
    if target.is_symlink() or not target.is_file():
        result["save_target_status"] = "missing_target_file"
    elif target.stat().st_size == 0:
        result["save_target_status"] = "empty_target_file"
    else:
        result.update({"save_target_verified": True, "save_target_status": "file_exists_at_requested_path"})
    return result


def guide_save_target(request: str, target: Path | None, max_length: int = 2000) -> str:
    if target is None:
        return request
    guidance = (
        "Can luu tai dung duong dan day du sau, khong chi ten file: "
        + str(target) + ". Trong Save As, nhap duong dan day du neu duoc ho tro. "
        "Khong bao hoan thanh khi chua xac minh file tai DUNG duong dan yeu cau. "
    )
    return guidance + "\n" + request if len(guidance) + len(request) + 1 <= max_length else request
