# TeslaX Plan, Folder, EnvTag & Report

## Endpoints

| 命令 | 方法 | 路径 |
| --- | --- | --- |
| `tesla folder list` | `GET` | `/apix/space/:spaceId/folder` |
| `tesla env-tag list` | `GET` | `/apix/space/:spaceId/envTag` |
| `tesla report list` | `GET` | `/api/v1/teslax/space/:spaceId/report` |
| `tesla report case` | `GET` | `/api/v1/teslax/space/:spaceId/case_detail` |
| `tesla plan list` | `GET` | `/apix/space/:spaceId/plan` |
| `tesla plan create` | `POST` | `/apix/space/:spaceId/plan` |
| `tesla plan get` | `GET` | `/apix/space/:spaceId/plan/:planId` |
| `tesla plan records` | `GET` | `/apix/space/:spaceId/plan/:planId/records` |
| `tesla plan update` | `PUT` | `/apix/space/:spaceId/plan/:planId` |
| `tesla plan delete` | `DELETE` | `/apix/space/:spaceId/plan/:planId` |
| `tesla plan trigger` | `POST` | `/apix/space/:spaceId/plan/:planId/trigger` |

## Examples

```bash
bytedcli --json tesla folder list --space-id 1000 --branch master
bytedcli --json tesla env-tag list --space-id 1000
bytedcli --json tesla report list --space-id 1000 --task-id "<task-id>" --bearer-token "<bearer-token>"
bytedcli --json tesla report case --space-id 1000 --task-id "<task-id>" --case-id 123 --bearer-token "<bearer-token>"

bytedcli tesla plan create \
  --space-id 1000 \
  --plan-name "sample plan" \
  --psm example.psm \
  --replay-env sample_env \
  --payload '{"psm_exec_params":{"example.psm":{"replay_env":"sample_env"}}}' \
  --execute

bytedcli tesla plan update \
  --space-id 1000 \
  --plan-id 2000 \
  --plan-name "updated sample plan" \
  --payload '{"notify_config_json":{"notify_users":["sample-user"]}}' \
  --execute

bytedcli tesla plan delete --space-id 1000 --plan-id 2000 --execute
```

## Rules

- `tesla plan create` defaults to `enable_ftf=false`, `enable_tesla=true`, and `platform=teslax`.
- `folder`、`env-tag`、`plan` commands use ByteCloud JWT.
- `report list` / `report case` require `--bearer-token`.
- Use placeholder values in examples; never paste real space IDs, task IDs, tokens, cookies, or JWTs into docs.
