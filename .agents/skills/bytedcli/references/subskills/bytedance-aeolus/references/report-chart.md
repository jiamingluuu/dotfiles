# Report / Chart commands

Router: this skill's SKILL.md (named GUIDE.md in the bytedcli mirror). This file is the command body for report, chart, style, dimMet, and report-side filters. Do not treat [aeolus.md](aeolus.md) as command body.

Examples using `$AEOLUS_REPORT_URL` expect the caller to export the actual user-provided URL. Do not replace them with fabricated hosts or commit real resource IDs into docs.

Physical-table SQL and `aeolus query` fallback live in [dataset.md](dataset.md). Dashboard sheet/filter/update live in [dashboard.md](dashboard.md).

Set the `$AEOLUS_*_ID` variables used below from the target resource or the corresponding list/get output. Numeric IDs and field names inside JSON examples are placeholders to replace with actual resource and field metadata.

## Table of contents

- [Recommended workflow for report/dataQuery links](#recommended-workflow-for-reportdataquery-links)
- [Failure signatures (report / query)](#failure-signatures-report--query)
- [resolve-report](#resolve-report)
- [aeolus report resolve](#aeolus-report-resolve)
- [aeolus report query](#aeolus-report-query)
- [aeolus report download](#aeolus-report-download)
- [chart get / chart query](#chart-get--chart-query)
- [report filters / filter options (report-side)](#report-filters--filter-options-report-side)
- [aeolus report create](#aeolus-report-create)
- [aeolus report style get / aeolus report style update](#aeolus-report-style-get--aeolus-report-style-update)
- [aeolus report update](#aeolus-report-update)

## Recommended workflow for report/dataQuery links

If `chart get` already returned the dimMet list or `display.conf` you need, **do not** run `report resolve`.

1. Prefer `chart get` when you have a chart/report id and only need metadata, Simple DSL, or style.
2. Use `resolve-report` only to map a dataQuery/dashboard URL to dataset IDs (batch discovery / access-request).
3. Use `report resolve` when you have a single dataQuery URL and need saved `reqJson` / full dimMet (and `chart get` did not already provide it).
4. Use `report filters` before writing repeatable `--filter` on `report query` / `report download`.
5. Use `report query` / `chart query` for bounded preview rows; use `report download` for CSV/XLSX file export.
6. If you need dataset SQL / physical-table discovery, stop and read [dataset.md](dataset.md).

### Failure signatures (report / query)

- `report query --format sql` still issues a real VizQuery. There is no compile-only endpoint.
- Preview output with `truncated:true` means use `report download` (or `dashboard download`), not a larger `--limit`.
- `aeolus/unknown` on report/scratch VizQuery: add `--data-source-id` from a browser payload or model info; most datasets work without it.
- `roleType must be 0 (dim) or 1 (metric)`: Aeolus page JSON uses `1=维度、2=指标`; CLI `viz-query` / `--dim-met` uses `0=维度、1=指标`. Convert before reuse.
- Dataset logical-SQL failures (`unknownTable`, `dummy`, `unknownIdentifier`) belong to [dataset.md](dataset.md), not this file.

---

### resolve-report

Resolve report and dataset references from Aeolus URLs.

```bash
bytedcli aeolus resolve-report [options]
```

**Options:**

- `-r, --region <region>` - Region: cn, sg, va, euttp, euttp2, eupipo, mycis, jplark, mybd, sglark, uspipo, usttpusts, usbd (required when URL cannot infer region)
- `--url <aeolusUrl>` - Aeolus URL (`dataQuery` or `dashboard`)
- `--app-id <appId>` - App ID (when not using URL)
- `--report-id <reportId>` - Report ID (when not using URL)
- `--json` is a global option and must appear before `aeolus`

**Examples:**

```bash
# Resolve from dataQuery URL
bytedcli aeolus resolve-report --url "$AEOLUS_REPORT_URL"

# Resolve from dashboard URL
bytedcli aeolus resolve-report --url "$AEOLUS_DASHBOARD_URL"

# Resolve from dashboard URL without sheetId (falls back to current/default sheet)
bytedcli aeolus resolve-report --url "$AEOLUS_DASHBOARD_URL"
```

**Output:**

- `dataQuery` URL: report IDs and resolved dataset IDs
- `dashboard` URL: report IDs, resolved dataset IDs, plus
  - `dashboardName`, `dashboardOwnerEmailPrefix`, `dashboardRoleList[]`
  - `sheets[]`: `sheetId`, `name`, `sheetOrder`, `visible`, `reportIds`
  - `reports[]`: `reportId`, `name`, `displayType`, `ownerEmailPrefix`, `statusCode`, `updatedAt`, `datasetIds`


---

### `aeolus report resolve`

Resolve an Aeolus dataQuery URL to report metadata and the full dimMet list (dimensions + metrics). Useful as a first step before `report query` when you have a browser URL but need the underlying dataset structure.

```bash
# Resolve from a dataQuery URL (region auto-detected from URL)
bytedcli aeolus report resolve --url "$AEOLUS_REPORT_URL"

# Resolve without URL (requires --region and --report-id)
bytedcli aeolus report resolve -r va --report-id <REPORT_ID>
```

Agent Guidance:

- `aeolus report resolve` fetches the report detail and enriches it with the dataset's full dimMet list (dimensions + metrics with IDs, names, expressions, and partition flags). Used to discover the saved query config (dimMet IDs, reqJson) for a single dataQuery URL — typically as input to `report query`.
- The flat `aeolus resolve-report` command serves a different intent: it resolves dashboard or dataQuery URLs to dataset IDs, intended for batch dataset discovery and access-request workflows. Prefer `report resolve` when you have a single dataQuery URL and want the saved query config; prefer `resolve-report` when you have a dashboard URL or only need dataset IDs.
- If the report has an associated dataset, the dimMet list is fetched automatically; a dimMet fetch failure is non-fatal and the report metadata is still returned.
- Saved reports store their dimMet selection in two shapes, and `report resolve` exposes it as `dimMetConfig` in the JSON output when the report has one: inline entry objects land in `dimMetConfig.dimMetMap`, ID-only selections land in `dimMetConfig.dimMetIdsByDataset` (e.g. `{"<datasetId>": [1700059025281, ...]}`). When `dimMetConfig` is present, both maps are present (the unused shape is an empty object). For the ID-list shape, resolve each ID against the `dimensions` / `metrics` arrays in the same output (or `dataset-fields`). The API may return `displayType: null` for saved dataQuery reports; the CLI normalizes that to an omitted field (`reportDisplayType` absent from JSON output).

---

### `aeolus report query`

Execute a saved Aeolus report and output rows (`--format data`, default) or the underlying ClickHouse SQL (`--format sql`). When `--url` is provided, the report's saved dimMet and where clauses are auto-resolved; otherwise specify `--dim-met` explicitly.

```bash
# Fetch data from a saved report URL (auto-resolves config)
bytedcli aeolus report query --url "$AEOLUS_REPORT_URL"

# Rebuild a scratch query from a URL using dataset field names
bytedcli aeolus report query --url "$AEOLUS_REPORT_URL" \
  --group-by "country,platform" --metrics "revenue" \
  --filter "p_date[lastSync]=1" --top-n 10 --sort-by "revenue"

# Fetch data with explicit parameters
bytedcli aeolus report query -r va --app-id <APP_ID> --dataset-id <DATASET_ID> \
  --dim-met '{"dimMetId":101,"name":"app_id","expr":"`app_id`","roleType":0}' \
  --limit 50

# Fetch with a where filter
bytedcli aeolus report query -r va --app-id <APP_ID> --dataset-id <DATASET_ID> \
  --dim-met '{"dimMetId":101,"name":"app_id","expr":"`app_id`","roleType":0}' \
  --where '{"dimMetId":102,"name":"partition_date","op":"lastSync","val":[1],"valOption":{"datetimeUnit":"day","anchorOffset":0}}'

# Get the underlying SQL (still issues a real query against Aeolus)
bytedcli aeolus report query --format sql --url "$AEOLUS_REPORT_URL"
```

**Options:**

- `--url <aeolusUrl>` — Aeolus dataQuery URL (auto-resolves report config)
- `-r, --region <region>` — Region (required when `--url` is not provided)
- `--app-id <appId>` — Aeolus app ID (required without `--url`)
- `--dataset-id <datasetId>` — Aeolus dataset ID (required without `--url`)
- `--report-id <reportId>` — Aeolus report ID for auto-resolving dimMet config
- `--dim-met <json>` — One dimension/metric entry, repeatable (required without `--url`)
- `--where <json>` — One filter entry, repeatable
- `--group-by <fields>` — Build a scratch DataQuery grouped by dataset field name/id; comma-separated and repeatable
- `--metrics <fields>` — Build scratch query metrics by dataset field name/id; comma-separated. Supports `sum(field)`, `count(field)`, `avg(field)` and bare metric names (bare raw numeric metrics default to `sum(`)
- `--filter <expr>` — Named filter, repeatable. Form: `field=value`, `field[op]=value`, or `stat_date[thisWeek]`. Date: `last` / `last:week` / `lastSync` / `thisWeek`. Compare: `contains` / `not_in` / `is_null`. Result: `field[having:>]=100` or `avg(field)[>]=100`
- `--filter-id <expr>` — Field-id filter, repeatable. Form: `123=value1,value2` or `123[op]=value`
- `--data-source-id <id>` — Override `query.dataSourceId` for report query / scratch VizQuery when the backend requires the browser payload's dataSourceId
- `--top-n <N>` — Apply server-side Top N to the sort field
- `--sort-by <field>` / `--sort-order <asc|desc>` — Sort field name/id and order for scratch query / Top N
- `--drill-down <fields>` — Append extra groupBy fields for a follow-up/drill-down scratch query; comma-separated and repeatable
- `--limit <N>` — Row limit (default 100)
- `--timeout-ms <ms>` — Request timeout in milliseconds
- `--format <fmt>` — `data` (default) returns rows; `sql` returns the generated ClickHouse SQL extracted from the response. **Note:** `--format sql` still issues a real VizQuery request — there is no compile-only endpoint.

Agent Guidance:

- When `--url` or `--report-id` resolves saved configuration (`reqJson`), it is used as the base request body. Explicit `--where` filters replace saved filters for the same `dimMetId`/`id` (falling back to `name`) and append new fields, while unrelated saved filters remain intact.
- `report query` and `viz-query` are bounded preview/query commands. Use `aeolus report download` when the user asks for a CSV/XLSX file export without a large stdout payload.


**Options (`report download`):**

- `--url <aeolusUrl>` - Aeolus dataQuery URL. Region, `rid`, and `id` are inferred from the URL when present.
- `-r, --region <region>` - Region; defaults to `cn` when `--url` is not provided.
- `--report-id <reportId>` - Saved report/chart id (`rid`).
- `--history-id <historyId>` - Query history id (`id`).
- `--filter <expr>` - Named filter, repeatable. Form: `field=value`, `field[op]=value`, or `stat_date[thisWeek]`. Same date / compare / HAVING syntax as `report query`.
- `--filter-id <expr>` - Field-id filter, repeatable. Form: `123=value1,value2` or `123[op]=value`.
- `--limit <N>` - Export row limit. Default is `1000000`; pivot/trend table XLSX downloads are capped at an effective `rowLimit` of `50000`.
- `--output <file>` - Destination CSV/XLSX file. The command writes through a temporary sibling file and atomically replaces the destination after the response is complete.
- An extensionless output path works for every report type. If an extension is used, choose `.csv` for ordinary table/chart reports and `.xlsx` for pivot/trend table reports; mismatched extensions are rejected.
- `--timeout-ms <ms>` - Download request timeout in milliseconds.

**Notes:**

- With `--url` / `--report-id`, saved `reqJson` is reused unless a scratch shape is requested.
- `--filter` / `--filter-id` can be used with saved `reqJson`; they are resolved through the dataset field list and merged into saved filters.
- `--group-by`, `--metrics`, and `--drill-down` rebuild a scratch VizQuery from the resolved dataset. Use them when the URL should be queried at a different grain or with a different metric set.
- `--top-n` / `--sort-by` can be used either with saved config or scratch config. When not rebuilding scratch, pass both `--top-n` and `--sort-by`.
- Most datasets work without `--data-source-id`; add it only when Aeolus returns `aeolus/unknown` and a browser payload or model info shows the required `dataSourceId`.
- `--format sql` extracts `sqlList` from the response, but it is not compile-only; Aeolus still executes the query.
- `report query` and `viz-query` return bounded query results. `report download` uses the Aeolus VizQuery download endpoint for file exports and emits only metadata such as `output`, `sizeBytes`, `queryHistoryId`, format, `rowLimit`, `rowCount`, `limitReached`, and `completeness`.
- CSV `rowCount` excludes the header row. XLSX `rowCount` is `null`; `limitReached` is `"unknown"` and `completeness` is `"unknown"` because bytedcli does not parse workbook contents.

---

### `aeolus report download`

Download a saved report or query-history result to `--output` using the Aeolus VizQuery download flow. The command accepts a dataQuery URL (`rid` and/or `id` are auto-parsed), `--report-id` / `--chart-id`, or `--history-id`.

```bash
bytedcli aeolus report download --url "$AEOLUS_REPORT_URL" --output ./report-export
bytedcli aeolus report download -r va --history-id 789012 --limit 1000000 --output ./history-export
bytedcli aeolus report download --url "$AEOLUS_REPORT_URL" --filter "country=SG,US" --output ./filtered-export
```

Agent Guidance:

- This is the file-export path. It writes through a sibling temporary file and atomically replaces `--output` after the file response is fully received.
- Do not use this command to preview rows. It intentionally emits only metadata (`output`, `sizeBytes`, `queryHistoryId`, format, `rowLimit`, `rowCount`, `limitReached`, `completeness`) and never prints the downloaded report payload to stdout.
- `--report-id` and `--chart-id` are the same Aeolus `rid` selector; prefer `--report-id` in examples.
- `--limit` defaults to `1000000`; pivot/trend table XLSX downloads are capped at an effective `rowLimit` of `50000`.
- `--filter` / `--filter-id` can be used with saved configuration; they are resolved through the dataset field list and merged into the saved where list.
- CSV `rowCount` excludes the header row. XLSX `rowCount` is `null`; `limitReached` is `"unknown"` and `completeness` is `"unknown"` because the CLI does not parse workbook contents.
- Uses the same VizQuery API as `aeolus viz-query`, so Titan Passport cookie auth applies.

---

### chart get / chart query

Use `aeolus chart get` to read one chart/report's metadata and Simple DSL. Use `aeolus chart query` to preview rows from an online chart ID or from a local temporary chart JSON object.

```bash
# Read chart metadata and Simple DSL
bytedcli aeolus chart get -r va --chart-id 123456

# Include generated SQL; this runs one bounded VizQuery and returns SQL best-effort
bytedcli --json aeolus chart get -r sg --chart-id 123456 --include-sql

# Preview rows from an online chart
bytedcli aeolus chart query -r va --chart-id 123456 --limit 20

# Query with dashboard/sheet context and runtime filters
bytedcli aeolus chart query -r va --chart-id 123456 --dashboard-id 789012 --sheet-id 345678 --filter "country=SG"

# Query a local temporary chart JSON inline
bytedcli aeolus chart query -r va --chart-json-file ./chart.json

# Explain filter merge only; no chart query request is made
bytedcli aeolus chart query -r va --chart-id 123456 --dashboard-id 789012 --sheet-id 345678 --filter "country=SG" --explain-filters
```

**Options (`chart get`):**

- `-r, --region <region>` - Region; defaults to `sg`.
- `--chart-id <chartId>` - Aeolus chart/report id (`rid`).
- `--include-sql` - Execute a bounded VizQuery and return generated SQL best-effort.

**Options (`chart query`):**

- `-r, --region <region>` - Region; defaults to `sg`.
- `--chart-id <chartId>` - Online Aeolus chart/report id (`rid`).
- `--chart-json-file <path>` - Local chart JSON object. Mutually exclusive with `--chart-id`; sent inline and never saved.
- `--dashboard-id <dashboardId>` / `--sheet-id <sheetId>` - Optional dashboard context for permission and sheet filter behavior.
- `--filter <expr>` - Named runtime filter, repeatable. Form: `field=value`, `field[op]=value`, or `stat_date[thisWeek]`. Same date / compare / HAVING syntax as `report query`.
- `--filter-id <expr>` - Field-id runtime filter, repeatable. Form: `123=value1,value2` or `123[op]=value`.
- `--where <json>` - Explicit runtime filter entry, repeatable.
- `--filters-json <json>` - Advanced runtime filter array forwarded as `effectiveFilters`.
- `--explain-filters` - Explain runtime/sheet/chart filter merge and exit before any chart query request.
- `--limit <N>` - Preview row limit. Output is capped at 100 rows.
- `--timeout-ms <ms>` - Request timeout in milliseconds.

**Notes:**

- `--chart-json-file` is read-only. bytedcli sends the parsed JSON to the chart query endpoint and does not call report save/update APIs.
- `--explain-filters` reads metadata/context and makes no real chart query request.
- `chart query` is a preview command. JSON output includes `rowCount`, `returnedRows`, `limit`, `truncated`, `completeness`, and `downloadGuidance`; when truncated, use `report download` or `dashboard download` for file exports.
- `chart get --include-sql` is intentionally not metadata-only. It reads `sqlList` first, falls back to query-history SQL, and may return `sql: null` with `sqlWarning` while metadata retrieval still succeeds.


Agent Guidance:

- `chart query --chart-json-file` sends the JSON object inline to the read-only chart query API. It never calls report save/update APIs and must not be used to mutate an online asset.
- `--explain-filters` is a no-query mode. It reads chart/report metadata and optional dashboard context, then explains runtime overrides, sheet/dashboard filters, and chart filters in merge order.
- Preview rows are capped at 100 even if `--limit` is larger. When output has `truncated:true`, use `aeolus report download` or `aeolus dashboard download` for CSV/XLSX file export.
- `--include-sql` on `chart get` is not metadata-only: it executes a bounded VizQuery, uses `sqlList` when returned, and falls back to query-history SQL. SQL extraction is best-effort; inspect `sql` and `sqlWarning`.

---

### report filters / filter options (report-side)

Use these read-only commands to discover valid filter names, dimMet IDs, default values, and option values before using repeatable `--filter` on `report query` or `report download`. Dashboard-scoped discovery is in [dashboard.md](dashboard.md).

```bash
# Discover filters from a saved dataQuery/report URL
bytedcli --json aeolus report filters --url "$AEOLUS_REPORT_URL"

# List selectable option values for a filter dimMetId
bytedcli --json aeolus filter options -r va --dataset-id <datasetId> --filter-id <dimMetId> --keyword demo
```

Agent Guidance:

- `report filters` groups `report_level`, `chart_schema`, and `dataset_field` filters. `dashboard filters` groups `dashboard_public`, `report_level`, and `chart_schema` filters.
- Each filter item includes `name`, `dimMetId`, `op`, `defaultValue`, `source`, `overridable`, and dataset/report context. Prefer `name` for repeatable `--filter`; use `dimMetId` with `--filter-id` when names are ambiguous.
- Repeatable filter syntax is `--filter "field=value"` or `--filter "field[op]=value1,value2"`. Examples: `--filter "country=SG"` and `--filter "p_date[lastSync]=1"`.
- Date shortcuts (confirmed on VQS): `--filter "stat_date[last]=14"` is the last 14 calendar days excluding today; `--filter "stat_date[thisWeek]"` / `[thisMonth]` / `[thisYear]` / `[lastWeek]` / `[lastMonth]` / `[lastQuarter]`; `--filter "stat_date[last:week]=2"` is the last two completed weeks. `lastSync` is only for partition fields.
- Compare aliases: `not_in`, `contains`, `starts_with`, `ends_with`, `is_null`, `is_empty`, `gt`/`gte`/`lt`/`lte`. Result/HAVING on a metric: `--filter "amount[having:>]=100"` or `--filter "avg(amount)[>]=100"`.
- `filter options` calls the Aeolus option-suggest endpoint for a dataset field. Use `--keyword` to narrow values; optional `--dashboard-id`, `--sheet-id`, and `--report-id` pass UI context when option values depend on dashboard/report state.


**Output:**

- `groups[]` — grouped filter descriptors.
- Each descriptor includes `name`, `dimMetId`, `op`, `defaultValue`, `source`, `overridable`, `dataSetId`, and optional report/chart context.
- `filter options` returns stable `options[]` entries with normalized `label` and `value`; backend-specific raw fields are not exposed.

**Repeatable filter syntax:**

- `--filter "field=value"` — equality for one value, `in` for comma-separated values.
- `--filter "field[op]=value1,value2"` — explicit operator such as `last`, `lastSync`, `in`, `not_in`, `contains`, `starts_with`, `is_null`, `gt`, or `>=`.
- Date shortcuts: `--filter "stat_date[last]=14"`, `--filter "stat_date[thisWeek]"`, `--filter "stat_date[last:week]=2"`. `lastSync` is only for partition fields.
- Result/HAVING: `--filter "amount[having:>]=100"` or `--filter "avg(amount)[>]=100"`.
- Prefer `--filter` by field name. Use `--filter-id "123=value"` when names are ambiguous and you already have the `dimMetId`.

---

### `aeolus report create`

Use `aeolus report create` when the user needs an openable/shareable Aeolus page, not just a one-off query result. The legacy flat alias `aeolus save-viz-query` still works but is hidden from help.

Typical cases:

- Turn a verified `viz-query` into a saved report page
- Share "yesterday users", "distinct app_id list", or a simple aggregate result
- Produce a visual page link for `hrbi_mycis`, where Query Editor is unavailable

Examples:

```bash
# Save a grouped page (yesterday distinct categories)
bytedcli aeolus report create \
  -r hrbi_mycis --app-id "$AEOLUS_APP_ID" --dataset-id "$AEOLUS_DATASET_ID" \
  --name "yesterday-categories" \
  --dim-met '{"dimMetId":101,"name":"category","expr":"`category`","roleType":0}' \
  --where '{"dimMetId":102,"name":"pdate","op":"lastSync","val":[1],"valOption":{"datetimeUnit":"day","anchorOffset":0}}'

# Save an aggregate page (yesterday row count)
bytedcli aeolus report create \
  -r hrbi_mycis --app-id "$AEOLUS_APP_ID" --dataset-id "$AEOLUS_DATASET_ID" \
  --name "yesterday-count" \
  --dim-met '{"dimMetId":102,"name":"pdate","expr":"`pdate`","roleType":1,"aggregation":"count("}' \
  --where '{"dimMetId":102,"name":"pdate","op":"lastSync","val":[1],"valOption":{"datetimeUnit":"day","anchorOffset":0}}'
```

Agent Guidance:

- `aeolus report create` calls `POST /aeolus/api/v3/dataMart/report`, and shareable links use `/aeolus/pages/dataQuery?...&rid=<reportId>&sid=<datasetId>`.
- `hrbi_mycis` defaults to `dataSourceId=10035`; other regions require explicit `--data-source-id` when no built-in mapping exists.
- Save responses may return `data.reportId`, `data.id`, or `data.lastInsertId` with `code=0`.
- Before `POST`/`PUT`, the CLI executes the final saved `reqJson` as a one-row VizQuery preflight.
  A query/schema/filter failure aborts without saving, so a success result means the returned page
  configuration was accepted by the same VQS path used by DataQuery.
- Aggregate payloads should stay on the normal aggregate path: use IDs like `count_<dimMetId>`, keep `sourceType: "aggr"`, set `realMetricTableRouteConfig.isRealMetricQuery = false`, and do not emit `real_metrics_*` / `metricConf`.
- To avoid page-side query errors, keep browser-parity metadata such as `query.dimMetList`, `schema.customConfig.fields.details=[]`, `originalSchema`, `requestId`, and `locale: "zh_CN"`.
- If the browser save payload is already available, prefer reusing it directly; otherwise keep the CLI-generated payload as close to browser shape as possible.
- `--table-calc` writes `schema.tableCalculation` on `report create` / `report update`. Types: `percentOfTotal`, `difference`, `percentDifferenceFrom`, `runningTotal`, `rank`, `percentile`, `movingCalculation`. Example: `--table-calc percentOfTotal` or `--table-calc amount=rank`.
- `--mini-chart` writes `display.conf.miniChart.enabled=true` on create/update.
- `--period-compare` writes `schema.periodCompare` plus derived `sourceType: "period_compare"` measures. Types: `relativeRatio` (aliases `wow` / `relative`), `lastyearRatio` (`yoy`), `lastweekRatio`, `lastmonthRatio`. Return types: `ratio`, `store`, `value`, `diff`, `store_ratio`, `reversed_store_ratio`. Examples: `--period-compare relativeRatio`, `--period-compare lastyearRatio=ratio`, `--period-compare '{"periodType":"relativeRatio","retType":"diff","field":"amount"}'`. A type is required. The default shift is the first date/datetime dimension; if none exists, pass `shift`. Derived measure names look like `amount_relativeRatio_ratio`; ids look like `table_<dateId>_1d_<measureId>_<retType>`. Do not write `query.periodCompare`. This only applies to `schema.measures`, not `double_axis` `subMeasures`.
- `--totals` writes `query.calculation.combined`. Default is row totals. Also: `--totals col`, `--totals row,col`, `--totals '{"row":true,"col":false}'`.
- `--forecast` writes `schema.forecast` with `granularity:"day"`. Default is 7 days: `--forecast`, `--forecast 7`, `--forecast 7d`, or `--forecast '{"step":7,"granularity":"day"}'`. The default time pill is the first date/datetime dimension. Do not write `query.forecast`. Week/month forecast is not accepted. CN console may hide the forecast UI even when the schema field is saved.
- `--chart-type <type>` saves the report as a chart instead of the default `table`. Supported family types: `table`, `measure_card`, `line`, `column`, `bar`, `bar_percent`, `area`, `pie`, `double_axis`, `histogram`, `pivot_table`, `funnel`, `combination`, `sankey`, `gauge`, `progress`, `waterfall`, `scatter`, `radar`, `word_cloud`, `bilateral`, `map`. Page aliases that reuse a family preset: `raw_table`, `column_percent`, `column_parallel`, `bar_parallel`, `area_percent`, `annular`, `rose`, `circle_views`, `comparative_measure_card`, `measure_trend`, `waterfall_change`, `scatter_map`, `gis_map`, `gis_mark_map`, `gis_heat_map`, `gis_pulse_map`, `gis_trace_map`, `gis_bar_map`. `trend_table` and `okr_table` are not create types: VizQuery rejects a displayType-only swap. The chart's query transform is not the same string as the displayType: `series` for cartesian/combo/map families, `pie_series` for `pie`/`annular`/`rose`, `histogram` for `histogram`, `funnel` for `funnel`, `table` for `table`/`raw_table`/`pivot_table`, and `measure_card` for measure cards / gauge / progress. `map` needs a dimension with a geographic role. `double_axis` with two or more measures puts the first measure on the main axis and the rest on `schema.subMeasures`.

```bash
# Save a line chart of a metric over a date dimension
bytedcli aeolus report create -r va --app-id "$AEOLUS_APP_ID" --dataset-id "$AEOLUS_DATASET_ID" \
  --name "accuracy-trend" --data-source-id "$AEOLUS_DATA_SOURCE_ID" --chart-type line \
  --dim-met '{"dimMetId":100,"name":"p_date","expr":"`p_date`","roleType":0}' \
  --dim-met '{"dimMetId":200,"name":"accuracy","expr":"`accuracy`","roleType":1}' \
  --set legend.legendPos=bottom --set label.visible=true \
  --field-format "accuracy=percent"

# Period comparison (环比), row totals, and a 7-day forecast
bytedcli aeolus report create -r va --app-id "$AEOLUS_APP_ID" --dataset-id "$AEOLUS_DATASET_ID" \
  --name "accuracy-wow" --data-source-id "$AEOLUS_DATA_SOURCE_ID" --chart-type line \
  --dim-met '{"dimMetId":100,"name":"p_date","expr":"`p_date`","roleType":0}' \
  --dim-met '{"dimMetId":200,"name":"accuracy","expr":"`accuracy`","roleType":1}' \
  --period-compare relativeRatio --totals --forecast 7d
```

`--set` writes dotted keys into `display.conf`. `--field-format` writes a per-measure number format. `--conf-file` accepts `report style get --json` output or a bare conf object. The same three options exist on `report update`. `--table-calc` / `--mini-chart` / `--period-compare` / `--totals` / `--forecast` write analysis on create/update only.


**Options (`report create`):**


- `-r, --region <region>` - Region: cn, sg, va, euttp, euttp2, eupipo, mycis, jplark, hrbimycis, mybd, sglark, uspipo, usttpusts, usbd (required)
- `--app-id <appId>` - Aeolus app ID (required)
- `--dataset-id <datasetId>` - Dataset ID (required)
- `--name <name>` - Saved query name (required)
- `--desc <desc>` - Saved query description
- `--dim-met <json>` - One dimension/metric entry, repeatable
- `--where <json>` - One filter entry, repeatable. Absolute date range: `{"op":"range","val":["2026-08-01","2026-08-03"],"dataTypeName":"date"}` is normalized to the page/VQS `between` op with full-day boundaries and `option.dateMode:"absolute"`.
- `--param <json>` - One in-chart parameter (dataset public param), repeatable
- `--data-source-id <id>` - Override the region default dataSourceId
- `--report-id <reportId>` - Overwrite an existing saved query by report ID
- `--period-compare <spec>` - Period comparison (同环比), repeatable. Type is required (`relativeRatio`, `lastyearRatio`, `lastweekRatio`, `lastmonthRatio`)
- `--totals [spec]` - Table totals. Default: row. Also: `col`, `row,col`
- `--forecast [spec]` - Forecast. Default: 7 day steps. Also: `7`, `7d`


#### In-chart parameters (`--param`)

图内参数（dataset public params，如 `sample_flag IN({sample_flag})`）是数据集模型 SQL 里的公共参数，和普通 `--where` 是两套机制：`--param` 通过 `paramList` 注入选中值，页面上以「图内参数控件」形式展示，可交互切换。

```bash
# 保存带图内参数的报表：只给 name 即可，id / 可选值 / emptyConfig 由数据集自动解析
bytedcli aeolus report create -r va --app-id 1000000 --dataset-id 2000000 --data-source-id "$AEOLUS_DATA_SOURCE_ID" \
  --name "demo report by category" \
  --dim-met '{"dimMetId":1700000000001,"name":"category","expr":"category","roleType":0,"dataType":"string"}' \
  --dim-met '{"dimMetId":1700000000002,"name":"field_cnt","expr":"count(distinct `field_id`)","roleType":1,"dataType":"int"}' \
  --param '{"name":"sample_flag","val":["A"]}' \
  --param '{"name":"sample_region_not_in","val":["region-x","region-y"]}'
# 先查数据集有哪些图内参数及可选值（Dataset in-chart parameters 段）
bytedcli aeolus report resolve -r va --app-id 1000000 --report-id <rid> -j

# Query a Cube with a numeric scalar parameter and an array parameter
bytedcli aeolus viz-query -r cn --app-id 1000000 --dataset-id 2000000 \
  --dim-met '{"dimMetId":1,"name":"sample_count","expr":"count()","roleType":1}' \
  --where '{"dimMetId":2,"name":"p_date","op":"between","val":["2026-08-01","2026-08-01"],"dataTypeName":"date"}' \
  --param '{"id":3,"name":"sample_code","type":"int","val":4}' \
  --param '{"id":4,"name":"sample_flag","val":["A"]}'
```

**Agent Guidance:**

- `--param` 的 JSON `val` 支持数组或有限数字标量，并保留输入形状。数值单选参数（如模型 SQL 中的 `{sample_code}=4`）使用 `"type":"int","val":4`；`[4]` 仍按数组发送，不自动拆为标量。`0`、负数和小数均按原数值保留。紧凑写法 `val=4` 仍生成字符串数组 `["4"]`，数值标量使用 JSON 写法。
- `--param` 条目至少给 `id` 或 `name` 其一；推荐只给 `name` + `val`，`id` / `type` / `initVal` / `emptyConfig` 会自动从 `dataSetModelInfo`（`nodeConf[*].tempParamsInfo`）解析，避免手填出错。
- 保存报表时 CLI 会同时写入 `query.paramList`（决定 SQL 实际过滤）与 `schema.parameters`（决定页面控件渲染，含 `visible` / `isIntial` / `isIntialVisible` / `emptyConfig`）。**两者缺一都会让控件不渲染**——旧版本只写 `paramList` 时页面看不到「图内参数选项」，现已修复。
- `aeolus report resolve` 输出里 `Saved in-chart parameters`（当前报表已保存的选值）与 `Dataset in-chart parameters`（数据集声明的全部可筛选参数及 `Allowed Values`）分开展示；先 resolve 拿可选值，再用 `--param` 复现或调整。

---

### `aeolus report style get` / `aeolus report style update`

Use these when the query (dimensions / metrics / filters) is already correct and only the chart appearance should change. `report style update` reads the existing `reqJson` and patches `display.conf`; it does not rebuild the query. `report update` still rebuilds the query from `--dim-met`.

```bash
# Inspect displayType, styleFamily, allowedConfKeys, paths[], and per-measure formats
bytedcli --json aeolus report style get --url "$AEOLUS_REPORT_URL"

# Preview a patch (default dry-run)
bytedcli aeolus report style update --url "$AEOLUS_REPORT_URL" \
  --set legend.legendPos=bottom --set label.visible=true \
  --field-format "amount=ms" --field-format "rate=permil"

# Array index from paths[].path, e.g. axisMeasure.0.titleEnable
bytedcli aeolus report style update --url "$AEOLUS_REPORT_URL" \
  --set axisMeasure.0.titleEnable=true

# Apply the same patch
bytedcli aeolus report style update --url "$AEOLUS_REPORT_URL" \
  --set legend.legendPos=bottom --set label.visible=true \
  --field-format "amount=ms" --yes

# Edit the get JSON and write it back
bytedcli --json aeolus report style get --url "$AEOLUS_REPORT_URL" > ./style.json
bytedcli aeolus report style update --url "$AEOLUS_REPORT_URL" --conf-file ./style.json --yes
```

Agent Guidance:

- Always run `report style get --json` first. Copy `--set` paths from `paths[].path`. Do not invent `--legend-pos` flags. `paths[]` is `{path,value,type,source}`: `source=saved` is on this report; `source=preset` is allowed for this family but not set yet.
- Numeric path segments are array indices. `--set axisMeasure.0.titleEnable=true` updates that slot and keeps the array.
- JSON `styleFamily` / `allowedConfKeys` list the top-level keys valid for **this** chart type. A table key such as `tableStyle` is rejected on a line chart; `dualAxis` is only valid on `double_axis`; `majorMeasure` is only valid on measure cards.
- Do not copy one chart's `display.conf` onto another type. `column_percent` / `raw_table` / `annular` reuse the `column` / `table` / `pie` key families.
- Field-format presets: `money`, `money_wan`, `auto` (unit scale 万/亿), `default` (page 自动), `int`, `percent`, `permil` (千分比), `raw` (原始值), `ms`, and 数字 units `千`/`万`/`百万`/`千万`/`亿`/`K`/`M`/`B`. `--field-format "*=percent"` applies to every measure. A full numFormat object is also accepted (`type` is `none`/`digit`/`percent`/`permil`/`custom`).
- Default is dry-run. Pass `--yes` to PUT. The command writes `display.conf` and `schema.display.conf` together, and writes both `display.fieldsFormat` and `schema.measures[].format.numFormat`.
- A `--conf-file` `displayType` must match the saved report. A top-level conf key that is not on this chart type is rejected.
- `report style update` only patches `display.conf` and measure number formats. `--table-calc` / `--mini-chart` / `--period-compare` / `--totals` / `--forecast` stay on `report create` / `report update`.

### `aeolus report update`

`aeolus report update --report-id <id>` overwrites an existing saved report in place via `PUT /aeolus/api/v3/dataMart/report`, keeping the same report ID so any dashboard referencing it stays intact. It takes the same options as `report create`, but **`--report-id` is required** here (for `report create` it is optional). `report create` always creates a new report. `report update` rebuilds the whole query and analysis from the flags you pass. To keep 同环比 / 总计 / 预测, pass `--period-compare` / `--totals` / `--forecast` again.

```bash
bytedcli aeolus report update -r cn --app-id "$AEOLUS_APP_ID" --dataset-id "$AEOLUS_DATASET_ID" \
  --report-id "$AEOLUS_REPORT_ID" --data-source-id "$AEOLUS_DATA_SOURCE_ID" --chart-type table \
  --dim-met '{"dimMetId":200,"name":"amount","expr":"`amount`","roleType":1,"aggregation":"sum("}'
```
