# XPA commands 参数详表

> 写命令一律 **dry-run by default**(不带 `--yes` 即打印 `[dry-run] ...` 后退出 0),加 `--yes` 才真发。没有 `--dry-run` flag、没有交互式 y/N 确认;CI 与 TTY 行为一致。

## 全局 XPA 选项

> **位置(commander 限制)**: 这组 `--xpa-*` 挂在 xpa 父命令上,**只能写在 `bytedcli xpa <这里> <subcmd>` 之间**。写在 `bytedcli` 后 `xpa` 前 / 叶子命令后都会 `error: unknown option --xpa-env`。位置不便时用对应环境变量(每个 flag 都有等价的 `BYTEDCLI_XPA_*` 环境变量)。

| 选项                  | 说明                                                                                                                                                                                 |
| --------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `--xpa-env <env>`     | XPA 业务环境：`boe`/`ppe`/`prod`（默认 `prod`）。同 `BYTEDCLI_XPA_ENV` 环境变量。**与 bytedcli 顶层 `--site` 互不影响**:`--site` 只切 ByteCloud SSO 区域,`--xpa-env` 才切 XPA 网关。 |
| `--xpa-tt-env <lane>` | 泳道 header `x-tt-env`，空 = 不带（基准环境）。同 `BYTEDCLI_XPA_TT_ENV`。                                                                                                            |

其他覆盖项（多数 hideHelp,通常走环境变量）：`--xpa-base-url` / `BYTEDCLI_XPA_BASE_URL`、`--xpa-path-prefix` / `BYTEDCLI_XPA_PATH_PREFIX`、`--xpa-use-ppe` / `BYTEDCLI_XPA_USE_PPE`、`--xpa-http-timeout-ms` / `BYTEDCLI_XPA_HTTP_TIMEOUT_MS`、`BYTEDCLI_XPA_CLIENT_TYPE`。

## auth

| 命令              | 说明                                                         |
| ----------------- | ------------------------------------------------------------ |
| `xpa auth login`  | 触发 ByteCloud JWT → exchange → 落盘；复用 bytedcli 登录态。 |
| `xpa auth status` | 显示本地凭据（脱敏），不发请求。                             |
| `xpa auth logout` | 清除本地 XPA 凭据。                                          |

## whoami / system

| 命令                | 选项         | 说明                             |
| ------------------- | ------------ | -------------------------------- |
| `xpa whoami`        | `--no-roles` | 网关 `/users/me`，默认带 roles。 |
| `xpa system status` | —            | 网关连通性 + env 路由自检。      |

## task（读）

> 分页统一 `--page`（1-based，默认 1）+ `--page-size`（默认 20）。`--status` 只接受语义值（不接受后端原始数字枚举）。
>
> 任务状态值（`task list`）：推荐使用 **显示标签** `pending` / `running` / `success` / `paused` / `stopped` / `continuous` / `init`（与 `task get` / `task status` 文本输出一致）。后端的过滤别名 `not_started`（= `pending`）/ `completed`（= `success`）也继续被接受作为兼容值，命令层会自动归一为后端 `?status=` 所需的过滤别名。
>
> 子任务状态值（`task subtask list`）：仅 `running` / `success` / `failed`。后端不接受 `pending` / `unknown` 作为过滤值。原始响应里 `status_name="unknown"` 是网关对 pending 态子任务（`status=1` 未派发、`status=8` 父任务未启动）的占位；CLI 文本模式会 fallback 到 code 映射并展示 `pending(1)` / `pending(8)` 等，不会直接输出字面 `unknown`。

| 命令                    | 必填   | 主要可选                                                                                                 |
| ----------------------- | ------ | -------------------------------------------------------------------------------------------------------- |
| `xpa task list`         | —      | `--status <semantic>`/`--task-id`/`--dataset-id`/`--all`/`--page`/`--page-size`                          |
| `xpa task get`          | `--id` | `--brief`（省去明细字段）                                                                                |
| `xpa task status`       | `--id` | —                                                                                                        |
| `xpa task running`      | —      | 分页同 list                                                                                              |
| `xpa task subtask list` | `--id` | `--status <semantic>`/`--sub-task-id`/`--serial-number`/`--fail-reason`/`--query`/`--page`/`--page-size` |

## task（写，默认 dry-run；加 `--yes` 执行）

| 命令                                | 必填                                                                                 | 选项                                                                                                                                                                                                                                                  |
| ----------------------------------- | ------------------------------------------------------------------------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `xpa task create`                   | `--name`、`--workflow-id`、`--device-ids`，以及 `--lark-file-url` / `--jsonl` 二选一 | `--queue-ids`（lark URL 必须含 `/sheets/`；JSONL 上限 5 MiB；name 限 128 字符）                                                                                                                                                                       |
| `xpa task start` / `pause` / `stop` | `--id`                                                                               | —                                                                                                                                                                                                                                                     |
| `xpa task subtask stop`             | `--id`、`--sub-id`                                                                   | 子任务被置失败态，前置任务 + 子任务都 running，权限 owner / super-admin                                                                                                                                                                               |
| `xpa task device add`               | `--id`、`--device-ids`                                                               | `--reason`                                                                                                                                                                                                                                            |
| `xpa task device remove`            | `--id`、`--device-ids`                                                               | `--reason`                                                                                                                                                                                                                                            |
| `xpa task export-result`            | `--id`                                                                               | `--all`、`--sub-ids`、`--status-list`、`--serial-number`、`--query`、`--execute-start-from`/`--execute-start-to`、`--execute-end-from`/`--execute-end-to`、`--collection-from`/`--collection-to`（**秒级时间戳**）、`--data-form-id`、`--fail-reason` |

## workflow（读）

> 分页统一 `--page`（1-based，默认 1）+ `--page-size`（默认 20）。`--device-type` 用语义值 `mobile` / `pc` / `cloud`（命令层映射到后端 1/2/3）。

| 命令                                  | 必填         | 主要可选                                                                                                                                                                                                                                                                                                                                      |
| ------------------------------------- | ------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `xpa workflow list`                   | —            | `--workflow-id`/`--name`/`--category`/`--subtitle`/`--device-type`/`--all-enabled`/`--all-workflows`/`--page`/`--page-size`                                                                                                                                                                                                                   |
| `xpa workflow get`                    | `--id`       | `--full`（返回 node graph / node 列表 / owner+view 用户 / 异常配置）                                                                                                                                                                                                                                                                          |
| `xpa workflow marketplace workflows`  | —            | `--keyword`/`--category`/`--published`/`--creatable`/`--page`/`--page-size`；只读 `marketplace [options]` 仍作为兼容入口路由到同一 handler（含旧 `-k`/`--page-num`/`--page-number`），但父命令 help 不展示这些兼容参数                                                                                                                        |
| `xpa workflow marketplace components` | —            | `--level all\|atomic`/`--device-type`/`--app-category-id`；返回按 level 分组的 marketplace 分类树，以 `bytedcli --json xpa ...` 形式重跑可查看该目录当前可见的完整结构                                                                                                                                                                        |
| `xpa workflow meta-node list`         | —            | `--meta-node-id`/`--name`/`--description`/`--level all\|atomic`/`--device-type`/`--app-category-id`/`--owner-user-ids`/`--page`/`--page-size`；独立的权限范围查询视图，加全局 `--json` 看该视图返回的 `node_param_struct` / `sub_nodes` / `exception_handle_config`                                                                           |
| `xpa workflow export-dsl`             | `--id`       | `--out <path>`（把前端可导入的 DSL 写入文件）。**只有 `--out` 落盘的文件是逐字节可导入的**：文件写的是后端 `data` 原始字节，int64 ID（`agentPlanId`/节点 `MetaNodeId`）保持数字形态；不带 `--out` 时文本模式只打摘要、`--json` 输出的 `dsl` 会把大 int64 转成字符串（仅供查看，不可直接导入）。链路 `logid` 只回显到终端 / JSON，绝不写进文件 |
| `xpa workflow device list`            | `--id`       | `--page`/`--page-size`（查工作流已绑定设备）                                                                                                                                                                                                                                                                                                  |
| `xpa workflow debug get`              | `--debug-id` | —（查单次调试结果详情）                                                                                                                                                                                                                                                                                                                       |
| `xpa workflow debug list`             | `--id`       | `--status <semantic>`（单值：`running`/`success`/`failed`，命令层映射到后端调试状态码 8/4/5）/`--page`/`--page-size`（查某工作流调试历史）                                                                                                                                                                                                    |

`marketplace components` 与 `meta-node list` 是两条独立的下游查询视图。两者都按当前用户过滤，但权限 / 发布状态边界与结果集不保证一致；不要把 components 的 `meta_node_id` 当成必然能在 meta-nodes 命中的详情入口。需要组件目录当前可见的完整结构时，以 `bytedcli --json xpa workflow marketplace components ...` 形式重跑原查询。响应里的 `authorized` 表示节点是否需要权限，不能据此在客户端放宽访问控制。

## workflow（写，默认 dry-run；加 `--yes` 执行）

| 命令                         | 必填                              | 选项                                                                                                                                                                                                   |
| ---------------------------- | --------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `xpa workflow update`        | `--id` + 至少一个字段             | `--name`（≤128 字符）/`--description`/`--category`/`--device-type`/`--app-category-id`（`--task-type` 为隐藏高级项：后端原始数字码）                                                                   |
| `xpa workflow copy`          | `--id`                            | —                                                                                                                                                                                                      |
| `xpa workflow publish`       | `--id`                            | —                                                                                                                                                                                                      |
| `xpa workflow unpublish`     | `--id`                            | —                                                                                                                                                                                                      |
| `xpa workflow create`        | `--from-json`                     | `--name`（覆盖 JSON 的 workflow_name）；JSON 需含非空 `nodes` 与 `node_graph`；文件 >5MB 直接拒。导出用 `--json ... \| jq '.data'` 取裸 body                                                           |
| `xpa workflow delete`        | `--id`、`--confirm-id`（=`--id`） | **破坏性、不可逆**；除 `--yes` 外必须 `--confirm-id` 精确等于 `--id`                                                                                                                                   |
| `xpa workflow debug start`   | `--id`、`--data`（合法 JSON）     | `--device-type`（默认取工作流的）/`--device-id`/`--node-graph`/`--parameter-type-validation`（`--debug-mode` 为隐藏高级项：后端原始数字码）。成功回显本次调试的链路 `logid`（`--json` 里也有 `logid`） |
| `xpa workflow debug stop`    | `--debug-id`                      | `--id`（可选；带上走 legacy 路径）。成功回显本次操作的链路 `logid`（`--json` 里也有 `logid`）                                                                                                          |
| `xpa workflow device bind`   | `--id`、`--device-ids`            | `--reason`                                                                                                                                                                                             |
| `xpa workflow device unbind` | `--id`、`--device-ids`            | `--reason`                                                                                                                                                                                             |

## device

| 命令                | 选项                                           | 备注                                                                                                                                                                                                                                                                                                                                                                                                                        |
| ------------------- | ---------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `xpa device list`   | `--type mobile\|pc`（默认 mobile）+ 多过滤维度 | 通用过滤：`--device-id`/`--device-name`/`--device-status <online\|offline>`/`--device-use-status <idle\|busy>`/`--connect-type <adb\|link>`/`--device-platform <private\|public\|cloud>`/`--serial-number`/`--bind-business-id`；mobile 专属：`--resolution`/`--brand`/`--device-cluster-id`/`--android-version`；pc 专属：`--os-type`/`--os-version`/`--available-memory-gb`/`--cpu-cores`/`--instance-ip`/`--mac-address` |
| `xpa device idle`   | 同 list                                        | 仅返回 idle 设备                                                                                                                                                                                                                                                                                                                                                                                                            |
| `xpa device get`    | `--type` + 定位符（恰好一个）                  | mobile: `--device-id`\|`--serial-number`；pc：再加 `--instance-name`\|`--instance-id`                                                                                                                                                                                                                                                                                                                                       |
| `xpa device tasks`  | 同 get                                         | 看占用设备的任务列表                                                                                                                                                                                                                                                                                                                                                                                                        |
| `xpa device unbind` | `--task`                                       | 写命令（dry-run / `--yes`），清空 task 的设备绑定                                                                                                                                                                                                                                                                                                                                                                           |
| `xpa device delete` | `--type`、`--device-id`                        | **破坏性、不可逆**；写命令                                                                                                                                                                                                                                                                                                                                                                                                  |

## dataset

| 命令                | 必填     | 选项                                                                                                              |
| ------------------- | -------- | ----------------------------------------------------------------------------------------------------------------- |
| `xpa dataset reset` | `--task` | 重置失败数据集记录（写命令；dry-run / `--yes`）                                                                   |
| `xpa dataset rerun` | `--task` | `--rerun-type failed_task\|any_final_state_task`（默认 `failed_task`，只接受语义值）、`--sub-ids`、`--device-ids` |

## 输入校验（命令层本地拦截）

- 所有 ID（task / sub-task / device / dataset / workflow）必须是**正整数**字符串；非正整数本地直接拒。
- `--device-ids` / `--sub-ids` / `--queue-ids` / `--status-list` 是逗号分隔的列表；命令层去重 + 正整数校验。
- 时间范围参数（`--execute-start-from/to` 等）正整数本地严校（拒 NaN/0/负数）。
- 设备定位符「恰好一个」：多传或全空命令层直接拒；mobile 传 instance\_\* 直接拒。
- task create 的 `--lark-file-url` 与 `--jsonl` 必须恰好指定一个；`--jsonl` 直接接收文本并以内联 `jsonl` 字段提交，上限为 5 MiB。shell 中的多行 JSONL 使用 ANSI-C 引号 `$'第一行\n第二行'`；inline 参数可能留在 shell history 或进程列表，不要传敏感内容。JSONL 每个非空行必须是 JSON object，行数与单行大小等内容校验由 Gateway 负责；每行还需包含所选 workflow 开始节点要求的输入字段。CLI 不开放 `tos_file_name`、`csv_url`、`jsonl_url`。`--name` 最多 128 字符。

## 退出码语义

- dry-run（写命令未带 `--yes`）：正常退出 0，仅打印将要执行的摘要。CI 与 TTY 行为一致(无交互式 y/N 确认,也不做 TTY 探测)。
- 后端业务失败（`AppError` code `XPA_API_ERROR`）：退出非零；text 模式展示服务端 message，并在独立 `Diagnostics` 行输出实际存在的 HTTP 状态、业务码与 `logid`；JSON 模式对应字段在 `error.status_code`、`error.request_id` 与 `error.details`。
- `workflow` 写命令（`update` / `copy` / `publish` / `unpublish` / `create` / `delete` / `debug start` / `debug stop` / `device bind` / `device unbind`）成功执行后，若网关响应携带链路 `logid`，文本模式会单起一行输出 `logid: ...`，`--json` 则写入 `logid` 字段。可凭它查询后端链路日志，定位「后端回 success 但状态未真正翻转」（如 publish/unpublish）等问题。
