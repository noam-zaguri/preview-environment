"""Discovery of other preview pods this dashboard tracks.

Any pod carrying the TRACKED_LABEL_SELECTOR label (see consts.py) in this
dashboard's namespace shows up on the dashboard. See
helm/preview-dashboard/README.md for the annotation contract other projects
should follow so their pods show up with useful metadata instead of just a
bare pod name.
"""

from __future__ import annotations

import os

from kubernetes import client, config
from kubernetes.client import ApiException

from consts import (
    ANN_APP,
    ANN_COMMIT_SHA,
    ANN_RELEASE_ID,
    ANN_TITLE,
    ANN_VERSION,
    DEFAULT_POD_NAMESPACE,
    ENV_POD_NAMESPACE,
    POD_HEALTHY_PHASES,
    TRACKED_LABEL_SELECTOR,
)


def list_tracked_pods() -> dict[str, object]:
    """List pods in this namespace carrying the tracked label.

    Uses the in-cluster service account, so the pod needs a Role granting
    `list` on `pods` in its own namespace. Returns an "error" key instead of
    raising if the API can't be reached, so the dashboard can render a
    degraded state rather than crash.
    """
    namespace = os.getenv(ENV_POD_NAMESPACE, DEFAULT_POD_NAMESPACE)
    try:
        config.load_incluster_config()
        pods = client.CoreV1Api().list_namespaced_pod(
            namespace, label_selector=TRACKED_LABEL_SELECTOR
        ).items
    except (ApiException, config.ConfigException, OSError) as exc:
        return {"namespace": namespace, "pods": [], "error": str(exc)}

    tracked = []
    for pod in pods:
        annotations = pod.metadata.annotations or {}
        phase = pod.status.phase
        tracked.append({
            "pod_name": pod.metadata.name,
            "app": annotations.get(ANN_APP, pod.metadata.name),
            "commit_sha": annotations.get(ANN_COMMIT_SHA, "unknown"),
            "release_id": annotations.get(ANN_RELEASE_ID, "unknown"),
            "title": annotations.get(ANN_TITLE, ""),
            "version": annotations.get(ANN_VERSION, "unknown"),
            "phase": phase,
            "healthy": phase in POD_HEALTHY_PHASES,
        })
    return {"namespace": namespace, "pods": tracked}
