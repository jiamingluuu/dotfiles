# Execution commands

`execution` is the "普通发布工单" scenario — a pipeline-node-level entity identified by an `execution_id` UUID (distinct from `ticket_id` / `train_id`).

Top-level: `bytedcli bytecycle execution ...`

## What is wrapped today

```bash
# Detail by execution_id (UUID)
bytedcli bytecycle execution get --execution-id 5b8c9d6e-...

# Current user's executions
bytedcli bytecycle execution list --mine \
  --status pending \
  --workspace-id <workspace-id> \
  --page 1 --page-size 20
```

Output schema: `{status, data, error, context}` when `--json` is set.

## What is NOT wrapped

The whole write side and the broader query/MR/pipeline integration are not in the CLI yet. Do not expose private execution request details or unwrapped fallback calls to agents. Wait for wrapped commands with typed payload builders before automating these actions.

## Important reminders

- The CLI deliberately ships only the read side until real-world payloads for each write are reviewed. Do **not** synthesize `pipeline_params_map` / `node_key` / `template_id` from the swagger; they depend on the pipeline template definition.
- When adding first-class support, keep request paths and payload schema details in implementation/test fixtures rather than agent-facing skill guidance.
