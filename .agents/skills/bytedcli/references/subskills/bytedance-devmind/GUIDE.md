---
name: bytedance-devmind
description: "Operate Bits DevMind / DataMind via bytedcli: doctor auth (ByteCloud JWT + Auth-Code), list/search metric stories, get complex metric detail and dimensions, query values through data_mart, and inspect the curated 「开发人员AI使用分析」 builtin catalog (tool-ratios 分项贡献率). Use when tasks mention DevMind, DataMind, Bits 数据洞察, metric story, insight metrics, report-line metrics, AI contribution rate, 工具贡献率, or bits.bytedance.net datamind/report pages."
---

# bytedcli DevMind

Use this skill when the task mentions DevMind / DataMind / Bits 数据洞察 / metric story / AI 贡献率 / 工具贡献率，或用户给出 `bits.bytedance.net` 的指标/报告链接并要求取数。

## How To Call

Use `bytedcli` directly. For machine-readable output, put `-j` before the domain:

```bash
bytedcli -j devmind <command> [options]
```

When parameters are unclear, inspect help instead of guessing:

```bash
bytedcli devmind --help
bytedcli devmind metric --help
bytedcli devmind query --help
```

## When To Use

- Search metric stories by report node or keyword with `devmind story list`.
- Inspect metric formula details and available dimensions.
- Resolve dimension/metric alias ids to display names and definitions with `devmind meta --alias`.
- Resolve usernames to real names and departments with `devmind user get --username`.
- Explore the report/business space tree to find node ids with `devmind space tree`.
- List the reports visible to you, with the template ids `dashboard get` needs, via `devmind report list`.
- Browse the underlying data models with `devmind model list`, inspect one with `devmind model get`, and check how fresh its data is with `devmind model partition get`.
- List what a model can be grouped or filtered by, with the operators each accepts, via `devmind model dimension list`; see a dimension's actual values with `devmind model dimension values`; list the model's own metric definitions with `devmind model metric list`.
- List the charts configured on a dashboard (chart ids, names, dimension/metric alias ids) with `devmind dashboard get --template-id`.
- List a metric's group / drill-down dimensions with `devmind drill dimensions`, then pull commit-level detail with `devmind drill get`.
- Query metric values by time range, report line, person, day/week, or commit grouping.
- Pull the curated 「开发人员AI使用分析」 metrics directly (no node-id needed) via `devmind builtin`, or compare which tool bucket is recognized via `builtin tool-ratio list`.
- Troubleshoot DevMind authentication or empty query results.

## Quick Start

```bash
# 1) Auth health check. This never prints JWT or Auth-Code.
bytedcli -j auth status
bytedcli -j devmind doctor
bytedcli -j devmind doctor --node-id <node-id>

# 2) Inspect a node (path, depth, liaison officers). metric list can also
#    derive node_path from --node-id automatically, so this is optional.
bytedcli -j devmind node get --node-id <node-id>

# 2b) No node id yet? Search by name. Hits carry a usable nodePath, which
#     node get omits for employee nodes.
bytedcli -j devmind node search --keyword <name>
bytedcli -j devmind node search --keyword <business> --space-type business
bytedcli -j devmind model list --keyword <name>
bytedcli -j devmind model partition get --model-id <model-id>
bytedcli -j devmind model dimension list --model-id <model-id> --keyword <name>

# 3) Find metrics.
bytedcli -j devmind metric list --node-id <node-id> --keyword "AI贡献率"

# 4) Inspect metric detail and dimensions.
bytedcli -j devmind metric get --metric-id <metric-id> --node-id <node-id>

# 4b) Query one metric's data directly (trend, or grouped sheet with --group-dim).
bytedcli -j devmind metric query \
  --metric-id <metric-id> --node-id <node-id> \
  --member <username> --start '<start>' --end '<end>' --granularity quarter

# 5) Preview, then query.
bytedcli -j devmind query --dry-run \
  --metric-id <metric-id> --node-id <node-id> \
  --start '<start>' --end '<end>' \
  --report-filter <report-filter> --group-by person

bytedcli -j devmind query \
  --metric-id <metric-id> --node-id <node-id> \
  --start '<start>' --end '<end>' \
  --report-filter <report-filter> --group-by person
```

Examples use placeholders such as `<node-id>`, `<metric-id>`, `<start>`, `<end>`, and `<report-filter>`; do not invent real production IDs. Time values look like `YYYY-MM-DD HH:mm:ss`.

## Recommended Workflow

1. Confirm login with `bytedcli -j auth status`; if needed, run `bytedcli auth login`.
2. Run `bytedcli -j devmind doctor`, adding `--node-id` when a target report node is known.
3. Optionally run `node get --node-id` to inspect a node's path/depth/officers; `metric list` derives `node_path` from `--node-id` on its own when omitted. Without a node id, run `node search --keyword` to find one by name (`--space-type business` searches the business tree instead of people).
4. Use `metric list` to find the metric id.
5. Use `metric get` to verify dimensions, especially `时间`, `汇报线`, and `人员`; resolve unknown alias ids via `meta --alias`.
6. Run `query --dry-run` to inspect the payload.
7. Run `query` and analyze the JSON locally.

## Agent Guidance

- Call DevMind queries sequentially by default.
- Use bytedcli auth only. Do not copy browser cookies or print `x-jwt-token` / `Auth-Code`.
- `--report-filter` is usually a username-style filter value, not the Chinese report-line display name.
- Use `devmind user get --username <name,name>` to look up the real name or department behind a username-style filter value.
- The default query builder depends on common dimensions named `时间`, `汇报线`, and `人员`. If a metric uses different dimensions, use `--payload-file`.
- Write custom payload drafts outside the repository, for example `/tmp/devmind-query.json`.
- v1 is read-only. Creation or update requests are out of scope.

## References

- `references/commands.md` — command cheat sheet
- `references/workflow.md` — recommended workflow
- `references/auth.md` — auth details
- `../../troubleshooting.md` — common failure modes
