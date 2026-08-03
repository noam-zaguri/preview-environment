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

The dashboard discovers pods **by name**, not by label — no registration
call, no extra service. A pod is tracked if its name contains a
`pr-<number>` segment. The workflow here already deploys as release
`pr-<number>` (see `RELEASE_NAME` in `preview-deploy.yml`), and Helm names
every resource after the release, so this "just works" as long as you don't
override that naming.

`templates/deployment.yaml` in this chart also sets annotations on the
**pod template** for richer display (optional — a bare `pr-<number>` name
with no annotations still shows up, just with less detail):

```yaml
annotations:
  preview.dashboard/app: "<your-app-name>"
  preview.dashboard/release-id: "pr-<number>"
  preview.dashboard/commit-sha: "<git-sha>"
  preview.dashboard/title: "<PR title>"
  preview.dashboard/version: "<git-sha>"
```

Once your pod goes `Running`, it appears in the dashboard's "Tracked Preview
Pods" table within a few seconds. When `preview-cleanup.yml` runs
`helm uninstall` on PR close, the pod is gone and it just stops appearing on
the next poll.
