# DevMind Workflow

1. Check auth:

```bash
bytedcli -j auth status
bytedcli -j devmind doctor
```

2. Optionally inspect a node (path, depth, liaison officers). `metric list` derives `node_path` from `--node-id` automatically, so this step is optional:

```bash
bytedcli -j devmind node get --node-id <node-id>
```

Without a node id to start from, search by name instead. Every hit carries a `nodePath`, including for employee nodes where `node get` answers `null`:

```bash
bytedcli -j devmind node search --keyword <name>
bytedcli -j devmind node search --keyword <business> --space-type business
```

To work from the data models behind `data_mart` instead of a report node, browse the
catalog and check how fresh a model's data is before querying it. Partition freshness is
an upper bound only -- there is no matching lower bound, and most models are not
partitioned at all:

```bash
bytedcli -j devmind model list --keyword <name>
bytedcli -j devmind model get --model-id <model-id>
bytedcli -j devmind model partition get --model-id <model-id>
```

Then look inside the model. The dimension list is what a filter can be written against
-- it reports the operators each dimension accepts -- and the value lookup answers what
to compare them to. The metric list is the model's own metric definitions, which are a
different thing from the report-node metrics `metric list` returns:

```bash
bytedcli -j devmind model dimension list --model-id <model-id> --keyword <name>
bytedcli -j devmind model dimension values --model-id <model-id> --dimension-id <dimension-id>
bytedcli -j devmind model metric list --model-id <model-id>
```

3. Resolve metrics for a report node:

```bash
bytedcli -j devmind metric list --node-id <node-id> --keyword <keyword>
```

4. Inspect the selected metric:

```bash
bytedcli -j devmind metric get --metric-id <metric-id> --node-id <node-id>
```

Confirm the metric has common dimensions named `时间`, `汇报线`, and `人员` before using the default query builder.

5. Preview the payload:

```bash
bytedcli -j devmind query --dry-run \
  --metric-id <metric-id> --node-id <node-id> \
  --start '<start>' --end '<end>' \
  --report-filter <report-filter> --group-by week-person
```

6. Execute the query:

```bash
bytedcli -j devmind query \
  --metric-id <metric-id> --node-id <node-id> \
  --start '<start>' --end '<end>' \
  --report-filter <report-filter> --group-by week-person
```

Use `--payload-file` only when the default builder cannot represent the desired dimensions or filters.

For a lighter one-metric read, `metric query` posts to the upgrade/query endpoint directly — no report-filter or payload builder needed. Without `--group-dim` it returns a trend (`chart_data`); with one or more group dimension ids it returns a grouped sheet (`metric_sheet_data`):

```bash
bytedcli -j devmind metric query \
  --metric-id <metric-id> --node-id <node-id> \
  --member <username>,<username> \
  --start '<start>' --end '<end>' --granularity quarter
# add --group-dim <dim-id> for a grouped sheet instead of the trend
```

`--node-path` is derived from `--node-id` when omitted; `--member` fills `report_tree`/`business_tree` per `--space-type`; `--granularity` takes full words (`day|week|month|quarter|year`).

7. Resolve opaque dimension/metric alias ids from query or drill-down output:

```bash
bytedcli -j devmind meta --alias <id>,<id>
```

Each id is looked up as both a dimension and a metric alias; unknown ids come back with `type: "unknown"`.

8. Resolve username-style filter values to real names and departments:

```bash
bytedcli -j devmind user get --username <name>,<name>
```

Unknown usernames still return an entry with `name`/`enName`/`deptName` set to `null`.

9. Explore the report/business space tree when you need to discover node ids:

```bash
bytedcli -j devmind space tree --space-type report
```

Returns a nested tree with node ids; use `--space-type business` for the business space.

10. Drill down to commit-level detail. First list the metric's drill-down dimensions, then pull the detail rows:

```bash
bytedcli -j devmind drill dimensions --metric-id <metric-id> --node-path <node-path>

bytedcli -j devmind drill get \
  --metric-id <metric-id> --alias-id <metric-alias-id> \
  --node-id <node-id> --node-path <node-path> \
  --member <username> --start '<start>' --end '<end>' \
  --group-dim <person-dim-id>
```

For a composite metric, `--alias-id` must be the real `metric_alias_id` (discover it from a base `query`'s series, it is not the metric id) and `--group-dim` should be a person dimension id; without them the platform 500s. For an atomic metric pass `--from-type meta_metric` (its alias id equals the metric id). `--node-path` is derived from `--node-id` when omitted. `--granularity` takes full words (`day|week|month|quarter|year`), default `quarter`.

11. Inspect a dashboard's configuration — list every chart with its dimensions and metric alias ids:

```bash
bytedcli -j devmind dashboard get --template-id <template-id> --node-id <node-id>
```

`--template-id` alone decides which dashboard is returned. `--node-id` is required by the endpoint (it 400s without one), but any report node/project id you can access works and does not change the result — discover one via `space tree` or `node get`. Resolve the returned `groupAliasIds`/`metricAliasIds` to display names with `meta --alias`.
