"""Local SmartAutomation API: read-only status and explicitly opt-in UFO tasks."""
from __future__ import annotations

import os
from pydantic import BaseModel, Field
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.responses import JSONResponse
from starlette.requests import Request

from smartautomation import __version__
from smartautomation.ufo import UfoConfig
from smartautomation.diagnostics import check_readiness
from smartautomation.jobs import manager
from smartautomation.export_diagnostics import export
from smartautomation.app_discovery import discover_start_apps, find_app
from smartautomation.progress import summarize
from smartautomation.screenshots import list_images, image_file
from smartautomation.recovery import recommend_apps, recovery_instructions
from smartautomation.recovery_gate import evaluate_gate
from smartautomation.ufo_compatibility import inspect_current

app = FastAPI(title="SmartAutomation", version=__version__)

@app.middleware("http")
async def loopback_only(request: Request, call_next):
    client = request.client
    if client is None or client.host not in {"127.0.0.1", "::1", "testclient"}:
        return JSONResponse({"detail": "localhost only"}, status_code=403)
    if request.method in {"POST", "PUT", "PATCH", "DELETE"}:
        origin = request.headers.get("origin", "")
        if origin not in {"http://127.0.0.1:5173", "http://localhost:5173"}:
            return JSONResponse({"detail": "Untrusted origin"}, status_code=403)
    return await call_next(request)

@app.get("/api/status")
def status():
    config = UfoConfig.from_environment()
    problems = config.validate()
    return {
        "product": "SmartAutomation",
        "version": __version__,
        "engine": "Microsoft UFO",
        "ufo_installed": not problems,
        "execution_api_available": os.environ.get("SMARTAUTOMATION_EXECUTION_ENABLED", "").lower() == "true" and not problems,
        "notes": problems or ["UFO detected; desktop execution via local CLI requires explicit opt-in"],
    }

@app.get("/api/readiness")
def readiness():
    """Read-only machine diagnostics; does not execute UFO or expose credentials."""
    return check_readiness()

class StartRequest(BaseModel):
    request: str = Field(min_length=1, max_length=2000)
    confirmed: bool = False


@app.get("/api/jobs/current")
def current_job():
    return manager.snapshot()


@app.post("/api/jobs")
def start_job(body: StartRequest):
    try:
        return manager.start(body.request, body.confirmed)
    except PermissionError as exc:
        raise HTTPException(403, str(exc)) from None
    except (RuntimeError, ValueError, OSError) as exc:
        raise HTTPException(409, str(exc)) from None


@app.post("/api/jobs/{job_id}/stop")
def stop_job(job_id: str):
    try:
        return manager.stop(job_id)
    except LookupError as exc:
        raise HTTPException(404, str(exc)) from None

@app.post("/api/jobs/{job_id}/export")
def export_job(job_id: str):
    current = manager.snapshot()
    if current["job_id"] != job_id:
        raise HTTPException(404, "Job not found")
    if current["state"] in {"starting", "running", "stopping"}:
        raise HTTPException(409, "Wait for job to finish before exporting diagnostics")
    try:
        archive = export("smartautomation-" + job_id[:8])
    except (OSError, ValueError) as exc:
        raise HTTPException(409, f"Diagnostic export failed: {exc}") from None
    return {"filename": archive.name, "saved_to": "Desktop"}

@app.get("/api/apps/discover")
def discover_apps(query: str = ""):
    """Read-only Windows Start Menu discovery. Never launches an app."""
    if not 1 <= len(query.strip()) <= 100:
        raise HTTPException(400, "Provide an application name (1..100 chars)")
    try:
        return {"candidates": find_app(query, discover_start_apps())}
    except (OSError, ValueError, RuntimeError) as exc:
        raise HTTPException(503, "App discovery unavailable") from None


@app.get("/api/jobs/{job_id}/events")
def job_events(job_id: str):
    current = manager.snapshot()
    if current["job_id"] != job_id:
        raise HTTPException(404, "Current job not found")
    return {"events": manager.events.list_events(job_id)}

@app.get("/api/jobs/{job_id}/progress")
def job_progress(job_id: str):
    current = manager.snapshot()
    if current["job_id"] != job_id:
        raise HTTPException(404, "Current job not found")
    config = UfoConfig.from_environment()
    return summarize(config.root, "smartautomation-" + job_id[:8])

@app.get("/api/jobs/{job_id}/screenshots")
def screenshots(job_id: str):
    current = manager.snapshot()
    if current["job_id"] != job_id:
        raise HTTPException(404, "Current job not found")
    return {"images": list_images(UfoConfig.from_environment().root, "smartautomation-" + job_id[:8])}


@app.get("/api/jobs/{job_id}/screenshots/{filename}")
def screenshot(job_id: str, filename: str):
    current = manager.snapshot()
    if current["job_id"] != job_id:
        raise HTTPException(404, "Current job not found")
    try:
        file = image_file(UfoConfig.from_environment().root, "smartautomation-" + job_id[:8], filename)
    except (ValueError, FileNotFoundError):
        raise HTTPException(404, "Screenshot not found") from None
    return FileResponse(file, media_type="image/png", headers={"Cache-Control": "no-store", "X-Content-Type-Options": "nosniff"})

@app.get("/api/jobs/{job_id}/recovery")
def recovery_advice(job_id: str, app_name: str = ""):
    """Advice only: never runs commands or bypasses UFO's security policy."""
    current = manager.snapshot()
    if current["job_id"] != job_id:
        raise HTTPException(404, "Current job not found")
    if len(app_name) > 100:
        raise HTTPException(400, "Application name too long")
    status = summarize(UfoConfig.from_environment().root, "smartautomation-" + job_id[:8])
    breaker = status["circuit_breaker"]
    if breaker["state"] != "suspected_repeat":
        return recommend_apps(app_name, [], breaker)
    if not app_name.strip():
        return {"status": "application_name_required", "candidates": [], "next_step": "provide_application_name"}
    try:
        apps = discover_start_apps()
    except (OSError, ValueError, RuntimeError):
        return {"status": "discovery_unavailable", "candidates": [], "next_step": "inspect_ufo_logs"}
    return recommend_apps(app_name, apps, breaker)

@app.get("/api/jobs/{job_id}/recovery/plan")
def recovery_plan(job_id: str, app_name: str = ""):
    """Return a proposed recovery instruction; NEVER launches an application."""
    current = manager.snapshot()
    if current["job_id"] != job_id:
        raise HTTPException(404, "Current job not found")
    if not 1 <= len(app_name.strip()) <= 100:
        raise HTTPException(400, "Application name required")
    breaker = summarize(UfoConfig.from_environment().root, "smartautomation-" + job_id[:8])["circuit_breaker"]
    if breaker["state"] != "suspected_repeat" or breaker["reason_code"] != "launch_not_found":
        return {"status": "not_allowed", "instruction": None}
    try:
        candidates = find_app(app_name, discover_start_apps())
    except (OSError, ValueError, RuntimeError):
        raise HTTPException(503, "Windows app discovery unavailable") from None
    if not candidates:
        return {"status": "no_candidate", "instruction": None}
    return recovery_instructions(candidates[0], breaker)

class RecoveryRetryRequest(BaseModel):
    app_name: str = Field(min_length=1, max_length=100)
    confirmed: bool = False


@app.post("/api/jobs/{job_id}/recovery/retry")
def retry_recovery(job_id: str, body: RecoveryRetryRequest):
    """User-authorized NEW UFO task only; never execute launch commands ourselves."""
    if not body.confirmed:
        raise HTTPException(403, "Separate retry confirmation required")
    current = manager.snapshot()
    if current["job_id"] != job_id:
        raise HTTPException(404, "Current task not found")
    if current["state"] != "failed":
        raise HTTPException(409, "Only failed tasks can be retried")
    breaker = summarize(UfoConfig.from_environment().root, "smartautomation-" + job_id[:8])["circuit_breaker"]
    if breaker["state"] != "suspected_repeat" or breaker["reason_code"] != "launch_not_found":
        raise HTTPException(409, "No supported launch-not-found recovery evidence")
    try:
        candidates = discover_start_apps()
        exact = next((app for app in candidates if app["name"].casefold() == body.app_name.strip().casefold()), None)
        if exact is None:
            raise HTTPException(409, "Confirmed application not found in Windows Start Menu")
        return manager.retry_from_failed(job_id, exact["name"], body.confirmed)
    except (OSError, ValueError, RuntimeError, PermissionError) as exc:
        raise HTTPException(409, str(exc)) from None
    except LookupError:
        raise HTTPException(404, "Original task no longer available") from None

@app.get("/api/jobs/{job_id}/gate")
def recovery_gate(job_id: str):
    current = manager.snapshot()
    if current["job_id"] != job_id:
        raise HTTPException(404, "Current job not found")
    progress = summarize(UfoConfig.from_environment().root, "smartautomation-" + job_id[:8])
    decision = evaluate_gate(progress, current["state"])
    return {"state": decision.state, "reason": decision.reason,
            "can_auto_resume": decision.can_auto_resume}


@app.get("/api/ufo/compatibility")
def ufo_compatibility():
    """Read-only source compatibility. Never enables experimental hooks."""
    return inspect_current()
