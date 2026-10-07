---
name: bytedance-maya
description: "读取 Maya BI dashboard 的 chart、业务方向和 metric ID，并从线上 dashboard 配置重建 chart query 取数。Use when tasks mention Maya, maya.tiktok-row.net, 各方向周均指标, dashboard detail, chart query, 业务方向指标, or Maya metric IDs."
---

# bytedcli Maya

## Capabilities

- 从 Maya dashboard 发现 sheet、chart、业务方向和指标 ID。
- 根据业务方向名称筛选 chart 中的指标集合。
- 复用线上 dashboard 保存的完整 query 配置取数，避免手工维护大型 payload。
- 在不打开浏览器的情况下，按国家和日期重放 Maya chart 查询。

## Authentication

Maya 复用 `bytedance` BDSSO browser session。首次使用或登录过期时运行：

```bash
bytedcli --site cn auth login --session
```

不要把浏览器 Cookie、`sso_session` 或 dashboard owner 信息写入命令、日志和分析文档。

## Workflow

先读取 dashboard catalog，确认 chart 与业务方向，再查询 chart。不要猜 chart ID 或 metric ID。

```bash
bytedcli --json maya dashboard get --dashboard-id demo-dashboard-id
bytedcli --json maya dashboard get --dashboard-id demo-dashboard-id --group-name "Traffic"
```

`dashboard get` 返回：

- `dashboard_id`、`dashboard_name`、`project_id`
- sheet 与 chart ID/name
- 每个 chart 的 metric group ID/name
- group 下的 metric unique ID、展示名、原始 field ID/name 和 dataset ID

确认目标 chart 后取数：

```bash
bytedcli --json maya chart get \
  --dashboard-id demo-dashboard-id \
  --chart-id demo-chart-id \
  --group-name "Traffic"
```

按国家和日期覆盖 dashboard 当前筛选：

```bash
bytedcli --json maya chart get \
  --dashboard-id demo-dashboard-id \
  --chart-id demo-chart-id \
  --group-name "Traffic" \
  --country US \
  --start 2026-07-20 \
  --end 2026-07-20
```

## Query semantics

- `chart get` 先实时调用 `dashboard/detail`，再从目标 chart 的 `query_params` 构造 `platform/query` 请求。
- `--group-name` / `--group-id` 只保留该 group 的 `metric_uniq_id_list` 对应指标。
- `--country` 会覆盖 chart 中所有 country filter；多个国家用逗号分隔。
- 日期必须同时提供 `--start` 与 `--end`，格式为 `YYYY-MM-DD`，按 Maya API 要求的 UTC 自然日边界转换。若线上 chart 使用 selected-day selector，两者必须是同一天；趋势周期由 chart 的保存配置派生。
- `applied_filters` 明确返回最终国家和日期筛选的来源与解析状态；不要把缺失的 CLI override 误读为线上 dashboard 未应用筛选。
- 返回的每一行保留 Maya 原始字段，并补充 `metric_unique_id` 与 `metric_name`。
- 如果 chart 没有 country filter，CLI 会报错，不会静默返回未筛选数据。

## Boundaries

- 当前能力只读，不修改 dashboard、chart 或 dataset。
- 不在源码、Skill 或自动化中硬编码真实 dashboard/chart/metric ID；这些值属于线上配置，应通过 `dashboard get` 实时发现。
- 查询失败或空结果不能证明指标不存在；先检查 dashboard 是否更新、chart/group 是否选对，以及 BDSSO 是否有效。

## References

- 调用、认证和输出约定：[`references/maya-invocation.md`](references/maya-invocation.md)
- 常见失败与停止条件：[`references/maya-troubleshooting.md`](references/maya-troubleshooting.md)
