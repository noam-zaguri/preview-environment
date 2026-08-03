"""
Preview Environment Dashboard
=============================

A small FastAPI web server that runs as a single, permanent "preview-environment"
deployment on Kubernetes/OpenShift, and acts as the central status page for every
OTHER preview pod running in its namespace (deliberately not deployed per-MR
itself, since a pod can't tell you it's down if the dashboard is on that same pod).

It serves:
  * GET /            -> a visual HTML dashboard showing this pod's own metadata,
                         plus a live table of every other tracked preview pod
  * GET /api/meta    -> this pod's own metadata as JSON (handy for scripts / debugging)
  * GET /api/pods    -> JSON list of other preview pods this dashboard tracks
                         (see tracked_pods.py for the label/annotation contract)
  * GET /healthz     -> Kubernetes liveness/readiness probe (returns 200 "ok")
  * GET /pod-status  -> queries the Kubernetes API and reports whether this pod is
                         actually Running (200) or not, e.g. Failed/Pending (503)

All metadata is read from environment variables that the CI/CD pipeline is
expected to inject into the pod (e.g. via the Deployment spec or a ConfigMap):

  COMMIT_SHA      git commit the image was built from
  MR_RELEASE_ID   merge-request / release identifier for this preview env
  MR_TITLE        human-readable MR title (optional)
  APP_VERSION     application version / image tag (optional)
  ENVIRONMENT     logical environment name (defaults to "preview")
  POD_NAMESPACE   namespace this pod runs in, used by /pod-status (defaults to "default")

The pod hostname is read from the OS and reflects the Kubernetes pod name.
"""

from __future__ import annotations

import os
import socket
from datetime import datetime, timezone

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse, PlainTextResponse
from fastapi.templating import Jinja2Templates

from consts import (
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
from get_pod_status import get_pod_status
from tracked_pods import list_tracked_pods
from uptime import format_uptime, uptime_seconds


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
        "pod_hostname": os.getenv(ENV_HOSTNAME, socket.gethostname()),
    }


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


@app.get("/pod-status")
def pod_status() -> JSONResponse:
    """Report whether the preview-environment pod is Running (and not e.g. Failed/Pending).

    Unlike /healthz, this actually queries the Kubernetes API for the pod's
    phase rather than just confirming the FastAPI process is up.
    """
    status = get_pod_status()
    status_code = 200 if status["healthy"] else 503
    return JSONResponse(status, status_code=status_code)


@app.get("/api/meta")
def api_meta() -> JSONResponse:
    """Return the environment metadata as JSON."""
    meta = _get_metadata()
    meta["uptime_seconds"] = uptime_seconds()
    meta["server_time_utc"] = datetime.now(timezone.utc).isoformat()
    return JSONResponse(meta)


@app.get("/api/pods")
def api_pods() -> JSONResponse:
    """List other preview pods this dashboard tracks (see tracked_pods.py)."""
    return JSONResponse(list_tracked_pods())


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
        "uptime": format_uptime(uptime_seconds()),
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
