# TeslaX Plan CRUD 完整 IDL（入参 / 出参）

> 本文件是 `tesla plan create/get/update/delete` 四个命令的 IDL 参考，供 `references/plan-crud.md` 引用。字段口径以 bytedance-tesla skill 的
> `references/teslax/plan/plan-crud.md` 为准（本文档只保留 bytedcli TeslaX CLI 需要的字段口径）。
>
> **两套入口，注意区分：**
>
> - **bytedcli tesla CLI 实际走的是 Tesla-X apix 直连**：`{FTF_TESLAX_HOSTS[env]}/apix/space/:spaceId/plan[/:planId]`，
>   鉴权头为 `ftfTeslaxAuthHeaders`（`Authorization` + `X-Jwt-Token`），响应 envelope 为
>   `error_code / error_message`（成功为 `0 / ""`）。
> - `api-plan.md` 文档描述的是 nova-manager OpenAPI 代理路径
>   `/openapi/teslax/:spaceId/plan[/:planId]`，二者是**两套入口**，但 body / response 的
>   业务字段结构一致，本文件的字段表对两者通用。
>
> CLI 侧只对**顶层浅字段**提供命名 flag（`{ ...base, ...extra }`，`--payload` 覆盖命名 flag）；
> 内层 `ftf_plan.*`、`psm_exec_params`、`notify_config_json`、`advanced_filter_group_list`
> 等深结构**没有专门 flag，一律通过 `--payload '{}'` 深合并注入**。

---

## 1. 请求入参（Request Body）

### 1.1 外层 body 顶层字段

创建 / 更新时 body 的顶层字段（`POST /apix/space/:spaceId/plan`、`PUT /apix/space/:spaceId/plan/:planId`）：

| 字段                 | 类型      | 必填         | CLI flag             | 说明                                                                                                                                                                      |
| -------------------- | --------- | ------------ | -------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `plan_name`          | string    | 是（create） | `--plan-name`        | 测试计划名称。create 侧 CLI 强制必填（早失败）；update 传入即覆盖                                                                                                         |
| `enable_tesla`       | bool/int  | 是           | 自动默认             | **恒为 true**。`tesla plan create` 默认写入 `true`                                                                                                          |
| `enable_ftf`         | bool/int  | 是           | 自动默认             | **恒为 false**（TeslaX-only 计划不启用 FTF）。`tesla plan create` 默认写入 `false`                                                                          |
| `test_scene`         | string    | 是           | `--test-scene`       | 枚举：`研发自测` / `新需求测试` / `全回归` / `核心功能回归` / `线上巡检` / `未分类`。**create 未显式传时默认落 `"研发自测"`**（`DEFAULT_TEST_SCENE`）；CLI 不做白名单校验 |
| `is_schedule`        | int (0/1) | 否           | 无（走 `--payload`） | 是否开启定时执行                                                                                                                                                          |
| `crontab`            | string    | 否           | 无（走 `--payload`） | crontab 语法字符串，如 `10 5 3 * 5`                                                                                                                                       |
| `notify_config_json` | object    | 否           | 无（走 `--payload`） | 通知配置对象，结构见 1.2                                                                                                                                                  |
| `ftf_plan`           | object    | 是           | 无（走 `--payload`） | FTF 内层计划配置，结构见 1.3。CLI 默认平铺透传、不加 `ftf_plan` 嵌套；若后端要求两层结构，用 `--payload '{"ftf_plan":{...}}'` 注入                                        |

> ⚠️ **平铺透传 vs 两层结构**：CLI 实现 `buildPlanCreatePayload/UpdatePayload` 默认把
> `enable_tesla / enable_ftf / --plan-name / --psm / --description / --test-scene / --replay-env / --idl-version /
--case-set-id / --parent-plan-id` 平铺到 body 顶层，**不**自动包一层 `ftf_plan`。
> `api-plan.md` 官方示例 body 是 `{ plan_name, enable_ftf, test_scene, ..., ftf_plan:{...} }`
> 的两层结构；若集成后报字段缺失或写不到内层，用 `--payload '{"ftf_plan":{...}}'` 手工补齐
> 。

### 1.2 `notify_config_json` 结构

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

### 1.3 内层 `ftf_plan` 关键字段

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
| `advanced_filter_group_list` | array                | 否   | 高级筛选组数组，结构见 1.5                   |

### 1.4 `psm_exec_params.<psm>` 关键字段（PSMExecParam，与 Task PSMRunParam 类似）

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

### 1.5 `advanced_filter_group_list[]`（与 Task 的 AdvancedFilterGroup 一致）

字段一般为 `{"op": <操作符>, "value": <值>}` 形式，例：

| 字段                                                                                   | 示例                                                                   |
| -------------------------------------------------------------------------------------- | ---------------------------------------------------------------------- |
| `teslax_space_id`                                                                      | `{"op":"eq","value":540}`                                              |
| `nario_space_id`                                                                       | `{"op":"in","value":[202]}`                                            |
| `psm`                                                                                  | `{"op":"eq","value":"example.psm"}`                                    |
| `scene_meta`                                                                           | `{"op":"in","value":[86972,86971]}`                                    |
| `record_time`                                                                          | `{"op":"since","value":["2024-11-05 17:26:26","2024-11-19 17:26:26"]}` |
| `flow_source`                                                                          | `{"op":"eq","value":"sdk"}`                                            |
| `pid`                                                                                  | `{"op":"in","value":["<pid1>","<pid2>"]}`                              |
| `case_total_replay_limit` / `single_method_replay_limit` / `single_scene_replay_limit` | int                                                                    |

### 1.6 CLI 命名 flag → 顶层 IDL 字段映射（CLI 实现）

| flag               | IDL 字段           | 类型   | 备注                                                                                                                                                             |
| ------------------ | ------------------ | ------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `--space-id`       | `space_id`（path） | int    | 四个命令都必填                                                                                                                                                   |
| `--plan-id`        | `plan_id`（path）  | int    | get / update / delete 必填                                                                                                                                       |
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

响应 envelope 为 `error_code / error_message`（成功 `0 / ""`），业务体在 `data`。

### 2.1 create / update 响应 `data` 字段

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
    "id": 1780,
    "space_id": 540,
    "plan_name": "xxx",
    "test_scene": "未分类",
    "enable_ftf": 1,
    "ftf_plan_id": 1169,
    "is_schedule": 0,
    "crontab": "",
    "env_tag_id": 978,
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

### 2.2 get 详情响应 `data` 字段（含内层 `ftf_plan{...}`）

get 详情响应在顶层字段（同 2.1 的 `id / space_id / plan_name / test_scene / ftf_plan_id /
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
    "id": 1810,
    "space_id": 540,
    "plan_name": "sample plan",
    "test_scene": "研发自测",
    "ftf_plan_id": 1196,
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
      "id": 1196,
      "space_id": 540,
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
          "id": 2155,
          "psm": "example.psm",
          "test_plan_id": 1196,
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
          "id": 176,
          "plan_id": 1196,
          "teslax_space_id": { "op": "eq", "value": 540 },
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

### 2.3 delete 响应

`DELETE /apix/space/:spaceId/plan/:planId` 无请求体（骨架用 `httpDeleteJson(url, {}, headers)`
传空对象占位）。响应同样是 `error_code / error_message` envelope，成功为 `0 / ""`；
`data` 内容以后端实际返回为准（通常回显被删除计划的 id 或为空）。

> 响应 envelope 使用 `error_code / error_message` 时，bytedcli 会按 `error_code=0` 识别成功；非 0 会抛 `FTF_API_ERROR`。
