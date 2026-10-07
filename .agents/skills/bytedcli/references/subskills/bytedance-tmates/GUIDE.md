---
name: bytedance-tmates
description: "Operate TMates OpenAPI through bytedcli: inspect and control runs, send follow-up inputs, handle HIL and queued inputs, manage unified spaces, list/read Memory Stores, inspect/export/update/archive managed agents, and list/fetch projects. Use for TMates task URLs, run IDs, run continuation, lifecycle control, unified space IDs, compatible scope IDs, managed agent IDs, and Memory Store IDs."
---

# bytedcli TMates

This skill covers bytedcli TMates OpenAPI commands:

- `tmates auth check`
- `tmates project list`
- `tmates project get`
- `tmates run list`
- `tmates run get`
- `tmates run create`
- `tmates run send`
- `tmates run cancel|start|close`
- `tmates run hil submit`
- `tmates run queue update|delete`
- `tmates space list|get|create|update|delete`
- `tmates memory store list|get`
- `tmates memory file list|read`
- `tmates agent list`
- `tmates agent get`
- `tmates agent export`
- `tmates agent update`
- `tmates agent archive`
- `tmates agent unarchive`

Space, run, and agent write commands require `--yes`. Run control commands submit one request and return immediately; polling, retry, timeout, and ongoing conversation orchestration belong to the calling system or agent. Personal agent discovery is not exposed by TMates OpenAPI yet; when working with personal agents, copy the numeric agent ID from the TMates Web URL and use `tmates agent get --id <agent-id>`.

## When to use

Use this skill when the user asks to inspect or debug TMates data:

- TMates task share URLs such as `https://tmates.tiktok-row.net/task/share/<run_id>`
- TMates sandbox run status, messages, toolcalls, or resources
- Sending a follow-up input to an existing run without waiting for a reply
- Cancelling a running run, starting a sleeping run, or closing a waiting run
- Responding to permission/form HIL requests
- Inspecting, updating, deleting, or clearing undelivered queued inputs
- MP2C Regression Steward managed-agent sessions
- TMates unified Space discovery and lifecycle, including viewer permissions and app/member summaries
- Memory Store discovery by a unified or known compatible scope ID, followed by file listing and text-preview reads
- TMates managed agent run history by known agent ID
- TMates managed agent lookup, export, update, archive, or unarchive by known agent ID
- Creating a run from a managed agent using the agent's configured repositories
- Checking whether current bytedcli auth can call TMates OpenAPI

## Authentication

TMates OpenAPI uses ByteCloud JWT in `x-jwt-token` plus the OpenAPI header `domain: tiktok_tmates;v1`.

For the TikTok ROW gateway, use the i18n-tt site:

```bash
bytedcli --site i18n-tt auth login
bytedcli --site i18n-tt tmates auth check
```

`--site` and `--json` are global options and must be placed before `tmates`.

## Quick Start

```bash
# Check current user authorization.
bytedcli --site i18n-tt tmates auth check

# List followed TMates projects.
bytedcli --site i18n-tt tmates project list

# Resolve a Codebase repo to a TMates project without creating a missing project.
bytedcli --site i18n-tt tmates project get --repo example-org/example-repo

# Inspect a sandbox run summary.
bytedcli --json --site i18n-tt tmates run get --run-id demo-run-id

# List recent runs created from a managed agent.
bytedcli --site i18n-tt tmates run list --managed-agent-id demo-agent-id

# Create a run from a managed agent. Without repo flags, TMates uses the agent's configured repos.
bytedcli --site i18n-tt tmates run create --managed-agent-id demo-agent-id --prompt 'Review this MR' --yes

# Send one follow-up input and return immediately.
bytedcli --site i18n-tt tmates run send --run-id demo-run-id --message 'Continue with the review' --yes

# Inspect queued inputs and pending HIL tunnels before acting.
bytedcli --json --site i18n-tt tmates run get --run-id demo-run-id
bytedcli --site i18n-tt tmates run hil submit --run-id demo-run-id --decision allowOnce --yes

# Inspect unified Spaces, agents, and Memory Stores.
bytedcli --site i18n-tt tmates space list
bytedcli --site i18n-tt tmates space get --id demo-space-id
bytedcli --site i18n-tt tmates agent list --space-id demo-space-id
bytedcli --site i18n-tt tmates agent get --id demo-agent-id
bytedcli --site i18n-tt tmates memory store list --space-id demo-space-id
bytedcli --site i18n-tt tmates memory file list --store-id demo-memory-store-id
bytedcli --site i18n-tt tmates memory file read --store-id demo-memory-store-id --path MEMORY.md

# Export, edit, and update a managed agent by ID.
bytedcli --site i18n-tt tmates agent export --id demo-agent-id --out agent.json
bytedcli --site i18n-tt tmates agent update --id demo-agent-id --from-file agent.json --yes
```

## Output Boundaries

The CLI returns normalized summaries instead of raw TMates payloads:

- Managed agent detail reports prompt length and config key summaries, not the raw system prompt or raw config body.
- `agent export` writes an editable JSON config and relies on the official OpenAPI projection, which omits Lark secret fields.
- Agent export/update preserves `memoryStoreIds`; review this list before updating an agent because it controls which Memory Stores the agent mounts.
- Run detail reports bounded previews for prompt, messages, tool inputs/outputs, HIL tunnel content, queued input content, and errors. It also exposes `waitingAt`, `failureReason`, `queuedInputs`, `tunnels`, `errors`, and `airbMossUrl` for caller-owned orchestration.
- Unified `space get` returns redacted, non-round-trippable config summaries. Do not copy a redacted config back into `space update`; provide a complete config JSON file instead.
- Memory file reads return text previews only. Binary files omit content, and text files larger than 256 KiB are marked `truncated: true`.
- Use `--message-limit`, `--toolcall-limit`, and `--preview-length` to control run summary size.

This keeps routine agent debugging useful while reducing accidental leakage of session content, environment values, or agent configuration secrets.

## Command Notes

### `tmates project get`

`project get` calls the OpenAPI project lookup with `createIfNotExist=false`. It does not create projects.

```bash
bytedcli --json --site i18n-tt tmates project get --repo example-org/example-repo
```

### `tmates run get`

Use the numeric run id from a TMates share URL:

```bash
bytedcli --json --site i18n-tt tmates run get --run-id demo-run-id --message-limit 5 --toolcall-limit 10
```

The JSON result includes status, managed-agent version identifiers, project/space ids, message/tool/resource counts, recent message previews, recent toolcall previews, resources, and toolcall status counts.

It also includes state-machine fields needed by integrations:

- `waitingAt` and `failureReason`
- `queuedInputCount` and bounded `queuedInputs[]`
- `tunnelCount` and bounded `tunnels[]`
- `errorCount` and bounded `errors[]`
- `airbMossUrl` when a dynamic local pool exposes one

Use these fields to decide the next atomic command. The CLI does not provide a built-in wait loop.

### `tmates run list`

Use this to list lightweight run history for a known managed agent ID:

```bash
bytedcli --json --site i18n-tt tmates run list --managed-agent-id demo-agent-id --page 1 --page-size 20
```

The JSON result includes `managedAgentId`, `total`, `page`, `page_size`, and `runs[]` with lightweight run metadata. It does not include raw messages, toolcalls, or resources; call `tmates run get --run-id <id>` for detail.

### `tmates run create`

Use this to start a run. Pass exactly one primary target — `--managed-agent-id`, `--team-id`, or `--dynamic-workflow-id`:

```bash
bytedcli --site i18n-tt tmates run create --managed-agent-id demo-agent-id --prompt 'Review this MR' --yes
bytedcli --site i18n-tt tmates run create --team-id demo-team-id --prompt 'Let the team handle it' --yes
bytedcli --site i18n-tt tmates run create --dynamic-workflow-id demo-workflow-id --prompt 'Workflow input' --yes
```

When no repository override is provided, a managed-agent run uses the agent's configured repositories, matching the Web agent run behavior. Use `--repo <repoPath> --branch <branch>`, `--project-id <id> --branch <branch>`, or `--project-list <json>` only when explicitly overriding that default. Do not combine `--project-list` with `--repo`, `--project-id`, or `--branch`.

Execution controls (all optional):

- `--environment-id <id>`: run inside a specific Managed Environment.
- `--managed-agent-version-id <id>`: pin a managed-agent config version (requires `--managed-agent-id`).
- `--execution-plane cloud|devbox|local_daemon`: pick the execution plane (default cloud).
- `--devbox-pool-id <id>`: required with `--execution-plane devbox` unless `--team-id` is set; rejected on other planes.
- `--local-agent-id <id>` / `--local-workspace-cwd <path>`: bind a local-daemon run to a Local Agent machine; both require `--managed-agent-id`.
- `--cloud-sandbox-region auto|i18n|cn`: cloud sandbox region override.

```bash
bytedcli --site i18n-tt tmates run create --managed-agent-id demo-agent-id --environment-id demo-env-id --prompt 'Run in a specific environment' --yes
bytedcli --site i18n-tt tmates run create --managed-agent-id demo-agent-id --execution-plane devbox --devbox-pool-id demo-pool-id --prompt 'Run on devbox' --yes
```

`--team-id` and `--dynamic-workflow-id` cannot be combined with `--managed-agent-id`, `--local-agent-id`, or `--execution-plane local_daemon`; `--dynamic-workflow-id` also cannot take repository overrides.

### `tmates run send`

Submit one follow-up input and return as soon as OpenAPI accepts it:

```bash
bytedcli --site i18n-tt tmates run send --run-id demo-run-id --message 'Continue with the review' --yes
bytedcli --site i18n-tt tmates run send --run-id demo-run-id --message $'Check the failure.\nThen propose a fix.' --yes
```

When the run is already executing, TMates may place the input in `queuedInputs`. Call `run get` to inspect queue state. For structured attachments, pass `--attachments-file <path>` containing a JSON array of public TMates `TaskAttachment` objects; do not embed file content in `--message`.

## Markdown 多行换行（必读）

传多行 `--message` 时使用 shell 的 `$'...'`，不要在普通双引号中写字面量 `\n`：

```bash
# 正确：shell 会传入真实换行
bytedcli --site i18n-tt tmates run send \
  --run-id demo-run-id \
  --message $'Check these items:\n- first\n- second' \
  --yes

# 错误：普通双引号不会把 \n 解释成换行
bytedcli --site i18n-tt tmates run send \
  --run-id demo-run-id \
  --message "first\nsecond" \
  --yes
```

### `tmates run cancel` / `start` / `close`

```bash
bytedcli --site i18n-tt tmates run cancel --run-id demo-run-id --yes
bytedcli --site i18n-tt tmates run start --run-id demo-run-id --message 'Continue' --yes
bytedcli --site i18n-tt tmates run start --run-id demo-run-id --message 'Start fresh' --reset-context --yes
bytedcli --site i18n-tt tmates run close --run-id demo-run-id --yes
```

`start --reset-context` requires `--message`. `close` is intended for a waiting run whose sandbox should be released.

### `tmates run hil submit`

Read pending tunnel IDs and metadata from `run get`, then submit one HIL response:

```bash
bytedcli --site i18n-tt tmates run hil submit --run-id demo-run-id --decision allowOnce --tunnel-id demo-tunnel-id --yes
bytedcli --site i18n-tt tmates run hil submit --run-id demo-run-id --decision deny --deny-reason 'Not approved' --yes
bytedcli --site i18n-tt tmates run hil submit --run-id demo-run-id --decision allow --form-data '{"choice":"demo"}' --yes
```

Allowed decisions are `allow`, `allowOnce`, and `deny`. `deny` requires `--deny-reason`; the other decisions reject it. `--form-data` must be a JSON object.

### `tmates run queue`

Queued input mutations apply only while the input remains undelivered:

```bash
bytedcli --site i18n-tt tmates run queue update --run-id demo-run-id --message-id demo-message-id --message 'Updated input' --yes
bytedcli --site i18n-tt tmates run queue delete --run-id demo-run-id --client-message-id demo-client-message-id --yes
bytedcli --site i18n-tt tmates run queue delete --run-id demo-run-id --all --yes
```

For a single-item update/delete, pass exactly one of `--message-id` or `--client-message-id`, using identifiers returned by `run get`. Pass `--all` alone to delete every undelivered input. Results such as `already_delivered` and `not_found` are business outcomes; inspect the structured result instead of automatically retrying.

### `tmates space`

`tmates space` always uses the current unified Space API:

```bash
bytedcli --site i18n-tt tmates space list --keyword demo
bytedcli --site i18n-tt tmates space get --id demo-space-id
bytedcli --site i18n-tt tmates space create --name demo-space --description 'Example space' --yes
bytedcli --site i18n-tt tmates space update --id demo-space-id --name demo-space --yes
bytedcli --site i18n-tt tmates space delete --id demo-space-id --yes
```

For a config update, pass `--from-file` with only `mcpConfig`, `skillConfig`, `subAgentConfig`, `pluginConfig`, or `workflowConfig`. Omit a field to preserve it; set a field to `null` to clear it. Do not replay the redacted config summaries from `space get`.

TMates does not expose legacy Space discovery because the legacy Space service is retired.

### `tmates memory`

First discover Memory Stores by a precise space scope, then list/read files:

```bash
# Unified Space is the default.
bytedcli --site i18n-tt tmates memory store list --space-id demo-space-id

# Compatibility scope requires an explicit choice and a known compatible scope ID.
bytedcli --site i18n-tt tmates memory store list --space-id demo-compatible-scope-id --scope-type ma-space

bytedcli --site i18n-tt tmates memory store get --id demo-memory-store-id
bytedcli --site i18n-tt tmates memory file list --store-id demo-memory-store-id
bytedcli --json --site i18n-tt tmates memory file read --store-id demo-memory-store-id --path MEMORY.md
```

`personal` and `project` Memory Stores are intentionally not public OpenAPI resources. Do not work around this limitation with private SDMA endpoints.

### `tmates agent get`

Use this to inspect a managed-agent summary.

```bash
bytedcli --json --site i18n-tt tmates agent get --id demo-agent-id
```

### `tmates agent export` / `update`

Use `agent export` as the template for `agent update`:

```bash
bytedcli --site i18n-tt tmates agent export --id demo-agent-id --out agent.json
bytedcli --site i18n-tt tmates agent update --id demo-agent-id --from-file agent.json --yes
```

The exported JSON may contain full system prompt and config bodies. Review edits before applying them. Fields omitted from the update file are not sent to OpenAPI; explicit `null` values are sent as clear/empty values where OpenAPI accepts them.

`agent list --space-id` defaults to unified `space` scope. For a known compatible scope ID, use `--scope-type ma-space`. bytedcli sends exactly one scope and never probes the other:

```bash
bytedcli --site i18n-tt tmates agent list --space-id demo-space-id
bytedcli --site i18n-tt tmates agent list --space-id demo-compatible-scope-id --scope-type ma-space
```

### Agent IDs and Space IDs

`tmates agent get/export/update/archive/unarchive` operate by managed agent ID and work for personal agents when you know the numeric ID from the Web URL, for example `/space/personal/agents/workflow/2033`.

`tmates agent list --space-id` interprets the ID according to `--scope-type`: unified `space` by default or explicit compatible `ma-space`. TMates OpenAPI does not expose legacy Space discovery, personal agent listing, or public personal/project Memory Stores.

## Safety Guidance

- Do not simulate unsupported Web-only operations by calling `sdma-api.tiktok-row.net` directly from bytedcli.
- `space create`, `space update`, `space delete`, `run create`, `run send`, `run cancel`, `run start`, `run close`, `run hil submit`, `run queue update/delete`, `agent update`, `agent archive`, and `agent unarchive` require `--yes`.
- Run commands are intentionally atomic. Do not add a hidden wait loop around `run send` or lifecycle actions; let the calling integration own polling and retry semantics.
- Avoid pasting raw run messages, raw tool output, system prompts, MCP configs, skill configs, env vars, or long-term memory content into chat unless the user explicitly asks and the data has been reviewed.

## References

- `../../invocation.md`
- `../../troubleshooting.md`
