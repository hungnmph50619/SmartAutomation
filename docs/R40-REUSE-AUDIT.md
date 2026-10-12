# R40 — Reuse-first integration audit

## Confirmed implementation (feature branch)
| Capability | Existing code | Decision |
| --- | --- | --- |
| Windows operator | `smartautomation/ufo.py` launches upstream Microsoft UFO | REUSE. Do not create a second computer operator. Live automation still needs Windows acceptance. |
| Application discovery | `app_discovery.py`, `window_discovery.py` | REUSE for process/window evidence. |
| UI capability preflight | `windows_ui_capability.py` | REUSE for read-only UFO MCP server capability checks; NOT proof of live UI execution. |
| Event history | `event_store.py` (SQLite) | REUSE existing operational event store; this is NOT a semantic knowledge database. |
| Run progress | `progress.py` | REUSE UFO log monitoring. |
| Output verification | `outcome_evidence.py`, `trajectory_evidence.py` | REUSE verification gates; they do not automatically prove task success. |
| Recovery | `recovery.py`, `recovery_gate.py`, `failure_breaker.py` | REUSE safety logic; not autonomous remediation. |
| Trace and telemetry | `telemetry.py`, `diagnostics.py` | REUSE. |
| CMIS import/approval | `cmis_candidate.py`, `cmis_approval.py` | REUSE existing read-only contracts. |
| CMIS retrieval | `cmis_retrieval.py`, `cmis_ui_context.py` | REUSE evidence checks; still not integrated into the UFO planner. |

## CMIS Experience Recorder (separate .NET 8/WPF repository)
- Continue to own consensual capture, UIA observation, NAudio microphone capture, FFmpeg screen capture, whisper.cpp CLI transcript, Review Studio, reviewed workflows and local exports.
- Do NOT duplicate UFO execution, app discovery, outcome verification, incident safety gates, or job event storage in Recorder.
- Existing CMIS Experience JSON knowledge snapshots are separate from SmartAutomation's SQLite event timeline. A semantic knowledge store must not be assumed to exist.

## Integration contract
1. Recorder exports a candidate JSON. SmartAutomation validates it with `inspect_candidate`.
2. Independent reviewer decisions are verified by `inspect_approval`; digest mismatches fail closed.
3. UI/process hints remain provenance only. Fresh local UI grounding and user authorization are required for each real execution.
4. `inspect_cmis_integration` composes existing checks without adding execution capabilities.
5. Before accepting any real planner integration: cross-repository fixture tests, an installed UFO environment, and independent Windows end-to-end acceptance.

## R41 recommendation
Finish propagating existing safe UI control hierarchy through the complete Recorder export pipeline and use `cmis_ui_context.py` for *advisory* matching. Do not implement a new UI engine.
