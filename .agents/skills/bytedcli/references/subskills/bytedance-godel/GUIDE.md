---
name: bytedance-godel
description: "Always use this skill for direct, read-only Godel Explainer scheduler-placement diagnosis when the user has an exact Kubernetes cluster, namespace, and Pod, PodGroup, or Application name, wants to list Godel clusters, or wants to inspect an existing Godel diagnosis id. It covers pending placement, static/FIFO checks, and node-group capacity through the CN or I18N production API. Do not invent coordinates or adjacent-platform, Fed, BOE, I18NBD, EUTTP, or USTTP routes. Use the Primus, Forge, or Flink skill instead when the request is about those platforms and exact Godel coordinates are not available."
---

# Godel Explainer

Use `bytedcli godel ...` for direct, read-only scheduling diagnosis. `instance get` requires exact Kubernetes coordinates: cluster, namespace, and workload name. The command never kills a FIFO queue head, resubmits a workload, changes priority, adds tolerations, or modifies cluster state.

## Routing boundary

- Use `godel` for a pending Pod, PodGroup, or Application when exact `cluster`, `namespace`, and `name` values are available.
- Use `godel cluster list` to confirm that the cluster belongs to the selected production deployment.
- Use `primus` or `forge` to inspect an original Primus/Forge URL. This Godel command does not accept those URLs or resolve their workload coordinates.
- Do not use `godel` for Fed task-name/IDC log reconciliation; that route is not supported in this version.
- Use `flink` for Godel stream-applications/Flink Web runtime questions such as job status, checkpoints, failover, lag, backpressure, TaskManager, or JobManager.

If the user has only an adjacent-platform URL or task selector, obtain the exact Godel coordinates through the corresponding platform workflow or ask for them. Do not guess a cluster, namespace, or workload name.

## Supported production deployments

| `--site`  | Production API origin                    | Status             |
| --------- | ---------------------------------------- | ------------------ |
| `cn`      | `https://godel-explainer.byted.org`      | Supported; default |
| `i18n-tt` | `https://godel-explainer-i18n.byted.org` | Supported          |

`boe`, `i18n-bd`, `eu-ttp`, and `us-ttp` fail closed. bytedcli does not fall back to a UI host or another region.

## Commands

```bash
# List clusters in the CN production deployment
bytedcli --json --site cn godel cluster list --page 1 --page-size 20 --timeout-ms 20000

# List clusters in the I18N production deployment
bytedcli --json --site i18n-tt godel cluster list --page 1 --page-size 20 --timeout-ms 20000

# Diagnose an exact Pod; --type defaults to pod
bytedcli --json --site cn godel instance get \
  --cluster demo-cluster \
  --namespace demo-namespace \
  --name demo-pod \
  --type pod

# Diagnose an Application in I18N
bytedcli --json --site i18n-tt godel instance get \
  --cluster demo-cluster \
  --namespace demo-namespace \
  --name demo-application \
  --type application \
  --timeout-ms 120000

# Reuse an existing diagnosis id for the same exact target
bytedcli --json --site cn godel instance get \
  --cluster demo-cluster \
  --namespace demo-namespace \
  --name demo-pod \
  --diagnosis-id demo-diagnosis-id

```

`--json` and `--site` are global options and must appear before `godel`.

## Diagnosis controls

- `--cluster`, `--namespace`, and `--name` are all required for `instance get`.
- `--type` accepts `pod`, `podgroup`, or `application` and defaults to `pod`.
- `--diagnosis-id` retrieves an existing result for the same exact target. If it is missing or expired, rerun without the option to create a fresh read-only diagnosis.
- `--timeout-ms` sets the HTTP timeout in milliseconds. Use a larger bounded value for a long diagnosis instead of retrying without a deadline.
- `cluster list` defaults to `--page 1 --page-size 20`; use later pages to inspect the bounded cluster catalog.

## Read the result

Prefer JSON for agent workflows. Confirm that the returned `requested_target` and `resolved_target` match the exact workload coordinates before interpreting the diagnosis.

- Static-check and FIFO entries are diagnostic evidence, not authorization to delete or resubmit a workload.
- The summary includes scheduling status, the backend message, and bounded node-group counts. Inspect `result.diagnosis` for the validated and bounded diagnostic evidence retained by the CLI.
- A backend response saying that no pending unit exists means the workload was not in Godel's pending scheduling queue when queried. It is not a historical diagnosis of a task that has already started or finished.
- Do not infer a healthy workload from missing historical evidence, and do not probe unrelated clusters after a failed exact lookup.
