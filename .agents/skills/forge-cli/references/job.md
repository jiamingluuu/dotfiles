# job.md — `forge job list`, `forge job create`, `forge job priority`, `forge job resource-group`, `forge job primus-crd`, `forge job kill`, profiling timeline and GPU memory snapshot artifacts, checkpoint management, owner transfer + job observability, Training Haven versions

Use this reference for listing, submitting, killing, changing priority or changing the resource group of Forge training jobs, managing Training Haven versions, running an exact-target RoW SDP container operation, viewing/diffing/updating Primus CRD config, transferring job owner, listing profiling timeline / GPU memory snapshot artifacts, listing / saving / deleting job checkpoints, and inspecting metadata, events, logs, training metrics (including CPU / GPU / memory utilization). For install / auth basics see [invocation.md](invocation.md).

For DeepInsight **evaluation** metrics (AUC / UAUC / NDCG …) see [deepinsight.md](deepinsight.md).
For Wandb / TensorBoard series (`scalar` / `histogram` / `image`) see [series.md](series.md).

All values written as `<...>` in command examples are placeholders. Replace
them with IDs and names returned by the target control plane; they are not
verified live sample resources.

---

## List jobs

List Forge training jobs. A bare list returns every visible job; use `--mine` for the current owner or an explicit actor/filter to narrow it.

```bash
forge job list
forge job list --mine
forge job list --owner <username>
forge job list --job-id <forge-job-id>
forge job list --job-id <forge-job-id>,<second-forge-job-id>
forge job list --status running --status killing --resource-group aml-forgeide
forge job list --resource-group ecom-k8s-highway --site cn
forge job list --owner <username> --page 2 --page-size 20
```

**This is the default tool for "查看某资源组所有任务 / 任务列表 / 有哪些任务".** `forge job list --resource-group <name>` returns **every job in that group — all owners and all statuses** (running / success / failed / killed …), paginated. Do **not** answer such a request with `forge quota task list`: that command only returns currently `running` + `queued` tasks (the quota-occupancy view) and silently omits finished / failed / killed jobs, so it under-reports "所有任务". Route to `forge quota task list` only when the user explicitly asks for 已分配 / 正在运行 / 排队中 tasks. See [quota.md](quota.md#task-list-running--queued-tasks).

Usage notes:

- `job list` is read-only and supports `cn`, `i18n`, `eu-ttp`, and `us-ttp`; pass `--site` when the target control plane is not the default.
- `--resource-group <name>` is group-wide: without `--mine` / `--owner` it lists jobs from all owners in the group. Add `--mine` for the current authenticated owner or `--owner <username>` for a named owner; the two are mutually exclusive.
- `--job-id` accepts positive IDs as one value, a comma-separated list, or a repeated flag.
- `--status` accepts repeated or comma-separated values from this whitelist: `running`, `streaming`, `success`, `failed`, `killing`, `killed`.
- `--display-status` is a deprecated compatibility alias; do not generate it in new commands or automation.
- Pagination is 1-based: `--page` defaults to `1`, `--page-size` defaults to `20`.
- Output includes `jobs` entries with job id, owner, model name, project/version info, model and Norbert commit ids, display resource group, display status, backend status, and framework fields.
- Each `jobs` entry also carries `links.forge2`, the Forge2 job page. Treat `links.*` as opaque command output — do not hand-build a job URL from `job_id`.

---

## Create a job

Create a Forge job from the selected workspace by default. It reuses staged artifacts in `.forge/forge_meta.json`. Outside a workspace, both model and norbert commit IDs are required.
Shared-weights jobs use the same `forge job create` command with `--share-weights-from`; they create an only-register/no-train job from a parent model name and require only the model commit ID.

```bash
cd ./workdir
forge job create

forge job create --resource-group <resource-group>

forge job create --resource-group <resource-group> --job-name <job-name>

forge job create --resource-group <resource-group> --model-type <model-type-name>

forge job model-type list --site <site>

forge job create \
  --resource-group <resource-group> \
  --job-name <job-name> \
  --model-commit-id 123456 \
  --norbert-commit-id 123455

# Shared-weights only-register/no-train job
forge job create \
  --share-weights-from <parent-model-name> \
  --model-commit-id 123456 \
  --model-type <model-type-name> \
  --job-name <job-name>

# Optional resource group override for shared-weights creation; when omitted,
# the CLI omits resource_group and backend falls back to the parent job's group.
forge job create \
  --share-weights-from <parent-model-name> \
  --model-commit-id 123456 \
  --resource-group <resource-group>

# Dry-run: validate request assembly without submitting
forge job create --resource-group <resource-group> --dry-run
```

Useful flags:

| Flag | Description |
|---|---|
| `--resource-group` | Optional resource group passed to `create_norbert`; prompts when omitted |
| `--job-name` | Optional job name override passed to `create_norbert`; defaults to a generated `<project>_v<version>` name |
| `--model-type` | Optional Universal Model Type label for normal or shared-weights creation; CLI resolves it through the existing site catalog |
| `--model-commit-id` | Optional explicit model commit override in a workspace; required with `--norbert-commit-id` outside a workspace |
| `--norbert-commit-id` | Optional explicit norbert commit override in a workspace; required with `--model-commit-id` outside a workspace |
| `--share-weights-from` | Parent model name (`training_haven_key`) for shared-weights only-register/no-train job creation; requires `--model-commit-id` and does not use `--norbert-commit-id` |
| `--dry-run` | Validate local request assembly and print the final backend create request without submitting; for normal jobs, it does not prove the backend will accept the resource group without `--model-type` |

## Update a job's Norbert commit

Use this when an existing training job should switch to a different Norbert commit, update its preload-model checkpoint config, or both.

```bash
forge job norbert-commit update \
  --job-id <job-id> \
  --norbert-commit-id <norbert-commit-id>

forge job norbert-commit update \
  --job-id <job-id> \
  --norbert-commit-id <norbert-commit-id> \
  --model-checkpoint hdfs://path/to/checkpoint \
  --training-instance-time 2026-06-20T10:00:00 \
  --comment "preload model"

# Non-interactive automation after the caller has accepted the risk
forge job norbert-commit update \
  --job-id <job-id> \
  --norbert-commit-id <norbert-commit-id> \
  --yes
```

Rules:

- `--job-id` and `--norbert-commit-id` are required. Preload-model fields are
  optional add-ons to the same update request.
- The CLI validates that `--norbert-commit-id` points to a `code_type=norbert` commit when commit metadata includes `code_type`.
- `--model-checkpoint` maps to the web form's "模型Checkpoint" field and must be a backend `backup_path`, for example `hdfs://...`. `model_name@training_instance_time` is not supported because the backend update path only forwards model config when `backup_path` is present.
- `--training-instance-time` maps to `model.training_instance_time`. It is optional, but when provided it must be sent together with `--model-checkpoint`.
- Updates follow the web "更新任务配置" path and submit `is_pseudo=true`, so they participate in the backend in-progress lock. Commit-only updates send an empty `model` object; supplying preload-model fields populates `model`.
- `owner`, `idc`, and the previous Norbert commit are inferred from job detail. If backend job detail omits owner or IDC, pass `--owner` or `--idc`; the CLI does not guess IDC from `--site` for existing jobs.
- `first_commit` is the backend rollback-to-initial-version switch, not an "old commit exists" marker. The CLI sends it as `false`; do not set rollback semantics without an explicit user-facing flag.
- Before calling `update_train_norbert`, the CLI attempts to show the Forge commit diff from the job's current Norbert commit to the target `--norbert-commit-id` and requires manual confirmation by typing exactly `yes`. If the diff cannot be built, it prints a skipped-preview reason and still lets the user confirm the update.
- `--yes` skips the interactive confirmation for non-interactive automation, but the command still prints the diff or skipped-preview reason before submitting. Agents must not add `--yes` unless the user explicitly requested non-interactive submission or already accepted the update risk.
- The update call re-reads job detail after the diff preview; if the job's current Norbert commit changed after preview, the CLI rejects the update and requires rerunning the command to review the latest diff.
- The command returns the backend audit object when present.

## List Norbert commit update history

Use this to inspect the update history shown in the web "Update Job Config" history table.

```bash
forge job norbert-commit list --job-id <job-id>
forge job norbert-commit list --job-id <job-id> --page 2 --page-size 20 --order asc
```

Rules:

- `--job-id` is required. There is no current-job fallback.
- The audit-history `region` follows `--site`: `cn -> cn`, `i18n -> i18n`, `us-ttp -> ttp`, `eu-ttp -> eu`.
- Pagination is 1-based. Defaults: `--page 1`, `--page-size 10`.
- `--order` controls operation time order and accepts `desc` (default) or `asc`.
- Output includes `history` entries with operation time, operator, status, target owner, parsed `norbert_commit_id`, parsed preload-model checkpoint fields (`backup_path`, `training_instance_time`, `model_name`, `job_id`), and comment.
- If an old backend record contains unparseable context, the CLI preserves it as `raw_context` instead of failing the whole list.

## Training Haven versions

Training Haven versions are the versioned model records stored in Haven's
`training` cluster. They are different from Forge code versions, model commits,
compile artifacts, checkpoints, and Norbert commits.

The command uses `--job-id` only as an entrypoint. It resolves the authoritative
Training Haven model name and IDC from the exact Forge model record. Haven
mutations are model-scoped and may affect other consumers of that model; they
are not limited to one job merely because the selector is a job ID.

### List history

```bash
forge job haven-version list --job-id <job-id>
```

Output includes:

- `selector.job_id`: the requested job
- `target.haven_model_name`, `target.haven_cluster=training`, and `target.idc`
- `state.latest_haven_version` and `state.pinned_haven_version`
- newest-first `haven_versions[]`, each with metadata and a file manifest

Known Lite metadata remains visible as `metas.model_type`,
`metas.framework_version`, `metas.tf_saved_model_hdfs_path`, and
`metas.tf_saved_model_version`. `metas.model_type` may be `tf`; preserve that
Haven value instead of rewriting it to the Forge framework label `lite`.

### Get one version

```bash
forge job haven-version get --job-id <job-id> --version <haven-version>
```

`get` returns the selected version metadata and its `files[]` manifest. The
current CLI intentionally does not preview or download Haven file contents.
Cross-region file access needs a separate compliance-aware design before it is
exposed.

### Create a new Training Haven version

This creates a model-graph version from a successfully built Forge model
commit.

```bash
forge job haven-version create --job-id <job-id> \
  --from-model-commit-id <model-commit-id> --dry-run

forge job haven-version create --job-id <job-id> \
  --from-model-commit-id <model-commit-id> --yes

forge job haven-version create --job-id <job-id> \
  --from-model-commit-id <model-commit-id> --reapply --yes
```

`create` validates that the source is a successfully built Forge model commit,
prints the resolved target/current pin/source commit preview, and creates a new
Training Haven version. `--dry-run` never mutates. Ordinary execution requires
typing `yes` or passing `--yes`.

The CLI does not restrict graph replacement by framework. Actual create support
depends on whether the selected commit has a compatible compiled artifact.
History, manifest, and pin operations remain available independently.

Important activation boundary:

- A successful Training Haven `create` creates the Haven version and
  synchronizes the training-side model commit metadata. It does not by itself
  make a running job load the new graph.
- `--reapply` is supported only by Training Haven create. It previews the
  current Norbert commit, rejects a pinned Training Haven, creates the new
  version, verifies that the newest history record carries this operation's
  `source_commit_id`, re-checks the Norbert commit for staleness, and submits an
  asynchronous reapply of that same commit.
- Historical Haven versions may omit source provenance. A newly created version
  records `source_commit_id`. List/get remain compatible with historical
  versions, while `create --reapply` verifies the newly created version through
  `source_commit_id`.
- `reapply_status=submitted` means only that the asynchronous update was
  submitted; it does not prove that the restart completed or that the graph is
  already active.
- `forge job norbert-commit update` does not expose a standalone `--reapply`.

Without `--reapply`, a successful write remains success even when Haven history
has not refreshed immediately; output uses `post_write_verified=false`. With
`--reapply`, failure to verify the new version prevents the second write and
returns `error.type=partial_success`: Haven creation has already succeeded, so
do not rerun create.

If Haven creation succeeds but the reapply is definitively rejected before
submission, the same `partial_success` result sets
`reapply_status=not_submitted` and leaves any follow-up
`norbert-commit update --norbert-commit-id <commit>` decision to the user. If
the reapply submission has no definitive result, it sets
`reapply_status=outcome_unknown`; inspect `norbert-commit list` and do not
automatically retry either write.

If the create request may have reached the service but no definitive result is
available, the CLI returns
`error.type=outcome_unknown`; follow its `haven-version list` hint and inspect
`metas.source_commit_id` before deciding whether to retry.

### Pin or unpin the Training Haven version

```bash
forge job haven-version update --job-id <job-id> \
  --pin-version <haven-version> --dry-run

forge job haven-version update --job-id <job-id> --unpin --yes
```

- Exactly one of `--pin-version` or `--unpin` is required.
- The CLI previews model-scoped before/after state, then rechecks the target and
  history before writing.
- Forge authorizes pin/unpin for the supported model owners and administrators;
  report any returned permission error without retrying under another identity.
- If an update returns `error.type=outcome_unknown`, inspect
  `state.pinned_haven_version` with `haven-version list` before deciding whether
  to retry.
- This pins the whole Haven model version. It is unrelated to a Serving
  deployment's Dense Snapshot pin.

### Job Name Rules

- If `--job-name` is omitted, the CLI generates a name from workspace/project metadata as `<project>_v<version>`.
- If `--job-name` is provided, it is normalized with the same rules as the generated name: trim surrounding whitespace, collapse any run of unsupported characters into a single `_`, then strip leading/trailing `_` and `-`.
- Supported characters in the final name are ASCII letters, digits, `_`, and `-`.
- `--job-name` must not be empty, whitespace-only, or composed solely of unsupported characters.
- Names submitted by the CLI must be at most 63 characters after normalization, including the `_v<version>` suffix for generated names. This check also applies to `--dry-run` and explicit shared-weights names. If a name is too long, pass a shorter `--job-name`; the CLI does not truncate it.

### Workspace And Commit Rules

- `job create` reads `.forge/forge_meta.json` from cwd or nearby parent directories. It does not accept `--dir` / `--output-dir` and does not search local workspaces by version id.
- Before running workspace mode, `cd` into the actual workspace root returned by `code fetch`, not its parent/wrapper directory.
- If the user gives a path/version/project, verify the selected workspace by reading `.forge/forge_meta.json`.
- CRITICAL: before asking for `model-commit-id` / `norbert-commit-id`, first try to identify the intended workspace using the same rules as `code commit create`.
- Workspace mode resolves commit IDs from target-specific successful compile artifacts. Explicit `--model-commit-id` or `--norbert-commit-id` overrides only that slot; omitted slots still come from workspace context.
- CRITICAL: if workspace context does not contain a successful norbert compile artifact and the user did not provide `--norbert-commit-id`, stop and ask the user whether to provide `--norbert-commit-id` or compile norbert first. Do not start `code compile create --code-type norbert` automatically as a repair step for `job create`.
- No-workspace mode requires both `--model-commit-id` and `--norbert-commit-id`. It calls `get_commit` on the model commit for `model_id`, `version_id`, `version`, and `project_name`, and validates norbert metadata when present.
- If no workspace is selected and either commit ID is missing, stop before resource-group selection. Ask the user to run `forge code fetch` or provide both explicit commit IDs.
- Shared-weights mode is selected by `--share-weights-from <parent-model-name>` and does **not** require workspace context or norbert compile artifacts.
- Shared-weights mode requires `--model-commit-id`; this is sent as backend `commit_id` to `create_share_weights_train`.
- Shared-weights mode must not pass `--norbert-commit-id`; it may pass the same `--model-type <model_type_label>` used by normal Norbert creation.
- Shared-weights creation resolves an explicitly selected label through the same model-type catalog path as normal creation and sends only its typed `model_type_id`; Forge writes the canonical `uni_model_info`. The model type is optional and independent of `--resource-group`. When omitted, the CLI leaves `universal_model_type` out of the request. A site with no catalog data, including CN today, returns the existing model-type-not-found error when `--model-type` is supplied.
- Shared-weights mode may pass `--job-name`; if omitted, backend derives a default from the parent model name.

### Resource Group Rules

- `--resource-group` is optional at the CLI surface.
- If omitted, the CLI first reuses matching `job.resource_group` from `.forge/forge_meta.json`.
- If no matching saved group exists, it lists the current user's resource groups and prompts for a numbered choice or exact name.
- In shared-weights mode, `--resource-group` is optional and is sent only when explicitly provided. If omitted, the CLI omits `resource_group` from `create_share_weights_train`; according to the backend contract, the backend falls back to the parent job's resource group. The CLI must not prompt or list resource groups for shared-weights creation.
- MANDATORY for agents/non-interactive Bash: if the workspace has no saved resource-group, first run `forge quota resource-group list --mine --page-size 10` (bare `list` now returns every group platform-wide, not just the caller's — `--mine` is required here), ask/select a group, then call `job create --resource-group <selected>`.
- MANDATORY: if the user named a specific resource group and it is unavailable, do not silently replace it with a similar-looking group. Show the available candidates and wait for the user's explicit resource-group choice before submitting.
- Successful workspace job creation stores the selected group under `job.resource_group` with owner/runtime metadata for later reuse.

### Model Type Rules

`--model-type` is optional. For shared-weights creation it is independent of the resource group and is sent only when the user provides it. The `model_type_required` recovery flow below applies only to normal Norbert creation.

Agent flow when a non-interactive `job create` fails with stderr JSON `error.type = "model_type_required"` (exit code `2`):

1. Run `forge job model-type list --site <site>`.
2. Ask the user for an exact `model_type_label` or a fuzzy hint.
3. Filter only the fetched catalog rows by substring/token matches over `model_type_label`, `namespace_label`, `model_type_group`, and `tenant`, using only fuzzy hints the user explicitly typed or confirmed.
4. Ask for final confirmation before rerunning:
   - exactly 1 match: confirm that exact `model_type_label`
   - 2-10 matches: present those final labels as choices
   - >10 matches: ask for a more specific hint
   - 0 matches: ask for another hint or exact label
5. Rerun the original command with `--model-type "<confirmed model_type_label>"`.

Hard rules:

- Never invent, guess, recommend, or default a model type. Options must come from `forge job model-type list --site <site>`.
- Never derive extra fuzzy filters from resource group, workspace, project name, commit metadata, examples, or prior context. If the user provides only one fuzzy hint, filter by that hint only; do not add words inferred from a resource group or project name unless the user explicitly provides or confirms those words.
- When matches are too many, ask the user for a more specific hint and optionally show a small sample. Do not silently run a second narrower filter from inferred business words.
- The user selects the final `model_type_label` only. Do not ask for tenant, namespace, ids, or JSON configs; show tenant / namespace / group only as context.
- `Other`, `其他`, and free-form choice UI fallbacks are not valid selections. If chosen, ask for an exact catalog label or a new fuzzy hint.
- A successful normal job creation that used model type stores it in workspace context for the same runtime, owner, and resource group; do not reselect unless CLI reports `model_type_required` again.
- `--dry-run` only validates local request assembly. It does not prove a resource group can submit without `--model-type`.

Example failure-recovery flow:

```bash
forge job create --site <site> \
  --resource-group <resource-group> \
  --model-commit-id <model-commit-id> \
  --norbert-commit-id <norbert-commit-id>

# if stderr has error.type=model_type_required
forge job model-type list --site <site>

forge job create --site <site> \
  --resource-group <resource-group> \
  --model-commit-id <model-commit-id> \
  --norbert-commit-id <norbert-commit-id> \
  --model-type "<confirmed model_type_label>"
```

### List Model Type Catalog

```bash
forge job model-type list --site cn
forge job model-type list --site i18n
forge job model-type list --site us-ttp
forge job model-type list --site eu-ttp
```

- `model-type list` is read-only and accepts `cn`, `i18n`, `eu-ttp`, and `us-ttp`; as before, the backend returns catalog data only for the US (`i18n`), EU-TTP, and US-TTP control planes, so CN returns an empty catalog.
- It returns the full catalog as final `model_types` rows. Each row includes `tenant`, `namespace_label`, `model_type_label`, and optional `model_type_group`.
- The output intentionally hides backend ids; use `model_type_label` as the value for `job create --model-type`.

### Output Rules

- Success prints `ok`, `job_id`, `status`, `owner`, `resource_group`, `model_commit_id`, `norbert_commit_id`, and `links`.
- Shared-weights success prints `ok`, `job_id`, `status`, `owner`, optional `resource_group`, `model_commit_id`, `share_weights_from`, and `links`; `norbert_commit_id` is intentionally omitted from JSON output.
- MANDATORY: after successful `job create`, tell the user which `resource_group`, `model_commit_id`, and `norbert_commit_id` were submitted.
- For shared-weights `job create`, tell the user which `share_weights_from`, `model_commit_id`, and optional `resource_group` were submitted; do not mention a Norbert commit.
- After successful `job create`, show the returned `links.forge2` as the primary job link.
- If the command output includes additional `links.*` fields such as `links.workspace`, they may be shown as optional secondary links when useful, but they are not required in every response.
- Treat `links.*` as opaque command output. Do not construct links from `job_id`, hostname mappings, or `<forge2_web_base>`; if a command output does not include a link, do not synthesize it.
- `--dry-run` prints `ok` plus `request` and has no links. It is a local request assembly check, not a live backend acceptance check.
- For `--site eu-ttp` / `--site us-ttp`, `job create` keeps the same CLI flags but submits the narrower TTP `create_norbert` body with the site default IDC.

---

## Profiling timeline and GPU memory snapshot artifacts

List downloadable profiling timeline files or GPU memory snapshots（显存快照）.

```bash
forge job profiling-timeline list --job-id <forge-job-id>
forge job profiling-timeline list --job-id <forge-job-id> --site i18n

forge job memory-snapshot list --job-id <forge-job-id>
forge job memory-snapshot list --job-id <forge-job-id> --site i18n
```

Usage notes:

- Pass the exact training `--job-id`; there is no default/current-job fallback. If the job is on a non-default control plane, pass the matching `--site`.
- `profiling-timeline list` returns profiling timeline files for the selected job and works across supported training frameworks.
- `memory-snapshot list` returns GPU memory snapshot files. PyTorch jobs use the regular memory snapshot catalog; TensorFlow jobs may return memory-profile CSVs and XLA dump JSON files through the same output shape.
- Download URLs are rewritten for the active `network + site` runtime cell. Treat the returned `files` values as opaque download URLs; do not rewrite bucket names, domains, paths, or query strings yourself.
- Both commands are unpaginated. Catalog results preserve the service order; TensorFlow memory-profile and XLA fallback results are merged newest first.
- Output includes `count` and `directories`; each directory contains `directory` plus downloadable `files` URLs. An empty lookup returns `directories: []`.
- These commands are read-only. They list remote artifacts but do not download them to the local filesystem.

---

## Job checkpoints

### List job checkpoints

List model checkpoints produced by a training job.

```bash
forge job checkpoint list --job-id <forge-job-id>
forge job checkpoint list --job-id <forge-job-id> --site i18n
forge job checkpoint list --job-id <forge-job-id> --page 2 --page-size 50
```

Usage notes:

- Pass the exact training `--job-id`; there is no default/current-job fallback. If the job is on a non-default control plane, pass the matching `--site`.
- Pagination is 1-based: `--page` defaults to `1`, `--page-size` defaults to `100`.
- Sorting flags are not exposed; backend default `backup_time desc` gives stable newest-first ordering for one job.
- Output fields are `checkpoint_id`, `checkpoint_time`, `training_instance_time`, `size_mb`, `hdfs_path`, `remark`, and `status` (`normal`, `keep`, `deleting`, or a future backend value). `hdfs_path` is the primary downstream recovery / serving input. `training_instance_time` is the training data timestamp that produced the checkpoint; warm-start training can load the checkpoint and use this value as the next training `start_time`.

### Save a checkpoint

Mark one checkpoint as kept so automatic retention / cleanup jobs do not delete it.

```bash
forge job checkpoint save --job-id <forge-job-id> --checkpoint-id 25640396
forge job checkpoint save --job-id <forge-job-id> --checkpoint-id 25640396 --site i18n
```

Usage notes:

- `save` is a mutating command. Run it only when the user explicitly asks to save / keep / retain a checkpoint; never run it as part of read-only diagnosis.
- `--checkpoint-id` comes from the `checkpoint_id` field in `forge job checkpoint list` output. Do not pass backend `backup_id` terminology to users.
- Pass the exact `--job-id` and `--checkpoint-id`; there is no default/current-job fallback.
- If the job is on a non-default control plane, include the matching `--site`.
- Success prints `ok`, `action: "save"`, `job_id`, `checkpoint_id`, and may include `auth_source` / `token_refreshed`.

### Delete a checkpoint

Delete one checkpoint by its `checkpoint_id`.

```bash
forge job checkpoint delete --job-id <forge-job-id> --checkpoint-id 25640396
forge job checkpoint delete --job-id <forge-job-id> --checkpoint-id 25640396 --site i18n
forge job checkpoint delete --job-id <forge-job-id> --checkpoint-id 25640396 --yes
```

Usage notes:

- `delete` is a mutating command. Run it only when the user explicitly asks to delete a checkpoint; never run it as part of read-only diagnosis.
- It prompts for manual confirmation because checkpoint deletion is permanent. `--yes` skips the prompt for explicit non-interactive automation; agents must not add `--yes` unless the user has already accepted the deletion risk.
- If the user's goal is to prevent automatic cleanup, use `checkpoint save` instead of `checkpoint delete`.
- `--checkpoint-id` comes from the `checkpoint_id` field in `forge job checkpoint list` output. Do not pass backend `backup_id` terminology to users.
- Pass the exact `--job-id` and `--checkpoint-id`; there is no default/current-job fallback.
- If the job is on a non-default control plane, include the matching `--site`.
- Success prints `ok`, `action: "delete"`, `job_id`, `checkpoint_id`, and may include `auth_source` / `token_refreshed`.

---

## Direct Primus application, role, and pod snapshots

Use object-specific three-level commands for a current Primus metadata snapshot. Results report `source: standalone_primus_cli` as the primary data; a job-derived empty result can fall back to the selected stage's `legacy_primus_new_status` endpoint:

```bash
forge job primus-app get --job-id <forge-job-id> --stage-id <stage-id>
forge job primus-app get --app-id nj-primus-application-id
forge job primus-role list --job-id <forge-job-id>
forge job primus-role list --app-id nj-primus-application-id --role worker
forge job primus-pod list --job-id <forge-job-id> --role worker
forge job primus-pod list --app-id nj-primus-application-id --role worker --state RUNNING
forge job primus-pod get --job-id <forge-job-id> --role worker --pod-name <exact-pod-name>
```

Rules:

- Pass exactly one of `--job-id` and `--app-id`. `--stage-id` is valid only with `--job-id`; omission selects the latest stage. Job mode verifies stage identity and ownership before trusting its app ID.
- `primus-app get` retrieves one application summary. `primus-role list` returns role resources and state counts. `primus-pod list` returns a paged collection for one exact role. `primus-pod get` retrieves one exact `role + pod_name` row after a client-side exact match. There is no ambiguous `job primus get/get-meta/query` alias.
- Pod pagination is 1-based (`--page 1 --page-size 100`, maximum 1000). `--state` accepts `ALL`, `STARTING`, `RUNNING`, `RELEASED`, or `OTHER`; `OTHER` is filtered client-side and preserves the actual uppercase state.
- The primary source is always tried first. Only a successful empty result in `--job-id` mode triggers the `legacy_primus_new_status` fallback; `primus-app get --job-id` also treats the primary source's not-found answer for an application without a summary as empty. Any other request error is preserved and reported instead, and direct `--app-id` mode never invents a legacy URL.
- Every result identifies `source` as `standalone_primus_cli` or `legacy_primus_new_status`. Role/pod `lifecycle_authority=primus_history` means their state fields are snapshots, not lifecycle truth or operation-target selection.
- On `--network office`, pod links rewrite only reviewed production host suffixes for the selected non-CN site, preserving scheme, port, path, query, and fragment. A missing `links.vela` is synthesized from exact `pod.host_name` for CN, i18n, EU-TTP, and US-TTP; production, unknown-site, and hostless rows do not synthesize it.
- These commands never return raw CRD. Raw/online CRD belongs to `job primus-crd`; logs belong to `job log`; Webshell operations belong to `job webshell`.

---

## Primus CRD config

View, list history, diff history, and update the online Primus CRD config for an existing Forge training job. This is the CLI surface for the Forge3 FE "Update Primus" CRD flow.

### Hot update intent guard

Users may not know the term "Primus CRD". Treat `Primus 热更`, `Primus热更`, `Update Primus`, `更新 Primus`, and `修改 Primus 配置` as the Primus CRD update flow, usually `forge job primus-crd update`.

If the user only says `热更`, `热更新`, `任务热更`, `job 热更`, or `更新任务配置` without explicitly saying `Primus`, `CRD`, `Norbert commit`, or `改任务 commit`, stop before any mutating command and ask whether they mean:

- Primus CRD hot update: update role CRD resources, params, image, or other trainer config through `forge job primus-crd update`.
- Norbert commit update: switch an existing job to another Norbert commit or preload-model checkpoint through `forge job norbert-commit update`.

Do not infer one from the word `热更` alone. If the user asks for `热更历史` without saying Primus or Norbert, ask which history they want before choosing `primus-crd list/diff` or `norbert-commit list`.

Agent index guard:

- CRITICAL: Primus CRD history `index` is newest-first. `index=1` is the latest history row; larger indexes are older rows. Do not interpret `--history-index` as oldest-first or chronological ascending.
- For `diff --history-index A,B`, patch direction is always older -> newer. Because larger indexes are older, `--history-index 1,3` and `--history-index 3,1` both mean `history[3].trainer_config -> history[1].trainer_config`.

```bash
# View online Primus CRD config through the v2 update path
forge job primus-crd get --job-id <forge-job-id>
forge job primus-crd get --job-id <forge-job-id> --stage-id <stage-id> --trainer-platform godel

# List update_trainer_config history; CLI computes newest-first index (1 = latest, larger = older)
forge job primus-crd list --job-id <forge-job-id>
forge job primus-crd list --job-id <forge-job-id> --page-size 20

# Diff Primus CRD update history; --history-index uses that newest-first index
forge job primus-crd diff --job-id <forge-job-id>
forge job primus-crd diff --job-id <forge-job-id> --history-index 1
forge job primus-crd diff --job-id <forge-job-id> --history-index 1,3

# Update after reviewing the diff and typing "yes"
forge job primus-crd update --job-id <forge-job-id> --config-file primus.json

# Submit, drive the current backend's status reconciliation, and wait for this
# update_trainer_config record to reach success or failed
forge job primus-crd update --job-id <forge-job-id> --config-file primus.json --wait
forge job primus-crd update --job-id <forge-job-id> --config-file primus.json --wait --wait-timeout 15m

# Validate v2 path, show local permission context, and run config check without submitting update_primus_job_v2
forge job primus-crd update --job-id <forge-job-id> --config-file primus.json --dry-run
```

Useful flags:

| Flag | Applies to | Description |
|---|---|---|
| `--job-id` | all | Required Forge job ID; there is no current-job fallback |
| `--stage-id` | `get`, `list`, `diff` | Optional stage ID used when reading online config or filtering history |
| `--trainer-platform` | `get`, `update` | Optional trainer platform override; v2 jobs normally use `godel` |
| `--page` | `list` | 1-based history page number; backend `page` is 0-based |
| `--page-size` | `list` | History page size |
| `--history-index` | `diff` | Newest-first index from `list`: `1` is latest, larger numbers are older. `N` diffs one record's `prev_trainer_config -> trainer_config`; `A,B` diffs older -> newer regardless of input order |
| `--config-file` | `update` | Path to uploaded Primus CRD config JSON |
| `--config-json` | `update` | Inline uploaded Primus CRD config JSON |
| `--dry-run` | `update` | Run v2 guard, online config fetch, local permission context lookup, and backend config check; do not call `update_primus_job_v2` |
| `--wait` | `update` | After submission, poll the v2 config endpoint to drive backend reconciliation and wait for this operation's history status to become `success` or `failed` |
| `--wait-interval` | `update` | Poll interval for `--wait`; defaults to `5s` |
| `--wait-timeout` | `update` | Maximum wait duration; defaults to `0` (wait until context cancellation) |

Hard rules:

- This command intentionally supports only the backend v2 path. It first checks `get_primus_update_method`; if the server does not return `v2`, stop and report the CLI error. Do not attempt the legacy `get_primus_job_config` / `update_primus_job` path.
- `get`, `list`, and `diff` are read-only, but still depend on the same authenticated Reckon API surface as other job commands. If the job belongs to a non-default control plane, pass the matching `--site`.
- If no `--site` is passed and no default runtime site is configured, the CLI prompts the user to choose a Primus CRD region/site (`cn`, `i18n`, `us-ttp`, or `eu-ttp`) before calling Reckon. Non-interactive flows should pass `--site` explicitly.
- `list` reads `/api/v2/forge/get_job_operate_history` with `operate_type=update_trainer_config`. Backend response is newest-first and does not include an index; the CLI computes `index` as `(page-1)*page_size + row_number`. This means `index=1` is latest, and larger indexes are older.
- `diff` is only for historical comparison. With one index, `--history-index=1` means the latest history record's own diff versus its previous CRD. With two indexes, `--history-index=1,3` compares the older record's CRD to the newer record's CRD; input order does not change patch direction. Remember: the larger index is the older/base record.
- If a selected history record has a non-success status and the backend has no CRD payload for it, `diff` returns `skipped=true` and `skip_reason` instead of failing the command.
- `update` is mutating. It always shows the diff between online config and uploaded config before submitting. Do not suppress the diff or auto-type the confirmation for the user.
- `update` requires manual confirmation by typing exactly `yes` after reviewing the diff. In non-interactive agent flows, if confirmation cannot be collected, stop and show the diff rather than trying to submit.
- The CLI includes a local permission hint (`permission`) based on current user and job owner/admin metadata, but it does not hard-reject non-owner/non-admin users. Final authorization is enforced by `update_primus_job_v2`, so report the backend permission error if the server rejects the update.
- The CLI preview stores the online config used for the displayed diff. The later update call fetches online config again and rejects the update if it differs from that previewed config. If this happens, rerun `forge job primus-crd update` and review the latest diff again.
- `--config-file` and `--config-json` are mutually exclusive. Prefer `--config-file` for substantial configs so shell quoting does not corrupt JSON.
- Without `--wait`, a successful `update` result means `update_primus_job_v2` accepted the submission; it does not claim the asynchronous Primus operation has reached `success`.
- With `--wait`, the CLI snapshots history before submission, then binds the synchronously created row before the first `get_primus_job_config_v2` call while the trainer's `UPDATING` lock still excludes a later accepted update. It binds exactly one new row for the current operator. The previous config is not a hard match because another update may finish after the CLI reads online config but before its submission; the resulting config is also not matched because the backend may consume `delete_envs_by_forge`, merge unchanged roles, or normalize related command/environment fields during a valid update.
- If multiple new history rows for the current operator make association ambiguous, wait mode exits before driving reconciliation and reports that the update was already submitted. Do not resubmit automatically; use `primus-crd get` and then `primus-crd list` as directed by the error.
- After the submitted row is bound, each reconciliation cycle calls `get_primus_job_config_v2` before rereading that immutable history identity. In the current backend, the config GET queries the Primus update UUID and persists the resulting operation status. Repeated `primus-crd list` calls alone only read the database and cannot advance an `in_progress` record. Do not assume the newest row remains the submitted operation: a later same-operator update or `automatic` cache record may become index `1`.
- Wait mode treats `success` and `failed` as terminal. Backend `timeout` and `rollback` remain reconcilable states and continue polling until a terminal status, the configured timeout, or context cancellation.
- `--dry-run` and `--wait` are mutually exclusive.
- A wait timeout, cancellation, or polling failure happens after the update has already been submitted. Do not resubmit automatically. Use `primus-crd get` to continue driving backend reconciliation, then `primus-crd list` to inspect the existing operation.

Output notes:

- `get` prints `ok`, `job_id`, optional `stage_id` / `trainer_platform`, `trainer_status`, and `config`.
- `list` prints `ok`, `job_id`, optional `stage_id`, `page`, `page_size`, `total`, and `items`; each item includes CLI-computed `index` plus operation metadata, not the full CRD payload.
- `diff` prints `ok`, `job_id`, `changed`, `patch`, and `history` metadata; `patch` is empty when configs are semantically identical after JSON normalization. If a failed/incomplete history record cannot provide config text, `skipped` and `skip_reason` explain why no patch was built.
- `update` prints `ok`, `job_id`, `check_passed`, `permission`, and the submitted normalized `config`. With `--dry-run`, `dry_run` is true and the update API is not called. With successful `--wait`, `waited` is true and `operation` contains the matched history record, including `operation_status=success`.

---

## Change job priority

Set exactly one priority value from 0 through 15:

```bash
# Group Priority: submit a BPM work order
forge job priority update --job-id 18531899 --group-priority 12

# Override the site-default BPM template during a rollout
forge job priority update --job-id 18531899 --group-priority 12 --workflow-config-id 1603

# Personal Priority: apply the update immediately
forge job priority update --job-id 18531899 --personal-priority 8

# Zero is a valid explicit value
forge job priority update --job-id 18531899 --personal-priority 0
```

Rules:

- Run this mutating command only when the user explicitly asks to change the exact job and priority value.
- `--group-priority` and `--personal-priority` are mutually exclusive. Values outside `0..15` are rejected.
- Group Priority creates a BPM work order and reports `submitted=true`; it never sends `priority_inner` directly. Personal Priority is updated immediately and reports `updated=true`.
- Personal Priority requires the job owner from Ream's latest scheduling context (including released rows), a current administrator of the resource group resolved from that context, or a Ream admin. Report a permission error without retrying under another identity. Group Priority approval follows the BPM template.
- Pass the exact numeric Forge job ID; no additional task-identity flag is needed.
- Personal Priority sends only the selected field and does not require an existing priority record; the backend creates one when needed.
- Group Priority captures the current personal/group/global snapshot required by the BPM template and preserves the current Personal Priority in the submitted form.

---

## Change job resource group

Submit a resource-group change request for one job:

```bash
forge job resource-group update \
  --job-id 18531899 \
  --resource-group target-rg \
  --reason "move the job to the target group"
```

Submit multiple jobs from one source group, with quota migration and its additional approval routing:

```bash
forge job resource-group update \
  --job-id 18531899,18531900 \
  --resource-group target-rg \
  --reason "move the jobs and quota to the target group" \
  --with-quota
```

Rules:

- This is a mutating workflow submission. Run it only when the user explicitly asks to change the exact jobs' resource group and has supplied the exact target group and reason.
- `--job-id` accepts repeated flags and comma-separated values. The CLI creates one BPM work order per job because the workflow template accepts one scalar job ID. Batch jobs must all belong to the same source resource group.
- Quota is not migrated by default. Pass `--with-quota` only when the user explicitly asks to migrate quota; that mode resolves the source and target payoff units and routes approval to their administrators plus the configured AML quota administrators.
- The exact target resource group must be available to the current user. If the command rejects it, report the returned error and do not substitute a similar-looking group.
- Success means work orders were created, not that the resource-group changes have already completed. Report each entry in `work_orders`; for a single job, also report the compatibility fields `work_order_id`, `work_order_url`, and `work_order_status`. Do not submit a duplicate merely because a job still shows the old group immediately afterward.
- A definite BPM rejection after at least one confirmed work order returns `partial_success`. Report the completed `work_orders` and exact `unsubmitted_job_ids`; only those definitely unsubmitted IDs are safe to retry, and completed jobs must never be resubmitted automatically.
- A transport/read failure, invalid response, or HTTP 5xx returns `outcome_unknown`, including when it happens on the first job. Report the current `unknown_job_ids` separately from later `unsubmitted_job_ids`. Check BPM for every unknown job before deciding whether any manual retry is needed, and never automatically retry an unknown job; only `unsubmitted_job_ids` are known not to have been attempted.
- Follow the control-plane preflight rules above and pass an explicitly named `--network` or `--site` through unchanged.

---

## Transfer job owner

Transfer a Forge training job to a new owner.

```bash
forge job owner transfer --job-id 18531899 --new-owner songfuxing

# Non-default control plane
forge job owner transfer --job-id 18531899 --new-owner songfuxing --site i18n
```

Usage notes:

- Pass the exact `--job-id` and exact target username as `--new-owner`; there is no default/current-job fallback.
- If the user names a control plane, include the matching `--site` — see [invocation.md → Control planes](invocation.md#control-planes) for the alias table.
- Use this only when the user intends to transfer owner. It is a mutating command and should not be part of read-only diagnosis.
- Direct owner transfer is backend-controlled and normally allowed only for the current job owner or a Forge admin.
- Agent fast-fail rule: run `forge job owner transfer` at most once for a user request. If the CLI exits non-zero or returns `ok: false`, show the returned error JSON/message directly and stop. Do not retry with another username, another identity, another site, the BPM flow, `job meta`, user search, or any repair/probing command unless the user explicitly asks for follow-up investigation.
- Success prints `ok`, `job_id`, `new_owner`, `transfer_status`, and `status_label`. If `blocked` is true, show `next_step` and any `data_sources`; do not retry automatically.

---

## Kill a job

Stop a Forge training job by job id.

```bash
forge job kill --job-id 18439638

# ROW / I18N job
forge job kill --job-id 18439638 --site i18n
```

Usage notes:

- Pass the exact `--job-id` of the job to stop; there is no default/current-job fallback.
- If the user names a control plane, include the matching `--site` — see [invocation.md → Control planes](invocation.md#control-planes) for the alias table.
- Use this only when the user intends to stop the job. It is a mutating command and should not be part of read-only diagnosis.
- Forge checks whether the current login can stop the job. If access is denied or the job can no longer be stopped, report the returned error instead of retrying with another identity.
- Success prints `ok` plus `job_id`, which means the stop request was accepted.

---

## Get a job stage by ID

Resolve one exact Forge training stage to its owning job when only a `stage_id` is known.

```bash
forge job stage get --stage-id 88687594

# Query the matching control plane explicitly when it is known
forge --site i18n job stage get --stage-id 88687594
```

Usage notes:

- `--stage-id` is required and must be a positive integer. The command does not accept a `--job-id` because resolving that ownership is its purpose.
- The lookup makes one exact `stage_detail` request on the selected `--site`; it does not enumerate jobs, scan running jobs, or switch control planes automatically.
- Output always includes `ok`, `stage_id`, `job_id`, and `status`. An unavailable status is represented by an empty string.
- Forge verifies a unique positive stage/job identity across the returned stage detail fields. Missing, conflicting, or mismatched identities fail instead of trusting the requested ID.
- If the stage cannot be resolved, verify both the stage ID and `--site`. Do not treat a miss on one site as proof that the stage does not exist on every control plane.
- After resolving `job_id`, pass the returned `job_id` and original `stage_id` to stage-scoped observation commands such as `job meta get`, `job event query`, `job log query`, or `job metrics query`.

---

## List job stages

List execution stages for a Forge training job. Use this when you need to discover historical `stage_id` values before running stage-scoped commands such as `job meta get --stage-id`, `job event query --stage-id`, `job log query --stage-id`, or `job metrics query --stage-id`.

```bash
forge job stage list --job-id 18439638
forge job stage list --job-id 18439638 --page 2 --page-size 10
```

Usage notes:

- `--job-id` is required. There is no default/current-job fallback.
- Pagination is 1-based: `--page` defaults to `1`, `--page-size` defaults to `10`. The CLI converts this to the tracing backend's 0-based `page`.
- The backend orders stages by `stage_id desc`, so the newest stage is listed first.
- Sorting and filtering flags are not exposed; use stage-scoped commands after choosing a `stage_id`.
- Output includes `ok`, `job_id`, `page`, `page_size`, `count`, `total`, and `stages`. Stage entries include `stage_id`, status/timing fields, resource group, commit IDs, Norbert version fields, training framework, and other tracing stage summary fields returned by the backend.
- When summarizing `stage list` results for a user, list each stage's sample date range (`ins_start_time` / `ins_end_time`) and stage run time range (`start_time` / `end_time`) when present. Preserve missing values as `-`; do not infer sample or run end times that the backend did not return.

---

## Get job metadata

Retrieve job info and latest (or selected) stage details.

```bash
# Latest stage
forge job meta get --job-id 18439638

# Specific stage
forge job meta get --job-id 18439638 --stage-id <stage-id>

# Include current active shared-weight child jobs
forge job meta get --job-id 18439638 --with-shared-weight-children
```

### Job vs Stage

- **Job** — A training submission with fixed configuration (name, owner, framework, commit IDs)
- **Stage** — An execution instance of a Job. A Job may have multiple Stages (new Stage created on retry)
- `job meta get` returns **latest_stage** by default. Different Stages may use different code versions
- Use `job stage get --stage-id <id>` to resolve the owning Job when only a Stage ID is known
- Use `job stage list` to discover historical Stage IDs, then `--stage-id` to inspect one Stage
- Job/stage metadata does not establish the current Primus pod or executor
  attempt. For pod inventory, attempt/version expansion, and lifecycle state,
  use Primus History according to [primus_pods.md](primus_pods.md); never use
  `forge job webshell list` as the Source of Truth.

### Output fields

- `job` — ID, name, owner, status, framework, scheduler type, commit IDs, repo/project info
- `shared_weight_children` (only with `--with-shared-weight-children`) — current active child jobs that share weights from this job. Each child contains `job_id`, `model_name`, `owner`, `status`, `created_at`, and `links.forge2`; an empty relationship returns `count: 0` and `jobs: []`. This remains job-level metadata when `--stage-id` is present, and an enrichment failure fails the command instead of being reported as an empty relationship.
- Route parent-to-child relationship questions here, not to `serving model get`; query serving separately only when the user also asks about a returned child's deployment or instance health.
- `job.model_type` (optional) — submitted model-type label, when it can be resolved from the job configuration
- `job.uni_model_info` (optional) — complete submitted model-type metadata object, including tenant, namespace, and model-type identifiers and labels; its fields are preserved as the platform evolves
- `latest_stage` — stage ID, status, task type, train mode, timing info, sub-stages, and the stage-detail monitor shortcuts:
  - `primus_url`, `primus_url_bdee`, `primus_history_url`: Primus links returned by the platform
  - `grafana_url`: the same framework-aware Grafana/indicator-dashboard link shown by Forge3, using the page's default stage/trainer time range; `null` when no link can be built
  - `onenet_url`: the same OneNet diagnosis link shown by Forge3; `null` for US-TTP and when the stage lacks the required Primus job metadata
  - `hwj_grafana_url`: the platform-provided 寒武纪/HWJ Grafana link; `null` when unavailable
  - All three monitor-link keys are stable whenever `latest_stage` is returned; unavailable links use JSON `null` rather than disappearing from the output.
- `latest_stage.links` (optional) — normalized navigation targets copied from the selected stage metadata:
  - `primus` / `primus_bdee`: standard and BDEE Primus entries
  - `primus_history_original`: unmodified backend History URL for audit and handoff
  - `primus_history_access`: runtime-site-aware History URL for navigation; only the established US-TTP host rewrite may differ from the original
  - `dorado` / `dorado_bdee`: standard and BDEE Dorado entries
- Treat every `latest_stage.links` value as opaque. Do not synthesize a missing BDEE, Dorado, or Primus URL from IDs or hostname tables. Older binaries retain the raw `latest_stage.primus_url*`, `primus_history_url`, and `dorado_url*` fields.
- `latest_stage.sub_stages[name=data_check].data_sources` (optional) — data flows checked during datacheck, including source identity/location, sample time range, DCs, check status/detail, and dataflow name
- `links` — canonical Forge2 link for the job:
  - `links.forge2`: Forge2 job page
- `gazer_diagnosis` (optional) — Gazer fault diagnosis when the stage has detected or recovering faults
- Agents should use `links.forge2` from `job meta get` when linking an existing job. Do not reverse-infer or hand-build Tracing links from hostname mapping tables.
- Treat every returned `*_url` as opaque command output. In particular, do not rewrite the time range, dashboard host, datasource, or OneNet Primus ID yourself.

### RoW SDP one-shot execution

`forge job sdp exec` is the native compliant container-operation path for RoW
Primus containers on `--site i18n`, including the current Primus-on-Godel
(`nj-*`) jobs. Read [primus_pods.md](primus_pods.md) in full before using it.
The command binds the selected/latest stage, verifies stage/job identity,
resolves one exact target (AM or one exact `RUNNING` executor attempt), takes
that pod's service-provided webshellauth URL, appends `type=sdp`, and follows
the redirect chain with the CN browser SSO session. webshellauth resolves the
pod host IP and container id server-side, creates the compliant `T_GENERAL` SDP
session, and redirects to the gpcp detail page; Forge reads the session id and
gpcp host from that landing and runs one command over the SDP WebSocket.

```bash
# Exact RUNNING executor attempt
forge --site i18n job sdp exec \
  --job-id <forge-job-id> --stage-id <stage-id> \
  --role <role> --executor-id <exact-running-executor-id> \
  --command "ps aux | head"

# AM target
forge --site i18n job sdp exec \
  --job-id <forge-job-id> --am \
  --command-file ./diagnose.txt
```

- Exactly one of `--am` or `--executor-id` is required. Executor selection also
  requires exact `--role`; Forge does not infer it from the ID.
- `--stage-id` is optional and defaults to latest. When supplied it remains
  attached to metadata, History lookup, target selection, and output.
- Executor execution requires exactly one History row with the exact
  `executor_id` in `RUNNING`. No match, a terminal match, or multiple RUNNING
  matches fails before SDP session creation.
- Forge never constructs the target IP, container id, or webshellauth URL, and
  never DNS-resolves a hostname; it only trusts the exact pod's service-provided
  webshellauth URL from Primus History. All target resolution (ip + container
  id) happens server-side in webshellauth.
- The container OS user is server-determined by webshellauth; there is no
  `--user`, `--region`, or IP/container flag.
- Two credentials are needed: the CN browser SSO session (webshellauth
  delegates OAuth2 to `sso.bytedance.com` for every region — a human
  terminal can use `forge auth login --session --site cn`, an agent the
  non-blocking `--begin --session` / `--complete` flow; an account whose QR scan Lark rejects with "Login method isn't allowed" uses `--session-method interactive-browser` instead) creates the SDP session, and an i18n
  ByteCloud **user** JWT drives the SDP WebSocket. Application identity is
  rejected, and an injected JWT must explicitly identify a human-user credential
  type.
- Exactly one of `--command` or `--command-file` is required. Input must contain
  one command line. Pipes are supported; newlines, `;`, `&&`, `||`, and
  background `&` are rejected. The server-side SDP whitelist is authoritative.
- Output is capped by `--max-output-bytes` and ANSI-stripped unless `--raw` is
  passed. Timeouts are separately bounded by `--connect-timeout-ms`,
  `--init-timeout-ms`, and `--timeout-ms`.
- `completed` is the command-completion signal. `protocol_code` is not a shell
  exit status and `exit_code` is null. On an incomplete/error result, use the
  returned/reported SDP session ID and detail URL; do not automatically create
  a second session.

### Sub-stages

A Stage lifecycle consists of the following sub-stages:

| Sub-stage | Description | Troubleshooting |
|---|---|---|
| `pre_check` | Pre-check | — |
| `data_check` | Data check | — |
| `quota_check` | Quota check via ream | Stuck? Check **ream log**, trust the **final conclusion** (intermediate results may be misleading) |
| `scheduling` | Resource scheduling (request resources from the underlying scheduler) | May be **pending**. Check **Primus URL/log** for role status |
| `training` | Actual training | — |
| `resource_release` | Resource release | — |

**Key concepts**:
- `scheduling` and `training` are **logically split** from the `Trainer` phase, not independent data fields
- Split basis: DAG API (scheduler/trainer namespace) or events (first_batch)
- `stage.end_time` corresponds to `resource_release` end time
- Stage status maps to a sub-stage (e.g., `failed` may mean scheduling failed with training `unstarted`)

**Troubleshooting tips**:
- `quota_check` finished but `scheduling` not started → Check Primus URL for pending roles
- `quota_check` stuck → Check ream log for queuing status. Ream log may have misleading intermediate states; always trust the final conclusion (e.g., "allocation succeeded" or explicit stuck reason)

---

## Job events

### Get event summary

```bash
forge job event get-meta --job-id 18439638
```

Returns a summary of event types with their levels and counts.

**Note**: `trainer_start` / `trainer_end` events correspond to `stage_detail.Trainer` start/end, **not** `training` sub-stage start/end, nor the entire Stage start/end. If scheduling fails, the trainer process may have started but training never began.

### Query events

```bash
# All events
forge job event query --job-id 18439638

# Filtered
forge job event query --job-id 18439638 --stage-id <stage-id> --event-level ERROR
```

Output: array of events with `type`, `level`, `time`, `message`, `source`, and optional `details` / `suggestions`.

---

## Job logs

### Discover log types

```bash
forge job log get-meta --job-id 18439638
```

Returns available log types (e.g., `workflow`, `driver`, `pretrain`, `primus`, `ream`).

### Query logs

```bash
# Primus logs (defaults to stderr.log)
forge job log query --job-id 18439638 --log-type primus

# With role filter (defaults to stderr.log for the role)
forge job log query --job-id 18439638 --log-type primus --role worker

# Primus AM: list files, then query one file
forge job log query --job-id 18439638 --log-type primus --am --list-files
forge job log query --job-id 18439638 --log-type primus --am --log-file am/var/log/tiger/stderr.log

# With keyword + limit
forge job log query --job-id 18439638 --log-type primus --keyword "error" --limit 100

# Page through workflow logs from oldest to newest
forge job log query --job-id 18439638 --log-type workflow --seek head --offset 500 --limit 500

# Specific historical stage
forge job log query --job-id 18439638 --stage-id <stage-id> --log-type primus --keyword "train_path" --seek head --limit 1000

# Specify a different log file
forge job log query --job-id 18439638 --log-type primus --role worker --log-file stdout.log

# Download the full raw Primus log file, matching the Primus UI download link
forge job log query --job-id 18439638 --log-type primus --role worker --log-file stdout.log --download --output stdout.log
forge job log query --job-id 18439638 --log-type primus --role worker --download --output stderr.log --max-bytes 10737418240
forge job log query --job-id 18439638 --log-type primus --am --log-file am/var/log/tiger/stderr.log --download --output am-stderr.log

# Allow more time for a large or slow log transfer (default: 30m)
forge job log query --job-id 18439638 --log-type primus --role worker --download --output stderr.log --download-timeout 60m
```

Notes:

- When `--log-type` is omitted, the query defaults to the `workflow` log stream. If `workflow` returns nothing, the CLI automatically retries the `pretrain` stream as a fallback; if both are empty (often the case for jobs that finished a while ago), the query returns an empty result and does not auto-select other available types such as `ream`. Run `forge job log get-meta --job-id <id>` first to see which log types are actually available (some finished jobs only expose `ream`), then pass `--log-type` explicitly.
- Logs may be empty if the job stage is not running; the response includes a Primus URL for direct access.
- `--stage-id` is supported for querying a specific historical stage. Use `forge job stage list` first when the user needs logs from a non-latest stage.
- `--seek tail` (default) for recent logs, `--seek head` for oldest logs.
- `--offset` is a non-negative, 0-based offset applied after `--seek` ordering for `workflow`, `driver`, and Tracing-backed `pretrain` logs. It defaults to 0. The Reckon `trainer_log` fallback used when Tracing has no pretrain data returns one unpaged log object: `--offset 0` is allowed and `--limit` is applied locally, while a positive offset returns an API error instead of repeating the first page. Positive offsets are also unsupported for `primus` or `ream`; use stage, role, file, and keyword filters for those streams instead.
- Structured JSON output always includes `offset` and `am`: successful backend-paged results expose the effective integer offset, an unpaged pretrain fallback exposes `0`, and `primus` exposes `null`; `am` is `true` only for a Primus application-master selection and `false` for all other structured log results. Successful `ream` queries keep their direct Markdown output and do not expose these structured fields. `has_more` describes the backend page before client-side `--keyword` filtering, so a page can contain fewer than `--limit` matches while still reporting more raw rows.
- `--am` selects the single Primus application-master pod from job-summary metadata. It is mutually exclusive with executor selectors `--role`, `--index`, and `--status`.
- AM queries support the same file workflow as executor queries: use `--am --list-files`, copy one returned full file name into `--log-file`, then query or download it. A bare basename such as `stderr.log` is accepted only when it uniquely identifies one listed AM file; if several directories contain that basename, the command returns a validation error instead of choosing one silently.
- AM queries try the stage's available Primus endpoints in priority order. An endpoint is usable only when it can serve the requested content, file list, or download; metadata alone does not stop fallback to the next endpoint.
- **When querying primus role logs, stderr.log is fetched by default** (most useful for debugging). Use `--log-file` to fetch other logs like stdout.log.
- `--download --output <path>` downloads the full raw Primus log file for the selected AM or role/index. It is not limited by `--limit` and does not return parsed log entries. To avoid filling local disks, downloads are capped at 4294967296 bytes by default; pass `--max-bytes <bytes>` to raise the cap for larger logs.
- Full Primus log downloads have a 30-minute transfer deadline by default. Pass `--download-timeout <duration>` (for example, `60m`) when a large log needs more time; this flag only applies with `--download`.
- Downloads through Footprint prepare the selected log before transferring it. Preparation can take up to 150 seconds within the overall download deadline; an incomplete or failed preparation returns an error without replacing the output file.
- File listings report `size: -1` when the file size is known to be unavailable. Some listings cannot distinguish an unknown size from an empty file and report `size: 0` for both, so treat `size: 0` as "empty or unknown". A zero-byte download succeeds when the listed size is `0`; if the file is expected to contain logs, run the same query without `--download` to read its content before relying on the empty output. When the listed size is `-1` or positive, an empty response fails without replacing an existing output file. Retry `--list-files` with the same job, stage, role/index (or `--am`) and select the exact listed file before retrying the download. `--max-bytes` controls log content size; increasing it does not change the file-list response limit.
- On the office network, `--site us-ttp` Primus content queries and downloads try Footprint before the unreachable direct log-proxy URL. `--site eu-ttp` preserves and tries the exact Primus-returned log-proxy URL first so overseas users avoid Footprint, then submits that same URL to Footprint when direct access fails. The Footprint path requires both the CN browser session and an i18n-office ByteCloud credential. When needed, create or refresh the browser session with `forge auth login --session --site cn` (human terminal) or the agent-safe `--begin`/`--complete` flow; if Lark rejects the scan with "Login method isn't allowed", use `--session-method interactive-browser` (see [QR scan rejected](invocation.md#qr-scan-rejected-login-method-isnt-allowed)). Refresh the API credential with `forge --site i18n auth login`. The JWT is sent only to the Footprint host. Role/executor/file discovery still comes from Primus, and CN/i18n/production runtimes do not call Footprint.
- Do not enter a container merely to search routine Primus logs; use
  `forge job log query`, Primus log, or the region's Footprint-backed log path.
  If the user explicitly requests Forge webshell and
  [primus_pods.md](primus_pods.md) confirms it as an available supplemental
  path, search `/var/log/tiger/*` (for example
  `grep -i "oom" /var/log/tiger/*`), not `/opt/tiger/primus_logs`.

### Find `train_path` across stages

Use this playbook when the user asks for a `train_path`, training path, or path containing a date from Primus logs, especially when they mention that the path may be in an older stage.

1. List candidate stages, newest first:

```bash
forge job stage list --job-id 18439638 --page-size 50
```

2. Use the returned stage timing fields to narrow candidates when the user provides a date. Treat the requested date as a literal path clue, not proof that the stage's start/end date must match; still try nearby stages when the timing filter is uncertain.

3. Query each candidate stage's Primus logs for `train_path` before reading broad logs:

```bash
forge job log query --job-id 18439638 --stage-id <stage-id> --log-type primus --keyword "train_path" --seek head --limit 1000
```

4. If the role-less query returns only a Primus UI link, available roles, or no matching lines, discover roles and retry the roles returned by the CLI. Do not invent roles when the CLI cannot discover them.

```bash
forge job log get-meta --job-id 18439638 --stage-id <stage-id> --with-roles
forge job log query --job-id 18439638 --stage-id <stage-id> --log-type primus --role worker --log-file stderr.log --keyword "train_path" --seek head --limit 1000
```

5. If `stderr.log` has no match and the selected executor exposes other files, list files before trying another file:

```bash
forge job log query --job-id 18439638 --stage-id <stage-id> --log-type primus --role worker --list-files
forge job log query --job-id 18439638 --stage-id <stage-id> --log-type primus --role worker --log-file stdout.log --keyword "train_path" --seek head --limit 1000
```

6. Extract only paths from log lines that also match the user's date clue. Accept common `train_path` spellings such as `train_path=...`, `train_path: ...`, `--train_path=...`, or JSON-like `"train_path":"..."`. Preserve the exact path string from the log; do not normalize or rewrite HDFS/TOS path components.

7. Report the matched `train_path` together with the `stage_id` and any known `role`, `index`, and `log_file`. If multiple paths match, show all candidates and explain which date clue matched each. If no path is found after the checked stages, say which stages/roles/files were checked instead of guessing.

### Primus log flags

| Flag | Applies to | Description |
|---|---|---|
| `--stage-id` | `get-meta`, `query` | Query logs for a specific historical stage; defaults to latest stage when omitted |
| `--am` | `query` | Select the Primus application master; mutually exclusive with `--role`, `--index`, and `--status` |
| `--role` | `query` | Filter by role name (e.g., `worker`, `ps`) |
| `--index` | `query` | Replica index among the role's executors that match `--status`, ordered by executor ID ascending (default: 0) |
| `--status` | `query` | Executor status filter: `ALL`, `STARTING`, `RUNNING`, `RELEASED` (default: `ALL`). `OTHER` is a `primus-pod list` category only; use `forge job primus-pod list --job-id <forge-job-id> [--stage-id <stage-id>] --role <role> --state OTHER` to find those pods. `--index` counts positions within the listing `--status` selects (the role's full listing only for the default `ALL`), so for a pod found this way read its position from the same command with `--state ALL` and query without `--status` |
| `--log-file` | `query` | Log file to read (default: `stderr.log`). A path is matched as given; a bare name resolves to the role's conventional `<role>/var/log/tiger/<name>` when that file is listed, otherwise it must match exactly one file in `--list-files` — ambiguity is a validation error, so pass a full path from that listing |
| `--list-files` | `query` | List available log files for the selected AM or executor instead of fetching content |
| `--download` | `query` | Download the full raw Primus log file for the selected AM or role/index instead of returning parsed entries |
| `--output` | `query` | Required output file path when `--download` is set |
| `--max-bytes` | `query` | Maximum bytes to download with `--download`; default is 4294967296 bytes |
| `--download-timeout` | `query` | Maximum duration for one `--download` transfer; default is 30m |
| `--with-roles` | `get-meta` | Include available primus roles in the response (adds extra latency) |

---

## Training metrics

### Discover metrics

```bash
# All available metrics for a job
forge job metrics get-meta --job-id 18439638

# A specific metric by name
forge job metrics get-meta --job-id 18439638 --metric-name metrics/sailor/read_instance
```

Each entry returns:

- `name` / `path` — metric identifier
- `description` — human-readable description
- `meta` — configuration (aggregator, alias, metric_name_template, filters)

### Query metric data

```bash
# By metric name
forge job metrics query --job-id 18439638 --metric-name metrics/sailor/read_instance

# For a specific historical stage (queries the latest stage when omitted)
forge job metrics query --job-id 18439638 --stage-id <stage-id> --metric-name metrics/sailor/read_instance

# With time range
forge job metrics query \
  --job-id 18439638 \
  --metric-name metrics/deepinsight/auc \
  --start-time 1776411000 \
  --end-time 1776420000

# Exact Primus pod CPU utilization from the DTOP usage source
forge job metrics query \
  --job-id 19807171 \
  --stage-id 88020215 \
  --metric-name dtop:cpu_util \
  --pod-name '<full-primus-pod-name>'

# Host CPU from Vela for the machine running one US-TTP pod
forge --network office --site us-ttp job metrics query \
  --job-id 1454850 \
  --stage-id 15893941 \
  --metric-name vela:cpu_util \
  --pod-name '<full-primus-pod-name>'

# Host data-disk free percentage, or free and total bytes, by mount
forge --network office --site us-ttp job metrics query \
  --job-id 1454850 \
  --stage-id 15893941 \
  --metric-name vela:disk_free_percent \
  --pod-name '<full-primus-pod-name>'

forge --network office --site us-ttp job metrics query \
  --job-id 1454850 \
  --stage-id 15893941 \
  --metric-name vela:disk_free_absolute \
  --pod-name '<full-primus-pod-name>'
```

Output: time series with `time` and `value` per point.

`metrics query` accepts one `--metric-name` per invocation. Copy that logical name from `metrics get-meta`; backend metric templates and paths are metadata-owned and are not user-selectable. Training and job-level OLAP names are unprefixed. Exact-pod machine metrics use a source-qualified name such as `dtop:cpu_util` or `vela:cpu_util`. There is no `--vela`, `--metric-path`, or batch `--metric-names` flag. Run separate commands when comparing multiple metrics.

The built-in accelerator aliases returned by `metrics get-meta` reflect the selected stage's hardware. CPU-only stages omit accelerator aliases. MLU stages expose `gpu_util`, `gpu_vram`, and `gpu_sm_active` but omit the NVIDIA-only `gpu_tensor_core`; NVIDIA GPU stages expose all four. Older stages without hardware metadata retain the previous catalog behavior for compatibility.

Job-level GPU OLAP curves (`gpu_util`, `gpu_vram`, `gpu_sm_active`, `gpu_tensor_core`) use the **physical-card average** (`physical_avg`), matching the console. `--group-by-role` retains `weighted_avg`; CPU/MEM, DTOP and Vela are unchanged. Missing or invalid physical averages are skipped; valid points remain available, with `partial=true`, `skipped_points` and an explanatory `message`. If all points are skipped, the result contains empty `metrics` with the same incomplete-result markers; this is not evidence of zero utilization or no activity. Valid zero values are retained. A backend request failure still returns an error. Inspection rule conditions still use their existing `weighted_avg` field; do not rename that filter to `physical_avg`.

Job/role utilization queries (`cpu_util`, `mem_util`, `mem_rss`, `gpu_util`, `gpu_vram`, `gpu_sm_active`, `gpu_tensor_core`, with optional `--group-by-role`) allow a maximum **7-day / 604800-second** range. The CLI rejects longer or reversed ranges before issuing the data query, including a range that becomes too long after an omitted endpoint is resolved from the selected stage. It preserves the existing default: the final five days ending at the stage end, or now for a running stage, shortened to the stage start when newer. Explicit ranges are rejected rather than silently clamped. Times are Unix **seconds**. This utilization limit does not apply to training metrics, DeepInsight, DTOP or Vela queries.

#### Source-qualified pod/host metrics (`--pod-name`)

`--pod-name` selects one exact Primus executor for the selected job/stage and must be combined with `dtop:<metric>` or `vela:<metric>`. Use the full pod name from that stage; a pod from another stage or job is rejected instead of widening the query. Unprefixed names continue to mean job-level metrics and are rejected with `--pod-name`.

DTOP CPU, memory, RSS, and GPU utilization are exact-pod queries. DTOP GPU VRAM and SM use the pod only to resolve its host, then return one explicitly labeled host/device series per accelerator card; those two results are not pod-isolated.

Supported metrics and output units:

| Forge metric | `value` unit |
|---|---|
| `dtop:cpu_util` | fraction: DTOP usage cores / role allocated CPU cores |
| `dtop:mem_util` | fraction: DTOP bytes used / role allocated memory bytes |
| `dtop:mem_rss` | RSS bytes |
| `dtop:gpu_util` | fraction (multiply by 100 for percent) |
| `dtop:gpu_vram` | bytes |
| `dtop:gpu_sm_active` | percentage points (`0..100`) |

CPU and memory denominators come from the matching role's per-pod allocation. Ratios are not clamped and can exceed 1 when observed usage exceeds the allocation. If the allocation is missing or invalid, the command fails instead of returning a raw usage amount under a utilization name.

For `dtop:gpu_vram`, the selected stage's accelerator type chooses MLU or NVIDIA per-card data and the CLI returns bytes. `dtop:gpu_sm_active` returns one series per card in percentage points. `gpu_tensor_core` is only a job-level OLAP name; query it without `--pod-name` and optionally use `--group-by-role`.

Vela selectors are host-wide: `vela:cpu_util`, `vela:load`, `vela:mem_free_percent`, `vela:disk_free_percent`, `vela:disk_free_absolute`, `vela:net_in`, `vela:net_out`, `vela:ss_total`, `vela:disk_read`, `vela:disk_write`, `vela:disk_await`, `vela:tcp_retrans`, `vela:process_cpu`, `vela:process_mem`, `vela:sys_reboot`, `vela:sys_uptime`, and `vela:ssh_ping_down`. `vela:cpu` and `vela:mem` are compatibility aliases. `vela:disk_free_percent` reproduces Vela's Disk Free Percent panel with percentage-point values and one series per `mount`. `vela:disk_free_absolute` reproduces both byte-valued curves in Vela's absolute panel, returning `df.bytes.free` and `df.bytes.total` per mount and preserving `__name__` so callers can distinguish them. Both selectors are restricted to the one-machine view's fixed `/data00` through `/data07` selection. Vela is available only for office-network CN/i18n/EU-TTP/US-TTP, uses the matching Forge token, resolves the exact pod's hostname to an IP, preserves Prometheus labels, and returns `links.vela`. These values describe the whole machine, not the selected container.

`--pod-name` and `--group-by-role` are mutually exclusive. If the pod cannot be resolved, run `forge job stage list --job-id <id>` to verify the stage, then retry with the full pod name for that stage.

**Note**: `metrics get-meta` returns a static metric catalog. If the job has not entered the Trainer phase, training metrics (e.g., AUC, loss) will not have data. The CLI will show a hint in this case.

**Note**: `metrics get-meta` and `metrics query` accept `--stage-id` (optional; use the latest stage when omitted). An explicit stage must report the requested stage identity and belong to the requested job; missing, conflicting, or cross-job ownership is rejected before catalog resolution or any data query. The query never falls back to an earlier stage: if the selected stage has metrics metadata but the query returns no sample points, the result is an empty array; if the selected stage has no Trainer/metrics metadata at all (for example, the latest stage failed before training started), the CLI returns a "no metrics metadata found" error instead. Run `forge job stage list --job-id <id>` first and pass a `--stage-id` of a stage that actually belongs to that job and trained.

**关于"吞吐"**：除非用户特别说明，"吞吐"均指**训练任务吞吐**（数据读取速率），对应指标为 `metrics/sailor/read_instance`（instances/second）。例如：
```bash
forge job metrics query --job-id 18439638 --metric-name metrics/sailor/read_instance
```

### 数据管道吞吐指标详解

数据从 HDFS 到训练框架的流向及各阶段吞吐指标：

```
HDFS → Primus IO → Fountain (各op预处理) → Sailor (训练框架消费)
```

| 指标 | 路径 | 阶段 | 说明 |
|---|---|---|---|
| **Primus IO Pool Size** | `metrics/fountain/primus_io/priority_pool_size_*` | HDFS → Primus IO | Primus DataIO 的 Buffer 水位，判断 HDFS 读取瓶颈 |
| **Fountain Read** | `metrics/fountain/read_instance` | Fountain 输入 | Fountain 各算子实际接收到的样本实例数 |
| **Fountain Preprocessing** | `metrics/fountain/preprocessing_instance` | Fountain 输出 | Fountain 预处理后输出给训练框架的速率 |
| **Fountain OP Pool Size** | `metrics/fountain/pool_size_avg` | Fountain 内部 | 各 Fountain 算子的 pool size，判断 op 阻塞 |
| **Sailor Read** | `metrics/sailor/read_instance` | 训练框架消费 | **真实训练吞吐** |

#### Primus IO Pool Size 指标解读

**指标含义**：每个 producer 容器中 Primus DataIO 维护的 buffer/pool 水位百分比（当前元素数 / 总容量）。

| 指标后缀 | 含义 |
|---|---|
| `_gt90` (≥90%) | pool 水位 ≥90% 的 producer 容器数，高表示 HDFS 读能力充足 |
| `_lt25` (≤25%) | pool 水位 ≤25% 的 producer 容器数 |
| `_lt01` (≤1%) | pool 水位 ≤1% 的 producer 容器数 |
| `_0` (=0) | pool 水位 = 0 的 producer 容器数，高表示 HDFS 读瓶颈 |

**判断方法**：
- **无 HDFS 瓶颈**：`pool_size_gt90` 接近总 replica 数，其他指标接近 0
- **HDFS 瓶颈**：`pool_size_0` 或 `pool_size_lt01` 较高，说明很多容器读不到数据

#### Fountain OP Pool Size 指标解读

**指标含义**：每个 Fountain 算子的 output pool size，判断是否是某些 op 运行慢把样本处理流程堵住。

**判断方法**：
- 某个 op **上游 pool 有数，但自身 output pool 为空** → 该 op 运行慢，阻塞流程
- **所有 pool 都接近 0** → 上游读文件慢（Primus DataIO 问题），不是 Fountain 问题

**注**：op name 为 `:0`、`:1`、`:2`... 表示对应数据流的 output pool；其他 name 表示对应 op 的 output pool。

#### 瓶颈排查流程

1. **先看 Primus IO Pool Size**
   - `pool_size_gt90` 低 → HDFS 读瓶颈，参考 GPU 训练 Sailor/Producer 瓶颈分析调优
   - `pool_size_gt90` 高 → HDFS 正常，继续排查 Fountain

2. **再看 Fountain OP Pool Size**
   - 某个 op 阻塞 → 优化该 op 或调整 Fountain 配置
   - 所有 pool 接近 0 → 实际上是 HDFS 问题，回到第 1 步

3. **最后对比吞吐指标**
   - `fountain/read_instance > fountain/preprocessing_instance` → 样本被某些 op 过滤或处理慢
   - `fountain/preprocessing_instance > sailor/read_instance` → 训练框架消费能力不足

**推荐查询方式**（分别查询关键指标）：
```bash
forge job metrics query --job-id 18439638 --metric-name metrics/sailor/read_instance
forge job metrics query --job-id 18439638 --metric-name metrics/fountain/read_instance
forge job metrics query --job-id 18439638 --metric-name metrics/fountain/preprocessing_instance
```

**注意**：这些数据管道指标的查询优先级不高。如果只是模糊地需要"吞吐"数据，只需查询训练吞吐 (`metrics/sailor/read_instance`) 即可。只有在发现数据异常、吞吐很低，或者用户明确要求排查数据管道瓶颈时，才需要查询这些细粒度指标。

### Utilization metrics

Utilization metrics (CPU, Memory, GPU) are queried through the same `metrics` command. Unprefixed names return job-level data or optional role groups. Source-qualified `dtop:<metric>` names require `--pod-name`; CPU/memory/GPU utilization then returns one exact executor series, while GPU VRAM and SM return per-card series from the pod-resolved host:

```bash
# Query CPU utilization
forge job metrics query --job-id 18439638 --metric-name cpu_util

# Query GPU utilization
forge job metrics query --job-id 18439638 --metric-name gpu_util

# Query exact-pod DTOP CPU utilization
forge job metrics query --job-id 18439638 --metric-name dtop:cpu_util --pod-name '<full-primus-pod-name>'

# Query host-wide Vela CPU busy percentage
forge --network office --site cn job metrics query --job-id 18439638 --metric-name vela:cpu_util --pod-name '<full-primus-pod-name>'
```

Available utilization metrics:

| Metric | Type | Description | `--group-by-role` | `--pod-name` |
|---|---|---|---|---|
| `cpu_util` | cpu | Job-level CPU utilization | Yes | No |
| `mem_util` | memory | Job-level memory utilization | Yes | No |
| `mem_rss` | memory | Job-level memory RSS | Yes | No |
| `gpu_util` | gpu | Job-level GPU utilization | Yes | No |
| `gpu_vram` | gpu | Job-level GPU/MLU VRAM | Yes | No |
| `gpu_sm_active` | gpu | Job-level SM activity | Yes | No |
| `gpu_tensor_core` | gpu | Tensor Core active ratio | Yes | No (host/device scoped) |
| `dtop:cpu_util` | cpu | Exact-pod allocated-CPU ratio | No | Yes |
| `dtop:mem_util` | memory | Exact-pod allocated-memory ratio | No | Yes |
| `dtop:mem_rss` | memory | Exact-pod RSS bytes | No | Yes |
| `dtop:gpu_util` | gpu | Exact-pod GPU utilization fraction | No | Yes |
| `dtop:gpu_vram` | gpu | GPU/MLU VRAM bytes per card | No | Yes (pod-resolved host/device) |
| `dtop:gpu_sm_active` | gpu | SM percentage points per card | No | Yes (pod-resolved host/device) |

**Note**: DeepInsight server metrics (`deepinsight_server_throughput`, `deepinsight_server_err_throughput`) are also queried via OLAP but do **not** support `--group-by-role`.

---

## Working patterns

### Inspect a job status (recommended order)

This order assesses Forge job/stage health. It does not determine concrete
Primus pod inventory, executor attempt identity, or lifecycle state. For those
facts, use Primus History and [primus_pods.md](primus_pods.md).

**Step 1 — Get metadata** to understand the overall stage and sub-stage status:

```bash
forge job meta get --job-id <id>
```

**Step 2 — Get event summary** to complement meta with event-level signals:

```bash
forge job event get-meta --job-id <id>
```

> **Important**: `meta get` alone is not enough to fully assess job health. Always combine with `event get-meta` (or `event query`) to capture error signals that may not be reflected in the stage status.

### How to determine if a job is abnormal

A job is considered **abnormal** if any of the following is true:

| Check | Abnormal indicator |
|---|---|
| `job.status` | `failed`, `killed` |
| `latest_stage.status` | `failed`, `killed` (or stuck in `pre_check` / `data_check` / `quota_check` / `scheduling` for an extended time) |
| `sub_stages` | Any sub-stage status is `failed` or `killed` |
| `event summary` | Contains events with level `ERROR` or `CRITICAL` |
| `gazer_diagnosis` | Contains `detected_profiles` with fault summary (e.g., hang, pod failure) |

**Note**: The CLI does not perform automatic abnormality detection. The skill (or user) must evaluate the combination of meta + events to determine if intervention is needed.

### Drill down based on findings

| Meta status | Suggested next step |
|---|---|
| `gazer_diagnosis` not empty | Check the detected profiles for automatic diagnosis first |
| `pre_check` / `data_check` / `quota_check` stuck | `job event query --event-level ERROR` + `job log query --log-type ream` |
| `scheduling` pending / failed | `job event query --event-level ERROR` + check Primus URL in meta |
| `training` running | `job metrics query` for throughput and resource pressure |
| `training` failed / killed | `job event query --event-level ERROR` + `job log query --log-type primus` |
| `finished` / `succeeded` | `job metrics query` for final evaluation metrics |

### Log investigation hierarchy (when status is failed but sub_stages/events are uninformative)

When the failure reason is not obvious from meta or events, query logs in this order:

1. **workflow** — orchestration-level errors (job setup, stage transitions)
2. **pretrain** — pre-training initialization errors
3. **If still unclear** → **primus** — actual training execution logs (per-role status and detailed error traces)
4. **If scheduling-related** → **driver** — scheduler-level logs (resource allocation, role placement)

**Log type mapping**:

| Log type | Level | Use when |
|---|---|---|
| `workflow` | Orchestration | Job setup failures, stage transition errors |
| `pretrain` | Pre-training | Initialization failures before training starts |
| `driver` | Scheduling | Resource scheduling, role placement issues |
| `primus` | Execution | Training runtime errors, per-role status and logs |
| `ream` | Quota | Quota check / queuing issues |

**Tip**: If events contain helpful pointers (e.g., error messages with log references), use them to jump directly to the relevant primus logs instead of scanning all log types.

### Framework-specific primus logs

When `training` fails and the generic primus log is uninformative, inspect framework-specific logs based on `latest_stage.training_framework` from `job meta get`.

#### Lagrange TensorFlow (`lagrange_tensorflow_sync` / `lagrange_tensorflow_async`)

Key log files under `/var/log/tiger/`:

| Log file | What it contains | When to check |
|---|---|---|
| `runner_ver_{replica}_{index}_globalrank_{g}_localrank_{l}.log` | GPU process direct output; user debug prints and framework training progress | Primary log for training errors, loss anomalies, or crash traces |
| `stderr.log` | Launcher process output; environment checks, liveness probes, startup failures | Scheduling or initialization issues before training begins |
| `async_executor.log` | Async debug/summary output; isolated user-facing debug info for performance | Debug/summary info when normal logs are too noisy; check for hang or performance regressions |

**Note**: Start with rank 0 (`globalrank_0_localrank_0`). Other ranks may also contain relevant errors for distributed failures.

#### Lagrange Torch (`lagrange_torch_sync` / `lagrange_torch_async`)

Same three log files as Lagrange TensorFlow, plus:

| Log file | What it contains | When to check |
|---|---|---|
| `hang_check.log` | Hang detection reports | Suspected distributed deadlock or NCCL timeout |

**Hang confirmation**: If `hang_check.log` contains `=== PySpy Analyze ===` or `=== Nccl Trace Analyze ===`, a hang is confirmed.

#### Other frameworks

| `training_framework` | Key log focus |
|---|---|
| `torch` | `stderr.log` + `stdout.log` for Zouwu runtime errors |
| `tensorflow` | `stderr.log` for Lite/TF session initialization |
| `dandelion_v3` | `stderr.log` for v3 launcher and resource scheduling |
| `jaguar` | `stderr.log` for Jaguar execution traces |
| `cpu` / `unknown` | `stderr.log` as primary; no framework-specific files |

### Debug training issues

1. Error events: `forge job event query --job-id <id> --event-level ERROR`
2. Logs: `forge job log query --job-id <id> --log-type primus`
3. Data throughput: `forge job metrics query --job-id <id> --metric-name metrics/sailor/read_instance`
4. Resource pressure: `forge job metrics query --job-id <id> --metric-name cpu_util` for job-level OLAP, `dtop:cpu_util --pod-name <pod>` for one executor, or `vela:cpu_util --pod-name <pod>` for the whole host

### Stage stuck diagnosis

| Symptom | Possible cause | Investigation |
|---|---|---|
| `quota_check` not finishing | Queuing for quota | Check **ream log**, trust the final conclusion |
| `quota_check` done but `scheduling` not started | Resource scheduling pending | Check **Primus URL/log** for role status |
| `scheduling` failed | Resource request failed | Check events + primus log |
| Training metrics empty | Job not yet in training phase | Confirm training status is running/finished via `meta get` |
