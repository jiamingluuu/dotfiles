---
name: bytedance-chronos
description: "Operate Chronos via bytedcli: list/get namespaces and tasks, inspect task details including HTTP scheduling URL and alarms, read executor/sharding configs, query job records and task modify records, and safely update only the existing task owner/alarm fields. Use when tasks mention Chronos, 调度任务, namespace, task_id, executor, sharding, job record, 运行记录, HTTP 调度链接, 报警接收人, or need region-specific Chronos lookup in China-North/China-East/China-Pay/China-Pay2/China-North6/China-BOE/China-BOE2. Make sure to use this skill whenever the user wants Chronos command guidance or agent routing, even if they only mention scheduler/task detail without saying 'Chronos'."
---

# Chronos (bytedcli)

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

- 分页列出 Chronos 命名空间
- 按 `namespace_id` 查询命名空间详情
- 按 `namespace_id` 查询任务列表
- 按 `task_id` 查询任务详情
- 安全更新任务 owner 和基础报警配置
- 获取 HTTP 调度链接、HTTP Method、报警接收人、报警组、监控链接
- 查询 executor 配置、sharding 配置、job 运行记录、分片 job 记录、任务变更记录
- 通过全局 `--site` + `--vregion` 选择 Chronos 控制面 Region，并确认认证状态

## 前置条件

- 按通用调用方式执行命令（含内网 registry）：`../../invocation.md`
- 需要鉴权的命令先登录：`bytedcli auth login`

> 执行前缀见 `../../invocation.md`；下面示例直接写 `bytedcli`。

## Quick start

Current Chronos commands are grouped under `chronos namespace`、`chronos task`、`chronos executor`、`chronos sharding`、`chronos job`. Chronos is physically split by Region; select it with the global `--site` and `--vregion` options.

| `--site` | Required `--vregion`                                                   |
| -------- | ---------------------------------------------------------------------- |
| `cn`     | `China-North`, `China-East`, `China-Pay`, `China-Pay2`, `China-North6` |
| `boe`    | `China-BOE`, `China-BOE2`                                              |

Each Region routes to an independent Chronos host. `--vregion` is mandatory: do not pick a default and do not fan out across all Regions. If the user has not specified a Region, ask which Region to query before running bytedcli.

```bash
bytedcli --site cn --vregion China-East chronos namespace list --namespace-tab ALL
bytedcli --site boe --vregion China-BOE2 chronos namespace list --namespace-tab MY --name demo-namespace --page 2 --page-size 50
bytedcli --site cn --vregion China-North chronos namespace get --namespace-id demo-namespace

bytedcli --site cn --vregion China-North chronos task list --namespace-id demo-namespace --task-tab ALL --task-type GENERAL
bytedcli --site boe --vregion China-BOE2 chronos task list --namespace-id demo-namespace --task-tab MY --task-type DYNAMIC_TREE --name demo-task --page 2 --page-size 20

bytedcli --site cn --vregion China-North6 chronos task get --task-id demo-task
bytedcli --site boe --vregion China-BOE2 chronos task get --task-id demo-task
bytedcli --site cn --vregion China-East chronos task modify-record list --task-id demo-task

bytedcli --site cn --vregion China-North chronos executor list --executor-type HTTP
bytedcli --site boe --vregion China-BOE2 chronos executor list --name demo-executor --executor-tab MY --page 2 --page-size 20
bytedcli --site cn --vregion China-East chronos executor get --executor-id demo-executor

bytedcli --site cn --vregion China-North chronos sharding list --sharding-type HTTP
bytedcli --site boe --vregion China-BOE2 chronos sharding list --name demo-sharding --sharding-tab MY --page 2 --page-size 20
bytedcli --site cn --vregion China-Pay chronos sharding get --sharding-id demo-sharding

bytedcli --site cn --vregion China-East chronos job record list --task-id demo-task --status FAILURE
bytedcli --site boe --vregion China-BOE2 chronos job record list --task-id demo-task --start-time '2026-01-01 00:00:00' --end-time '2026-01-02 00:00:00'
bytedcli --site cn --vregion China-North chronos job sharding-record list --job-id demo-job

bytedcli --site cn --vregion China-North chronos task update --task-id demo-task --owner demo-user
bytedcli --site boe --vregion China-BOE2 chronos task update --task-id demo-task --namespace-id demo-namespace --alarm-switch true --alarm-people demo-user-a,demo-user-b --alarm-group demo-group

# machine-readable output
bytedcli --json --site cn --vregion China-North chronos namespace list --namespace-tab MY_FOLLOW
bytedcli --json --site boe --vregion China-BOE2 chronos task get --task-id demo-task
bytedcli --json --site cn --vregion China-East chronos job record list --task-id demo-task --status FAILURE
```

## Supported control-plane reads

The first-batch Chronos control-plane read APIs below are exposed as executable bytedcli commands. Use these commands directly; do not call hidden/raw APIs from this skill.

| Need                       | Upstream route                       | CLI surface                                                                                      |
| -------------------------- | ------------------------------------ | ------------------------------------------------------------------------------------------------ |
| Get namespace detail by ID | `GET /scheduler/namespace/get`       | `chronos namespace get --namespace-id <id>`                                                      |
| List executors             | `POST /scheduler/executor/list`      | `chronos executor list --name <name> --executor-type <type> --executor-tab <tab>`                |
| Get executor detail by ID  | `GET /scheduler/executor/get`        | `chronos executor get --executor-id <id>`                                                        |
| List sharding configs      | `POST /scheduler/sharding/list`      | `chronos sharding list --name <name> --sharding-type <type> --sharding-tab <tab>`                |
| Get sharding detail by ID  | `GET /scheduler/sharding/get`        | `chronos sharding get --sharding-id <id>`                                                        |
| Query task job records     | `GET /scheduler/job/record`          | `chronos job record list --task-id <id> --status <status> --start-time <time> --end-time <time>` |
| Query sharding job records | `GET /scheduler/job/sharding_record` | `chronos job sharding-record list --job-id <id> --task-id <id>`                                  |
| Query task modify records  | `GET /scheduler/task/modify_record`  | `chronos task modify-record list --task-id <id>`                                                 |

Command notes:

- Use global `--site cn|boe` for the control plane and mandatory global `--vregion` for the concrete Chronos Region. Do not treat Region as a query filter: it selects a different host. If Region is absent, ask the user instead of executing a default or all-Region query.
- `executor list` supports `--executor-type UNKNOWN|HTTP|RPC|FAAS|GO_PLUGIN|CRONJOB` and `--executor-tab ALL|MY|MY_FOLLOW`.
- `sharding list` supports `--sharding-type NOT|STATIC|RPC|HTTP|GO_PLUGIN` and `--sharding-tab ALL|MY|MY_FOLLOW`.
- `job record list` and `job sharding-record list` support `--status ALL|SUCCESS|FAILURE|RUNNING|PARTIAL_SUCCESS|CANCELED|WAIT_FOR_EXECUTE`.
- Use `--page` / `--page-size` in CLI commands even though upstream fields are `page_index` / `page_size`.
- Text output focuses on IDs, names, owner/status, and key configuration fields; `--json` preserves structured response data.

## Write capability boundary

Chronos write/mutation support in this skill is intentionally narrow.

- The only supported Chronos write command is `chronos task update`.
- `chronos task update` only allows updating `owner`、`alarm_switch`、`alarm_people`、`alarm_group`.
- Skill developers must not add or document any other Chronos write capability in this skill unless the corresponding bytedcli command is implemented, reviewed, tested, and explicitly accepted as supported product behavior.
- Do not satisfy natural-language write requests by inventing commands, calling hidden/raw Chronos APIs, using ad hoc HTTP requests, or composing lower-level scripts.
- If a user asks to create/delete/rerun/cancel/deploy/switch a task, edit executor/sharding config, or perform any write that is not exactly covered by `chronos task update`, explain that this skill does not expose that write capability.
- Only run `chronos task update` when the user explicitly asks for one of the allowed fields and provides the required identifiers/options. If the user's wording is ambiguous, ask for confirmation before running the update.

## Notes

- `--json` 是全局参数，必须放在子命令前，例如 `bytedcli --json --site cn --vregion China-North chronos task get --task-id demo-task`
- `chronos namespace list` 会始终带 `--namespace-tab` 语义；可选值为 `ALL`、`MY`、`MY_FOLLOW`，默认 `ALL`
- `chronos namespace list --name <name>` 可按 namespace 名称过滤
- `chronos namespace get` 必须显式传 `--namespace-id`
- `chronos namespace list`、`chronos task list`、`chronos executor list`、`chronos sharding list`、`chronos job record list`、`chronos job sharding-record list` 未显式传分页参数时，默认 `--page 1 --page-size 20`
- 任务列表查询必须显式传 `--namespace-id`
- `chronos task list --task-tab` 支持 `ALL`、`MY`、`MY_FOLLOW`，默认 `ALL`
- `chronos task list --task-type` 支持 `UNKNOWN`、`GENERAL`、`DYNAMIC_TREE`，默认 `GENERAL`
- `chronos task list --name <name>` 可按 task 名称过滤
- `--json` 输出会携带后端 `header`，并返回更完整的 namespace/task/detail 字段；`chronos task get` 额外包含 `executor`、`sharding`、`alarm_list`、`extra`，默认不返回 `raw`
- 任务详情查询必须显式传 `--task-id`
- `chronos task modify-record list` 必须显式传 `--task-id`
- `chronos executor get` 必须显式传 `--executor-id`
- `chronos sharding get` 必须显式传 `--sharding-id`
- `chronos job record list` 必须显式传 `--task-id`
- `chronos job sharding-record list` 必须显式传 `--job-id` 或 `--task-id` 中至少一个
- 当前控制面站点只支持 `cn` 与 `boe`；全局 `--vregion` 是必填语义，缺失时 CLI 返回 `CHRONOS_REGION_REQUIRED`
- `--site cn` 支持 `China-North`、`China-East`、`China-Pay`、`China-Pay2`、`China-North6`
- `--site boe` 支持 `China-BOE`、`China-BOE2`
- 用户未给出 Region 时必须先反问，不要默认选择 `China-North` / `China-BOE`，也不要自动遍历全部 Region
- 常用别名会自动规范化，例如 `cn`/`huabei` → `China-North`、`hj`/`huadong` → `China-East`、`boe2` → `China-BOE2`；文档和自动化推荐使用规范全名
- `chronos task get` 的文本输出会聚焦关键字段；默认 JSON 也不暴露 `raw`
- `chronos task update` 只允许更新 `owner`、`alarm_switch`、`alarm_people`、`alarm_group`
- `chronos task update --owner` 支持逗号分隔的多人，例如 `demo-user-a,demo-user-b`
- `chronos task update --alarm-people` 支持逗号分隔的多人，例如 `demo-user-a,demo-user-b`
- `chronos task update --alarm-group` 只允许单值，不能传逗号分隔的多个群
- `chronos task update` 不支持更新 `switch`；若任务开关未生效，不要继续重试同一个 PUT 参数
- `chronos task update` 会先调用 `task get` 读取当前任务，再调用 `namespace list --namespace-tab MY` 校验当前账号是否对所属 namespace 有编辑权限
- `chronos task update` 发给后端的 PUT 请求体是从 `task get` 原始返回全量回填后再只覆盖允许字段，避免 overwrite 接口覆盖其它配置
- 遇到 `Not authenticated` / `AUTH_REQUIRED` 时，先为目标站点执行登录，再重试原命令

## References

- `../../invocation.md`
- `references/chronos.md`
- `../../troubleshooting.md`
