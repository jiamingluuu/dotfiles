# BMA command reference

Use `bytedcli bma --help` before selecting a command. All examples use placeholder IDs and do not perform a remote mutation unless `--yes` is explicitly supplied.

## Resource groups

- `bma workspace`, `bma model`, `bma agent`, and `bma session` manage the BMA control-plane resource hierarchy.
- `bma credential`, `bma connector`, and `bma schedule` manage credential metadata and Connector-backed integrations. A Schedule is a Connector type.
- `bma dataset` manages Datasets and their documents. `bma dataset doc update` is FILE replacement only.
- `bma skill` and `bma plugin` manage supported Agent capability metadata.
- `bma skill get` is metadata-only; it does not mix private content download into the read command.
- `bma session wait` polls the management Session control plane until it has a trusted Sandbox binding. `bma session event`, `bma session send`, and `bma session stream execute` use the controlled Runtime bridge associated with that Session. `session send` accepts exactly one of `--prompt-file` or `--events-file`.

## Read examples

```bash
bytedcli --json bma workspace list --page-size 20
bytedcli --json bma agent version list --agent-id "demo-agent" --page-size 20
bytedcli --json bma session list --agent-id "demo-agent" --statuses "pending,running" --page-size 20
bytedcli --json bma session event list --session-id "demo-session" --since-ts 0 --max-events 20
bytedcli --json bma session wait --session-id "demo-session" --timeout-seconds 180 --interval-seconds 2
bytedcli --json bma connector receipt list --connector-id "demo-connector" --statuses "succeeded,failed" --page-size 20
bytedcli --json bma schedule receipt list --schedule-id "demo-schedule" --statuses "succeeded,failed" --page-size 20
bytedcli --json bma skill market search --query "demo" --page 1 --page-size 20
bytedcli --json bma skill agentbuddy search --query "demo" --page 1 --page-size 20
bytedcli --json bma skill agentbuddy-space list --space-url "https://skills.example.com/spaces/demo-space" --page 1 --page-size 20
bytedcli --json bma skill agentbuddy execute --from-file "./demo-skill-updates.json"
bytedcli --json bma connector feishu-scope execute --connector-id "demo-feishu"
bytedcli --json bma connector webhook-eventhub get --connector-id "demo-webhook"
bytedcli --json bma session interrupt execute --session-id "demo-session" --dry-run
bytedcli --json bma session send --runtime local --session-id "demo-local-session" --prompt-file "./demo-prompt.txt" --dry-run
bytedcli --json bma session send --session-id "demo-session" --prompt-file "./demo-prompt.txt" --no-follow --dry-run
bytedcli --json bma connector webhook-eventhub execute --connector-id "demo-webhook" --dry-run
bytedcli --json bma connector feishu-invite create --connector-id "demo-feishu" --app-id "demo-app" --target-email-file "./demo-email.txt" --dry-run
bytedcli --json bma plugin git get --repo-path "demo/repository" --branch "main"
```

Cursor-paginated BMA lists use `--page-size` (default 20, valid range 1-50) and optional `--page-token`; their JSON pagination reports server-returned `page_size` when present, `current_count`, and optional `next_page_token`, without inventing a numeric page from an opaque token. Skill Market and AgentBuddy search commands expose `--page` plus `--page-size` (1-50) and translate them to the backend offset/limit contract. AgentBuddy `agentbuddy-space list` instead requires `--space-url` and sends its one-based `page`/`page_size` contract directly (1-100). Persisted Session event listing is bounded by `--max-events` (maximum 200), not `--page-size`.

Connector receipt 使用 `bma connector receipt` 与 `--connector-id`；Schedule receipt 使用 `bma schedule receipt` 与 `--schedule-id`，不要在 Schedule 场景复用 generic Connector 路由。

User-visible enum options use semantic values and are mapped to the frozen Engine codes internally: Session statuses are `pending,running,idle,terminating,terminated,failed`; receipt statuses are `succeeded,failed,pending,working,zombie` (`processing` is a deprecated backend placeholder and is not accepted); sort order is `asc|desc`; AgentBuddy search uses `--order`; document status is `normal|in-progress|failed|deleted`; document upload type uses `--doc-type file|lark`; update rule is `day|realtime`. Numeric enum values are not accepted at the CLI boundary. Status mutations use the standard `update --status active|disabled` form: `bma connector update`, `bma schedule update`, and `bma dataset update`. Active Schedule creation requires --agent-id and uses the separate CreateConnector path. Draft Schedule status transitions remain blocked because the confirmed Engine activation path applies a Feishu-only validation to all Connector types; configure the Schedule as Draft, but do not attempt `active` or `disabled` until the Engine exposes a Schedule-specific transition.

## Mutation pattern

```bash
# Inspect exactly what would be applied.
bytedcli --json bma agent archive execute --agent-id "demo-agent" --dry-run

# Apply only after the plan has been reviewed.
bytedcli --json bma agent archive execute --agent-id "demo-agent" --yes
```

Use identical inputs for the confirmed invocation. The CLI submits a mutation once and reads the authoritative result back; it does not replay an ambiguous write.

## Protected inputs and Runtime

Use the documented `--*-file` options for sensitive values. On POSIX, inputs must be regular files with mode `0600`.
Credential auth create stores its transient OOB `display_code` only in the protected `--challenge-file`; normal JSON/readback and HTTP traces redact it. Poll an existing protected challenge with `bma credential auth execute`.

```bash
bytedcli --json bma session send --session-id "demo-session" --prompt-file "./demo-prompt.txt" --reconnect-limit 1 --dry-run
bytedcli --json bma session stream execute --session-id "demo-session" --since-ts 0
```

`bma session wait` waits only for the control-plane Sandbox binding; it does not open a Runtime event stream, change SSE timeouts, or reconnect a stream. A non-empty `sandbox_session_id` is the ready condition. Missing, ended, expired, or timed-out Sessions fail closed with a structured error; use `--timeout-seconds` (1-600, default 180) and `--interval-seconds` (1-30, default 2) to bound control-plane polling.

`--no-follow` is managed-prompt-only. It requires explicit `--yes` for a real delivery, cannot be combined with `--events-file`, and is unavailable in `--runtime local` mode. After Runtime Session creation or prompt write succeeds, it returns an accepted-delivery receipt without opening the Runtime event stream; it does not retry an ambiguous write. Use `--no-follow --dry-run` first to inspect the protected-input-redacted mutation plan, then rerun the same command with `--yes` to deliver.

`--since-ts` and `--reconnect-limit` accept non-negative decimal integers. Runtime commands never accept an arbitrary Agent Core base URL.

## Document update boundary

```bash
bytedcli --json bma dataset doc update --dataset-id "demo-dataset" --doc-id "demo-doc" --file "./demo.txt" --file-name "demo.txt" --dry-run
```

The supported update is a non-empty FILE replacement. Lark document updates, metadata-only patches, arbitrary `--doc-type` values, and raw endpoints are intentionally unavailable.

## Contract-blocked capabilities

Draft cleanup uses `bma schedule archive execute`, which calls the dedicated archive operation before an optional delete. Draft status updates remain blocked. Archived Schedule restore remains blocked; do not route either through generic `schedule update --status`.

Do not attempt to synthesize commands for Runtime Config, Connector/Schedule restore, Schedule run-now/next-fire/status, browser OAuth callbacks, or internal Engine bootstrap/token/state APIs. These need a confirmed public backend contract before they can be exposed by `bytedcli`.
