"""Read-only capability audit of the official pinned UFO Windows UI MCP servers.

Source structure is evidence of implementation, not proof an actual Windows
session or app can be controlled. Does not import UFO or execute any action.
"""
from __future__ import annotations

import ast
from pathlib import Path


def _functions(node: ast.AST) -> set[str]:
    return {n.name for n in ast.walk(node) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}


def inspect_windows_ui(root: Path) -> dict:
    path = root / "ufo/client/mcp/local_servers/ui_mcp_server.py"
    result = {"source_present": False, "host_tools": [], "app_tools": [],
              "data_tools": [], "implementation_detected": False,
              "live_windows_verified": False, "reason": "source_missing"}
    if not path.is_file() or path.is_symlink():
        return result
    try:
        tree = ast.parse(path.read_text(encoding="utf-8-sig"))
    except (OSError, UnicodeError, SyntaxError):
        result["reason"] = "source_unreadable"
        return result
    result["source_present"] = True
    factories = {n.name: n for n in tree.body
                 if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}
    required = {
        "host_tools": ("create_host_action_mcp_server", {"select_application_window"}),
        "app_tools": ("create_app_action_mcp_server", {"click_input", "keyboard_input", "set_edit_text"}),
        "data_tools": ("create_data_mcp_server", {"get_desktop_app_target_info", "capture_desktop_screenshot"}),
    }
    for key, (factory, names) in required.items():
        if factory in factories:
            result[key] = sorted(names.intersection(_functions(factories[factory])))
    result["implementation_detected"] = all(
        set(result[key]) == names for key, (_, names) in required.items()
    )
    result["reason"] = ("implementation_present_live_test_required"
                        if result["implementation_detected"] else "missing_expected_ui_tools")
    return result
