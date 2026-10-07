# TeslaX Plan API Schema

## 章节索引

- [请求入参](#1-请求入参request-body)
- [`notify_config_json`](#13-notify_config_json-结构)
- [`ftf_plan`](#14-内层-ftf_plan-关键字段)
- [`psm_exec_params`](#15-psm_exec_paramspsm-关键字段psmexecparam与-task-psmrunparam-类似)
- [高级筛选组](#16-advanced_filter_group_list与-task-的-advancedfiltergroup-一致)
- [CLI 参数映射](#17-cli-命名-flag--顶层-idl-字段映射cli-实现)
- [响应出参](#2-响应出参response)

> 本文件整理 canonical `ftf plan list/get` 及存量 `ftf plan create/update/delete` 的请求与
> 响应 Schema，供 `references/plan-management.md` 引用。
>
> **接口边界：**
>
> - canonical `ftf plan list` 使用 TeslaX v1 gateway
>   `POST /ftf/test_plan/list/by_page`；`data.plan_list` 是当前页测试计划。
> - canonical `ftf plan get --id <id>` 使用 TeslaX v1 gateway
>   `GET /ftf/test_plan/query?planID=<id>`；`data` 是完整 `FtfTestPlanV1` 业务对象。
> - `ftf plan create/update/delete/records` 是仓库基线中已经存在的 TeslaX plan 管理能力，
>   当前使用 `{teslaXOrigin}/apix/space/:spaceId/plan[/:planId]`。
>   `teslaXOrigin` 是对应分区的 Tesla-X 页面 host；
>   鉴权头为 `ftfTeslaxAuthHeaders`（`Authorization` + `X-Jwt-Token`，不发送 `Domain`），响应 envelope 为
>   `error_code / error_message`（成功为 `0 / ""`）。
> - `/apix/...` 不属于 FTF OpenAPI。新增 FTF 命令只能使用 TeslaX v1 gateway `/ftf/...`，不得新增或扩展 `/apix/...` 调用；这些存量管理命令后续应迁移到 TeslaX v1。
> - 本文件只记录现有管理命令所需的 body / response Schema，不作为新增 API 接入依据。
>
> CLI 侧只对**顶层浅字段**提供命名 flag（`{ ...base, ...extra }`，`--payload` 覆盖命名 flag）；
> 内层 `ftf_plan.*`、`psm_exec_params`、`notify_config_json`、`advanced_filter_group_list`
> 等深结构**没有专门 flag，一律通过 `--payload '{}'` 深合并注入**。

---

## 1. 请求入参

### 1.0 canonical `plan list`

- Method / Path：`POST /ftf/test_plan/list/by_page`
- CLI：`bytedcli --json --site cn ftf plan list --psm example.psm`

| CLI flag             | Body 字段                 | 类型   | 必填 | 说明                                                 |
| -------------------- | ------------------------- | ------ | ---- | ---------------------------------------------------- |
| `--space-id`         | `space_id`                | Long   | 否   | TeslaX 空间 ID筛选条件；提供时必须为正整数           |
| `--parent-plan-id`   | `parent_plan_id`          | Long   | 否   | ATP/TeslaX parent plan ID                            |
| `--name`             | `name`                    | string | 否   | 计划名称筛选                                         |
| `--env`              | `env`                     | string | 否   | 计划业务环境筛选                                     |
| `--case-filter-mode` | `case_filter_mode`        | int    | 否   | `realtime/scene/non-realtime/third-party` 的后端映射 |
| `--psm`              | `bind_psm`                | string | 否   | 绑定 PSM 筛选                                        |
| `--advanced-filter`  | `is_open_advanced_filter` | int    | 否   | `enabled/disabled` 分别映射为 `1/0`                  |
| `--create-user`      | `create_user`             | string | 否   | 创建人用户名筛选                                     |
| `--page`             | `page`                    | int    | 否   | 正整数，默认 `1`                                     |
| `--page-size`        | `page_size`               | int    | 否   | 正整数，默认 `20`                                    |
| CLI 固定             | `sort_fields`             | string | 是   | 固定为 `create_time`                                 |
| CLI 固定             | `sort_mode`               | string | 是   | 固定为 `DESC`                                        |

`case_filter_mode` 的后端映射为 `realtime=0`、`scene=1`、`non-realtime=2`、
`third-party=4`。这些数字只存在于请求适配层，CLI 帮助和用户输入均使用语义值。

### 1.1 canonical `plan get`

- Method / Path：`GET /ftf/test_plan/query`
- CLI：`bytedcli --json --site cn ftf plan get --id 2000`
- Query：`planID=2000`

| CLI flag | Query 字段 | 类型 | 必填 | 说明                                 |
| -------- | ---------- | ---- | ---- | ------------------------------------ |
| `--id`   | `planID`   | Long | 是   | ATP/TeslaX 测试计划 ID，必须为正整数 |

该命令不需要 `--space-id`，也不使用下文的 `/apix` path 参数。

### 1.2 外层 body 顶层字段

创建 / 更新时 body 的顶层字段（`POST /apix/space/:spaceId/plan`、`PUT /apix/space/:spaceId/plan/:planId`）：

| 字段                 | 类型      | 必填         | CLI flag             | 说明                                                                                                                                                                      |
| -------------------- | --------- | ------------ | -------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `plan_name`          | string    | 是（create） | `--plan-name`        | 测试计划名称。create 侧 CLI 强制必填（早失败）；update 传入即覆盖                                                                                                         |
| `enable_ftf`         | int       | 是           | 自动默认             | **恒为 1**（启用 FTF 计划）。create 侧 CLI 默认写入 `1`；如需调试特殊值，可通过 `--payload` 覆盖                                                                          |
| `test_scene`         | string    | 是           | `--test-scene`       | 枚举：`研发自测` / `新需求测试` / `全回归` / `核心功能回归` / `线上巡检` / `未分类`。**create 未显式传时默认落 `"研发自测"`**（`DEFAULT_TEST_SCENE`）；CLI 不做白名单校验 |
| `is_schedule`        | int (0/1) | 否           | 无（走 `--payload`） | 是否开启定时执行                                                                                                                                                          |
| `crontab`            | string    | 否           | 无（走 `--payload`） | crontab 语法字符串，如 `10 5 3 * 5`                                                                                                                                       |
| `notify_config_json` | object    | 否           | 无（走 `--payload`） | 通知配置对象，结构见 1.3                                                                                                                                                  |
| `ftf_plan`           | object    | 是           | 无（走 `--payload`） | FTF 内层计划配置，结构见 1.4。CLI 默认平铺透传、不加 `ftf_plan` 嵌套；若后端要求两层结构，用 `--payload '{"ftf_plan":{...}}'` 注入                                        |

> **平铺透传与两层结构**：CLI 实现 `buildPlanCreatePayload/UpdatePayload` 默认把
> `enable_ftf / --plan-name / --psm / --description / --test-scene / --replay-env / --idl-version /
--case-set-id / --parent-plan-id` 平铺到 body 顶层，**不**自动包一层 `ftf_plan`。
> `api-plan.md` 官方示例 body 是 `{ plan_name, enable_ftf, test_scene, ..., ftf_plan:{...} }`
> 的两层结构；若集成后报字段缺失或写不到内层，用 `--payload '{"ftf_plan":{...}}'` 手工补齐
> 。

### 1.3 `notify_config_json` 结构

```json
{
  "notify_switch": ["ftf"],
  "notify_types": ["manual", "schedule", "devops"],
  "notify_users": ["sample-user"],
  "notify_groups": []
}
```

| 字段            | 类型     | 说明                                                           |
| --------------- | -------- | -------------------------------------------------------------- |
| `notify_switch` | string[] | 通知开关渠道，如 `tesla` / `ftf`                               |
| `notify_types`  | string[] | 生效类型：`manual`（手工）、`schedule`（定时）、`devops`（CI） |
| `notify_users`  | string[] | 通知用户名列表                                                 |
| `notify_groups` | string[] | 通知群列表                                                     |

### 1.4 内层 `ftf_plan` 关键字段

| 字段                         | 类型                 | 必填 | 说明                                         |
| ---------------------------- | -------------------- | ---- | -------------------------------------------- |
| `method_replay_count`        | int                  | 否   | 单接口回放条数（非场景）                     |
| `status_callback_switch`     | int                  | 否   | 回调开关                                     |
| `env`                        | string               | 是   | `boe` / `online`                             |
| `enabled`                    | bool                 | 否   | 是否启用                                     |
| `case_filter_mode`           | int                  | 是   | 用例筛选类型，见 `enums.md#case_filter_mode` |
| `replay_assert_mode`         | int                  | 否   | 断言模式                                     |
| `replay_module_mode`         | int                  | 否   | 回放模块模式                                 |
| `replay_time_limit`          | int                  | 否   | 回放时长（分钟）                             |
| `noflow_abort_duration`      | int                  | 否   | 无流量停止时间（秒），默认 60                |
| `single_scene_replay_count`  | int                  | 否   | 单场景回放条数                               |
| `psm_exec_params`            | map[psm]PSMExecParam | 是   | PSM 具体回放参数，结构见 1.4                 |
| `select_directory_list`      | object               | 否   | 场景目录选择                                 |
| `create_user`                | string               | 是   | 创建人                                       |
| `is_base_test_plan`          | int (0/1)            | 否   | 是否是基准测试计划                           |
| `is_open_base_compare`       | bool                 | 否   | 是否开启基准任务对比降噪                     |
| `is_open_advanced_filter`    | int/bool             | 否   | 是否开启高级筛选                             |
| `advanced_filter_group_list` | array                | 否   | 高级筛选组数组，结构见 1.6                   |

### 1.5 `psm_exec_params.<psm>` 关键字段（PSMExecParam，与 Task PSMRunParam 类似）

```
psm / replay_psm / replay_qps_limit / retry_max / run_timeout / assert_scene /
idl_version / replay_downstream / record_entrance / record_downstream /
base_idl_version / replay_env / replay_cluster / replay_idc / replay_host /
base_replay_psm / base_replay_env / base_replay_cluster / base_replay_idc /
base_replay_host / bytecopy_psm / bytecopy_stage / bytecopy_cluster /
bytecopy_idc / instance_num / method_param_detail
```

`method_param_detail[]` 每项常见字段：`method / http_method / protocol / flow_count /
is_open_edit / inbound_before_script / inbound_after_script / new_method / mock_enable`。

> **注意**：`inbound_before_script` / `inbound_after_script` 生效的前提是同一 method 的
> `is_open_edit` 为 `1`；否则脚本不会在回放时执行。

> `psm_exec_params[psm].method_param` 是 JSON 字符串形式的 method 数组，结构与
> `method_param_detail` 一致但更详细，额外包含 `edit_info / mock_wait_time /
outbound_before_script / outbound_after_script`。

### 1.6 `advanced_filter_group_list[]`（与 Task 的 AdvancedFilterGroup 一致）

字段一般为 `{"op": <操作符>, "value": <值>}` 形式，例：

| 字段                                                                                   | 示例                                                                   |
| -------------------------------------------------------------------------------------- | ---------------------------------------------------------------------- |
| `teslax_space_id`                                                                      | `{"op":"eq","value":1000}`                                             |
| `nario_space_id`                                                                       | `{"op":"in","value":[2000]}`                                           |
| `psm`                                                                                  | `{"op":"eq","value":"example.psm"}`                                    |
| `scene_meta`                                                                           | `{"op":"in","value":[86972,86971]}`                                    |
| `record_time`                                                                          | `{"op":"since","value":["2024-11-05 17:26:26","2024-11-19 17:26:26"]}` |
| `flow_source`                                                                          | `{"op":"eq","value":"sdk"}`                                            |
| `pid`                                                                                  | `{"op":"in","value":["<pid1>","<pid2>"]}`                              |
| `case_total_replay_limit` / `single_method_replay_limit` / `single_scene_replay_limit` | int                                                                    |

### 1.7 CLI 命名 flag → 顶层 IDL 字段映射（CLI 实现）

| flag               | IDL 字段           | 类型   | 备注                                                                                                                                                             |
| ------------------ | ------------------ | ------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `--space-id`       | `space_id`（path） | int    | 存量 create / update / delete 必填                                                                                                                               |
| `--plan-id`        | `plan_id`（path）  | int    | 存量 update / delete 必填                                                                                                                                        |
| `--plan-name`      | `plan_name`        | string | create 必填（CLI 强制早失败）；update 传即覆盖                                                                                                                   |
| `--psm`            | `psm`              | string | create 必填（CLI 强制早失败）                                                                                                                                    |
| `--description`    | `description`      | string | 选填                                                                                                                                                             |
| `--test-scene`     | `test_scene`       | string | 选填；create 未传默认 `"研发自测"`                                                                                                                               |
| `--replay-env`     | `replay_env`       | string | 选填                                                                                                                                                             |
| `--idl-version`    | `idl_version`      | string | 选填                                                                                                                                                             |
| `--case-set-id`    | `case_set_id`      | int    | 选填（`parseNumericOption` 校验数字）                                                                                                                            |
| `--parent-plan-id` | `parent_plan_id`   | int    | 选填（`parseNumericOption` 校验数字）                                                                                                                            |
| `--payload '{}'`   | 其它任意字段       | object | 深合并；`ftf_plan` / `psm_exec_params` / `notify_config_json` / `advanced_filter_group_list` 等复合结构全部走这里，且 `--payload` 覆盖命名 flag 与 create 默认值 |

---

## 2. 响应出参（Response）

### 2.0 canonical `plan list` 响应

TeslaX v1 响应使用 `code / msg / log_id / data` envelope，`data` 中的分页结构如下：

| 字段        | 类型                     | 说明               |
| ----------- | ------------------------ | ------------------ |
| `plan_list` | `FtfTestPlanSummaryV1[]` | 当前页测试计划列表 |
| `total`     | int                      | 符合条件的计划总数 |
| `page`      | int                      | 当前页码           |
| `page_size` | int                      | 每页数量           |

列表条目的 canonical 核心字段：

| 字段             | 类型      | 说明                      |
| ---------------- | --------- | ------------------------- |
| `id`             | int       | FTF 测试计划 ID           |
| `space_id`       | int       | TeslaX 空间 ID            |
| `parent_plan_id` | int       | ATP/TeslaX parent plan ID |
| `name`           | string    | 计划名称                  |
| `env`            | string    | 计划业务环境              |
| `bind_psm`       | string?   | 绑定 PSM                  |
| `enable_ci`      | int/bool? | 是否启用 CI               |
| `create_user`    | string?   | 创建人                    |
| `create_time`    | string?   | 创建时间                  |

API 层剥离后端 envelope 后，CLI 把 `plan_list` 映射为语义化 `plans`；bytedcli JSON 外壳为：

```json
{
  "data": {
    "plans": [],
    "total": 0,
    "page": 1,
    "page_size": 20
  }
}
```

非 `--json` 输出列固定为 `ID`、`PARENT ID`、`NAME`、`PSM`、`ENABLE CI`、
`CREATED BY`、`CREATED AT`。

### 2.1 canonical `plan get` 响应

TeslaX v1 响应使用 `code / msg / log_id / data` envelope；API 层校验并剥离 envelope 后，
bytedcli JSON 外壳的 `.data` 直接承载 `FtfTestPlanV1`；完整 Nova envelope 位于
`.context.backend`，因此 `msg/log_id` 和后端新增 envelope 字段不会丢失。

| 字段                         | 类型                 | 说明                                                  |
| ---------------------------- | -------------------- | ----------------------------------------------------- |
| `id`                         | int                  | FTF 内层测试计划 ID                                   |
| `space_id`                   | int                  | TeslaX 空间 ID                                        |
| `parent_plan_id`             | int                  | ATP/TeslaX 测试计划 ID                                |
| `name`                       | string               | 计划名称                                              |
| `env`                        | string               | 计划业务环境                                          |
| `bind_psm`                   | string               | 绑定 PSM，响应存在时透传                              |
| `psm_exec_params`            | map[psm]PSMExecParam | PSM 回放参数，含 `method_list`、`replay_qps_limit` 等 |
| `is_open_advanced_filter`    | int/bool             | 是否开启高级筛选                                      |
| `advanced_filter_group_list` | array/null           | 高级筛选组                                            |

`FtfTestPlanV1` 可能继续增加字段。API 层严格校验上述核心结构，并保留未枚举的计划级、
PSM 级和高级筛选扩展字段，避免查询结果丢失后端详情。

非 `--json` 模式不会将 `psm_exec_params`、`advanced_filter_group_list` 等深层结构直接
序列化到单个 Value 单元格，而是拆成摘要与专用表格；其它复杂字段仅显示条目数、字段数或
字符串长度。完整内容仍位于 `--json` 输出的 `.data`。

以下 2.2 至 2.4 仅描述存量 `/apix` create/update/delete 响应；其 envelope 为
`error_code / error_message`（成功 `0 / ""`），业务体在 `data`。

### 2.2 create / update 响应 `data` 字段

| 字段                 | 类型        | 说明                                                  |
| -------------------- | ----------- | ----------------------------------------------------- |
| `id`                 | int         | 计划 ID（TeslaX plan id）                             |
| `space_id`           | int         | 空间 ID                                               |
| `plan_name`          | string      | 计划名称                                              |
| `test_scene`         | string      | 测试场景枚举                                          |
| `plan_tag`           | string      | 计划标签                                              |
| `env_type`           | string      | 环境类型                                              |
| `enable_tesla`       | int         | 是否启用 Tesla                                        |
| `tesla_plan_id`      | int         | Tesla 计划 ID                                         |
| `enable_ftf`         | int         | 是否启用 FTF（通常 1）                                |
| `ftf_plan_id`        | int         | FTF 内层计划 ID                                       |
| `enable_odg`         | int         | 是否启用 ODG                                          |
| `odg_plan_id`        | int         | ODG 计划 ID                                           |
| `is_schedule`        | int         | 是否定时执行                                          |
| `crontab`            | string      | crontab 表达式                                        |
| `psm_config`         | string      | PSM 配置（create 响应可能出现）                       |
| `env_tag_id`         | int         | 环境标签 ID（create 响应可能出现）                    |
| `notify_chat_id`     | string      | 通知群 ID                                             |
| `notify_config`      | string      | 通知配置（JSON 字符串形式）                           |
| `notify_config_json` | object/null | 通知配置对象形式                                      |
| `creator`            | string      | 创建人                                                |
| `updater`            | string      | 更新人                                                |
| `created_at`         | string      | 创建时间（RFC3339）                                   |
| `updated_at`         | string      | 更新时间（RFC3339）                                   |
| `deleted_at`         | string/null | 删除时间，未删除为 null                               |
| `ftf_psm`            | string      | FTF 调度 PSM（update 响应可能出现，如 `example.psm`） |
| `enable_ci`          | int         | 是否启用 CI（update 响应可能出现）                    |

create 响应示例：

```json
{
  "error_code": 0,
  "error_message": "",
  "data": {
    "id": 2000,
    "space_id": 1000,
    "plan_name": "xxx",
    "test_scene": "未分类",
    "enable_ftf": 1,
    "ftf_plan_id": 3000,
    "is_schedule": 0,
    "crontab": "",
    "env_tag_id": 4000,
    "notify_config": "{...}",
    "notify_config_json": null,
    "creator": "sample-user",
    "updater": "sample-user",
    "created_at": "2024-11-18T21:54:16.739+08:00",
    "updated_at": "2024-11-18T21:54:16.739+08:00",
    "deleted_at": null
  }
}
```

### 2.3 存量 `/apix` 详情响应参考（不对应 canonical `plan get`）

get 详情响应在顶层字段（同 2.2 的 `id / space_id / plan_name / test_scene / ftf_plan_id /
is_schedule / crontab / notify_config / notify_config_json / creator / updater /
created_at / updated_at` 等）基础上，额外返回**完整内层 `ftf_plan` 对象**：

`ftf_plan` 内常见字段：

| 字段                                        | 类型                 | 说明                                                                             |
| ------------------------------------------- | -------------------- | -------------------------------------------------------------------------------- |
| `id`                                        | int                  | FTF 内层计划 ID（= 顶层 `ftf_plan_id`）                                          |
| `space_id`                                  | int                  | 空间 ID                                                                          |
| `parent_plan_id`                            | int                  | 父计划 ID                                                                        |
| `name`                                      | string               | 计划名称（内层）                                                                 |
| `use_desc`                                  | string               | 用途描述                                                                         |
| `env`                                       | string               | `boe` / `online`                                                                 |
| `bind_psm`                                  | string               | 绑定的 PSM                                                                       |
| `replay_assert_mode` / `replay_module_mode` | int                  | 断言 / 回放模块模式                                                              |
| `case_filter_mode`                          | int                  | 用例筛选类型                                                                     |
| `directory_conditions`                      | string               | 目录条件（JSON 字符串）                                                          |
| `create_user` / `update_user`               | string               | 创建人 / 更新人                                                                  |
| `single_scene_replay_count`                 | int                  | 单场景回放条数                                                                   |
| `replay_time_limit`                         | int                  | 回放时长（分钟）                                                                 |
| `method_replay_count`                       | int                  | 单接口回放条数                                                                   |
| `noflow_abort_duration`                     | int                  | 无流量停止时间（秒）                                                             |
| `status_callback_switch`                    | int                  | 回调开关                                                                         |
| `psm_exec_params`                           | map[psm]PSMExecParam | PSM 回放参数（结构见 1.4，响应侧还含 `id` / `test_plan_id` / `method_param` 等） |
| `directory_list`                            | array/null           | 目录列表                                                                         |
| `select_directory_list`                     | object               | 场景目录选择                                                                     |
| `is_open_advanced_filter`                   | int/bool             | 是否开启高级筛选                                                                 |
| `advanced_filter_group_brief`               | string               | 高级筛选摘要                                                                     |
| `advanced_filter_group_list`                | array                | 高级筛选组（结构见 1.5，响应侧还含 `id` / `plan_id` / `create_user`）            |
| `enabled`                                   | bool                 | 是否启用                                                                         |
| `is_base_test_plan`                         | int                  | 是否基准测试计划                                                                 |
| `is_open_base_compare`                      | int                  | 是否开启基准对比降噪                                                             |

get 详情响应结构示例（截断）：

```json
{
  "error_code": 0,
  "error_message": "",
  "data": {
    "id": 2000,
    "space_id": 1000,
    "plan_name": "sample plan",
    "test_scene": "研发自测",
    "ftf_plan_id": 3000,
    "is_schedule": 0,
    "notify_config_json": {
      "notify_groups": [],
      "notify_switch": ["tesla", "ftf"],
      "notify_types": ["manual", "schedule", "devops"],
      "notify_users": ["sample-user"]
    },
    "creator": "xxxxx",
    "updater": "xxxxx",
    "created_at": "2024-11-19T17:28:22+08:00",
    "updated_at": "2024-11-19T17:28:22+08:00",
    "ftf_plan": {
      "id": 3000,
      "space_id": 1000,
      "parent_plan_id": 0,
      "name": "sample plan",
      "use_desc": "研发自测",
      "env": "boe",
      "bind_psm": "example.psm",
      "case_filter_mode": 1,
      "create_user": "sample-user",
      "single_scene_replay_count": 10,
      "replay_time_limit": 30,
      "method_replay_count": 100,
      "noflow_abort_duration": 60,
      "psm_exec_params": {
        "example.psm": {
          "id": 5000,
          "psm": "example.psm",
          "test_plan_id": 3000,
          "replay_qps_limit": 10,
          "assert_scene": "default",
          "idl_version": "master",
          "replay_env": "sample_env",
          "method_param_detail": [
            { "method": "GetDemo", "protocol": "thrift", "mock_enable": 1, "new_method": "GetDemo" }
          ]
        }
      },
      "advanced_filter_group_list": [
        {
          "id": 6000,
          "plan_id": 3000,
          "teslax_space_id": { "op": "eq", "value": 1000 },
          "psm": { "op": "eq", "value": "example.psm" },
          "flow_source": { "op": "eq", "value": "sdk" }
        }
      ],
      "enabled": false,
      "is_base_test_plan": 0,
      "is_open_base_compare": 0
    }
  }
}
```

### 2.4 delete 响应

`DELETE /apix/space/:spaceId/plan/:planId` 无请求体（骨架用 `httpDeleteJson(url, {}, headers)`
传空对象占位）。响应同样是 `error_code / error_message` envelope，成功为 `0 / ""`；
`data` 内容以后端实际返回为准（通常回显被删除计划的 id 或为空）。

> 响应 envelope 使用 `error_code / error_message` 时，bytedcli 会按 `error_code=0` 识别成功；非 0 会抛 `FTF_API_ERROR`。
