# APM Metric 探索与高级查询

`apm metric` 支持完整的探索式查询连招（Tenant -> Metric -> Tags -> TagValues），以及通过 Query DSL 进行时序数据查询。底层使用 Byteplot API，原生支持多值指标查询。

**所有命令必须加 `--json`**（全局选项，放在 `apm` 之前）。

## Query DSL 语法

```
aggregator[:downsample][:rate{opts}][:topK]:metric_name{group_tags}{filter_tags}[multi_field_expr]
```

| 部分 | 必填 | 格式 | 示例 | 说明 |
|------|------|------|------|------|
| aggregator | ✅ | `sum\|avg\|max\|min\|count\|zimsum\|pct50\|pct90\|pct99` | `sum` | 顶层聚合函数；前 5 种为日常主力，`zimsum` 与 `sum` 等价，`pct50/pct90/pct99` 仅在少量百分位场景使用（如 pod CPU pct50/pct90） |
| downsample | ❌ | `<interval>-<agg>[-<fill>]` 或 `store` | `1m-sum-zero` | 可选，降采样；`store` = 不降采样（返回原始粒度）；省略 = 同 `store`。**必须以数字开头**；interval 单位：s/m/h/d；`<agg>` 仅支持 `max\|min\|avg\|count\|sum` 这 5 种核心聚合 |
| rate{opts} | ❌ | `rate{counter[,diff][,before_downsample\|after_downsample]}` 或 `rate(counter,...)` | `rate{counter}` | 可选，计算速率；`counter` 表示单调递增计数器；`before_downsample` 与 `after_downsample` 互斥，默认 `before_downsample` |
| topK | ❌ | `top-<N>-<agg>` 或 `bottom-<N>-<agg>` | `top-10-max` | 可选，TopK 排序；`<agg>` 仅支持 `max\|min\|avg\|count\|sum` 这 5 种核心聚合 |
| metric_name | ✅ | 点分指标名 | `example.service.api.throughput` | 原始指标名，不带 field 后缀 |
| group_tags | ✅ | `tagk=type(value)[,tagk=type(value)]` | `{_psm=literal_or(example.service.api)}` | 第一个 `{}`，groupBy=true；可为空 `{}` |
| filter_tags | ✅ | `tagk=type(value)[,tagk=type(value)]` | `{priority_region=literal_or(MY)}` | 第二个 `{}`，groupBy=false；可为空 `{}` |
| multi_field_expr | ❌ | `delta\|rate\|counter\|pct50\|pct99\|weighted_avg(value=X,weight=counter)\|avg` | `[delta]` | 仅多值指标需要；单值指标不写；**必须放在末尾** |

**⚠️ DSL 段顺序约定**：LLM / Skills 生成查询时**必须严格**按 `aggregator → downsample → rate → topK → metric → {tags}{filters}[field]` 的顺序拼接，便于人类阅读和审查。

> 实现侧 parser 出于鲁棒性考虑会宽松接受任意顺序的中间段（按格式特征识别 downsample / rate / topK），但这是「容错」而非「推荐用法」。Agent / 文档示例不应依赖这种宽松行为，避免后续维护时被误以为顺序无关。

**⚠️ 旧格式 downsample 拦截**：`sum-1m-zero`（agg-interval-fill）是旧 Argos 格式，已被拒绝。必须使用 `1m-sum-zero`（interval-agg-fill）。CLI 会自动检测并给出修正建议。

**5 种典型 DSL 格式**：

| # | 场景 | DSL 示例 |
|---|------|---------|
| 1 | 最简单 | `sum:metric_name{}{}` |
| 2 | 带降精度 | `sum:1m-sum-zero:metric_name{}{}` |
| 3 | 原始精度 | `sum:store:metric_name{}{}` |
| 4 | TopK | `sum:top-10-max:metric_name{}{}` |
| 5 | TopK + 降精度 | `sum:1m-sum-zero:top-10-max:metric_name{}{}` |

**最简形式（单值指标，无降采样，无 topK）：**
```
sum:metric_name{}{}
```

**完整形式（多值指标，含所有可选部分）：**
```
sum:1m-sum-zero:rate{counter}:top-10-max:example.service.api.throughput{method=literal_or(*)}{priority_region=literal_or(MY)}[delta]
```

### 降采样策略

| 场景 | 推荐 downsample | 说明 |
|------|----------------|------|
| delta（区间增量） | `1m-sum` / `5m-sum` / `1h-sum-zero` | delta 是增量值，降采样用 sum 聚合 |
| rate（速率）/ timer（延迟） | `1m-avg` / `5m-avg` / `1h-avg-zero` | rate 和 timer 是比率/百分位值，降采样用 avg 聚合 |
| 短周期（≤6h） | `store` 或省略 | 返回原始粒度数据点（通常 30s），数据最精确 |
| 长周期（>24h） | 必须指定 downsample | 不指定则返回原始粒度，数据量过大可能导致查询超时 |

**`store` 的行为**：DSL 中写 `store` 会被转换为 Byteplot API 的空字符串 `""`，效果与不指定 downsample 完全一致——返回底层存储的原始粒度数据点（大部分指标默认 30s 粒度）。

**⚠️ 不存在 `auto` downsample**：Byteplot API 不支持 `auto-avg-none` 等以 `auto` 开头的 downsample 格式，传入会报 `Invalid duration (number): auto` 错误。

**合法的 downsample 格式**：`<interval>-<aggregator>[-<fill_policy>]`
- `interval`：数字（秒），如 `30`、`60`、`300`、`3600`
- `aggregator`：`avg`、`sum`、`max`、`min`、`count`（仅 5 种核心聚合，`zimsum` / `pct50` / `pct90` / `pct99` 不支持，传入会触发 ByteTSD 服务端报错）
- `fill_policy`（可选）：`none`（默认）、`zero`（填 0）、`nan`（填 NaN）

示例：
- `1m-avg` = `60-avg`：60 秒平均
- `5m-sum-zero` = `300-sum-zero`：300 秒求和，空值填 0
- `1h-avg-nan` = `3600-avg-nan`：1 小时平均，空值填 NaN

### 过滤操作符 (Filter Operators)

**必须使用** `key=func(value)` 格式，**禁止** `key=value`。默认推荐 `literal_or`。

- `literal_or`：精确匹配多个值，大小写敏感。例如 `_psm=literal_or(example.api,example.rpc)`
- `iliteral_or`：精确匹配多个值，大小写不敏感。例如 `country_code=iliteral_or(us,my)`
- `regexp`：支持正则过滤。例如 `_psm=regexp(example\..*)`
- **按 tag 分组但不过滤**：`key=literal_or(*)`，例如 `country_code=literal_or(*)` 表示按 country_code 分组

### 双花括号 `{}` 规则

- 第一个 `{}`：**分组 (Group By) 并过滤**。放在这里的 Tag Key，返回数据会按它分组
- 第二个 `{}`：**仅过滤 (Filter Only)**。只缩小数据范围，不分组
- 同一个 Tag Key 可以在两个 `{}` 里同时出现

### `[multi_field_expr]` 规则

- **多值指标**：**必须**在末尾写 `[field]`，如 `[delta]`、`[weighted_avg(value=pct99,weight=counter)]`
- **单值指标**：**不写** `[field]`
- `[field]` 必须放在 `{...}{...}` 之后，是整个表达式的最后一部分

## 多值指标类型判断

通过 `field-list` 返回的字段列表判断指标类型：

| 字段组合 | 类型 | 说明 |
|----------|------|------|
| 空列表 `[]` | **单值** | 如 `bytedtrace.sdk.span.server.rate` |
| `counter` + `delta` + `rate` | **delta_counter** | 吞吐类指标，如 `*.throughput` |
| `counter` + `pct50` + `pct90` + `pct95` + `pct99` + `avg` + `max` + `min` + `sum` | **timer** | 延迟类指标，如 `*.latency` |
| 其他组合 | **未知多值类型** | 自定义多值指标，需和用户确认查询逻辑 |

**各类型查询方式：**

| 类型 | 查总量 | 查 QPS | 查百分位 |
|------|--------|--------|---------|
| delta_counter | `[delta]` | `[rate]` | — |
| timer | — | — | `[weighted_avg(value=pct99,weight=counter)]` 或 `[pct50]` |
| 未知多值 | 需确认 | 需确认 | 需确认 |

**判断流程**：
1. 先用 `field-list` 查字段列表
2. 空列表 → 单值指标，不需要 `[field]`
3. 匹配 delta_counter 或 timer 模式 → 按上表选择
4. 其他组合 → 向用户确认使用哪个 field 以及是否需要加权

## TagRewrite 规则

TagRewrite 将 tag 拼接到指标名中，查询时**必须固定携带**申请的 TagKV，不支持 `*` 或多个 tagv。

常见 TagRewrite 指标：
- `bytedtrace.sdk.span.*` 前缀指标**必须**传入 `_psm` tag
- `tce.container.*` 前缀指标**必须**传入 `_psm` 或 `cluster` tag

**错误信息示例**（中英文均可能）：
- `[IllegalArgumentException](无效的查询参数：指标「bytedtrace.sdk.span.server.rate」申请了tag rewrite，查询时需要填写这些tag(s):[_psm]。)`

**Agent 处理逻辑**：
1. 查询报错包含 "tag rewrite" 或 "tag(s)" → 提取必须填写的 tagKey 列表
2. 如果已知 tagValue（如从 PSM 推断 `_psm`），自动填入
3. 如果不知道 tagValue，提示用户确认

## 5大命令连招 (探索工作流)

1. **查租户 (tenant-list)**:
   ```bash
   bytedcli --json apm metric tenant-list
   ```

2. **找对名字 (search)**:
   ```bash
   bytedcli --json apm metric search --prefix "service.request"
   bytedcli --site i18n-tt --json apm metric search --prefix "example.service.api"
   ```

3. **查多值字段与 Tag Keys (field-list / tagk-list)**:
   ```bash
   bytedcli --json apm metric field-list --metric "demo.service.api.latency"
   bytedcli --json apm metric tagk-list --metric "example.service.api.throughput"
   ```

4. **查特定 Tag 的合法值 (tagv-list)**:
   ```bash
   bytedcli --json apm metric tagv-list --metric "example.service.api.throughput" --tags [tag_name]
   ```

5. **组装最终查询 (query)**:
   ```bash
   # 单值指标
   bytedcli --json apm metric query "sum:bytedtrace.sdk.span.server.rate{}{_psm=literal_or(example.demo.api)}" --start-time 1714000000 --end-time 1714003600

   # 多值 delta_counter + delta
   bytedcli --site i18n-tt --json apm metric query "sum:store:example.service.api.throughput{_psm=literal_or(example.service.api)}{}[delta]" --start-time 1714000000 --end-time 1714003600 --region Singapore-Central

   # 多值 timer + 加权 P99
   bytedcli --site i18n-tt --json apm metric query "sum:store:demo.service.api.latency{_psm=literal_or(example.service.api)}{}[weighted_avg(value=pct99,weight=counter)]" --start-time 1714000000 --end-time 1714003600 --region Singapore-Central
   ```

## Response 格式（`--json` 输出）

所有 `apm metric` 命令在 `--json` 模式下返回统一外层格式：

```json
{
  "status": "success" | "error",
  "data": <array | object | null>,
  "error": <object | null>,
  "context": {}
}
```

### 判断成功/失败

| 判断方式 | 成功 | 失败 |
|----------|------|------|
| `status` 字段 | `"success"` | `"error"` |
| 进程 exit code | `0` | `1`（API 错误）/ `2`（CLI 参数缺失） |

**Agent 必须先检查 `status` 字段**，不要仅依赖 exit code。

### 各子命令成功响应示例

**`tenant-list`** — `data` 为 `string[]`：

```json
{"status":"success","data":["default","example.tenant.a","example.tenant.b","example.tenant.c"],"error":null,"context":{}}
```

**`search`** — `data` 为 `string[]`，空结果返回 `[]`：

```json
{"status":"success","data":["example.service.api.throughput","example.service.api.latency"],"error":null,"context":{}}
```

**`field-list`** — `data` 为 `string[]`；空数组 `[]` = 单值指标：

```json
{"status":"success","data":["counter","delta","rate"],"error":null,"context":{}}
```

**`tagk-list`** — `data` 为 `string[]`：

```json
{"status":"success","data":["_psm","_dc","_deploy_stage","method","cluster"],"error":null,"context":{}}
```

**`tagv-list`** — `data` 为 `object[]`，每个元素是 `{tagKey: [values]}`：

```json
{"status":"success","data":[{"_dc":["dc-1","dc-2","dc-3"]},{"_deploy_stage":["canary","single_dc","all_dc"]}],"error":null,"context":{}}
```

**空结果不报错**：不存在的指标名，`search`/`field-list`/`tagk-list` 返回 `data: []` + `status: "success"`，不会报错。

### `query` 成功响应详解

`data` 是时序数组，每个元素代表一条时间线。

**输入 → 输出对照**：

```
# 输入 DSL：按 _dc 和 _deploy_stage 分组，过滤 _psm
sum:1m-sum-zero:example.service.api.throughput{_dc=literal_or(*),_deploy_stage=literal_or(*)}{_psm=literal_or(example.service.api)}[delta]
```

```json
{
  "status": "success",
  "data": [
    {
      "metric": "example.service.api.throughput",
      "aggregatedTags": [],
      "stats": {
        "rewriteTags": null,
        "preaggTags": null,
        "preAggRewrites": null,
        "mergedSubQueryIndexes": [],
        "read_dps": 1319,
        "read_series": 52,
        "read_bytes": 75952,
        "read_files": 0
      },
      "dps": {
        "1779870000": 6,
        "1779870060": 5,
        "1779870120": 13,
        "1779870180": 7,
        "1779870240": 5,
        "1779870300": 9
      },
      "query": { "index": 0, "tenant": "default" },
      "tags": { "_dc": "dc-1", "_deploy_stage": "all_dc" }
    },
    {
      "metric": "example.service.api.throughput",
      "aggregatedTags": [],
      "stats": { "rewriteTags": null, "read_dps": 800, "read_series": 30, "read_bytes": 45000, "read_files": 0 },
      "dps": { "1779870000": 3, "1779870060": 4, "1779870120": 8 },
      "query": { "index": 0, "tenant": "default" },
      "tags": { "_dc": "dc-2", "_deploy_stage": "canary" }
    }
  ],
  "error": null,
  "context": {}
}
```

**解读**：DSL 第一个 `{}` 里 `_dc=literal_or(*)` 和 `_deploy_stage=literal_or(*)` 表示按这两个 tag 分组，因此返回多条时间线——每条对应一组 tag 值组合（`dc-1+all_dc`、`dc-2+canary` 等）。第二个 `{}` 里 `_psm=literal_or(example.service.api)` 只做过滤、不分组，所以 `_psm` 不出现在 `tags` 中，而是出现在 `aggregatedTags` 里（被聚合掉了）。

| 字段 | 类型 | 说明 |
|------|------|------|
| `data[].metric` | string | 指标名 |
| `data[].dps` | object | **时间序列**：key=Unix 秒级时间戳（字符串），value=指标值（数字）；按 downsample 间隔排列，如 `1m-sum-zero` 则每 60s 一个点 |
| `data[].tags` | object | 分组 tag 的值（groupBy 的 tag 出现在这里）；无 groupBy 时为 `{}` |
| `data[].aggregatedTags` | string[] | 被聚合掉的 tag key |
| `data[].stats` | object | 查询统计：`read_dps`（扫描数据点数）、`read_series`（扫描时间线数）、`read_bytes`（扫描字节数） |
| `data[].query` | object | 查询元信息：`index`（子查询序号）、`tenant`（租户名） |

**阅读要点**：
- `dps` 为空对象 `{}` → 该时间线无数据点
- `data` 为空数组 `[]` → 查询成功但无匹配时间线（指标名错误或 tag 不匹配）
- 多个 `data[]` 元素 → 有 groupBy tag 导致的多条时间线（每个 tag 值组合一条）
- `dps` 的 key 是**字符串类型**的 Unix 时间戳，不是数字

### query 结果处理脚本

**提取时间线摘要（metric + tags + 点数 + 最新值）**：

```bash
bytedcli --json apm metric query "sum:1m-sum-zero:example.metric{country_code=literal_or(ID)}{}[delta]" \
  --start-time 1779870000 --end-time 1779873600 --region Singapore-Central \
  | python3 -c "
import sys, json
result = json.load(sys.stdin)
if result['status'] != 'success':
    print('Error:', result['error']['message']); sys.exit(1)
for ts in result['data']:
    dps = ts['dps']
    latest_ts = max(dps.keys()) if dps else 'N/A'
    latest_val = dps[latest_ts] if dps else 'N/A'
    print(f\"metric={ts['metric']} tags={ts['tags']} points={len(dps)} latest={latest_val} @{latest_ts}\")
"
```

**提取某条时间线的值序列**：

```bash
bytedcli --json apm metric query "sum:1m-sum-zero:example.metric{country_code=literal_or(ID)}{}[delta]" \
  --start-time 1779870000 --end-time 1779873600 --region Singapore-Central \
  | python3 -c "
import sys, json
result = json.load(sys.stdin)
for ts in result['data']:
    if ts['tags'].get('country_code') == 'ID':
        for t, v in sorted(ts['dps'].items(), key=lambda x: int(x[0])):
            from datetime import datetime, timezone
            dt = datetime.fromtimestamp(int(t), tz=timezone.utc)
            print(f'{dt.isoformat()}  {v}')
        break
"
```

**汇总多条时间线的总和**：

```bash
bytedcli --json apm metric query "sum:1m-sum-zero:example.metric{country_code=literal_or(*)}{}[delta]" \
  --start-time 1779870000 --end-time 1779873600 --region Singapore-Central \
  | python3 -c "
import sys, json
from collections import defaultdict
result = json.load(sys.stdin)
merged = defaultdict(float)
for ts in result['data']:
    for t, v in ts['dps'].items():
        merged[t] += v
total = sum(merged.values())
print(f'Total across all series: {total:.0f}')
print(f'Points: {len(merged)}')
"
```

### 失败响应（`status: "error"`）

**API 错误**（exit code=1）：

```json
{
  "status": "error",
  "data": null,
  "error": {
    "message": "HTTP 400\n...",
    "code": 400,
    "status_code": 400,
    "request_id": "20260427...",
    "endpoint": "https://metrics-fe-i18n.tiktok-row.org/byteplot/api/metrics/query?...",
    "details": { "method": "POST", "response": { "kind": "json", "value": { "error": { "code": 400, "message": "..." } } } }
  }
}
```

**CLI 参数缺失**（exit code=2）：

```json
{
  "status": "error",
  "data": { "help": { "name": "search", "options": [...] } },
  "error": {
    "message": "Missing required arguments/options: --prefix.",
    "code": "CLI_ARGS_MISSING",
    "details": { "command": "search", "missing": ["--prefix"] }
  }
}
```

| 字段 | 说明 |
|------|------|
| `error.message` | **首选字段**：错误描述（API 错误含 HTTP 状态码 + 原始信息；CLI 错误指出缺少的参数） |
| `error.code` | 错误码：`CLI_ARGS_MISSING`（CLI 参数缺失）或 HTTP 状态码（API 错误） |
| `error.details.missing` | CLI 参数缺失时，列出缺少的参数名 |
| `error.details.response.value.error.message` | Byteplot API 原始错误（嵌套较深，`error.message` 通常已足够） |

### 常见错误模式

| 错误关键词 | 原因 | 处理 |
|-----------|------|------|
| `CLI_ARGS_MISSING` | 缺少必填 CLI 参数 | 按 `error.details.missing` 补充参数 |
| `多值指标` + `请明确指定` | 多值指标未写 `[field]` | 补充 `[delta]`/`[rate]`/`[weighted_avg(...)]` 等 |
| `tag rewrite` + `需要填写这些tag(s)` | TagRewrite 指标缺少必需 tag | 补充 `_psm`/`cluster` 等 tag |
| HTTP 400 + 其他 | DSL 语法错误 | 检查 `{}` 配对、`[field]` 位置、filter 语法 |
| `data: []` 且无 error | 指标名或 tag 值不匹配 | 用 `search`/`tagv-list` 确认指标名和 tag 值 |

## 参数格式（防幻觉警告）

**`apm metric query` 绝对没有 `--psm` 和 `--query` 这两个 flag。**
查询语句必须是 **位置参数 (Positional Argument)** 直接紧跟在 `apm metric query` 之后。过滤条件（如 PSM、Method 等）必须写在 query 的标签（大括号 `{}`）内。

## 常见指标查询范式

### 单值 gauge 指标

```bash
bytedcli --json apm metric query "sum:bytedtrace.sdk.span.server.rate{}{_psm=literal_or(example.demo.api)}" --start-time 1714000000 --end-time 1714003600
```

### 单值 counter 指标

```bash
# 算 QPS（rate{counter}）
bytedcli --json apm metric query "sum:rate{counter}:example.service.api.request{_psm=literal_or(example.service.api)}{}" --start-time 1714000000 --end-time 1714003600

# 算区间和（rate{counter,diff}）
bytedcli --json apm metric query "sum:rate{counter,diff}:example.service.api.request{_psm=literal_or(example.service.api)}{}" --start-time 1714000000 --end-time 1714003600
```

### 多值 delta_counter（吞吐量）

```bash
# 求增量总量
bytedcli --json apm metric query "sum:store:example.service.api.throughput{_psm=literal_or(example.service.api)}{}[delta]" --start-time 1714000000 --end-time 1714003600

# 求 QPS
bytedcli --json apm metric query "sum:store:example.service.api.throughput{_psm=literal_or(example.service.api)}{}[rate]" --start-time 1714000000 --end-time 1714003600

# 带 groupBy + filter
bytedcli --json apm metric query "sum:store:example.service.api.throughput{method=literal_or(*)}{priority_region=literal_or(MY)}[delta]" --start-time 1714000000 --end-time 1714003600
```

### 多值 timer（延迟）

```bash
# 加权 P99（推荐）
bytedcli --json apm metric query "sum:store:demo.service.api.latency{_psm=literal_or(example.service.api)}{}[weighted_avg(value=pct99,weight=counter)]" --start-time 1714000000 --end-time 1714003600

# 加权 avg
bytedcli --json apm metric query "sum:store:demo.service.api.latency{_psm=literal_or(example.service.api)}{}[weighted_avg(value=avg,weight=counter)]" --start-time 1714000000 --end-time 1714003600

# 非加权 pct50
bytedcli --json apm metric query "sum:store:demo.service.api.latency{_psm=literal_or(example.service.api)}{}[pct50]" --start-time 1714000000 --end-time 1714003600

# 长窗口降精度（5m-avg）
bytedcli --json apm metric query "sum:5m-avg:demo.service.api.latency{_psm=literal_or(example.service.api)}{}[weighted_avg(value=pct99,weight=counter)]" --start-time 1714000000 --end-time 1714033600
```

**为什么延迟指标需要加权**：P99 是百分位值，多个实例的 P99 不能简单相加。例如实例 A（1000 QPS，P99=50ms）和实例 B（10 QPS，P99=500ms），直接 sum 会得到 550ms，但真实全局 P99 应接近 50ms。`weighted_avg` 用 `counter`（请求计数）作为权重，确保高流量实例对结果的影响更大。

### TopK 查询

```bash
# Top 10 by delta
bytedcli --json apm metric query "sum:top-10-max:store:example.service.api.throughput{method=literal_or(*)}{}[delta]" --start-time 1714000000 --end-time 1714003600

# Bottom 5 by P99
bytedcli --json apm metric query "sum:bottom-5-min:store:demo.service.api.latency{_psm=literal_or(example.service.api)}{}[weighted_avg(value=pct99,weight=counter)]" --start-time 1714000000 --end-time 1714003600
```

### 多 Region 查询

默认只查询当前站点的默认单 region（例如 `--site i18n-tt` 默认 `Singapore-Central`）。多 region 会改变结果语义，只有明确需要跨机房联合查询时才显式传多个 `--region` 或使用 `--all-regions`。

```bash
# 双 region
bytedcli --site i18n-tt --json apm metric query "sum:store:example.service.api.throughput{_psm=literal_or(example.service.api)}{}[delta]" --start-time 1714000000 --end-time 1714003600 --region Singapore-Central --region MY-Compliance

# 三 region
bytedcli --site i18n-tt --json apm metric query "sum:store:example.service.api.throughput{_psm=literal_or(example.service.api)}{}[delta]" --start-time 1714000000 --end-time 1714003600 --region Singapore-Central --region MY-Compliance --region Singapore-Compliance
```

## 常见指标 (Common Metrics)

### Server 端指标
- **QPS**: `bytedtrace.sdk.span.server.rate`（单值，有 TagRewrite，必须带 `_psm`）
- **Latency (us)**: `bytedtrace.sdk.span.server.latency.us`（单值，有 TagRewrite，必须带 `_psm`）
- **入流量 (Bytes)**: `bytedtrace.sdk.span.server.receive.bytes`
- **出流量 (Bytes)**: `bytedtrace.sdk.span.server.send.bytes`
- **常用 Tag**: `_psm` (所在服务名), `_method` (接口名), `_from_service` (上游调用方 PSM), `_status_code` (状态码), `_is_error` (0:成功, 1:失败)

### Client 端指标
- **QPS**: `bytedtrace.sdk.span.client.rate`
- **Latency (us)**: `bytedtrace.sdk.span.client.latency.us`
- **入流量 (Bytes)**: `bytedtrace.sdk.span.client.receive.bytes`
- **出流量 (Bytes)**: `bytedtrace.sdk.span.client.send.bytes`
- **常用 Tag**: `_psm` (所在服务名), `_to_service` (下游被调服务名), `_to_method` (下游接口名)

### Panic 与 Runtime 指标
- **Panic 次数**: `runtime.go.panics` (注：需在特定租户 apm.runtime 下使用)
  - 常用 Tag: `role` (server/client), `from_service`, `to_service`, `method`
