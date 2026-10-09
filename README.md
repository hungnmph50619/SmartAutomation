# SmartAutomation

A clean, **Microsoft UFO-first** computer automation project.

## Architecture
- **Microsoft UFO upstream**: the sole desktop agent engine (HostAgent, AppAgent, UIA, vision, execution).
- **SmartAutomation shell**: optional user interface, configuration and independent acceptance checks.
- No legacy PersonalAI Computer Operator C# modules are imported.

## Source of truth
Upstream: https://github.com/microsoft/UFO

We track UFO separately so it can be updated without rewriting vendor internals.
Bootstrap a local checkout with `scripts/bootstrap-ufo.ps1` (Windows).
Do not commit UFO's local `agents.yaml`, API keys, credentials, logs or virtual environments.

## First milestones
1. Safe repository bootstrap and pinned upstream UFO revision.
2. Dry-run launch and provider configuration validation.
3. Windows Notepad acceptance: exact text entry + independently verified file output.
4. Recovery, cancellation, performance comparison and app-general reliability.

**No unattended desktop control is enabled by default.**
UFO is open-source software under its own MIT license; preserve upstream attribution.
This repository is independent from `AI-Ca-Nhan`, which is retained without modification.
