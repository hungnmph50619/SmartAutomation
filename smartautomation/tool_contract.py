"""Strict validation for UFO list_tools responses.

The upstream app agent currently expects a list of mapping objects. Treat
connection errors, status failures and strings as failures, never as tools.
No desktop execution is performed here.
"""
from __future__ import annotations
from collections.abc import Mapping


class ToolDiscoveryError(RuntimeError):
    def __init__(self, reason: str):
        super().__init__(reason)
        self.reason = reason


def validate_list_tools(results: object) -> list[dict]:
    if not isinstance(results, list) or not results:
        raise ToolDiscoveryError("missing_dispatch_result")
    first = results[0]
    if isinstance(first, Mapping):
        status = first.get("status")
        payload = first.get("result")
    else:
        status = getattr(first, "status", None)
        payload = getattr(first, "result", None)
    if status is not None:
        status_text = str(getattr(status, "value", status)).lower()
        if status_text not in {"success", "resultstatus.success"}:
            raise ToolDiscoveryError("list_tools_command_failed")
    if not isinstance(payload, list):
        raise ToolDiscoveryError("unexpected_tools_payload_type")
    if not payload:
        raise ToolDiscoveryError("empty_tool_list")
    if any(not isinstance(item, Mapping) for item in payload):
        raise ToolDiscoveryError("non_mapping_tool_entry")
    if any(not isinstance(item.get("tool_name"), str) or not item["tool_name"].strip() for item in payload):
        raise ToolDiscoveryError("invalid_tool_name")
    return [dict(item) for item in payload]
