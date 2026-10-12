"""Reversible P0.3 extension of pinned Microsoft UFO HostUIExecutor.

Adds read-only Start Apps discovery and a bounded, exact-name launch tool to
the existing UFO MCP server. SmartAutomation does not become a second operator.
No arbitrary user-supplied command, executable path, or AppID is executed.
"""
from __future__ import annotations

import argparse
from pathlib import Path

RELATIVE_PATH = Path("ufo/client/mcp/local_servers/ui_mcp_server.py")
BACKUP_SUFFIX = ".smartautomation-p03.bak"
MARKER = "# SmartAutomation P0.3: installed application tools"
ANCHOR = '''    return action_mcp


@MCPRegistry.register_factory_decorator("AppUIExecutor")'''
INSERT = '''    # SmartAutomation P0.3: installed application tools
    # Keep discovery and launch inside the existing UFO HostAgent MCP server.
    def _installed_start_apps():
        import json
        import subprocess
        response = subprocess.run(
            ["powershell.exe", "-NoProfile", "-NonInteractive", "-Command",
             "$ErrorActionPreference='Stop';"
             "ConvertTo-Json -InputObject @(Get-StartApps | Select-Object Name,AppID) -Compress"],
            capture_output=True, text=True, encoding="utf-8", errors="replace",
            check=True, timeout=12,
        )
        payload = json.loads(response.stdout)
        if isinstance(payload, dict):
            payload = [payload]
        if not isinstance(payload, list):
            return []
        return [(str(p["Name"]), str(p["AppID"])) for p in payload
                if isinstance(p, dict) and p.get("Name") and p.get("AppID")]

    @action_mcp.tool(tags={"HostAgent"})
    def discover_installed_applications(query: str) -> Dict[str, Any]:
        """Search installed Windows Start apps when the target has no open window.

        Returns candidates from the operating system, not guessed executables.
        """
        if not isinstance(query, str) or not 2 <= len(query.strip()) <= 100:
            raise ToolError("Application query must be 2..100 characters")
        try:
            matches = [
                {"name": name, "source": "windows_start"}
                for name, appid in _installed_start_apps()
                if query.casefold().strip() in name.casefold()
            ]
        except Exception as exc:
            raise ToolError("Windows Start Apps discovery failed") from exc
        return {"candidates": matches[:20], "count": len(matches)}

    @action_mcp.tool(tags={"HostAgent"})
    def launch_installed_application(name: str) -> Dict[str, Any]:
        """Launch exactly one installed Windows Start app by its discovered name.

        The OS AppID is resolved afresh from Get-StartApps; never execute
        arbitrary shell commands, model-provided AppIDs or file paths.
        Afterwards call get_desktop_app_info and select_application_window.
        """
        if not isinstance(name, str) or not 2 <= len(name.strip()) <= 100:
            raise ToolError("Invalid application name")
        try:
            matches = [
                (app_name, appid) for app_name, appid in _installed_start_apps()
                if app_name.casefold() == name.casefold().strip()
            ]
        except Exception as exc:
            raise ToolError("Windows Start Apps discovery failed") from exc
        if len(matches) != 1:
            raise ToolError("Application name not uniquely installed; discover again")
        app_name, appid = matches[0]
        if not (1 <= len(appid) <= 200 and
                all(c.isascii() and (c.isalnum() or c in "._!-/") for c in appid)):
            raise ToolError("Windows AppID contains unsupported characters")
        import os
        try:
            os.startfile("shell:AppsFolder\\\\" + appid)
        except OSError as exc:
            raise ToolError("Windows could not launch the installed application") from exc
        return {"launch_requested": True, "name": app_name,
                "next_step": "observe_desktop_then_select_window"}

    return action_mcp


@MCPRegistry.register_factory_decorator("AppUIExecutor")'''


def modify(root: Path, restore: bool = False) -> str:
    source = root / RELATIVE_PATH
    backup = source.with_name(source.name + BACKUP_SUFFIX)
    if not source.is_file() or source.is_symlink():
        raise FileNotFoundError(f"UFO UI source missing: {source}")
    raw = source.read_bytes()
    if restore:
        if not backup.is_file() or backup.is_symlink():
            raise FileNotFoundError("Missing P0.3 source backup")
        if MARKER.encode() not in raw:
            raise RuntimeError("UFO source changed; refusing restoration")
        source.write_bytes(backup.read_bytes())
        backup.unlink()
        return "restored"
    if MARKER.encode() in raw:
        return "already_applied"
    original = raw.decode("utf-8")
    normalized = original.replace("\r\n", "\n")
    if normalized.count(ANCHOR) != 1:
        raise RuntimeError("Unsupported UFO source revision; no changes made")
    changed = normalized.replace(ANCHOR, INSERT)
    if "\r\n" in original:
        changed = changed.replace("\n", "\r\n")
    backup.write_bytes(raw)
    try:
        source.write_bytes(changed.encode("utf-8"))
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
        print(f"P0.3 UFO tools: {exc}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
