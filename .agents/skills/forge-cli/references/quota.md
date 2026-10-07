# quota.md — quota commands

Use this reference to list or update resource groups, inspect their quota, pick a group for `forge job create`, diagnose whether a group has room for a workload, or list active tasks for a resource group. It also covers payoff units (结算单元 / billing units) and config change records (配置变更记录).

For the actual job submission see [job.md](job.md). For install / auth basics see [invocation.md](invocation.md).

Implemented quota commands:

- `forge quota resource-group list` — list resource groups (资源组); `--payoff-unit` scopes to one billing unit
- `forge quota resource-group update` — preview and update supported resource-group metadata
- `forge quota task list` — running / queued tasks for a resource group
- `forge quota payoff-unit list` — list payoff units (结算单元 / billing units)
- `forge quota payoff-unit update` — preview and update supported payoff-unit metadata
- `forge quota config-change list` — config modification records (配置变更)
- `forge quota quota-change list` — quota change history (配额变更记录)
- `forge quota request create` — preview and submit quota application, release, transfer, lending/reclaim, or whole-group migration

All `list` commands are read-only; `resource-group update`, `payoff-unit update`, and `request create` are mutating. The usual discovery flow is: `payoff-unit list` to find the unit → `resource-group list --payoff-unit <unit>` for its groups → `config-change list` for configuration history. Top-level actor-scoped collections do not implicitly filter to the current user: a bare list returns every visible match and explicit filters only narrow it. `quota task list` requires one resource group and returns only its running/queued occupancy tasks. `quota quota-change list` also requires an explicit resource-group or payoff-unit target; `--mine` only filters the operator within that history. Use each command's native `--mine` when the user asks for their own relation (`resource-group`: admin/member, `payoff-unit`: admin, `task`: owner, `config-change`: operator); never derive one relation from another command's output — see [Identity-only](#identity-only-default), [Task list](#task-list-running--queued-tasks), and [Payoff units](#payoff-units-forge-quota-payoff-unit-list).

---

## Identity-only (default)

Lists **every** resource group by default, returning identity fields only (name, payoff unit, admins, members) — no quota numbers, so the result stays fast. Narrow with filters; add `--with-quota` for quota details.

```bash
# All resource groups (identity fields only)
forge quota resource-group list

# Just your own groups
forge quota resource-group list --mine

# A specified person's groups
forge quota resource-group list --user someone

# Every group in one payoff unit
forge quota resource-group list --payoff-unit reckon_payoff

# Fuzzy name search
forge quota resource-group list --name aml-forge

# Your groups within one payoff unit
forge quota resource-group list --payoff-unit reckon_payoff --mine

# A specified person's groups within one payoff unit
forge quota resource-group list --payoff-unit reckon_payoff --user someone
```

> Scope rule (uniform across top-level actor-scoped collections): **a bare `list` returns everything visible; every filter only narrows.** There is **no** implicit "current user" default. `--mine` resolves the current authenticated username into the resource's real actor relation (`resource-group`: admin/member, `payoff-unit`: admin, `config-change`: operator); use `--user`, `--admin`, or `--operator` only when a specified person was named. Filters combine (AND): `--payoff-unit X --mine` = my groups in X; `--payoff-unit X --user Y` = Y's groups in X. `--all-users` is a deprecated compatibility alias for the resource-group default. All three top-level lists are paginated with `--page` / `--page-size`. For an overseas resource, remember the global `--site` or the query hits the wrong control plane.

Output items contain `name`, `payoff_unit_name`, `description`, `admins`, `members`. The `quotas` array is **absent** in this mode — do not tell the user "no quota" based on default output; just remind them to pass `--with-quota`.

---

## Update a resource group

`resource-group update` is a partial, mutating update. It always reads the exact resource group and prints a complete before/after preview to stderr before applying changes. Use `--dry-run` first for shared resources; it validates and previews without applying changes. A real update requires typing `yes`, while `--yes` is for an already-authorized automated mutation and skips only the prompt, not the preview.

```bash
# Read-only preview
forge quota resource-group update --name aml-forgeide \
  --description "training pool" \
  --priority 10 \
  --dry-run

# Replace admins/members after preview (repeat or comma-separate)
forge quota resource-group update --name aml-forgeide \
  --admin alice --admin bob \
  --member carol
```

Supported patch flags:

| Flag | Semantics |
|---|---|
| `--name` | Required exact resource-group name |
| `--description` | Replace description; `--description=` clears it |
| `--admin` | Replace the full admin list; repeat or comma-separate; cannot be empty |
| `--member` | Replace the full member list; repeat or comma-separate; `--member=` clears it |
| `--priority` | Replace priority; must be zero or greater |
| `--config` | Replace the opaque resource-group config; `--config=` clears it |
| `--dry-run` | Read, validate, preview, and return proposed JSON without applying changes |
| `--yes` | Skip the manual `yes` prompt after the preview |

Omitted fields remain unchanged. Existing `galaxy_node` remains visible in before/after output but is read-only because resource-group service-tree bindings must be changed through the service-tree workflow. Existing `alert_conf` is also visible but read-only because its field-specific validation belongs to the dedicated console alert workflow. Immediately before applying the update, the CLI checks the requested fields again: if any changed after the preview, it aborts; changes to other fields are preserved. This check is not atomic with applying the update. Coordinate with other editors, rerun `--dry-run`, review the refreshed preview, and then retry. The platform enforces permissions. Service-tree binding, alert configuration, payoff unit, and region are intentionally not update flags.

The stdout result has `dry_run`, `changed`, `changed_fields`, `before`, and `after`. Keep stdout as machine-readable JSON; the human preview and confirmation prompt are on stderr.

---

## Update a payoff unit

`payoff-unit update` follows the same partial-update safety contract as `resource-group update`: it reads the exact unit, prints a complete before/after preview to stderr, and requires `yes` unless `--yes` is explicitly supplied. Use `--dry-run` first for a shared billing unit; it validates and previews without applying changes.

```bash
# Read-only preview
forge quota payoff-unit update --name ad_aio \
  --description "training pool" \
  --priority 10 \
  --dry-run

# Replace the full administrator and tag lists
forge quota payoff-unit update --name ad_aio \
  --admin alice --admin bob \
  --tag production --tag regulated \
  --yes

# Change an explicit false value without losing false-vs-omitted semantics
forge quota payoff-unit update --name ad_aio --apply-quota-check=false --yes
```

Supported patch flags:

| Flag | Semantics |
|---|---|
| `--name` | Required exact payoff-unit name |
| `--description` | Replace description; `--description=` clears it |
| `--admin` | Replace the full admin list; repeat or comma-separate; cannot be empty |
| `--priority` | Replace priority; must be zero or greater |
| `--config` | Replace opaque payoff-unit config; `--config=` clears it |
| `--babi-source-name` | Replace BABI source name; it cannot be empty |
| `--apply-quota-check` | Replace quota-check setting; explicitly accepts `true` or `false` |
| `--pilot-galaxy-node` | Replace pilot galaxy node; `--pilot-galaxy-node=` clears it |
| `--tag` | Replace tags; repeat or comma-separate; `--tag=` clears them |
| `--dry-run` | Read, validate, preview, and return proposed JSON without applying changes |
| `--yes` | Skip the manual `yes` prompt after the preview |

Omitted fields remain unchanged. Immediately before applying the update, the CLI checks the requested fields again: if any changed after the preview, it aborts; changes to other fields are preserved. This check is not atomic with applying the update. Coordinate with other editors, rerun `--dry-run`, review the refreshed preview, and then retry. The primary `galaxy_node` is intentionally not an update flag: it is managed by the billing service tree, so migrate that binding through the service-tree workflow instead. The platform enforces permissions and reports denied updates.

The stdout result has `dry_run`, `changed`, `changed_fields`, `before`, and `after`. Keep stdout as machine-readable JSON; the human preview and confirmation prompt are on stderr.

---

## With quota (`--with-quota` or any quota filter)

Passing `--with-quota` — or any of the quota-level filters below — makes the CLI include detailed quota rows for each listed group. Each group's row then carries a `quotas` array. On a quota lookup failure for one group, that group gets a `quota_error` string; other groups still return their data.

```bash
# All visible groups with quota
forge quota resource-group list --with-quota

# Fuzzy search + quota
forge quota resource-group list --name aml-forge --with-quota

# Only GPU rows, only where there is capacity left
forge quota resource-group list --resource-type gpu --has-available

# Pick a concrete pool (e.g. g02) and product type
forge quota resource-group list --resource-annotation g02 --product-type guarantee --has-available
```

### Quota-level filter flags (each one auto-enables `--with-quota`)

| Flag | Notes |
|---|---|
| `--resource-type` | `gpu` / `cpu` / `training_ps` |
| `--resource-annotation` | GPU card / pool identifier, e.g. `g02`, `g10`, `h20`, `hwj590`. Non-GPU rows have this empty |
| `--product-type` | `guarantee` / `pbd` |
| `--dc` | data center, e.g. `lf`, `hl` |
| `--training-type` | `batch` / `realtime` |
| `--has-available` | keep rows where `available == null` (unlimited) **or** `available > 0` |

Use quota filters when the user already knows the relevant resource dimension and wants a smaller result set.

---

## Output contract

```json
{
  "ok": true,
  "total": 1,
  "page": 1,
  "page_size": 20,
  "items": [
    {
      "name": "aml-forgeide",
      "payoff_unit_name": "reckon_payoff",
      "admins": ["user_a"],
      "members": ["user_b", "user_c"],
      "links": {
        "forge2": "https://reckon.bytedance.net/forge2/resources/groups/aml-forgeide"
      },
      "quotas": [
        {
          "dc": "hl",
          "training_type": "batch",
          "resource_type": "gpu",
          "resource_annotation": "g02",
          "product_type": "guarantee",
          "rigid": 328,
          "elastic": 0,
          "total": 328,
          "allocated": 88,
          "available": 240
        },
        {
          "dc": "hl",
          "training_type": "batch",
          "resource_type": "cpu",
          "product_type": "guarantee",
          "unit": "cpu",
          "rigid": 11111,
          "elastic": null,
          "total": null,
          "allocated": 2055,
          "available": null
        }
      ]
    }
  ]
}
```

Quota rows are grouped by `(dc, training_type, resource_type, resource_annotation?, product_type)`.

### Links

Each item carries `links.forge2`, the resource-group detail page (**no query string** — appending one is known to route to the wrong tab). Treat `links.*` as opaque command output — do not hand-build a resource-group URL from `name`.

### Numeric fields are nullable

- `rigid` / `elastic` / `total` / `allocated` / `available` are all nullable integers.
- `null` means **unlimited**. A negative number is overallocation, not unlimited — don't conflate them.
- `total = rigid + elastic`; if either is `null`, `total` is `null`.
- `available = total - allocated`; if `total` is `null`, `available` is `null`.

When reasoning about capacity, treat `null` as "yes, there is capacity". With `--has-available`, null rows are kept.

### Per-group quota failures

If quota lookup failed for a specific group, that group carries `"quota_error": "<reason>"` and has no `"quotas"` array. The overall list call still succeeds; other groups are unaffected. Don't retry the whole list to recover one group — re-run with `--name <that-group>` scoped.

### What is NOT returned

- `unallocated`, `reserved`, `used`, `unused` — not reported by this command.
- `update_time` / `mem_to_cpu_quota_ratio` — not surfaced.
- Older map-shaped quota fields — not surfaced in the CLI output.

---

## Task list: running / queued tasks

Use `forge quota task list` to list running and queued tasks for a specific resource group.

> Scope guard: this command returns **only** `running` + `queued` tasks (the quota-occupancy view) and never includes finished / failed / killed jobs. It is the right tool only when the user explicitly asks for 已分配 / 正在运行 / 排队中 tasks. A generic "查看某资源组所有任务 / 任务列表 / 有哪些任务" wants **all jobs in the group** and must go to `forge job list --resource-group <name>` instead — see [job.md](job.md#list-jobs). Do not answer "所有任务" with this command.

```bash
# Running + queued tasks for one group
forge quota task list --resource-group aml-forgeide

# Only running tasks
forge quota task list --resource-group aml-forgeide --status running

# Only queued tasks, scoped to batch tasks in one allocated DC
forge quota task list --resource-group aml-forgeide \
  --status queued \
  --training-type batch \
  --allocate-dc lf

# Filter to one task owner
forge quota task list --resource-group aml-forgeide --user alice

# Current authenticated user's running / queued tasks in the group
forge quota task list --resource-group aml-forgeide --mine
```

Flags:

| Flag | Notes |
|---|---|
| `--resource-group` | Required. Exact resource group name |
| `--status` | `running` or `queued`; repeat or comma-separate. Default: `running,queued` |
| `--training-type` | `batch` or `realtime`; repeat or comma-separate. Default: `batch,realtime` |
| `--request-dc` | Requested data center filter; repeat or comma-separate |
| `--allocate-dc` | Allocated data center filter; repeat or comma-separate |
| `--mine` | Current authenticated task owner; mutually exclusive with `--user` |
| `--user` | Optional task owner filter |

Status choices:

- `running`: tasks currently using or already admitted to resource slots.
- `queued`: tasks waiting for scheduling / resource admission.

Output contract:

```json
{
  "ok": true,
  "resource_group": "aml-forgeide",
  "statuses": ["running", "queued"],
  "counts": {
    "running": 1,
    "queued": 1
  },
  "total": 2,
  "tasks": [
    {
      "status_group": "running",
      "task": {
        "id": 11,
        "user": "alice",
        "status": "running",
        "meta": {
          "job_id": 123,
          "job_name": "demo",
          "stage_id": 456
        },
        "team_info": {
          "resource_group": "aml-forgeide"
        }
      }
    }
  ]
}
```

Read `tasks[].status_group` for the requested status bucket. `tasks[].task.status` may be more granular; prefer `status_group` when summarizing running vs queued counts for users.

When summarizing tasks for users, use `tasks[].task.meta.job_id` as the primary identifier and label it **Job ID**. This is the ID users need for follow-up commands such as `forge job meta get`, logs, metrics, and event queries. Do **not** label `tasks[].task.id` as "Task ID" in a user-facing list; if it is useful to include, label it as `scheduler_task_id` or "scheduler task id" and put it after the Job ID.

---

## Payoff units: `forge quota payoff-unit list`

List payoff units (结算单元 / billing units) — the cost/settlement units that own resource groups. Identity + metadata only; results are paginated.

```bash
# All payoff units
forge quota payoff-unit list

# Payoff units you administer
forge quota payoff-unit list --mine

# Fuzzy name search
forge quota payoff-unit list --name aml

# Units administered by a specified user
forge quota payoff-unit list --admin someone

# Second page, 50 units per page
forge quota payoff-unit list --page 2 --page-size 50
```

| Flag | Notes |
|---|---|
| `--name` | fuzzy match payoff unit name |
| `--mine` | filter to payoff units administered by the current authenticated user |
| `--admin` | filter by a specified administrator username |
| `--page` / `--page-size` | 1-based page; default page-size 20 |

Output carries `total`, `page`, `page_size`, and the current page's `items`. Each item contains `id`, `name`, `description`, `admins`, `priority`, `tags`, `babi_source_name`, `galaxy_node`, `created_at`, `updated_at`. **Quota numbers are not included here** — for a unit's quota breakdown use `forge quota resource-group list --payoff-unit <name> --with-quota`, which models the (dc × type × annotation) fact table.

---

## Config change records: `forge quota config-change list` (配置变更)

Config modification records — create/update/delete edits to a payoff unit's or resource group's configuration, with a field-level diff.

```bash
# A payoff unit's config history
forge quota config-change list --name aml_engine --config-type payoff_unit

# A resource group's config history
forge quota config-change list --name aml-forgeide --config-type resource_group

# Only updates, across all payoff units
forge quota config-change list --config-type payoff_unit --change-kind update

# Changes made by the current authenticated user
forge quota config-change list --mine
```

| Flag | Notes |
|---|---|
| `--name` | payoff unit or resource group name(s); repeat or comma-separate |
| `--config-type` | `payoff_unit` or `resource_group` (validated) |
| `--mine` | Current authenticated operator; mutually exclusive with `--operator` |
| `--operator` | operator username(s); repeat or comma-separate |
| `--change-kind` | `create` / `update` / `delete` (validated); repeat or comma-separate |
| `--start-time` / `--end-time` | unix seconds window (inclusive) |
| `--page` / `--page-size` | 1-based page; default page-size 20 |

Each record carries `id`, `record_name`, `config_type`, `operator`, `region`, `created_at`, `change_kind`, and `diffs[]` — a field-level list with `field`, `label`, and `op`, where `op` is `added` / `removed` / `modified`. Full configuration snapshots (`old_config_payload` / `new_config_payload`) are no longer included in CLI output; use `diffs[]` to read the changes and its labels when summarizing.

For JSON-valued fields (`config` / `alart_conf`), `diffs[].entries[]` may provide `{path, old_value, new_value, op}`. When entries are nonempty, the CLI omits that diff's duplicate top-level `old_value` / `new_value`; consumers should read values from entries. When entries are absent or empty, the CLI retains the existing field values as a fallback; absent/empty entries do not establish that there were no changes. Non-JSON fields, including comma-separated admins/members, keep their legacy representation.

Entry paths are relative to `diff.field`; `path: ""` means the field root. Preserve escaped keys, array order, and `[#type]` markers for JSON-encoded containers. Values are display strings: keep exact number tokens and quotes for type changes, distinguish `null`, `{}`, `[]`, and the empty string, and use `op` to distinguish an added/removed leaf from an empty value. The CLI passes entries through in JSON without reparsing or reordering them. If the response has no entries, read `diffs[].old_value` / `new_value` as the fallback. The CLI cannot recover details missing from those values or precision already lost in them.

> This endpoint honors server-side pagination — `--page` / `--page-size` map straight through.

---

## Quota change history

Use `forge quota quota-change list` for quota additions/releases, lending/reclaim history, or Job quota occupancy changes. Require exactly one target kind: `--resource-group` or `--payoff-unit`. Names are exact and accept repeated flags or comma-separated values. `--mine` filters the operator within those targets; it does not discover the user's groups or units.

```bash
# Resource group quota history
forge quota quota-change list --resource-group training-pool --site cn

# Payoff unit history
forge quota quota-change list --payoff-unit training-budget --site us-ttp

# Include child resource group operations in a payoff unit's history
forge quota quota-change list --payoff-unit training-budget \
  --include-resource-groups --site i18n

# Job occupancy changes, explicitly selected
forge quota quota-change list --resource-group training-pool \
  --operation AllocateTrainingTask,AdjustTrainingTask,ModifyTrainingTask,ReleaseTrainingTask \
  --site cn
```

All four sites (cn, i18n, us-ttp, eu-ttp) query quota operation history. Historical coverage depends on when each site began recording these operations. Earlier legacy transfers are outside this command's coverage; an empty time window must not be interpreted as proof that no earlier transfer occurred.

Every query has a time range. If both time flags are omitted, query from local midnight 14 calendar days ago through today (exclusive next local midnight), matching the frontend calendar-day lookback. To override it, provide both `--start-time` and `--end-time` as positive Unix seconds with start < end. A single bound or an explicitly zero/negative time is rejected. There is no implicit all-history mode. Large explicit windows may still fail; narrow the range and retry.

Common filters: `--operator` (repeat/comma-separated), `--mine` (exclusive with operator), `--start-time` / `--end-time` (start inclusive and end exclusive), `--page` (one-based), `--page-size` (default 20). Exactly one target kind remains required even with `--mine` or `--request-id`.

Additional filters: `--operation`, `--dc`, `--training-type`, `--product-type`, `--resource-type`, `--resource-annotation`, `--request-id`, and `--include-resource-groups`. All except `--request-id` and the boolean `--include-resource-groups` accept repeated flags or comma-separated values. The maximum page size is 100.

Quota operations default to `AddTrainingQuota,ReleaseTrainingQuota`, matching the default quota history view. To include Job occupancy changes, explicitly add `AllocateTrainingTask`, `AdjustTrainingTask`, `ModifyTrainingTask`, and/or `ReleaseTrainingTask` to `--operation`. An explicit list replaces the default. Resource types use the history's values, e.g. `physical_gpu` for GPU, `cpu`, `training_ps`, or `exclusive_ps`. `--include-resource-groups` is valid only with `--payoff-unit`; by default quota history returns only the unit's own operations.

Output contains `records`, `total`, `page`, `page_size`, `has_more`, and the applied `start_time` / `end_time` in Unix seconds. Request the next page while `has_more` is true, passing those same time bounds to keep the window stable across dates or timezone changes.

Records contain `request_id`, `operation`, resource dimensions, `operator`, `created_at`, optional `job_id`, and `log_context.before_change` / `after_change` / `delta` with optional `total`, `used`, and `lent`. Zero is a real value; missing snapshot fields are unknown, never zero. Keep total quota changes, occupancy changes (`used`), and lending changes (`lent`) distinct. Do not classify lending/reclaim direction from `operation` alone; inspect the `lent` change.

Configuration edits (admins, descriptions, etc.) remain `forge quota config-change list`.

---

## Working patterns

### "Which group should I submit into for an A100 / g02 / whatever guarantee batch job?"

```bash
forge quota resource-group list \
  --with-quota \
  --resource-type gpu \
  --resource-annotation g02 \
  --product-type guarantee \
  --training-type batch \
  --has-available
```

Read the `items[].quotas[]` and recommend the group with the largest `available`. If multiple DCs, prefer the one matching the user's region (ask if unclear). If every row's `available` is 0 or negative, tell the user the pool is saturated and suggest either PBD product, a different card pool, or waiting.

### "Does resource group X still have room for my job?"

```bash
forge quota resource-group list --name <X> --with-quota
```

Scan `items[0].quotas[]`:
- `available > 0`: has room on that dimension.
- `available == null`: unlimited on that dimension (often CPU guarantee / PS elastic).
- `available <= 0`: full / overallocated. Combined with `--has-available` to list only the dimensions that still have headroom.

### "Why is my job queuing?" — resource-group view first

Start with the group-level active tasks:

```bash
forge quota task list --resource-group <X> --status queued
```

If the queued list is large, compare it with capacity:

```bash
forge quota resource-group list --name <X> --with-quota
```

`quota task list` shows what is currently running / waiting in that resource group; it does not explain every scheduler decision for a specific job. If the user already has a `--job-id`, pair it with `forge job event query --job-id <id> --event-level ERROR` and `forge job meta get` for task-side context; if those don't resolve it, suggest platform oncall.

### Pair with `forge job create`

When the user lands on a group name, next step is `forge job create --resource-group <name>` from inside the fetched workspace (see [job.md](job.md)). If the user omits `--resource-group`, `job create` will list the current user's groups and prompt for a selection; it never defaults to a test group. `quota resource-group update` changes group metadata only; it does not submit jobs or edit quota quantities.

## Quota requests: apply, release, transfer, and migration

Use `forge quota request create` for ordinary and reserved quota changes. Always pass the
conversation's selected `--site`. These operations are mutating: use them only
when the user asks to apply, release, transfer, lend, reclaim quota or migrate a resource group.
`--quantity 0` is accepted but still submits a real operation or approval request.
Use `--dry-run` when you only want a preview.

Start with `--dry-run`, review the target, quantity, route and approvers, then
submit with manual `yes` or an already-authorized `--yes`. `--yes` skips local
confirmation; it never removes platform approval requirements.

```bash
# Apply for eight physical GPU cards in a resource group
forge quota request create --operation apply --resource-group training \
  --dc lf --training-type batch --resource-type gpu \
  --resource-annotation g02 --quantity 8 --reason "training capacity" --dry-run

# Release CPU quota from a payoff unit
forge quota request create --operation release --payoff-unit training-budget \
  --dc lf --training-type batch --resource-type cpu \
  --quantity 100 --reason "unused capacity" --dry-run

# Transfer group quota; destination dimensions default to the source
forge quota request create --operation transfer --resource-group source-group \
  --to-resource-group target-group --dc lf --training-type batch \
  --resource-type gpu --resource-annotation g02 --quantity 8 \
  --reason "rebalance training capacity" --dry-run

# Transfer across payoff units and data centers
forge quota request create --operation transfer --payoff-unit source-unit \
  --to-payoff-unit target-unit --dc lf --to-dc hl --training-type batch \
  --resource-type cpu --quantity 100 --reason "capacity relocation" --dry-run

# Lend unused payoff-unit quota (increase reserved quota)
forge quota request create --operation lend --payoff-unit training-budget \
  --dc lf --training-type batch --resource-type gpu --resource-annotation g02 \
  --quantity 8 --reason "lend unused capacity" --dry-run

# Reclaim previously lent quota (decrease reserved quota)
forge quota request create --operation reclaim --payoff-unit training-budget \
  --dc lf --training-type batch --resource-type gpu --resource-annotation g02 \
  --quantity 8 --reason "restore training capacity" --dry-run

# Move an entire resource group, including quota, into another payoff unit
forge quota request create --operation migrate --resource-group training \
  --to-payoff-unit target-unit --reason "billing ownership change" --dry-run
```

| Flag | Meaning |
|---|---|
| `--operation` | Required: `apply`, `release`, `transfer`, `migrate`, `lend`, or `reclaim` |
| `--resource-group` / `--payoff-unit` | Exactly one exact source name; group ownership is inferred |
| `--to-resource-group` | Required for group-to-group quota transfer |
| `--to-payoff-unit` | Required for unit-to-unit quota transfer or whole-group migration |
| `--dc`, `--training-type`, `--resource-type` | Required except for migration; training type is `batch`/`realtime`, resource is `gpu`/`cpu`/`training_ps` |
| `--product-type` | `guarantee` (default) or `pbd`; Training PS supports `guarantee` only |
| `--resource-annotation` | Required physical GPU card/pool; omitted for CPU and Training PS |
| `--quantity` | Required non-negative integer: GPU cards, CPU cores, or Training PS GB; omitted for migration |
| `--to-dc`, `--to-training-type`, `--to-resource-type`, `--to-product-type`, `--to-resource-annotation` | Transfer destination dimensions; omitted values inherit applicable source dimensions |
| `--reason` | Required explanation for the change |
| `--dry-run` | Read and preview without applying or submitting |
| `--yes` | Skip local confirmation after preview |

Apply/release targets the selected object's parent allocation. A group can only
transfer quota to another group; a payoff unit can only transfer quota to another
payoff unit. Cross-unit group transfers infer both units. `migrate` changes group
ownership and carries the whole quota, so it rejects quantity and dimension
flags. If no physical quota is reported, the preview shows an empty list and a
warning; migration still carries the whole group and its quota at execution.
To move jobs between groups, use `forge job resource-group update` instead.

`lend` and `reclaim` require `--payoff-unit` and do not accept destination flags.
They operate on reserved quota, using the same physical GPU/CPU guarantee/PBD
and Training PS guarantee dimensions supported by the backend. Lending increases
reserved quota and is limited to total minus allocated minus already-reserved
quota. Reclaiming decreases reserved quota and is limited to the amount already
reserved; it does not use ordinary unallocated capacity. Both execute directly
without BPM, matching the console route. The CLI checks the server-provided
reclaim disable policy and exact user exemptions again before submission;
platform authorization and the backend's current policy remain authoritative.

Platform/REAM administrators and the parent payoff-unit administrators can
execute group apply/release directly. Other group callers submit approval
requests. Payoff-unit apply/release, both transfer kinds and whole-group migration
always submit approval requests. The CLI resolves administrator lists and
additional approvals automatically, and refuses to submit when a required list
is missing. Correct the resource's administrator configuration before retrying.

Release and transfer previews use rigid/source quota minus current allocations;
payoff-unit capacity also excludes reserved quota. The `available` value from
`resource-group list --with-quota` includes elastic quota and is not the amount
that can be released. `preview.source_capacity` explicitly distinguishes finite,
unlimited and unknown capacity. Upstream payoff-unit application capacity may
be unknown; the preview warns and submits for approval without promising that
quota is available. The platform makes the final capacity decision.

The CLI re-reads ownership, approvers, permissions and quota immediately before
submission. A changed route, ownership, approval list or migration quota aborts;
rerun `--dry-run` to review the current state. This check is not atomic with the
write, and capacity can still change while a request awaits approval.

Interpret `status` precisely:

- `dry_run`: preview only, no write or work order.
- `applied`: direct quota change succeeded; there is no work order ID.
- `submitted`: approval request created; quota is not yet confirmed delivered.
  Open `work_order_url` to view progress or handle approval in BPM.
- `outcome_unknown` (non-zero exit): submission may have succeeded. Do not retry
  automatically. Check quota transfer history in Forge and same-site BPM work
  orders, reconcile the request, then decide whether a retry is needed.

HDFS/OnlinePS quantity changes, bulk quota requests and approval
or cancellation actions are not supported by this command. Use the corresponding
Forge console workflow for those operations.

The CLI does not query work-order details. Follow the returned BPM link for
progress and approval, then verify current quota after successful completion.

Use `forge job resource-group update --with-quota` to move a job together with
its quota. The quota request command covers apply, release, transfer, reserved
lending/reclaim, and whole-resource-group migration.
