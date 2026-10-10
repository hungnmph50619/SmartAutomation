"""Offline UFO source compatibility probe.

Never executes UFO; verifies key source structures before attempting an
optional, separately reviewed per-action integration.
"""
from __future__ import annotations

import ast
from pathlib import Path
from smartautomation.ufo import UfoConfig


def _method(cls: ast.ClassDef, name: str):
    return next((node for node in cls.body
                 if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
                 and node.name == name), None)


def inspect_ufo_hooks(root: Path) -> dict:
    processor = root / "ufo/agents/processors/core/processor_framework.py"
    strategy = root / "ufo/agents/processors/strategies/host_agent_processing_strategy.py"
    if not processor.is_file() or not strategy.is_file():
        return {"available": False, "action_guard_supported": False, "reason": "source_missing"}
    try:
        tree = ast.parse(processor.read_text(encoding="utf-8-sig"))
        host_tree = ast.parse(strategy.read_text(encoding="utf-8-sig"))
    except (SyntaxError, UnicodeError, OSError):
        return {"available": False, "action_guard_supported": False, "reason": "source_unreadable"}
    cls = next((n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == "ProcessorTemplate"), None)
    host = next((n for n in host_tree.body if isinstance(n, ast.ClassDef) and n.name == "HostActionExecutionStrategy"), None)
    if cls is None or host is None:
        return {"available": False, "action_guard_supported": False, "reason": "expected_classes_missing"}
    process = _method(cls, "process")
    action = _method(host, "execute")
    if process is None or action is None:
        return {"available": False, "action_guard_supported": False, "reason": "expected_methods_missing"}
    before = [n for n in ast.walk(process) if isinstance(n, ast.Attribute) and n.attr == "before_process"]
    execute = [n for n in ast.walk(process) if isinstance(n, ast.Attribute) and n.attr == "execute"]
    # The observed before_process middleware is processor-wide. There is no
    # demonstrated per-action interception contract, so fail closed.
    return {
        "available": True,
        "processor_middleware_detected": bool(before),
        "processing_phase_execution_detected": bool(execute),
        "host_action_strategy_detected": True,
        "action_guard_supported": False,
        "reason": "per_action_guard_not_verified",
    }


def inspect_current() -> dict:
    return inspect_ufo_hooks(UfoConfig.from_environment().root)
