"""Constants for the Preview Environment Dashboard."""

# Environment variable names (injected by the CI/CD pipeline into the pod).
ENV_COMMIT_SHA = "COMMIT_SHA"
ENV_MR_RELEASE_ID = "MR_RELEASE_ID"
ENV_MR_TITLE = "MR_TITLE"
ENV_APP_VERSION = "APP_VERSION"
ENV_ENVIRONMENT = "ENVIRONMENT"
ENV_HOSTNAME = "HOSTNAME"
ENV_PORT = "PORT"
ENV_RELOAD = "RELOAD"
ENV_POD_NAMESPACE = "POD_NAMESPACE"

# Fallback values used when the corresponding env var is not set.
DEFAULT_COMMIT_SHA = "unknown"
DEFAULT_MR_RELEASE_ID = "unknown"
DEFAULT_MR_TITLE = ""
DEFAULT_APP_VERSION = "dev"
DEFAULT_ENVIRONMENT = "preview"
DEFAULT_PORT = "8000"
DEFAULT_POD_NAMESPACE = "default"

# Pod phases considered healthy for the preview-environment pod check.
POD_HEALTHY_PHASES = {"Running"}

# A pod in this dashboard's namespace is treated as a tracked preview pod if
# its name contains a "pr-<number>" segment (e.g. "test-app-pr-4", "pr-9") --
# matching this release-naming convention, not a bare "pr" substring, so it
# doesn't also catch things like "prometheus-xyz" or this dashboard's own
# "preview-environment-xxxxx" pod. See tracked_pods.py.
TRACKED_POD_NAME_PATTERN = r"(?:^|-)pr-\d+(?:-|$)"

# Annotation keys other projects may set on their pods for richer display.
# Any of them missing just falls back to "unknown"/"" per pod.
ANN_APP = "preview.dashboard/app"
ANN_COMMIT_SHA = "preview.dashboard/commit-sha"
ANN_RELEASE_ID = "preview.dashboard/release-id"
ANN_TITLE = "preview.dashboard/title"
ANN_VERSION = "preview.dashboard/version"

# FastAPI app metadata.
APP_TITLE = "Preview Environment Dashboard"
APP_DESCRIPTION = "Live metadata for an on-demand Kubernetes preview environment."

# Jinja2 template settings.
TEMPLATES_DIR = "templates"
DASHBOARD_TEMPLATE = "dashboard.html"
