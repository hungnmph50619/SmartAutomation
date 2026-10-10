"""Read-only local integration preflight report for installed UFO and Windows apps."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import platform
import sys

from smartautomation.ufo import UfoConfig
from smartautomation.ufo_compatibility import inspect_ufo_hooks
from smartautomation.app_discovery import discover_start_apps, find_app


def collect(app_query: str = "Word") -> dict:
    config = UfoConfig.from_environment()
    installed = not config.validate()
    result = {
        "platform": platform.system(),
        "python_version": platform.python_version(),
        "ufo_detected": installed,
        "ufo_root": str(config.root),
        "ufo_hooks": inspect_ufo_hooks(config.root),
        "application_query": app_query,
        "applications": [],
        "discovery_status": "not_run",
        "desktop_actions_executed": False,
    }
    if sys.platform == "win32":
        try:
            result["applications"] = find_app(app_query, discover_start_apps())[:10]
            result["discovery_status"] = "ok"
        except (OSError, ValueError, RuntimeError) as exc:
            result["discovery_status"] = "unavailable"
    else:
        result["discovery_status"] = "windows_required"
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--app", default="Word")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if not 1 <= len(args.app.strip()) <= 100:
        parser.error("--app must contain 1..100 characters")
    report = json.dumps(collect(args.app), ensure_ascii=False, indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(report, encoding="utf-8")
        print("Saved:", args.output)
    else:
        print(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
