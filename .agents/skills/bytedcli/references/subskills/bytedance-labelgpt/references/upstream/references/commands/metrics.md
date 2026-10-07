# metrics 命令

`metrics` 只读调用 ByteCloud Byteplot Metrics OpenAPI，用于发现和查询 LabelGPT 大盘、
小盘背后的监控指标。它复用 `auth login` 的 ByteCloud 登录态或显式 ByteCloud JWT，不要求
`--space-id`，也不使用 LabelGPT sync-token。

若 `LABELGPT_SERVER_TOKEN` trim 后非空，所有 Metrics 叶子命令都必须显式提供
`--byted-jwt-token <JWT>` 或 `LABELGPT_CLI_BYTED_JWT_TOKEN=<JWT>`。flag 优先于环境变量；
未提供时不读取 ByteCloud SDK 登录态，并在发出任何网络请求前失败。Server Token 本身不能
用于 Metrics。

分析 LabelGPT 核心服务时，继续读取
[LabelGPT 服务指标分析模板](../metrics/labelgpt-core.md)。该参考给出通用服务健康指标、
业务指标发现方法、核心 tag、查询模板和结果解释规则；其中 PSM 与指标名均为占位符，
执行前必须替换为当前环境确认后的值。

## 推荐探索顺序

```bash
bytedcli labelgpt metrics tenant-list --format raw
bytedcli labelgpt metrics search --prefix <LABELGPT_METRIC_PREFIX> --limit 100 --format raw
bytedcli labelgpt metrics field-list --metric <METRIC> --format raw
bytedcli labelgpt metrics tagk-list --metric <METRIC> --format raw
bytedcli labelgpt metrics tagv-list --metric <METRIC> --tag <TAG_KEY> --format raw
```

- `tenant-list`：列出当前 Metrics region 可见的 tenant。
- `search`：按 `--prefix` 搜索指标名；`--limit` 必须为正数，默认 10。
- `field-list`：查询指标字段。`fields` 非空表示多字段指标，查询时通常需要尾部字段表达式。
- `tagk-list`：查询指标的 tag key。
- `tagv-list`：查询一个或多个 tag key 的候选值；`--tag` 可重复或逗号分隔。
- 上述命令的 `--tenant` 默认 `default`。

`tagv-list --filter` 可重复，接受 `key=value` 或完整的 `key=filter(value)`；简写会转换为
`literal_or(value)`：

```bash
bytedcli labelgpt metrics tagv-list \
  --metric <FLOW_COUNTER_METRIC> \
  --tag scene --tag success \
  --filter agent_id=<AGENT_ID> \
  --format raw
```

## metrics query

```bash
bytedcli labelgpt metrics query '<QUERY_DSL>' \
  --start-time <UNIX_SECONDS> \
  --end-time <UNIX_SECONDS> \
  --format raw
```

DSL 与 Metrics 面板查询一致：

```text
aggregator[:topK][:downsample][:rate{options}]:metric{group_tags}{filter_tags}[multi_field_expr]
```

- aggregator：`max|min|avg|count|sum|zimsum|pct50|pct90|pct99`。
- topK：例如 `top-10-max`、`bottom-5-avg`。
- downsample：例如 `5m-sum-zero`；`store` 表示沿用存储粒度。
- rate：可选 `counter`、`diff`、`before_downsample|after_downsample`。
- 第一组 tag 同时 group-by 和过滤；第二组 tag 只过滤。
- 多字段指标在末尾添加 `[delta]`、`[rate]` 或面板支持的复合字段表达式。
- `--start-time/--end-time` 是 Unix 秒，必须为正且 start 小于 end。
- downsample interval 必须带单位，例如 `5m`、`1h`、`1d`；不要写裸数字 `300` 或
  `86400`。
- `delta_counter` 默认使用 `5m-sum`、`1h-sum` 或 `1d-sum`。只有确认该指标支持 fill
  policy 时才加 `-zero`。
- Histogram 的 `[hist_sum()]` 只能配 `sum` downsample，且不能加 `-zero/-nan/-none`。

示例：

```bash
bytedcli labelgpt metrics query \
  'sum:5m-sum:<FLOW_COUNTER_METRIC>{success=literal_or(*)}{scene=literal_or(agent_execute),agent_id=literal_or(<AGENT_ID>)}[delta]' \
  --start-time <START_SECONDS> \
  --end-time <END_SECONDS> \
  --format raw
```

高基数指标不要直接按所有 `agent_id`、`process_id`、`node_id` 或 `model_id` 展开长时间窗。
遇到 HTTP 430 / “查询读取数据量过大”时，先缩短时间范围，再增加这些业务 ID 或 `scene`
过滤，而不是反复重试原查询。

`raw/json` 输出包含原 DSL、metric、tenant、region、时间窗口、series 和 total_series。
每条 series 包含 tags、dps、可选 aggregated_tags 与读取统计。`pretty` 只展示每条时序的
点数、最新值、最小值、最大值和平均值；做精确分析时使用 `--format raw`。

## Region 与安全边界

- `--region` 可重复或逗号分隔，用于覆盖站点默认 Metrics region。
- `--custom-region` 决定固定的 Metrics OpenAPI host 与默认 region。
- 全局 `--endpoint` 只影响 LabelGPT API，不覆盖 Metrics host。
- CLI 不暴露任意 Metrics endpoint flag，并拒绝跨源 HTTP 重定向，避免把 JWT 发送到其它主机。
- Metrics 请求的 `Authorization` 使用 ByteCloud JWT 原值，不加 `Bearer`；不要在命令、日志或输出中回显 JWT。
- 设置 `LABELGPT_SERVER_TOKEN` 时只接受显式 flag/JWT 环境变量，不得通过 SDK fallback
  补齐 JWT；缺失时停止，不要重试 Metrics 请求。

## Schema 查询索引

```bash
bytedcli labelgpt schema metrics tenant-list --format raw
bytedcli labelgpt schema metrics search --format raw
bytedcli labelgpt schema metrics field-list --format raw
bytedcli labelgpt schema metrics tagk-list --format raw
bytedcli labelgpt schema metrics tagv-list --format raw
bytedcli labelgpt schema metrics query --format raw
```
