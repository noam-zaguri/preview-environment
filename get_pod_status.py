"""Kubernetes API helpers for the Preview Environment Dashboard."""

from __future__ import annotations

import os
import socket

from kubernetes import client, config
from kubernetes.client import ApiException

from consts import (
    DEFAULT_POD_NAMESPACE,
    ENV_HOSTNAME,
    ENV_POD_NAMESPACE,
    POD_HEALTHY_PHASES,
)


def get_pod_status() -> dict[str, object]:
    """Ask the Kubernetes API for this pod's current phase.

    Uses the in-cluster service account, so the pod needs a Role granting
    `get` on `pods` for itself in its own namespace. Returns healthy=False
    (rather than raising) if the API can't be reached or the pod isn't found,
    so callers can turn that into a proper failed check.
    """
    pod_name = os.getenv(ENV_HOSTNAME, socket.gethostname())
    namespace = os.getenv(ENV_POD_NAMESPACE, DEFAULT_POD_NAMESPACE)
    try:
        config.load_incluster_config()
        pod = client.CoreV1Api().read_namespaced_pod(name=pod_name, namespace=namespace)
        phase = pod.status.phase
        return {
            "pod_name": pod_name,
            "namespace": namespace,
            "phase": phase,
            "healthy": phase in POD_HEALTHY_PHASES,
        }
    except (ApiException, config.ConfigException, OSError) as exc:
        return {
            "pod_name": pod_name,
            "namespace": namespace,
            "phase": "Unknown",
            "healthy": False,
            "error": str(exc),
        }
