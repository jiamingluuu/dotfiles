---
name: bytedance-bytetask
description: "Operate ByteTask scheduler (webcast.platform.scheduler / webcast.scheduler.job) read-only queries via bytedcli: query projects/tasks, list scheduling records (Record/MapRecord/TaskRecord), find failed LogID, look up tasks by business PSM, resolve cron expressions, inspect debug status. Use when tasks mention ByteTask, 调度平台, webcast.platform.scheduler, 调度任务排障, LogID 查调度结果, Cron 预测, Debug 状态."
---

# ByteTask (bytedcli)

ByteTask 调度系统控制面**只读运维** Skill。底层通过 bytedcli 复用 ByteCloud JWT 鉴权，走字节云接口测试平台的泛化 RPC 调用，无需任何自建鉴权脚本。

- 控制面 PSM：`webcast.platform.scheduler`（CN）
- 执行层 PSM：`webcast.scheduler.job`（仅 `debug-status`）

## 如何调用 bytedcli

```bash
# 推荐方式：先全局安装，后续直接调用 bytedcli
NPM_CONFIG_REGISTRY=http://bnpm.byted.org npm install -g @bytedance-dev/bytedcli@latest
bytedcli --help
bytedcli <command> [options]
```

```bash
# Fallback：仅在无法全局安装时使用 npx 临时执行
NPM_CONFIG_REGISTRY=http://bnpm.byted.org npx -y @bytedance-dev/bytedcli@latest <command> [options]
```

- 默认使用全局安装的 `bytedcli ...`。
- 仅当目标环境完全无法 `npm install -g` 时，才把示例里的 `bytedcli` 替换为 `NPM_CONFIG_REGISTRY=http://bnpm.byted.org npx -y @bytedance-dev/bytedcli@latest`。

## 只读边界（必读）

- 本 Skill 不提供任何写入或变更状态能力。`bytetask` 命令树只暴露 9 个只读子命令，底层 API 层维护只读方法白名单，任何写方法（`UpdateProject`、`UpdateTask`、`Debug`、`ControlTask`、`ReRun`、`StopJob`、`Review`、`ResetMqTriggerOffset` 等）都会被拒绝。
- 当用户输入出现创建、更新、修改、删除、暂停、恢复、重跑、停止、审核、重置位点、触发 Debug、变更 Cron / Executor / 重试 / 限流 / 订阅人等诉求时，必须打断并明确提示：当前 ByteTask skill 只提供只读查询能力；如需变更配置或状态，请到 ByteTask 平台界面或走正式变更流程。
- 拒绝写操作后，可按用户需要提供只读查询辅助。

## 前置条件与鉴权

- 鉴权完全复用 bytedcli 的 ByteCloud JWT 链路，无需手动粘贴 JWT、无需自建 Python 脚本：
  - 优先环境变量 `BYTEDCLI_USER_CLOUD_JWT` / `AIME_USER_CLOUD_JWT`
  - 其次本地 bytedcli 会话缓存（由 `bytedcli auth login` 写入）
  - 都不可用时自动触发 `bytedcli auth login` 飞书扫码登录
- 首次使用本地终端可先执行 `bytedcli auth login`；Aime 环境通常已注入 JWT，无需扫码。
- 站点通过全局 `--site` 或 `BYTEDCLI_CLOUD_SITE` 切换。ByteTask 当前支持 `cn` 与 `boe`；BOE 数据使用 `bytedcli --site boe bytetask ...`。
- 若返回提示无权限（`BYTETASK_PERMISSION_ERROR`），表示当前用户缺少 BAM / 接口测试平台对 `webcast.platform.scheduler` 的 PSM 调用权限，不是 ByteCloud JWT 登录失败。请到 BAM 平台 https://cloud.bytedance.net/bam/rd/webcast.platform.scheduler/ 申请 `psm=webcast.platform.scheduler` 的调用权限，申请理由写「使用 bytedcli skill」。

## When to use

- ByteTask / 调度平台 / `webcast.platform.scheduler` 的任何只读排障、定位
- 查 ByteTask 项目 / 任务 / 执行记录 / 调度记录 / 分片记录
- 用 LogID 查 ByteTask 调度结果
- 某业务 PSM 在 ByteTask 上有哪些任务
- 解析 Cron 表达式的下次触发时间
- 查看某 Executor 上一次 Debug 状态

如果用户意图同时包含查询和写操作，先拒绝写操作，只执行明确的只读查询部分。

## 子命令

| 子命令             | 对应方法         | PSM                | 用途                                              |
| ------------------ | ---------------- | ------------------ | ------------------------------------------------- |
| `project list`     | GetProject       | platform.scheduler | 按 ID/PSM/模糊词查询项目                          |
| `task list`        | GetTask          | platform.scheduler | 按项目/状态/触发类型/环境查询任务列表             |
| `record list`      | GetRecordList    | platform.scheduler | 按 TaskID/状态/LogID/时间区间查询执行记录         |
| `record get`       | GetRecord        | platform.scheduler | 按 ID 查询单条记录详情                            |
| `map-record list`  | GetMapRecordList | platform.scheduler | 查询分片调度记录                                  |
| `task-record list` | GetTaskRecord    | platform.scheduler | 按 RecordID/LogID/Key 查询任务记录组              |
| `cron-times get`   | GetCronTimes     | platform.scheduler | 解析 Cron 表达式，返回若干次预计触发时间          |
| `task-by-psm list` | GetTaskByPsm     | platform.scheduler | 按业务 PSM 反查依赖的所有调度任务                 |
| `debug-status get` | GetDebugStatus   | scheduler.job      | 查询某 Executor 上一次 Debug 的状态 / LogID / Pod |

执行任何子命令前，可先看一遍 `bytedcli bytetask <resource> <action> --help` 确认参数语义。详细字段与枚举见 `references/api-reference.md`。

## 常用命令

```bash
# 1) 查名字里带 "live" 的项目
bytedcli bytetask project list --fuzzy demo --page-size 20

# 2) 查项目下运行中的任务
bytedcli bytetask task list --project-id 12345 --task-status running --page-size 50

# 3) 用 LogID 查某 task 的执行记录
bytedcli bytetask record list --task-id 67890 --log-id 20260309184054DEMOLOGID

# 4) 查最近 1 小时该任务执行失败的记录（毫秒时间戳）
bytedcli bytetask record list --task-id 67890 --job-status fail \
  --from-time 1700000000000 --to-time 1700003600000

# 5) 单条记录详情
bytedcli bytetask record get --id 99999

# 6) 任务记录组（一次执行可能跨多个 executor）
bytedcli bytetask task-record list --record-id <RecordID> --task-id 67890

# 7) 查某 Executor 上一次 Debug 状态
bytedcli bytetask debug-status get --task-id 67890 --executor-id 11

# 8) 业务 PSM 反查依赖的所有 ByteTask 任务
bytedcli bytetask task-by-psm list --psm demo.live.sample

# 9) Cron 表达式预测：每天 0 点
bytedcli bytetask cron-times get --expression "0 0 * * *"

# 10) 查看任务完整配置（原始网关响应）
bytedcli bytetask task list --id 67890 --raw
```

## 输出格式

- 默认文本输出业务返回的 `data` 字段摘要。
- 加 `--raw` 可看到网关层完整响应（含 `error_code`、`log_id`、`has_permission` 等）。
- 结构化输出加全局 `--json`，必须放在子命令前，例如 `bytedcli --json bytetask project list --fuzzy demo`。

## References

以下文件随 `skills/bytedance-bytetask/` 源 skill 一起维护，可直接按相对路径读取：

- `../../invocation.md`：bytedcli 通用调用方式、站点切换、JSON 输出
- `references/bytetask.md`：命令速查、常用示例与只读边界
- `references/api-reference.md`：各只读接口的请求字段、返回结构与枚举速查
- `../../troubleshooting.md`：常见错误与处理方式
