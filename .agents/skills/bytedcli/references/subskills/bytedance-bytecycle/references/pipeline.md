# Pipeline & MR commands

Two top-level families: `bytedcli bytecycle mr ...` and `bytedcli bytecycle pipeline ...`.

All write subcommands print a dry-run payload first; pass `--yes` to execute.

## `mr train` — train MR

```bash
# Read current MR(s) on the train
bytedcli bytecycle mr train get --train-id <train-id>

# Create the train MR — dry-run by default
bytedcli bytecycle mr train create --train-id <train-id>

# Merge the train MR — dry-run by default
bytedcli bytecycle mr train merge --train-id <train-id>
```

`create` and `merge` share the same train id input. Inspect with `--json` when you need the full response.

## `pipeline ticket status` — ticket pipeline creation status

```bash
bytedcli bytecycle pipeline ticket status --ticket-id <ticket-id> --region cn
```

Response contains `status`, `build_id`, `info`.

## `pipeline train status` — train pipeline creation status

```bash
bytedcli bytecycle pipeline train status --train-id <train-id> --region cn
```

Response shape is the same `{status, build_id, info}`.

## `pipeline trigger-ticket` — trigger an existing ticket pipeline build

```bash
bytedcli bytecycle pipeline trigger-ticket \
  --ticket-id <ticket-id> \
  --pipeline-id <pipeline-id> \
  --region cn \
  --trigger-params-file params.json
  # add --yes to execute
```

- `--trigger-params-file` is optional; without it the payload sends `trigger_params: {}`.
- Response: `{build_id}`.

## `pipeline trigger-train` — trigger an existing train pipeline build

```bash
bytedcli bytecycle pipeline trigger-train \
  --train-id <train-id> \
  --pipeline-id <pipeline-id> \
  --region cn \
  --activity-phase train_deploy
  # add --yes to execute
```

`--activity-phase` examples: `train_deploy`, `train_mr`, `train_release` (depends on the pipeline template).

## `pipeline build` — build operations

```bash
# Inspect one build
bytedcli bytecycle pipeline build get --build-id <build-id>

# List child builds of a parent train phase build
bytedcli bytecycle pipeline build list --parent-build-id <parent-build-id>

# Read vars for starting a pipeline, optionally inheriting an origin build
bytedcli bytecycle pipeline build vars --pipeline-id <pipeline-id> --origin-build-id <build-id>

# Start a build; dry-run by default
bytedcli bytecycle pipeline build start \
  --pipeline-id <pipeline-id> \
  --origin-build-id <build-id> \
  --variable-file variable.json \
  --trigger-params-file trigger_params.json

# Re-run an existing build by resolving its pipeline id from build detail
bytedcli bytecycle pipeline build rerun --build-id <build-id>
```

`build start` and `build rerun` are wrapped commands. Pass `--yes` to execute after checking the dry-run payload.

## `pipeline job` — manual checkpoint jobs

```bash
# List pending jobs in a build
bytedcli bytecycle pipeline job pending --build-id <build-id>

# Approve / reject one job; dry-run by default
bytedcli bytecycle pipeline job approve --build-id <build-id> --job-id <job-id>
bytedcli bytecycle pipeline job reject --build-id <build-id> --job-id <job-id> --note "reason"

# Approve all pending jobs in one build that expose approve actions
bytedcli bytecycle pipeline job approve-build --build-id <build-id>
```

When `--build-id` is provided, approve/reject reuses the button body from build detail. Without `--build-id`, the CLI builds a default `extra_context` body.

## `pipeline train jobs` / `pipeline train approve` — train phase checkpoints

```bash
# Resolve the train phase pipeline build, include child builds, and list pending jobs
bytedcli bytecycle pipeline train jobs \
  --train-id <train-id> \
  --region cn \
  --activity-phase train_deploy

# Dry-run all approve actions across the parent/child builds
bytedcli bytecycle pipeline train approve \
  --train-id <train-id> \
  --region cn \
  --activity-phase train_deploy

# Execute after checking the dry-run actions
bytedcli bytecycle pipeline train approve \
  --train-id <train-id> \
  --region cn \
  --activity-phase train_deploy \
  --yes
```

The train phase resolver queries train pipeline list, rejects ambiguous matches unless `--build-id` is provided, then queries child builds by `parent_build_id`. It preflights all pending jobs and refuses execution if any pending job lacks an approve action.

## Important caveats

- The status commands intentionally hide underlying request details from agent-facing guidance. If a live call ever rejects the current implementation, fix the API client instead of teaching agents private request paths.
- `pipeline train approve --yes` may approve multiple jobs across parent/child builds. Always inspect the dry-run `actions` first.

## Common chain

```bash
# 1. Create the pipeline
bytedcli bytecycle ticket pipeline create-and-build --ticket-id <ticket-id> --region cn --yes

# 2. Check creation status
bytedcli bytecycle pipeline ticket status --ticket-id <ticket-id> --region cn

# 3. Trigger build once status reports ready
bytedcli bytecycle pipeline trigger-ticket --ticket-id <ticket-id> --pipeline-id <id> --region cn --yes
```
