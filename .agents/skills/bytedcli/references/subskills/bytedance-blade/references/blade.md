# Blade Notes

## Command surface

当前 Blade domain 提供 task 查询、创建、补数据、更新命令与 resource 预检查命令：

```bash
bytedcli --site i18n-bd blade task get --id sample-task-id
bytedcli blade task list --region mycis --owner demo.owner --project-id demo-project-id --task-name demo
bytedcli blade task list --region mycis --owner demo.owner --project-id demo-project-id --create-status created --task-type data-sync
bytedcli blade task operation list --region mycis --id sample-task-id --project-id demo-project-id
bytedcli blade task project list --region mycis --project-id demo-project-id
bytedcli blade task project get --region mycis --project-id demo-project-id
bytedcli blade task get --region mycis --id sample-task-id
bytedcli blade resource precheck --region mycis --project-id demo-project-id --resource-id example_db.example_table --resource-region 102 --auth-object demo.psm
bytedcli blade task create --region mycis --payload-file ./blade-task-create.json --dry-run
bytedcli blade task backtrack --region mycis --id sample-task-id --user-id demo.user --rps 5000 --dry-run
bytedcli blade task update --region mycis --id sample-task-id --payload-file ./blade-task-update.json --dry-run
```

## URL to CLI

Blade 控制台 URL 常见格式：

```text
https://blade.byteintl.net/resource/task/<taskId>
https://blade.byteintl.net/resource/task/create?project=<projectId>
```

CLI 参数映射：

- 路径里的 `<taskId>` 对应 `--id`
- `mycis` 任务可直接传 `--region mycis`，CLI 会自动映射到 `i18n-bd`
- 未显式传 region 时，站点默认建议 `--site i18n-bd`
- 列表过滤条件映射为 `--task-name` / `--owner` / `--project-id` / `--create-status` / `--task-type` / `--page` / `--page-size`
- 任务操作记录映射为 `blade task operation list --id <taskId> --project-id <projectId>`
- 创建页 URL 的 `project` query 可用于 `blade task project list --project-id` 或 `blade task project get --project-id`
- 创建页资源权限预检查对应 `blade resource precheck --project-id`
- 创建任务对应 `blade task create --payload-file ./blade-task-create.json --dry-run`
- backtrack / 补数据 curl 对应 `blade task backtrack --id <taskId> --user-id <userId> --rps <rps> --dry-run`
- 编辑页或抓包回放场景，更新 body 建议放到 `--payload-file`

示例：

```bash
bytedcli --site i18n-bd blade task get --id sample-task-id
bytedcli blade task list --region mycis --owner demo.owner --project-id demo-project-id --task-name demo
bytedcli blade task list --region mycis --owner demo.owner --project-id demo-project-id --create-status created --task-type data-sync
bytedcli blade task operation list --region mycis --id sample-task-id --project-id demo-project-id
bytedcli blade task project list --region mycis --project-id demo-project-id
bytedcli blade task project get --region mycis --project-id demo-project-id
bytedcli blade task get --region mycis --id sample-task-id
bytedcli blade resource precheck --region mycis --project-id demo-project-id --resource-id example_db.example_table --resource-region 102 --auth-object demo.psm
bytedcli blade task create --region mycis --payload-file ./blade-task-create.json --dry-run
bytedcli blade task backtrack --region mycis --id sample-task-id --user-id demo.user --rps 5000 --dry-run
bytedcli blade task update --region mycis --id sample-task-id --payload-file ./blade-task-update.json --dry-run
```

## List tasks

- `blade task list` 对应 `POST /v1/des_controller/data_sync_tasks/list`
- 请求体中的分页字段固定映射为 `page.page_num` / `page.page_size`
- 已验证 `--task-name`、`--owner`、`--project-id`、`--create-status`、`--task-type` 可直接覆盖浏览器列表页常见查询
- 当前已验证的公共枚举是 `--create-status created` 与 `--task-type data-sync`

示例：

```bash
bytedcli blade task list --region mycis --owner demo.owner --project-id demo-project-id
bytedcli blade task list --region mycis --owner demo.owner --project-id demo-project-id --create-status created --task-type data-sync
bytedcli blade task list --region mycis --task-name demo --page 1 --page-size 20
```

## List task operations

- `blade task operation list` 对应 `GET /v1/des_controller/data_sync_tasks/<taskId>/operations`
- `--project-id` 只用于构造任务页 Referer：`/resource/task/<taskId>?project=<projectId>`
- 返回 `taskId` / `projectId` 与完整 `raw` payload

示例：

```bash
bytedcli blade task operation list --region mycis --id sample-task-id --project-id demo-project-id
bytedcli --site i18n-bd --json blade task operation list --id sample-task-id
```

## Get task project metadata

- `blade task project list` 对应 `GET /v1/des_controller/data_sync_tasks/projects`
- `blade task project get` 对应 `GET /v1/des_controller/data_sync_tasks/projects/<projectId>`
- `blade task project list` 的 `--project-id` 只用于构造创建页 Referer
- `blade task project get` 优先使用语义 flag `--scene create-page|btube-edit-target`；默认场景是 `create-page`
- `--resource-type` / `--task-scene` 仍保留为高级 backend override，仅在浏览器抓包显示其他 numeric code 时使用
- `blade task project list` 返回 `projectId` 与完整 `raw` payload
- `blade task project list` / `blade task operation list` 若后端返回分页字段，JSON 输出会额外提升 `page_info`
- `blade task project get` 返回 `projectId` / `scene` / `resourceType` / `taskScene` 与完整 `raw` payload

示例：

```bash
bytedcli blade task project list --region mycis --project-id demo-project-id
bytedcli blade task project get --region mycis --project-id demo-project-id
bytedcli --site i18n-bd --json blade task project get --project-id demo-project-id
```

## Precheck resource privilege

- `blade resource precheck` 对应 `POST /v1/des_controller/resource/precheck`
- 请求体字段映射：`--resource-id -> resource_id`、`--resource-region -> region`、`--auth-object -> auth_objects[]`
- 默认 `apply_type=all` 与 `auth_type=psm`，可用 `--apply-type` / `--auth-type` 覆盖
- `--region mycis` 只用于 Blade 鉴权站点映射；请求体里的 numeric `region` 使用 `--resource-region`

示例：

```bash
bytedcli blade resource precheck --region mycis --project-id demo-project-id \
  --resource-id example_db.example_table \
  --resource-region 102 \
  --auth-object demo.psm
```

## Create task

- `blade task create` 对应 `POST /v1/des_controller/data_sync_tasks`
- 创建 payload 建议直接保存浏览器抓包里的 JSON body，再通过 `--payload-file` 传入
- 这是写操作：必须先 `--dry-run`，确认后再用 `--yes`
- 如果 payload 内带 `data_sync_task.basic_info.btube_project_id`，CLI 会自动构造 `/resource/task/create?project=<projectId>` Referer

推荐顺序：

```bash
bytedcli blade task create --region mycis \
  --payload-file ./blade-task-create.json \
  --dry-run

bytedcli blade task create --region mycis \
  --payload-file ./blade-task-create.json \
  --yes
```

## Backtrack tasks

- 单个 `--id` 对应 `POST /v1/des_controller/data_sync_tasks/<taskId>/backtrack`，`x-api-name=DesControllerService.CreateBacktrackTask`
- 多个 `--id` 对应 `POST /v1/des_controller/data_sync_tasks/backtrack`，`x-api-name=DesControllerService.BatchCreateBacktrackTask`
- 单任务请求体生成：`user_id`、`backtrack_type:0`、`full_backtrack_conf.rps`
- 批量请求体生成：`task_id_list`、`user_id`、`full_backtrack_conf.rps`
- `--id` 可重复或逗号分隔；单个 ID 走单任务接口，多个 ID 走批量接口
- `--user-id` 映射为请求体 `user_id`
- `--rps` 映射为请求体 `full_backtrack_conf.rps`，默认 `5000`
- 这是写操作：必须先 `--dry-run`，确认后再用 `--yes`
- 不要把浏览器抓包里的 cookie、JWT 或完整 header 写入命令；认证继续复用 bytedcli 的 Blade 认证链路

推荐顺序：

```bash
bytedcli blade task backtrack --region mycis \
  --id sample-task-id \
  --user-id demo.user \
  --rps 5000 \
  --dry-run

bytedcli blade task backtrack --region mycis \
  --id sample-task-id \
  --user-id demo.user \
  --rps 5000 \
  --yes
```

## Update task

- `blade task update` 对应 `PUT /v1/des_controller/data_sync_tasks/<taskId>`
- 更新 payload 建议直接保存浏览器抓包里的 JSON body，再通过 `--payload-file` 传入
- BTube task 的 edit/update 不要直接把 `blade task get --json` 里的 `raw.data_sync_task` 当成 update body。浏览器实际提交的是扁平 payload，至少包含 `task_name`、`description`、`owner`、`dorado_run_queue`、`monitor_config`、`updated_source_info`、`updated_target_info`、`btube_project_id`、`target_db_name`
- 字段变更时，修改的是 `updated_source_info.column_list` 与 `updated_target_info.column_list`；若目标表 schema 受影响，通常还要先对目标表执行 `resource precheck`，并用 `task project get --project-id <projectId> --scene btube-edit-target` 拉编辑页目标资源元数据
- 这是写操作：必须先 `--dry-run`，确认后再用 `--yes`

推荐顺序：

```bash
bytedcli blade task update --region mycis --id sample-task-id \
  --payload-file ./blade-task-update.json \
  --dry-run

bytedcli blade task update --region mycis --id sample-task-id \
  --payload-file ./blade-task-update.json \
  --yes
```

## Authentication summary

- 首选：`blade.byteintl.net` 站点 cookie + fresh `ByteCloud JWT`
- `--region mycis` 会自动走 `i18n-bd` 站点获取鉴权材料
- 兜底：Titan Passport cookie
- 无 cookie 也可直接请求，但前提是 JWT 仍然有效
- 如果命中 `code=82000` 或 `redirect_url=/auth/api/v1/jwt`，优先判断 JWT 是否过期

建议命令：

```bash
bytedcli --site i18n-bd auth login --session
bytedcli --site i18n-bd blade task get --id sample-task-id
```

纯 JWT 自动化场景：

```bash
export BYTEDCLI_USER_CLOUD_JWT="sample-fresh-jwt"
bytedcli --site i18n-bd blade task get --id sample-task-id
```

## Output

`blade task get` 与 `blade task list` 的文本模式 / JSON 顶层会优先暴露这些字段：

- `id`
- `name`
- `status`
- `taskType`
- `projectId`
- `owner`
- `region`
- `sourceRegion`
- `targetRegion`
- `sourceDb`
- `sourceTable`
- `targetDb`
- `targetTable`
- `consoleUrl`

`--json` 模式仍然走标准输出 envelope：`{ status, data, ... }`。下面这些字段约定位于 `data` 内；完整后端响应仍保留在 `raw` 里。

字段语义说明：

- `taskType` 已从后端原始值归一化为语义枚举（当前已验证 `data-sync`）
- `createStatus` 已从后端原始值归一化为语义枚举（当前已验证 `created`）
- 原始数值会保留在 `taskTypeCode` / `createStatusCode`
- `executeStatus` 当前仍是后端原始 code 字符串，尚未在 CLI 层语义化
- 对既有 `blade task get --json` 消费方，`data.taskType` 现在是语义枚举；若只需要当前已验证的 Blade numeric mapping，可读 `data.taskTypeCode`（当前 `data-sync -> 2`）。原始字符串形态如 `data_sync` 当前不再单独保留

`blade task list` 额外会暴露：

- `page_info.total_count`
- `page_info.page_num`
- `page_info.page_size`
- `createStatus`
- `createStatusCode`
- `executeStatus`
- `taskTypeCode`

`blade task operation list` 额外会暴露：

- `taskId`
- `projectId`
- `raw`

`blade task project list` 额外会暴露：

- `projectId`
- `raw`

`blade task project get` 额外会暴露：

- `projectId`
- `resourceType`
- `taskScene`
- `raw`

`blade resource precheck` 额外会暴露：

- `request`
- `raw`

`blade task create` 的输出约定：

- `--dry-run`：返回 `dry_run: true` 与 `request`
- `--yes`：返回 `request` 与后端 `response`

`blade task backtrack` 的输出约定：

- `--dry-run`：返回 `dry_run: true` 与 `request`
- `--yes`：返回 `request` 与后端 `response`
- `request.mode` 标识 `single` 或 `batch`
- 单任务时 `request.payload.backtrack_type` 固定为 `0`
- 批量时 `request.payload.task_id_list` 是最终提交的 task ID 列表
- `request.payload.user_id` 是最终提交的用户 ID
- `request.payload.full_backtrack_conf.rps` 是最终提交的 RPS

`blade task update` 的输出约定：

- `--dry-run`：返回 `dry_run: true` 与 `request`
- `--yes`：返回 `request` 与后端 `response`
