# Workflow Operations

## Server-side batch Jobs

Use `aicolate batch job create` for the Task Center workflow: it uploads and
validates `--input-csv` before creating the Job. Query lifecycle state with
`batch job list|get|wait`; query row-level executions with `batch task list`.
The latter includes `log_id`, which can be passed to
`bytedcli log get-logid-log` or `bytedcli log footprint search --log-type argos`.

This is separate from `workflow batch run`, which performs client-side JSONL
fan-out and does not create a Task Center Job.

This document is the operational runbook for `bytedcli aicolate workflow`.
Use it for end-to-end workflow execution: inspect, edit, explain, debug, and
lifecycle operations.

## Scope comes before release

```text
AI Colate workflow
├── resource library / 资源库工作流 (project_id absent)
│   └── release one workflow: workflow publish
└── project development / 项目工作流 (project_id present)
    ├── release project version: app workflow publish
    └── serve one workflow through Application Management
        ├── app-service cluster list
        ├── app-service workflow create
        ├── app-service version list
        ├── app-service publish
        ├── app-service publish-record advance
        └── app-service quota publish
```

`workflow list --space <spaceId>` defaults to resource-library workflows.
Add `--project-id <projectId>` to list project workflows. The same flag on
`workflow create` creates the new workflow inside that project. Both scopes use
the same inspect, edit, export, and test-run commands.

Release differs: `workflow publish` is intentionally resource-library-only.
Project workflows are versioned with the entire project and must use
`app workflow publish --id <projectId>`. The CLI rejects an individual publish when the
canvas reports a `project_id`.

## Command surface

Read and inspect:

```bash
bytedcli aicolate workflow list --space <spaceId>                       # resource library
bytedcli aicolate workflow list --space <spaceId> --project-id <projectId>  # project
bytedcli aicolate workflow list --space <spaceId> --keyword <keyword> --mine
bytedcli aicolate workflow list --space <spaceId> --workflow-id <wfIdOrUrl>
bytedcli aicolate workflow get --id <wfIdOrUrl> --space <spaceId>
bytedcli aicolate workflow export --id <wfIdOrUrl> --space <spaceId> --schema
bytedcli aicolate workflow export --id <wfIdOrUrl> --space <spaceId> --format yaml --output dag.yaml
bytedcli aicolate workflow export --id <wfIdOrUrl> --space <spaceId> --format runtime-yaml --output ./fireflow-bundle
bytedcli aicolate workflow import --file ./fireflow-bundle --format runtime-yaml --output dag.json
bytedcli aicolate workflow import --file ./fireflow-bundle --format runtime-yaml --space <spaceId> --project-id <projectId>
bytedcli aicolate workflow summary get --id <wfIdOrUrl> --space <spaceId>
bytedcli aicolate workflow node-types --space <spaceId>
```

Edit and persist:

```bash
bytedcli aicolate workflow apply --id <wfIdOrUrl> --space <spaceId> --ops-file ops.json --dry-run
bytedcli aicolate workflow apply --id <wfIdOrUrl> --space <spaceId> --ops-file ops.json --save
bytedcli aicolate workflow apply --id <wfIdOrUrl> --space <spaceId> --ops-file ops.json --dry-run --save
bytedcli aicolate workflow apply --id <wfIdOrUrl> --space <spaceId> --schema-file dag.json --dry-run
```

`ops.json` is a local file path provided by the user. The `references/` docs in
this skill are shape references, not runtime file paths consumed by the command.

Execute and debug:

```bash
bytedcli aicolate workflow run --id <wfIdOrUrl> --space <spaceId> --input '{"k":"v"}'
bytedcli aicolate workflow run --id <wfIdOrUrl> --space <spaceId> --input '{"k":"v"}' --no-wait
bytedcli aicolate workflow batch run --id <wfIdOrUrl> --space <spaceId> --input-file inputs.jsonl
bytedcli aicolate workflow instance list --space <spaceId>
bytedcli aicolate workflow task list --job-id <jobId> --space <spaceId>
bytedcli aicolate workflow execution get --id <wfIdOrUrl> --space <spaceId> --execute-id <executeId>
bytedcli aicolate workflow log get --id <wfIdOrUrl> --execute-id <executeId>
bytedcli aicolate workflow execution retry --id <wfIdOrUrl> --space <spaceId> --execute-id <executeId> --event-id <eventId> --data-json '{"key":"value"}'
```

Lifecycle:

```bash
bytedcli aicolate workflow create --space <spaceId> --name <name> --desc <desc>  # resource library
bytedcli aicolate workflow create --space <spaceId> --project-id <projectId> --name <name> --desc <desc>
bytedcli aicolate workflow duplicate create --id <wfIdOrUrl> --space <spaceId>
bytedcli aicolate workflow publish --id <wfIdOrUrl> --space <spaceId>  # resource-library only
bytedcli aicolate app workflow publish --id <projectId>                # whole project; auto patch
```

Saving an existing workflow is allowed only when the current user is its owner
or an editable collaborator. Resource-library `workflow publish` has the same
permission boundary. Workflow deletion is intentionally not available in the
CLI.

For resource-library workflows, `workflow publish` defaults to `v0.0.1` for the
first publish, then increments the latest published patch version. Pass
`--workflow-version vMAJOR.MINOR.PATCH` to select a larger version explicitly.

## Project workflow release

`app workflow publish` releases the whole project, including every project workflow and
other project resource in the project version. It checks the version for
duplication and validates selected connectors. Connector `1024` (hosted API) is
used when `--connector-id` is omitted. When `--version` is omitted, the first
semantic version is `v0.0.1`; otherwise the highest existing
`vMAJOR.MINOR.PATCH` version is patch-incremented. An explicit version remains
unchanged and is only checked for duplication.

```bash
# Preview only.
bytedcli aicolate app workflow publish --id <projectId> \
  --version-description "release notes"

# Explicit version override.
bytedcli aicolate app workflow publish --id <projectId> --version v1.2.3 \
  --version-description "release notes"

# Submit.
bytedcli aicolate app workflow publish --id <projectId> --version v1.2.3 \
  --version-description "release notes" --yes
```

Without `--yes` no publish request is sent. Use `app workflow publish-records` to inspect
the resulting project release record.

The authenticated account must be the project creator or a collaborator. The
CLI checks the platform collaboration list before all other publish preflight
and fails closed when the permission metadata is absent. The project publish
request has no operator field; current platform history can show the project
owner rather than the API caller. Actual-caller attribution requires a backend
change to persist the authenticated caller.

## Application Management release

Application Management has two different writes:

1. `app-service cluster list --space <spaceId>` resolves the selectable cluster
   host prefixes. `app-service workflow create` registers a specific project workflow and its
   traffic configuration as an App Service. It rejects resource-library
   workflows, workflows belonging to another project, and host prefixes not in
   that space's cluster list.
2. `app-service publish` creates a release record for an eligible project
   version, using one to four small-traffic stages followed automatically by
   full traffic. `app-service publish-record advance` enters each configured
   stage through a separate write. It reads record detail before and after the
   write, reports stage progress and tells the caller whether to advance again,
   wait, or stop. A completed record is an idempotent no-op.

Quota/config publication is independent from both writes above:
`app-service quota publish` reads the current service configuration, updates the
selected `ROW`, `US-TTP`, and/or `EU-TTP` quotas, preserves omitted regions and
unrelated config, and submits a BPM-backed config publish. App Service creation
still requires initial traffic configuration. Quota publication is allowed only
for the App Service creator or a collaborator, using permission metadata from
the service detail response; missing metadata is denied.

PAT selection returns metadata IDs only; it never returns or needs token
plaintext.

```bash
# Resolve PAT metadata ID.
bytedcli aicolate app-service api-key list

# Resolve the host prefix selectable in this space.
bytedcli aicolate app-service cluster list --space <spaceId>

# Register the workflow-backed service (preview, then submit).
bytedcli aicolate app-service workflow create \
  --space <spaceId> --project-id <projectId> --workflow-id <workflowId> \
  --name <serviceName> --desc <description> --host-prefix <clusterPrefix> \
  --api-id <patMetadataId> --row-qps 3 --us-ttp-qps 2 --eu-ttp-qps 1
bytedcli aicolate app-service workflow create \
  --space <spaceId> --project-id <projectId> --workflow-id <workflowId> \
  --name <serviceName> --desc <description> --host-prefix <clusterPrefix> \
  --api-id <patMetadataId> --row-qps 3 --us-ttp-qps 2 --eu-ttp-qps 1 --yes

# Publish the project first, then pick an App Service-eligible version.
bytedcli aicolate app workflow publish --id <projectId> --version v1.2.3 --yes
bytedcli aicolate app-service version list --id <appServiceId>

# Preview 10% -> 50% -> full traffic, then submit it.
bytedcli aicolate app-service publish --id <appServiceId> --version v1.2.3 \
  --small-traffic-percent 10 --small-traffic-percent 50 --note "go online"
bytedcli aicolate app-service publish --id <appServiceId> --version v1.2.3 \
  --small-traffic-percent 10 --small-traffic-percent 50 --note "go online" --yes

# The initial publish creates the record. Advance only when its output says the
# next stage is ready; the command reports progress and the next required action.
bytedcli aicolate app-service publish-record advance --id <publishRecordId>
bytedcli aicolate app-service publish-record advance --id <publishRecordId> --yes

# Publish quota changes separately (preview, then submit).
bytedcli aicolate app-service quota publish --id <appServiceId> \
  --us-ttp-qps 2 --us-ttp-qpm 120 --eu-ttp-qps 1 --note "quota update"
bytedcli aicolate app-service quota publish --id <appServiceId> \
  --us-ttp-qps 2 --us-ttp-qpm 120 --eu-ttp-qps 1 --note "quota update" --yes
```

For each region, QPM defaults to that region's QPS × 60. App Service creation
requires at least one ROW/US-TTP/EU-TTP QPS or QPM option, accepts QPS `0..10`
and QPM `0..6000` per region, and initializes omitted regions to zero. Later
`app-service quota publish` updates accept QPS `0..100` and QPM `0..6000` per
region while preserving omitted regions. Project and
resource-library workflow publishing both auto-increment a semantic patch version
when their version option is omitted; explicit project versions are only checked
for duplication. App Service versions are selected explicitly from eligible
project versions. Every App Service write defaults to a dry-run and requires
`--yes` to submit. A quota publish result includes a derived BPM ticket URL when
the backend returns `bpm_ticket_id`.

## Workflow URL target resolution

For workflow commands using `--id`, both raw id and page URL are supported:

```text
https://aicolate.tiktok-row.net/agent/work_flow?workflow_id=<wfId>&space_id=<spaceId>
```

Rules:

- If `--id` is a URL and `--space` is omitted, URL `space_id` is used.
- If URL `space_id` and explicit `--space` both exist, explicit `--space` wins.
- For raw workflow id, `--space` is required on space-scoped commands.
- For `workflow list` with repeatable `--workflow-id`, all URL ids must resolve to one
  space when `--space` is omitted.
- Fuzzy workflow-name filtering uses `--keyword`; creator filtering uses `--mine`.

Backend passthrough numeric filters use explicit suffixes so the CLI surface is
honest about raw enum values:

- `workflow list`: `--type-code`, `--status-code`, `--order-by-code`, `--flow-mode-code`, `--schema-type-code`, `--checker-id`, `--bind-biz-type-code`
- `workflow instance list`: `--status-code`, `--order-by-code`, `--job-entity-type-code`
- `workflow task list`: `--status-code`, `--order-by-code`

Known code values (from workflow IDL enums):

- `--status-code` for `workflow list` (`WorkFlowListStatus`):
  - `1`: unpublished
  - `2`: published
- `--order-by-code` (`OrderBy`):
  - `0`: create_time
  - `1`: update_time
  - `2`: publish_time
  - `3`: hot
  - `4`: id
- `--flow-mode-code` (`WorkflowMode`):
  - `0`: workflow
  - `1`: imageflow
  - `2`: sceneflow
  - `3`: chatflow
  - `100`: all (query-only)
- `--schema-type-code` (`SchemaType`):
  - `0`: dag (legacy)
  - `1`: fdl
  - `2`: blockwise (legacy)
- `--checker-id` (`CheckType`):
  - `1`: web_sdk_publish
  - `2`: social_publish
  - `3`: bot_agent
  - `4`: bot_social_publish
  - `5`: bot_web_sdk_publish
- `--bind-biz-type-code` (`BindBizType`):
  - `1`: agent
  - `2`: scene
  - `3`: douyin_bot
- `--status-code` for `workflow instance list` / `workflow task list` (`WorkflowBatchStatus`):
  - `0`: pending
  - `1`: queuing
  - `2`: running
  - `3`: success
  - `4`: fail
  - `5`: canceled
  - `6`: expired
- `--job-entity-type-code` (`WorkflowJobEntityType`):
  - `0`: workflow

## Apply behavior and safety contract

`workflow apply` accepts exactly one input source:

- `--ops-file`: structured ops mutation.
- `--schema-file`: full schema replacement.

Behavior:

- Default (`no --save`) is preview-only.
- `--dry-run` prints diff and does not save by itself.
- `--save` persists schema through `workflow_api/save`.
- `--save` without `--dry-run` skips the full diff preview and returns a
  `diff` marker reminding to add `--dry-run` when you want a preview.
- `--dry-run --save` is valid and runs preview first, then save.
- No-op mutation reports no schema changes and skips unnecessary save.

Safety:

- Always start with dry-run before save.
- Use `--schema-file` only when full replacement is intentional.
- For schema internals and End-node mapping constraints, read
  `workflow-schema.md`.

## Runtime YAML export and import

`workflow export --format runtime-yaml --output <dir>` converts the AICOLATE graph
into a FireFlow runtime bundle. `--output` is required for this format because the
bundle is a directory, not a single file.

The Knowledge Retriever sidecars described below are deliberately customized
for IPR and are emitted only by this export command. Native JSON/YAML export does
not emit them, and runtime import does not consume them. They export executable
retrieval adapters for dataset ids referenced by the workflow, not knowledge-base
documents or a portable, general-purpose knowledge integration.

- The bundle contains `workflow.yaml`, a `prompts/` directory (one YAML per LLM
  prompt), a `knowledge/` directory with one executable Python client per
  Knowledge Retriever node, recursively exported SubWorkflows under
  `subworkflows/<workflowId>/`, and a `manifest.json` listing every exported
  workflow plus adapter warnings.
- IPR-only Knowledge sidecars use
  `knowledge/knowledge_retrieval_<nodeId>.py` for top-level nodes and
  `knowledge/knowledge_retrieval_<ownerNodeId>_<nodeId>.py` for Knowledge
  Retriever blocks nested inside Batch nodes. `knowledge/idl/` contains
  `base.thrift`, the fixed MixRAG retrieve request/response IDL, a minimal
  `MixRagService.Retrieve` service declaration, and `__init__.py` for Euler's
  runtime Thrift import hook.
  The client calls `Retrieve` with buffered transport and fixed IPR service
  routing (for example, `sd://demo.ecom.mixrag?idc=<idc>&cluster=default`).
  PSM, target, timeout, dataset ids, `user_id`, business code, query
  context, and node retrieval settings are emitted as editable constants at the
  top of the Python file; no business value is read from local environment
  variables. As in OpenCoze, MixRAG `USER_ID` is fixed to `1` for experiment
  routing and is not the current account user. The workflow canvas does not
  expose `rag_strategy_id`, so each dataset gets an explicit `None` placeholder
  in `RAG_STRATEGY_IDS`; fill it only when the target service cannot select a
  default strategy. The client exposes `main(inputs)` and a standalone stdin/argv
  entry point, with `Query`/`query` as the runtime input. Execution requires the
  internal `bytedeuler~=2.0` package and a working ByteDance Service Discovery
  environment. Copy the complete `knowledge/` directory: omitting
  `idl/__init__.py` makes `idl` a namespace package and breaks Thrift loading.
  Exporting the sidecar does not change `workflow.yaml` or `manifest.json`;
  FireFlow does not invoke these files automatically.
- Node adaptation: HTTP nodes become standard `code` nodes with generated `urllib`-based request sources. Authentication values are not embedded as credentials; inject them in the runtime when required. RPC/Batch/SubWorkflow and any other unsupported
  node also become `code` nodes, but as non-executing adapters (they carry the
  original semantics for identification, not runnable logic).
- HTTP sources keep an `AICOLATE_NODE_TYPE = 'http'` marker and editable
  `CONFIG`, but do not carry an original-node snapshot. RPC, Batch, SubWorkflow,
  and unknown non-executing adapters additionally keep `AICOLATE_METADATA` in
  their source so import can restore the original node and its outgoing edge
  ports without losing data.
- Natural Code, HTTP, IfElse, and Prompt nodes do not carry
  `AICOLATE_METADATA`. Their editable `input_schema`, `output_schema`,
  `on_error`, and Prompt `parameters` fields preserve native types and runtime
  settings; `platform_id` provides stable cross-node reference remapping without
  storing a node snapshot, including references embedded as
  `{{block_output_<id>.<output>}}`. Import treats the current YAML values as the
  source of truth.
- AICOLATE End nodes are omitted; their inbound routes target FireFlow's
  synthesized `approve` / `reject` / `unknown` terminals.
- The first runtime node is ordered from the AICOLATE Start node's outgoing
  edge. If that edge is missing or does not target a business node, the export
  records a warning instead of silently claiming a valid entry point.
- AICOLATE async code functions without `await` are normalized to the runner
  contract `def main(inputs: dict)`, including `args.params` to `inputs` and
  removal of `Args` / `Output` annotations.
- Use `--no-subworkflows` to export only the root workflow.

`workflow import --file <workflow.yaml | bundleDir> --format runtime-yaml` converts a runtime bundle back
into an AICOLATE schema.

- `--output <path>` writes the converted schema as JSON.
- `--save` persists the converted schema to an existing workflow and requires both
  `--id` and `--space`; omitting either raises `AICOLATE_WORKFLOW_INPUT_ERROR`.
- `--project-id <projectId>` creates a new workflow under the project in the
  specified `--space`, then saves the converted schema. The workflow name comes
  from `workflow.yaml` `name` by default and receives a millisecond timestamp
  suffix to avoid collisions. Explicit `--name` is used as-is; `--desc` sets the
  description.
- Import reads only `workflow.yaml` and `prompts/*.yaml`; `knowledge/*.py` and
  `knowledge/idl/*` are export-only executable resources and are not required
  for schema restoration.
  Natural nodes are rebuilt from their current YAML fields. Only non-natural
  adapter nodes restore their original payload from source-level
  `AICOLATE_METADATA`.
- Code sources are restored to the AICOLATE executor contract
  (`async def main(args: Args) -> Output` with `params = args.params`). HTTP
  adapter markers and `CONFIG` are restored to native AICOLATE HTTP nodes
  (`type: "45"`), and the End node uses id `900001` with the last runtime
  node's outputs mapped into `data.inputs.inputParameters`.

## Durable debugging chain

Use `instance list -> task list -> execution get` for stable identifiers and node-level state.

- `instance list` returns async jobs and high-level status.
- `task list` resolves `task_id`, `execute_id`, and `log_id` under one job.
- `execution get` returns node-level execution details and supports deeper filters:
  `--sub-execute-id`, `--need-async`, `--log-id`, `--node-id`.

`log get` wraps `workflow_api/get_trace`. If logs are empty but UI Trace console
has rows, use the page Trace console as fallback observability.

`execution retry` is a state-changing operation:

- `--event-id` must be a numeric id string from an actual interrupted event.
- Placeholder values (for example `demo-event-id`) fail backend id parsing.
- Require explicit approval before running resume.

## Lifecycle safety

- `create` and `copy` create durable objects; verify with `get` or `export`.
- Resource-library `workflow publish` is externally visible; require explicit
  user intent.
- Project and App Service publish commands preview by default and submit only
  with `--yes`.
- `delete` is irreversible and should never be default behavior.
