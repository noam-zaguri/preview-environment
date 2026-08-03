# preview-dashboard Helm chart

Deploys the Preview Environment Dashboard to OpenShift as a single, permanent
release named `preview-environment` in a shared namespace. It is the central
status page for every *other* preview pod in that namespace — deliberately not
deployed per-PR itself, since a pod that goes down can't tell you it's down if
the dashboard was running on that same pod.

## How other projects show up on the dashboard

Any pod in the shared namespace gets picked up automatically if it carries
this label:

```
preview.dashboard/tracked: "true"
```

Add these annotations too for richer display (all optional — missing ones
just fall back to "unknown" or the bare pod name):

| Annotation | Meaning |
|---|---|
| `preview.dashboard/app` | Human-readable app/project name |
| `preview.dashboard/release-id` | MR/release identifier |
| `preview.dashboard/commit-sha` | Git commit the image was built from |
| `preview.dashboard/title` | e.g. MR title |
| `preview.dashboard/version` | App version / image tag |

Example, from another project's own Deployment manifest:

```yaml
metadata:
  labels:
    preview.dashboard/tracked: "true"
  annotations:
    preview.dashboard/app: "checkout-api"
    preview.dashboard/release-id: "pr-42"
    preview.dashboard/commit-sha: "a1b2c3d..."
    preview.dashboard/version: "a1b2c3d"
```

No registration call, no extra service to run — the dashboard polls the
Kubernetes API for this label on a timer (`GET /api/pods`, see
`tracked_pods.py`), so a newly deployed pod just appears within a few seconds
of going `Running`.

## One-time cluster setup

1. **Namespace** — create the shared namespace preview pods (this dashboard
   and every tracked project) get deployed into, e.g.:
   ```
   oc new-project previews
   ```

2. **CI ServiceAccount + token** — create a ServiceAccount for CI and grant it
   `admin` (not just `edit`) on that namespace. `admin` is required because the
   chart creates a Role/RoleBinding per release (for the app's own
   `/pod-status` and `/api/pods` checks), and `edit` is intentionally
   forbidden from managing RBAC:
   ```
   oc create serviceaccount preview-ci -n previews
   oc adm policy add-role-to-user admin -z preview-ci -n previews
   oc create token preview-ci -n previews --duration=8760h   # -> OPENSHIFT_TOKEN
   ```

3. **GHCR personal access token** — images are pushed to GitHub Container
   Registry (`ghcr.io`) and pulled by the cluster from there. The workflow's
   own `GITHUB_TOKEN` can push (job-scoped, expires when the job ends), but
   the cluster needs a long-lived credential to pull later, so create a
   classic PAT with `read:packages` and store it as `GHCR_PAT` below. If the
   package is private, also make sure that PAT's owner (or the repo) has
   access to it.

## GitHub repo configuration

| Name | Type | Value |
|---|---|---|
| `OPENSHIFT_SERVER` | secret | cluster API URL, e.g. `https://api.mycluster.example.com:6443` |
| `OPENSHIFT_TOKEN` | secret | token from the `preview-ci` ServiceAccount above |
| `GHCR_USERNAME` | secret | GitHub username tied to `GHCR_PAT` |
| `GHCR_PAT` | secret | PAT from step 3, used as the cluster's GHCR pull credential |
| `OPENSHIFT_NAMESPACE` | variable | `previews` (or whatever you named it in step 1) |

With those set, `.github/workflows/deploy-dashboard.yml` deploys/updates the
`preview-environment` release automatically on every push to `main` (or via a
manual `workflow_dispatch` run).

## Manual install (for testing outside CI)

```
helm upgrade --install preview-environment ./helm/preview-dashboard \
  --namespace previews \
  --set image.repository=ghcr.io/<owner>/<repo> \
  --set image.tag=<tag-you-pushed>
```

See `values.yaml` for the full set of configurable values (resources, route
host/TLS, probe timing, etc).
