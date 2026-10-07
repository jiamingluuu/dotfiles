# Chronos

## Region routing

Chronos data is isolated by Region. `--site` selects the CN or BOE control plane, while the mandatory global `--vregion` selects the concrete scheduler deployment and host. Missing Region must be clarified with the user; there is no default and no automatic all-Region query.

| `--site` | Required `--vregion`                                                   |
| -------- | ---------------------------------------------------------------------- |
| `cn`     | `China-North`, `China-East`, `China-Pay`, `China-Pay2`, `China-North6` |
| `boe`    | `China-BOE`, `China-BOE2`                                              |

```bash
# List namespaces
bytedcli --site cn --vregion China-East chronos namespace list --namespace-tab ALL
bytedcli --site boe --vregion China-BOE2 chronos namespace list --namespace-tab MY --name demo-namespace --page 2 --page-size 50

# Get namespace detail
bytedcli --site cn --vregion China-North chronos namespace get --namespace-id demo-namespace

# List tasks under a namespace
bytedcli --site cn --vregion China-North chronos task list --namespace-id demo-namespace --task-tab ALL --task-type GENERAL
bytedcli --site boe --vregion China-BOE2 chronos task list --namespace-id demo-namespace --task-tab MY --task-type DYNAMIC_TREE --name demo-task --page 2 --page-size 20

# Get task detail
bytedcli --site cn --vregion China-North6 chronos task get --task-id demo-task
bytedcli --site boe --vregion China-BOE2 chronos task get --task-id demo-task

# List task modify records
bytedcli --site cn --vregion China-East chronos task modify-record list --task-id demo-task

# Executor config reads
bytedcli --site cn --vregion China-North chronos executor list --executor-type HTTP
bytedcli --site boe --vregion China-BOE2 chronos executor list --name demo-executor --executor-tab MY --page 2 --page-size 20
bytedcli --site cn --vregion China-East chronos executor get --executor-id demo-executor

# Sharding config reads
bytedcli --site cn --vregion China-North chronos sharding list --sharding-type HTTP
bytedcli --site boe --vregion China-BOE2 chronos sharding list --name demo-sharding --sharding-tab MY --page 2 --page-size 20
bytedcli --site cn --vregion China-Pay chronos sharding get --sharding-id demo-sharding

# Job records
bytedcli --site cn --vregion China-East chronos job record list --task-id demo-task --status FAILURE
bytedcli --site boe --vregion China-BOE2 chronos job record list --task-id demo-task --start-time '2026-01-01 00:00:00' --end-time '2026-01-02 00:00:00'
bytedcli --site cn --vregion China-North chronos job sharding-record list --job-id demo-job

# Update a task safely
bytedcli --site cn --vregion China-North chronos task update --task-id demo-task --owner demo-user
bytedcli --site boe --vregion China-BOE2 chronos task update --task-id demo-task --namespace-id demo-namespace --alarm-switch true --alarm-people demo-user-a,demo-user-b --alarm-group demo-group

# JSON output
bytedcli --json --site cn --vregion China-North chronos namespace list --namespace-tab MY_FOLLOW
bytedcli --json --site cn --vregion China-North chronos task list --namespace-id demo-namespace --task-tab MY_FOLLOW --task-type GENERAL
bytedcli --json --site boe --vregion China-BOE2 chronos task get --task-id demo-task
bytedcli --json --site cn --vregion China-East chronos job record list --task-id demo-task --status FAILURE
```

## Command surface

- `chronos namespace list`
  - 支持分页获取命名空间
  - 关键参数：`--namespace-tab`、`--name`、`--page`、`--page-size`
- `chronos namespace get`
  - 按 `namespace_id` 获取命名空间详情
  - 必填参数：`--namespace-id`
- `chronos task list`
  - 按 `namespace_id` 分页获取任务列表
  - 关键参数：`--namespace-id`、`--task-tab`、`--task-type`、`--name`
- `chronos task get`
  - 按 `task_id` 获取任务详情
  - 必填参数：`--task-id`
- `chronos task modify-record list`
  - 按 `task_id` 获取任务变更记录
  - 必填参数：`--task-id`
- `chronos executor list`
  - 分页获取 executor 配置
  - 关键参数：`--executor-type`、`--executor-tab`、`--name`、`--page`、`--page-size`
- `chronos executor get`
  - 按 `executor_id` 获取 executor 详情
  - 必填参数：`--executor-id`
- `chronos sharding list`
  - 分页获取 sharding 配置
  - 关键参数：`--sharding-type`、`--sharding-tab`、`--name`、`--page`、`--page-size`
- `chronos sharding get`
  - 按 `sharding_id` 获取 sharding 详情
  - 必填参数：`--sharding-id`
- `chronos job record list`
  - 按 `task_id` 分页获取任务运行记录
  - 关键参数：`--task-id`、`--status`、`--start-time`、`--end-time`、`--job-ids`、`--page`、`--page-size`
- `chronos job sharding-record list`
  - 按 `job_id` 或 `task_id` 分页获取分片 job 记录
  - 关键参数：`--job-id`、`--task-id`、`--status`、`--start-time`、`--end-time`、`--page`、`--page-size`
- `chronos task update`
  - 按 `task_id` 安全更新任务
  - 只允许更新：`owner`、`alarm_switch`、`alarm_people`、`alarm_group`
  - `--owner` 支持逗号分隔多值
  - `--alarm-people` 支持逗号分隔多值
  - `--alarm-group` 只允许单值
  - 可选参数：`--namespace-id`

## Supported control-plane reads

以下 Chronos 控制面读接口已暴露为可执行 bytedcli 命令。使用这些命令直接查询；不要在 skill 中调用隐藏/raw API。

| 需求                      | 上游路由                             | CLI 形态                                                                                         |
| ------------------------- | ------------------------------------ | ------------------------------------------------------------------------------------------------ |
| 按 ID 获取 namespace 详情 | `GET /scheduler/namespace/get`       | `chronos namespace get --namespace-id <id>`                                                      |
| 分页查询 executor         | `POST /scheduler/executor/list`      | `chronos executor list --name <name> --executor-type <type> --executor-tab <tab>`                |
| 按 ID 获取 executor 详情  | `GET /scheduler/executor/get`        | `chronos executor get --executor-id <id>`                                                        |
| 分页查询 sharding 配置    | `POST /scheduler/sharding/list`      | `chronos sharding list --name <name> --sharding-type <type> --sharding-tab <tab>`                |
| 按 ID 获取 sharding 详情  | `GET /scheduler/sharding/get`        | `chronos sharding get --sharding-id <id>`                                                        |
| 查询任务运行记录          | `GET /scheduler/job/record`          | `chronos job record list --task-id <id> --status <status> --start-time <time> --end-time <time>` |
| 查询分片 job 记录         | `GET /scheduler/job/sharding_record` | `chronos job sharding-record list --job-id <id> --task-id <id>`                                  |
| 查询任务变更记录          | `GET /scheduler/task/modify_record`  | `chronos task modify-record list --task-id <id>`                                                 |

命令约束：

- 使用全局 `--site cn|boe` 选择控制面，使用必填语义的全局 `--vregion` 选择具体 Chronos Region。Region 会切换请求 host，不是普通查询过滤条件；缺失时先询问用户。
- `executor list` 支持 `--executor-type UNKNOWN|HTTP|RPC|FAAS|GO_PLUGIN|CRONJOB` 和 `--executor-tab ALL|MY|MY_FOLLOW`。
- `sharding list` 支持 `--sharding-type NOT|STATIC|RPC|HTTP|GO_PLUGIN` 和 `--sharding-tab ALL|MY|MY_FOLLOW`。
- `job record list` 与 `job sharding-record list` 支持 `--status ALL|SUCCESS|FAILURE|RUNNING|PARTIAL_SUCCESS|CANCELED|WAIT_FOR_EXECUTE`。
- 即使上游字段是 `page_index` / `page_size`，CLI 也使用 `--page` / `--page-size`。
- 文本输出聚焦 ID、名称、owner/status 与关键配置字段；`--json` 保留结构化响应。

## Write capability boundary

Chronos 写能力在本 skill 中是白名单，不是开放式自然语言操作。

- 唯一支持的 Chronos 写命令是 `chronos task update`。
- `chronos task update` 只允许更新 `owner`、`alarm_switch`、`alarm_people`、`alarm_group`。
- Skill 开发者不允许在本 skill 中添加或透出其他 Chronos 写能力，除非对应 bytedcli 命令已经实现、评审、测试，并被明确验收为支持能力。
- 不允许为了满足自然语言写请求而编造命令、调用隐藏/raw Chronos API、发临时 HTTP 请求，或组合脚本绕过 CLI 能力边界。
- 用户要求创建、删除、重跑、取消、发布、切换任务开关、编辑 executor/sharding 配置，或任何不属于 `chronos task update` 白名单字段的写操作时，必须说明当前 skill 不支持该写能力。
- 只有当用户明确要求更新白名单字段并提供必要参数时，才能执行 `chronos task update`；表达不清时先确认。

## Output highlights

- `chronos namespace list`
  - 命名空间 ID
  - 名称
  - owner / creator
- `chronos task list`
  - task ID
  - task 名称
  - owner
  - namespace
- `chronos task get`
  - HTTP 调度链接
  - HTTP Method
  - 报警接收人
  - 报警组
  - 监控链接
- `chronos executor list/get`
  - executor ID / 名称 / 类型
  - owner / creator
  - HTTP / RPC 关键配置
- `chronos sharding list/get`
  - sharding ID / 名称 / 类型
  - owner / creator
  - HTTP / RPC / 分片字段关键配置
- `chronos job record list` / `chronos job sharding-record list`
  - job ID
  - task ID / task 名称
  - 状态
  - log ID / log URL
- `chronos task modify-record list`
  - 变更记录中的任务字段快照
- `chronos task update`
  - 更新后返回最终任务详情
  - 输出本次真正修改的字段和权限校验结果
- `--json` 输出会携带后端 `header`，并返回补齐后的 namespace/task/detail 字段；`task get` 额外包含 `executor`、`sharding`、`alarm_list`、`extra`，默认不返回 `raw`

## Notes

- 当前控制面站点只支持 `cn` 与 `boe`
- `--site cn` 支持 `China-North`、`China-East`、`China-Pay`、`China-Pay2`、`China-North6`
- `--site boe` 支持 `China-BOE`、`China-BOE2`
- `--vregion` 缺失时返回 `CHRONOS_REGION_REQUIRED`；Agent 应先反问用户，不默认选区，也不自动查询全部 Region
- 查询不到资源时核对 `--vregion`；不同 Region 的 namespace/task/job 数据彼此隔离
- `chronos namespace list --namespace-tab` 支持 `ALL`、`MY`、`MY_FOLLOW`，默认 `ALL`
- `chronos namespace get` 必须显式传 `--namespace-id`
- `chronos task list --task-tab` 支持 `ALL`、`MY`、`MY_FOLLOW`，默认 `ALL`
- `chronos task list --task-type` 支持 `UNKNOWN`、`GENERAL`、`DYNAMIC_TREE`，默认 `GENERAL`
- `chronos namespace list`、`chronos task list`、`chronos executor list`、`chronos sharding list`、`chronos job record list`、`chronos job sharding-record list` 未显式传分页参数时，默认使用 `page=1`、`page_size=20`
- `chronos task modify-record list` 必须显式传 `--task-id`
- `chronos executor get` 必须显式传 `--executor-id`
- `chronos sharding get` 必须显式传 `--sharding-id`
- `chronos job record list` 必须显式传 `--task-id`
- `chronos job sharding-record list` 必须显式传 `--job-id` 或 `--task-id` 中至少一个
- `chronos task get` 文本模式展示关键字段，`--json` 返回结构化字段且默认不暴露 `raw`
- `chronos task update` 会先调用 `task get` 和 `namespace list --namespace-tab MY`，确认当前账号对 namespace 有编辑权限后再发 PUT
- `chronos task update` 的入参会从 `task get` 的原始返回全量回填，只覆盖允许修改的字段，避免 overwrite 接口覆盖其它配置
- `chronos task update` 不支持更新 `switch`
- `chronos task update --alarm-group` 不能传逗号分隔的多个群；若需要切群，只保留一个目标群值
- 若先前在其他站点已登录，不代表 `boe` 一定已登录；切换到 `boe` 后优先执行 `bytedcli --site boe auth status`
