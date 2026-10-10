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
