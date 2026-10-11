"""Read-only reachability check for the pinned UFO HardwareAgent MCP endpoint.

Tests TCP connectivity only. A listening port does not prove that MCP works,
that tool discovery succeeds, or that desktop actions are safe.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import socket
from smartautomation.ufo import UfoConfig


def hardware_endpoint(root: Path) -> dict:
    file = root / "config" / "ufo" / "mcp.yaml"
    if not file.is_file() or file.is_symlink():
        return {"status": "config_missing"}
    content = file.read_text(encoding="utf-8-sig")
    match = re.search(r"(?ms)^HardwareAgent:\s*\n(.*?)(?=^[A-Za-z][A-Za-z0-9_]*:\s*$|\Z)", content)
    if not match:
        return {"status": "hardware_agent_missing"}
    section = match.group(1)
    types = re.findall(r"(?m)^\s+type:\s*([^#\n]+)", section)
    hosts = re.findall(r"(?m)^\s+host:\s*[\x22\x27]?([^\x22\x27#\s]+)", section)
    ports = re.findall(r"(?m)^\s+port:\s*(\d+)", section)
    paths = re.findall(r"(?m)^\s+path:\s*[\x22\x27]?([^\x22\x27#\s]+)", section)
    if not types or any(t.strip() != "http" for t in types):
        return {"status": "unsupported_transport"}
    if not ports or len(set(ports)) != 1 or not hosts or len(set(hosts)) != 1:
        return {"status": "inconsistent_hardware_endpoints"}
    host = hosts[0].lower()
    if host not in {"localhost", "127.0.0.1", "::1"}:
        return {"status": "non_local_endpoint_not_probed"}
    port = int(ports[0])
    if not 1 <= port <= 65535:
        return {"status": "invalid_port"}
    return {"status": "configured", "host": host, "port": port, "path": paths[0] if paths else "/mcp"}


def probe(root: Path, timeout: float = 1.5) -> dict:
    endpoint = hardware_endpoint(root)
    if endpoint.get("status") != "configured":
        return {"endpoint": endpoint, "tcp_status": "not_tested", "mcp_verified": False}
    try:
        with socket.create_connection((endpoint["host"], endpoint["port"]), timeout=timeout):
            tcp = "listening"
    except (ConnectionError, TimeoutError, OSError):
        tcp = "not_reachable"
    return {"endpoint": endpoint, "tcp_status": tcp, "mcp_verified": False}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    data = probe(UfoConfig.from_environment().root)
    report = json.dumps(data, ensure_ascii=False, indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(report, encoding="utf-8")
        print("Saved:", args.output)
    else:
        print(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
