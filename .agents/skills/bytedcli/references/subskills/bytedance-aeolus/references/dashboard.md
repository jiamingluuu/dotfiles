# Dashboard commands

Router: this skill's SKILL.md (named GUIDE.md in the bytedcli mirror). This file is the command body for dashboard query, filters, diff, download, create/build/update, folder/move, and resource discovery. Do not treat [aeolus.md](aeolus.md) as command body.

Examples using `$AEOLUS_DASHBOARD_URL` expect the caller to export the actual user-provided URL. Do not replace them with fabricated hosts or commit real resource IDs into docs.

Changing an existing dashboard (live re-anchor, smallest change, verify): [dashboard-development.md](dashboard-development.md). Report/chart command body: [report-chart.md](report-chart.md).


Set the `$AEOLUS_*_ID` variables used below from the target resource or the corresponding list/get output. Numeric IDs and field names inside JSON examples are placeholders to replace with actual resource and field metadata.

## Table of contents

- [Resource Types](#resource-types)
- [list-authorized](#list-authorized)
- [resource recent](#resource-recent)
- [resource search](#resource-search)
- [dashboard query](#dashboard-query)
- [filter options (dashboard-scoped)](#filter-options-dashboard-scoped)
- [dashboard diff](#dashboard-diff)
- [dashboard download](#dashboard-download)
- [aeolus dashboard create / aeolus dashboard build](#aeolus-dashboard-create--aeolus-dashboard-build)
- [aeolus dashboard folder list / aeolus dashboard move](#aeolus-dashboard-folder-list--aeolus-dashboard-move)

## Resource Types

| Type        | Description      |
| ----------- | ---------------- |
| `dashboard` | Aeolus dashboard |
| `data_set`  | Aeolus dataset   |

---

### list-authorized

List dashboards and datasets you have access to.

```bash
bytedcli aeolus list-authorized [options]
```

**Options:**

- `-r, --region <region>` - Region: cn, sg, va, euttp, euttp2, eupipo, mycis, jplark, hrbimycis, mybd, sglark, uspipo, usttpusts, usbd (required)
- `-t, --type <type>` - Filter by type: dashboard, data_set
- `--limit <limit>` - Number of results (default: 20)
- `--offset <offset>` - Pagination offset (default: 0)
- `--creator <creator>` - Filter by creator (owner username)
- `--keyword <keyword>` - Filter by keyword (matches resource name)

**Examples:**

```bash
# List all authorized resources (VA region)
bytedcli aeolus list-authorized -r va

# List only datasets (CN region)
bytedcli aeolus list-authorized -r cn --type data_set --limit 50

# Pagination (SG region)
bytedcli aeolus list-authorized -r sg --offset 20 --limit 20

# Filter by keyword (matches resource name)
bytedcli aeolus list-authorized -r cn --keyword demo
```

**Output:**

- ID, Type, Name, Owner, App, Last Visit Time

---

### resource recent

List recently visited Aeolus resources.

```bash
bytedcli aeolus resource recent [options]
```

**Options:**

- `-r, --region <region>` - Region: cn, sg, va, euttp, euttp2, eupipo, mycis, jplark, hrbimycis, mybd, sglark, uspipo, usttpusts, usbd (required)
- `--limit <limit>` - Number of results to return (default: 20)

**Examples:**

```bash
# List recently visited resources
bytedcli aeolus resource recent -r va --limit 20
```

**Output:**

- ID, Type, Name, Owner, App, URL
- JSON output includes `limit` and `truncated`.

---

### resource search

Search Aeolus resources by keyword.

```bash
bytedcli aeolus resource search [options]
```

**Options:**

- `-r, --region <region>` - Region: cn, sg, va, euttp, euttp2, eupipo, mycis, jplark, hrbimycis, mybd, sglark, uspipo, usttpusts, usbd (required)
- `--keyword <keyword>` - Search keyword (required)
- `-t, --type <type>` - Comma-separated resource types: dashboard, data_set, report, screen, prep_task, scene
- `--page <n>` - Page number, 1-based (default: 1)
- `--page-size <n>` - Items per page (default: 20)

**Examples:**

```bash
# Search dashboards and reports
bytedcli aeolus resource search -r va --keyword sample --type dashboard,report --page 1 --page-size 20

# Continue from the next page
bytedcli aeolus resource search -r va --keyword sample --page 2 --page-size 20
```

**Output:**

- ID, Type, Name, Owner, App, URL
- JSON output includes `total`, `page`, `page_size`, `types`, and `truncated`.

---

### dashboard query

Discover chart reports and dashboard public filters from a dashboard URL, or query one/all chart reports with bounded preview rows. Use `dashboard download` instead when the user needs CSV/XLSX file exports.

```bash
# Discovery: list selected-sheet charts and public filters
bytedcli aeolus dashboard query --url "$AEOLUS_DASHBOARD_URL"

# Read-only structured filter discovery
bytedcli --json aeolus dashboard filters --url "$AEOLUS_DASHBOARD_URL"

# Query one chart/report with named filters and Top N
bytedcli aeolus dashboard query --url "$AEOLUS_DASHBOARD_URL" \
  --report-id 345678 \
  --filter "country=SG" \
  --sort-by "revenue" \
  --top-n 10

# Query every report in the selected sheet with per-report failure isolation
bytedcli --json aeolus dashboard query -r va --dashboard-id 123456 --sheet-id 789012 --all-reports --limit 20
```

**Options (`dashboard query`):**

- `--url <aeolusUrl>` - Aeolus dashboard URL. Region, dashboard id, optional sheet id, and optional report id are inferred when present.
- `-r, --region <region>` - Region; defaults to `cn` when `--url` is not provided.
- `--dashboard-id <dashboardId>` - Dashboard id.
- `--sheet-id <sheetId>` - Sheet id. If omitted, Aeolus chooses the current/default sheet.
- `--report-id <reportId>` - Query one report from the selected sheet.
- `--all-reports` - Query every report from the selected sheet. Execution is serial and each report failure is isolated in `failed[]`.
- `--filter <expr>` - Named filter, repeatable. Form: `field=value`, `field[op]=value`, or `stat_date[thisWeek]`. Same date / compare / HAVING syntax as `report query`. The field matches a dashboard filter candidate (public filter name or report whereList condition name) first; an all-digit field then matches by `dimMetId` — the only handle for **unnamed** report whereList conditions (typically dates): `--filter "<dimMetId>[gte]=<date>" --filter "<dimMetId>[lte]=<date>"`. Candidate dimMetIds show up in discovery `publicFilters[]` and in the unmatched-filter error's candidate list. Filters that match no candidate fall back to dataset named filters, which requires dataset access (board-only permission gets a 403 with the candidate list in the hint).
- `--top-n <N>` - Apply Top N to `--sort-by` and use `N` as the effective preview limit. Requires `--sort-by`.
- `--sort-by <field>` / `--sort-order <asc|desc>` - Sort field name/id and order.
- `--limit <N>` - Preview row limit. Default is `100`.
- `--timeout-ms <ms>` - Per-report VizQuery timeout in milliseconds.
- `--with-sql` - Include the executed SQL per successful report (`sqlList`; `sqlWarning` explains failures). The executed SQL is where symbolic date filters (e.g. `lastSync`) appear resolved to real partition dates — the way to confirm data freshness on daily-snapshot boards. Adds up to two serial requests per report when the VizQuery response lacks SQL; the SQL may contain sensitive table/column names, avoid pasting into public logs.

**Notes:**

- Without `--report-id` or `--all-reports`, the command is discovery-only and returns `reports[]` plus a `publicFilters[]` summary.
- Single/all-report query results use stable `results[]` and `failed[]` arrays. Successful items include `chartId`, `reportId`, `name`, `status`, `columns`, `rows`, `rowCount`, `returnedRows`, `limit`, `truncated`, `queryHistoryId`, and `fileGuidance`.
- `truncated:true` means returned rows reached the effective preview limit. Use `aeolus dashboard download` for file exports.
- `dashboard query` reuses the selected dashboard sheet's saved report `reqJson` and dashboard public filters, then merges CLI `--filter` overrides by candidate name or dimMetId (all-digit fields; name match wins first).


### filter options (dashboard-scoped)

```bash
bytedcli --json aeolus dashboard filters --url "$AEOLUS_DASHBOARD_URL"
bytedcli --json aeolus filter options -r va --dataset-id <datasetId> --filter-id <dimMetId> --keyword demo
```

`filter options` calls the Aeolus option-suggest endpoint for a dataset field. Use `--keyword` to narrow values; optional `--dashboard-id`, `--sheet-id`, and `--report-id` pass UI context when option values depend on dashboard/report state. Shared `--filter` syntax is the same as report-side: `--filter "field=value"` or `--filter "field[op]=value1,value2"`.

---

### dashboard diff

Compare a local dashboard sheet JSON payload with the current online `simpleSheet` payload. This is read-only and does not query dashboard data rows.

```bash
bytedcli aeolus dashboard diff -r cn --app-id <appId> --dashboard-id <dashboardId> --sheet-id <sheetId> --payload-file ./simple-sheet.json
bytedcli --json aeolus dashboard diff -r va --app-id <appId> --dashboard-id <dashboardId> --sheet-id <sheetId> --payload-file ./simple-sheet.json
```

**Options (`dashboard diff`):**

- `-r, --region <region>` - Region (required).
- `--app-id <appId>` - Aeolus app id.
- `--dashboard-id <dashboardId>` - Dashboard id.
- `--sheet-id <sheetId>` - Sheet id.
- `--payload-file <file>` - Local JSON object payload. A direct object is compared as-is. Common bytedcli wrappers such as `{ "status": "success", "data": { "data": { ... } } }` are unwrapped when unambiguous.

**Notes:**

- The command fetches online state through `sheet/simpleSheet` only.
- Object keys are canonicalized recursively; array order is preserved.
- Output includes `equal`, `changedCount`, `changes[]`, `localHash`, and `remoteHash`. Each change has a deterministic `path`, `kind` (`added`, `removed`, `changed`), and bounded JSON value summaries.
- `dashboard diff` does not save, update, publish, delete, sync, or create dashboard resources. Dashboard sync/delete/new flows remain unsupported/deferred here.

---

### dashboard download

Download report file exports from a dashboard sheet. Pass either one `--report-id` or `--all-reports`; each successful report writes one CSV/XLSX file under `--output`.

```bash
bytedcli aeolus dashboard download --url "$AEOLUS_DASHBOARD_URL" --all-reports --output ./dashboard-export
bytedcli aeolus dashboard download -r va --dashboard-id 123456 --sheet-id 789012 --report-id 345678 --output ./dashboard-export
bytedcli aeolus dashboard download --url "$AEOLUS_DASHBOARD_URL" --report-id 345678 --report-filter '[{"id":123,"val":["demo"]}]' --output ./dashboard-export
```

**Options (`dashboard download`):**

- `--url <aeolusUrl>` - Aeolus dashboard URL. Region, dashboard id, optional sheet id, and optional report id are inferred when present.
- `-r, --region <region>` - Region; defaults to `cn` when `--url` is not provided.
- `--dashboard-id <dashboardId>` - Dashboard id.
- `--sheet-id <sheetId>` - Sheet id. If omitted, Aeolus chooses the current/default sheet.
- `--report-id <reportId>` - Download one report from the selected sheet.
- `--all-reports` - Download every report from the selected sheet.
- `--report-filter <json>` - JSON array of dashboard filter overrides, for example `[{"id":123,"val":["demo"]}]`.
- `--limit <N>` - Per-report export row limit. Default is `1000000`; pivot/trend table XLSX downloads are capped at an effective `rowLimit` of `50000`.
- `--output <directory>` - Destination directory.
- `--timeout-ms <ms>` - Per-report download timeout in milliseconds.

**Notes:**

- Batch mode is serial and continues after individual report failures.
- JSON mode always returns stable `results[]` and `failed[]` arrays. Use `results[].output` for downloaded files and `failed[].message` for per-report errors.
- Successful `results[]` entries include `rowCount`, `limitReached`, and `completeness`; CSV row counts exclude the header row and XLSX row counts are unknown.
- Filter discovery remains a separate capability; `dashboard download` does not replace dedicated filter-list commands.
- This is a file export, not the bounded preview returned by `report query` / `viz-query`.

---

### `aeolus dashboard create` / `aeolus dashboard build`

Use `aeolus dashboard create` for an empty dashboard, or `aeolus dashboard build --spec <file>` to build a complete multi-chart dashboard from a JSON spec in one call: it creates each report, auto-lays-out a 12-column masonry `componentTree`, then creates the dashboard embedding all charts (a single `POST /aeolus/api/v3/dashboard/dashboard`).

```bash
# Empty dashboard
bytedcli aeolus dashboard create -r cn --app-id "$AEOLUS_APP_ID" --name "demo-dashboard"
# Multi-chart dashboard from a spec
bytedcli aeolus dashboard build -r cn --spec ./dashboard.json
# List published dashboard versions
bytedcli --json aeolus dashboard version list -r cn --app-id "$AEOLUS_APP_ID" --dashboard-id 123456
# Fetch a sheet's simpleSheet payload
bytedcli --json aeolus dashboard sheet get -r cn --app-id "$AEOLUS_APP_ID" --dashboard-id 123456 --sheet-id 789012
# Compare a local sheet payload with the current online simpleSheet payload
bytedcli --json aeolus dashboard diff -r cn --app-id <appId> --dashboard-id <dashboardId> \
  --sheet-id <sheetId> --payload-file ./simple-sheet.json
# Save/publish an existing dashboard from an editor-compatible PUT payload
bytedcli --json aeolus dashboard update -r cn --app-id "$AEOLUS_APP_ID" --dashboard-id 123456 \
  --payload-file ./dashboard-update.json --publish --version-descr "add funnel" \
  --auto-delete-oldest-version --dry-run
# List dashboard charts and public filters from a dashboard URL
bytedcli --json aeolus dashboard query --url "$AEOLUS_DASHBOARD_URL"
# List structured dashboard public/report/chart filters without querying data
bytedcli --json aeolus dashboard filters --url "$AEOLUS_DASHBOARD_URL"
# Query one dashboard chart with bounded preview rows
bytedcli --json aeolus dashboard query --url "$AEOLUS_DASHBOARD_URL" \
  --report-id 345678 --filter "country=SG" --sort-by "revenue" --top-n 10
# Download every report from one dashboard sheet, one file per report
bytedcli --json aeolus dashboard download --url "$AEOLUS_DASHBOARD_URL" \
  --all-reports --output ./dashboard-export
```

Spec shape (`dashboard.json`):

```jsonc
{
  "appId": 1000000,
  "name": "demo-cost-monitor",
  "datasetId": 2000000,
  "dataSourceId": 3000000,
  "charts": [
    {
      "type": "measure_card",
      "name": "total",
      "dimMet": [{ "field": "amount", "agg": "sum", "as": "total" }],
      "where": [{ "field": "bill_type", "op": "in", "val": ["normal"] }],
      "style": { "numFormat": "money_wan" },
    },
    {
      "type": "table",
      "name": "by product",
      "dimMet": [{ "field": "product_name" }, { "field": "amount", "agg": "sum" }],
      "style": { "topN": 25, "conditionalFormat": "bar" },
    },
  ],
}
```

Agent Guidance:

- `dashboard build` resolves each chart's `dimMet[].field` / `where[].field` to its dimMetId via dataset metadata, so the spec uses field **names**, not IDs.
- A chart's `type` may be omitted or set to `"auto"` to recommend one from the dimMet shape: no measure → `table`; 0 dimensions → `measure_card`; 1 date-dimension + 1 measure → `line` (trend); 1 dimension + 1 measure → `column`; 1 dimension + ≥2 measures → `double_axis`; ≥2 dimensions → `table`. Pass an explicit `type` to override.
- `style.numFormat` takes **either a full numFormat object** (any prefix / suffix / unit / precision / type — not limited to money) **or a shortcut string**. Shortcuts: `"money"` (￥ auto 万/亿), `"money_wan"` (￥ fixed 万), `"auto"` (plain number, auto-scaled 万/亿, no currency), `"default"` (page 自动), `"int"`, `"percent"`, `"permil"` (千分比, wire `type:"permil"`), `"raw"` (原始值, wire `type:"none"`), `"ms"`, and named 数字 units `"千"`/`"万"`/`"百万"`/`"千万"`/`"亿"`/`"K"`/`"M"`/`"B"`. `style.fieldFormat` may use `"*"` to apply one format to every measure. For any other unit, pass the object directly, e.g. a count in 万: `{ "kSep": true, "precision": 1, "unit": "万" }`, or bytes→GB: `{ "precision": 2, "unit": { "ratio": 1073741824, "symbol": " GB" } }`, or a plain suffix: `{ "kSep": true, "precision": 0, "suffix": " 人" }`. Custom tiered rules (`type:"custom"`) only accept a full object copied from a saved report.
- `style.set` is a dotted-path overlay into `display.conf`, same language as `report style update --set`. Example: `{ "legend.legendPos": "bottom", "label.visible": true }`. `style.fieldFormat` maps measure name/id to a preset or numFormat object. `style.conf` is a raw `display.conf` overlay.
- `style.conditionalFormat`: `"bar"` (in-cell data bar) / `"heatmap"` (color scale) / `"tag"` (up/down/flat arrows + colored text by sign, best on diff measures), or a full conditionalFormat object. `style.topN`: keep the top N dimension rows, sorted by the measure desc.
- More analysis configs (reference fields by **name**): `style.sort` `[{ "field": "amount", "order": "desc" }]` (sort by a dimension or a measure); `style.referenceLine` `[{ "name": "目标", "value": 100, "field": "amount" }]` (fixed-value line; `field` defaults to the first measure).
- `layout` is optional per chart; omitted charts auto-flow in a 12-column masonry (measure_card spans 4 columns, table/line span 12, others 6). Pass an explicit `layout` (`width` px / `x` / `gridIndex`) to override.
- Auth reuses `getAeolusHeaders` (Titan Passport cookie), same as `report create`. `appId` and `dataSourceId` are required; when `dataSourceId` is unknown, read it from a `viz-query --http-debug` SQL comment (`data_source_id: <id>`).
- `dashboard update` mirrors the dashboard editor's `PUT /aeolus/api/v3/dashboard/dashboard` call and adds the required `App-Id` header. Use it when modifying an existing dashboard sheet/layout with a browser-compatible payload containing fields such as `id`, `updateDashboard`, `updateSheets`, `publish`, `versionDescr`, and `deleteVersionId`.
- When publishing, pass `--publish --version-descr <text>`. By default the command sets `update_dashboard_resource=true`; use `--no-update-dashboard-resource` only when intentionally preserving the raw payload behavior.
- Aeolus dashboards can have a small published-version cap. `--auto-delete-oldest-version` first calls `dashboard version list` and, when there are already 3 versions and no explicit `--delete-version-id`, adds the oldest version ID to `deleteVersionId`.
- Always run `bytedcli --json aeolus dashboard update --dry-run ...` before a write to inspect the final payload. Then rerun without `--dry-run` to save/publish.
- `dashboard diff` is read-only. It compares a local JSON payload file with the current online simpleSheet from `sheet/simpleSheet`, canonicalizes object key order, preserves array order, and reports stable leaf/path changes with bounded value summaries plus local/remote hashes. It does not save, update, publish, delete, sync, create a new dashboard, or retrieve dashboard data rows.
- `dashboard query` without `--report-id` / `--all-reports` is discovery-only: it lists chart `reportId` / `chartId`, names, display types, and dashboard public-filter summaries. With `--report-id`, it returns a stable single-report result containing `chartId`, `reportId`, `name`, `status`, `columns`, `rows`, `rowCount`, `returnedRows`, `truncated`, and `fileGuidance`. With `--all-reports`, it queries reports serially and isolates individual failures in `failed[]`.
- `dashboard filters` is read-only filter discovery. It returns grouped `dashboard_public`, `report_level`, and `chart_schema` filters with `name`, `dimMetId`, `op`, `defaultValue`, `source`, `overridable`, and dataset/report context. Use it before writing repeatable `--filter` expressions.
- `dashboard query --filter` matches a dashboard filter candidate by **name** first (public filter name / report whereList condition name); an **all-digit** field then matches by `dimMetId` — the only handle for unnamed report whereList conditions, typically dates: `--filter "<dimMetId>[gte]=<date>" --filter "<dimMetId>[lte]=<date>"` (find dimMetIds via `dashboard filters`). Filters matching no candidate fall back to dataset named filters and need dataset access; board-only permission gets a 403 whose hint lists this report's candidates.
- `dashboard query --with-sql` adds per-report `sqlList` (with `sqlWarning` when SQL could not be fetched). The executed SQL is where symbolic date filters (`lastSync` etc.) show up resolved to real partition dates — use it to confirm data freshness on daily-snapshot boards. Costs up to two extra serial requests per report; the SQL can contain sensitive table/column names, keep it out of public logs.
- `dashboard query` is a bounded preview command. Treat `truncated:true` as a signal to use `dashboard download` for CSV/XLSX file exports. `--top-n` requires `--sort-by` and becomes the effective preview limit; otherwise `--limit` defaults to 100.
- `dashboard query` returns every row the server sent for the requested limit, including charts that paginate in the browser. `rowCount` is the display row count and `truncated` is decided by the server-side row count, so a pivot result that expands into more table rows than the limit is still reported as `complete` when nothing was cut.
- `pivot_table` results are the expanded table, so they include the chart's subtotal and grand-total rows (their dimension cells carry the chart's total label). Filter those rows out before summing a pivot result, otherwise every value is counted twice.
- `dashboard download` writes VizQuery export files under `--output`; it does not print report payload rows to stdout. In `--json` mode, read `data.results[]` and `data.failed[]`; batch mode continues after individual report failures. Inspect each result's `completeness`: `complete`, `limit_reached`, or `unknown`.
- `style.tableCalculation`, `style.miniChart`, `style.periodCompare`, `style.totals`, and `style.forecast` write the same analysis blocks as `--table-calc` / `--mini-chart` / `--period-compare` / `--totals` / `--forecast`. `combination` is a `--chart-type`; `double_axis` with two measures uses `schema.subMeasures` for the second axis.

### `aeolus dashboard folder list` / `aeolus dashboard move`

`folder list` is how you discover the folder ids that `dashboard move --target-folder-id` and `dashboard create --parent-id` expect. Dashboards live in a `public` or `private` space; `move` derives the target space from `--target-folder-id`, so `--space` is only needed for folder id `0` (the space root). Moving across spaces is supported and the dashboard adopts the target folder's space.

```bash
# Folder tree for one app, every space
bytedcli aeolus dashboard folder list -r cn --app-id "$AEOLUS_APP_ID"
# Only the public dashboard space
bytedcli --json aeolus dashboard folder list -r cn --app-id "$AEOLUS_APP_ID" --space public
# Preview a move; nothing is written without --yes
bytedcli aeolus dashboard move -r cn --app-id "$AEOLUS_APP_ID" --id 123456 --target-folder-id "$AEOLUS_FOLDER_ID"
# Apply the move
bytedcli aeolus dashboard move -r cn --app-id "$AEOLUS_APP_ID" --id 123456 --target-folder-id "$AEOLUS_FOLDER_ID" --yes
# Move back to the private space root
bytedcli aeolus dashboard move -r cn --app-id "$AEOLUS_APP_ID" --id 123456 --target-folder-id 0 --space private --yes
```
