---
name: bytedance-nvqos
description: "Operate NVQoS / VQoS via bytedcli: list spaces, list datasets, query dataset data, search trace records, and trigger root cause analysis. Use when tasks mention NVQoS, VQoS, vqos, QoS traces, trace/query, QoS attribution, rootcause/root cause analysis, space/list, dataset/list, query_data, or intelligent attribution for QoS metrics."
---

# bytedcli NVQoS

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

- 用户提到 NVQoS / VQoS / vqos / QoS root cause / 智能归因 / 触发归因
- 需要列出 NVQoS spaces 或 datasets，用于后续构造查数或归因请求
- 用户需要查询数据集数据（查数 / query_data / data query），给出 dataset id、metric、时间窗口、维度等
- 用户已经给出 `SpaceId`、`Dataset`、`Metric`、时间窗口、Filters JSON，需要调用 `/rootcause/v1/analysis`

## Auth and region

- 先执行 `bytedcli auth login`。
- NVQoS 命令使用 ByteCloud JWT 调用后端，并设置 `X-Jwt-Token`；带 `--space-id` 时同时设置 `X-Nvqos-Space-Id`。
- `--region` 支持 `cn`、`boe`、`sg`、`va`、`mybd`。默认 `cn`；也可用 `BYTEDCLI_NVQOS_REGION` 覆盖。
- `mybd` 使用 SINF i18n FaaS endpoint，并通过 `i18n-bd` ByteCloud 站点获取 JWT。
- 需要联调非内置环境时，用 `--base-url <url>` 或 `BYTEDCLI_NVQOS_BASE_URL` 覆盖。

## Commands

```bash
# 列空间
bytedcli nvqos space list --region sg --page 1 --page-size 20

# 按名称过滤空间
bytedcli --json nvqos space list --region cn --name sample-space

# 列数据集；--space-id 会同时进入 query SpaceID 和 X-Nvqos-Space-Id header
bytedcli nvqos dataset list --region sg --space-id 10001 --page-size 50

# 按名称过滤数据集
bytedcli --json nvqos dataset list --region sg --space-id 10001 --name sample-dataset

# 查数（dataset query_data）— 显式参数模式
bytedcli --json nvqos dataset query \
  --region sg \
  --space-id 10001 \
  --dataset-id 10086 \
  --metric sample_metric \
  --group-by os \
  --start 2026-07-01T16:00:00Z \
  --end 2026-07-02T02:00:00Z \
  --window 3600

# 查数 — body-file 模式
bytedcli --json nvqos dataset query --region sg --body-file /tmp/nvqos-query-body.json

# 搜索 trace；文本模式优先显示 Columns.Alias 中文列名
bytedcli nvqos trace search \
  --region cn \
  --space-id 10001 \
  --trace-id 20001 \
  --app-id 123 \
  --device-id sample-device-id \
  --start 2026-07-01T16:00:00Z \
  --end 2026-07-02T02:00:00Z
```

## Dataset Query (查数)

调用 `POST /dataset/query_data`，请求体为 thrift `DataRequest`。优先用显式参数构造；复杂请求用 `--body-file` 传完整 JSON。显式参数会覆盖 body 里的同名字段。

```bash
bytedcli --json nvqos dataset query \
  --region sg \
  --space-id 10001 \
  --dataset-id 10086 \
  --metric sample_metric \
  --group-by os \
  --start 2026-07-01T16:00:00Z \
  --end 2026-07-02T02:00:00Z \
  --window 3600 \
  --filters-json '[{"Op":"and","SubFilters":[{"Field":"app_id","Op":"in","Values":["123"]}]}]'
```

完整 body 文件示例：

```json
{
  "DataSetID": 10086,
  "Start": 1782940800,
  "End": 1783012800,
  "Metrics": ["sample_metric"],
  "GroupBys": ["os"],
  "Window": 3600,
  "Filters": [
    {
      "Op": "and",
      "SubFilters": [
        {
          "Field": "app_id",
          "Op": "in",
          "Values": ["123"]
        }
      ]
    }
  ]
}
```

```bash
bytedcli --json nvqos dataset query --region sg --body-file /tmp/nvqos-query-body.json
```

### 请求体要点

- `DataSetID` 是数字类型的数据集 ID；CLI 用 `--dataset-id 10086` 传入。也可用 `--dataset-key <key>` 传 `DataSetKey`，二选一。
- `Start` / `End` 是**秒级 Unix 时间戳**；CLI 的 `--start` / `--end` 接受 RFC3339 字符串或 Unix 秒/毫秒，内部自动折算成秒。
- `Window` 为聚合粒度（秒），常见值：`60`、`300`、`3600`、`86400`。
- `Metrics` 是指标名数组，`--metric` 支持重复传或逗号分隔。
- `GroupBys` 是拆分维度数组，`--group-by` 支持重复传或逗号分隔。
- `Filters` 结构与 NVQoS 后端一致，支持 `Op`、`Field`、`Values`、`SubFilters`。
- `--space-id` 只设置 `X-Nvqos-Space-Id` header，不进入 body。
- `--order-by <field>` 默认 `Direction: "desc"`，可用 `--order-direction asc` 改为升序。

### 响应结构

响应为 `DataResponse`（解包后）：

- `Columns`: 列元信息，每列包含 `Name`、`Alias`、`Type`
- `Data`: 行数据数组，每行是 `{ [列名]: 值 }` 的 map
- `Total` / `TotalPoint`: 总行数相关
- `Limit` / `Offset`: 分页参数

JSON 输出中 `data.columns` 和 `data.data` 分别对应解析后的列和行。

## Trace Search

调用 `POST /trace/query`。`--start` / `--end` 接受 RFC3339 或 Unix 秒/毫秒，发送时统一转换为毫秒级 `StartTime` / `EndTime`。

```bash
bytedcli --json nvqos trace search \
  --region mybd \
  --space-id 10001 \
  --trace-id 20001 \
  --app-id 123 \
  --device-id sample-device-id \
  --start 2026-07-01T16:00:00Z \
  --end 2026-07-02T02:00:00Z \
  --page 1 \
  --page-size 20
```

- 显式参数模式必须提供 `--space-id`、`--trace-id`、`--app-id`、`--device-id`、`--start`、`--end`。
- CLI 将 `--app-id`、`--device-id` 自动转换为值非空的 Filters 条件；`--filters-json` / `--filters-file` 仅追加其他 AND 条件。
- 完整 body 模式可通过 `--body-json` / `--body-file` 直接提供 Filters，其中仍须在 AND 路径下同时包含值非空的 `app_id in` 与 `device_id in` 条件。
- `Filters` 是单个递归 JSON 对象，不是数组；复杂查询也可额外使用 `--kql`。
- 默认按 `nvqos_timestamp ASC` 排序并设置 `WithSource=true`；使用 `--no-with-source` 可关闭。
- `--language` 支持 `zh`、`en`，默认 `zh`。
- 文本模式默认展示常用 trace 字段，并优先使用 `Columns.Alias` 中文表头；`--field` 支持重复或逗号分隔，只影响文本展示。
- JSON 模式返回全部 `columns`、`traces`、`total_point`、`limit` 和不含 SQL 的 `debug_info`。

## Root Cause Analysis

优先用显式参数构造请求；复杂请求可以用 `--body-file` 传完整 JSON。显式参数会覆盖 body 里的同名字段。

```bash
bytedcli --json nvqos rootcause analyze \
  --region sg \
  --space-id 23 \
  --dataset-id 231 \
  --metric sample_metric \
  --aggregate-interval 3600 \
  --start 2026-07-01T16:00:00Z \
  --end 2026-07-02T02:00:00Z \
  --filters-json '[{"Op":"and","SubFilters":[{"Field":"app_id","Op":"in","Values":["123"]}]}]'
```

完整 body 文件示例：

```json
{
  "AggregateInterval": 3600,
  "Dataset": "231",
  "End": "2026-07-02T02:00:00Z",
  "Filters": [
    {
      "Op": "and",
      "SubFilters": [
        {
          "Field": "app_id",
          "Op": "in",
          "Values": ["123"]
        }
      ]
    }
  ],
  "Metric": "sample_metric",
  "SpaceId": 23,
  "Start": "2026-07-01T16:00:00Z"
}
```

```bash
bytedcli --json nvqos rootcause analyze --region sg --body-file /tmp/nvqos-rootcause-body.json
```

## Request shape notes

- `Dataset` 需要传字符串形式的数据集 ID，例如 `"231"`；CLI 的 `--dataset-id 231` 会自动作为 `Dataset` 传入。
- `AggregateInterval` 仅支持 `60`、`300`、`3600`、`86400`；未传时 CLI 默认补 `3600`，JSON 输出会在 `defaults_applied.AggregateInterval` 里标出。
- `Filters` 必须是 JSON array，结构与 NVQoS 后端一致，支持 `Op`、`Field`、`Values`、`SubFilters`。
- `Operator` 可以传入，但后端通常会用 JWT 解析出的用户名覆盖它。
- `--analysis-dim` 和 `--scene` 都支持重复传或逗号分隔。

## JSON output preference

Agent 调用默认加 `--json`，并把它放在 domain 前：

```bash
bytedcli --json nvqos space list --region sg
bytedcli --json nvqos dataset list --region sg --space-id 10001
bytedcli --json nvqos dataset query --region sg --dataset-id 10086 --metric sample_metric --start 2026-07-01T16:00:00Z --end 2026-07-02T02:00:00Z
bytedcli --json nvqos trace search --region mybd --space-id 10001 --trace-id 20001 --app-id 123 --device-id sample-device-id --start 2026-07-01T16:00:00Z --end 2026-07-02T02:00:00Z
bytedcli --json nvqos rootcause analyze --region sg --body-file /tmp/nvqos-rootcause-body.json
```
