# UFO tool-discovery reliability gate

The diagnostic bundle smartautomation-40e00b13 showed a HardwareAgent handoff followed by an unexpected list_tools payload, then AttributeError: 'str' object has no attribute 'get' in AppAgent._load_mcp_context.

Layer 1: smartautomation/tool_contract.py validates list_tools responses without accessing Windows desktop. Tests cover valid tools, connection failures, strings, missing results, empty tool lists and malformed entries.

Important: this validator is not integrated into upstream UFO yet. Green unit tests do not prove MCP connectivity.

Before integrating: identify the specific failing tool service, check connection lifecycle from stdout/stderr, add fail-closed typed validation to pinned UFO only after compatibility assessment, and test a dedicated HardwareAgent smoke task with explicit user confirmation. Never bypass UFO security policies or add a second computer operator.

Test: py -3.11 -m unittest tests.test_tool_contract -v