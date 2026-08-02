# preview-dashboard Helm chart

Deploys the Preview Environment Dashboard to OpenShift. Each PR gets its own
Helm release (`pr-<number>`) in a shared namespace, torn down when the PR closes.

## One-time cluster setup

1. **Namespace** — create the shared namespace previews get deployed into, e.g.:
   ```
   oc new-project previews
   ```

2. **CI ServiceAccount + token** — create a ServiceAccount for CI and grant it
   `admin` (not just `edit`) on that namespace. `admin` is required because the
   chart creates a Role/RoleBinding per release (for the app's own `/pod-status`
   check), and `edit` is intentionally forbidden from managing RBAC:
   ```
   oc create serviceaccount preview-ci -n previews
   oc adm policy add-role-to-user admin -z preview-ci -n previews
   oc create token preview-ci -n previews --duration=8760h   # -> OPENSHIFT_TOKEN
   ```

3. **Expose the internal image registry** (cluster-admin, one-time, only if not
   already done on this cluster):
   ```
   oc patch configs.imageregistry.operator.openshift.io/cluster \
     --type merge -p '{"spec":{"defaultRoute":true}}'
   oc get route default-route -n openshift-image-registry -o jsonpath='{.spec.host}'
   ```

## GitHub repo configuration

| Name | Type | Value |
|---|---|---|
| `OPENSHIFT_SERVER` | secret | cluster API URL, e.g. `https://api.mycluster.example.com:6443` |
| `OPENSHIFT_TOKEN` | secret | token from the `preview-ci` ServiceAccount above |
| `OPENSHIFT_REGISTRY` | secret | the exposed registry route host from step 3 |
| `OPENSHIFT_NAMESPACE` | variable | `previews` (or whatever you named it in step 1) |

With those set, `.github/workflows/preview-deploy.yml` and
`preview-cleanup.yml` handle the rest automatically.

## Manual install (for testing outside CI)

```
helm upgrade --install pr-test ./helm/preview-dashboard \
  --namespace previews \
  --set image.repository=image-registry.openshift-image-registry.svc:5000/previews/preview-dashboard \
  --set image.tag=<tag-you-pushed> \
  --set env.mrReleaseId=pr-test
```

See `values.yaml` for the full set of configurable values (resources, route
host/TLS, probe timing, etc).
