---
name: bytedance-pearl
description: Use when listing Nova applications, sources, or countries; reading source/task/landing-page configurations; sizing DMP crowd sets; searching creator appeal or other risk-control cases; inspecting SOP definitions, variables, caches, checkpoint reports, or Odin endpoints; or previewing an explicitly requested Odin mutation. Covers ROW/US-BDEE, US-TTP, US-USTS, and EU control planes through bytedcli. Nova and Case mutations remain unavailable; Odin mutation previews are dry-runs and live submissions require the local gate plus --yes.
---

# Pearl

Use this skill for Pearl platform operations: Nova, DMP crowd sets, and Odin (`pearl case|odin|sop|report ...`). Nova resources form a hierarchy: applications own sources, and tasks are mounted under a source. Odin uses the same Pearl session and site routing rather than a separate cookie store.

## Region routing

`--region` takes a country code. The CLI resolves the API origin and application ID from its control-plane mapping:

| `--region`                                                            | Control plane                    |
| --------------------------------------------------------------------- | -------------------------------- |
| `us` + `--site us-ttp-bdee`                                           | US-BDEE                          |
| `us` + `--site us-ttp`                                                | US-TTP                           |
| `us` + `--site us-ttp-usts`                                           | US-USTS                          |
| `at` `be` `cz` `de` `es` `fr` `gb` `gr` `hu` `ie` `it` `nl` `pl` `pt` | EU full or limited from `--site` |
| `br` `dk` `fi` `id` `jp` `mx` `my` `ph` `sa` `se` `sg` `th` `vn`      | ROW                              |

- Read endpoints ignore `aid` server-side (the domain selects the control plane; `region`/`oec_region` filter by country), but the CLI still sends the console-faithful value defensively (some endpoints may validate it). Override with `--aid` only when you know why.
- The mapping follows each control plane's non-hidden country registry, live-verified on 2026-07-31. A country can be supported even when the current account sees no applications or sources there.
- An explicit `--site` and `--region` must name the same control plane; incompatible combinations fail before authentication. US-BDEE uses the US-TTP API origin but keeps a separate permission partition; use `--site us-ttp-bdee`, not `i18n-tt` or US-TTP. US-TTP and USTS are supported in code and offline tests even when the current account cannot live-verify them.
- US-BDEE keeps a separate permission partition, so its session cache and login target are derived from `--site us-ttp-bdee` (the derived target carries the SOP page path and `oec_region=US`). Let the site flag resolve it; do not hand-write `--url`.
- For an EU country, global `--site eu-ttp` and `--site eu-ttp-limited` select the limited backend; `--site eu-ttp-full` selects the full backend. `--region` remains the country and does not select the authorization boundary.
- The explicit EU profiles are Pearl access selections. Other bytedcli domains compatibility-normalize both to the existing `eu-ttp` route.

## Authentication

Pearl uses a separate private `sso_session` cache for each control plane. Bootstrap the control plane you need before calling Nova APIs:

```bash
# ROW
bytedcli --site i18n-tt auth pearl-session login

# EU limited (`eu-ttp` is the backward-compatible limited alias)
bytedcli --site eu-ttp auth pearl-session login

# EU full
bytedcli --site eu-ttp-full auth pearl-session login

# US-BDEE (HTTP-only: never opens a browser)
bytedcli --site us-ttp-bdee auth pearl-session login --no-browser-fallback

# US-TTP / US-USTS (only when the caller has the corresponding permission)
bytedcli --site us-ttp auth pearl-session login --no-browser-fallback
bytedcli --site us-ttp-usts auth pearl-session login --no-browser-fallback

# Read only the selected control-plane cache status; never prints the cookie
bytedcli --site us-ttp-bdee --json auth pearl-session status
```

The command first uses the reusable local TTSSO session to complete the control-plane-specific MPS ticket exchange over HTTP. Add `--no-browser-fallback` for deterministic non-interactive operation; it fails with an actionable error instead of opening Chromium. Without that flag, an explicitly invoked login command may use Chromium as a last-resort fallback. Business commands and automatic 401 recovery are always HTTP-only and never open a browser. ROW/US use TikTok SSO; EU may combine TikTok and ByteDance SSO sessions for its Feishu chain.

The global site determines the default Pearl login origin, so `--url` is normally unnecessary. EU limited and EU full sessions use separate private cache files and cannot be substituted for one another. `auth pearl-session status` only reads the selected cache partition and returns validity plus timestamps; it does not return the cookie.

## Discover applications, sources, and countries

Keep all IDs as strings; Pearl IDs exceed the JavaScript safe integer range. Use global `--json` for machine-readable output (full objects; text mode shows trimmed tables).

```bash
# Applications (source containers) in a region
bytedcli --site us-ttp-bdee pearl nova application list --region us

# EU limited access for Germany
bytedcli --site eu-ttp pearl nova application list --region de

# One application detail by key (full owners list, description)
bytedcli --site us-ttp-bdee pearl nova application get --region us --application-key sample_application

# Sources, optionally filtered by application
bytedcli --site us-ttp-bdee pearl nova source list --region us --application-key sample_application --page-size 100

# One source detail by ID (source_detail/get, POST under the hood; richer
# than the list row: full advanced_settings descriptions, support_ab, etc.)
bytedcli --site us-ttp-bdee pearl nova source get --region us --source-id 7000000000000000001

# Countries visible to the region's control plane (valid --region inputs)
bytedcli --site i18n-tt pearl nova country list --region jp
```

The same `source_key` can exist as different `source_id`s per control plane. Always resolve IDs in the region you query.

## Read Nova tasks

```bash
bytedcli --site us-ttp-bdee pearl nova source task list \
  --region us \
  --source-id 7000000000000000001 \
  --source-env 2 \
  --page 1 \
  --page-size 100
```

`--page` is 1-based (repo convention); it is translated to Pearl's 0-based API internally. The task-list count is surfaced as `returned` (this page), not `total` — page (`--page 2`, `3`, …) until a short page comes back. (Source and application lists, by contrast, return a genuine global `total`.)

Read a task detail:

```bash
bytedcli --site us-ttp-bdee pearl nova source task get --region us --task-id 7000000000000000001
```

## Task version history and attribution

`task log list` shows a task's version / operation history (who did what, when):

```bash
# Table: version, action, operator, updated, operate-log-id
bytedcli --site us-ttp-bdee pearl nova source task log list --region us --task-id 7000000000000000001

# Attribution: field-level diff of adjacent versions' task snapshots
bytedcli --site us-ttp-bdee pearl nova source task log list --region us --task-id 7000000000000000001 --diff
```

- `--nova-log-type` defaults to `3` (task config log); other values are raw Pearl console codes, unverified.
- No pagination: the endpoint returns only the most recent ~30 versions (the gateway rejects `page`/`size`).
- `action_type` labels are inferred from a real task's history — `2`=edit/save-draft, `13`=submit-for-review, `3`/`4`=audit-approved — treat them as hints, not a spec.
- `--diff` flattens each adjacent version's `task` snapshot and reports `path: before => after` (e.g. an added A/B vid shows as `task_settings[..].ab_vids[..]: ∅ => <vid>`). Use `--json` for the full per-version snapshots and complete change list.

## Read landing-page (undertake) schemas

A **schema** is the reusable landing-page config ("承接") a delivery task points
at. Schemas are registered per application, which is why the command sits under
`application`. A task setting references one by id, and that id also travels in
the task's landing URL, so read the task first and take the id from there.

```bash
bytedcli --site i18n-tt pearl nova application schema get --region ph --schema-id 7000000000000000001
```

- Served from the `/api/v1/nova/*` path family, not the `/api/v1/configuration/*`
  one every other Nova read uses.
- Schemas come in two shapes. `is_template: true` with `instance_parent_id: 0`
  is a **template**: its `schema_config` is a full config object holding the
  placeholder-bearing landing config and the `region_list` it may be used in.
  `is_template: false` is an **instance**: `instance_parent_id` points at its
  template and `schema_config` is a substitution list such as
  `[{"placeholder":"__KEYWORD__","replacement":"demo-keyword"}]`.
- `schema_content` is the rendered landing URL after substitution. A task
  setting stores this same rendered string, so **diffing a task setting's stored
  landing config against its schema's current `schema_content` detects a schema
  edited after the task was saved** — the two are byte-identical while in sync.
- One schema instance is typically shared by many tasks, so campaign-level
  values that live in the schema (a search keyword, for example) are **not**
  per-task. Read the schema before assuming a task owns the value.
- For interpreting what a schema actually delivers, independent of any one
  business, see the `nova-undertake-schema` skill.

## Read DMP crowd sets

A task whose delivery strategy carries `dmp_info` is targeted at a **DMP crowd
set** rather than all users. The set id in `dmp_info.set_id` is the input here.
DMP lives on the same Pearl hosts but a different gateway family
(`/api/dmp_meta/*`, which additionally requires an `agw-js-conv: str` header).

```bash
# Batch snapshot: repeat --set-id for several sets
bytedcli --site us-ttp-bdee pearl dmp set get --region us --set-id un00000000

# Recompute one set: latest size + the data partition it came from
bytedcli --site us-ttp-bdee pearl dmp set get --region us --set-id un00000000 --refresh
```

- Both commands return the set size, the population of its country, and the
  derived **share of the country** the set covers — usually the number worth
  reporting, since a crowd size alone says nothing about reach.
- The share is `null` (rendered `n/a`) whenever either side is missing or the
  population is zero. An absent share stays visibly absent; it never renders
  as `0%`.
- One resource, two query paths, so it is one verb plus a flag: without
  `--refresh` you get the cheap batch snapshot; with `--refresh` the set is
  recomputed and the response also carries the `datePartition` the counts came
  from. Prefer `--refresh` when freshness matters.
- `--refresh` recomputes a **single** set, so it rejects more than one
  `--set-id` rather than silently dropping ids.
- `--country-code` defaults to `--region`; `--domain-code` / `--tenant-code`
  default to the console's values and only need overriding for another tenant.

## Read Case Center cases and appeals

The SSAP Case Center holds risk-control cases (the console page at
`/ssap/case`). It rides a fourth gateway family on the same Pearl hosts
(`/api/v1/gne/odin_platform/*`), so authentication and `--region` routing are
identical to Nova.

```bash
# Creator-risk appeal cases in Vietnam (the console's Ongoing tab)
bytedcli --site i18n-tt pearl case list --region vn --entity-type creator --risk-domain-code 14 --status ongoing

# All cases bound to one entity (e.g. every case of one creator ID)
bytedcli --site i18n-tt --json pearl case list --region vn --entity-id 7000000000000000001

# One case with its appeal, violation, and enforcement details
bytedcli --site i18n-tt --json pearl case get --region vn --id 7000000000000000001

# One case's read-only operation history (1-based pagination)
bytedcli --site i18n-tt --json pearl case operation-log list --region vn --id 7000000000000000001 --page 1 --page-size 20
```

- `case operation-log` is the Case Center's operation/audit history for one case. `nova source task log` is Nova's task-version/configuration history; the two records describe different resources and are not interchangeable.
- `--entity-type` takes semantic values (`creator`, `shop`, `seller`, `buyer`,
  `product`, `order`, `video`, `room`, ... — the error hint lists all); the raw
  numeric code goes through `--entity-type-code` (e.g. `5` = creator).
- `--risk-domain-code` is the raw risk-domain code (TCC-configured and
  drift-prone, so no semantic values): `14` = Creator Risk, `8` = Creator And
  Content. Read the current tree from the console when unsure.
- `--status` accepts the console tab presets `ongoing` (accepted /
  machine_reviewing / pending_assign / assigned / ongoing / pending) and
  `closed`, the default `all` (no status filter), or a comma-separated list of
  raw `case_status` values.
- More server-side filters (all live-verified): `--name` (fuzzy case-name
  match), `--case-region vn,br` (case row countries — unrelated to the scope
  `--region`, which selects the control plane), `--scenario Appeals`,
  `--source appeal-center` (semantic values, e.g. appeal-center, sentry,
  clue-center; raw codes via `--source-code`), `--risk-level 3`,
  `--decision-code 1302` (1302 = Appeal Reject), and `--start` / `--end`
  (case create time bounds: unix seconds, ISO datetime, or relative like
  `"7d ago"`).
- Filtering by violation label is NOT supported by the gateway (display column
  only) — pull pages and filter the rows client-side on the
  `Violation Label Code` entry in each row's labels.
- The server `total` is capped at 10000; `total_capped: true` in JSON output
  marks an inexact total — narrow the filters to count precisely.
- `case get` returns structured fields for appeal-carrying cases (the creator
  scenario): the appeal metadata and text (`appealReason` is the appellant's
  own words, often not in English), the appeal history with evidence counts,
  and the appealed violation with its enforcement actions. Cases without an
  appeal payload (other entities / scenarios) degrade to the generic case
  fields; the full raw `taskInfo` is always in the JSON output.
- int64 safety: Odin responses use a lossless parser, so unsafe integer tokens
  inside `raw` remain exact decimal strings. Pass request IDs as JSON strings
  and prefer the structured IDs (`caseId`, `appealId`, `entityId`, ...).

## Odin discovery and calls

Inspect the closed registry when you need to understand available gateway methods:

```bash
bytedcli pearl odin endpoint list --page 1 --page-size 300
```

The registry mirrors the SSAP web client's generated API classes and contains 257 methods:
139 reads and 118 mutations. The frontend's whole-SOP deletion method is intentionally absent.
Use `pearl odin execute` for an exact registered read method when no higher-level
typed command exists. It accepts JSON objects through `--body-json` /
`--body-file` and extra query parameters through `--query-json` /
`--query-file`. GET methods reject non-empty bodies, so pass their selectors as
query parameters. Arbitrary paths and mutations are rejected by this read-only
command.
Generic reads validate the Thrift `BaseResp` envelope and preserve int64 values,
but return the method payload without asserting an unverified result schema.
Methods with `contractVerified: true` also have typed Case, SOP, or report
commands that validate method-specific request and result shapes.

```bash
bytedcli --site us-ttp-bdee --json pearl odin execute --region us --method SearchTeamV2 --body-json '{}'
bytedcli --site us-ttp-bdee --json pearl odin execute --region us --method GetSamplingTask --query-json '{"id":"7000000000000000001"}'
```

Use `pearl odin mutation execute` only for an explicitly user-requested registered
mutation. It is registry-closed to POST mutations, defaults to a local dry-run,
and preserves int64 request values as decimal strings. A live submission needs
both this machine's human-enabled write gate and `--yes`; even then, read the
authoritative object first, review the exact payload, and read it back after
submission. `pearl odin execute` never mutates.

```bash
# Preview only; no network write is sent
bytedcli --site us-ttp-bdee --json pearl odin mutation execute --region us --method SopDraftSave --body-json '{"sopCode":"sample-sop","version":"1","config":"{}"}'
```

High-level SOP commands preserve the useful local workflows:

```bash
bytedcli --site us-ttp-bdee --json pearl sop list --region us --page 1 --page-size 20
bytedcli --site us-ttp-bdee --json pearl sop get --region us --sop-code sample --status published
bytedcli --site us-ttp-bdee --json pearl sop get --region us --sop-code sample --status draft
bytedcli --site us-ttp-bdee --json pearl sop variable list --region us --sop-code sample --page 1 --page-size 20
bytedcli --site us-ttp-bdee --json pearl sop cache get --region us --sop-code sample --status published
bytedcli --site us-ttp-bdee --json pearl sop cache update --region us --sop-code sample --status published
bytedcli --site us-ttp-bdee --json pearl sop cache status --region us --sop-code sample --status published
bytedcli --site us-ttp-bdee --json pearl sop cache search --region us --sop-code sample --status published --keyword review --page 1 --page-size 20
bytedcli --json pearl sop cache list --page 1 --page-size 20
bytedcli --json pearl sop graph build --input ./sop-detail.json --output ./sop-layout.json
bytedcli --site us-ttp-bdee --json pearl sop graph build --region us --sop-code sample --status published --offline
bytedcli --site us-ttp-bdee --json pearl report checkpoint list --region us --risk-domain sample-domain --page 1 --page-size 20
bytedcli --site us-ttp-bdee --json pearl report checkpoint build --region us --risk-domain sample-domain --reporting-start 1767225600 --reporting-end 1767311999 --comparison-start 1767139200 --comparison-end 1767225599 --aggregation daily --checkpoint sample-field
```

- Cache files live under bytedcli's profile-aware data directory, are isolated
  by collision-free site/business-mode/region/AID/SOP/status keys, validate selector/hash on read,
  and are atomically written with mode `0600`.
- `cache list` validates at most 10,000 entries and 512 MiB of aggregate local
  cache-file bytes before reading entry contents. It fails closed with
  `PEARL_SOP_CACHE_LIST_TOO_LARGE` instead of silently truncating; delete unused
  entries and retry.
- `cache get` accepts `--ttl` (default `86400` seconds). A cache entry can be inspected with
  `cache status`, and `cache delete` removes only that local cache entry without a `--yes` gate;
  it never changes Pearl. `graph build --sop-code` accepts `--offline` to require a cache hit;
  `--input` is already local and therefore rejects `--offline`.
- Layout validates a DAG with exactly one start node and returns stable graph
  hashes and positions. Local input is capped at 10 MiB; JSON depth, value
  count, graph nodes, and graph edges are bounded.
- `graph build` doubles as an SOP design audit. Input that cannot be laid out at
  all (bad or duplicate node id, not exactly one start node, dangling edge,
  directed cycle) fails with `PEARL_SOP_LAYOUT_INVALID`. Design defects in the
  SOP itself are instead reported in `validation.findings[]` and set
  `validation.valid` to `false`, so a defective SOP can still be inspected. Each
  finding carries a `code`, a message, and the `node_id` / `edge_index` it
  anchors to:
  - `UNREACHABLE_NODE` — not reachable from the start node.
  - `BRANCH_NODE_MISSING_BRANCHES` — an If node without `data.branches`.
  - `BRANCH_PORT_INVALID` — an edge leaving an If node without selecting one of
    its declared branches.
  - `SOURCE_PORT_UNKNOWN` — an edge carrying a `sourcePortID` its source node
    does not declare.
  - `BRANCH_TO_BRANCH_EDGE` — If wired directly to If.
  - `PROCESS_FANOUT_MULTIPLE_BRANCHES` — one Process node fanning out to several
    If nodes.
  - `DUPLICATE_PROCESS_ITEM_ID` — the same Process item id declared twice.
  - `BRANCH_RULE_ITEM_UNKNOWN` / `BRANCH_RULE_ITEM_NOT_ANCESTOR` — an If rule
    reading a Process item that does not exist, or that is produced downstream
    or on a disconnected path.
- `graph build --sop-code` defaults to the draft status; pass `--status published`
  explicitly when laying out the published graph. Other SOP/cache selectors
  default to published.
- Layout is always local. It preserves unknown top-level config fields and has
  no `--apply`, `--version`, `--expected-hash`, or `--yes` submission path.
  Because nothing is ever written back, it reports design findings and stable
  hashes rather than layout-aesthetics metrics such as edge-crossing counts.
- Checkpoint reports fail closed on incomplete detail pages and reconcile
  both current and comparison overview counts/precision against detail records.
  A run is limited to 20 checkpoints, 20,000 mismatch rows, 40 mismatch-detail
  lookups, 121 requests, and a two-minute request-start deadline; split larger
  reports explicitly.

## Mutation operations are human-gated by design

Nova, DMP, Case Center, SOP reads, caches, layouts, and reports stay read-only. Every operation that mutates a Nova task —
editing a task, adding a Libra vid to a setting, saving a draft, submitting for review, submitting
an audit, and creating, duplicating, or offlining tasks — and every Case Center mutation —
assigning, deciding, or closing a case, and submitting appeal decisions — is intentionally not
available as a command. These are production writes with high blast radius, so a human performs
them in the Pearl console. Do not expect, request, or add a CLI path for them; if a task needs to
change, hand off to a human operator.

Odin SOP, team, and scenario mutations use a separate three-layer guard:

1. `bytedcli pearl odin write status` reports the machine-local switch.
2. A human runs `bytedcli pearl odin write enable` in an interactive terminal and types the
   displayed sentence exactly. This rejects JSON mode and piped/scripted input, and it only opens
   the machine-local switch once; it never submits a request.
3. `pearl odin mutation execute` still defaults to dry-run. A live request requires the exact JSON
   payload, `--yes`, and the enabled switch. A missing, malformed, oversized, non-regular, symlinked,
   or permission-changed switch file always means disabled.

`bytedcli pearl odin write disable` turns the switch back off and is safe to run non-interactively.
The switch is stored as an owner-only, profile-independent file in a dedicated machine-local
directory under bytedcli's base directory, so enabling it once applies to later bytedcli profiles
on the same user account.

Because most mutation request contracts are method-generic JSON, do not infer a payload. Resolve exact
identifiers from authoritative reads, quote int64 IDs as strings, use complete replacement lists
where the platform contract requires them, and read back the affected object after every confirmed
change. Whole-SOP deletion is not part of the registry. Team, role, and member deletion APIs are
present but high risk; invoke them only after the user explicitly confirms the exact target.
Team V2 create and update requests have captured request schemas. They require exact string IDs
and complete replacement arrays where the platform contract requires them; deletion requests only
need the exact target identifier and audit actor. Creating a member without a role may submit an
empty `skillGroupID[]`, while member update requires at least one role.

## Routing and safety notes

- On hosts where `pearl-ttp.tiktok-us.net` does not resolve (devbox / office network), pass the RD HTTP proxy as a global flag: `bytedcli --http-proxy "$TOOL_RUNNER_PROXY_RD_HTTP_URL" --site us-ttp pearl …`. The ROW domain is usually directly reachable — and the RD proxy may be rejected by the ROW gateway (`network_segregation_rejected`), so scope the proxy flag to US-TTP calls only.
- A successful country-list session probe proves authentication, not resource authorization. `PEARL_NOVA_API_ERROR` code `15006002` is blocked evidence for application/source/task reads; do not interpret it as an empty country.
- `--biz-mode` defaults to `L2L` and can be overridden explicitly.
- Never pass browser cookies or an `sso_session` value on the command line. Use the Pearl session login command so secrets stay in the private cache.
- Never infer consent for an Odin mutation from a read, report, cache, or layout request. A mutation requires the user's explicit target and payload, the machine-local write gate, and `--yes`.

## References

- [`../../invocation.md`](../../invocation.md)
- [`../../troubleshooting.md`](../../troubleshooting.md)
