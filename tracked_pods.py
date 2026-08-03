"""Discovery of other preview pods this dashboard tracks.

Any pod in this dashboard's namespace whose name matches
TRACKED_POD_NAME_PATTERN (see consts.py) is treated as a tracked preview
pod -- no label or registration required, just name the release/pod with a
"pr-<number>" segment. See helm/preview-dashboard/README.md for the optional
annotation contract other projects can use for richer display.
"""

from __future__ import annotations

import os
import re

from kubernetes import client, config
from kubernetes.client import ApiException

from consts import (
    ANN_APP,
    ANN_COMMIT_SHA,
    ANN_RELEASE_ID,
    ANN_TITLE,
    ANN_VERSION,
    DEFAULT_POD_NAMESPACE,
    ENV_HOSTNAME,
    ENV_POD_NAMESPACE,
    POD_HEALTHY_PHASES,
    TRACKED_POD_NAME_PATTERN,
)

_TRACKED_NAME_RE = re.compile(TRACKED_POD_NAME_PATTERN)


def list_tracked_pods() -> dict[str, object]:
    """List pods in this namespace whose name matches the preview-pod pattern.

    Uses the in-cluster service account, so the pod needs a Role granting
    `list` on `pods` in its own namespace. Excludes this dashboard's own pod
    by name so it never lists itself. Returns an "error" key instead of
    raising if the API can't be reached, so the dashboard can render a
    degraded state rather than crash.
    """
    namespace = os.getenv(ENV_POD_NAMESPACE, DEFAULT_POD_NAMESPACE)
    own_pod_name = os.getenv(ENV_HOSTNAME, "")
    try:
        config.load_incluster_config()
        pods = client.CoreV1Api().list_namespaced_pod(namespace).items
    except (ApiException, config.ConfigException, OSError) as exc:
        return {"namespace": namespace, "pods": [], "error": str(exc)}

    tracked = []
    for pod in pods:
        name = pod.metadata.name
        if name == own_pod_name or not _TRACKED_NAME_RE.search(name):
            continue
        annotations = pod.metadata.annotations or {}
        phase = pod.status.phase
        tracked.append({
            "pod_name": name,
            "app": annotations.get(ANN_APP, name),
            "commit_sha": annotations.get(ANN_COMMIT_SHA, "unknown"),
            "release_id": annotations.get(ANN_RELEASE_ID, "unknown"),
            "title": annotations.get(ANN_TITLE, ""),
            "version": annotations.get(ANN_VERSION, "unknown"),
            "phase": phase,
            "healthy": phase in POD_HEALTHY_PHASES,
        })
    return {"namespace": namespace, "pods": tracked}
