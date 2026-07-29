"""
Preview Environment Dashboard
=============================

A small FastAPI web server intended to run inside an on-demand, per-Merge-Request
preview environment on Kubernetes.

It serves:
  * GET /          -> a visual HTML dashboard showing live pod / release metadata
  * GET /api/meta  -> the same metadata as JSON (handy for scripts / debugging)
  * GET /healthz   -> Kubernetes liveness/readiness probe (returns 200 "ok")

All metadata is read from environment variables that the CI/CD pipeline is
expected to inject into the pod (e.g. via the Deployment spec or a ConfigMap):

  COMMIT_SHA     git commit the image was built from
  MR_RELEASE_ID  merge-request / release identifier for this preview env
  MR_TITLE       human-readable MR title (optional)
  APP_VERSION    application version / image tag (optional)
  ENVIRONMENT    logical environment name (defaults to "preview")

The pod hostname is read from the OS and reflects the Kubernetes pod name.
"""

from __future__ import annotations

import os
import socket
import time
from datetime import datetime, timezone

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse, PlainTextResponse
from fastapi.templating import Jinja2Templates

from constants import (
    APP_DESCRIPTION,
    APP_TITLE,
    DASHBOARD_TEMPLATE,
    DEFAULT_APP_VERSION,
    DEFAULT_COMMIT_SHA,
    DEFAULT_ENVIRONMENT,
    DEFAULT_MR_RELEASE_ID,
    DEFAULT_MR_TITLE,
    DEFAULT_PORT,
    ENV_APP_VERSION,
    ENV_COMMIT_SHA,
    ENV_ENVIRONMENT,
    ENV_HOSTNAME,
    ENV_MR_RELEASE_ID,
    ENV_MR_TITLE,
    ENV_PORT,
    ENV_RELOAD,
    TEMPLATES_DIR,
)

# ---------------------------------------------------------------------------
# Metadata collection
# ---------------------------------------------------------------------------

# Process start time, used to display uptime on the dashboard.
_START_TIME = time.time()


def _get_metadata() -> dict[str, str]:
    """Collect runtime metadata from the environment and the OS.

    Every value has a sane fallback so the dashboard still renders even when a
    variable was not injected (e.g. when running locally).
    """
    return {
        "commit_sha": os.getenv(ENV_COMMIT_SHA, DEFAULT_COMMIT_SHA),
        "mr_release_id": os.getenv(ENV_MR_RELEASE_ID, DEFAULT_MR_RELEASE_ID),
        "mr_title": os.getenv(ENV_MR_TITLE, DEFAULT_MR_TITLE),
        "app_version": os.getenv(ENV_APP_VERSION, DEFAULT_APP_VERSION),
        "environment": os.getenv(ENV_ENVIRONMENT, DEFAULT_ENVIRONMENT),
        # In Kubernetes the pod name is exposed as the container hostname.
        "pod_hostname": os.getenv(ENV_HOSTNAME, socket.gethostname()),
    }


def _uptime_seconds() -> int:
    return int(time.time() - _START_TIME)


def _format_uptime(seconds: int) -> str:
    minutes, secs = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    days, hours = divmod(hours, 24)
    parts = []
    if days:
        parts.append(f"{days}d")
    if hours or days:
        parts.append(f"{hours}h")
    if minutes or hours or days:
        parts.append(f"{minutes}m")
    parts.append(f"{secs}s")
    return " ".join(parts)


# ---------------------------------------------------------------------------
# FastAPI application
# ---------------------------------------------------------------------------

app = FastAPI(
    title=APP_TITLE,
    description=APP_DESCRIPTION,
    version=_get_metadata()["app_version"],
)

templates = Jinja2Templates(directory=TEMPLATES_DIR)


@app.get("/healthz", response_class=PlainTextResponse)
def healthz() -> PlainTextResponse:
    """Kubernetes health check endpoint.

    Kept intentionally cheap and dependency-free so it can be used for both
    liveness and readiness probes.
    """
    return PlainTextResponse("ok", status_code=200)


@app.get("/api/meta")
def api_meta() -> JSONResponse:
    """Return the environment metadata as JSON."""
    meta = _get_metadata()
    meta["uptime_seconds"] = _uptime_seconds()
    meta["server_time_utc"] = datetime.now(timezone.utc).isoformat()
    return JSONResponse(meta)


@app.get("/", response_class=HTMLResponse)
def dashboard(request: Request) -> HTMLResponse:
    """Render the visual dashboard."""
    meta = _get_metadata()
    short_sha = (
        meta["commit_sha"][:12]
        if meta["commit_sha"] != DEFAULT_COMMIT_SHA
        else DEFAULT_COMMIT_SHA
    )
    context = {
        "environment": meta["environment"],
        "mr_release_id": meta["mr_release_id"],
        "commit_sha": meta["commit_sha"],
        "short_sha": short_sha,
        "pod_hostname": meta["pod_hostname"],
        "app_version": meta["app_version"],
        "mr_title": meta["mr_title"],
        "uptime": _format_uptime(_uptime_seconds()),
        "server_time": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
    }
    return templates.TemplateResponse(request, DASHBOARD_TEMPLATE, context)


if __name__ == "__main__":
    import uvicorn
    
    reload_env = os.getenv(ENV_RELOAD, "").lower()

    uvicorn.run(
            "main:app",
            host="0.0.0.0",
            port=int(os.getenv(ENV_PORT, DEFAULT_PORT)),
            reload=reload_env in ("true", "1", "yes"),
        )
