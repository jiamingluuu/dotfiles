# Workflow Debugging

## Durable execution chain

When you need real execution identifiers, follow this order:

1. `instance list` to find the async job.
2. `task list` to get `task_id`, `execute_id`, and `log_id` under that job.
3. `execution get` to inspect node-level execution detail for a specific execution.

```bash
bytedcli aicolate workflow instance list --space <spaceId> --page 1 --page-size 20
bytedcli aicolate workflow task list --job-id <jobId> --space <spaceId>
bytedcli aicolate workflow execution get --id <wfId> --space <spaceId> --execute-id <executeId>
```

## Trace guidance

- `bytedcli aicolate workflow log get` is the thin wrapper over `workflow_api/get_trace`.
- The workflow page's bottom Trace console is a different observability surface.
- A workflow page can show Trace rows even when `workflow_api/get_trace` returns `{}`.
- If the user wants the same rows visible in the page Trace console, or `log get` returns `{}` while the UI clearly has rows, use the page Trace console instead of assuming the execution has no trace data.

```bash
bytedcli aicolate workflow log get --id <wfId> --execute-id <executeId>
```

## Resume

`execution retry` changes execution state. Treat it like a write operation and get explicit approval first.

```bash
bytedcli aicolate workflow execution retry --id <wfId> --space <spaceId> --execute-id <executeId> --event-id <eventId> --data-json '{"key":"value"}'
```

`--event-id` must be a numeric id string from a real interrupted execution event.
Placeholder values such as `demo-event-id` fail backend id parsing before resume business checks.
