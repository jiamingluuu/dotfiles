---
name: bytedance-blade
description: "Inspect, create, backtrack, and update Blade data sync tasks via bytedcli: get/list tasks, query project metadata, precheck resource privileges, submit backtrack or update writes with `--dry-run` / `--yes`, and troubleshoot Blade auth on `blade.byteintl.net`. Use when tasks mention Blade, `blade.byteintl.net`, data sync tasks, backtrack/补数据, `des_controller`, or Blade console URLs."
---

# bytedcli Blade

## 如何调用 bytedcli

推荐：先全局安装一次，后续所有命令直接调用 `bytedcli`。

```bash
# 推荐方式：先全局安装，后续直接调用 bytedcli
NPM_CONFIG_REGISTRY=http://bnpm.byted.org npm install -g @bytedance-dev/bytedcli@latest
bytedcli <command> [options]
```

```bash
# Fallback：仅在无法全局安装时使用 npx 临时执行
NPM_CONFIG_REGISTRY=http://bnpm.byted.org npx -y @bytedance-dev/bytedcli@latest <command> [options]
```

## When to use

- 按 Blade task ID 查看单个 data sync task 详情
- 按 owner / project / task name 分页列出 Blade tasks
- 查询 Blade 创建页的 task project metadata
- 预检查创建任务时的 resource privilege
- 按 task ID 提交单个或批量 Blade backtrack / 补数据请求
- 按浏览器抓包 payload 回放或提交 Blade task update
- 从 `blade.byteintl.net/resource/task/<id>` 页面回到 CLI
- 从 `blade.byteintl.net/resource/task/create?project=<projectId>` 页面回到 CLI
- 确认任务的 `projectId`、owner、源/目标 region、db/table
- 排查 Blade 鉴权问题，尤其是 JWT 过期或页面态未准备好的场景

## 前置条件

- 使用通用调用方式：`../../invocation.md`
- Blade 国际站默认建议显式带 `--site i18n-bd`
- 如果已经知道任务在 `mycis`，可直接传 `--region mycis`，CLI 会自动映射到 `i18n-bd` 鉴权站点
- 认证优先使用 fresh `ByteCloud JWT`
- 如果需要先准备浏览器态，再执行：`bytedcli --site i18n-bd auth login --session`
- 如果只想走纯 JWT 模式，也可以直接提供 `BYTEDCLI_USER_CLOUD_JWT`

> 执行前缀见 `../../invocation.md`；下面示例直接写 `bytedcli`。

## Quick start

当前接入 `blade task get`、`blade task list`、`blade task operation list`、`blade task project list`、`blade task project get`、`blade resource precheck`、`blade task create`、`blade task backtrack` 与 `blade task update`。

```bash
# 直接按 task ID 查询
bytedcli --site i18n-bd blade task get --id sample-task-id

# 按 owner / project / task name 分页列出任务
bytedcli blade task list --region mycis --owner demo.owner --project-id demo-project-id --task-name demo

# 按创建状态 / 任务类型过滤
bytedcli blade task list --region mycis --owner demo.owner --project-id demo-project-id --create-status created --task-type data-sync

# 查询任务操作记录
bytedcli blade task operation list --region mycis --id sample-task-id --project-id demo-project-id

# 查询项目元数据；默认场景是 create-page
bytedcli blade task project list --region mycis --project-id demo-project-id
bytedcli blade task project get --region mycis --project-id demo-project-id --scene create-page

# 预检查创建任务时的资源权限
bytedcli blade resource precheck --region mycis --project-id demo-project-id \
  --resource-id example_db.example_table \
  --resource-region 102 \
  --auth-object demo.psm

# 直接用 region 推导站点
bytedcli blade task get --region mycis --id sample-task-id

# 需要完整 raw payload 时用 --json
bytedcli --site i18n-bd --json blade task get --id sample-task-id

# 创建前必须先 dry-run 预览请求体
bytedcli blade task create --region mycis \
  --payload-file ./blade-task-create.json \
  --dry-run

# 确认 dry-run 后，再加 --yes 真正创建
bytedcli blade task create --region mycis \
  --payload-file ./blade-task-create.json \
  --yes

# 单任务补数据 / backtrack 前必须先 dry-run 预览 endpoint、apiName、user_id 和 rps
bytedcli blade task backtrack --region mycis \
  --id sample-task-id \
  --user-id demo.user \
  --rps 5000 \
  --dry-run

# 确认 dry-run 后，再加 --yes 真正提交 backtrack
bytedcli blade task backtrack --region mycis \
  --id sample-task-id \
  --user-id demo.user \
  --rps 5000 \
  --yes

# 更新前必须先 dry-run 预览请求体
bytedcli blade task update --region mycis --id sample-task-id \
  --payload-file ./blade-task-update.json \
  --dry-run

# 确认 dry-run 后，再加 --yes 真正提交
bytedcli blade task update --region mycis --id sample-task-id \
  --payload-file ./blade-task-update.json \
  --yes

# 纯 JWT 模式：显式提供 fresh ByteCloud JWT
BYTEDCLI_USER_CLOUD_JWT="sample-fresh-jwt" \
  bytedcli --site i18n-bd blade task get --id sample-task-id
```

如果用户给的是 Blade 控制台 URL：

```text
https://blade.byteintl.net/resource/task/sample-task-id
```

则直接把路径里的 task ID 提出来即可：

```bash
bytedcli blade task get --region mycis --id sample-task-id
```

如果用户给的是任务列表页上下文，例如 owner / project / 模糊 task name 过滤条件：

```bash
bytedcli blade task list --region mycis --owner demo.owner --project-id demo-project-id --task-name demo
bytedcli blade task list --region mycis --owner demo.owner --project-id demo-project-id --create-status created --task-type data-sync
```

如果用户给的是创建页 URL：

```text
https://blade.byteintl.net/resource/task/create?project=demo-project-id
```

则直接使用 project 参数查询创建页项目元数据：

```bash
bytedcli blade task project list --region mycis --project-id demo-project-id
bytedcli blade task project get --region mycis --project-id demo-project-id
bytedcli blade resource precheck --region mycis --project-id demo-project-id \
  --resource-id example_db.example_table \
  --resource-region 102 \
  --auth-object demo.psm
bytedcli blade task create --region mycis --payload-file ./blade-task-create.json --dry-run
```

如果用户给的是 backtrack / 补数据 curl：

```bash
bytedcli blade task backtrack --region mycis \
  --id sample-task-id \
  --user-id demo.user \
  --rps 5000 \
  --dry-run
```

如果用户给的是编辑页 URL：

```text
https://blade.byteintl.net/resource/task/sample-task-id/edit?project=demo-project-id
```

则仍然用路径里的 task ID，更新 body 建议落到文件里再执行：

```bash
bytedcli blade resource precheck --region mycis --project-id demo-project-id \
  --resource-id demo_target_db.demo_target_table \
  --resource-region 102 \
  --auth-object blade.bsave.btube_flink

bytedcli blade task project get --region mycis --project-id demo-project-id \
  --scene btube-edit-target

bytedcli blade task update --region mycis --id sample-task-id \
  --payload-file ./blade-task-update.json \
  --dry-run
```

## Authentication

- CLI 会优先复用 `blade.byteintl.net` 的站点 cookie，并同时携带 fresh `X-Jwt-Token`
- `--region mycis` 会自动选择 `i18n-bd` 站点来换取 JWT 与 Titan cookie
- 如果站点 cookie 不可用，会继续尝试 Titan Passport cookie
- 即使 cookie 都不可用，只要当前 `ByteCloud JWT` 仍然有效，也允许直接请求 Blade 详情接口
- 运行期已验证：**过期 JWT** 常见返回是 `code=82000`，并带 `redirect_url=/auth/api/v1/jwt`
- 因此 Blade 鉴权排查时，先看 JWT 是否 fresh，再看站点页面态是否准备好

推荐顺序：

```bash
# 推荐：先刷新页面态 + JWT
bytedcli --site i18n-bd auth login --session

# 然后查询任务
bytedcli --site i18n-bd blade task get --id sample-task-id

# 或者直接按 region 查询
bytedcli blade task get --region mycis --id sample-task-id
```

如果调用方只维护自动化 JWT，不希望依赖 session：

```bash
export BYTEDCLI_USER_CLOUD_JWT="sample-fresh-jwt"
bytedcli --site i18n-bd blade task get --id sample-task-id
```

## Output

文本模式会优先展示这些归一化字段：

- `Task ID`
- `Name`
- `Status`
- `Type`
- `Project ID`
- `Owner`
- `Region`
- `Source Region` / `Target Region`
- `Source DB` / `Source Table`
- `Target DB` / `Target Table`
- `Console URL`

`--json` 模式仍然走标准输出 envelope：`{ status, data, ... }`。以下字段约定位于 `data` 内，同时保留完整 `raw` payload，适合继续补字段映射或和浏览器抓包对齐。

`blade task get` / `blade task list` 的字段约定：

- `taskType` 已从后端原始值归一化为语义枚举（当前已验证 `data-sync`）
- `createStatus` 已从后端原始值归一化为语义枚举（当前已验证 `created`）
- 原始数值会保留在 `taskTypeCode` / `createStatusCode`
- `executeStatus` 当前仍是后端原始 code 字符串，尚未在 CLI 层语义化
- 对既有 `blade task get --json` 消费方，`data.taskType` 现在是语义枚举；若只需要当前已验证的 Blade numeric mapping，可读 `data.taskTypeCode`（当前 `data-sync -> 2`）。原始字符串形态如 `data_sync` 当前不再单独保留

`blade task list` 的输出约定：

- 返回 `tasks` 与 `page_info`
- `tasks[].basic_info` 会归一化为顶层 `id` / `name` / `owner` / `projectId` / `sourceDb` / `targetDb`
- 顶层 `create_status` / `execute_status` 会归一化为 `createStatus` / `executeStatus`
- 当前已验证的公共枚举是 `--create-status created` 与 `--task-type data-sync`
- 原始数值会保留在 `createStatusCode` / `taskTypeCode`

`blade task operation list` 的输出约定：

- 对应 `GET /v1/des_controller/data_sync_tasks/<taskId>/operations`
- `--project-id` 只用于构造任务页 Referer
- JSON 输出包含 `taskId` / `projectId` 与完整 `raw` payload

`blade task project list` / `blade task project get` 的输出约定：

- `blade task project list` 对应 `GET /v1/des_controller/data_sync_tasks/projects`
- `blade task project get` 对应 `GET /v1/des_controller/data_sync_tasks/projects/<projectId>`
- `blade task project list` 的 `--project-id` 只用于构造创建页 Referer
- `blade task project get` 优先使用语义 flag `--scene create-page|btube-edit-target`；默认场景是 `create-page`
- `--resource-type` / `--task-scene` 仍保留为高级 backend override，仅在浏览器抓包显示其他 numeric code 时使用
- `blade task project list` 的 JSON 输出包含 `projectId` 与完整 `raw` payload
- `blade task project list` / `blade task operation list` 若后端返回分页字段，JSON 输出会额外提升 `page_info`
- `blade task project get` 的 JSON 输出包含 `projectId` / `scene` / `resourceType` / `taskScene` 与完整 `raw` payload

`blade resource precheck` 的输出约定：

- 对应 `POST /v1/des_controller/resource/precheck`
- 默认 `apply_type=all` 与 `auth_type=psm`
- `--resource-region` 对应请求体里的 numeric `region`，不要和用于站点鉴权映射的 `--region mycis` 混用
- JSON 输出包含 `request` 与后端完整 `raw` payload

`blade task create` 的输出约定：

- 对应 `POST /v1/des_controller/data_sync_tasks`
- 请求体建议直接保存浏览器抓包里的 JSON body，再通过 `--payload-file` 传入
- `--dry-run`：输出 `dry_run: true` 和 `request`
- `--yes`：输出 `request` 与后端 `response`
- 若 payload 内有 `data_sync_task.basic_info.btube_project_id`，CLI 会自动构造 `/resource/task/create?project=<projectId>` Referer

`blade task backtrack` 的输出约定：

- 单个 `--id` 对应 `POST /v1/des_controller/data_sync_tasks/<taskId>/backtrack`，`x-api-name=DesControllerService.CreateBacktrackTask`
- 多个 `--id` 对应 `POST /v1/des_controller/data_sync_tasks/backtrack`，`x-api-name=DesControllerService.BatchCreateBacktrackTask`
- 单任务请求体生成 `user_id`、`backtrack_type:0`、`full_backtrack_conf.rps`
- 批量请求体生成 `task_id_list`、`user_id`、`full_backtrack_conf.rps`
- `--user-id` 映射为请求体 `user_id`
- `--rps` 映射为请求体 `full_backtrack_conf.rps`，默认 `5000`
- `--dry-run`：输出 `dry_run: true` 和 `request`
- `--yes`：输出 `request` 与后端 `response`

`blade task update` 的输出约定：

- `--dry-run`：输出 `dry_run: true` 和 `request`
- `--yes`：输出 `request` 与后端 `response`
- BTube task 的 edit/update 不要直接把 `blade task get --json` 里的 `raw.data_sync_task` 当成 update body。浏览器实际提交的是扁平 payload，至少包含 `task_name`、`description`、`owner`、`dorado_run_queue`、`monitor_config`、`updated_source_info`、`updated_target_info`、`btube_project_id`、`target_db_name`
- 字段变更时，修改的是 `updated_source_info.column_list` 与 `updated_target_info.column_list`；若目标表 schema 受影响，通常还要先对目标表执行 `resource precheck`，并用 `task project get --scene btube-edit-target` 拉编辑页目标资源元数据

## Notes

- `--json` 是全局参数，必须放在 `blade` 前面，例如 `bytedcli --site i18n-bd --json blade task get --id sample-task-id`
- 当前内置 region 只支持 `mycis`
- 当前支持 `task get`、`task list`、`task operation list`、`task project list`、`task project get`、`resource precheck`、`task create`、`task backtrack` 与 `task update`；还没有 search / delete 能力
- `task create` / `task backtrack` / `task update` 是显式写操作：必须先 `--dry-run`，确认后再 `--yes`
- parser 会优先读取 `data_sync_task.basic_info`、`source_resource_config`、`target_resource_config` 的显式路径字段；如果某个任务仍有字段遗漏，优先查看 `raw`

## References

- `references/blade.md`
- `../../invocation.md`
