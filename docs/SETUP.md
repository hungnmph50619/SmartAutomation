# SmartAutomation v0.1 — UFO foundation

This branch keeps **Microsoft UFO as the sole computer-action engine**. It does not bring the legacy C# Computer Operator code into SmartAutomation.

## Windows setup

In PowerShell, from a checkout of this repository:

```powershell
.\scripts\bootstrap-ufo.ps1
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements-app.txt
python -m pip install -r vendor\UFO\requirements.txt
python -m unittest discover -s tests -v
python -m uvicorn smartautomation.api:app --host 127.0.0.1 --port 8765
```

**Important:** Microsoft's UFO may have version-specific extra installation steps and model configuration; check the upstream README before attempting to run tasks. The install command above is a starting point, not proof that the upstream dependencies match your Python version.

Visit http://127.0.0.1:8765/api/status to see whether UFO source is present.

## Safe dry-run

```powershell
python -m smartautomation.ufo --task notepad-smoke --request "Open Notepad and type a short sentence"
```

Dry-run verifies source layout but does not open or control applications.

## Explicit desktop execution (only after UFO is configured)

```powershell
$env:SMARTAUTOMATION_EXECUTION_ENABLED="true"
python -m smartautomation.ufo --task notepad-smoke --request "Open Notepad and type a short sentence" --execute
```

Do this **only on your own Windows machine**, initially in a test account/session without confidential data. The underlying UFO CLI will operate the real Windows desktop. Do not enter actual CMIS credentials or live customer records in demonstration prompts. Press Ctrl+C to interrupt; verify the application result independently.

The API intentionally exposes no /run endpoint at this stage, and is only for localhost status.

## Next phase
- Verify this pinned UFO checkout and configuration on Windows.
- Use the upstream demonstration/experience subsystems rather than reinventing their internals.
- Add a controlled job lifecycle, cancel mechanism and task verification before enabling chat-driven desktop execution.
- Only then develop a React UI and skill teaching flow.
