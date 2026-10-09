"""Read-only local foundation API. No remote desktop-control endpoint."""
from __future__ import annotations

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from starlette.requests import Request

from smartautomation import __version__
from smartautomation.ufo import UfoConfig

app = FastAPI(title="SmartAutomation", version=__version__)

@app.middleware("http")
async def loopback_only(request: Request, call_next):
    client = request.client
    if client is None or client.host not in {"127.0.0.1", "::1", "testclient"}:
        return JSONResponse({"detail": "localhost only"}, status_code=403)
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
        "execution_api_available": False,
        "notes": problems or ["UFO detected; desktop execution via local CLI requires explicit opt-in"],
    }
