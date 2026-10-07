# inspection.md — resource inspection tasks

Use this reference for Forge **resource inspection tasks** (巡检规则 / 巡检任务) — CRUD plus on-demand execution of inspection rules that periodically scan PSMs, resource groups, payoff units, or BUs for under-utilized / low-QPS / cleanable models, plus the offline rule catalog that decides which rule a task runs.

The **kill whitelist** (强杀白名单) surface — exempting a job or user in a resource group from inspection-driven automatic kill — is a separate reference: [inspection_whitelist.md](inspection_whitelist.md).

For install / auth / `--site` basics see [invocation.md](invocation.md); these commands take the usual `--network` / `--site` runtime flags.

**Inspection data is per control plane — the site is never irrelevant here.** A task (or whitelist) lives on exactly one site: one created on `cn` is invisible on `i18n` / `eu-ttp` / `us-ttp`, and every list/query returns only the site you asked.

- If the user names a site (or gives a Reckon URL), pass `--site` explicitly.
- If they don't, the command still runs against a single default site (`cn`). Say which site you queried and that other control planes hold separate tasks (offer to re-run elsewhere). Never present one site's result — including an empty one — as "you have no tasks"; it only means none on that site.

All commands emit JSON by default; do not add `--json`.

Not every control plane supports resource inspection yet. If a command fails with a `method not found` error, or a create returns no `id`, the target site does not have it enabled — tell the user the operation did not take effect instead of reporting success.

Implemented commands:

- `forge inspection task create | list | update | delete | execute | enable | disable`
- `forge inspection rule list`
- `forge inspection scheduler-job list` — run history / execution results
- `forge inspection target list | role list | gpu-type list` — discover valid values for `--inspection-target` and the filters
- `forge inspection kill-whitelist create | list | update` — see [inspection_whitelist.md](inspection_whitelist.md)

---

## Inspection tasks (巡检规则)

An inspection task is a scheduled rule. Its top-level shape: a `name`, a `task_type` (what is being inspected), an `inspection_target` (the concrete PSM / resource group / payoff unit / BU), and a nested `task_config` describing the schedule, the inspection job type, and alerting.

### Enums

`--task-type` (and the `task_type` filter / update) accept these labels:

| Label | Meaning |
|---|---|
| `psm` | PSM inspection |
| `resource` | Resource-group inspection |
| `online-ps` | OnlinePS inspection |
| `bu` | BU inspection |
| `payoff-unit` | Payoff-unit inspection |

`task_config` enum integers (the config is raw JSON; pass enums as numbers). Output normalizes them to labels in `task_config_summary`:

- `time_type`: `0` fix-rate, `1` cron
- `inspection_job_type`: the inspection **rule** the task runs (see "Which inspection rule" below). One rule per task.

### Which inspection rule does a task run? (配置巡检规则)

Each task runs exactly one inspection rule (`inspection_job_type`), chosen from the set valid for its `task_type` — mirroring the Forge console, where the rule is a single-select that depends on the task type. Discover the catalog with `forge inspection rule list`:

```bash
# All rules, with which task type(s) each is valid for
forge inspection rule list

# Only the rules a resource-group task may run
forge inspection rule list --task-type resource
```

Output: `{ "ok": true, "task_type": "resource", "total": 8, "rules": [ { "code": 10, "label": "low-deployment-rate", "description": "...", "task_types": ["resource"], "deprecated_for_new": false }, ... ] }`. This is a static offline catalog; it does not call the backend.

Then select the rule by label with `--job-type` on `task create` / `task update` instead of hand-writing the enum integer:

```bash
forge inspection task create --name daily-rg --task-type resource \
  --inspection-target rg-a --job-type low-deployment-rate \
  --task-config '{"time_type":1,"cron":"0 9 * * *","inspection_job_config":{"within_seconds":1800},"task_alert_config":{"alert_switch":false},"model_alert_config":{"alert_switch":false}}'
```

`--job-type` writes `inspection_job_type` into `task_config`, validates the rule is valid for `--task-type`, and rejects rules the console no longer offers for new tasks (`deprecated_for_new`). You may still set `inspection_job_type` directly in `--task-config`; passing both with different values is rejected. On `task update`, `--job-type` requires `--task-config` (update replaces the whole config) and is checked against `--task-type` only when you also pass it — otherwise the rule is left for the backend to validate against the task's stored type. The rule labels and their integer codes:

`0` low-qps-model · `1` no-onlineps-sail-model · `2` no-serving-sail-model · `3` no-serving-lite-model · `4` low-onlineps-qps-model · `5` low-utilization-rate-model · `6` low-utilization-rate-batching-model · `7` low-utilization-rate-streaming-model · `8` no-onlineps-batching-sail-model · `9` bu-low-qps-model · `10` low-deployment-rate · `11` low-utilization-rate-olap · `12` low-deployment-rate-payoff-unit · `13` cleanable-streaming-job

Picking the rule only chooses *what* to inspect. Its thresholds (metric, percentage, and the 巡检指标 filters — utilization %, training type, task status, exclude-startup minutes, effective-duration, …) are configured separately in `inspection_job_config`; see [Inspection conditions](#inspection-conditions-巡检指标) below.

### task_config JSON schema

Pass `--task-config` as inline JSON or `@file.json`. It maps directly to the backend `TaskConfig` (snake_case, enum integers):

```jsonc
{
  "time_type": 1,                 // 0 fix-rate, 1 cron (required)
  "fix_rate": 0,                  // seconds between runs; required and > 0 when time_type=0
  "cron": "0 9 * * *",            // standard cron; required and valid when time_type=1
  "inspection_job_type": 11,      // the rule (see "Which inspection rule"); prefer --job-type
  "inspection_job_config": {       // the rule's window + conditions — see "Inspection conditions" below
    "within_seconds": 300,        // averaging window in SECONDS (console shows minutes; 5 min = 300)
    "is_or": false,               // false = match ALL condition groups (AND); true = match ANY (OR)
    "filters": [                  // 巡检指标 condition groups (this is where the rule's thresholds live)
      [
        { "field": "path",         "operator": "=", "value": "utilization/GPU/gpu_util" },
        { "field": "weighted_avg", "operator": "<", "value": "30" }
      ]
    ],
    "inspection_targets": [],      // explicit complete resource-group list; wins over payoff_units
    "payoff_units": []             // dynamically resolve these payoff units to resource groups
  },
  "task_alert_config": { "alert_switch": false },   // task-level alerting
  "model_alert_config": { "alert_switch": false }   // per-model alerting and kill_threshold; exemptions use kill-whitelist commands
}
```

The CLI validates that `--task-config` is a JSON object and that OLAP-backed rules (codes 10, 11, 12) explicitly set an integer `inspection_job_config.within_seconds` between 1 and 86400 seconds; the backend validates `time_type` + `fix_rate`/`cron` and authorization, and surfaces precise errors (e.g. `FixRate must be greater than 0`, `Cron is not a valid cron expression`). Cron runs in the site scheduler timezone: **Asia/Shanghai (UTC+8) for CN**, **UTC for i18n / US-TTP / EU-TTP**. `fix_rate` is in seconds (the console edits minutes).

When unsure of the exact conditions for a rule, fetch an existing task with `forge inspection task list` and copy its `task_config` as a starting point.

### Inspection conditions (巡检指标)

Picking the rule with `--job-type` only chooses *what* to inspect; the actual thresholds — the console's "巡检指标 / 符合以下条件" builder — live in `inspection_job_config.filters`, which the CLI passes through untouched. An agent must write them by hand, so they are documented here.

- `filters` is a **list of condition groups**; each group is a list of `{ field, operator, value }` clauses that are ANDed together.
- `is_or` joins the groups: `false` = a model must match every group (符合所有条件), `true` = matching any group is enough (符合任一条件).
- `within_seconds` is the averaging window in **seconds** (the console's "取过去 N min 的平均值" — multiply minutes by 60). For `low-deployment-rate`, `low-utilization-rate-olap`, and `low-deployment-rate-payoff-unit`, it is **required**, with a range of **1–86400 seconds**; there is no implicit API default. Set `300` explicitly for five minutes. Creation, full config replacement, and the merged `--set` config are checked locally. The backend also checks stored configs when enabling/rescheduling or manually executing an old rule: repair an invalid window with `task update --task-id <id> --set inspection_job_config.within_seconds=300` before retrying.

The **24-hour maximum** applies to these three inspection rules. The console edits minutes and bounds its form to **1–1440 minutes for utilization** and **30–1440 minutes for deployment**; its initial values are 5 and 30 minutes respectively. The raw API/CLI contract accepts positive integer seconds up to 86400, so the CLI retains that API lower bound rather than imposing the console's higher form minimum. For console-compatible configurations, use at least `60` seconds for utilization and `1800` for deployment. Unlike the console's input clamping, the CLI rejects invalid windows without modifying the supplied value. This inspection lookback is separate from the **7-day** job/role utilization query limit and the **31-day** hit-history list window.

For a utilization rule (`low-utilization-rate-olap`) or deployment rule (`low-deployment-rate` / `low-deployment-rate-payoff-unit`), the first two clauses of a group are the metric and its percentage threshold:

- `path` — the metric (console 指标 dropdown), operator `=`. Utilization metrics: `utilization/CPU`, `utilization/GPU/gpu_util`, `utilization/GPU/sm_active`, `utilization/GPU/tensor_core_active`, `utilization/GPU/vram`, `utilization/MEM`, `cpu_vs_gpu`. Deployment metrics: `deployment_rate/CPU`, `deployment_rate/GPU`, `deployment_rate/training_ps`.
- `weighted_avg` — the percentage threshold (console 利用率百分数 / 部署率百分数), operator one of `< <= > >= = !=`.

The remaining clauses are optional filters (each `field` : console label : usual operator : value):

| `field` | Console label | Operator | Value |
|---|---|---|---|
| `train_type` | 训练类型 | `=` | utilization: `batch` / `stream`; deployment: `batch` / `realtime` (omit = total) |
| `product_type` | 商品类型 | `=` | `guarantee` / `pbd` (omit = total) |
| `gpu_type` | 卡型 | `=` | a GPU card key (GPU metrics only) |
| `role` | Role | `in` | comma-joined roles |
| `status` | 任务状态 | `in` | comma-joined subset of `running,success,failed,killing,killed` |
| `tags` | tags | `contain` / `not contain` | string |
| `model_type_label` | model_type_label | `contain` / `not contain` | comma-joined values; substring match against any value / none of the values |
| `job_duration` | 有效时长大于 | `>` | minutes |
| `time_offset` | 向前检测 | `=` | minutes |
| `remove_head_minute` | 除去启动 | `=` | minutes |
| `remove_tail_minute` | 除去结尾 | `=` | minutes |
| `remove_stage_head_minute` | 除去Stage启动 | `=` | minutes |
| `remove_stage_tail_minute` | 除去Stage结尾 | `=` | minutes |
| `remove_failover_before_minute` | 除去 failover 前 | `=` | integer string, 0–10080 minutes; utilization rules only |
| `remove_failover_after_minute` | 除去 failover 后 | `=` | integer string, 0–10080 minutes; utilization rules only |

For example, `{"field":"model_type_label","operator":"contain","value":"召回,精排"}` matches a label containing either `召回` or `精排`. `not contain` excludes either match. Empty values are ignored by the executor; do not write `=` / `!=` for this field.

### Exclude failover time from utilization

Add the failover clauses to each utilization condition group in `inspection_job_config.filters`. They use the existing JSON configuration surface, not standalone CLI flags. Each `value` must be an **integer string** from `"0"` through `"10080"`, in minutes. The executor validates these values.

- Both fields absent: failover exclusion is disabled.
- Either field present, including `"0"`: exclude the failover interval itself; the other field defaults to zero extra padding.
- Before/after padding extends the excluded interval around `failover_start` / `failover_finished`. The executor removes raw metric samples before averaging; a job with no remaining metric rows cannot become a low-utilization candidate. This does not infer framework-specific warmup.
- To disable exclusion, remove both clauses from each affected group. Setting both to `"0"` keeps exclusion enabled.

For example, replace the utilization conditions with GPU utilization below 30%, excluding failover plus two minutes before and five minutes after:

```bash
forge inspection task update --task-id 745 \
  --set 'inspection_job_config.filters=[[{"field":"path","operator":"=","value":"utilization/GPU/gpu_util"},{"field":"weighted_avg","operator":"<","value":"30"},{"field":"remove_failover_before_minute","operator":"=","value":"2"},{"field":"remove_failover_after_minute","operator":"=","value":"5"}]]'
```

This replaces the **entire filters array**, including all groups and their existing conditions; read the task first and include every condition you intend to retain. `--set` preserves other config fields, including `within_seconds`, scheduling and alert settings. It does not support array-index paths such as `filters.0.2.value`. For creation or full config replacement, put the same clauses into `--task-config` under `inspection_job_config.filters` and explicitly set the required `within_seconds`.

Failover-event query failures abort evaluation instead of being treated as an empty event history. Exclusion depends on the executor deployment at the selected site; successfully storing the JSON alone does not prove that it was applied. Event pairing is limited to the expanded query window: a failover spanning that entire window without either endpoint inside it cannot be inferred.

### Utilization configuration example

A resource-group utilization rule that flags currently-running streaming models whose 5-minute average GPU util stays under 30%, ignoring the first 10 minutes and jobs shorter than 60 minutes:

```bash
forge inspection task create --name gpu-underused --task-type resource \
  --inspection-target aml-forgeide --job-type low-utilization-rate-olap \
  --task-config '{
    "time_type": 1, "cron": "0 9 * * *",
    "inspection_job_config": {
      "within_seconds": 300, "is_or": false,
      "filters": [[
        { "field": "path",              "operator": "=",  "value": "utilization/GPU/gpu_util" },
        { "field": "weighted_avg",      "operator": "<",  "value": "30" },
        { "field": "train_type",        "operator": "=",  "value": "stream" },
        { "field": "status",            "operator": "in", "value": "running" },
        { "field": "remove_head_minute","operator": "=",  "value": "10" },
        { "field": "job_duration",      "operator": ">",  "value": "60" }
      ]]
    },
    "task_alert_config": { "alert_switch": false },
    "model_alert_config": { "alert_switch": false }
  }'
```

The low-QPS rules (`low-qps-model`, `low-onlineps-qps-model`, `bu-low-qps-model`) don't use `filters`; they read the top-level `min_qps` / `qps_range_time` / `max_tolerance_time` / `query_regions` fields on `inspection_job_config` instead.

### Create inspection task

```bash
# Cron-scheduled resource-group utilization rule
forge inspection task create \
  --name daily-rg-utilization \
  --task-type resource \
  --inspection-target aml-forgeide \
  --task-config '{"time_type":1,"cron":"0 9 * * *","inspection_job_type":5,"inspection_job_config":{"within_seconds":300},"task_alert_config":{"alert_switch":false},"model_alert_config":{"alert_switch":false}}'

# From a config file, created disabled
forge inspection task create --name nightly --task-type resource \
  --inspection-target rg-a --task-config @config.json --enabled=false
```

| Flag | Notes |
|---|---|
| `--name` | Required task name |
| `--task-type` | Required: `psm` / `resource` / `online-ps` / `bu` / `payoff-unit` |
| `--inspection-target` | Required concrete target (PSM, resource group, payoff unit, or BU name) |
| `--task-config` | Required JSON (inline or `@file`); see schema above |
| `--job-type` | Optional rule label (see `forge inspection rule list`); sets/validates `task_config.inspection_job_type` for `--task-type` |
| `--description` | Optional |
| `--creator` | Optional; defaults to the current authenticated user. The backend stores this as the task creator |
| `--enabled` | Default `true`; `--enabled=false` creates the task without scheduling it |

Output: `{ "ok": true, "id": <new task id>, "creator": "<user>" }`. Report the new `id`.

### List inspection tasks

```bash
forge inspection task list
forge inspection task list --mine                               # 我的巡检任务
forge inspection task list --task-id 745                        # exact rule lookup
forge inspection task list --task-type resource --inspection-target aml-forgeide
forge inspection task list --owner alice --page 1 --page-size 50
```

For "我的巡检任务 / my inspection tasks" use `--mine` — it resolves the current authenticated user. Do **not** invent an `--owner self` / `--owner me`: `--owner` is matched as an exact username, so a sentinel like `self` silently matches nobody and looks like "you have no tasks".

| Flag | Notes |
|---|---|
| `--task-id` | Positive exact rule ID; combines with owner and other filters by AND |
| `--task-name` | Exact task name |
| `--task-type` | Filter by task type label |
| `--inspection-target` | Exact target; the backend requires `--task-type` alongside it (the CLI enforces this) |
| `--mine` | Only tasks you created (resolves the current user); mutually exclusive with `--owner` |
| `--owner` | Filter by an **exact** creator username (no `self`/`me` sentinel — use `--mine`) |
| `--page`, `--page-size` | Pagination (defaults page 1, size 20) |
| `--order-by`, `--order` | Sort column (default `id`) and direction (`asc` / `desc`, default `desc`) |

Output has `total`, `page`, `page_size`, and `tasks`. Each task carries label fields (`task_type`), the raw `task_config`, a decoded `task_config_summary` (`time_type`, `fix_rate`, `cron`, `inspection_job_type`, and `inspection_job_type_desc`), and `can_edit`. Lead with `id`, `name`, `task_type`, `inspection_target`, whether `switch` (enabled) is true, and `can_edit`. The `id` is the handle for update / delete / execute. Use `task list --task-id <id>` to read one exact rule.

When presenting a task's rule to a user, show the human-readable **`inspection_job_type_desc`** (e.g. `实时 OLAP 下的低利用率`, `资源组低部署率`), not the raw kebab `inspection_job_type` label (`low-utilization-rate-olap`) — the label is an internal identifier for `--job-type`/filters, not a name users recognize.

### Dynamic resource-group scope and cleanable streaming jobs

For rule types **10 / 11**, a nonempty `inspection_job_config.inspection_targets` is the complete explicit resource-group scope. It takes precedence over `payoff_units`; the two are not unioned. With no explicit groups, `payoff_units` resolves the union of those units' current resource groups **on every execution**, so later membership changes are included. Only when both arrays are empty do these two rules fall back to the top-level `inspection_target`. To switch an existing rule to dynamic units, clear its explicit groups in the same update:

```bash
forge inspection task update --task-id 745 --inspection-target 'unit-a,unit-b' \
  --set 'inspection_job_config.inspection_targets=[]' \
  --set 'inspection_job_config.payoff_units=["unit-a","unit-b"]'
```

The top-level target is the searchable label for this batch scope. Do not apply this resource-group expansion contract to type 12 (`low-deployment-rate-payoff-unit`). Multi-role conditions use a comma-joined `role` value. The retired `train_mode` filter is no longer a supported way to constrain utilization rules.

`cleanable-streaming-job` (type **13**) also uses explicit groups first, otherwise dynamic `payoff_units`; it does **not** fall back to the top-level target. Supply one of these arrays. It uses the backend's cleanable-streaming signal and does not require an OLAP `within_seconds` or utilization filters. A disabled rule can be prepared as follows; enabling scheduling is a separate explicit action:

```bash
forge inspection task create --name cleanable-streaming --task-type resource \
  --inspection-target 'unit-a,unit-b' --job-type cleanable-streaming-job --enabled=false \
  --task-config '{"time_type":1,"cron":"0 9 * * *","inspection_job_config":{"payoff_units":["unit-a","unit-b"]},"task_alert_config":{"alert_switch":false},"model_alert_config":{"alert_switch":false}}'
```

### Update inspection task

Only the flags you pass are sent; unchanged fields are left intact.

```bash
forge inspection task update --task-id 12 --enabled=false           # pause scheduling
forge inspection task update --task-id 12 --description "paused for migration"
forge inspection task update --task-id 12 --new-owner bob           # transfer rule ownership
forge inspection task update --task-id 745 --set task_alert_config.alert_switch=false   # 改一个字段，不用重写整份配置
forge inspection task update --task-id 745 --set model_alert_config.kill_threshold=5 --set inspection_job_config.within_seconds=600
forge inspection task update --task-id 12 --task-config @config.json # replace the whole config
```

To change **one nested config field**, use `--set path=value` — do **not** hand-roll a fetch-modify-resubmit script. The backend replaces `task_config` wholesale, so `--set` fetches the task's current config using an exact `task_id` query, patches the given path(s), and writes the merged config back for you (including dropping the nulls the list returns, which the backend rejects on write). This is the ergonomic way to e.g. turn off a notification switch or bump a threshold. Note `--set field=null` **removes** the field (nulls can't be stored), rather than setting it to an explicit null.

| Flag | Notes |
|---|---|
| `--task-id` | Required task id (`--id` is a deprecated compatibility alias) |
| `--name`, `--description`, `--task-type`, `--inspection-target` | Sent only when provided |
| `--new-owner` | Transfer to a nonempty username; backend edit permission checks apply. Changes current `creator`/owner, not historical hit-record owner snapshots |
| `--set` | Patch one `task_config` field as `path=value` (repeatable), e.g. `task_alert_config.alert_switch=false`. Path is dot-separated within `task_config`; value is parsed as JSON (`false`→bool, `600`→number), falling back to a string. Read-modify-write; **mutually exclusive** with `--task-config` |
| `--task-config` | **Replace the whole** config as JSON (inline or `@file`); sent only when provided |
| `--job-type` | Rule label; rewrites `inspection_job_type` inside `--task-config` (requires `--task-config`, since that path replaces the whole config) |
| `--enabled` | Enable/disable scheduling; sent only when provided |

At least one mutable flag is required. Output includes the updated `task` when the backend returns it.

### Enable / disable inspection task (启用 / 停用)

Pause or resume a task's scheduling without editing its config. These are thin wrappers over update's `task_switch`; the backend cancels the scheduled run on disable and recreates it on enable.

```bash
forge inspection task enable --task-id 12    # resume scheduling
forge inspection task disable --task-id 12   # pause scheduling
```

`forge inspection task update --task-id 12 --enabled=false` is equivalent to `disable`.

### Delete inspection task

Destructive. Requires confirmation: interactively type `yes`, or pass `--yes` for automation.

```bash
forge inspection task delete --task-id 12
forge inspection task delete --task-id 12 --yes
```

Deleting an enabled task also cancels its scheduled runs on the backend.

### Execute inspection task

Trigger a one-off run now (does not change the schedule). Returns an async-cloud `event_id`.

```bash
forge inspection task execute --task-id 12
```

Output: `{ "ok": true, "id": 12, "event_id": "<event>" }`. The inspection then runs asynchronously on the backend. This is a **Once** run: it records findings without triggering automatic kill or inheriting the scheduled run's consecutive-hit streak. An `event_id` confirms submission, not completion; check `scheduler-job list` for the batch and `hit-item list` for its findings.

### Alert config (task_config alert blocks)

`task_config` carries two alert blocks (`task_alert_config` and `model_alert_config`), passed through untouched by the CLI. They mirror the console's "通知配置" step; only the fields below are user-set (others exist in the IDL but the console never exposes them, so leave them unset).

`task_alert_config` — task-level notifications:

| Field | Console label | Type | Meaning |
|---|---|---|---|
| `alert_switch` | 通知开关 | bool | master toggle for task notifications |
| `alert_users` | 通知接受人 | list&lt;string&gt; | SSO usernames to notify |
| `alert_lark_groups` | 通知接受群 | list&lt;string&gt; | Lark group chat ids to notify |
| `invite_user_to_group` | 拉 owner 进群 | bool | pull the model owner into the notify group |

`model_alert_config` — per-model owner alerting and auto-kill:

| Field | Console label | Type | Meaning |
|---|---|---|---|
| `alert_switch` | 是否通知模型 Owner | bool | notify the model owner |
| `alarm_methods` | 报警方式 | string | `""` = Feishu + @user; `"alertUrge"` = Feishu urgent |
| `kill_threshold` | 强杀任务阈值 | int (≥1) | consecutive-hit count that triggers auto-kill |
| `kill_progress_exemption_threshold` | 训练进度豁免阈值 | int (0–100) | positive values skip kill when training progress ≥ this %; **0 disables** progress exemption (utilization-OLAP batching jobs only) |

Do **not** hand-write `kill_whitelist` / `kill_user_whitelist` here — those are managed through `forge inspection kill-whitelist` ([inspection_whitelist.md](inspection_whitelist.md)). Creation strips legacy embedded lists; updates reject changes to them when the migration guard is enabled. Copying an old task does not copy its exemptions. `alarm_level` and `duty_name_list` are not exposed by the console; leave them unset.

Automatic kill is supported only for `low-utilization-rate-olap` and `cleanable-streaming-job`, on scheduled Loop runs with `model_alert_config.alert_switch=true` and a positive `kill_threshold`. A hit or `decision=action-required` alone does **not** prove a kill succeeded: inspect the hit item's `action_status`. Whitelist exemptions reset the consecutive-hit streak; once protection expires, qualifying scheduled hits accumulate again. Continuity also depends on the previous successful, contiguous Loop batch and an unchanged rule snapshot. Training-progress exemption is evaluated for batching jobs in the OLAP rule.

---

## Run history: scheduler-job list (执行记录)

Each scheduled or manual run of a task is a "schedule job". List batches and their summary counters here; use `hit-item list/get` below for individual findings and action outcomes:

```bash
forge inspection scheduler-job list --task-id 12
forge inspection scheduler-job list --status failed \
  --start-time 2026-07-01T00:00:00+08:00 --end-time 2026-07-02T00:00:00+08:00
forge inspection scheduler-job list --scheduler-job-id 99
```

| Flag | Notes |
|---|---|
| `--task-id` | Filter to one inspection task's runs |
| `--task-name` | Exact task name |
| `--status` | `running` / `success` / `failed` |
| `--scheduler-job-id` | Exact scheduler job id (`--job-id` is a deprecated compatibility alias) |
| `--start-time`, `--end-time` | Schedule-time window (ISO-8601 with offset, e.g. `2026-07-01T00:00:00+08:00`) |
| `--page`, `--page-size`, `--order-by`, `--order` | Pagination / sort |

Output has `total`, `page`, `page_size`, and `runs`. Each run carries `id`, `task_id`, `task_name`, `status` (label) + `status_code`, `schedule_time`, and `schedule_mode` (`once` / `loop`). The following nullable summary fields retain **null versus zero**:

| Field | Meaning |
|---|---|
| `checked_count` | Checked population; `null` means historical batch or unavailable summary |
| `hit_item_count` | Number of structured hit items |
| `action_count` | Number of actions with status `succeeded`, not candidates or attempted actions |
| `exempted_count` | Number of exempted decisions |
| `action_failed_count` | Number of failed actions |
| `action_unknown_count` | Number of actions whose outcome is unknown |
| `result_degraded` | Backend reports degraded/incomplete results; `null` means unknown |

Never translate missing counters into zero or assume `status=success` means every action succeeded. When `checked_count` is null, describe the summary as unavailable. When `result_degraded=true`, explicitly state the result is incomplete. `false` describes the backend's quality marker, not proof that every target was checked. `job_result` is retained for compatibility with older deployments; the current backend returns only a bounded legacy summary and log id for historical batches, and omits raw per-object result maps. Do not infer “no hits” from an empty `job_result`. There is no per-id batch endpoint; filter this list by `--scheduler-job-id` instead.

## Hit evidence and action outcomes: hit-item list/get

Use these read-only commands for “为什么被巡检杀了”, “为什么命中但没杀”, “巡检命中明细”, and “豁免原因”. Query the same `--site` as the inspection rule or training job. Backend rollout is required on that site; do not silently fall back to another site if the API is unavailable.

```bash
# Findings for a training job (explicit time range, up to 31 days)
forge inspection hit-item list --job-id 123456 \
  --start-time 2026-09-01T00:00:00+08:00 --end-time 2026-09-02T00:00:00+08:00

# Findings in one execution batch; time bounds are still required
forge inspection hit-item list --scheduler-job-id 99 --decision exempted \
  --start-time 2026-09-01T00:00:00Z --end-time 2026-09-02T00:00:00Z

# Follow inspection_item_id from a kill reason; no time bounds needed
forge inspection hit-item get --item-id 987
```

| Flag on `list` | Meaning |
|---|---|
| `--start-time`, `--end-time` | Required inclusive bounds on hit time, RFC3339 with offset or Unix **milliseconds**; start ≤ end; at most 31 days; sent as normalized UTC RFC3339 |
| `--task-id` | Inspection rule id (wire `rule_id`) |
| `--scheduler-job-id` | Execution batch id (wire `inspection_batch_id`) |
| `--job-id` | **Training job** id (wire `train_job_id`); differs from scheduler-job's deprecated `--job-id` alias |
| `--owner`, `--mine` | Exact training job owner / current authenticated user; mutually exclusive; not the rule creator |
| `--target-type` | `job`, `model`, `resource-group`, or `payoff-unit` |
| `--target-key` | Exact target key; combine with type to disambiguate |
| `--decision` | `recorded`, `exempted`, `safety-blocked`, `action-required` |
| `--action-status` | `not-requested`, `pending`, `succeeded`, `failed`, `unknown` |
| `--page`, `--page-size` | Defaults 1 / 20; positive page; page size 1–100 |

Filters combine by AND; without owner filters the list is not silently scoped to the caller. Paginate using `total` and the requested page size. An empty list means no structured records matched the query, not proof there were no historical hits.

`list` returns `{ok,total,page,page_size,items}`; `get --item-id` returns `{ok,item}`. Each item preserves the API's `inspection_batch_id`, `rule_id`, optional `train_job_id`, target identity, rule name/owner/update time, evidence (`metric_name`, actual value, threshold, aggregation, observation window/time), consecutive hit count/required count, progress and whitelist exemption flags, `notification_muted`, decision reason, action status/timestamps/failure reason, resource group, and log id. Optional values remain null when unavailable. `target_type` keeps the API's native `resource_group` / `payoff_unit` spellings in JSON. Inspection rule type, decision, and action status have readable labels plus separate `*_code` fields; unknown future enums remain `unknown:<code>`. Show `inspection_job_type_desc` for the rule type in user summaries. Progress values and thresholds are fractions (0–1).

Report `decision` separately from `action_status`: a candidate may be blocked or fail later. `unknown` means the outcome cannot be determined; do not report success or automatically retry a kill. These commands only read history.

---

## Discovering valid values (targets, roles, GPU types)

Filling `--inspection-target` and the filter fields needs concrete names. These read-only commands mirror the console's dropdowns.

### Targets — `forge inspection target list --task-type <t> [--keyword]`

One task-type-aware command; it mirrors the console's target picker for each task type:

| `--task-type` | Lists | Notes |
|---|---|---|
| `psm` | PSMs | supports `--keyword` fuzzy matching and `--limit` |
| `resource` | resource groups | supports `--keyword`; caps at ~1000 |
| `online-ps` | Online PS clusters | `--idc` to scope; lists the default IDC when empty |
| `bu` | BUs | supports `--keyword`; caps at ~1000 |
| `payoff-unit` | payoff units (结算单元) | supports `--keyword`; caps at ~1000 |

```bash
forge inspection target list --task-type resource --keyword aml
forge inspection target list --task-type psm --keyword search_
forge inspection target list --task-type bu --keyword search
forge inspection target list --task-type payoff-unit
```

Output: `{ ok, task_type, total, targets:[...] }` (deduped, sorted). A `resource`, `bu`, or `payoff-unit` listing caps at ~1000 values and a `psm` listing at `--limit`; when more match, the output sets `truncated: true` — do not treat the result as complete, and narrow it with `--keyword`.

> This command is a value picker for an inspection task's `--inspection-target`. It is **not** the general "list billing units / resource groups" tool: for "有哪些结算单元 / 结算单元列表" use `forge quota payoff-unit list` (returns id, admins, priority, …), and for "有哪些资源组 / 资源组列表" use `forge quota resource-group list` (returns `payoff_unit_name` / `admins` / `members`). Only use `target list --task-type bu|payoff-unit|resource` when you are actually filling an inspection task's target argument.

### Roles — `forge inspection role list [--keyword]`

Lists roles seen in the last 5 minutes — the values for the `role` filter in a utilization rule. The lookback is fixed to match the Forge console. This command discovers current dropdown values; historical role lookup is not supported.

### GPU types — `forge inspection gpu-type list`

Lists GPU card types as `{ key, accelerator, label }`; `key` is the value for the `gpu_type` filter in a utilization rule (e.g. `{"field":"gpu_type","operator":"=","value":"<key>"}`).
