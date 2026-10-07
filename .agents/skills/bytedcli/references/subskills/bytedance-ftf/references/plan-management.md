# FTF Plan 管理与执行

目录：[用途](#用途) · [常用命令](#常用命令) · [参数规则](#参数规则) · [分页查询](#分页查询计划) · [执行计划](#执行已有计划) · [安全检查](#安全检查)

## 用途

本文件覆盖 TeslaX FTF Plan 的查询、创建、更新、删除和执行，并说明写操作保护。

`ftf plan list`、`ftf plan get` 和 `ftf plan execute` 是 canonical FTF 命令，分别调用
TeslaX v1 gateway 的 `POST /ftf/test_plan/list/by_page`、`GET /ftf/test_plan/query` 和
`POST /ftf/test_plan/trigger/task`。新增 FTF plan 命令也只能使用 TeslaX v1 `/ftf/...`，
禁止接入 `/apix/...`、旧域名或 FTF2.0 OpenAPI。

`create/update/delete/records` 是仓库基线中已经存在的 TeslaX plan 管理能力，直连对应分区
的 Tesla-X 页面 host 并使用 `/apix/...`，不属于 FTF OpenAPI。它们仅为兼容现有命令保留，
后续应迁移到 TeslaX v1；不得在这些路径上新增或扩展 FTF 命令：

| 命令              | 方法     | 路径                                |
| ----------------- | -------- | ----------------------------------- |
| `ftf plan create` | `POST`   | `/apix/space/:spaceId/plan`         |
| `ftf plan update` | `PUT`    | `/apix/space/:spaceId/plan/:planId` |
| `ftf plan delete` | `DELETE` | `/apix/space/:spaceId/plan/:planId` |

`ftf plan list` 通过 `POST /ftf/test_plan/list/by_page` 分页查询测试计划，`--space-id` 是可选筛选条件。
`ftf plan get` 通过 `GET /ftf/test_plan/query?planID=<id>` 查询 ATP/TeslaX 测试计划
详情，返回完整 `FtfTestPlanV1` 业务对象。`ftf plan execute` 通过 TeslaX v1 gateway 的
`POST /ftf/test_plan/trigger/task` 执行已有 parent plan；源码和后端文档中的业务路径写作
`/openapi/test_plan/trigger/task`，client 发送前统一映射为 `/ftf/...`。

`plan get` 的非 JSON 输出按用途拆分为计划摘要、PSM 执行配置、Replay Methods、
Advanced Filters 和 Additional Plan Settings。复杂对象、数组以及 JSON 字符串只展示
条目数、字段数或长度摘要，避免把整段 JSON 压入单个表格单元格；需要完整原始字段时使用
`bytedcli --json --site cn ftf plan get --id <id>`。

TeslaX v1 `/ftf/...` 请求使用 ByteCloud JWT，同时发送 `Domain: teslax;v1` 与 `X-Jwt-Token`。存量 `/apix/...` 管理接口发送 `Authorization` 与 `X-Jwt-Token`，不发送 `Domain`。Plan 管理接口的完整请求与响应字段见 `plan-api-schema.md`。

## 常用命令

```bash
bytedcli --json --site cn ftf plan list \
  --psm example.psm \
  --page 1 \
  --page-size 20

bytedcli --site cn ftf plan list --psm example.psm --env boe --ci

bytedcli --json --site cn ftf plan get --id 2000

bytedcli --site cn ftf plan create \
  --space-id 1000 \
  --plan-name "sample plan" \
  --psm example.psm \
  --replay-env sample_env \
  --idl-version master \
  --payload '{"ftf_plan":{"enabled":true},"psm_exec_params":{"example.psm":{"replay_env":"sample_env"}}}' \
  --execute

bytedcli --site cn ftf plan update \
  --space-id 1000 \
  --plan-id 2000 \
  --plan-name "updated sample plan" \
  --payload '{"notify_config_json":{"notify_users":["sample-user"]}}' \
  --execute

bytedcli --site cn ftf plan delete --space-id 1000 --plan-id 2000 --execute

bytedcli --json --site cn ftf plan execute \
  --parent-plan-id 2000 \
  --noflow-abort-duration 300

bytedcli --site cn ftf plan execute --parent-plan-id 2000 --method-list "GET /flow/list,POST /caseset/add-flow,THRIFT GetTaskDetail,RMQ EventConsumer" --replay-env ppe_xxx --replay-cluster default --yes

# 确认 online Method 预览后，原命令增加 --yes
bytedcli --json --site cn ftf plan execute \
  --parent-plan-id 2000 \
  --noflow-abort-duration 300 \
  --yes
```

## 参数规则

- canonical `plan list` 的 `--space-id` 是可选筛选条件；可用 `--parent-plan-id`、`--name`、`--env`、
  `--case-filter-mode`、`--psm`、`--advanced-filter`、`--create-user` 和 `--ci` 组合筛选。
- `plan list --ci` 只返回已开启 CI 的计划，映射后端 `enable_ci=1`。
- `plan list --case-filter-mode` 只接受 `realtime`、`scene`、`non-realtime`、
  `third-party`；`--advanced-filter` 只接受 `enabled`、`disabled`。CLI 在请求后端前映射为
  对应数字枚举，不对用户暴露后端数字。
- `plan list --psm` 映射后端 `bind_psm`；列表按 `create_time DESC` 排序，`--page` 默认
  `1`，`--page-size` 默认 `20`。
- `create` 必填 `--space-id`、`--plan-name`、`--psm`；`--test-scene` 未传时默认写入 `研发自测`。
- `create` 默认写入 `enable_ftf=1`；`--payload` 仍可覆盖该默认值和其它命名 flag。
- canonical `plan get` 必填 `--id`，表示 ATP/TeslaX 测试计划 ID，对应后端 Query
  `planID`；不需要 `--space-id`。
- `update/delete` 必填 `--space-id`、`--plan-id`。
- `create/update/delete` 是外部写操作，必须显式传 `--execute`。
- `create/update` 支持浅字段：`--plan-name`、`--psm`、`--description`、`--test-scene`、`--replay-env`、`--idl-version`、`--case-set-id`、`--parent-plan-id`。
- `--payload '{}'` 用于注入深结构字段，例如 `ftf_plan`、`psm_exec_params`、`notify_config_json`、`advanced_filter_group_list`。
- 命名 flag 与 `--payload` 冲突时，`--payload` 覆盖命名 flag，便于用完整 JSON body 修正默认值或深字段。
- `plan execute` 必须提供 `--plan-id`、`--parent-plan-id` 或 `--request-json` 之一；两个 ID 也允许同时提供，同时提供时后端按 `plan_id` 选择 FTF 计划，并保留 `parent_plan_id` 作为任务关联信息。
- `--trigger-user` 是可选覆盖；未传时使用当前 bytedcli 登录用户名。完整 request JSON 已包含非空 `trigger_user` 时保留该值。
- `plan execute` 的无流量停止参数统一为 `--noflow-abort-duration`；省略时继承计划配置，`0` 表示关闭，正数必须在 `[60, 3600]` 秒范围内。
- `--replay-mode` 只接受 `normal`、`diffy`，分别映射后端 `0`、`1`。
- `--method-list` 接收英文逗号分隔的 UniversalMethod 值，例如 `GET /flow/list`、
  `THRIFT GetTaskDetail`；CLI 将数组合并到计划实际包含的每个 PSM。
- 12 个公共 PSM/IDL 参数为 `--replay-env`、`--replay-cluster`、`--replay-region`、
  `--replay-host`、`--replay-psm`、`--base-replay-env`、`--base-replay-cluster`、
  `--base-replay-region`、`--base-replay-host`、`--base-replay-psm`、`--idl-version`、
  `--base-idl-version`。CLI 将这些值应用到计划实际包含的每个 PSM；
  `--psm-trigger-params` 中的同名 per-PSM 字段优先于公共值。
- `--notify-groups` 和 `--notify-users` 接受逗号分隔值，分别映射为通知群 ID 和用户名数组。
- `--psm-trigger-params` JSON 的每个顶层 key 都必须属于所选计划实际包含的 PSM；不得借此为计划外 PSM 增加触发配置。
- 过渡期保留 `--request-json`、`--psm-trigger-params`、`--advanced-filter-group-list`、`--pipeline-job-id`、`--pipeline-url`、`--commit-hash`、`--code-branch`、`--pipeline-demand-items` 等复杂请求兼容参数。
- `--request-json` 是完整请求，覆盖所有 named business flags；CLI 只为缺失的 `trigger_user` 补登录用户名。
- 未传 `--yes` 时，CLI 会读取计划。`env=online` 时输出 Method 预览并停止；非 online 计划不做 Method 预查或确认，直接调用执行接口。
- 传 `--yes` 时直接调用执行接口，不发起计划详情或 Method 预查。
- `plan execute` 不接受 `--space-id`。使用 `--plan-id` 时，CLI 通过 TeslaX v1 gateway 直接定位计划；使用 `--parent-plan-id` 时按 parent plan 查询。
- `--case-filter-mode` 只接受 `realtime`、`scene`、`non-realtime`、`third-party`，handler 分别映射为后端 `0`、`1`、`2`、`4`。

## 分页查询计划

`ftf plan list` 通过 TeslaX v1 gateway 查询测试计划，可用 `--space-id` 收窄到指定空间。

- Method / Path：`POST /ftf/test_plan/list/by_page`
- CLI：`bytedcli --site cn ftf plan list --psm example.psm`
- JSON：bytedcli 统一外壳的 `.data` 为
  `{ "plans": [...], "total": 0, "page": 1, "page_size": 20 }`
- 文本列固定为 `ID`、`PARENT ID`、`NAME`、`PSM`、`ENABLE CI`、`CREATED BY`、
  `CREATED AT`

请求和响应的完整字段映射见 `plan-api-schema.md`。

## 执行已有计划

`ftf plan execute` 根据 TeslaX parent plan 创建 FTF task。

- 业务 Method / Path：`POST /openapi/test_plan/trigger/task`
- Gateway Path：`POST /ftf/test_plan/trigger/task`
- CLI：`bytedcli --site cn ftf plan execute --parent-plan-id 2000`

### 请求 Body

| 字段                         | 必填 | 说明                                                    |
| ---------------------------- | ---- | ------------------------------------------------------- |
| `plan_id` / `parent_plan_id` | 是   | 至少一个；CLI 参数为 `--plan-id`、`--parent-plan-id`    |
| `trigger_user`               | 是   | 触发人；CLI 未传 `--trigger-user` 时使用当前登录用户名  |
| `trigger_type`               | 否   | 触发类型，见 `enums.md#trigger_type`                    |
| `method_replay_count`        | 否   | 覆盖计划内单接口回放条数                                |
| `single_scene_replay_count`  | 否   | 覆盖计划内单场景回放条数                                |
| `task_run_time`              | 否   | 覆盖计划内任务运行时长                                  |
| `no_flow_abort_duration`     | 否   | 无流量停止时长；CLI 参数为 `--noflow-abort-duration`    |
| `is_open_advanced_filter`    | 否   | 是否覆盖计划内高级筛选开关                              |
| `advanced_filter_group_list` | 否   | 高级筛选组                                              |
| `psm_trigger_params`         | 否   | `map[string]PSMTriggerParam`，按 PSM 覆盖计划内回放参数 |
| `replay_mode`                | 否   | `0` normal，`1` diffy；CLI 使用 `--replay-mode`         |
| `notify_groups`              | 否   | 通知群 ID 数组；CLI 使用 `--notify-groups`              |
| `notify_users`               | 否   | 通知用户名数组；CLI 使用 `--notify-users`               |
| `status_callback_switch`     | 否   | `1` 开启状态回调；CLI 参数为 `--status-callback`        |
| `pipeline_info`              | 否   | 关联流水线或代码变更                                    |
| `inherited_branches`         | 否   | 需要同时提供 `pipeline_info.code_branch` 才生效         |
| `extra_params`               | 否   | 业务透传字符串，建议 JSON 字符串                        |

`psm_trigger_params`、`advanced_filter_group_list`、`pipeline_info` 可通过上面的过渡兼容
参数或 `--request-json` 提供。`psm_trigger_params` 的 key 必须是计划实际包含的 PSM。
接口中的 `custom_test_plan`、`replay_condition_v2_detail`
等更深或已废弃字段不作为 named flags 暴露；当前 `--request-json` 也只接受 CLI 白名单中的
已支持字段。

### 响应

```json
{ "code": 0, "data": 833688, "log_id": "...", "msg": "OK" }
```

`data` 是创建出的 FTF task id。普通输出只展示触发接口返回的任务 ID，以及请求中的
Parent Plan ID；CLI 不额外查询 task detail。需要查看任务详情时，继续执行
`ftf task get --id <task_id>` 验证 branch、commit、replay 参数和任务状态。

`POST /create/task/with_plan` 已废弃，统一使用 `POST /openapi/test_plan/trigger/task`。

### online Method 预览

未传 `--yes` 时，`plan execute` 先通过 TeslaX v1 查询完整 FTF 计划：

- 计划 `env=online`：CLI 输出本次实际执行的 Method 集合，不创建任务。
- 计划不是 `online`：不做 Method 预查或二次确认，直接调用执行接口。
- Method 无法解析或为空：返回错误，不允许继续执行。

Method 集合按以下规则计算：

- 普通筛选：以测试计划 `psm_exec_params.<psm>.method_list` 为计划范围；本次触发通过
  `psm_trigger_params.<psm>.method_list` 传入范围时，最终结果为两者交集。触发未传
  `method_list` 时直接使用计划范围。
- 高级筛选：高级筛选组含 `method` 条件时，以该 Method 集合作为计划范围；本次触发传入
  `method_list` 时取两者交集，未传时直接使用高级筛选 Method。
- 计划普通筛选的 `method_list=["*"]`，或高级筛选组未配置 Method 条件时，计划范围表示
  全部接口，通过 `POST /ftf/method/query/by_conditions`、`read_only=true` 展开。
- 本次触发的 `method_list=["*"]` 表示不进一步收窄，最终范围仍受测试计划普通/高级筛选
  限制；如果计划范围也是全部接口，则展示 Method API 展开的全部接口。

这份预览用于人工确认业务语义，不能发现平台自身的接口类型误标。后端执行阶段仍会根据自身
策略做最终过滤。用户确认后，原命令增加 `--yes`；此时 CLI 直接调用执行接口，不重复预查。

## 安全检查

- 删除不可逆；存量 `/apix` plan delete 需要用对应页面计划信息确认
  `space_id`、`plan_id`、`plan_name` 和绑定 PSM。canonical `plan get --id` 查询的是
  ATP/TeslaX parent plan，不要把返回的内层 FTF `id` 当成 `/apix` plan path ID。
- 创建或更新用于代码 diff 的计划前，先确认 PSM、replay env、branch/commit、是否立刻执行外部写入。
- 触发计划生成 task 后，不要只返回创建结果；继续用 `ftf task get --id <task_id>` 验证 branch/commit/replay 参数。
