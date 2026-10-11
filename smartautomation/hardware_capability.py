"""Identify unsafe mock-only UFO Hardware MCP implementations.

Read-only source inspection: do not launch the HTTP service or hardware actions.
A reachable mock endpoint must not be considered a working Windows operator.
"""
from __future__ import annotations
from pathlib import Path
import ast


def classify_hardware_server(root: Path) -> dict:
    path = root / "ufo" / "client" / "mcp" / "http_servers" / "hardware_mcp_server.py"
    if not path.is_file() or path.is_symlink():
        return {"status": "source_missing", "desktop_control_verified": False}
    try:
        text = path.read_text(encoding="utf-8-sig")
        tree = ast.parse(text)
    except (OSError, UnicodeError, SyntaxError):
        return {"status": "source_unreadable", "desktop_control_verified": False}
    function = next((n for n in tree.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
                     and n.name == "create_hardware_mcp_server"), None)
    if function is None:
        return {"status": "unknown_implementation", "desktop_control_verified": False}
    marker = "dummy" in (ast.get_docstring(function) or "").lower() or "mock" in (ast.get_docstring(function) or "").lower()
    names = {n.name for n in ast.walk(function) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}
    if marker and {"click_mouse", "type_text", "press_hotkey"}.issubset(names):
        return {"status": "mock_server", "desktop_control_verified": False,
                "reason": "upstream_server_declares_dummy_hardware_tools"}
    return {"status": "unknown_implementation", "desktop_control_verified": False}
