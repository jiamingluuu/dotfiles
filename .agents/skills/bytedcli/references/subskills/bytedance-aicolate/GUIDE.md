---
name: bytedance-aicolate
description: "Operate AI Colate (Coze + Fornax) via bytedcli: authenticate with ByteCloud JWT or a legacy browser cookie session; distinguish resource-library workflows from project workflows; develop, inspect, and release workflow DAGs; publish whole projects; register project workflows in Application Management, advance staged App Service releases, and publish quota changes; and manage spaces, agents/apps, knowledge bases, plugins, MCP servers, skills, models, connectors, evaluation tasks, result exports, and traces. Includes the IPR-specific Knowledge Retriever Python/IDL sidecars emitted by workflow export --format runtime-yaml. Use when tasks mention AI Colate/aicolate, Coze, AI Application, workflow development or release, Application Management, evaluation, traces, or AI Colate backend Skill resources. AI Colate Skill resources are unrelated to repo Agent skills under skills/."
---

# bytedcli AI Colate (Coze + Fornax large-model platform)

AI Colate ROW uses `aicolate.tiktok-row.net` on the office network and
`aicolate-sg.byted.org` on the production network. It is a Coze + Fornax based
large-model platform with three products: **AI Application**, **Model
Development**, **Model Market**. This skill covers the AI Application surface.

## Auth

AI Colate uses a user ByteCloud JWT by default. bytedcli obtains it from the
`i18n-tt` credential partition and sends it in `x-jwt-token`; business commands
do not require an AI Colate Cookie session.

```bash
bytedcli aicolate auth login
bytedcli aicolate auth status
bytedcli aicolate space list
```

`aicolate auth login` delegates to ByteCloud Auth for `i18n-tt`. The equivalent
shared command is `bytedcli --site i18n-tt auth login`.

ROW network selection uses the shared bytedcli network profile:

- `BYTEDCLI_NETWORK_PROFILE=prod` selects the production network.
- `BYTEDCLI_NETWORK_PROFILE=office` selects the office network.
- When unset, the shared production-runtime detection selects production in a
  production runtime and office otherwise.

The browser authorization page and production fallback may use
`cloud.bytedance.net` even though the AI Colate business API uses
`aicolate-sg.byted.org`; this is expected.

The JWT login is shared by other `i18n-tt` commands, so
`aicolate auth logout` does not clear it. Use
`bytedcli --site i18n-tt auth logout` only when the user intends to sign out all
commands that share that login. Browser-mode logout remains AI Colate-specific.

The legacy bdsso Cookie flow remains available. Select it with the group-level
`--auth-mode browser` option or `BYTEDCLI_AICOLATE_AUTH_MODE=browser`. Its login
command prefers the reusable SSO session and falls back to an interactive
browser when needed.

```bash
BYTEDCLI_CLOUD_SITE=i18n-tt bytedcli auth login --session
bytedcli aicolate --auth-mode browser auth login
bytedcli aicolate --auth-mode browser auth status
bytedcli aicolate --auth-mode browser space list
```

If browser mode reports `AUTH_AICOLATE_SESSION_REQUIRED`, refresh the browser
session with the commands above. For JWT login failures, run
`bytedcli aicolate auth login`.

### US-USTS (`--region us-ttp-usts`)

Two unrelated credentials share the name "JWT" — do not conflate them:

|             | ByteCloud JWT                        | OG JWT                              |
| ----------- | ------------------------------------ | ----------------------------------- |
| Sent as     | `x-jwt-token` **header**             | `X-Og-Jwt-Token` **cookie**         |
| Purpose     | default transport auth (`row`)       | Open Gateway **region gate** (USTS) |
| Obtained by | `bytedcli --site i18n-tt auth login` | `aicolate auth import-jwt`          |

**ByteCloud JWT does not work on `us-ttp-usts`.** That region sits behind an
Open Gateway that requires the OG-JWT cookie _plus_ the bdsso cookie jar — both
are mandatory. So `us-ttp-usts` always uses the cookie path automatically, even
though `jwt` is the global default; passing `--auth-mode jwt` with that region is
rejected. The OG-JWT cookie (~7 days) cannot be minted headlessly: copy it from
an authenticated browser session and import it.

```bash
# 1. import the Open Gateway gate cookie (never echoed back; stored 0600)
bytedcli aicolate auth import-jwt --region us-ttp-usts --from /tmp/ogjwt.txt
# 2. refresh the bdsso SSO session (CAS is on sso.bytedance.com for USTS)
bytedcli --auth-site bytedance auth login --session
# 3. mint the AI Colate session for the region
bytedcli aicolate auth login --region us-ttp-usts
bytedcli aicolate auth status --region us-ttp-usts   # shows session + og_jwt expiry
bytedcli aicolate space list --region us-ttp-usts
```

Sessions are cached per region, so a `row` login is never reused for USTS.
`aicolate auth clear-jwt --region us-ttp-usts` drops the imported gate cookie.
Requests ignore all cached `X-Og-Jwt-Token` copies and send exactly one current
token: `AICOLATE_OG_JWT` takes precedence over the imported store. Importing a fresh
token does not require refreshing an otherwise valid bdsso session.
USTS `auth status` reports the effective token's `source` (`environment` or `store`)
and expiry without exposing its value. Its `valid` field requires both a valid
session and a present, non-expired token; `session_valid` reports the session alone.
These are local credential checks, not a live gateway authentication probe.

### EU (`--region eu-ttp`)

EU AI Colate (`aicolate.tiktok-eu.net`) is a separate data plane from ROW: space
ids are shared, but resources are not, so a ROW query never returns EU
workflows. Its gateway accepts only the bdsso cookie session — the ByteCloud JWT
is rejected — so `eu-ttp` always uses the cookie path automatically and
`--auth-mode jwt` with that region is rejected. The login reuses the TikTok SSO
session (the CAS chain hops through `tt-sso.tiktok-eu.net` to
`sso.tiktok-intl.com`), and no gate cookie import is needed. `eu` and
`tiktok-eu` are accepted aliases.

```bash
BYTEDCLI_CLOUD_SITE=i18n-tt bytedcli auth login --session
bytedcli aicolate auth login --region eu-ttp
bytedcli aicolate auth status --region eu-ttp
bytedcli aicolate library list --region eu-ttp --space <spaceId> --mine
bytedcli aicolate workflow list --region eu-ttp --space <spaceId>
```

Not every surface is available on EU:

- The native model platform (`/api/*`: `market`, `dev`, `trace`,
  `evaluation task get`, `evaluation result export`) is not served on EU; those
  commands fail fast with `AICOLATE_REGION_UNSUPPORTED`.
- Knowledge bases, MCP servers, and Skill resources currently return backend
  errors on EU even though the same calls work on ROW.

`--region` accepts only `row`, `eu-ttp`, `us-ttp-usts`, and their aliases; any
other value fails with `AICOLATE_INPUT_ERROR` instead of falling back to `row`.

## Spaces / Applications

`space_id` (a.k.a. tenant id) scopes almost everything.

```bash
bytedcli aicolate space list                              # list spaces (tenants)
bytedcli aicolate app list --space <spaceId>              # list intelligences (agents/apps)
bytedcli aicolate app get --id <intelligenceId> --type app  # --type agent | app
bytedcli aicolate app workflow publish --id <projectId>         # preview, auto patch version
bytedcli aicolate app workflow publish-records --id <projectId> # publish history
```

## AI Application resources (space-scoped lists)

```bash
bytedcli aicolate knowledge   list --space <spaceId>   # knowledge bases (datasets)
bytedcli aicolate plugin      list --space <spaceId>   # plugins
bytedcli aicolate mcp         list --space <spaceId>   # MCP servers
bytedcli aicolate skill       list --space <spaceId>   # skills
bytedcli aicolate model       list --space <spaceId>   # models available to the space
bytedcli aicolate app-service list --space <spaceId>   # Application Management services
bytedcli aicolate connector   list --id <projectId>    # publish connectors of an intelligence
```

## Workflow scopes and release routes

AI Colate has two workflow scopes. Do not infer the release route only from the
word "workflow":

```text
workflow
├── resource-library workflow（资源库工作流）
│   ├── create/list: workflow create|list without --project-id
│   ├── develop:      workflow get|export|apply|run
│   └── release:      workflow publish
└── project workflow（项目开发工作流）
    ├── create/list: workflow create|list --project-id <projectId>
    ├── develop:      workflow get|export|apply|run
    ├── release:      app workflow publish --id <projectId>   (publishes the whole project)
    └── Application Management
        ├── clusters: app-service cluster list
        ├── register: app-service workflow create
        ├── versions: app-service version list
        ├── create release: app-service publish
        ├── advance stage: app-service publish-record advance
        └── quota config: app-service quota publish
```

The platform does **not** publish one project workflow through
`workflow_api/publish`. A project workflow is packaged and versioned with its
whole project. `workflow publish` rejects a workflow whose canvas contains a
`project_id` and points to `app workflow publish`.

Whole-project publishing defaults to the hosted API connector `1024`. It checks
that the version is unused and each selected connector is available before
showing the request. Omit `--version` to use `v0.0.1` for the first semantic
release or increment the highest existing `vMAJOR.MINOR.PATCH` patch version.
An explicit version is kept unchanged and only checked for duplication. It is
preview-only unless `--yes` is present:

```bash
# Preview; includes every workflow developed inside the project.
bytedcli aicolate app workflow publish --id <projectId> \
  --version-description "release notes"

# Or choose the version explicitly.
bytedcli aicolate app workflow publish --id <projectId> --version v1.2.3 \
  --version-description "release notes"

# Submit the reviewed request.
bytedcli aicolate app workflow publish --id <projectId> --version v1.2.3 \
  --version-description "release notes" --yes
```

Whole-project publishing is allowed only when the authenticated account is the
project creator or a collaborator. The CLI checks this before version and
connector preflight and fails closed when permission metadata is unavailable.
The current `publish_project` API does not accept an operator ID; platform
history may therefore display the project owner instead of the API caller.
Correct caller attribution requires the backend to persist the authenticated
caller and cannot be repaired by adding an undocumented CLI payload field.

Application Management is a separate serving lifecycle. First register a
specific project workflow as an API App Service. Traffic configuration keys are
PAT metadata IDs, not token plaintext. The cluster selector value is the returned
host prefix for that space:

```bash
bytedcli aicolate app-service api-key list
bytedcli aicolate app-service cluster list --space <spaceId>

# Preview App Service registration. If exactly one usable accessible PAT exists,
# --api-id may be omitted; otherwise pass it explicitly.
bytedcli aicolate app-service workflow create \
  --space <spaceId> --project-id <projectId> --workflow-id <workflowId> \
  --name <serviceName> --desc <description> --host-prefix <clusterPrefix> \
  --api-id <patMetadataId> --row-qps 3 --us-ttp-qps 2 --eu-ttp-qps 1

# Submit after reviewing the exact app_service/create payload.
bytedcli aicolate app-service workflow create \
  --space <spaceId> --project-id <projectId> --workflow-id <workflowId> \
  --name <serviceName> --desc <description> --host-prefix <clusterPrefix> \
  --api-id <patMetadataId> --row-qps 3 --us-ttp-qps 2 --eu-ttp-qps 1 --yes
```

`app-service workflow create --host-prefix` must match the space cluster list.
For `app-service quota publish`, an explicitly overridden `--host-prefix` is
validated against that same list; omitting it preserves the current cluster.

Registration does not itself put the service online. Publish the project first,
select an eligible version, then create the staged App Service release. At least
one 1–99% small-traffic stage is required; repeat the option in strictly
increasing order (up to four stages). A final 100% full-traffic stage is appended
automatically. Creating the release record does not enter its first stage; advance
the record once per configured small/full-traffic stage.

```bash
bytedcli aicolate app-service version list --id <appServiceId>

# Preview 10% -> 50% -> 100%.
bytedcli aicolate app-service publish --id <appServiceId> --version v1.2.3 \
  --small-traffic-percent 10 --small-traffic-percent 50 --note "go online"

# Submit the staged release.
bytedcli aicolate app-service publish --id <appServiceId> --version v1.2.3 \
  --small-traffic-percent 10 --small-traffic-percent 50 --note "go online" --yes

# Inspect progress, then enter the next configured stage when the CLI says it is ready.
bytedcli aicolate app-service publish-record advance --id <publishRecordId>
bytedcli aicolate app-service publish-record advance --id <publishRecordId> --yes

# Quotas are published independently from application versions. Configure any
# combination of ROW, US-TTP, and EU-TTP; omitted regions are preserved.
bytedcli aicolate app-service quota publish --id <appServiceId> \
  --us-ttp-qps 2 --us-ttp-qpm 120 --eu-ttp-qps 1 --note "quota update"
bytedcli aicolate app-service quota publish --id <appServiceId> \
  --us-ttp-qps 2 --us-ttp-qpm 120 --eu-ttp-qps 1 --note "quota update" --yes
```

`publish-record advance` reads the release detail before every operation and
prints the overall status, completed-stage count, current/next stage, and exact
next action. Repeat it only when the output shows another `advance` command. If a
stage is still running, it submits nothing and asks you to wait. Once all stages
are published, repeated invocations are successful no-ops instead of surfacing
the platform's "not in publishing status" error.

Quota publishing returns `publish_record_id`, `bpm_ticket_id`, and a derived BPM
ticket URL when the backend creates an approval ticket. App Service creation still
requires initial traffic configuration: at least one regional QPS/QPM option is
required, each region accepts QPS `0..10` and QPM `0..6000`, QPM defaults to that
region's QPS × 60, and omitted regions start at zero. Later
`app-service quota publish` updates accept QPS `0..100` and QPM `0..6000` per
region while preserving omitted regions. Application-version releases and
quota/config releases remain separate.

## MCP server tools

Fetch an MCP server's tool catalog (`name` + `input_schema` + `description`) — these
are the entries inlined into a workflow Skill node's `mcpList[].tools` when the
workflow calls the MCP. `--psm` mirrors the MCP server metadata (the backend
`source_type`/`transport_mode` enums default to `1`).

```bash
bytedcli aicolate mcp tools --id <mcpServerId> --psm <psm>   # e.g. --psm bytedance.mcp.example_server
```

## Skill lifecycle (create / upload / release)

> Terminology: an **AI Colate "skill"** here is a backend **Skill resource** of the
> AI Application platform (a reusable prompt/tool capability bound into a workflow
> Skill node via `mcpList[]`/`skills[]`). It is NOT a Claude/Agent skill under the
> repo's top-level `skills/` directory — unrelated concepts that share the word.

Beyond `skill list`, a skill can be created and have its content uploaded. The
content is a zip package (with a `SKILL.md`) stored in TOS; `save-data --data-file`
takes a JSON file holding the **base64 of that zip** as a JSON string.

```bash
bytedcli aicolate skill create    --space <spaceId> --name N --desc D [--tags a,b] [--public]   # -> skill_id
bytedcli aicolate skill save-data --space <spaceId> --id <skillId> --data-file zip_b64.json [--config-file cfg.json]
bytedcli aicolate skill release   --space <spaceId> --id <skillId> --env online --version 1.0.0 [--desc D]
bytedcli aicolate skill get       --space <spaceId> --id <skillId> [--version 1.0.0]   # draft when --version omitted
```

A workflow Skill node (type 63) binds a released skill via its `skills[]` and calls
MCP tools via `mcpList[]`. `config` is sent to the backend as a JSON string.

## Workflow batch Jobs

`aicolate batch` operates the server-side Batch Tasks workflow. It is different
from `workflow batch run` (local JSONL fan-out) and `evaluation task` (Evaluate
page datasets and evaluators).

```bash
# Upload CSV, validate it against the published workflow schema, then create.
bytedcli aicolate batch job create \
  --space <spaceId> --workflow-id <workflowId> --workflow-version <version> \
  --name <jobName> --input-csv ./input.csv --parallel 1 --qps 0

bytedcli aicolate batch job list --space <spaceId> --page 1 --page-size 20
bytedcli aicolate batch job get --space <spaceId> --job-id <jobId>
bytedcli aicolate batch job wait --space <spaceId> --job-id <jobId>
bytedcli aicolate batch task list --space <spaceId> --job-id <jobId>
```

`job create` accepts `--timeout-ms <milliseconds>` (default 60000). The upload
step transfers a file and the following validate/create calls can be slow, so
this per-request timeout is more generous than the global default; raise it
(for example `--timeout-ms 120000`) when working with large CSVs.

`job wait` polls every 5 seconds for at most 30 minutes by default. Timeout or
Ctrl-C only stops the local wait; it does not cancel the remote Job. Use
`job cancel --yes`, `job retry`, or repeatable `task retry --task-id <taskId>`
for explicit mutations.

Result export is asynchronous:

- `result export` only queues the export server-side; the generated CSV or Lark
  artifact is delivered by the Feishu bot "电商算法机器人". Tell the user to
  watch that bot's message for the Job — the CLI neither polls nor downloads.
- Without `--flatten`, CSV/Lark output keeps complete JSON input/output columns.
- With `--flatten`, each selected top-level workflow field becomes one column;
  nested objects and arrays remain JSON strings.
- `--input-field` and `--output-field` are repeatable and require `--flatten`.

```bash
bytedcli aicolate batch job result export \
  --space <spaceId> --job-id <jobId> --format csv

bytedcli aicolate batch job result export \
  --space <spaceId> --job-id <jobId> --format lark --flatten \
  --input-field query --output-field answer
```

`batch task list` returns each Task's `log_id`. Use that value to continue with
the log/Argos domain, for example:

```bash
bytedcli log get-logid-log "<logId>" --vregion "<VRegion>"
bytedcli log footprint search --log-type argos --log-id "<logId>" \
  --region <region> --start <unixSeconds> --end <unixSeconds>
```

## Evaluation tasks

The AI Application Evaluate page creates batch tasks in this sequence: find a
workflow, choose a published version (or latest), upload an input file, then
create the task. `evaluation task create` performs the upload automatically when
`--file` is provided. After creation, poll `evaluation task get` with the returned
`task_id`; once the task is complete, use `evaluation result export` to create a
CSV download URL or save the CSV locally.

```bash
# choose workflow/version
bytedcli aicolate workflow list --space <spaceId> --keyword <keyword> --status-code 2 --mine
bytedcli aicolate workflow version list --id <workflowId> --space <spaceId>

# create from a local csv/json/jsonl/tsv file
bytedcli aicolate evaluation task create --space <spaceId> --workflow-id <workflowId> --workflow-version latest --file cases.csv --concurrency 1

# create from an already-uploaded AI Colate file URL
bytedcli aicolate evaluation task create --space <spaceId> --workflow-id <workflowId> --workflow-version v1.0 --file-url 'https://example.test/file/preview?id=model_platform/demo.csv'

# create from a Tokadb dataset instead of an uploaded file
bytedcli aicolate evaluation task create --space <spaceId> --workflow-id <workflowId> --workflow-version v1.0 --dataset-id <datasetUuid> --dataset-version v1.0

# inspect lifecycle status and counters
bytedcli aicolate evaluation task get --task-id <taskId>

# export default result fields after completion
bytedcli aicolate evaluation result export --task-id <taskId>

# export selected fields/dimensions and download the CSV
bytedcli aicolate evaluation result export --task-id <taskId> --field log_id --field video_url --dimension data --output result.csv
```

`--workflow-version latest` sends the UI's empty `version` field, matching the
"latest" option. `--evaluator-workflow-id <workflowId>` is optional; omit it to
match the page behavior where the evaluator field is empty.

For result export, omit `--field` and `--dimension` to use the platform's default
field set. `--export-count-type` defaults to `all`; `--count` is an optional
row-count hint for that export scope and can be omitted. The command infers the
`operator` from the current AI Colate login session; pass `--operator <email>`
only when overriding that identity. If `--output` already exists, pass `--force`
to overwrite it.

## Traces / spans (observability)

Read-only span search and single-trace inspection. **`--start` and `--end` are
mandatory** — the backend requires a window and retains only a few days
(commonly 7). It also **silently clamps** a window that reaches past its
retention floor or into the future, so the JSON output echoes
`requested_window` to make the discrepancy visible.

```bash
# search spans in a workspace (newest first; root spans by default)
bytedcli aicolate trace spans list --space <spaceId> \
  --start 2026-08-12T00:00:00Z --end 2026-08-13T00:00:00Z

# query a backend data region through the ROW API host
bytedcli aicolate trace spans list --space <spaceId> --start <s> --end <e> \
  --region row --target-region US-TTP
bytedcli aicolate trace get --id <traceId> --space <spaceId> --start <s> --end <e> \
  --region row --target-region US-TTP

# only LLM spans, filtered, paged
bytedcli aicolate trace spans list --space <spaceId> \
  --start 1786500000000 --end 1786600000000 \
  --span-list-type llm_span --filter "status eq error" --page-size 50

# typed and multi-value filters
bytedcli aicolate trace spans list --space <spaceId> --start <s> --end <e> \
  --filter "duration gte 1000" \
  --filter "status in error" --filter-or

# one trace as a span tree (+ token totals)
bytedcli aicolate trace get --id <traceId> --space <spaceId> --start <s> --end <e>

# a single span within a trace (repeatable; other spans are dropped server-side)
bytedcli aicolate trace get --id <traceId> --space <spaceId> --start <s> --end <e> \
  --span-id <spanId> --span-id <spanId2>

# starting from only a log id: find the span(s), then read the trace
bytedcli aicolate trace spans list --space <spaceId> --start <s> --end <e> \
  --span-list-type all_span --filter "logid eq <logId>"
bytedcli aicolate trace get --id <traceIdFromAbove> --space <spaceId> --start <s> --end <e>

# find every run of one workflow, then isolate a single execution
bytedcli aicolate trace spans list --space <spaceId> --start <s> --end <e> \
  --filter "aicolate_agent_workflow_id eq <workflowId>"
bytedcli aicolate trace spans list --space <spaceId> --start <s> --end <e> \
  --span-list-type all_span --filter "aicolate_agent_execution_id eq <executionId>"

# skip large payloads (drops input/output and attr_tos URLs server-side)
bytedcli aicolate trace get --id <traceId> --space <spaceId> --start <s> --end <e> --no-io
```

- `--start` / `--end` take epoch **milliseconds** or ISO-8601. Epoch _seconds_
  are rejected with a ×1000 hint rather than silently misread.
- `--region` selects the AI Colate API host. `--target-region` is passed as the
  backend `target_region` field in the span-list body or trace-get query string.
  Use the backend value `US-TTP` for US trace data through the ROW host; `us` and
  `us-ttp-usts` are rejected by the backend. Omit the flag to preserve the backend
  default; its value is passed through unchanged.
- `--filter "<field> <op> <value>"` is repeatable and AND-joined; `--filter-or`
  switches to OR. Operators: `match`, `not_match`, `eq`, `not_eq`, `lt`, `lte`,
  `gt`, `gte`, `in`, `not_in`, `exist`, `not_exist` (the last two take no value).
  `in`/`not_in` split the value on commas.
- **Compound filters** are verified exact against ground truth, including 3- and
  4-predicate ANDs and repeating the _same_ field to express a bounded range
  (`--filter "duration gte 100" --filter "duration lte 1000"`):

```bash
# AND (default): slow failures only
bytedcli aicolate trace spans list --space <spaceId> --start <s> --end <e> \
  --span-list-type all_span \
  --filter "status in error" --filter "duration gte 1000"

# OR: anything failing OR anything very slow
bytedcli aicolate trace spans list --space <spaceId> --start <s> --end <e> \
  --span-list-type all_span \
  --filter "status in error" --filter "duration gte 20000" --filter-or
```

**`--filter-or` applies to every predicate at once** — there is no grouping, so
`A AND (B OR C)` is not expressible. Three predicates with `--filter-or` mean
`A OR B OR C`. Run two queries and intersect if you need mixed logic.

- Two backend field rules the CLI applies for you:
  - **`status`** accepts only `success` / `error`, and the backend only permits
    the `in` operator on it. `status eq error` is rewritten to `status in error`
    automatically; `not_eq`/`not_in`/`match` on `status` are rejected locally
    with a hint rather than as an opaque `invalid filter`.
  - **Latency fields** (`duration`, `latency_first_resp`, `latency_first_token_resp`,
    `start_time_first_resp`, `start_time_first_token_resp`, `reasoning_duration`)
    default to `field_type: long`, so `--filter "duration gte 3500"` works with no
    `--filter-type`. Their values are **milliseconds**, matching the `Dur(ms)`
    column.
  - **`duration lte N` behaves like `< N`** — it drops nearly every span the UI
    shows as exactly `N` ms. The filter converts your operand ms→µs exactly
    (`lte 5` → 5000µs) but the displayed value is floored from µs, so a span shown
    as `5` is really 5001–5999µs. Ask for `lte N+1` to include the `N` bucket.
    `gte` is exact and needs no adjustment. Verified live: `lte 5` → 306 spans,
    `lte 6` → 522, the 216 extra all displaying `5`.
- Field types otherwise default to `string`; declare others with
  `--filter-type <field>=<long|double|bool|string>`. A `string` field cannot use
  `lt/lte/gt/gte` — the CLI says so up front instead of letting the backend
  answer `list spans req is invalid`.
- `--page-size` max is 1000 (backend `MaxListSpansLimit`). Paging is
  caller-driven: pass the response's `next_page_token` back via `--page-token`.
  **The backend's own `has_more` is unreliable on an exactly-full page** (it
  over-fetches a sentinel row that never survives), so the CLI reports
  `has_more: true` whenever a full page came back with a token, and adds
  `has_more_backend` to show the disagreement. Keep paging until `has_more` is
  false — a trailing empty page is normal and cheaper than losing data.
- Sorting is fixed by the backend to `start_time DESC, span_id DESC`; `--no-sort`
  is the only lever (it asks for no ordering at all, though results may still
  come back ordered).
- Span shapes differ a lot by workload. Agent traces are shallow with descriptive
  names (`claude_code.llm_request`); workflow traces nest 6+ levels with
  `Workflow`/`Lambda`/`Graph`/`prompt`/`model` types whose `span_name` is often a
  bare numeric node id; hand-instrumented services add `chain`/`prompt_hub` and
  long dotted names (`services_agent.handler.talk.agent_loop`, up to ~97 chars).
  `span_type` is a free-form string — do not assume a fixed set. `trace get`
  renders the parent→child tree, so an error deep in a trace is visible against
  its ancestors. Prefer `--no-io` when sweeping: it cut a real 57-span trace from
  2.4 MB to 64 KB.
- Long span names are shortened as `head...tail` rather than head-only, because
  such names are usually distinguished by their suffix. Use `--json` when you need
  the exact untruncated `span_name`.
- Three ways to narrow a lookup, all verified live:
  - **`trace get --id <traceId>`** is the only _primary_ lookup — `--id` is
    required, so a trace id is mandatory even when you also pass the others.
  - **`--span-id <id>`** (repeatable) returns just those spans of that trace.
  - **`--log-id <id>`** narrows within the trace and really does filter: a log id
    belonging to a different trace returns 0 spans, not the whole trace.
  - If you only have a **log id**, you cannot pass it to `trace get` directly.
    Find the span first with
    `trace spans list --span-list-type all_span --filter "logid eq <logId>"`,
    take its `trace_id`, then call `trace get`. Both observed log-id formats work.
- **Workflow / execution lookups go through `--filter`, not a dedicated flag.**
  There is no `--workflow-id`; a workflow run is identified by two custom tags:
  `aicolate_agent_workflow_id` (one workflow, many runs) and
  `aicolate_agent_execution_id` (**one run == one trace**). Related tags on the
  same spans: `aicolate_agent_version`, `aicolate_agent_mode`,
  `aicolate_agent_api_key_id`, `aicolate_agent_agentapp_id`,
  `aicolate_agent_app_service_id`, `aicolate_agent_node_title`. Use
  `--span-list-type all_span` for an execution (root-only returns just 1 span).
  `eq`, `in`, `match` (prefix), `exist`/`not_exist` all work.
  - **Never pass `--filter-type <idTag>=long` for these ID tags.** The backend
    stores each field type in a _different_ column, and these IDs are stored as
    strings, so a `long` filter matches nothing and returns `count: 0` with no
    error — indistinguishable from "that execution does not exist". The IDs only
    look numeric; ordering them is meaningless, so `in`/`match` (default `string`)
    are always the right operators. This is the one filter mistake that fails
    silently instead of erroring.
- **Some spaces are very high volume** (one measured ~68k spans per 2 hours), and
  a filter that misses a backend index can take a long time or not return — this is
  expected, not a CLI failure. Narrow `--start`/`--end` to minutes rather than days
  when exploring a busy workspace, and prefer adding an indexed predicate
  (`span_type`, `status`) over paging a wide window.
- A lookup that matches nothing is a **success with `count: 0`**, not an error
  (exit code 0) — check `count`, and remember an out-of-retention window is
  clamped silently and also yields 0.

## Workflows (DAG)

Workflow is the deepest and most stateful surface in AI Colate. Keep the entry
skill concise and route workflow tasks to dedicated references.

When a task touches workflow read/modify/debug/lifecycle, read these files in
order before operating:

1. [workflow-operations.md](references/workflow-operations.md)
2. [workflow-schema.md](references/workflow-schema.md)
3. [workflow-debugging.md](references/workflow-debugging.md)

Quick workflow command map:

The Knowledge Retriever Python/IDL sidecars produced by `workflow export
--format runtime-yaml` are custom IPR export support. They are not a generic
knowledge-base export or a reusable implementation for other domains. Native
JSON/YAML export does not emit them, and runtime import ignores them.

```bash
# read / inspect
bytedcli aicolate workflow list --space <spaceId>                       # resource library
bytedcli aicolate workflow list --space <spaceId> --project-id <projectId>  # project
bytedcli aicolate workflow list --space <spaceId> --keyword <keyword> --mine
bytedcli aicolate workflow list --space <spaceId> --workflow-id <wfIdOrUrl>
bytedcli aicolate workflow version list --id <wfIdOrUrl> --space <spaceId>
bytedcli aicolate workflow get --id <wfIdOrUrl> --space <spaceId>
bytedcli aicolate workflow summary get --id <wfIdOrUrl> --space <spaceId>

# runtime YAML export / import
bytedcli aicolate workflow export --id <wfIdOrUrl> --space <spaceId> \
  --format runtime-yaml --output ./fireflow-bundle
bytedcli aicolate workflow import --file ./fireflow-bundle \
  --format runtime-yaml --output ./aicolate.json
bytedcli aicolate workflow import --file ./fireflow-bundle \
  --format runtime-yaml --space <spaceId> --project-id <projectId> [--name <name>]

# edit
bytedcli aicolate workflow apply --id <wfIdOrUrl> --space <spaceId> --ops-file ops.json --dry-run
bytedcli aicolate workflow apply --id <wfIdOrUrl> --space <spaceId> --ops-file ops.json --save

# debug
bytedcli aicolate workflow run --id <wfIdOrUrl> --space <spaceId> --input '{"k":"v"}'
bytedcli aicolate workflow run --id <wfIdOrUrl> --space <spaceId> --input '{"k":"v"}' --no-wait
bytedcli aicolate workflow batch run --id <wfIdOrUrl> --space <spaceId> --input-file inputs.jsonl
bytedcli aicolate workflow instance list --space <spaceId>
bytedcli aicolate workflow task list --job-id <jobId> --space <spaceId>
bytedcli aicolate workflow execution get --id <wfIdOrUrl> --space <spaceId> --execute-id <executeId>
bytedcli aicolate workflow log get --id <wfIdOrUrl> --execute-id <executeId>
bytedcli aicolate workflow execution retry --id <wfIdOrUrl> --space <spaceId> --execute-id <executeId> --event-id <eventId> --data-json '{"approved":true}'

# lifecycle
bytedcli aicolate workflow create --space <spaceId> --name <name> --desc <desc>  # resource library
bytedcli aicolate workflow create --space <spaceId> --project-id <projectId> --name <name> --desc <desc>
bytedcli aicolate workflow duplicate create --id <wfIdOrUrl> --space <spaceId>
bytedcli aicolate workflow publish --id <wfIdOrUrl> --space <spaceId>  # resource-library only
bytedcli aicolate app workflow publish --id <projectId>                # all project workflows; auto patch
```

Saving an existing workflow requires owner or editable collaborator permission.
`workflow publish` applies only to resource-library workflows and has the same
permission boundary. Project workflows cannot be published one-by-one; release
their containing project with `app workflow publish`. Workflow deletion is intentionally
unavailable in the CLI.

For a resource-library workflow, omitting `--workflow-version` makes
`workflow publish` use `v0.0.1` for the first publish and increment the latest
published patch version thereafter.

`ops.json` is a user-provided local file. If you need a structural reference for
the ops payload shape, use `references/workflow-schema.md` and
`references/workflow-operations.md` as format guides.

## Agent Guidance

- All commands accept `--json` for structured output and are exposed as MCP tools.
- `--region` supports `row` (default; office `aicolate.tiktok-row.net`,
  production `aicolate-sg.byted.org`, selected by the network precedence above) and
  `us-ttp-usts` (`aicolate.tiktok-usts.net`, USDS partition — gated by an
  imported `X-Og-Jwt-Token` cookie, NOT the ByteCloud JWT; see the US-USTS auth
  section). Aliases: `usts`, `tiktok-usts`. It also supports `eu-ttp`
  (`aicolate.tiktok-eu.net`, a separate EU data plane — bdsso cookie session
  only, no native `/api/*`; see the EU auth section). Aliases: `eu`,
  `tiktok-eu`. Note `us-ttp` is reserved for a future distinct region and is NOT
  an alias for `us-ttp-usts`. Unknown or empty `--region` values fail with
  `AICOLATE_INPUT_ERROR`. Additional
  regions can be added to `src/api/aicolate/site.ts` as they are confirmed.
- Some endpoints (knowledge, mcp) return results at the top level alongside
  `code` rather than under `data`; the client handles both.
- Whole-project publish and both App Service write commands default to dry-run;
  only `--yes` submits. Other write operations (`workflow create/apply/publish/run`,
  `evaluation task create`) mutate real data, so confirm intent before running them.
