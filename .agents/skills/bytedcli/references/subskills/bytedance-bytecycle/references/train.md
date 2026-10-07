# Train commands

Top-level: `bytedcli bytecycle train ...`

All write subcommands print a dry-run payload first; pass `--yes` to actually call the API.

## Read

```bash
bytedcli bytecycle train get --train-id <id>
bytedcli bytecycle train list --workspace-id <id> --status integrating --username <username>
bytedcli bytecycle train vars get --train-id <id>
bytedcli bytecycle train pipeline list --train-id <id> --region cn --activity-phase train_deploy
```

`train list` filters: `--workspace-id`, `--status`, `--username`, `--team-name`, `--keyword`, `--page`, `--page-size`.

## Create train

```bash
bytedcli bytecycle train create \
  --workspace-id <id> \
  --name "<train name>" \
  --region cn \
  --plan-start-integrated-time 2026-05-20T14:30:00+08:00 \
  --plan-code-freeze-time      2026-05-21T18:00:00+08:00 \
  --plan-release-time          2026-05-26T18:00:00+08:00 \
  --lark-group-list-file       lark-group-list.json \
  --train-workflow-vars-file   train-workflow-vars.json
```

`--region` is repeatable. `--train-workflow-vars-file` is required and must contain the full `train_workflow_vars` JSON array captured from the page request.

For Lark groups, either pass `--lark-group-list-file` with the full `lark_group_list` JSON array, or use `--lark-group-type <create|bind|none>` plus `--lark-group-id <id>`.

## Lifecycle transitions

```bash
bytedcli bytecycle train to-integrating --train-id <id>
bytedcli bytecycle train to-code-freeze --train-id <id>
bytedcli bytecycle train to-deploying   --train-id <id> --region cn --release-note "..."
bytedcli bytecycle train complete       --train-id <id>
bytedcli bytecycle train cancel         --train-id <id> --note "..."
```

`to-deploying` requires one or more `--region` flags and an optional `--release-note`.

## Edit

```bash
bytedcli bytecycle train update \
  --train-id <id> \
  --name "renamed train" \
  --plan-release-time 2026-05-28T18:00:00+08:00
```

The handler reads `get_train_detail`, keeps fields you did not pass, and overrides the requested fields. Time order is re-checked after patching.

## Rollback

```bash
bytedcli bytecycle train rollback --train-id <id> --rollback-entire-train
bytedcli bytecycle train complete-rollback --train-id <id>
```

## Hotfix

`hotfix-create` takes the same base fields as `train create`, except it does not require `--train-workflow-vars-file`.

```bash
bytedcli bytecycle train hotfix-create \
  --workspace-id <id> \
  --name "hotfix 2026-05-20" \
  --region cn \
  --plan-start-integrated-time 2026-05-20T14:30:00+08:00 \
  --plan-code-freeze-time      2026-05-20T16:00:00+08:00 \
  --plan-release-time          2026-05-20T20:00:00+08:00
```

## Merge-back + operation records + pipeline create

```bash
bytedcli bytecycle train merge-back --train-id <id> --region cn
bytedcli bytecycle train operation list --train-id <id> --action create --action deploy
bytedcli bytecycle train pipeline create-and-build --train-id <id> --region cn
```

`--region` is required across lifecycle commands that operate on a region; there is no implicit `cn` default.
