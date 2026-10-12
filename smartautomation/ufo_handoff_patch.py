"""Apply or restore a narrowly scoped, reversible Microsoft UFO window-handoff fix.

The pinned upstream HostActionExecutionStrategy currently trusts a truthy
selection result. This patch validates the real selected window evidence
before allowing that result to be used by the state machine.

Does not change Windows security, UFO shell policies, or other tools.
"""
from __future__ import annotations

import argparse
from pathlib import Path

RELATIVE_PATH = Path("ufo/agents/processors/strategies/host_agent_processing_strategy.py")
BACKUP_SUFFIX = ".smartautomation-p02.bak"
MARKER = "# SmartAutomation P0.2: verify HostUIExecutor window selection"
OLD = '''            # Extract application root information
            if execution_result and execution_result[0].result:
                app_root = execution_result[0].result.get("root_name", "")

                self.logger.info(
                    f"Selected application: {target.name}, root: {app_root}"
                )

            return execution_result'''
NEW = '''            # SmartAutomation P0.2: verify HostUIExecutor window selection
            # Do not forward a failed command or an empty window to AppAgent.
            # This is the real UFO command-dispatch boundary, not a model hint.
            if not execution_result:
                raise ValueError("Window handoff refused: selection returned no result")
            selected = execution_result[0]
            status = getattr(selected, "status", None)
            status_name = str(getattr(status, "value", status)).lower()
            payload = getattr(selected, "result", None)
            if status_name not in ("success", "resultstatus.success"):
                raise ValueError("Window handoff refused: selection tool failed")
            if not isinstance(payload, dict):
                raise ValueError("Window handoff refused: invalid selection payload")
            if not str(payload.get("root_name") or "").strip():
                raise ValueError("Window handoff refused: selected root is missing")
            if not isinstance(payload.get("window_info"), dict):
                raise ValueError("Window handoff refused: window metadata is missing")

            app_root = payload["root_name"]
            self.logger.info(
                f"Selected application: {target.name}, root: {app_root}"
            )
            return execution_result'''


def modify(root: Path, restore: bool = False) -> str:
    source = root / RELATIVE_PATH
    backup = source.with_name(source.name + BACKUP_SUFFIX)
    if not source.is_file() or source.is_symlink():
        raise FileNotFoundError(f"Pinned UFO source missing: {source}")
    raw = source.read_bytes()
    if restore:
        if not backup.is_file() or backup.is_symlink():
            raise FileNotFoundError("No matching SmartAutomation backup")
        original = backup.read_bytes()
        if MARKER.encode() not in raw:
            raise RuntimeError("UFO source changed since patch; refusing overwrite")
        source.write_bytes(original)
        backup.unlink()
        return "restored"
    if MARKER.encode() in raw:
        return "already_applied"
    original_text = raw.decode("utf-8")
    text = original_text.replace("\r\n", "\n")
    if text.count(OLD) != 1:
        raise RuntimeError("Unsupported UFO source revision; no changes made")
    if backup.exists():
        raise RuntimeError("Existing backup needs manual review; no changes made")
    updated_text = text.replace(OLD, NEW)
    if "\r\n" in original_text:
        updated_text = updated_text.replace("\n", "\r\n")
    updated = updated_text.encode("utf-8")
    backup.write_bytes(raw)
    try:
        source.write_bytes(updated)
    except BaseException:
        source.write_bytes(raw)
        raise
    return "applied"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ufo-root", required=True, type=Path)
    parser.add_argument("--restore", action="store_true")
    args = parser.parse_args()
    try:
        print(modify(args.ufo_root, restore=args.restore))
        return 0
    except (OSError, RuntimeError, UnicodeError) as exc:
        print(f"handoff patch: {exc}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
