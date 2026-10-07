# serving.md — deployment inspection, dense snapshots, Serving Haven versions, deployment lifecycle, and OnlinePS

Use this reference when an agent needs to list, inspect, create, get, update, start, or stop ModelHub / MaaS serving deployments, or start/stop OnlinePS.
For install / auth / runtime basics see [invocation.md](invocation.md).
For root-cause analysis of distribution failure / status discrepancy, read [serving_diagnosis.md](serving_diagnosis.md).

---

## What this command is for

`forge serving model get` is a **read-only serving inspection** command.

`forge serving deployment create|get|list|update|start|stop` are the unified
**ModelHub / MaaS serving deployment** commands. Selectors identify the target
kind; users do not pass a provider flag.

`forge serving online-ps start|stop` are **OnlinePS lifecycle** commands.

`forge serving haven-version list|get|create|update` manages versioned model
records in Haven's `serving` cluster.

`forge serving dense-snapshot list|update` inspects deployment dense snapshots
and manages the current time-selected pin set.

Use it for:

- listing MaaS jobs in one business unit or ModelHub deployments for one PSM
- listing which serving deployments / PSMs exist for one model
- inspecting one concrete `model_name + psm` deployment
- creating or inspecting a MaaS job before its PSM exists
- updating MaaS capacity, package, snapshot, latency, dump, or runtime configuration
- enabling runtime for an existing offline MaaS job
- starting MaaS with its mandatory online precheck, and checking push-online progress
- checking serving-side health, instance counts, and MaaS presence
- listing dense snapshots and pinning the backend-selected snapshot set at or before a baseline time
- starting or stopping OnlinePS by `--model-name` or `--job-id`

## Dense snapshot pinning

```bash
forge serving dense-snapshot list --deployment-id 442016 --site cn
forge serving dense-snapshot update --deployment-id 442016 \
  --pin-before '2026-09-04T12:00:00+08:00' --dry-run --site cn
forge serving dense-snapshot update --deployment-id 442016 --unpin --yes --site cn
```

`--pin-before` accepts Unix seconds or RFC3339 with an explicit timezone. An
ordinary deployment selects one snapshot; a MaaS runtime deployment selects one
snapshot per `(card type, runtime env)` group. The CLI deliberately requests one
candidate per group, submits the complete set in one operation, and does not
expose a runtime/card selector. Review the selected set with `--dry-run`, then
rerun and confirm or pass `--yes`.

Read-only `dense-snapshot list` may use a ModelHub selector for the downstream
deployment. For an exact `pilot_gpu.*` PSM, mutations must use
`--maas-job-id` or `--model-name + --biz-unit`; do not use `--deployment-id` or
`--model-name + --psm` to mutate a MaaS-managed deployment.
When MaaS has assigned the model and PSM but its downstream deployment has not
registered yet, list succeeds with an empty catalog and
`target.deployment_id=null`; this is a pending-registration state, not a query
failure.

After a mutation, treat `post_write_verified=false` as submitted but not yet
confirmed: run `dense-snapshot list` and do not claim the final pin state or
retry automatically. If the command returns `error.type=outcome_unknown`, do
not retry; first run the indicated `dense-snapshot list` command and reconcile
`state.pinned_dense_snapshots`.

Do **not** use it for:

- training job diagnosis / logs / metrics → read [job.md](job.md)
- distribution-failure root cause or rollout-readiness interpretation → read [serving_diagnosis.md](serving_diagnosis.md)
- mutating a MaaS-managed `pilot_gpu.*` PSM through the ModelHub selector → select the MaaS job with `--maas-job-id` or `--model-name + --biz-unit`; read-only `deployment get` may still inspect its downstream ModelHub deployment
- applying for MaaS online/offline approval → not supported by the current CLI

---

## Serving profiling artifacts

List pre-collected profiling archives for one model and PSM:

```bash
forge serving profiling-artifact list \
  --model-name <model-name> \
  --psm <psm> \
  --site <site>
```

Both selectors are required. The read-only result exposes `profile_tos_path`
as the opaque `artifact_url`; normal `--site` routing supports all four control
planes. If the URL is reachable, users may download it themselves:

```bash
curl -fL -O '<artifact_url>'
wget '<artifact_url>'
```

List success does not prove URL reachability. Do not probe or rewrite URLs to
bypass EU-TTP / US-TTP restrictions. Do not invent `get`; it requires a stable
backend `profile_id` and compliant regional transport.

---

## Serving Haven versions

Serving Haven versions are distinct from Forge code versions, model commits,
compile artifacts, and serving deployment versions. The command resolves an
exact Forge model and its IDC, then fixes the Haven cluster to `serving`; users
do not pass `--cluster` or raw Haven infrastructure identifiers.

### List or inspect

```bash
forge serving haven-version list --model-name <model-name>
forge serving haven-version get --model-name <model-name> --version <haven-version>
```

The list output includes explicit `state.latest_haven_version`,
`state.pinned_haven_version`, metadata, and file manifests. `get` returns one
version and its manifest. The current CLI intentionally does not preview or
download Haven file contents; cross-region file access needs a separate
compliance-aware design.

For Lite records, preserve the Haven metadata values exactly under
`metas.model_type`, `metas.framework_version`,
`metas.tf_saved_model_hdfs_path`, and `metas.tf_saved_model_version`.
`metas.model_type` may be `tf`; it is Haven metadata and must not be rewritten
to the Forge framework label `lite`.

### Create a new Serving Haven version

This creates a serving model-graph version from a successfully built Forge
model commit.

```bash
forge serving haven-version create --model-name <model-name> \
  --from-model-commit-id <model-commit-id> --dry-run

forge serving haven-version create --model-name <model-name> \
  --from-model-commit-id <model-commit-id> --yes
```

The CLI validates a successfully built Forge model commit, previews the source,
target, and current pin state, rejects stale state, then creates a new Serving
Haven version. Serving create does not accept `--reapply`.

The CLI does not restrict graph replacement by framework. Actual create support
depends on whether the selected commit has a compatible compiled artifact.
History, manifest, and pin operations remain available independently.

Activation boundary:

- Creating the version does not prove serving instances loaded it.
- Normal activation may wait for a later dump/reload. Use deployment/instance
  evidence before claiming the new graph is live.
- If output has `post_write_verified=false`, the create request returned
  success but the immediate history refresh did not expose the new version.
  Do not resubmit automatically.
- If the create request may have reached the service but no definitive result
  is available, the CLI returns `error.type=outcome_unknown`; run the indicated
  `haven-version list`, inspect `metas.source_commit_id`, and do not resubmit
  automatically.
- Serving Haven graph replacement records source commit metadata in Haven but
  does not rewrite the training job's global model commit.

### Pin or unpin

```bash
forge serving haven-version update --model-name <model-name> \
  --pin-version <haven-version> --dry-run

forge serving haven-version update --model-name <model-name> --unpin --yes
```

This pins the entire model version in Serving Haven. It is **not** Dense
Snapshot Pinning: a Dense Snapshot is scoped to one Serving deployment/job and
must remain under deployment semantics rather than `haven-version`.
Forge authorizes pin/unpin for the supported model owners and administrators;
report any returned permission error without retrying under another identity.
If an update returns `error.type=outcome_unknown`, inspect
`state.pinned_haven_version` with `haven-version list` before deciding whether
to retry.

---

## Query strategy for agents

`serving model get` answers **serving-side deployment state**.
`model_info` is attached training-side context.
The command is **workspace-agnostic**: it does **not** read `.forge/forge_meta.json`.

### Strategy A — user provides `model_name` only

```bash
forge serving model get --model-name <model_name>
```

### Strategy B — user provides `model_name + psm`

```bash
forge serving model get --model-name <model_name> --psm <service_psm>
```

### Strategy C — user asks about “某个部署” but does not provide PSM

Do **not** guess the PSM.

1. Run list mode first.
2. If `list.deployments` is empty → report no matching serving deployment.
3. If there are multiple deployments → present candidate PSMs; do not choose one arbitrarily.
4. If there is exactly one deployment and the user clearly wants detail → continue with that unique PSM.

One concrete deployment relationship is identified by **`model_name + psm`**.

---

## Deployment commands

### List deployments

Choose exactly one collection view; the command never merges them:

```bash
forge serving deployment list --biz-unit <bu>
forge serving deployment list --psm <psm>
forge serving deployment list --psm <psm> --state created,stopped --page 2 --page-size 20
```

`--biz-unit` queries MaaS jobs. Its raw filter states are
`offline,start,online,stop`, with `start,online` used when `--state` is omitted.
`--psm` queries ModelHub deployment rows. Its raw filter states are
`created,todo,started,healthy,stopped`, with `todo,started,healthy` used when
`--state` is omitted. `--state` may be repeated or comma-separated. Page
numbers are 1-based, `--page-size` defaults to 20, and its maximum is 100.

The PSM backend may return `partial_ready` after read-time health recalibration
even though that value cannot be selected with `--state`. `failed` is neither
a supported filter nor an expected list result. Preserve returned states as
raw values; do not translate them into a second lifecycle vocabulary.

The selected view is authoritative. A PSM result may represent a downstream
deployment created by MaaS, but the CLI does not query Prifly to add its BU or
MaaS job ID. Use `--biz-unit` when the user needs the MaaS job view. The compact
item shape is `deployment_id`, `maas_job_id`, `model_name`, `biz_unit`, `psm`,
`state`, and `owner`; non-applicable identities are `null`. It intentionally
omits provider, deploy type, IDC, framework, framework version, and
architecture.

### Resource selectors

Deployment lifecycle commands use one of four non-overlapping selectors:

| Resource | Selector |
|---|---|
| ModelHub deployment | `--deployment-id <id>` |
| ModelHub deployment | `--model-name <model> --psm <psm>` |
| MaaS job | `--maas-job-id <id>` |
| MaaS job | `--model-name <model> --biz-unit <bu>` |

`deployment_id` and `maas_job_id` are different IDs. A MaaS start may later
create a PSM and downstream ModelHub deployment, but that downstream ID never
replaces the MaaS job selector.

Selectors also define the read view. `deployment get --deployment-id` or
`--model-name + --psm` returns the ModelHub deployment even when MaaS created
that downstream deployment; it does not infer or fetch the MaaS job.

### Create a deployment

ModelHub:

```bash
forge serving deployment create --model-name <model_name> --psm <service_psm>
forge serving deployment create --job-id <job_id> --psm <service_psm>
forge serving deployment create --model-name <model_name> --psm <service_psm> --region sg --site i18n
```

MaaS:

```bash
forge serving deployment create --model-name <model_name> --biz-unit <bu>
forge serving deployment create --model-name <model_name> --biz-unit <bu> --use-runtime=false
```

Shared and ModelHub flags:

| Flag | Notes |
|---|---|
| `--model-name` / `--job-id` | Exactly one is required. MaaS currently requires `--model-name`; `--job-id` is ModelHub-only. |
| `--psm` / `--biz-unit` | Exactly one is required. `--psm` selects ModelHub; `--biz-unit` selects MaaS. |
| `--region` | ModelHub-only. Repeat or comma-separate to select a subset allowed by `--site`; when omitted, all regions mapped from the site are used. |
| `--deploy-cluster` | Required when the target service has `ctx.dispatch_by_cluster=true`; must be one of `ctx.deploy_clusters`. |
| `--baseline` | Required only when the target service has `ctx.enable_maas=true` (MaaS 1.0 service ctx); often the target model name. Do not pass it for non-MaaS services. |
| `--snapshot-config-file` | ModelHub-only. Path to a JSON object replacing `model_config.sail_config.snapshot_config`; valid for `sail` / `torch`, not `lite`. |
| `--start` | ModelHub-only. Start after create succeeds. MaaS create and start remain separate operations. |
| `--use-runtime` | MaaS-only, default `true`; non-Torch models may pass `--use-runtime=false`. Torch MaaS always requires runtime, so an explicit opt-out fails before create instead of being silently ignored. |

The CLI derives these fields; do not ask users to pass them manually:

- `model_type`: from `servable_models.framework`
- `idc`: from `servable_models.idc`
- `exclusive_dump`: true when `share_weights_from` is non-empty
- `regions`: defaults from `--site` (`cn` → `cn`, `i18n` → `sg,va`, `eu-ttp` → `eu,eu_ttp,eu_ttp2`, `us-ttp` → `ttp`); explicit `--region` values must be a subset of that mapping
- `deploy_type`: normal `0`; MaaS 1.0 baseline-only `22`; MaaS 1.0 baseline + deploy_cluster `21`

Framework-specific create rules:

- `sail`: send `model_type=sail`, use `sail_config`, `isTorch=false`
- `torch`: send `model_type=torch`, use `sail_config`, `isTorch=true`
- `lite`: send `model_type=lite`, use `lite_config`; do not pass snapshot config

MaaS create rules:

- The business identity is the unique `model_name + biz_unit` combination.
- Create uses the platform's available BU defaults. Inspect the returned config
  before updating it.
- Successful create returns `maas_job_id`, `state=offline`, and normally
  `psm=null`; the PSM becomes available during the online flow.
- Create-time config overrides and create-with-start are not supported. Create,
  inspect, then update or start the job.

### Get a deployment

```bash
forge serving deployment get --deployment-id <deployment_id>
forge serving deployment get --model-name <model_name> --psm <service_psm>
forge serving deployment get --maas-job-id <maas_job_id>
forge serving deployment get --model-name <model_name> --biz-unit <bu>
```

For MaaS jobs:

- `psm` is always present in the JSON shape and is `null` until MaaS creates it.
- `use_runtime` reports the current runtime switch and is independent from the
  runtime-environment list. If the switch lookup fails, `use_runtime=null`,
  `runtime_error` records that failure, and the CLI still attempts runtime
  enrichment.
- `maas_config.package_list` contains the MaaS package statuses.
- `maas_config.runtime_envs` is independently enriched and preserves each
  runtime ID, type, status, base runtime, SCM repos, optimizing-pass JSON
  string, extra-context JSON string, package, and template name.
- The CLI does not infer a package relation between `package_list[].package_name`
  and `runtime_envs[].package`; report both collections independently.
- When `use_runtime=false`, the CLI skips the runtime-environment request and
  returns `runtime_envs=[]`.
- A successful runtime lookup with no environments also returns
  `runtime_envs=[]`.
  A failed or resource-mismatched runtime-environment lookup keeps the MaaS
  job, returns `runtime_envs=null`, and sets a structured `runtime_error`. If
  both switch and environment enrichment fail, `runtime_error` includes both.
- While `state=start`, get also returns a normalized `progress` object
  containing stage, progress text, hold reason, solution, and a detail link.
- Progress is best-effort enrichment. If that auxiliary call fails, the command
  still returns the authoritative MaaS job and sets `progress=null` plus a
  structured `progress_error`; report both the lifecycle state and the fact
  that progress is temporarily unavailable. A successful envelope with missing
  `data` is also reported as `progress_error.code=INVALID_RESPONSE` rather than
  being mistaken for an empty successful progress result.
- `serving deployment get` is the lifecycle-resource view. `serving model get`
  remains the model-centric inventory and instance-health view.

For ModelHub jobs, `framework` is `sail`, `torch`, `lite`, or `null` when the
available deployment data cannot distinguish the training framework. Do not
treat serving model type `tf` as a training framework.

`modelhub_config` returns the complete editable deployment configuration:
`service_config`, raw `model_config`, raw `deploy_config`, and `deploy_type`.
The raw config objects preserve fields the CLI does not currently expose, so
they are the right source for understanding an older deployment before update.

MaaS lifecycle state interpretation:

| `state` | Meaning |
|---|---|
| `offline` | The MaaS job exists and is offline. A PSM may not exist yet. |
| `start` | The online operation has been submitted and is still progressing; inspect `progress` or `progress_error`. |
| `online` | The MaaS online flow completed. Use `serving model get --model-name ... --psm ...` only when instance health is needed. |
| `stop` | The offline operation has been submitted and is still progressing. |

Do not require a PSM to explain these MaaS job states. A concrete PSM is needed
only for ModelHub deployment and instance-health diagnosis.

When a MaaS-created downstream `deployment_id` or PSM is already known, the
ModelHub view remains directly queryable:

```bash
forge serving deployment get --deployment-id <downstream_deployment_id>
forge serving deployment get --model-name <model_name> --psm <maas_created_psm>
```

This returns `deployment_id` with `maas_job_id=null`. Use a MaaS selector when
the requested information is the MaaS lifecycle state, config, or progress.

### Update a deployment

ModelHub:

```bash
forge serving deployment update --deployment-id <deployment_id> <update flags>
forge serving deployment update --model-name <model_name> --psm <psm> <update flags>
```

MaaS:

```bash
forge serving deployment update --maas-job-id <maas_job_id> <update flags>
forge serving deployment update --model-name <model_name> --biz-unit <bu> <update flags>
```

A real update requires either interactive `yes` confirmation or `--yes`.
Confirmation shows the selected resource and requested fields; it confirms
mutation intent rather than a frozen server-state preview. The update validates
the current state, preserves unexposed config fields, and applies only the
requested changes.

`FORBIDDEN` means the current account cannot modify the selected resource; use
an authorized owner/admin account or ask the resource owner to perform it.

`--dry-run` skips confirmation, performs the same provider
read/validation/patch flow, prints a structured before/after preview, and does
not apply the update. Preview/result output includes
`provider=modelhub|maas`, `mode=config|runtime`, and
`lifecycle_state`.

`--dry-run` and the later real update are independent invocations. Rerunning
with `--yes` re-evaluates the current state and current local file contents; it
does not apply a frozen dry-run snapshot.

Recommended ModelHub workflow:

```bash
forge serving deployment get --deployment-id <id>
forge serving deployment update --deployment-id <id> \
  --snapshot-config-file snapshot.json --dry-run
forge serving deployment update --deployment-id <id> \
  --snapshot-config-file snapshot.json --yes
```

ModelHub update currently supports only `--snapshot-config-file` and
`--dump-extra-args`, while preserving other config fields. Snapshot config is
rejected for Lite deployments. On an update error, run `deployment get` before
retrying.

Recommended MaaS update workflow:

```bash
forge serving deployment get --model-name <model> --biz-unit <bu>
forge serving deployment update --model-name <model> --biz-unit <bu> \
  --max-capacity-pct 0.9 --dry-run
forge serving deployment update --model-name <model> --biz-unit <bu> \
  --max-capacity-pct 0.9 --yes
```

MaaS create does not accept `snapshot_config` or `dump_extra_args` overrides.
Create first, inspect the generated config, then update.

State-based update rules:

| MaaS state | Allowed changes |
|---|---|
| `offline` | MaaS config fields, existing-package switches, runtime enable, or one existing runtime environment |
| `start` / `online` / `stop` | `--max-capacity-pct` and `--preferred-package` only |
| any unknown state | fail closed; do not update |

Here `offline` is the MaaS lifecycle state, not the CLI runtime network
`--network office|prod`.

Enable runtime after create as part of config mode:

```bash
forge serving deployment update \
  --maas-job-id <id> \
  --use-runtime \
  --package age2.1x-nvidia.l20.64g.1x=online \
  --dry-run
```

`--use-runtime` is enable-only. In `state=offline`, it may accompany MaaS
config and package changes, but cannot accompany `--runtime-*` edits. Runtime
cannot be disabled after create.

Config mode supports:

```bash
forge serving deployment update \
  --maas-job-id <id> \
  --max-capacity-pct 0.9 \
  --preferred-package age2.1x-nvidia.l20.64g.1x \
  --dry-run

forge serving deployment update \
  --maas-job-id <id> \
  --package age2.1x-nvidia.l20.64g.1x=online \
  --package age2.4x-nvidia.l20.64g.4x=offline \
  --max-latency 80 \
  --dump-extra-args='...' \
  --snapshot-config-file snapshot.json \
  --yes
```

Config flags:

| Flag | Rule |
|---|---|
| `--max-capacity-pct` | Must be between `0.6` and `0.95` inclusive; hot-update allowed. |
| `--preferred-package` | Exact package name used for preferred scale-out scheduling; it must exist and be `online`. Pass an empty value to clear. Hot-update allowed. |
| `--max-latency` | Positive integer. |
| `--dump-extra-args` | Replaces the string; pass an empty value to clear. |
| `--snapshot-config-file` | Replaces `snapshot_config` from a JSON object. |
| `--package <name>=online|offline` | Toggles an existing package; repeat it or comma-separate entries. Unknown package names fail instead of implying package creation. |

The CLI preserves unexposed MaaS config fields while applying the requested
changes. If an update fails, fetch the MaaS job before retrying because the
final package state may be uncertain.

For `snapshot_config`, dry-run and the submitted request preserve the exact
validated JSON object supplied by the user, including number literals.
Accepted outer fields are `switch`, `snapshot_psm`, `optimization_passes`, and
`byted_tf_opt_snapshot_config`; unknown outer fields are rejected.

`--snapshot-config-file` expects that outer object, not a bare Byted TF Opt
payload. On a bare object, follow the CLI's wrapper hint; do not infer the
snapshot PSM or require `byted_tf_opt_snapshot_config` keys to match
`snapshot_psm`. Fine-grained arbitrary-key deletion is not exposed.

Runtime mode is mutually exclusive with config mode and edits one existing
runtime environment. It does not create or delete runtime environments:

```bash
forge serving deployment update \
  --maas-job-id <id> \
  --runtime-env-id 84559 \
  --runtime-scm erdos/inference/pilot_gpu=1.0.0.1574 \
  --runtime-scm-add data/aml/new_ops=1.0.0.8@/opt/tiger/new_ops \
  --runtime-scm-remove data/aml/old_ops \
  --yes

forge serving deployment update \
  --model-name <model_name> \
  --biz-unit <bu> \
  --runtime-package L \
  --runtime-template stable \
  --runtime-pass-config-file pass_config.json \
  --runtime-extra-context-file extra_context_patch.json \
  --yes
```

Runtime rules:

- Select exactly one runtime by `--runtime-env-id` or exact
  `--runtime-package`. A package selector that matches multiple runtimes fails;
  use the runtime ID instead.
- `--runtime-template` replaces base runtime, SCM repos, optimizing pass,
  extra context, and template name from the exact named template. A template
  whose package is empty or `*` applies to the selected concrete package; a
  different concrete package is rejected. The selected runtime's package is
  always preserved.
- `--runtime-pass-config-file` then replaces only `pass_config` inside the
  current/template `optimizing_pass` JSON object. It preserves SDK versions,
  `env`, checkers, and other top-level optimizing fields. The file may contain
  any non-null JSON value accepted as `pass_config`, normally an array.
- `--runtime-extra-context-file` recursively merges a JSON object into
  `extra_context`; untouched environment/config keys remain.
- `--runtime-scm <name>=<version>` updates an existing repo version while
  preserving its path.
- `--runtime-scm-add <name>=<version>@<path>` adds a new repo. Existing names
  must use `--runtime-scm`; duplicate or missing names fail rather than guess.
- `--runtime-scm-remove <name>` removes an existing repo by exact name.
  Repeat it to remove multiple repos. Missing or duplicate names fail rather
  than being silently ignored.
- Explicit runtime patches run after template replacement in remove, update,
  then add order. The same name may be removed and added in one command to
  replace its version/path; remove plus `--runtime-scm` for the same name is
  rejected.

Do not infer a direct mapping between `package_list` and `runtime_envs`.
Package changes may refresh the available runtimes, so `--package` and every
`--runtime-*` flag are mutually exclusive. Update packages first, run
`forge serving deployment get`, then edit one runtime from the refreshed
response.

Update output uses `mode=config|runtime`, `changed_fields`,
`before`, and `after`. `after` is the CLI-visible target projection, not a
second post-write read. Use `deployment get` when the final refreshed state is
required.

### Start / stop a deployment

ModelHub:

```bash
forge serving deployment start --deployment-id <deployment_id>
forge serving deployment stop --deployment-id <deployment_id> --yes
forge serving deployment start --model-name <model_name> --psm <service_psm>
forge serving deployment stop --model-name <model_name> --psm <service_psm> --yes
```

MaaS:

```bash
forge serving deployment start --maas-job-id <maas_job_id>
forge serving deployment stop --maas-job-id <maas_job_id> --yes
forge serving deployment start --model-name <model_name> --biz-unit <bu>
forge serving deployment stop --model-name <model_name> --biz-unit <bu> --yes
```

MaaS start sequence:

1. Resolve the selected MaaS job.
2. Require the current state to be `offline`; reject every other state before
   precheck or update.
3. Run the online precheck.
4. If `allow_online=false`, return a validation error whose `detail` preserves
   the full structured precheck and do not start.
5. If allowed, submit start. Warnings remain visible but do not override the
   allow decision.

The CLI does not expose a standalone read-only MaaS precheck command.
`deployment start` is a mutation: if precheck allows the operation, the same
command immediately submits start. When a user asks only to run or inspect the
precheck, explain that this is not currently supported and do not call
`deployment start`; run it only after the user explicitly asks to bring the
MaaS deployment online.

All ModelHub and MaaS stop operations are destructive and require typing
`yes`, or an explicit `--yes` for non-interactive automation. Selector
validation runs before the prompt. The CLI does not query traffic or add a
`--force` bypass. The operator must verify that traffic has been drained;
`--yes` confirms that decision.

MaaS stop requires the current state to be `start` or `online`, then calls
the stop operation. `offline`, `stop`, and unknown states are rejected before
the update. Stop does not run an offline precheck.

For mutation only, PSMs whose whitespace-trimmed, case-sensitive value starts
with the exact `pilot_gpu.` prefix are rejected through the ModelHub selector.
The CLI then requires the MaaS selector so start runs the MaaS precheck and
operation flow. Names such as `PILOT_GPU.*` and `data.pilot_gpu.*` do not match
this prefix rule.

TTP lifecycle behavior:

- For ModelHub selectors only, `serving deployment start` and ModelHub
  `serving deployment create --start` on `--site us-ttp` submit a ByteCycle
  approval instead of directly calling the normal start ops. The response
  includes `bytecycle.ticket_id` and `bytecycle.url`; approval completion
  triggers the actual start backend flow.
- MaaS start does not use ByteCycle on any site, including `us-ttp`. It follows
  the MaaS state check and online precheck above, then directly submits the
  MaaS start operation when allowed. MaaS lifecycle approval is not supported
  by the current CLI.
- `serving deployment stop` does not use ByteCycle and still calls the normal stop ops on all sites.

---

## OnlinePS lifecycle commands

### Start OnlinePS

Use one of:

```bash
forge serving online-ps start --model-name <model_name> --cluster <cluster> [--compress 0]
forge serving online-ps start --job-id <job_id> --cluster <cluster> [--compress 0]
forge serving online-ps start --job-id <job_id> --cluster <permodel_group> [--target-cluster <sub_cluster>] [--dump-path <checkpoint_path>]
```

Rules:

- `--model-name` / `--job-id`: exactly one is required; `--job-id` must resolve to exactly one servable model.
- `--cluster`: required; start currently accepts one cluster/group only. Top-level `list_clusters` entries are either PerModel cluster groups (`is_per_model=true`, e.g. `tag_predict`) or Original clusters (`is_per_model=false`); PerModel physical sub-clusters live in the group's nested `clusters` list.
- `--target-cluster`: optional pin to one physical sub-cluster inside the PerModel `--cluster` group (e.g. `du_kv_tag_160a` inside `tag_predict`); omit it to let OP2 pick automatically. It must be an allowed member of that group's nested `clusters` list, must differ from `--cluster`, and is rejected for Original clusters, `STABLE_PS`, and `us-ttp`. If the backend returns a flat list (group has no nested members), the pin fails instead of guessing.
- `--dump-path`: optional manual checkpoint (dump) path for PerModel push; omit it to use the latest dump. Rejected for streaming jobs (`on_need_streaming=true`, where the backend forces an immediate full dump), Original clusters, `STABLE_PS`, and `us-ttp`.
- `--compress`: string enum `0` through `6`, default `0`.
- The CLI runs `push_online_check`, rejects unavailable checkpoint/PS, and supports only `SYMBIOTIC_PS` and `STABLE_PS`.
- `SYMBIOTIC_PS` uses `symbiotic_push_online` and returns `symbiotic.online_job_id` for the backend online job id. The result always includes `target_cluster` and `dump_path`; each is `null` unless the matching flag was set.
- `STABLE_PS` uses `releases`. On `--site i18n` / `--site eu-ttp`, if `list_clusters` does not contain the requested cluster, the CLI tries elastic cluster groups and expands enabled children.
- On `--site us-ttp`, start submits a ByteCycle approval through `release_executions` instead of directly calling `symbiotic_push_online` or `releases`. The response includes `bytecycle.execution_id`, `bytecycle.execution_ttp_url`, and `bytecycle.execution_tx_url`; approval completion triggers the backend callback flow.

Compression labels:

| Value | Meaning |
|---|---|
| `0` | 集群默认压缩 |
| `1` | f16压缩（全局基线） |
| `2` | 8位量化压缩 qtz |
| `3` | qat压缩（不建议使用，无人维护） |
| `4` | lsqqat压缩（不建议使用，无人维护） |
| `5` | 自适应 qtz8 压缩（ps版本 ≥ 2.8.0.1） |
| `6` | f32压缩 |

### Stop OnlinePS

Use one of:

```bash
forge serving online-ps stop --model-name <model_name> --cluster <cluster> [--cluster <cluster>...] [--clean-job]
forge serving online-ps stop --job-id <job_id> --cluster <cluster> [--cluster <cluster>...] [--clean-job]
```

Rules:

- `--model-name` / `--job-id`: exactly one is required.
- `--cluster`: at least one is required; repeat the flag or pass comma-separated values (`--cluster c1,c2`).
- The CLI runs `offline_precheck` first. If any cluster is denied, it reports the denied clusters/reasons and does not call `unrelease`.
- `--clean-job` defaults to `false` and is passed through to `unrelease`.

State query remains read-side only:

```bash
forge serving model get --model-name <model_name>
```

Relevant read-side fields are `model_info.is_online_ps_released`, `model_info.online_ps_clusters`, and `model_info.training_ps_name`.

---

## Flags for `serving model get`

This table is scoped to the read-only inspection command. Deployment lifecycle commands use the action-specific flags documented above.

| Flag | Notes |
|---|---|
| `--model-name` | Required. The training-side model name. |
| `--psm` | Optional. Omit it to list deployments; pass it to inspect one concrete deployment. |
| `--network`, `--site` | Standard Forge runtime flags. Keep `--network office` unless the user explicitly needs prod. |

---

## Output contract

- List mode (`--psm` omitted): returns `model_info + list`
- Detail mode (`--psm` provided): returns `model_info + detail`
- Deployment lifecycle actions use action-specific stable JSON shapes. Common
  identity/state fields are `deployment_id`, `maas_job_id`, `model_name`,
  `biz_unit`, `psm`, and `state`; nullable common fields use `null` when not
  applicable.
- `deployment list` returns `total`, `page`, `page_size`, `count`, and a compact
  `deployments` array. Its state and selector semantics are defined in
  [List deployments](#list-deployments).
- `deployment create` additionally returns `framework`, `framework_version`,
  `started`, and optional `start_result`.
- `deployment get` is the enriched detail shape. It additionally returns
  `modelhub_config`, `maas_config`, `use_runtime`, `progress`,
  `progress_error`, and `runtime_error`; these fields are present and use
  `null` when not applicable or unavailable.
- `deployment start` / `stop` additionally return `action`, `result`, and
  `precheck`. `bytecycle` is optional and is emitted only for a ModelHub
  US-TTP start that submits ByteCycle.
- `deployment update` uses a mutation-specific preview/result shape:
  `provider`, `mode`, `changed`, `changed_fields`, `before`, and `after`.

| Area | Important fields | How to use |
|---|---|---|
| `model_info` | `framework`, `job_status`, `train_mode`, `deployment_count` | attached model background |
| `list.deployments[]` | `psm`, raw `status`, `from_maas` | discovery and coarse summary only |
| `detail.deployment` | `deployment_status`, raw `status`, `from_maas`, `config` | primary view for one concrete deployment |
| `detail.instance_list` | `total_instance_count`, `error_instance_count` | serving-side instance summary |

---

## Response-shaping rules for agents

Do **not** dump the full JSON by default unless the user explicitly asks for raw output.

### When answering a list-mode question

Prefer this order:

1. whether any deployment exists
2. total deployment count
3. each candidate PSM
4. each candidate's raw `status`
5. whether each candidate is MaaS

- In list mode, `status` is only the raw summary status for that deployment row.
- Do **not** treat list-mode `status` as equivalent to detail-mode `deployment_status`.
- If the user asks why a deployment is unhealthy, about rollout readiness, status discrepancy, or instance abnormality root cause, drill down to detail mode and then read [serving_diagnosis.md](serving_diagnosis.md).

### When answering a detail-mode question

Prefer this order:

1. `deployment_status`
2. `total_instance_count`
3. `error_instance_count`
4. MaaS / non-MaaS
5. config summary when asked

- Use `deployment_status` as the default user-facing health status in detail mode.
- Mention raw `status` mainly when the user is explicitly troubleshooting status discrepancy.
- Determine MaaS by `from_maas != nil`; do **not** infer MaaS from `deployment_status`.

---

## Failure handling rules for agents

### `model <name> not found`

- This means the CLI did not find an exact servable-model match for the requested `model_name`.
- Treat it as model lookup failure, not deployment lookup failure.

### `serving deployment not found`

- This means the model matched, but no concrete serving deployment was found for the requested detail lookup.
- Prefer **“未找到对应的 serving 部署”** or **“未找到该 model + psm 对应的 serving 部署关系”**.

### Empty instances

- `total_instance_count == 0` means the current response has no instances.
- Do **not** automatically conclude the deployment is failed.
- Use `deployment_status`, raw `status`, and the zero-instance fact together.
