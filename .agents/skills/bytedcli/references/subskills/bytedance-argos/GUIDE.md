---
name: bytedance-argos
description: "Argos observability fallback and Agent orchestration via bytedcli. Prefer bytedance-log for log search, LogID, pod/instance/Footprint, and log analysis; prefer bytedance-apm for metrics, QPS/SLA, CPU/MEM, dependencies, topology, Redis, and APM analysis. Use this skill when those dedicated skills cannot close the investigation, when the task needs Argos/SRE Agent multi-tool reasoning, alarm RCA or alarm-rule diagnosis and optimization, dashboard patrol or server-provided dashboard operations, when full/AI trace retrieval is specifically needed, when an AI agent session trajectory must be recovered from a PSM and session ID, when an already attempted Measurement/Metrics query needs metadata correction or a Metrics FE/Bosun/Argos query URL needs parsing, or when the user explicitly asks for Argos. Direct `argos tool` log/metrics calls are documented here but do not take priority over bytedance-log/bytedance-apm."
---

# bytedcli Argos Agent

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

- 已先使用 `bytedance-log` / `bytedance-apm`，但确定性查询或分析不足以闭环，需要继续调用 Argos tool 或 Agent
- 用户要求获取完整 trace span 或 AI/LLM trace → `bytedtrace.get_trace` / `bytedtrace.get_ai_trace`
- 用户要按 PSM 检索 span 列表（server/client/gen_ai 等）→ `bytedtrace.get_span_list` / `bytedtrace.get_ai_span_list`
- 用户要通过 MCP tool 查询 AI trace session 索引或 turn 详情 → `bytedtrace.query_session_index` / `bytedtrace.query_session_detail`
- 已知 PSM 与 AI agent session ID，需要按 session 还原全部 turn 轨迹或定位单个 user message → `argos ai-agent-session get`（CLI 编排）或 `bytedtrace.query_session_index` + `bytedtrace.query_session_detail`（单次 tool 调用）
- 用户要求对 Trace 做错误、耗时或 LogID 提取等深度诊断 → `trace.inspect`
- 已有 Measurement / Metrics 查询需要纠偏、检查精确元数据，或需要解析 Metrics FE、Bosun、Argos 查询 URL → `timeseries.inspect`
- 用户明确提到 `bytedcli argos`、`argos tool` 或具体 Argos MCP tool 名
- 用户明确要求使用 "argos agent" / "sre agent" / "agent 排障"
- 报警 RCA、报警治理、oncall 统计，以及已有报警规则的诊断和优化（降噪、误报、漏报、报警风暴、阈值或发送策略合理性）
- Dashboard / 大盘巡检、服务拓扑、服务 RCA 等 bytedance-log / bytedance-apm 不直接覆盖的服务端可观测诊断
- 通过服务端提供的 `dashboard-operation` 创建或维护 Argos Dashboard、Folder，或从 Grafana、Metrics-FE、Metrics SDK 导入

## When NOT to use

- 普通日志搜索、PSM/LogID、Pod/实例/泳道日志、Footprint/TCE Sync、日志聚类、长时间窗滚动、接口性能分析或 LogID 调用树 → 优先使用 `bytedance-log`
- 普通指标查询、QPS/SLA、CPU/MEM、上下游依赖、服务拓扑、Redis、中间件、Query DSL 或多 region 指标 → 优先使用 `bytedance-apm`
- EU/US TTP 日志或指标查询 → 使用支持对应控制面的 `bytedance-log` / `bytedance-apm`
- Argos Footprint 日志下载（viewlog argos/argos_keyword 类型）→ 使用 `bytedance-log`

## 前置条件

- 已完成 ByteCloud 登录（`bytedcli login`），或按下方“服务账号 JWT”配置受管环境凭据。

## 支持站点与 Region 映射

`--site` 参数决定连接哪个控制面（Partition），必须与目标服务所在 region 的控制面对应，否则查不到数据。

| `--site`     | 控制面  | 说明                  | 典型 Region                                            |
| ------------ | ------- | --------------------- | ------------------------------------------------------ |
| `cn`（默认） | cn      | 国内站                | China-North, China-East, ChinaSinf-North, China-PPE    |
| `boe`        | boe     | 测试环境              | China-BOE, US-BOE, ChinaSinf-BOE                       |
| `i18n`       | i18n    | 海外站通用别名        | Singapore-Central, US-East, Europe-Central, US-West    |
| `i18n-tt`    | i18n    | 海外站（TikTok 等）   | Singapore-Central, US-East, Europe-Central, US-West    |
| `i18n-bd`    | i18n-bd | 海外 BD 站（Lark 等） | Singapore-SaaS, US-EE, Singapore-Common, Europe-WestBD |
| `us-ttp`     | us-ttp  | 美国 TTP              | US-TTP, US-TTP2                                        |
| `eu-ttp`     | eu-ttp  | 欧洲 TTP 合规         | EU-Compliance, EU-TTP, EU-TTP2, US-EastRed             |

`argos tool` 与 `argos ai-agent-session get` 支持表中的全部 site；`argos run`、`argos session list/get` 暂不接受 `i18n` 别名，请使用同路由的 `i18n-tt`。`eu-ttp-limited` 与 `eu-ttp-full` 会在 Argos 路由中归一化为 `eu-ttp`。不要把 EU-TTP、US-TTP 或 TX-TTP region 静默改用 `--site i18n-tt`；它们必须连接各自的 TTP 控制面。

`us-ttp-bdee` 与 `us-ttp-usts` 不是独立的 Argos 控制面。bytedcli 为兼容全局 site 配置会把它们归一化到 `us-ttp`，但这不表示它们分别对应 `US-TTP` / `US-TTP2`，也不构成对 USTS 网络入口可用性的承诺。调用 Argos 时优先显式使用已验证的 `--site us-ttp`：带 region 参数的 `argos tool` 再选择 `US-TTP` 或 `US-TTP2`；`argos run` 把目标 region 写进 `--prompt`；session 查询不额外传 region。

完整 Region 列表见 [references/regions.md](./references/regions.md)。

## 服务账号 JWT

受管环境推荐注入站点级变量，避免不同 credential partition 的 JWT 串用：

| Argos `--site`                              | 服务账号 JWT 环境变量                  | credential site |
| ------------------------------------------- | -------------------------------------- | --------------- |
| `cn` / `boe`                                | `BYTEDCLI_SERVICE_ACCOUNT_JWT_CN`      | `cn`            |
| `i18n-tt`                                   | `BYTEDCLI_SERVICE_ACCOUNT_JWT_I18N_TT` | `i18n-tt`       |
| `i18n` / `i18n-bd`                          | `BYTEDCLI_SERVICE_ACCOUNT_JWT_I18N_BD` | `i18n-bd`       |
| `us-ttp` / `us-ttp-bdee` / `us-ttp-usts`    | `BYTEDCLI_SERVICE_ACCOUNT_JWT_US_TTP`  | `us-ttp`        |
| `eu-ttp` / `eu-ttp-limited` / `eu-ttp-full` | `BYTEDCLI_SERVICE_ACCOUNT_JWT_EU_TTP`  | `eu-ttp`        |

也可使用通用变量 `BYTEDCLI_SERVICE_ACCOUNT_JWT`。credential site 只决定读取哪个 JWT 环境变量，不决定 Argos 入口是否受支持，也不决定目标数据 Region。三个 US site 都共享 `BYTEDCLI_SERVICE_ACCOUNT_JWT_US_TTP`；这条凭据归一化规则不代表 `us-ttp-usts` 已通过 Argos 可用性验证。不要创建 `BYTEDCLI_SERVICE_ACCOUNT_JWT_US_TTP_BDEE` 或 `BYTEDCLI_SERVICE_ACCOUNT_JWT_US_TTP_USTS`。

- `argos run` 使用服务账号时必须显式传 `--project`。
- `argos tool` 与 `argos ai-agent-session get` 没有 `--project` 参数，使用服务账号时必须设置 `BYTEDCLI_ARGOS_PROJECT`。
- 设置 `ARGOS_SERVER_URL` 或 `BYTEDCLI_ARGOS_AGENT_HOST` 自定义 Agent Center 地址时，bytedcli 不会向该地址发送受管环境注入的服务账号 JWT；请使用个人或显式测试凭据。

## 命令

### `bytedcli argos tool list`

列出所有可用的 Argos MCP tool。

```bash
# 查看全量 tool
bytedcli argos tool list

# 按 namespace 过滤
bytedcli argos tool list --namespace bytedtrace
bytedcli argos tool list --namespace log
bytedcli argos tool list --namespace metrics

# 按关键词搜索
bytedcli argos tool list --search trace

# JSON 输出（含完整 inputSchema）
bytedcli --json argos tool list
```

### `bytedcli argos tool <tool_name>`

直接调用某个 MCP tool。每个 tool 是一个独立子命令，option 从 inputSchema 自动生成。

**两种调用方式：**

1. **结构化参数**（推荐）：`--key value` 风格，从 schema 自动生成

```bash
bytedcli argos tool bytedtrace.get_trace \
  --query-id 5a25e2f7-3063-326c-b0da-6584cc4b7c6e

bytedcli argos tool bytedtrace.get_ai_trace \
  --query-id 5a25e2f7-3063-326c-b0da-6584cc4b7c6e

bytedcli argos tool trace.inspect \
  --query-id 5a25e2f7-3063-326c-b0da-6584cc4b7c6e \
  --region China-North

bytedcli argos tool log.search.keywords_stream \
  --psm-list example.service \
  --region China-North \
  --keywords timeout,error \
  --start 2026-08-06T10:00:00+08:00 \
  --end 2026-08-06T11:00:00+08:00 \
  --limit 50

bytedcli argos tool metrics.data \
  --metric sample.metric \
  --region China-North \
  --start-time 2026-08-06T10:00:00+08:00 \
  --end-time 2026-08-06T11:00:00+08:00 \
  --top-bottom top-20-max \
  --aggregator avg
```

2. **原始 JSON 调用**：通过 `--input` 传入完整 JSON

```bash
bytedcli argos tool bytedtrace.get_trace \
  --input '{"query_id":"5a25e2f7-3063-326c-b0da-6584cc4b7c6e"}'

bytedcli argos tool trace.inspect \
  --input '{"query_id":"5a25e2f7-3063-326c-b0da-6584cc4b7c6e","source":"apm","region":"China-North"}'
```

**查看参数和 Schema：**

```bash
# 查看某个 tool 的所有可选参数
bytedcli argos tool bytedtrace.get_trace -h

# 仅输出 JSON Schema（方便脚本消费）
bytedcli argos tool bytedtrace.get_trace --schema
```

**通用选项：**

| 参数                    | 说明                                                                           |
| ----------------------- | ------------------------------------------------------------------------------ |
| `--duration <duration>` | 结构化参数模式下补齐缺失的时间边界；日志/metrics 查询未传时间时默认最近 1 小时 |
| `--input <json>`        | 原始 JSON 单次调用；绕过参数优化和自动翻页                                     |
| `--schema`              | 打印该 tool 的 JSON Schema                                                     |
| `-h, --help`            | 查看可用参数列表（JSON Schema 使用 `--schema` 单独输出）                       |

`log.search.keywords_stream` 额外支持：

| 参数                | 说明                             |
| ------------------- | -------------------------------- |
| `--no-auto-page`    | 只查询当前 cursor 页，不自动翻页 |
| `--max-pages <n>`   | 自动翻页最大页数，默认 100       |
| `--max-results <n>` | 自动翻页累计日志上限，默认 10000 |

---

### 当前已注册的 Tool 子命令

| Namespace  | Tool                              | 说明                                                  |
| ---------- | --------------------------------- | ----------------------------------------------------- |
| log        | `log.search.keywords_stream`      | 推荐的关键词检索，支持 cursor、KV 过滤和排除词        |
| log        | `log.logid_prune`                 | 按 LogID 追踪请求链路                                 |
| log        | `log.error_log`                   | 错误日志聚合                                          |
| log        | `log.search.keywords`             | 简单关键词检索                                        |
| log        | `log.local_file`                  | 查询 Pod 本地日志文件                                 |
| log        | `log.key_word_v2`                 | 已废弃的兼容入口，优先用 `log.search.keywords_stream` |
| metrics    | `metrics.name_suggestion`         | 按前缀搜索指标名                                      |
| metrics    | `metrics.tag_key`                 | 查询指标可用标签键                                    |
| metrics    | `metrics.tag_value`               | 查询指标标签值                                        |
| metrics    | `metrics.data`                    | 查询时序指标数据                                      |
| timeseries | `timeseries.inspect`              | 检查已知时序查询的元数据或解析查询 URL                |
| bytedtrace | `bytedtrace.get_trace`            | 通用全量 trace 查询（所有 span，不限 AI）             |
| bytedtrace | `bytedtrace.get_ai_trace`         | GenAI trace（仅 AI 相关 span）                        |
| bytedtrace | `bytedtrace.get_span_list`        | 按 PSM 检索 span 列表（server/client/gen_ai 等）      |
| bytedtrace | `bytedtrace.get_ai_span_list`     | 按 PSM 检索 AI span 列表（GenAI span）                |
| bytedtrace | `bytedtrace.query_session_index`  | 查询 AI trace session 的 turn 索引列表                |
| bytedtrace | `bytedtrace.query_session_detail` | 查询 AI trace session 某个 turn 的详情                |
| trace      | `trace.inspect`                   | Trace 深度诊断（查询 + 后处理，输出结构化 artifact）  |

> 静态子命令 schema 会随 bytedcli 发布；运行 `bytedcli argos tool list` 可查询服务端当前开放的最新全量列表。

---

### 日志 Tool

本节是 `bytedance-log` 无法闭环或用户明确要求 Argos 时的直接 Tool 路径，不替代日志 skill 的默认入口。

新查询优先使用 `log.search.keywords_stream`。它支持 cursor 分页、`kv_filters`、排除关键词和精确 term 匹配；`log.search.keywords` 不支持同等的结构化过滤能力，`log.key_word_v2` 已废弃。

```bash
# PSM + 关键词 + RFC3339 时间窗
bytedcli argos tool log.search.keywords_stream \
  --psm-list example.service \
  --region China-North \
  --keywords timeout,error \
  --duration 1h \
  --limit 100 \
  --max-results 5000

# 结构化 KV 过滤；数组/对象参数传 JSON
bytedcli argos tool log.search.keywords_stream \
  --psm-list example.service \
  --region China-North \
  --keywords sample-request-id \
  --kv-filters '[{"key":"_podname","values":["sample-pod"]}]'

# 使用上一页响应中的 opaque cursor 继续查询
bytedcli argos tool log.search.keywords_stream \
  --psm-list example.service \
  --region China-North \
  --cursor 'sample-cursor' \
  --no-auto-page

# LogID 追踪
bytedcli argos tool log.logid_prune \
  --log-id sample-log-id \
  --region China-North

# 错误日志聚合；start/end 为 Unix 秒
bytedcli argos tool log.error_log \
  --psm example.service \
  --region China-North \
  --duration 1h

# Pod 本地日志：未传 seek-position 时自动生成最近 15 分钟的 time_range
bytedcli argos tool log.local_file \
  --psms example.service \
  --regions China-North \
  --pod-names sample-pod \
  --paths /opt/tiger/toutiao/log/app.log \
  --duration 15m
```

注意：

- `--xxx` 结构化参数模式会先经过对应 tool handler：补默认 region、默认值和时间窗，再调用后端。
- 日志与 metrics 的 `--start` / `--end`、`--start-time` / `--end-time` 接受 RFC3339、Unix 秒/毫秒、`now`、`1h ago`；handler 会转换成 tool schema 要求的格式。
- `log.search.keywords_stream` 默认持续请求后端 cursor，合并每页 `logs`，直到 `finished=true`、达到 `--max-pages` / `--max-results`，或检测到缺失/重复 cursor。
- 自动翻页结果包含 `pagination.pages`、`pagination.complete`、`pagination.truncated`、`pagination.stop_reason` 等结构化证据。
- `log.error_log` 的 handler 会将时间转换为后端需要的 Unix 秒，并默认 `aggregator=location`。
- `log.local_file` 未传 `--seek-position` 时，会按 `--duration` 生成 `seek_position.time_range`。
- `level` 是 `_level` KV filter 的简写，不能同时传 `--level` 和 key 为 `_level` 的 `--kv-filters`。
- `--cursor` 是后端返回的不透明值，不要自行解析或修改。
- `--input` 是原始逃生口：不补时间/default、不自动翻页，完整透传一次。
- `eu-ttp` 的 Agent Center 对 server 模式 `log.search.keywords_stream` 可能返回 403；保持默认 `auto` 执行模式，让 SDK 优先使用 WebSocket。

### Metrics Tool

本节是 `bytedance-apm` 无法闭环或用户明确要求 Argos 时的直接 Tool 路径，不替代 APM skill 的默认入口。

不确定指标名和标签时，按 `name_suggestion` → `tag_key` → `tag_value` → `data` 的顺序探索。

```bash
# 1. 搜索指标名
bytedcli argos tool metrics.name_suggestion \
  --region China-North \
  --tenant default \
  --metrics-name-prefix sample. \
  --limit 10

# 2. 查询标签键
bytedcli argos tool metrics.tag_key \
  --region China-North \
  --metrics-name sample.metric

# 3. 查询某个标签的可用值；wire 字段 tagK 对应 CLI 参数 --tag-k
bytedcli argos tool metrics.tag_value \
  --region China-North \
  --metrics-name sample.metric \
  --tag-k _psm

# 4. 查询时序数据
bytedcli argos tool metrics.data \
  --metric sample.metric \
  --region China-North \
  --duration 1h \
  --tags '[{"key":"_psm","value":"example.service","function":"literal_or","is_filter":true}]'
```

`metrics.data` 的结构化参数模式默认补 `aggregator=avg`、`top_bottom=top-20-max`、`tenant=default`；`metrics.name_suggestion` 默认 `namespace=default`、`tenant=default`、`limit=10`；`metrics.tag_key/tag_value` 默认 `namespace=default`、`tenant=default`。显式传参始终优先。

Timer/counter 多字段指标通常还需传：

```bash
bytedcli argos tool metrics.data \
  --metric sample.timer.metric \
  --region China-North \
  --start-time 2026-08-06T10:00:00+08:00 \
  --end-time 2026-08-06T11:00:00+08:00 \
  --top-bottom top-20-max \
  --aggregator avg \
  --is-multi-field true \
  --multi-field-expr 'weighted_avg(value=pct99,weight=counter)'
```

### Timeseries Inspect Tool

`timeseries.inspect` 用于对**已知的** Measurement / Metrics 查询做纠偏、检查元数据，或解析已有查询 URL。它不是开放式语义指标发现入口；指标名完全未知时，优先使用 `metrics.name_suggestion`。

```bash
# 按已知前缀建议可能的 Metrics 名称
bytedcli argos tool timeseries.inspect \
  --command suggest_names \
  --source metrics \
  --name-prefix sample. \
  --region China-North

# 查看已知 Measurement 的结构
bytedcli argos tool timeseries.inspect \
  --command describe \
  --source measurement \
  --name sample.measurement \
  --observable-object service:example.service \
  --region China-North

# CN 示例：解析 Metrics FE 指标详情 URL（必须保留完整 hash）
bytedcli argos tool timeseries.inspect \
  --command parse \
  --url 'https://metrics-fe.byted.org/web/plot/metrics#now-1h,now,,,,,,,China-North,false,,;sum:store:top-20-max:sample.metric{}{_psm=literal_or(example.service)};0'

# CN 示例：解析 Metrics FE Bosun URL（必须保留 bosun 查询参数）
bytedcli argos tool timeseries.inspect \
  --command parse \
  --url 'https://metrics-fe.byted.org/web/bosun/cn?bosun=sum%28q%28%22sum%3Asample.metric%7B_psm%3Dexample.service%7D%22%2C%223600s%22%2C%220s%22%29%29&region=China-North'

# CN 示例：解析包含 queries 参数的 Argos Explore / Dashboard / Overview URL
bytedcli argos tool timeseries.inspect \
  --command parse \
  --url 'https://cloud.bytedance.net/argos/dashboard/demo?queries=%5B%7B%22queryType%22%3A%22metrics%22%2C%22metrics%22%3A%7B%22metric%22%3A%22sample.metric%22%2C%22tenant%22%3A%22default%22%2C%22aggr%22%3A%22avg%22%2C%22region%22%3A%22China-North%22%2C%22tags%22%3A%5B%5D%7D%7D%5D&from=now-1h&to=now'
```

`command` 支持 `suggest_names`、`describe`、`values`、`parse`；前三种命令的 `source` 为 `measurement` 或 `metrics`。实际所需字段以 `bytedcli argos tool timeseries.inspect --schema` 为准。

以上 URL 均为 CN 控制面示例。`parse` 需要页面携带完整查询状态：Metrics FE 指标详情 URL 要保留 `#...`，Bosun URL 要保留 `bosun=...`，Argos Explore / Dashboard / Overview URL 要保留 `queries=...`。普通大盘首页和 Grafana URL 不在支持范围内。解析只返回一个或多个 `measurement.data` / `metrics.data` / `bosun.data` 的 `parsed_queries`，不会执行查询，也不会校验指标是否存在。

---

### BytedTrace AI 应用观测 Tool

详见 [references/ai-observability-tools.md](references/ai-observability-tools.md)。

---

### `bytedcli argos run`

向 Argos AI Agent 发送自然语言查询，agent 自主推理、调用工具、返回结论。

```bash
# 分析报警根因
bytedcli argos run --prompt "分析这个报警的根因: https://argos.byted.org/alarm/detail?id=example-alarm-id"

# 优化已有报警规则；site 必须对应规则所属控制面
bytedcli --site cn argos run --project argos \
  --prompt "优化报警规则 1234567890123" \
  --timeout-ms 600000

# 服务可用性/延迟分析
bytedcli argos run --prompt "查看 psm=example.service.api 最近 30 分钟的可用性和延迟"

# 故障诊断
bytedcli argos run --prompt "example.service.api 的错误率突增，帮我定位根因"

# TraceID 追踪
bytedcli argos run --prompt "追踪 traceID abc123def456"

# 查服务 QPS、延时、可用性
bytedcli argos run --prompt "查看 example.service.api 在 China-North 最近 1 小时的 QPS、P99 延时和可用性"

# 巡检大盘
bytedcli argos run --prompt "巡检 example-team 的核心服务大盘，看有没有异常指标"

# 海外站查询（指定 site）
bytedcli --site i18n-tt argos run --prompt "查看 example.i18n.service 在 Singapore-Central 的错误日志"

# 继续已有 session
bytedcli argos run --prompt "继续分析上面的问题" --session <session-id>

# JSON 模式（适合脚本/AI agent 消费）
bytedcli --json argos run --prompt "分析 example.service.api 最近的报警"

# JSONL 事件流（stdout 每行一个事件）
bytedcli argos run --prompt "分析 example.service.api 最近的报警" --format stream-json

# 同步 HTTP 模式：明确不使用 SSE，也不提供实时工具进度
bytedcli argos run --prompt "分析 example.service.api 最近的报警" --execution-profile server

# 增加经过脱敏和截断的工具参数、结果摘要
bytedcli argos run --prompt "排查报警" --verbose

# 复杂分析加大超时
bytedcli argos run --prompt "全面巡检 example.service.api" --timeout-ms 600000

# 限制本地 fs.* 工具工作区（默认是当前目录）
bytedcli argos run --prompt "阅读当前项目代码并总结入口" --fs-base-path ./safe-workspace

# 使用服务端提供的 dashboard-operation；写入前要求预览
bytedcli argos run \
  --prompt "使用 dashboard-operation，在 sample-team folder 创建 sample-service Metrics dashboard；写入前先预览"
```

**参数说明：**

| 参数                            | 必填 | 说明                                                 |
| ------------------------------- | ---- | ---------------------------------------------------- |
| `--prompt <text>`               | 是   | 发送给 agent 的自然语言查询（中文查询效果更好）      |
| `--project <name>`              | 否   | 项目名称；用户 JWT 可省略，服务账号 JWT 必须显式传入 |
| `--session <id>`                | 否   | 继续已有 session                                     |
| `--fs-base-path <path>`         | 否   | 本地 fs.\* 工具工作区，默认当前目录                  |
| `--model <name>`                | 否   | LLM 模型覆盖                                         |
| `--max-turns <n>`               | 否   | 最大 agent 工具调用轮次                              |
| `--timeout-ms <ms>`             | 否   | 超时时间，默认 300000（5 分钟）；复杂查询建议 600000 |
| `--format <fmt>`                | 否   | `text`（默认）或 `stream-json` JSONL 事件流          |
| `--execution-profile <profile>` | 否   | `interactive`（WS）、`server`（同步 HTTP）或 `auto`  |
| `--verbose`                     | 否   | 追加经过脱敏和截断的工具参数、结果摘要               |

**输出行为：**

- **文本模式**（默认）：stdout 只输出最终回答；stderr 展示 session、连接、用户可见的简短 `thought` 说明或 CLI 生成的一行工具动作说明、工具名与有界参数摘要、告警和人工动作。成功工具完成行省略，失败提示保留；模型内部 thinking、工具结果以及内部 `fs.*` / `finish` 调用不展示。
- **JSON 模式**（全局 `--json`）：保持向后兼容，只在 stdout 输出一个最终对象。
- **JSONL 模式**（`--format stream-json`）：stdout 每行一个 `{type,timestamp,data}` 事件；每次运行只有一个 `result` / `needs_input` / `error` 终态。工具事件通过 `call_id` 关联，`tool_finished` 带 `duration_ms` 和 `success`。
- 全局 `--json` 与 `--format stream-json` 不能同时使用。工具事件使用 `name` 并通过 `call_id` 关联；其他过程事件分别使用 `session_id`、`status`、`stage` 或 `code` 等字段。机器可读结果里的 `tool_calls[].duration_ms` 稳定输出为数字或 `null`；默认文本不显示该字段。`--verbose` 只增加经截断、脱敏的有界摘要。
- `--execution-profile server` 直接调用同步 HTTP 接口，固定 `stream=false, async=false`，**不走 SSE**；仅说明 `live_progress_available=false` 并输出最终终态，不伪造实时工具事件。`auto` 仅在 WS 不可用时降级到同一同步 HTTP 路径。
- 终态优先级和退出码固定：`needs_input`=2、失败/异常=1、成功=0。

全局 JSON 成功示例：

```json
{
  "status": "ok",
  "data": {
    "session_id": "uuid",
    "content": "agent 的完整回复文本",
    "success": true,
    "token_usage": { "input": 1234, "output": 567 },
    "files_modified": []
  }
}
```

### `bytedcli argos session list`

列出历史 agent session。

```bash
bytedcli argos session list
bytedcli argos session list --project my-team-project
bytedcli argos session list --page 2 --page-size 10
bytedcli --json argos session list
```

### `bytedcli argos session get`

获取某个 session 的详细信息。

```bash
bytedcli argos session get --id <session-id>
bytedcli --json argos session get --id <session-id>
```

### `bytedcli argos ai-agent-session get`

按 PSM 与 AI agent session ID，通过 Argos MCP tool 查询 BytedTrace 轨迹。省略 `--user-message-id` 时，bytedcli 会先读取 session index，再以固定 5 路并发获取 turn 详情并按 index 顺序输出；单个 turn 失败不会丢弃其它成功结果。默认最多获取 50 个 turn，可通过 `--max-turns` 调整（范围 1–200）。指定 `--user-message-id` 时只获取对应 turn。

命令复用全局 `--site` 选择 Argos 控制面；未指定时默认 `cn`。已验证支持的 canonical site 为 `cn`、`boe`、`i18n`、`i18n-tt`、`i18n-bd`、`us-ttp` 与 `eu-ttp`。命令也接受 `us-ttp-bdee`、`us-ttp-usts` 作为兼容输入并归一化到 `us-ttp`，但 USTS 入口尚未完成可用性验证，调用 Argos 时优先显式使用 `--site us-ttp`。不支持的控制面会在 MCP 调用前明确报错。

```bash
bytedcli argos ai-agent-session get \
  --psm example.service \
  --session-id sample-session-id \
  --access-mode personal \
  --max-turns 50 \
  --timeout-ms 30000

bytedcli argos ai-agent-session get \
  --psm example.service \
  --session-id sample-session-id \
  --user-message-id sample-message-id \
  --access-mode viewer

bytedcli --json argos ai-agent-session get \
  --psm example.service \
  --session-id sample-session-id
```

`--access-mode` 支持 `personal`（默认，按当前用户的个人 session 权限访问）和 `viewer`（使用普通 viewer 权限，内容可能脱敏），并原样传给 index/detail MCP tool。`query_scope` 明确区分 `session` 与 `single_turn`；`session_index_queried` 表示是否查询过 index。完整 session 查询中，`index_turns_truncated` 直接反映后端 index 是否截断，`turns_limited_by_max` 表示 CLI 是否因 `--max-turns` 进一步截断。`failed_turn_message_ids` 可用于逐 turn 重试，`returned_turn_count` 是本次成功返回的 turn 数量；即使所有 detail 请求都失败，命令也会返回失败 ID 清单。每个 index/detail MCP 调用默认超时 30 秒，可通过 `--timeout-ms` 调整（1000–120000 毫秒）。文本模式只展示摘要与 turn 表格；使用全局 `--json` 获取完整轨迹内容。

## Agent Guidance

### 路由选择：`argos tool` vs `argos run`

| 场景                                        | 推荐                                                   |
| ------------------------------------------- | ------------------------------------------------------ |
| 关键词日志检索 / KV 过滤 / cursor 分页      | `argos tool log.search.keywords_stream`                |
| LogID 追踪                                  | `argos tool log.logid_prune`                           |
| 指标元数据探索                              | `argos tool metrics.name_suggestion/tag_key/tag_value` |
| 单 region 时序指标查询                      | `argos tool metrics.data`                              |
| 已知时序查询纠偏、元数据检查或 URL 解析     | `argos tool timeseries.inspect`                        |
| 确定性 trace 查询（知道 traceID/logID）     | `argos tool bytedtrace.get_trace`                      |
| AI Agent/LLM 调用链分析                     | `argos tool bytedtrace.get_ai_trace`                   |
| 按 PSM 检索 span 列表（server/client 等）   | `argos tool bytedtrace.get_span_list`                  |
| 按 PSM 检索 AI span 列表（GenAI span）      | `argos tool bytedtrace.get_ai_span_list`               |
| 查询 AI session turn 索引                   | `argos tool bytedtrace.query_session_index`            |
| 查询 AI session turn 详情                   | `argos tool bytedtrace.query_session_detail`           |
| Trace 深度诊断（需要错误/耗时/logID 提取）  | `argos tool trace.inspect`                             |
| 按 PSM + session ID 获取 AI agent turn 轨迹 | `argos ai-agent-session get`                           |
| 需要 AI 推理/编排多个工具/不确定查什么      | `argos run`                                            |
| 报警 RCA / oncall / 大盘巡检                | `argos run`                                            |
| 已有报警规则诊断或优化                      | `argos run --project argos`                            |
| Dashboard/Folder 创建、修改或导入           | `argos run`                                            |

优先使用 `argos tool`：结果确定性强、速度快、无 token 消耗。只有当单个 tool 调用不够（需要多步推理）时才升级到 `argos run`。

### 报警规则优化

当用户要求诊断或优化已有报警规则时，读取 [报警规则优化](references/alarm-rule-optimization.md)，按其中的输入识别、安全边界和控制面规则执行。

### tool 调用注意事项

- `--site` 必须与目标 region 所属控制面对应，否则查不到数据
- 每个 tool 的参数可通过 `-h` 或 `--schema` 查看
- 不确定用哪个 tool 时，先 `bytedcli argos tool list --search <keyword>` 搜索
- 日志搜索优先 `log.search.keywords_stream`；长 ID、KV 过滤和完整分页不要默认用 `log.search.keywords`
- `log.search.keywords_stream` 默认自动翻页；需要自行管理 cursor 时显式传 `--no-auto-page`
- metrics 不确定字段时先走 `name_suggestion` → `tag_key` → `tag_value`，再调用 `data`
- `timeseries.inspect` 只用于已知 Measurement / Metrics 查询的纠偏、元数据检查或 URL 解析，不作为开放式语义指标发现入口
- object/array 参数必须传合法 JSON；普通数组也支持逗号分隔
- trace 查询推荐 `bytedtrace.get_trace`（全量 span），AI trace 用 `bytedtrace.get_ai_trace`（仅 GenAI span）
- 按 PSM 检索 span 列表用 `bytedtrace.get_span_list`（通用）或 `bytedtrace.get_ai_span_list`（仅 AI span）
- AI session 查询：完整编排用 `argos ai-agent-session get`，单次 tool 调用用 `bytedtrace.query_session_index` / `bytedtrace.query_session_detail`

### argos run 注意事项

- 查询文本优先使用中文（CN 环境优化）
- 多次查询必须串行执行（禁止并发）
- agent session 有状态：如果需要多轮交互，用 `--session` 继续上一个 session
- 超时默认 5 分钟；复杂分析任务建议显式设置 `--timeout-ms 600000`
- 使用用户 JWT 且不传 `--project` 时使用用户个人 project，agent 会使用该 project 配置的工具集和知识库；服务账号 JWT 无法可靠派生个人 project，`argos run` 必须传 `--project`
- `--site` 必须与目标 region 所属控制面对应，否则查不到数据
- `bytedcli argos run` 会允许 Agent 通过 SDK 处理服务端发起的 `fs.*` 本地工具调用；默认工作区是当前目录。不要在包含敏感文件的目录运行，或使用 `--fs-base-path <path>` 限制到安全目录
- Dashboard 创建、修改、复制、迁移或导入通过服务端提供的 `dashboard-operation` 执行，并遵循 [Dashboard operation through an Argos agent session](./references/dashboard-operation.md)。能力是否可用取决于当前控制面、project 和服务端配置
- Dashboard MCP tools 仅供 Agent Session 内的 skill 调用，不注册成直接 `argos tool` 子命令；`argos tool list` 也不代表会话内的 agent-only tool 集合
- HTTP `server` 模式是同步、非流式执行，不会接受服务端反向本地工具调用；需要本地 `fs.*` 或实时工具进度时使用默认 `interactive` 模式
- 权限型 `needs_input` 只报告待授权工具和 pending 状态，需转到支持工具审批的客户端继续；普通问答型 `needs_input` 才会给出 `--session` 续跑命令

## 重试策略

- 失败后不自动重试——展示失败原因，询问用户是否重试
- 用户确认后最多重试 3 次
- 参数校验错误：提示用户修正参数，不进入重试

## 与 bytedance-log / bytedance-apm 的关系

`bytedance-log` 和 `bytedance-apm` 也会面向 Agent 做查询与分析，不只是"原始数据查询"。因此路由优先级应是：

| 场景                                                        | 推荐 skill                        |
| ----------------------------------------------------------- | --------------------------------- |
| 日志搜索、PSM/LogID、Pod/实例、Footprint、日志分析          | `bytedance-log`                   |
| 指标、QPS/SLA、CPU/MEM、依赖拓扑、Redis、APM 分析           | `bytedance-apm`                   |
| Log/APM 已执行但证据不足，需要额外 Argos tool 补充          | `bytedance-argos`                 |
| 完整/AI Trace、报警 RCA、oncall、大盘巡检、Argos Agent 编排 | `bytedance-argos`                 |
| EU/US TTP 日志或指标                                        | `bytedance-log` / `bytedance-apm` |

Agent 先按用户自然语言需求选择 `bytedance-log` 或 `bytedance-apm`，不要求用户知道底层命令。只有专用 skill 无法闭环、需求属于 Argos 独有能力、或用户明确指定 Argos 时，才进入本 skill。进入后优先调用确定性的 `argos tool`，多步推理才使用 `argos run`。
