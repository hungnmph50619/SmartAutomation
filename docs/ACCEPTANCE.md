# Windows acceptance checklist (v0.1)

This is a **manual acceptance protocol**, not a claim of a successful Windows test.

## Prerequisites

1. Use a Windows test session with no confidential customer data.
2. Clone `feat/v0.1-ufo-foundation`, bootstrap Microsoft UFO, and configure its model provider using official upstream documentation.
3. Run `python -m smartautomation` to check readiness.
4. Confirm Notepad starts normally, and that the desktop is interactive.

## Test 1: dry run

```powershell
python -m smartautomation.ufo --task notepad-smoke --request "Open Notepad" 
```

Expected: no desktop action occurs.

## Test 2: explicitly authorized UFO run

```powershell
$env:SMARTAUTOMATION_EXECUTION_ENABLED="true"
.\scripts\test-notepad.ps1
```

Expected: Notepad contains **exactly** `SmartAutomation UFO Windows acceptance test.`
An exit code of zero is NOT proof of success. Inspect Notepad and mark pass/fail yourself.

## Test 3: interruption and timeout

Execute a suitable harmless task and interrupt with Ctrl+C; ensure UFO stops interacting with the desktop. If automation continues, mark FAIL and do not proceed to live office applications. The launcher has a process timeout, but this is NOT yet a fully verified process-tree kill switch.

## Evidence template

- Windows version:
- Python version:
- UFO git SHA: `git -C vendor/UFO rev-parse HEAD`
- Provider/model (no API key):
- Readiness result:
- Dry-run result:
- Task launch result:
- Exact text visible in Notepad: PASS / FAIL
- Ctrl+C stops actions: PASS / FAIL
- Notes/screenshots (redact personal information):

**No CMIS production or operational control testing until security and task verification have passed.**
