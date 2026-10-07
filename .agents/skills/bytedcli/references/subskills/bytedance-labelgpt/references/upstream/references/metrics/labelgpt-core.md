# LabelGPT 服务指标分析模板

本页用于分析 LabelGPT 的五类核心服务：

- `<MODEL_WEB_PSM>`
- `<FLOW_PSM>`
- `<PLUGIN_PSM>`
- `<MODEL_GATEWAY_PSM>`
- `<DATA_PSM>`

PSM 与业务指标名使用语义占位符，避免把环境相关标识固化在 Skill 中。执行前先从目标
环境或服务 owner 确认 PSM，再用 `metrics search`、`field-list` 和 `tagk-list` 获取真实指标
契约；不要直接把占位符当作命令参数。

所有示例均为只读命令，不要求 `--space-id`。使用绝对 Unix 秒时间窗并优先输出
`--format raw`。指标和 tag 会随埋点演进；先探索，再套用模板。

## 固定分析顺序

1. 对目标 PSM 查通用服务健康：QPS、错误 QPS、延迟、入/出流量。
2. 用 `metrics search --prefix <PSM>` 重新发现当前业务指标；不要只依赖本文静态清单。
3. 对选中的指标执行 `field-list` 和 `tagk-list`。
4. 只对低基数分类 tag，或在业务 ID filter 下执行 `tagv-list`。
5. 用业务 ID、`scene`、成功状态等条件收窄查询后再拉时序。

```bash
bytedcli labelgpt metrics search --prefix <PSM> --limit 100 --format raw
bytedcli labelgpt metrics field-list --metric <METRIC> --format raw
bytedcli labelgpt metrics tagk-list --metric <METRIC> --format raw
bytedcli labelgpt metrics tagv-list \
  --metric <METRIC> --tag <TAG_KEY> --filter <FILTER_KEY>=<FILTER_VALUE> \
  --format raw
```

`field-list` 的判定规则：

- `[]`：单值指标，查询末尾不写 `[field]`。
- `counter, delta, rate`：`delta_counter`；总量用 `[delta]`，速率用 `[rate]`。
- Histogram：使用服务端返回的字段表达式，例如 `[hist_sum()]`。
- 其它字段组合：不要猜字段含义，按返回结果和面板语义确认。

## 五个服务都适用的服务健康指标

以下 BytedTrace Server 指标通过 `_psm` TagRewrite 定位服务。`_psm` 必须固定为单个服务，
不能写 `*` 或一次传多个 PSM，也不存在 `metrics query --psm` flag。

| 目标 | 指标 | 常用过滤/分组 |
|---|---|---|
| QPS | `bytedtrace.sdk.span.server.rate` | `_method`、`_from_service` |
| 延迟 | `bytedtrace.sdk.span.server.latency.us` | `_method`、`_is_error` |
| 入流量 | `bytedtrace.sdk.span.server.receive.bytes` | `_method`、`_from_service` |
| 出流量 | `bytedtrace.sdk.span.server.send.bytes` | `_method`、`_from_service` |
| 错误 QPS | `bytedtrace.sdk.span.server.rate` | `_is_error=literal_or(1)`、`_status_code` |

以 `<PSM>` 替换为五个服务之一：

```bash
# 总 QPS
bytedcli labelgpt metrics query \
  'sum:5m-avg-zero:bytedtrace.sdk.span.server.rate{}{_psm=literal_or(<PSM>)}' \
  --start-time <START_SECONDS> --end-time <END_SECONDS> --format raw

# 按接口拆分 QPS
bytedcli labelgpt metrics query \
  'sum:5m-avg-zero:bytedtrace.sdk.span.server.rate{_method=literal_or(*)}{_psm=literal_or(<PSM>)}' \
  --start-time <START_SECONDS> --end-time <END_SECONDS> --format raw

# 错误 QPS
bytedcli labelgpt metrics query \
  'sum:5m-avg-zero:bytedtrace.sdk.span.server.rate{}{_psm=literal_or(<PSM>),_is_error=literal_or(1)}' \
  --start-time <START_SECONDS> --end-time <END_SECONDS> --format raw

# 平均延迟，原始单位为微秒
bytedcli labelgpt metrics query \
  'avg:5m-avg-zero:bytedtrace.sdk.span.server.latency.us{}{_psm=literal_or(<PSM>)}' \
  --start-time <START_SECONDS> --end-time <END_SECONDS> --format raw
```

需要流量时，把指标替换为 `server.receive.bytes` 或 `server.send.bytes`。比较五个服务时使用
同一时间窗，分别执行五次查询；不要绕过 TagRewrite 把多个 PSM 填入一次查询。

## `<MODEL_WEB_PSM>`

核心业务指标：

| 指标 | 含义 | 字段/类型 | 核心 tag |
|---|---|---|---|
| `<MODEL_WEB_COUNTER_METRIC>` | 模型 Web 请求量/成功失败量 | `counter,delta,rate` | `scene,success,agent_id,caller,channel,sync,error_code` |
| `<MODEL_WEB_P99_METRIC>` | 模型 Web P99 耗时 | 单值 | 与 counter 相同 |
| `<MODEL_WEB_TRACE_COUNTER_METRIC>` | CLI/调用链命令计数 | `counter,delta,rate` | `command,success,tenant_id,user,version,error_code` |

当前常见 `scene` 为 `sync_execute`、`send_label`。先用 `tagv-list` 重新确认。

```bash
# 指定 Agent 的同步执行成功/失败量
bytedcli labelgpt metrics query \
  'sum:5m-sum:<MODEL_WEB_COUNTER_METRIC>{success=literal_or(*)}{scene=literal_or(sync_execute),agent_id=literal_or(<AGENT_ID>)}[delta]' \
  --start-time <START_SECONDS> --end-time <END_SECONDS> --format raw

# 指定 Agent 的同步执行 P99；timer 单位以当前面板/埋点定义为准
bytedcli labelgpt metrics query \
  'avg:5m-avg-zero:<MODEL_WEB_P99_METRIC>{}{scene=literal_or(sync_execute),agent_id=literal_or(<AGENT_ID>),success=literal_or(true)}' \
  --start-time <START_SECONDS> --end-time <END_SECONDS> --format raw
```

`trace_counter` 的 `command` 可用于判断 CLI/调用链命令使用情况。命令值会随版本增加，必须先
查 `tagv-list --tag command`，不要维护封闭枚举。

## `<FLOW_PSM>`

核心业务指标：

| 指标 | 含义 | 字段/类型 | 核心 tag |
|---|---|---|---|
| `<FLOW_COUNTER_METRIC>` | Flow 各 scene 事件量 | `counter,delta,rate` | `scene,success,agent_id,node_id,process_id,model_id,tenant_id,error_code` |
| `<FLOW_NODE_COUNTER_METRIC>` | 节点执行量 | `counter,delta,rate` | 上述 tag，另有 `retry_type` |
| `<FLOW_P99_METRIC>` | Flow 各 scene P99 耗时 | 单值 | 与通用 counter 相同 |
| `<FLOW_BACKLOG_METRIC>` | Agent backlog | 单值 gauge | `agent_id,scene` |
| `<FLOW_AUTO_CONCURRENCY_METRIC>` | 自动并发额度 | 单值 gauge | `agent_id,scene` |
| `<FLOW_AUTO_QPM_METRIC>` | 自动 QPM 额度 | 单值 gauge | `agent_id,scene` |

`counter.delta_counter` 的常见 `scene` 包括 `agent_execute`、`node_execute`、
`agent_first_execute`、`agent_worker`、`phrase_worker`、重试与过期相关场景。不要一次按全部
Agent 展开长时间窗，Flow 指标基数很高。

```bash
# 单个 Agent 执行成功/失败量
bytedcli labelgpt metrics query \
  'sum:5m-sum:<FLOW_COUNTER_METRIC>{success=literal_or(*)}{scene=literal_or(agent_execute),agent_id=literal_or(<AGENT_ID>)}[delta]' \
  --start-time <START_SECONDS> --end-time <END_SECONDS> --format raw

# 单个 Agent 的节点执行成功/失败量
bytedcli labelgpt metrics query \
  'sum:5m-sum:<FLOW_NODE_COUNTER_METRIC>{success=literal_or(*)}{agent_id=literal_or(<AGENT_ID>)}[delta]' \
  --start-time <START_SECONDS> --end-time <END_SECONDS> --format raw

# 单个 Agent 的执行 P99
bytedcli labelgpt metrics query \
  'avg:5m-avg-zero:<FLOW_P99_METRIC>{}{scene=literal_or(agent_execute),agent_id=literal_or(<AGENT_ID>),success=literal_or(true)}' \
  --start-time <START_SECONDS> --end-time <END_SECONDS> --format raw

# 单个 Agent 的 backlog 峰值
bytedcli labelgpt metrics query \
  'max:5m-max-zero:<FLOW_BACKLOG_METRIC>{}{scene=literal_or(agent_backlog),agent_id=literal_or(<AGENT_ID>)}' \
  --start-time <START_SECONDS> --end-time <END_SECONDS> --format raw
```

分析拥塞时，把 backlog 与 `auto_concurrency_gauge`、`auto_qpm_gauge` 放在同一时间窗对照：
backlog 持续升高且额度触顶，通常比单看执行量更能说明容量瓶颈。

## `<PLUGIN_PSM>`

如果 `metrics search --prefix <PLUGIN_METRIC_PREFIX>` 在目标 region 返回空列表：

1. 先查本页的 BytedTrace 通用 QPS、错误 QPS、延迟和流量，`_psm` 固定为
   `<PLUGIN_PSM>`。
2. 每次分析都重新执行前缀搜索；新埋点上线后再按 `field-list/tagk-list/tagv-list` 探索。
3. 搜索仍为空时，不得编造业务 `counter`、`timer` 等指标名。
4. 通用查询也无数据时，只能结论为“该 region/时间窗无匹配时序”，不能结论为服务无流量；
   继续核对 region、时间窗和真实 PSM。

```bash
bytedcli labelgpt metrics search --prefix <PLUGIN_METRIC_PREFIX> --limit 100 --format raw
bytedcli labelgpt metrics query \
  'sum:5m-avg-zero:bytedtrace.sdk.span.server.rate{}{_psm=literal_or(<PLUGIN_PSM>)}' \
  --start-time <START_SECONDS> --end-time <END_SECONDS> --format raw
```

## `<MODEL_GATEWAY_PSM>`

核心业务指标：

| 指标 | 含义 | 字段/类型 | 核心 tag |
|---|---|---|---|
| `<MODEL_CALL_COUNTER_METRIC>` | 模型调用量/成功失败量 | `counter,delta,rate` | `scene,success,agent_id,root_agent_id,model_id,model_name,category,end_point,error_code` |
| `<MODEL_CALL_P99_METRIC>` | 模型调用 P99 耗时 | 单值 | 与 counter 相同 |
| `<MODEL_TOKEN_USAGE_METRIC>` | Token 用量分布/总量 | Histogram | `token_type,model_scene,model_id,model_name,agent_id,category,success` |

常见调用 `scene` 包括 `model_chat`、`multi_model_chat`、`agent_model_call`、
`agent_model_limit`。`token_type` 当前包括 `prompt_tokens`、`completion_tokens`、
`total_tokens`、`reasoning_tokens`、`cached_tokens`、`cache_ratio`。

```bash
# 单个 Agent 的模型调用成功/失败量
bytedcli labelgpt metrics query \
  'sum:5m-sum:<MODEL_CALL_COUNTER_METRIC>{success=literal_or(*)}{scene=literal_or(model_chat),agent_id=literal_or(<AGENT_ID>)}[delta]' \
  --start-time <START_SECONDS> --end-time <END_SECONDS> --format raw

# 按模型拆分 P99
bytedcli labelgpt metrics query \
  'avg:5m-avg-zero:<MODEL_CALL_P99_METRIC>{model_name=literal_or(*)}{scene=literal_or(model_chat),agent_id=literal_or(<AGENT_ID>),success=literal_or(true)}' \
  --start-time <START_SECONDS> --end-time <END_SECONDS> --format raw

# 按 token 类型统计总量；Histogram 的 sum downsample 不能带 fill policy
bytedcli labelgpt metrics query \
  'sum:5m-sum:<MODEL_TOKEN_USAGE_METRIC>{token_type=literal_or(*)}{agent_id=literal_or(<AGENT_ID>),success=literal_or(true)}[hist_sum()]' \
  --start-time <START_SECONDS> --end-time <END_SECONDS> --format raw
```

不要把 `cache_ratio` 与 token 数量直接相加；需要总 Token 成本时只选择对应的 token count
类型。按多个模型汇总 P99 时不要简单求和，优先保留 `model_name` 分组或限定单个模型。

## `<DATA_PSM>`

核心业务指标：

| 指标 | 含义 | 字段/类型 | 核心 tag |
|---|---|---|---|
| `<DATA_PROCESS_COUNTER_METRIC>` | 导入、预标、导出等数据处理计数 | `counter,delta,rate` | `scene,result,stage,process_step,source_type,export_type,flow,engine,error_code` |
| `<DATA_PROCESS_P99_METRIC>` | 数据处理阶段 P99 耗时 | 单值 | 与 counter 相同 |

常见 `scene` 包括 `process.total.success`、`process.total.failed`、
`process.stage.total`、`process.stage.items`、`process.import.parser.total`、
`process.export.group.total`、`process.export.sender.total`。常见 `stage` 为 `import`、
`prelabel`、`export_group`、`export`。

```bash
# 各数据处理场景计数
bytedcli labelgpt metrics query \
  'sum:1h-sum:<DATA_PROCESS_COUNTER_METRIC>{scene=literal_or(*)}{}[delta]' \
  --start-time <START_SECONDS> --end-time <END_SECONDS> --format raw

# 按阶段查看 P99
bytedcli labelgpt metrics query \
  'avg:1h-avg-zero:<DATA_PROCESS_P99_METRIC>{stage=literal_or(*)}{}' \
  --start-time <START_SECONDS> --end-time <END_SECONDS> --format raw
```

只分析某类导入/导出时，增加 `source_type`、`export_type`、`flow`、`process_step` 或
`result` 过滤，避免把不同阶段混成一个结论。

## 结果解释与排障

- `series=[]`：查询成功但当前 region、时间窗和 filters 没有匹配时序；不等于指标不存在。
- 指标是否存在以 `search` 为准，字段类型以 `field-list` 为准，tag 名和值分别以
  `tagk-list/tagv-list` 为准。
- HTTP 430 / “查询读取数据量过大”：缩短时间窗，并优先增加 `agent_id`、`process_id`、
  `node_id`、`model_id` 或 `scene` 过滤。
- `delta_counter` 总量默认用 `[delta]` + `sum` downsample；QPS 用 `[rate]` + `avg`
  downsample。业务多字段查询默认不加 fill policy，除非已验证该指标支持。
- P99 指标不要跨 Agent/模型/阶段简单相加。单值 `*.pct99` 用 `avg` 做时间降采样，并尽量
  保留业务分组；多字段 timer 才使用服务端支持的 weighted 表达式。
- 成功率从同一查询返回的 `success=true/false` 总量计算：
  `true / (true + false)`。DSL 不支持任意算术时，在调用侧计算。
- 任何对比必须使用相同 tenant、region、时间窗和 downsample；查询结果中的 `dps` 时间戳为
  Unix 秒。
