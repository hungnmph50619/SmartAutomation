"""Read-only Windows/UFO readiness probe; never starts desktop automation."""
from __future__ import annotations

import importlib.util
import platform
import shutil
import subprocess
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

from smartautomation.ufo import UfoConfig

@dataclass(frozen=True)
class Check:
    name: str
    ok: bool
    detail: str

def check_readiness(config: UfoConfig | None = None) -> dict:
    config = config or UfoConfig.from_environment()
    checks: list[Check] = []
    checks.append(Check("windows", sys.platform == "win32", platform.platform()))
    problems = config.validate()
    checks.append(Check("ufo_source", not problems, str(config.root) if not problems else "; ".join(problems)))
    checks.append(Check("python", sys.version_info >= (3, 10), sys.version.split()[0]))
    checks.append(Check("python_path", bool(shutil.which(config.python) or Path(config.python).is_file()), config.python))
    # Inspect dependency availability from the current environment only.
    for name in ("pywinauto", "pyautogui", "PIL"):
        available = importlib.util.find_spec(name) is not None
        checks.append(Check("module_" + name, available, "available" if available else "not installed in the active Python environment"))
    return {
        "ready_for_windows_validation": all(c.ok for c in checks),
        "checks": [asdict(c) for c in checks],
        "note": "Readiness is not proof UFO works: model setup, Windows desktop permissions and live task verification are required.",
    }
