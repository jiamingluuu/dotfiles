# APM Service & Redis

## 命令行结构

`bytedcli [全局选项] apm <子命令族> <子命令> [命令选项]`

- 全局选项（`--json`、`--site`）放在 `apm` 之前
- 命令选项放在子命令之后
- **所有命令必须加 `--json`**

## apm service deps

查看服务的上下游依赖关系，包含每个依赖的 QPS、错误率和成功率。

| 选项 | 说明 |
|---|---|
| `--psm <psm>` | **必填**，服务 PSM |
| `--direction <dir>` | `upstream`、`downstream` 或 `both`（默认 both） |
| `--with-method` | 输出方法级依赖，增加对端 `method` 与当前 PSM 的 `self_method` |
| `--method <method>` | 只看当前 PSM 的指定接口（可多次指定/逗号分隔，隐含 `--with-method`） |
| `--start <timestamp>` | 开始时间（推荐 Unix 秒级时间戳，也支持 RFC3339 / `-1h`） |
| `--end <timestamp>` | 结束时间（推荐 Unix 秒级时间戳，也支持 RFC3339 / `now`） |
| `--range <duration>` | ⚠️ 废弃，不要使用 |
| `--region <region...>` | 过滤机房（可多次指定） |

输出内容：
- **Downstream Services**: 下游服务列表，含 Service、QPS、Error Rate、Success Rate
- **Upstream Services**: 上游服务列表，同上
- 使用 `--with-method` 或 `--method` 时，输出方法级依赖，其中 `self_method` 是当前 PSM 的接口，`method` 是对端接口

```bash
bytedcli --json apm service deps --psm "example.service.api"
bytedcli --json apm service deps --psm "example.service.api" --direction upstream
bytedcli --json apm service deps --psm "example.service.api" --direction downstream
bytedcli --json apm service deps --psm "example.service.api" --start 1714000000 --end 1714003600
bytedcli --json apm service deps --psm "example.service.api" --region "China-North"
bytedcli --json apm service deps --psm "example.service.api" --with-method
bytedcli --json apm service deps --psm "example.service.api" --method "QueryFoo"
```

## apm service methods

查看服务每个 method 的 QPS 和成功率，支持按成功率阈值过滤异常接口。

| 选项 | 说明 |
|---|---|
| `--psm <psm>` | **必填**，服务 PSM |
| `--min-success-rate <percent>` | 仅显示成功率低于此阈值的方法（如 `99.9`） |
| `--top <n>` | 仅显示 Top N（按 Max QPS） |
| `--method <method>` | 只看指定方法（可多次指定/逗号分隔） |
| `--latency` | 输出方法 P99 延迟（默认指标 `service.request.server.latency.total`，单位 ms） |
| `--latency-metric [name]` | 自定义延迟指标（可选，默认 `service.request.server.latency.total`） |
| `--total-metric <name>` | 自定义总量指标（默认 `service.request.server.throughput.total`） |
| `--error-metric <name>` | 自定义错误指标（默认 `service.request.server.throughput.error`） |
| `--aggregator <name>` | 聚合器（可多次/逗号分隔） |
| `--start <timestamp>` | 开始时间（推荐 Unix 秒级时间戳） |
| `--end <timestamp>` | 结束时间（推荐 Unix 秒级时间戳） |
| `--range <duration>` | ⚠️ 废弃，不要使用 |
| `--region <region...>` | 过滤机房（可多次指定） |

输出内容：
- **Service Methods**: 方法列表，含 Method、QPS、Success Rate
- 若无 per-method 数据，输出 Warning 提示

```bash
bytedcli --json apm service methods --psm "example.service.api"
bytedcli --json apm service methods --psm "example.service.api" --min-success-rate 99.9
bytedcli --json apm service methods --psm "example.service.api" --latency
bytedcli --json apm service methods --psm "example.service.api" --latency --top 10
bytedcli --json apm service methods --psm "example.service.api" --latency --method "QueryFoo"
bytedcli --json apm service methods --psm "example.service.api" --start 1714000000 --end 1714003600 --region "China-North"
```

## apm service qps

查看服务 QPS，支持自定义指标和多机房过滤。

| 选项 | 说明 |
|---|---|
| `--psm <psm>` | **必填**，服务 PSM |
| `--metric <name>` | 指标名（默认 `service.request.server.throughput.total`） |
| `--method <method>` | 过滤方法（可多次/逗号分隔） |
| `--measurement-tag <key=value>` | 过滤 Argos measurement tag（可多次；多值用 `|` 连接） |
| `--service-type <type>` | 服务类型（默认 `service`） |
| `--aggregator <name>` | 聚合器（可多次/逗号分隔） |
| `--start <timestamp>` | 开始时间 |
| `--end <timestamp>` | 结束时间 |
| `--range <duration>` | ⚠️ 废弃，不要使用 |
| `--region <region...>` | 过滤机房（可多次指定） |

```bash
bytedcli --json apm service qps --psm "example.service.api"
bytedcli --json apm service qps --psm "example.service.api" --metric "service.request.server.throughput.total"
bytedcli --json apm service qps --psm "example.service.api" --measurement-tag "service.env=prod"
```

## apm service measurement-params

查询指定 measurement 的建议 tag 和 aggregator。优先使用返回的原值；该列表不是完备约束，有较强理由时仍可尝试集合外值，空结果也不证明字段不存在。

| 选项 | 说明 |
|---|---|
| `--psm <psm>` | **必填**，服务 PSM |
| `--metric <name>` | **必填**，measurement 名称 |
| `--service-type <type>` | 服务类型（默认 `service`） |
| `--region <region>` | Argos region |

```bash
bytedcli --json apm service measurement-params --psm "example.service.api" --metric "service.request.server.throughput.total"
```

## apm service downstream-qps

查看服务调用下游依赖的 QPS。

| 选项 | 说明 |
|---|---|
| `--psm <psm>` | **必填**，服务 PSM |
| `--metric <name>` | 指标名（默认 `service.request.downstream.throughput.total`） |
| `--method <method>` | 过滤方法（可多次/逗号分隔） |
| `--measurement-tag <key=value>` | 过滤 Argos measurement tag（可多次；多值用 `|` 连接） |
| `--service-type <type>` | 服务类型 |
| `--aggregator <name>` | 聚合器（可多次/逗号分隔） |
| `--start <timestamp>` | 开始时间 |
| `--end <timestamp>` | 结束时间 |
| `--range <duration>` | ⚠️ 废弃，不要使用 |
| `--region <region...>` | 过滤机房（可多次指定） |

```bash
bytedcli --json apm service downstream-qps --psm "example.service.api"
```

## apm service preview

服务预览。默认 `--service-type service` 走 Argos overview（含 golden signals 与 clusters CPU/MEM）；`runtime` / 中间件类型走 Byteheart，**不要**用 `runtime` 代替服务级资源查询。

| 选项 | 说明 |
|---|---|
| `--psm <psm>` | **必填**，服务 PSM |
| `--service-type <type>` | 类型：`service`、`redis`、`mysql`、`runtime`、`tlb`、`tcc`、`agw_sidecar`（默认 `service`） |
| `--start <timestamp>` | 开始时间 |
| `--end <timestamp>` | 结束时间 |
| `--range <duration>` | ⚠️ 废弃，不要使用 |
| `--region <region...>` | 过滤机房（可多次指定；仅 Argos `service`/`redis` 路径生效） |

```bash
# 服务级 QPS / CPU / MEM（推荐；TTP/ROW 的 --region 必须配匹配的 --site）
bytedcli --json apm service preview --psm "example.service.api"
bytedcli --site eu-ttp --json apm service preview --psm "example.service.api" --region "EU-TTP2"
# JSON：golden_signals = QPS/SLA；clusters.rows = cpu_percent / mem_percent

bytedcli --json apm service preview --psm "cache.demo.redis" --service-type redis
# 中间件专项（Byteheart；非服务级 CPU/MEM 入口）
bytedcli --json apm service preview --psm "example.service.api" --service-type tlb
bytedcli --json apm service preview --psm "example.service.api" --service-type tcc
bytedcli --json apm service preview --psm "example.service.api" --service-type mysql
bytedcli --json apm service preview --psm "example.service.api" --service-type agw_sidecar
bytedcli --json apm service preview --psm "example.service.api" --service-type runtime
```

## apm faas-mq-trigger metrics

查询 FaaS MQ trigger 的成功消费 QPS。该命令走 infra Grafana 的 Prometheus datasource proxy，适合按 function id + MQ trigger id 快速确认消费吞吐。

| 选项 | 说明 |
|---|---|
| `--function <id>` | **必填**，FaaS function id |
| `--mqid <id>` | **必填**，FaaS MQ trigger id |
| `--start-time <timestamp>` | 开始时间（Unix 秒级时间戳）；与 `--end-time` 成对使用时覆盖默认时间窗 |
| `--end-time <timestamp>` | 结束时间（Unix 秒级时间戳）；与 `--start-time` 成对使用时覆盖默认时间窗 |
| `--duration <duration>` | 相对时间窗，默认 `30m` |
| `--step <duration>` | Prometheus query step，默认 `15s` |
| `--end-offset <duration>` | 默认结束时间相对 now 的偏移，默认 `30s` |
| `--datasource <name>` | Grafana Prometheus datasource，默认 `vefaas-cn-beijing` |
| `--grafana-url <url>` | Grafana base URL，默认 `https://infra-grafana.byted.org` |

输出内容：
- `function_id`: FaaS function id
- `mqid`: FaaS MQ trigger id
- `datasource`: Grafana Prometheus datasource name
- `datasource_id`: Grafana Prometheus datasource numeric id
- `grafana_url`: Grafana base URL used for the query
- `query`: 实际执行的 PromQL
- `start_time` / `end_time`: 实际查询时间窗（Unix 秒）
- `step_seconds`: Prometheus query step（秒）
- `points`: 成功消费 QPS 的时序点位
- `summary`: 点数、min、max、avg、last 摘要

```bash
bytedcli --json apm faas-mq-trigger metrics --function "demo-function" --mqid "demo-mqid" --duration 30m
bytedcli --json apm faas-mq-trigger metrics --function "demo-function" --mqid "demo-mqid" --start-time 1714000000 --end-time 1714003600 --step 15s
```

## apm faas-mq-trigger lag

查询 FaaS MQ trigger 关联 RocketMQ topic / consumer group 的生产 TPS、消费 TPS 和 group lag。该命令走 infra Grafana 的 Influx datasource proxy，与 `metrics` 的 Prometheus datasource 独立。

| 选项 | 说明 |
|---|---|
| `--mq-cluster <resource_id>` | **必填**，RocketMQ ResourceId |
| `--topic <topic>` | **必填**，RocketMQ topic |
| `--consumer-group <group>` | **必填**，RocketMQ consumer group |
| `--start-time <timestamp>` | 开始时间（Unix 秒级时间戳）；与 `--end-time` 成对使用时覆盖默认时间窗 |
| `--end-time <timestamp>` | 结束时间（Unix 秒级时间戳）；与 `--start-time` 成对使用时覆盖默认时间窗 |
| `--duration <duration>` | 相对时间窗，默认 `30m` |
| `--bucket <duration>` | Influx `GROUP BY time(...)` 桶，默认 `1m` |
| `--end-offset <duration>` | 默认结束时间相对 now 的偏移，默认 `2m`，避免当前分钟桶未完整 |
| `--datasource <name>` | Grafana Influx datasource，默认 `rocketmq_metrics_ops-influxdb-BJ` |
| `--database <name>` | Influx database，默认 `rocketmq_metrics_ops` |
| `--grafana-url <url>` | Grafana base URL，默认 `https://infra-grafana.byted.org` |

输出内容：
- `producer_tps`: topic 总生产速度，来自 `rmqtob_topic_put_tps`
- `consumer_tps`: 目标 consumer group 消费速度，来自 `rmqtob_consumer_tps`
- `group_lag`: 目标 consumer group lag，来自 `rmqtob_group_lag`

```bash
bytedcli --json apm faas-mq-trigger lag --mq-cluster "rocketmq-demo" --topic "demo-topic" --consumer-group "GID-demo" --duration 30m
bytedcli --json apm faas-mq-trigger lag --mq-cluster "rocketmq-demo" --topic "demo-topic" --consumer-group "GID-demo" --start-time 1714000000 --end-time 1714003600 --bucket 1m
```

## i18n 站点查询

deps / methods / qps / preview 均支持 `--site i18n-bd` 和 `--site i18n-tt`：

```bash
bytedcli --site i18n-bd --json apm service deps --psm "example.service.api"
bytedcli --site i18n-tt --json apm service qps --psm "example.service.api"
```

## apm argos event list

查看服务最近的 Argos 事件，适合在报警、成功率波动或错误日志上涨前后确认是否有 TCC、Bernard、TCE、Redis 等变更。

| 选项 | 说明 |
|---|---|
| `--psm <psm>` | **必填**，服务 PSM |
| `--region <region>` | Argos/APM region 或 vregion，如 `China-North` / `Singapore-Central` |
| `--start <timestamp>` | 开始时间（Unix 秒级时间戳），必须与 `--end` 成对使用 |
| `--end <timestamp>` | 结束时间（Unix 秒级时间戳），必须与 `--start` 成对使用 |
| `--duration <duration>` | 相对时间窗，默认 `12h`；不能与 `--start` / `--end` 同时使用 |
| `--category <name>` | 事件类别过滤，可重复指定或逗号分隔，如 `TCC,Bernard` |
| `--page <n>` | 页码，默认 `1` |
| `--page-size <n>` | 每页数量，默认 `100`，最大 `1000` |
| `--show-psms` | 文本模式展示事件影响的 PSM 列表 |

```bash
bytedcli --json apm argos event list --psm "example.service.api" --duration 12h
bytedcli --json apm argos event list --psm "example.service.api" --start 1714000000 --end 1714043200 --category TCC --category Bernard --page-size 100
```

## apm redis

Redis 监控命令，返回 Grafana/Argos 监控入口链接（按集群维度）。

| 子命令 | `--psm` | `--idc` | 说明 |
|--------|---------|---------|------|
| `qps` | ✅ 必填 | ❌ | 基于 Cache 服务详情的当前 QPS 统计 |
| `traffic` | ✅ 必填 | ❌ | 基于 Cache 服务详情的当前流量统计 |
| `overview` | ✅ 必填 | ✅ | Redis 集群概览 |
| `client` | ✅ 必填 | ✅ | 客户端连接信息 |
| `server` | ✅ 必填 | ✅ | 服务端信息 |
| `proxy` | ✅ 必填 | ✅ | 代理信息 |

**注意**：`apm redis` 不支持 `--region`，部分命令使用 `--idc` 过滤机房。

```bash
bytedcli --json apm redis qps --psm "cache.demo.redis"
bytedcli --json apm redis traffic --psm "cache.demo.redis"
bytedcli --json apm redis overview --psm "cache.demo.redis"
bytedcli --json apm redis client --psm "cache.demo.redis" --idc "HLF"
bytedcli --json apm redis server --psm "cache.demo.redis"
bytedcli --json apm redis proxy --psm "cache.demo.redis"
```
