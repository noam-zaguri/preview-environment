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

# Fallback values used when the corresponding env var is not set.
DEFAULT_COMMIT_SHA = "unknown"
DEFAULT_MR_RELEASE_ID = "unknown"
DEFAULT_MR_TITLE = ""
DEFAULT_APP_VERSION = "dev"
DEFAULT_ENVIRONMENT = "preview"
DEFAULT_PORT = "8000"

# FastAPI app metadata.
APP_TITLE = "Preview Environment Dashboard"
APP_DESCRIPTION = "Live metadata for an on-demand Kubernetes preview environment."

# Jinja2 template settings.
TEMPLATES_DIR = "templates"
DASHBOARD_TEMPLATE = "dashboard.html"
