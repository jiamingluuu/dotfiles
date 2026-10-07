# bytedcli TeslaX

## When To Use

- 查询 TeslaX 空间目录：`tesla folder list`
- 查询 TeslaX 空间 envTag：`tesla env-tag list`
- 查询 TeslaX 任务报告列表和 case 明细：`tesla report list`、`tesla report case`
- 创建、查看、更新、删除或触发 TeslaX-only 测试计划：`tesla plan ...`

## Quick Start

```bash
bytedcli --json tesla folder list --space-id 1000 --branch master
bytedcli --json tesla env-tag list --space-id 1000
bytedcli --json tesla report list --space-id 1000 --task-id "<task-id>" --bearer-token "<bearer-token>"
bytedcli --json tesla report case --space-id 1000 --task-id "<task-id>" --case-id 123 --bearer-token "<bearer-token>"
bytedcli tesla plan list --space-id 1000 --psm example.psm
bytedcli tesla plan get --space-id 1000 --plan-id 2000
bytedcli tesla plan records --space-id 1000 --plan-id 2000
bytedcli tesla plan create --space-id 1000 --plan-name "sample plan" --psm example.psm --replay-env sample_env --execute
bytedcli tesla plan update --space-id 1000 --plan-id 2000 --plan-name "updated sample plan" --execute
bytedcli tesla plan delete --space-id 1000 --plan-id 2000 --execute
bytedcli tesla plan trigger --space-id 1000 --plan-id 2000 --execute
```

## Auth

- `folder`、`env-tag`、`plan` 走 TeslaX apix，使用本地 bytedcli ByteCloud JWT，同时发送 `Authorization` 与 `X-Jwt-Token`。
- `report list` / `report case` 走 TeslaX OpenAPI gateway，使用 `--bearer-token "<bearer-token>"`。
- 多环境通过 `--env cn|boe|i18n|zg` 选择，对应 host 由 CLI 维护。

## Plan Notes

- `tesla plan create` 创建 TeslaX-only 计划，默认写入 `enable_ftf=false`、`enable_tesla=true`、`platform=teslax`。
- `--payload` 可补充深层 IDL 字段，例如 `psm_exec_params`、`notify_config_json`、`advanced_filter_group_list`。
- `create`、`update`、`delete`、`trigger` 都是写操作，必须显式传 `--execute`。

## References

- [Plan CRUD](plan/plan-crud.md)
- [Plan IDL](plan/plan-api-idl.md)
- [Plan Scaffold](plan/plan-scaffold-guide.md)
- [Report OpenAPI](report/report-openapi.md)
