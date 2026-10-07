---
name: bytedance-byteflow
description: Use when users ask about ByteFlow apps, statemachines, revisions, executions, current workflow nodes, workflow JSON/ASL syntax, BRN resources, or bytedcli ByteFlow CLI support, including safe query/update/revision/start/stop/retry/delete/activity/DAG operations.
---

# ByteFlow

This is the bytedcli-bundled form of the byteflowcli MVP skill. ByteFlow is ByteDance's workflow engine. Use this skill to query ByteFlow metadata and execution status, reason about workflow JSON, and plan safe statemachine/revision operations.

## Safety First

- Default to read-only operations: app list/get, statemachine list/get, revision list, execution list/get/events/current, express execution list/events, activity list/get, DAG list/get/execution queries, local workflow validation/explanation.
- Do not modify existing online flows unless the user explicitly names the target and confirms the write.
- Every write requires human confirmation: run `--dry-run` first, show `required_confirm_write` to the user, and only execute after the user explicitly confirms that exact target.
- Treat app tokens, JWTs, `sa_secret`, `token`, `Authorization`, cookies, and secrets as sensitive. Never print raw credentials.
- For writes, do a dry-run summary first: app, statemachine id/name, latest revision, intended endpoint, payload source, and rollback/verification plan.
- Prefer creating or updating a disposable/test workflow over touching production flows.

## Authentication

Use `bytedcli` to obtain ByteCloud JWT on this machine:

```bash
JWT=$(bytedcli auth get-bytecloud-jwt-token)
```

If `bytedcli` is unavailable, install it and complete `bytedcli auth login` first.

Security: JWTs and app tokens are sensitive; do not echo the raw token unless the user explicitly asks.

## Quick Commands

Prefer the top-level bytedcli command. The command forwards to this skill's bundled helper:

```bash
bytedcli byteflow app list --subscribed-only --name example
bytedcli byteflow app get --app example_app
bytedcli byteflow statemachine list --app example_app
bytedcli byteflow statemachine list --site i18n-tt --region-id Singapore-Central --resource-account bytedance --app example_app
bytedcli byteflow statemachine get --app example_app --id 12345
bytedcli byteflow revision list --app example_app --statemachine-id 12345
bytedcli byteflow execution list --app example_app
bytedcli byteflow execution list --app example_app --statemachine-id 12345
bytedcli byteflow execution current --url https://example.test/byteflow/app/example_app/execution/12345
bytedcli byteflow execution events --app example_app --id 12345
bytedcli byteflow express list --app example_app
bytedcli byteflow express events --app example_app --id 12345
bytedcli byteflow activity list --app example_app --name sample_activity
bytedcli byteflow activity get --app example_app --name sample_activity
bytedcli byteflow dag list --app example_app
bytedcli byteflow dag get --app example_app --id 12345
bytedcli byteflow dag execution list --app example_app
bytedcli byteflow dag execution get --app example_app --id 12345
bytedcli byteflow dag execution events --app example_app --id 12345
bytedcli byteflow statemachine update --app demo_workflow --id 12345 --file examples/standard-workflow.json --dry-run
bytedcli byteflow workflow validate --file examples/standard-workflow.json
bytedcli byteflow workflow explain --file examples/standard-workflow.json
```

Write commands are guarded by `--dry-run`, `--yes`, and a per-operation `--confirm-write` phrase:

```bash
bytedcli byteflow app subscribe --app example_app --dry-run
bytedcli byteflow app unsubscribe --app example_app --dry-run
bytedcli byteflow statemachine create --app demo_workflow --name demo_sm_YYYYMMDD_HHMMSS --file examples/standard-workflow.json --dry-run
bytedcli byteflow statemachine update --app demo_workflow --id 12345 --file workflow.json --dry-run
bytedcli byteflow statemachine delete --app demo_workflow --id 12345 --dry-run
bytedcli byteflow revision create --app demo_workflow --statemachine-id 12345 --name demo-revision --dry-run
bytedcli byteflow revision delete --app demo_workflow --statemachine-id 12345 --revision-number 1 --dry-run
bytedcli byteflow execution start --app example_app --payload-file payload.json --dry-run
bytedcli byteflow execution retry --app example_app --id 12345 --dry-run
bytedcli byteflow execution stop --app example_app --id 12345 --dry-run
bytedcli byteflow execution delete --app example_app --id 12345 --dry-run
bytedcli byteflow express start --app example_app --payload-file payload.json --dry-run
bytedcli byteflow activity create --app example_app --name sample_activity --payload-file payload.json --dry-run
bytedcli byteflow activity update --app example_app --name sample_activity --payload-file payload.json --dry-run
bytedcli byteflow activity delete --app example_app --name sample_activity --dry-run
bytedcli byteflow dag create --app example_app --payload-file payload.json --dry-run
bytedcli byteflow dag update --app example_app --id 12345 --payload-file payload.json --dry-run
bytedcli byteflow dag delete --app example_app --id 12345 --dry-run
bytedcli byteflow dag execution start --app example_app --payload-file payload.json --dry-run
bytedcli byteflow dag execution stop --app example_app --id 12345 --dry-run
```

Legacy helper-shaped forms such as `bytedcli byteflow execution-current` still pass through for compatibility, but new examples should use the bytedcli-style noun/verb command form.
For TikTok ROW ByteFlow consoles under `https://cloud.tiktok-row.net`, pass helper site `--site i18n-tt` (aliases `row` and `tiktok-row` are also accepted). Keep the helper `--site` after the ByteFlow leaf command, for example `bytedcli byteflow statemachine list --site i18n-tt ...`, so the Python helper receives it.
The helper redacts sensitive fields, omits large workflow definitions unless `--include-definition` is passed, and requires explicit write confirmation.
For every write, run dry-run first, show the target and online-risk summary to the user, then only execute after the user confirms that specific operation. Copy the exact `required_confirm_write` value from dry-run into `--confirm-write`; never reuse a phrase from another operation.
For `--payload-file` write commands, the dry-run output includes `payload_sha256`, and the confirmation phrase includes that digest so a changed payload cannot reuse an older confirmation.
For workflow definition writes (`statemachine create` and `statemachine update`), the dry-run output includes `workflow_sha256`, and the confirmation phrase includes that digest so a changed workflow file cannot reuse an older confirmation.
Keep revision names short; the helper rejects names longer than 30 characters before calling the API.
For `statemachine update` and `revision create`, the helper first checks online revisions. If the statemachine has no revision yet, it blocks execution and requires explicit user consent plus `--allow-first-revision-risk`.
For status-sensitive execution writes, the helper reads the current status first. `execution stop` and `dag execution stop` expect `Running`; `execution retry` expects `Failed` or `Cancelled`; `execution delete` expects a terminal state. If the status does not match, live execution is blocked unless the user explicitly accepts the mismatch and the command is rerun with `--allow-status-risk`.

## Workflow Validation Standard

Before proposing or writing a workflow definition, run the validator through the top-level command:

```bash
bytedcli byteflow workflow validate --file workflow.json
```

Use `bytedcli byteflow workflow explain --file workflow.json` when you need per-state notes. `workflow validate`, `workflow explain`, `statemachine create`, and `statemachine update` reuse the same bundled validator, so write paths fail before any API call when syntax checks have errors.

The validator emits fixed check IDs:

- `WF001_JSON_OBJECT`: workflow root is an object.
- `WF002_REQUIRED_TOP_LEVEL`: `StartAt` and `States` are present and usable.
- `WF003_STARTAT_TARGET`: `StartAt` points to an existing state.
- `WF004_STATE_OBJECT_AND_TYPE`: every state is an object with a supported type.
- `WF005_TRANSITION_TARGETS`: `Next`, `Default`, `Choices[].Next`, and `Catch[].Next` targets exist.
- `WF006_TERMINATION`: states use valid `Next` / `End:true` / terminal semantics.
- `WF007_CHOICE_SHAPE`: `Choice` branches have usable targets and condition-like fields.
- `WF008_TASK_RESOURCE`: `Task.Resource` is present and warns on unknown BRN shapes.
- `WF009_WAIT_SHAPE`: `Wait` uses exactly one valid wait field.
- `WF010_RETRY_CATCH_SHAPE`: `Retry` and `Catch` arrays are shaped correctly.
- `WF011_PARALLEL_SHAPE`: `Parallel.Branches` exists and nested branches validate.
- `WF012_MAP_SHAPE`: `Map.Iterator` or `Map.ItemProcessor` exists and validates.
- `WF013_REACHABILITY`: states are reachable from `StartAt`.
- `WF014_TERMINAL_REACHABILITY`: a terminal state is reachable from `StartAt`.

If the script cannot be used, apply the manual checklist in `references/workflow-syntax.md` and report that the validation was manual.

## Classic API Model

Read `references/api.md` when you need endpoint details.

Important facts:

- Classic API base on CN: `https://cloud.bytedance.net/api/v1/byteflow/api/v1`
- App APIs use `x-jwt-token`.
- Statemachine/revision/execution/activity/DAG APIs require both `x-jwt-token` and `Authorization: Bearer <app token>`.
- The app token comes from `GET /apps/{appName}` and must stay in memory only.
- Add `Bf-Cluster`, default `default`, for app-scoped APIs.

For execution URLs, use `execution current --url <console-url>` first. It fetches execution detail and events, then reports `status`, `active_states`, and recent events. `active_states` is derived by pairing `*StateEntered` events with `*StateExited` / `*StateFailed` events, so parallel executions can report more than one active node.
If Python TLS validation fails on an internal CA chain, rerun the same read command with `--insecure`.
Use `execution list`, `activity list`/`activity get`, `dag list`/`dag get`, and `dag execution *` for console inventory questions. Use `express list` and `express events` for the console's Express Execution tab. For create/start/retry/stop/delete operations, use the matching helper write command only after the user has reviewed the dry-run output and explicitly confirmed the exact `required_confirm_write` phrase.

Classic revision create does not accept workflow JSON directly. The workflow update flow is:

1. `PUT /statemachines/{id}` with the updated statemachine payload.
2. `POST /statemachines/{id}/revisions` with `{ "revision_name": "...", "description": "..." }`.

Before step 1 or 2, always query `GET /statemachines/{id}/revisions?page_no=1&page_size=1`.
If the online revision count is 0, stop and ask the user to confirm, explicitly saying that updating the definition or creating the first revision may introduce online risk or change how executions/releases resolve the workflow.

## Workflow Syntax

Read `references/workflow-syntax.md` when generating, reviewing, or explaining a workflow.

ByteFlow is ASL-compatible. Common top-level fields:

- Required: `StartAt`, `States`
- Optional: `Comment`, `TimeoutSeconds`, `Version`, `ContextMergeStrategy`

Common state types:

- `Task`, `Choice`, `Succeed`, `Fail`, `Pass`, `Wait`, `Parallel`, `Map`

Known BRN resource shapes:

```text
brn:byteflow:::{AppName}/stateMachine/{StateMachineName}:startExecution.{action-mode}
brn:byteflow:::{AppName}/stateMachine/{StateMachineName}/{RevisionNumber}:startExecution.{action-mode}
```

Known action modes: `requestResponse`, `sync`.

## Response Pattern

When answering ByteFlow questions:

- Say which facts are confirmed from docs/API/frontend bundle and which are inferred.
- If the user asks for an operation, show the exact read or dry-run command before doing any write.
- For workflow JSON, run the validator first, then summarize state count, state types, transitions, validation errors, warnings, and risky areas.
- For execution URLs, run `execution current --url <url>` and answer from `status`, `active_states`, and `last_events`.
- If a write is requested, require explicit confirmation for that individual write. Do not batch-confirm multiple writes, and do not treat a broad "go ahead" as consent for later writes.
- After dry-run, repeat the exact app, statemachine/revision target, endpoint, and risk in chat before executing. Execute only with `--yes --confirm-write <required_confirm_write>`.
- For online write tests, prefer creating a brand-new uniquely named statemachine and only creating revisions on that newly created statemachine.
- Before updating a statemachine or creating a revision, check whether online revisions already exist. If none exist, do not proceed until the user explicitly accepts the risk.

## References

- API and auth details: `references/api.md`
- Workflow/ASL syntax: `references/workflow-syntax.md`
- Example standard workflow: `examples/standard-workflow.json`
