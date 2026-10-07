# FTF Task、Report 与 Flow API

## 章节索引

- [用途](#用途)
- [online 回放预览确认](#online-回放预览确认)
- [CLI 到接口映射](#cli-到接口映射)
- [任务操作](#停止任务)
- [报告与 Flow](#获取-method-报告)
- [独立创建任务](#独立创建任务)
- [高级筛选与后端参考](#高级筛选组)

## 用途

本文件整理 FTF task、report、flow 相关 API 口径，帮助解释 `bytedcli ftf task/report/flow` 的请求字段、响应字段和枚举含义。report 和 flow 都是 task 执行结果的查询视角，因此在同一文件维护。枚举值见 `enums.md`。

## 接口接入约束

本次新增及后续新增的 FTF 命令只能调用 TeslaX v1 API，实际请求路径统一为 gateway `/ftf/...`，并携带 `Domain: teslax;v1` 与 `X-Jwt-Token`。新增实现只声明 `/ftf` 下的业务 path suffix，不得把旧 `/openapi/...` 入口当作 FTF OpenAPI。

新增命令禁止使用 `/apix/...`、Nova Manager、assert、nova-assertion、Tesla-X 页面代理或 FTF2.0 OpenAPI，也不得在 TeslaX v1 请求失败后自动回退到这些链路。仓库基线中已经存在的 `/apix/...` plan 管理和 assert `/nova/...` 深度诊断能力仅为兼容保留，后续会迁移到 TeslaX v1，不能作为新增命令的实现依据。

gateway 默认走办公网 host；`BYTEDCLI_NETWORK_PROFILE=prod` 时按 FTF 分区切换到生产网 host。当前 bytedcli 已封装的接口优先使用 CLI 命令，不建议手写 HTTP 请求。

### 站点与 ID 门禁

Tesla-X URL 先用 `bytedcli --json ftf target parse --url "<ftf-url>"`，冻结返回的 `site` 与
selector。URL 命令自身会自动派生站点；工作流仍须将解析结果与用户明确声明的目标站点对比，
如不一致，在任何派生 ID 查询前停止。后续从 URL 改用 ID 的命令必须显式复用全局路由：cn
用 `--site cn`，zg 用 `--site cn --vregion China-Pay`；两者都放在 `ftf` 前。只给裸 ID 时先要求
明确 cn/zg，不从 ID、默认配置、响应字段或登录态猜测。下文裸 ID 示例均以 cn 为例；zg 按上述
规则追加 `--vregion China-Pay`。

## 输出契约

- `--json` 使用 bytedcli 统一 `status/data/error/context` 外壳。业务 payload 直接位于 `.data`；
  canonical Nova envelope 的 `code/msg/log_id/data` 完整保存在 `.context.backend`，endpoint 和
  分区位于 `.context.api_endpoint` / `.context.env`。
- canonical list 将数组放入语义化 key（`tasks`、`flows` 等），同时保留后端其它同级字段与
  真实分页；后端未返回 `total` 时输出 `page_count`，不会用当前页条数伪造总数。
- analysis/diff 编排命令保留稳定摘要，并通过 `raw`、`full_result`、`source_data`、
  `sources[].data` 保存完整后端业务响应。
- 非 `--json` 输出不会直接打印超大 payload：列表采用固定业务列和分页，详情展示完整字段，
  写操作展示目标与回执，diff/analysis 展示任务、聚类、代表值与链接。
- online `plan execute` / `task create` 预览的 `.sources` 保留计划详情和 Method 目录查询的
  完整来源响应；`methods` 仍是便于确认的稳定字段。

## online 回放预览确认

canonical `ftf task create` 以最终请求 body 的 `env` 决定是否需要二次确认：

- `env=online` 且未传 `--yes`：从 `psm_trigger_params` 和 `advanced_filter_group_list` 解析本次 PSM / Method。显式 Method 直接展示；`*`、高级筛选或未提供显式 Method 时，通过 TeslaX v1 `POST /ftf/method/query/by_conditions`（`{ "psm": "<psm>", "read_only": true }`）展开当前只读接口，并按高级筛选 Method 取交集。CLI 输出预览后停止，不创建任务。
- `env=online` 但无法解析任何 Method：返回 `FTF_PLAN_PREVIEW_ERROR`，要求先补齐请求范围。
- `env=boe`：不做 Method 预查或确认，直接调用 `POST /ftf/create/task`。
- 已传 `--yes`：不检查业务 `env`，也不查询 Method，直接调用创建接口。
- 预览只用于让用户确认本次 online 回放范围，不根据 `access_status` 在 CLI 自动阻断；后端仍负责最终接口过滤。

## CLI 到接口映射

| CLI 命令                               | Gateway API                                                                                             | 状态                                                       |
| -------------------------------------- | ------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------- |
| `ftf task stop`                        | `POST /ftf/stop/task`                                                                                   | 已封装，写操作需父级 `--yes`                               |
| `ftf task list`                        | `GET /ftf/task/list/by_page`                                                                            | 已封装                                                     |
| `ftf task get --id`                    | `GET /ftf/query/task`                                                                                   | 已封装；`--task-id` 为过渡期隐藏别名                       |
| `ftf task report get`                  | task：`POST /ftf/task/aggregate/report/task`；PSM/method：`POST /ftf/task/aggregate/report/{dimension}` | 已封装                                                     |
| `ftf task report reason list`          | `GET /ftf/query/task`                                                                                   | CLI 在 service 层聚合 diff/失败原因                        |
| `ftf task report summary`              | `POST /ftf/mcp/get/report_brief`                                                                        | 已封装；批量任务简报                                       |
| `ftf task report export`               | `POST /ftf/mcp/get/report_brief/render`                                                                 | 已封装；返回渲染态报告数据                                 |
| `ftf task flow list`                   | `POST /ftf/task/aggregate/flow/list`                                                                    | 已封装                                                     |
| `ftf task flow get`                    | `POST /ftf/task/aggregate/flow/get`                                                                     | 已封装                                                     |
| `ftf task retry`                       | `POST /ftf/task/retry`                                                                                  | bytedcli 扩展，写操作需 `--yes`                            |
| `ftf task create`                      | `POST /ftf/create/task`                                                                                 | 已封装；仅 online 需预览确认                               |
| online 预览内部调用                    | `POST /ftf/method/query/by_conditions`                                                                  | 展开只读 Method 供用户确认                                 |
| `ftf task intelligent-attribution get` | `POST /denoise/query_attribute_report` (TSP CN-only)                                                    | 已封装；本地支持 `--classifier` / `--similar-diff-id` 过滤 |

## 停止任务

- Gateway Path：`POST /ftf/stop/task`
- CLI：`bytedcli --site cn ftf --yes task stop --id 1234567 --source bytedcli --call-status assert`

### Query

| 参数         | 必填 | 说明                                                    |
| ------------ | ---- | ------------------------------------------------------- |
| `taskId`     | 是   | 任务 ID                                                 |
| `source`     | 否   | 调用方标识                                              |
| `callStatus` | 否   | CLI 用 `assert` / `abort`，handler 映射为后端 `0` / `1` |

CLI 参数名为 `--source`、`--reason` 和 `--call-status`。

## 查询任务列表

- Gateway Path：`GET /ftf/task/list/by_page`
- CLI：`bytedcli ftf task list --page 1 --page-size 20`

### Query

| 参数             | 必填 | 说明                                          |
| ---------------- | ---- | --------------------------------------------- |
| `page`           | 是   | 分页页码，CLI 默认 `1`                        |
| `page_size`      | 是   | 分页大小，CLI 默认 `20`                       |
| `psm`            | 否   | 回放 PSM 筛选；不传时按其它筛选或分页查询     |
| `space_id`       | 否   | TeslaX 空间 ID，CLI 参数为 `--space-id`       |
| `parent_plan_id` | 否   | TeslaX parent plan id，CLI 参数为 `--plan-id` |
| `trigger_type`   | 否   | 触发类型，见 `enums.md#trigger_type`          |
| `status`         | 否   | 任务状态，见 `enums.md#status`                |
| `filter_time`    | 否   | 最近 N 天                                     |

CLI 对外使用语义值，例如 `--trigger-type manual`、`--status running`，handler 会映射到后端数字。

## 获取任务基本信息

- Gateway Path：`GET /ftf/query/task`
- CLI：`bytedcli --site cn ftf task get --id 1234567`
- 兼容：过渡期仍接受隐藏参数 `--task-id`，新调用统一使用 `--id`
- Query：`taskId=<task_id>`

### 响应关键字段

| 字段                                                                                     | 说明                                     |
| ---------------------------------------------------------------------------------------- | ---------------------------------------- |
| `id`                                                                                     | 任务 ID                                  |
| `test_plan_id` / `parent_plan_id`                                                        | 关联测试计划 ID                          |
| `space_id`                                                                               | TeslaX 空间                              |
| `trigger_type`                                                                           | 触发类型                                 |
| `status` / `detail_status`                                                               | 任务状态和详细状态，见 `enums.md`        |
| `task_run_time`                                                                          | 运行时长                                 |
| `case_filter_mode`                                                                       | 流量来源，见 `enums.md#case_filter_mode` |
| `run_psm`                                                                                | 主 PSM                                   |
| `single_scene_replay_count`                                                              | 单场景回放条数                           |
| `status_callback_switch`                                                                 | 回调开关                                 |
| `case_count` / `diff_case_count` / `need_confirm_case_count` / `fail_case_count`         | 用例数、diff 数、待确认数、失败数        |
| `create_time` / `update_time` / `finish_time`                                            | 时间                                     |
| `nario_task_id` / `scene_coverage_detail` / `scene_coverage`                             | 场景覆盖度                               |
| `code_coverage` / `code_coverage_url` / `code_coverage_detail`                           | 代码覆盖度                               |
| `psm_replay_param_detail`                                                                | PSM 级回放参数详情，含 method 参数       |
| `task_duration`                                                                          | 任务耗时，通常为分钟                     |
| `task_flow_count`                                                                        | 流量条数                                 |
| `demand_items`                                                                           | 关联需求                                 |
| `parent_plan_name`                                                                       | 测试计划名                               |
| `is_open_advanced_filter` / `advanced_filter_group_brief` / `advanced_filter_group_list` | 高级筛选                                 |
| `inherited_branches`                                                                     | 继承分支                                 |
| `enable_base_compare` / `base_task_id`                                                   | 基准任务对比                             |

分析任务是否可消费时，优先结合 `status` 和 `detail_status` 的终态判定。

## 获取 Task/PSM 聚合报告

- Task Gateway Path：`POST /ftf/task/aggregate/report/task`
- PSM Gateway Path：`POST /ftf/task/aggregate/report/psm`
- CLI：`bytedcli --site cn ftf task report get --dimension task --id 1234567`
- CLI：`bytedcli --site cn ftf task report get --dimension psm --id 1234567 --psm example.psm`

普通文本模式将 task 结果按 PSM、PSM 结果按 method 展开为统计表，不直接倾倒嵌套对象；
`--json` 保留完整业务响应，供归因流程取证。PSM 聚合中的 method 条目是实际回放接口的
权威清单：每个条目的 `total` 是该接口回放流量数，`failed_reason` map 中全部枚举值的加和是
该接口回放失败流量数，两者之差是该接口有效流量数。

## 获取 Method 报告

- Gateway Path：`POST /ftf/task/aggregate/report/method`
- CLI：`bytedcli --site cn ftf task report get --dimension method --id 1234567 --psm example.psm --method GetDemo`

### Body

```json
{
  "task_id": 1234567,
  "psm": "example.psm",
  "method": "GetDemo"
}
```

### 响应关键字段

| 字段                           | 说明                                                   |
| ------------------------------ | ------------------------------------------------------ |
| `protocol`                     | 协议                                                   |
| `method` / `http_method`       | 接口                                                   |
| `total`                        | 总流量数                                               |
| `diff_count`                   | diff 数                                                |
| `confirm_count`                | 已确认数                                               |
| `replay_failed_reason`         | method 聚合的回放失败线索；null 只表示该字段无证据     |
| `is_diff_covered`              | diff 是否已覆盖                                        |
| `diff_reason`                  | `map[reason_code]count`                                |
| `replay_status_failed_count`   | 回放失败数                                             |
| `log_id_classify_map`          | `map[failed_reason][]log_id`，回放失败聚类逐条流量来源 |
| `diff_reason_aggregate_result` | 按噪音模板聚合的 diff 分布                             |
| `diffs`                        | `map[pid]DiffDetail`，键不要长期依赖                   |

该接口返回某个 method 的聚合结果，全部接口逐个聚合可能较重。必须先从 task detail 的 PSM
范围和 `task flow list` 的实际 PSM/method 建立 method 集，再对发现的 method 查询；不得猜测
PSM/method 扇出。分析 task diff 时优先使用 `task evidence get` 或 `task analyze`，需要下钻单
method 时再查该接口。`replay_failed_reason=null` 不证明没有回放失败，仍须与 task
`failed_reason_count`、`replay_status_failed_count`、Flow 列表和单条 `failed_reason` 对账。

按 `method × failed_reason` 做回放失败聚类时，代表流量 `log_id` 从 `log_id_classify_map` 取；每个聚类必须附代表流量“查看 diff 明细”链接，拼接规则见 `diff-query-reference.md` 的“Flow diff 链接拼接”与 `task-diff-triage.md` 的“聚类必须附「查看 diff 明细」链接”。

## 批量任务简报与渲染导出

- Gateway Path：`POST /ftf/mcp/get/report_brief`（`task report summary`）、`POST /ftf/mcp/get/report_brief/render`（`task report export`）
- CLI：
  ```bash
  bytedcli --json --site cn ftf task report summary --ftf-task-ids 1234567,1234568
  bytedcli --json --site cn ftf task report export --ftf-task-ids 1234567
  ```
- 用途区分：`summary` 返回批量任务的简报字段，适合一次性核对多个任务的整体状态；`export` 返回同一批任务的渲染态报告数据，适合直接呈现。两者都不是任务级归因报告——完整归因仍由 `task-analysis.md` 编排。

### Selector 与优先级

| 参数                    | 说明                                                        |
| ----------------------- | ----------------------------------------------------------- |
| `--ftf-task-ids`        | 逗号分隔 FTF 任务 ID（正整数），映射 `ftf_task_id_list`     |
| `--tesla-task-ids`      | 逗号分隔 Tesla 任务 ID，映射 `tesla_task_id_list`           |
| `--tesla-repo-task-ids` | 逗号分隔 Tesla repo 任务 ID，映射 `tesla_repo_task_id_list` |
| `--request-json`        | `BatchQueryTaskBriefInfo` 请求文件路径                      |

`--request-json` 优先级最高，提供后覆盖上述全部 ID selector；三类 ID 全部为空且未给 `--request-json` 时抛 `FTF_INPUT_ERROR`。

## 获取 Flow 列表

- Gateway Path：`POST /ftf/task/aggregate/flow/list`
- CLI：首次查询可使用 `bytedcli --site cn ftf task flow list --task-id 1234567 --page-size 100` 获取首批
  流量，也可追加 `--psm example.psm --method GetDemo` 缩小范围。该命令不会自动翻页；响应
  `has_more=true` 时，把 `next_cursor` 作为 `--cursor` 继续查询，直到 `has_more=false` 或达到
  `diag-replay-failure.md#第一步读任务终态与失败聚类` 定义的请求预算；遇到 429 或连续超时
  立即停止。未读完时只能建立已覆盖范围的索引，结论必须标为“部分”并列出证据缺口。
- 迁移：旧的 `ftf flow list --task-id ...` 路径已移除；任务维度流量列表统一使用 `ftf task flow list`

### Body

| 字段        | 必填 | 说明                                           |
| ----------- | ---- | ---------------------------------------------- |
| `task_id`   | 是   | 任务 ID                                        |
| `psm`       | 否   | PSM 筛选                                       |
| `method`    | 否   | method 筛选                                    |
| `page_size` | 是   | 分页大小，建议 `1-100`                         |
| `cursor`    | 否   | 首次查询不传；续查时传上次响应的 `next_cursor` |

### 响应关键字段

```json
{
  "code": 0,
  "data": {
    "flows": [
      {
        "pid": "sample-pid",
        "log_id": "sample-logid",
        "logid_benchmark": "sample-base-logid",
        "logid_comparison": "sample-replay-logid"
      }
    ],
    "next_cursor": "sample-next-cursor"
  },
  "log_id": "...",
  "message": ""
}
```

## 获取 Flow 详情

- Gateway Path：`POST /ftf/task/aggregate/flow/get`
- CLI：`bytedcli --site cn ftf task flow get --task-id 1234567 --pid sample-pid`
- 迁移：旧的 `ftf flow get --task-id ...` 路径已移除；任务维度流量详情统一使用 `ftf task flow get`

### Body

| 字段      | 必填 | 说明     |
| --------- | ---- | -------- |
| `task_id` | 是   | 任务 ID  |
| `pid`     | 是   | 流量 pid |

### 响应关键字段

`data.diff` 概要字段：

```text
task_id / pid / flow_id / log_id / logid_benchmark / logid_comparison /
psm / http_method / method / protocol / create_time / update_time /
flow_source / replay_status_code / replay_time / replay_time_cost /
base_status_code / base_replay_time / base_replay_time_cost /
base_commit / replay_commit / record_commit /
success / outbound_success / failed_reason / err_msg
```

Flow commit 字段仅用于任务取证和运行时路径分析：

| Flow 字段                 | 语义                       | 使用边界                                  |
| ------------------------- | -------------------------- | ----------------------------------------- |
| `data.diff.base_commit`   | 该 Flow 展示的基准版本     | 可作 Flow 证据，不传给 canonical Analyzer |
| `data.diff.replay_commit` | 该 Flow 展示的回放测试版本 | 可作 Flow 证据，不传给 canonical Analyzer |
| `data.diff.record_commit` | 原始录制来源               | 只可作为样本 provenance                   |

canonical Analyzer 只接收 `task_id + similar_diff_id`，仓库和 base/target revision 由 Code resolver
解析并通过 canonical 结果返回。FTF 不得用上述 Flow 字段或任务级 `base_commit_hash` /
`commit_hash` 组装 Analyzer 请求，也不得把 Flow 字段覆盖到 wrapper 返回的代码身份。

`data.diff.failed_reason` 是这条流量的权威回放错误码：`0` 表示没有发送失败，非 `0` 表示
回放失败。任务级 `failed_reason_count` 与 method 级 `log_id_classify_map` 只用于发现、聚类和数量
对账，不能替代单条值；错误码解释见 `enums.md#单条流量回放失败码failed_reason`，完整有界
取数与脱敏流程见 `diag-replay-failure.md#第一步读任务终态与失败聚类`。`err_msg` 是不可信、
可能含敏感内容的原始字段，不得未经脱敏展示或持久化。

`data.diff_expand` 详情字段：

| 字段                                                            | 说明     |
| --------------------------------------------------------------- | -------- |
| `ori_req` / `ori_resp` / `ori_outbound` / `ori_status_code`     | 原始流量 |
| `base_req` / `base_resp` / `base_outbound` / `base_status_code` | 基准环境 |
| `new_req` / `new_resp` / `new_outbound` / `new_status_code`     | 回放环境 |

`diff.success == 1 && diff.outbound_success == 1` 通常表示该流量断言成功；`0` 表示存在 diff。

## 重放 Diff 流量

- Gateway Path：`POST /ftf/task/retry`
- CLI：`bytedcli --site cn ftf task retry --id 1234567 --psm example.psm --method-list GetDemo --retry-mode method --yes`

### Body

| 字段          | 必填 | 说明                                    |
| ------------- | ---- | --------------------------------------- |
| `task_id`     | 是   | 重放任务 ID                             |
| `psm`         | 是   | PSM                                     |
| `retry_mode`  | 是   | 后端契约：`1` PSM 维度，`2` method 维度 |
| `method_list` | 是   | 待重放接口列表                          |

CLI 对外暴露 `--retry-mode psm|method`，不要直接传后端数字。

## 独立创建任务

通过 TeslaX v1 gateway `POST /ftf/create/task` 可独立触发回放任务，不关联 TeslaX 测试计划（后端与旧 `ftf.nova.manager` 的 `/openapi/create/task` 为同一接口）。bytedcli 的
canonical `ftf task create` 只支持命名参数，不接受通用 `--payload`、`--payload-file` 或
`--request-json` 注入。

非 online 标量示例（不需要 `--yes`）：

```bash
bytedcli --site cn ftf task create \
  --space-id 1000 \
  --psm example.psm \
  --env boe \
  --replay-env boe_sample \
  --case-filter-mode scene \
  --task-run-time 30 \
  --noflow-abort-duration 300 \
  --single-scene-replay-count 1 \
  --method-replay-count 100
```

online 脚本参数示例：

```bash
bytedcli --site cn ftf task create \
  --space-id 1000 \
  --psm example.psm \
  --env online \
  --replay-env online \
  --method-list GetDemo \
  --inbound-before-script 'return request' \
  --inbound-after-script 'return response'

# 检查 Method 预览并获得用户确认后，原命令增加 --yes
bytedcli --site cn ftf task create \
  --space-id 1000 \
  --psm example.psm \
  --env online \
  --replay-env online \
  --method-list GetDemo \
  --inbound-before-script 'return request' \
  --inbound-after-script 'return response' \
  --yes
```

说明：

- canonical FTF host 分区来自 bytedcli 全局 `--site` / `--vregion`；task create 的 `--env` 是请求体业务环境，只接受 `online|boe`。
- `--create-user` 是可选覆盖；未传时使用当前 bytedcli 登录用户名。
- `--case-filter-mode` 只接受 `realtime`、`scene`、`non-realtime`、`third-party`，分别映射为后端 `0`、`1`、`2`、`4`。
- 标量模式会根据 `--psm` 和 `--replay-env` 生成 `psm_trigger_params.<psm>.replay_env`；`--replay-cluster`、`--replay-region`、`--replay-host`、`--replay-psm`、`--method-list`、`--record-env`、`--record-time-last`、`--flow-source` 等会继续补充回放目标和高级筛选字段。
- `--bytecopy-psm`、`--bytecopy-stage`、`--bytecopy-cluster`、`--bytecopy-region` 均为可选字符串，分别写入 `psm_trigger_params.<psm>` 的 `bytecopy_psm`、`bytecopy_stage`、`bytecopy_cluster`、`bytecopy_idc`；未传时这些字段保持空字符串。
- `--inbound-before-script <script>` 与 `--inbound-after-script <script>` 直接接收脚本文本，分别写入回放前和回放后脚本；参数值不会被当作路径读取。
- canonical `task create` 不提供通用 JSON 合并或完整请求覆盖入口；复杂需求必须使用已登记的 named flags。
- 仅 `env=online` 需要 Method 预览和用户确认；非 online 不需要 `--yes`。canonical 命令不接受 `--execute`。
- `--yes` 可放在写子命令后，也兼容放在 `ftf` 后；带 `--yes` 时跳过预览，直接创建。
- 创建成功后 CLI 会立即查询 task detail，并输出任务 ID、Space ID、PSM、创建时间和
  Tesla-X Task URL。

关键 body 字段：

| 字段                                     | 标量模式必填 | 说明                                                          |
| ---------------------------------------- | ------------ | ------------------------------------------------------------- |
| `create_user`                            | 是           | 用户名；CLI 可从当前登录信息补齐                              |
| `space_id`                               | 是           | TeslaX 空间 ID                                                |
| `env`                                    | 是           | `online` 或 `boe`                                             |
| `psm_trigger_params.<psm>.replay_env`    | 是           | 指定 PSM 的回放泳道，由 `--psm` + `--replay-env` 生成         |
| `case_filter_mode`                       | 否           | 流量来源，见 `enums.md#case_filter_mode`；CLI 默认 `scene`    |
| `task_run_time`                          | 否           | 任务执行时长，单位分钟；CLI 默认 1                            |
| `noflow_abort_duration`                  | 否           | 无流量停止时间；默认 600，`0` 关闭，正数为 60–3600 秒         |
| `single_scene_replay_count`              | 否           | 单场景回放条数，仅场景流量生效；CLI 默认 5                    |
| `method_replay_count`                    | 否           | 单接口回放条数，非场景流量生效；CLI 默认 5000                 |
| `replay_mode` / `status_callback_switch` | 否           | 回放模式（CLI 使用 `normal\|diffy`）与回调开关                |
| `link_replay` / `not_masked`             | 否           | 链路回放与脱敏开关                                            |
| `inherited_branches`                     | 否           | 继承分支                                                      |
| `notify_groups` / `notify_users`         | 否           | 固定通知群或通知人                                            |
| `psm_trigger_params.<psm>.bytecopy_*`    | 否           | ByteCopy PSM、stage、cluster 与 IDC，由四个 ByteCopy 参数生成 |
| `psm_trigger_params`                     | 自动生成     | 由 `--psm` 及回放、IDL、Method、脚本等 named flags 生成       |

## 高级筛选组

`AdvancedFilterGroup` 表示一组独立筛选条件，字段一般是 `{ "op": "...", "value": ... }`：

| 字段                         | 说明                                                |
| ---------------------------- | --------------------------------------------------- |
| `teslax_space_id`            | TeslaX 空间，例如 `{"op":"eq","value":1000}`        |
| `psm`                        | PSM，例如 `{"op":"eq","value":"example.psm"}`       |
| `method`                     | method 列表，例如 `{"op":"in","value":["GetDemo"]}` |
| `scene_meta`                 | 模板 ID                                             |
| `psm_scene`                  | 场景 ID 列表                                        |
| `caseset`                    | 用例集                                              |
| `record_env`                 | 录制泳道，例如 `prod`                               |
| `record_idc`                 | 录制机房，例如 `lf`                                 |
| `record_cluster`             | 录制集群                                            |
| `record_time`                | 录制时间范围                                        |
| `flow_source`                | 流量来源，例如 `sdk`、`bytecopy`                    |
| `pid`                        | 具体 pid 列表                                       |
| `case_total_replay_limit`    | 本组用例回放整体上限                                |
| `single_method_replay_limit` | 单 method 上限，需要选择 method                     |
| `single_scene_replay_limit`  | 单场景上限，需要选择模板或场景                      |

常见 `op` 包括 `eq`、`in`、`between`。同一个筛选组内多条件共同约束；多个筛选组之间按平台规则组合。

## 后端参考：Neptune ACL 检查

- Gateway Path：`POST /ftf/test_plan/check/neptune_permission_detail`
- 当前 bytedcli 尚未封装。

用途：线上服务可能存在严格授权，回放前若未申请 ACL 权限可能出现未授权错误。该接口用于判断待回放接口是否需要申请 ACL。

Body：

| 字段          | 必填 | 说明           |
| ------------- | ---- | -------------- |
| `psm`         | 是   | 回放 PSM       |
| `method_list` | 是   | 待回放接口列表 |
| `cluster`     | 否   | 指定回放集群   |

Response 关键字段：

| 字段                 | 说明          |
| -------------------- | ------------- |
| `is_all_pass`        | 是否全部通过  |
| `not_access_methods` | 未授权 method |
| `access_methods`     | 已授权 method |
| `apply_acl_url`      | ACL 申请地址  |

## 后端参考：外调 Mock Result

- Gateway Path：`GET /ftf/assertion/aggregate/flow/get_mock_result`
- 当前 bytedcli 尚未封装。

用途：查看指定序号的 outbound 返回结果。接口文档对 Body / Query 标注不完全一致，封装前需要以实际请求行为为准。

参数：

| 字段               | 必填 | 说明                               |
| ------------------ | ---- | ---------------------------------- |
| `task_id`          | 是   | 任务 ID                            |
| `psm`              | 是   | PSM                                |
| `log_id`           | 是   | 流量 log id                        |
| `outbound_index`   | 是   | 目标 outbound 序号                 |
| `trigger_platform` | 否   | 触发平台                           |
| `not_masked`       | 否   | 是否对返回结果加密，`1` 表示不加密 |
