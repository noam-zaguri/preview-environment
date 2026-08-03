# Template: per-PR preview pod tracked by preview-environment

Copy this into a **new app's own repo** to get per-PR preview pods that show
up automatically on the central `preview-environment` dashboard, and get torn
down on merge/close.

## What to copy

```
helm/sample-app/          -> rename to helm/<your-app-name>/
.github/workflows/preview-deploy.yml
.github/workflows/preview-cleanup.yml
```

## What to change

1. Rename the chart directory and `name:` in `Chart.yaml` to your app's name.
2. In `values.yaml`: set `image.repository`, `port`, `service.port`,
   `tracking.app` to your app.
3. In both workflows, update the `helm upgrade --install ... ./helm/sample-app`
   path to match your renamed chart directory.
4. Make sure your app actually serves whatever path `livenessProbe`/
   `readinessProbe` hit (defaults to `/healthz`) — change those in
   `values.yaml` if your app uses something else.
5. Set these in your repo (GitHub → Settings → Secrets and variables):

   | Name | Type | Value |
   |---|---|---|
   | `OPENSHIFT_SERVER` | secret | same cluster the dashboard deploys to |
   | `OPENSHIFT_TOKEN` | secret | a token with `edit` role on the shared namespace (doesn't need `admin` — this chart has no RBAC of its own) |
   | `GHCR_USERNAME` / `GHCR_PAT` | secret | only if your image is private |
   | `OPENSHIFT_NAMESPACE` | variable | **must be the same namespace** the `preview-environment` dashboard is deployed into — that's how it gets discovered |

## The part that makes it show up on the dashboard

`templates/deployment.yaml` in this chart puts a label and annotations on the
**pod template** (not just the Deployment):

```yaml
labels:
  preview.dashboard/tracked: "true"
annotations:
  preview.dashboard/app: "<your-app-name>"
  preview.dashboard/release-id: "pr-<number>"
  preview.dashboard/commit-sha: "<git-sha>"
  preview.dashboard/title: "<PR title>"
  preview.dashboard/version: "<git-sha>"
```

The dashboard polls the Kubernetes API for that label in its own namespace —
no registration call, no extra service. Once your pod goes `Running`, it
appears in the dashboard's "Tracked Preview Pods" table within a few seconds.
When `preview-cleanup.yml` runs `helm uninstall` on PR close, the pod is gone
and it just stops appearing on the next poll.
