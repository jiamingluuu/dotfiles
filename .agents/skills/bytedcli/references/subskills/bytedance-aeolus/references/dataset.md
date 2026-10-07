# Dataset commands

Router: this skill's SKILL.md (named GUIDE.md in the bytedcli mirror). This file is the command body for dataset fields, model, Join, sync, SQL, viz-query, and dataset-specific auth. Do not treat [aeolus.md](aeolus.md) as command body.

App ID / dataset ID come from `list-authorized` / `resource search` (command body in [dashboard.md](dashboard.md)). Partition fields are marked in `dataset-fields`. `dataset-fields`, `dataset-model-info`, and `query` only work with `data_set`, not `dashboard`.

Examples using `$AEOLUS_REPORT_URL` expect the caller to export the actual user-provided URL. Do not replace them with fabricated hosts.

Set the `$AEOLUS_*_ID` variables used below from the target resource or the corresponding list/get output. Numeric IDs and field names inside JSON examples are placeholders to replace with actual resource and field metadata.

## Table of contents

- [dataset-fields](#dataset-fields)
- [dataset-dim-met-map](#dataset-dim-met-map)
- [dataset-fields-download](#dataset-fields-download)
- [dataset-fields-upload](#dataset-fields-upload)
- [dataset-model-info](#dataset-model-info)
- [dataset-create](#dataset-create)
- [dataset-update-sql](#dataset-update-sql)
- [dataset-sync](#dataset-sync)
- [dataset-add-source-table](#dataset-add-source-table)
- [dataset-add-fields](#dataset-add-fields)
- [dataset-update-fields](#dataset-update-fields)
- [dataset-remove-fields](#dataset-remove-fields)
- [dataset-draft](#dataset-draft)
- [dataset-delete / dataset-restore](#dataset-delete--dataset-restore)
- [dataset-folder / dataset-move](#dataset-folder--dataset-move)
- [query](#query)
- [SQL Syntax](#sql-syntax)
- [Logical dataset names may not be queryable](#logical-dataset-names-may-not-be-queryable)
- [Physical-table SQL](#physical-table-sql)
- [Partition Fields](#partition-fields)
- [Recommended workflow for report/dataQuery URLs](#recommended-workflow-for-reportdataquery-urls)
- [End-to-end fallback example](#end-to-end-fallback-example)
- [Extra aeolus query failure signatures](#extra-aeolus-query-failure-signatures)
- [Dataset VizQuery (无需写 SQL 的数据集可视化查询)](#dataset-vizquery-无需写-sql-的数据集可视化查询)
- [VizQuery quick start](#vizquery-quick-start)
- [hrbi_mycis 使用提示](#hrbi_mycis-使用提示)
- [复用浏览器 payload](#复用浏览器-payload)
- [Authentication (dataset-specific)](#authentication-dataset-specific)
- [Open API v3 token (dataset-dim-met-map)](#open-api-v3-token-dataset-dim-met-map)

### dataset-fields

Get dataset dimensions and metrics (field details).

```bash
# List active datasets with the same default scope as the project data-management page.
bytedcli aeolus dataset list -r sg --app-id <APP_ID> --page 1 --page-size 100
bytedcli aeolus dataset list -r sg --app-id <APP_ID> --mine
bytedcli aeolus dataset-fields <datasetId> [options]
```

**Arguments:**

- `datasetId` - Dataset ID (from list-authorized output)

**Options:**

- `-r, --region <region>` - Region: cn, sg, va, euttp, euttp2, eupipo, mycis, jplark, mybd, sglark, uspipo, usttpusts, usbd (required)
- `--json` is a global option and must appear before `aeolus`

**Examples:**

```bash
# Get dataset fields (VA region)
bytedcli aeolus dataset-fields -r va "$AEOLUS_DATASET_ID"

# Get dataset fields (CN region, JSON output)
bytedcli --json aeolus dataset-fields -r cn "$AEOLUS_DATASET_ID"
```

**Output:**

- Dataset name
- **Dimensions**: ID, Name, Type, Partition flag, Description
- **Metrics**: ID, Name, Type, Expression, Description
- Text mode also prints the resolved region as `input -> normalized`; JSON mode returns both `inputRegion` and `normalizedRegion`

---

### dataset-dim-met-map

Get the **edit-time** dimMet map of a dataset through the Aeolus Open API v3 gateway (`GET /aeolus/openApi/v3/dataFactory/getDimMetMap`).

Compared with `dataset-fields` (consumption-side view), every field additionally carries its source-table bindings, authoring flags and upstream inheritance. Use `dataset-fields` when you only need names and types to build a query; use this command when you need to know where a field comes from or whether it can be edited.

```bash
bytedcli aeolus dataset-dim-met-map [options]
```

**Options:**

- `-r, --region <region>` - Region: cn, sg, va, euttp, euttp2, eupipo, mycis, jplark, hrbimycis, mybd, sglark, uspipo, usttpusts, usbd (required)
- `--app-id <appId>` - Aeolus app ID (required; sent as the `App-Id` header)
- `--dataset-id <dataSetId>` - Aeolus dataset ID (required)
- `--need-tags <needTags>` - Pass through the upstream `needTags` filter (optional; default empty)
- `--json` is a global option and must appear before `aeolus`

**Authentication (different from every other aeolus command):**

This gateway does not use the `bytedcli auth login` session or region-scoped `ClientID/ClientSecret`. It requires a standalone Open API token, exported as an environment variable:

- `BYTEDCLI_AEOLUS_OPEN_API_TOKEN` - Open API token, issued per Aeolus app from the console Open API settings page (required)
- `BYTEDCLI_AEOLUS_OPEN_API_BASE_URL` - Override the whole base URL to reach a self-hosted or dev deployment (optional)

There is no `--open-api-token` flag on purpose: keeping the credential in the environment avoids leaking it into shell history and the process list. A missing token fails fast with `AEOLUS_OPEN_API_TOKEN_MISSING` and a hint, before any HTTP request is sent.

**Examples:**

```bash
# Export the token once per shell, then query the dimMet map
export BYTEDCLI_AEOLUS_OPEN_API_TOKEN=<token>
bytedcli aeolus dataset-dim-met-map -r cn --app-id <APP_ID> --dataset-id <DATASET_ID>

# JSON output carries the full field payload including fieldSource bindings
bytedcli --json aeolus dataset-dim-met-map -r cn --app-id <APP_ID> --dataset-id <DATASET_ID>

# Target a self-hosted or dev deployment instead of a built-in region host
export BYTEDCLI_AEOLUS_OPEN_API_BASE_URL=https://demo-dev.example.net/aeolus/openApi/v3
bytedcli aeolus dataset-dim-met-map -r cn --app-id <APP_ID> --dataset-id <DATASET_ID>
```

**Output:**

- `datasetId`, `appId`, `total` field count
- **Dimensions** (`mapType: 0`): ID, Name, Type, Partition flag, Source Table, Description
- **Metrics** (`mapType: 1`): ID, Name, Type, Expression, Source Table, Description
- JSON mode additionally returns per field: `expr`, `fullExpr`, `filterType`, `defaultDataTypeName`, `dimMetVariety`, `dimMetOrder`, `dimMetMixOrder`, `editable`, `visible`, `isPrivate`, `isDeletedField`, `upstreamDimMetId`, `ownerEmailPrefix`, `traits`, `fieldList`, and the full `fieldSource` array
- Text mode shows only the first `fieldSource` entry per field; a field joined from several source tables keeps all of them in JSON output
- Text mode also prints the resolved region as `input -> normalized`; JSON mode returns both `inputRegion` and `normalizedRegion`

**Notes:**

- Dimensions and metrics are split by the upstream `mapType` field: `0` -> dimension, `1` -> metric. Do not use `dimMetVariety` for this — partition dimensions such as `p_date` come back as `dimMetVariety: 1` with `mapType: 0`.
- `fieldList` is JSON-encoded upstream (`"[\"p_date\"]"`); the CLI decodes it into a string array.

---

### dataset-fields-download

Download the native Aeolus dataset-fields XLSX template file for batch editing. This command follows the browser field editor flow (`dimMetDownload` -> `downloadUrl`) and writes the original Aeolus workbook to disk.

```bash
bytedcli aeolus dataset-fields-download [options]
```

**Options:**

- `-r, --region <region>` - Region (required)
- `--app-id <appId>` - Aeolus app ID (required)
- `--dataset-id <dataSetId>` - Dataset ID (required)
- `--output <path>` - Output XLSX path (optional; default `./dataset-fields-<datasetId>.xlsx`)

**Example:**

```bash
bytedcli aeolus dataset-fields-download -r sg --app-id <APP_ID> --dataset-id <DATASET_ID> --output ./dataset-fields.xlsx
```

---

### dataset-fields-upload

Batch add/update dataset fields from the native Aeolus XLSX template. The CLI now follows the browser flow (`uploadDimMetFile` -> `checkDimMetName` -> `PUT dimMetList`) and no longer uses a private `_meta` sheet.

```bash
bytedcli aeolus dataset-fields-upload [options]
```

**Options:**

- `-r, --region <region>` - Region (required)
- `--app-id <appId>` - Aeolus app ID (required)
- `--dataset-id <dataSetId>` - Dataset ID (required)
- `--file <path>` - Input XLSX file path (required)
- `--dry-run` - Preview add/update diff without saving

**Examples:**

```bash
# Recommended: review changes first
bytedcli --json aeolus dataset-fields-upload -r sg --app-id <APP_ID> --dataset-id <DATASET_ID> --file ./dataset-fields.xlsx

# Execute after review
bytedcli aeolus dataset-fields-upload -r sg --app-id <APP_ID> --dataset-id <DATASET_ID> --file ./dataset-fields.xlsx --yes
```

**Recommended workflow:**

- Always run `--dry-run` first and review `addedFields` / `updatedFields` before real upload.
- Use the XLSX file downloaded by `dataset-fields-download`; existing rows should keep their native `ID` column so updates are matched by field id.
- The native template edits `field_name`, `dimensions(0)/measures(1)`, `expression`, `display name`, `desc`, and `ID`; if `checkDimMetName` fails, the CLI stops before `PUT dimMetList`.

---

### dataset-model-info

Get dataset model info from data factory, including the raw model info plus a concise read-only inspection summary for sync mode, partitions, hot fields, filter-rule metadata hints, and bounded preview metadata.

```bash
bytedcli aeolus dataset-model-info [options]
```

**Options:**

- `-r, --region <region>` - Region: cn, sg, va, euttp, euttp2, eupipo, mycis, jplark, mybd, sglark, uspipo, usttpusts, usbd (required)
- `--app-id <appId>` - Aeolus app ID (required, from list-authorized JSON output `app.id`)
- `--dataset-id <dataSetId>` - Dataset ID (required)
- `--json` is a global option and must appear before `aeolus`

**Examples:**

```bash
# Get dataset model info (VA region)
bytedcli aeolus dataset-model-info -r va --app-id <APP_ID> --dataset-id <DATASET_ID>

# Get dataset model info with JSON output
bytedcli --json aeolus dataset-model-info -r cn --app-id <APP_ID> --dataset-id <DATASET_ID>
```

**Output:**

- Text mode prints a short summary only: dataset name/id, sync mode, latest partition, partition fields, hot field top list, filter-rule metadata hints, and preview counts.
- JSON mode keeps `data.modelInfo` unchanged for compatibility and adds `data.inspection`.
- `inspection.syncMode`: normalized `full` / `increment` / `unknown` plus raw values when available.
- `inspection.partitionRange`, `inspection.latestPartition`, `inspection.partition.fields`, `inspection.partition.info`: partition metadata when the auxiliary endpoints expose it.
- `inspection.fieldHeat.fields` and `inspection.hotFields`: bounded field heat metadata; `hotFields` is top 10 ranked by heat desc then name asc.
- `inspection.permissionFilterSummary`: filter rule count, bounded field hints, `coverage: "filter_rules_only"`, and warnings. It does not claim complete column-permission denial coverage.
- `inspection.preview`: dimension/metric/field counts and at most 10 preview metadata fields; it does not include raw sample rows.
- `inspection.warnings`: best-effort auxiliary endpoint failures. A warning does not hide a successful `modelInfo`.

`modelInfo` still includes the raw data factory model, such as:

- `baseConf`: Dataset basic configuration (name, owner, description, sync mode, etc.)
- `nodeConf`: Data source configuration, including:
  - `dataSourceType`: e.g., "hive", "click_house"
  - `dbName`: Database name
  - `tbName`: Table name
  - `query`: Underlying SQL query (if any)
  - `fields`: Field schema with types
  - `partitionConfList`: Partition configuration
- `modelType`: Model type (0 = standard)
- Text mode also prints the resolved region as `input -> normalized`; JSON mode returns both `inputRegion` and `normalizedRegion`

**Use cases:**

- Trace metric calculation logic back to underlying data source
- Understand the SQL transformation between raw tables and dataset fields
- Debug data discrepancies by examining the underlying query

---

### dataset-create

Create a **single-source** dataset from a hive/click_house table or custom SQL. Mirrors the dataManage create page.

**Supported create types:**

- Single source table (`--table-name`) → `nodeType=table`
- Custom SQL (`--sql` / `--sql-file`) → `nodeType=sql`

**Supported `--data-source-type`:** `hive` (default, primary) and `click_house`. Multi-table join create and other engines (e.g. Doris) are not supported yet.

```bash
bytedcli aeolus dataset-create [options]
```

**Options:**

- `-r, --region <region>` - Region (required)
- `--app-id <appId>` - Aeolus app ID (required)
- `--name <name>` - Dataset name (required)
- `--db-name <dbName>` - Source / SQL-node database name (required)
- `--table-name <tableName>` - Source table name (table mode required); SQL mode optional alias (default `Hive-sql-0` / `ClickHouse-sql-0`)
- `--sql <sql>` / `--sql-file <path>` - Custom SQL for SQL-node create
- `--data-source-type <type>` - `hive` (default) or `click_house`
- `--cluster-name <name>` - Source cluster (default: `cn`)
- `--parent-id <parentId>` - Folder parent ID (default: `0`)
- `--belong <belong>` - Belong flag from dataManage URL (default: `1`)
- `--owner <emailPrefix>` - Owner email prefix (default: current auth user)
- `--dc <dc>` - Data-center for source hive catalog (dataManage VA/SG switcher). `va|sg|cn|ce|cn6`; on VA console **SG → `ce`**, **VA → `cn`**
- `--group-id <groupId>` - Resource group id (auto-picked when the app has exactly one group)
- `--clickhouse-data-source-id <id>` - Destination ClickHouse datasource id written to `syncConf.performanceSettings.dataSourceId`
- `--dimension-field` / `--metric-field` / `--field-descr` - Optional field selection
- `--yes` - Submit create; **default is dry-run**
- `--skip-preview` - Skip previewSchema before create

**Examples:**

```bash
# Dry-run create from SG hive (VA app, console SG switcher)
bytedcli aeolus dataset-create -r va --app-id "$AEOLUS_APP_ID" --name demo-dataset --db-name demo_db --table-name sample_table --cluster-name default --data-source-type hive --dc sg --parent-id "$AEOLUS_FOLDER_ID"

# Dry-run create from custom SQL and select the destination ClickHouse datasource
bytedcli aeolus dataset-create -r va --app-id "$AEOLUS_APP_ID" --name demo-sql-dataset --db-name demo_db --cluster-name default --data-source-type hive --dc sg --parent-id "$AEOLUS_FOLDER_ID" --clickhouse-data-source-id 10001 --sql 'SELECT id FROM demo_db.sample_table WHERE date = '\''${date}'\'''

# Submit create and expose selected fields
bytedcli --json aeolus dataset-create -r va --app-id "$AEOLUS_APP_ID" --name demo-dataset --db-name demo_db --table-name sample_table --dimension-field p_date --metric-field score --dc sg --yes
```

**Notes:**

- Default is dry-run. Pass `--yes` to actually create.
- On VA dataManage, the left-side VA/SG switcher maps to API `dc` (`cn`/`ce`). Pass `--dc sg` when the hive table lives under the SG catalog.
- If create returns `aeolus/clickHouseCluster/notFoundSuitAbleCluster`, read `syncConf.performanceSettings.dataSourceId` from a compatible Dataset in the same app/resource group and pass it through `--clickhouse-data-source-id`.
- When no field flags are given, all supported source columns are exposed as dimensions.
- Use `--json` to inspect the generated `dataSetV2` payload before submitting.

---

### dataset-update-sql

Update the custom SQL (`nodeType=sql`) on an existing dataset model. Mirrors dataManage edit save:
`allDataSetInfoV2` -> `getTableSchemaFromSql` -> `previewSchema` -> `preCheckDimMetList` -> `PUT /dataFactory/dataSetV2`.

```bash
bytedcli aeolus dataset-update-sql [options]
```

**Options:**

- `-r, --region <region>` - Region (required)
- `--app-id <appId>` - Aeolus app ID (required)
- `--dataset-id <dataSetId>` - Dataset ID (required)
- `--sql <sql>` / `--sql-file <path>` - New custom SQL (one required)
- `--node-id` / `--node-name` - Target sql node when multiple exist
- `--dc <dc>` - Optional dc override (default: dataset `baseConf.dc`)
- `--dimension-field` / `--metric-field` / `--field-descr` - Optional field selection
- `--save-as online|draft` - Save target. Default `online` writes the online version; `draft` saves an unpublished draft (see [dataset-draft](#dataset-draft))
- `--yes` - Submit save; **default is dry-run**
- `--skip-preview` - Skip previewSchema before save

**Examples:**

```bash
# Dry-run SQL update
bytedcli aeolus dataset-update-sql -r va --app-id "$AEOLUS_APP_ID" --dataset-id 999001 --sql-file ./demo.sql

# Submit SQL update
bytedcli --json aeolus dataset-update-sql -r va --app-id "$AEOLUS_APP_ID" --dataset-id 999001 --sql 'SELECT id FROM demo_db.sample_table WHERE date = '\''${date}'\''' --yes

# Save the SQL change as an unpublished draft; online stays unchanged
bytedcli aeolus dataset-update-sql -r cn --app-id <appId> --dataset-id <dataSetId> --sql-file ./demo.sql --save-as draft --yes
```

**Notes:**

- Only works for sql-node datasets.
- Keeps existing upstream fields by name; adds new SQL columns as dimensions; drops removed upstream columns; preserves computed fields.
- Default is dry-run. Pass `--yes` to save.

---

### dataset-sync

Trigger or inspect data factory sync/backfill instances for an Aeolus dataset.

```bash
bytedcli aeolus dataset-sync trigger [options]
bytedcli aeolus dataset-sync status [options]
bytedcli aeolus dataset-sync rerun [options]
bytedcli aeolus dataset-sync stop [options]
bytedcli aeolus dataset-sync settings get [options]
bytedcli aeolus dataset-sync settings update [options]
```

**Options:**

- `-r, --region <region>` - Region: cn, sg, va, euttp, euttp2, eupipo, mycis, mybd, sglark, usttpusts (required)
- `--app-id <appId>` - Aeolus app ID (required)
- `--dataset-id <dataSetId>` - Dataset ID (required)
- `--start-date <startDate>` - Business start time, e.g. `"2026-04-22 00"` for hourly datasets (required for trigger/status; optional for rerun/stop when using --instance-json)
- `--end-date <endDate>` - Business end time, e.g. `"2026-05-06 23"` for hourly datasets (required for trigger/status; optional for rerun/stop when using --instance-json)
- `--instance-id <id>` - Rerun/Stop only: specific instance ID (acts as filter within date range; repeatable)
- `--instance-json <json>` - Rerun/Stop only: explicit JSON array of instances (direct submit without date range)
- `--only-failed` - Rerun only: only rerun failed/suspended instances in the specified date range (syncStatus=5 or 6)
- `--queue-name <queueName>` - Trigger/Rerun only: queue name recorded by dataManage
- `--max-parallelism <value>` - Trigger/Rerun only, default `5`
- `--dry-run` - Trigger/Rerun/Stop only: print preview without submitting
- `--no-check-min-max` - Trigger only: maps to `checkMinMax: false` in the payload
- `--ttl-days <days>` - Settings update only: fixed data lifecycle, `0-1500`
- `--sync-type <type>` - Settings update only: `scheduled` or `manual`
- `--expect-ttl-days <days>` - Settings update only: fail if the current TTL differs
- `--expect-sync-type <type>` - Settings update only: fail if the current mode differs
- `--yes` - Settings update only: submit the Fabric batch PUT; default is dry-run
- `--json` is a global option and must appear before `aeolus`

**Examples:**

```bash
# Submit the same payload as the dataManage sync page
bytedcli aeolus dataset-sync trigger -r cn --app-id <appId> --dataset-id <dataSetId> --start-date "2026-04-22 00" --end-date "2026-05-06 23" --queue-name root.demo_queue --max-parallelism 5

# Inspect the payload first
bytedcli --json aeolus dataset-sync trigger -r cn --app-id <appId> --dataset-id <dataSetId> --start-date "2026-04-22 00" --end-date "2026-05-06 23" --dry-run

# Check instance status after submit
bytedcli aeolus dataset-sync status -r cn --app-id <appId> --dataset-id <dataSetId> --start-date "2026-04-22 00" --end-date "2026-05-06 23"

# Rerun failed instances in date range
bytedcli aeolus dataset-sync rerun -r cn --app-id <appId> --dataset-id <dataSetId> --start-date "2026-04-22 00" --end-date "2026-05-06 23" --only-failed

# Rerun specific instance IDs within a date range
bytedcli aeolus dataset-sync rerun -r cn --app-id <appId> --dataset-id <dataSetId> --start-date "2026-04-22 00" --end-date "2026-05-06 23" --instance-id 12345 --instance-id 67890

# Rerun using an explicit JSON array of instances without querying date ranges
bytedcli --json aeolus dataset-sync rerun -r cn --app-id <appId> --dataset-id <dataSetId> --instance-json '[{"id":12345,"taskTime":"2026-04-22 00:00:00","sign":"..."}]'

# Stop active instances in date range
bytedcli aeolus dataset-sync stop -r cn --app-id <appId> --dataset-id <dataSetId> --start-date "2026-04-22 00" --end-date "2026-05-06 23"

# Read Fabric default and node-specific sync rules
bytedcli aeolus dataset-sync settings get -r sg --app-id <appId> --dataset-id <dataSetId>

# Preview a Fabric fixed-TTL and sync-mode update
bytedcli aeolus dataset-sync settings update -r sg --app-id <appId> --dataset-id <dataSetId> --ttl-days 60 --sync-type manual --expect-ttl-days 30 --expect-sync-type scheduled

# Apply the reviewed update, poll the async result, and verify the readback
bytedcli aeolus dataset-sync settings update -r sg --app-id <appId> --dataset-id <dataSetId> --ttl-days 60 --sync-type manual --expect-ttl-days 30 --expect-sync-type scheduled --yes
```

**Endpoint mapping:**

- `trigger` mirrors browser `POST /aeolus/api/v3/dataFactory/createSyncJob`
- When `--node-id` is omitted, CLI auto-fills `nodeIdList` from the dataset model. An empty `nodeIdList` returns ok/`previewId` but **does not submit** backfill instances.
- Day-partition datasets (`partitionDefaultFilter=day`) prefer `--start-date/--end-date` as `YYYY-MM-DD`; hourly datasets use `YYYY-MM-DD HH`.
- `status` mirrors browser `POST /aeolus/api/v3/dataFactory/dataSetSyncInfoAllPageBatch`
- `settings get/update` only supports Fabric datasets (`dataSetType=34`).
- Fabric settings read `GET /dataFactory/dataSetSyncSettingsBatch`, save through `PUT /dataFactory/dataSetSyncBatch`, and poll `GET /dataFactory/getDataSetSyncResult`. They do not use ordinary `PUT /dataFactory/dataSetSync`.
- Settings update changes only the `default` rule and preserves node-specific rules, schedule, partition mode, TTL type, and backtracking configuration. Dynamic TTL edits fail closed.
- A single-node Fabric dataset with an empty batch rule list can read its effective ordinary view. Its first CLI save must include `--ttl-days`, because the fallback response does not prove the Fabric TTL type. Multi-node empty configurations fail closed.

---

### dataset-add-source-table

Add a source table into an existing editable dataset model, left join it from an existing table/node, expose selected fields as dimensions or metrics, preview the generated schema, and save through the same V2 data factory endpoint used by the Aeolus edit page.

```bash
bytedcli aeolus dataset-add-source-table [options]
```

**Options:**

- `-r, --region <region>` - Region: cn, sg, va, euttp, euttp2, eupipo, mycis, mybd, sglark, usttpusts (required)
- `--app-id <appId>` - Aeolus app ID (required)
- `--dataset-id <dataSetId>` - Dataset ID (required)
- `--db-name <dbName>` - Source database name (required)
- `--table-name <tableName>` - Source table name (required)
- `--join-from-table <tableOrNode>` - Existing node/table to left join from; accepts `nodeId`, `tbId`, `tbName`, `tableAlias`, or `schemaName` (required)
- `--join-key <key>` - Join key; repeatable. Use `field` for same-name joins or `left=right` when names differ (required)
- `--field <field>` / `--metric-field <field>` - Expose a source field as metric (repeatable)
- `--dimension-field <field>` - Expose a source field as dimension (repeatable)
- `--field-descr <field=descr>` - Override exposed field description (repeatable)
- `--increment-field <field>` - Use incremental extraction by this source field; omitted means full extract
- `--dry-run` - Build and preview the `dataSetV2` payload without saving
- `--skip-preview` - Save without calling `previewSchema`
- `--retry-updating <times>` - Retry save when Aeolus reports the dataset is updating
- `--json` is a global option and must appear before `aeolus`; use it with `--dry-run` to inspect the generated payload

**Example:**

```bash
bytedcli --json aeolus dataset-add-source-table \
  -r cn \
  --app-id <appId> \
  --dataset-id <dataSetId> \
  --db-name demo_db \
  --table-name sample_table \
  --join-from-table sample_prev_table \
  --join-key key1 \
  --join-key key2 \
  --metric-field score \
  --field-descr score=points \
  --increment-field updated_at \
  --dry-run
```

**Notes:**

- This command follows the browser edit flow: `allDataSetInfoV2` -> `tableSchema` -> `previewSchema` -> `dataSetV2`.
- For RDS tables, pass `--db-name` / `--table-name`; do not pass a source `dataSourceId`.
- Use `--dry-run` first on important datasets and review `data.payload` before removing `--dry-run`.

---

### dataset-add-fields

Add source or computed dimensions/metrics to an existing editable dataset, then save via the same data factory `dataSetV2` edit endpoint used by the dataManage page.

```bash
bytedcli aeolus dataset-add-fields -r va --app-id "$AEOLUS_APP_ID" --dataset-id "$AEOLUS_DATASET_ID" \
  --metric "accuracy=[right_count]/[total_count]" \
  --dim "category=get_json_object(\`payload\`, '\$.cat')"

# Expose a source column after the upstream table schema adds it
bytedcli aeolus dataset-add-fields -r sg --app-id <APP_ID> --dataset-id <DATASET_ID> \
  --dim "demo_country_name=demo_country_name"
```

**Options:**

- `-r, --region <region>` (required)
- `--app-id <appId>` (required)
- `--dataset-id <dataSetId>` (required)
- `--dim <name=expression>` - Source or computed dimension, repeatable; use `name=name` for a source column
- `--metric <name=expression>` - Source or computed metric, repeatable; computed expressions may reference other fields via `[name]`
- `--dry-run` - Preview the change without saving
- `--dependencies keep|resolve` - Hive schedule deps on save. Default `keep` sends the model's `dependencyConfList` unchanged; the dataset model read does not return one, so this is normally an empty list. `resolve` re-runs `getSubDependencyList` and can rewrite Dorado upstreams.
- `--save-as online|draft` - Save target. Default `online` writes the online version; `draft` saves an unpublished draft (see [dataset-draft](#dataset-draft))

**Notes:**

- Reads `allDataSetInfoV2`; missing source columns are refreshed through `tableSchema` and saved as upstream fields, while computed fields remain `isUpstreamField=false`. The command then pre-checks via `preCheckDimMetList` and saves with `dataSetV2`.
- Retries with backoff while a freshly edited dataset reports `saveForbidden`/`updating`.
- Duplicate field names are rejected.
- Field-only edits should keep `--dependencies keep`. Use `resolve` only when you intentionally want to refresh Hive task upstreams.

---

### dataset-update-fields

Update one or more existing computed dimension/metric expressions in place. The command preserves the persisted field ID, role, and ordering; Aeolus revalidates and may re-infer the expression output type.

```bash
# Default dry-run: fetch and precheck the complete model without saving
bytedcli --json aeolus dataset-update-fields -r va --app-id "$AEOLUS_APP_ID" --dataset-id "$AEOLUS_DATASET_ID" \
  --field "accuracy=[right_count]/nullIf([total_count], 0)"

# Apply the checked update
bytedcli --json aeolus dataset-update-fields -r va --app-id "$AEOLUS_APP_ID" --dataset-id "$AEOLUS_DATASET_ID" \
  --field "accuracy=[right_count]/nullIf([total_count], 0)" --yes

# Save the update as an unpublished draft; online stays unchanged until dataset-draft publish
bytedcli --json aeolus dataset-update-fields -r cn --app-id <appId> --dataset-id <dataSetId> \
  --field "accuracy=[right_count]/nullIf([total_count], 0)" --save-as draft --yes
```

**Options:**

- `-r, --region <region>` (required)
- `--app-id <appId>` (required)
- `--dataset-id <dataSetId>` (required)
- `--field <name=expression>` - Existing computed field and its new expression, repeatable
- `--yes` - Save the update; without it the command is a dry-run
- `--dependencies keep|resolve` - Hive schedule deps on save. Default `keep` sends the model's `dependencyConfList` unchanged (normally empty).
- `--save-as online|draft` - Save target. Default `online` writes the online version; `draft` saves an unpublished draft (see [dataset-draft](#dataset-draft))

**Notes:**

- Splits each `--field` at the first `=`, so comparisons such as `if([flag] = 1, 1, 0)` remain intact.
- Only editable computed fields can be updated; source, partition, auto-added, missing, duplicate-request, and ambiguous-name fields are rejected before save.
- A batch is atomic: the command applies every requested expression to one in-memory model, calls `preCheckDimMetList`, then performs one `PUT /dataFactory/dataSetV2` only with `--yes`.
- Target fields keep their IDs, roles, and ordering. Their cached `fullExpr`/`fieldList`, plus those of direct/transitive dependents, are invalidated so Aeolus can rebuild canonical dependency expressions.
- Ready-state retries re-fetch the model before applying the patch again, preserving unrelated concurrent edits.

---

### dataset-remove-fields

Remove dimensions/metrics from an existing editable dataset by name.

```bash
bytedcli aeolus dataset-remove-fields -r va --app-id "$AEOLUS_APP_ID" --dataset-id "$AEOLUS_DATASET_ID" --field old_metric
```

**Options:**

- `-r, --region <region>` (required)
- `--app-id <appId>` (required)
- `--dataset-id <dataSetId>` (required)
- `--field <name>` - Field name to remove, repeatable
- `--force` - Remove even a referenced or partition field
- `--dry-run` - Preview the change without saving
- `--dependencies keep|resolve` - Hive schedule deps on save. Default `keep` sends the model's `dependencyConfList` unchanged (normally empty).
- `--save-as online|draft` - Save target. Default `online` writes the online version; `draft` saves an unpublished draft (see [dataset-draft](#dataset-draft))

**Notes:**

- By default blocks removing a field referenced by another field's expression (`[name]`) or a partition/auto-added field; `--force` overrides.
- Refuses to remove every field.

**Agent notes (dataset-add-fields / update-fields / remove-fields):**

- `--dim`/`--metric` are repeatable and take `name=expression`; metric expressions may reference other fields via `[name]`.
- `--field` on update splits on the first `=`, so the expression itself may contain `=`.
- Default `--dependencies keep` sends the model's `dependencyConfList` unchanged and does not recompute upstreams. Do **not** pass `--dependencies resolve` on join datasets unless you intend to rewrite upstreams; `getSubDependencyList` can pick closed/legacy Hive tasks.
- A freshly created/edited dataset can briefly report `saveForbidden`/`updating`; add/update commands retry with backoff.
- Update does not rename or recreate fields. It preserves the persisted field ID, dimension/metric role (`mapType`), and ordering; Aeolus may re-infer the output data type from the new expression.
- Only editable computed fields are accepted for update. Source columns and partition/auto-added fields are rejected.
- Updates are atomic: all target fields are validated and prechecked together, then a single `dataSetV2` save is issued with `--yes`.
- The update command resets backend-derived expression caches for each target and every direct/transitive field that references it via `[field name]`; Aeolus rebuilds canonical `fullExpr` and `fieldList` values during save.
- Retry attempts re-read the whole dataset model before rebuilding the update, avoiding overwriting concurrent field edits with a stale `dataSetV2` payload.
- `--field` on remove is repeatable. By default the command blocks removing a field that another field's expression references via `[name]`, or a partition/auto-added field; pass `--force` to override.
- Refuses to remove every field (a dataset must keep at least one).
- `--save-as draft` applies to `dataset-add-fields`, `dataset-update-fields`, `dataset-remove-fields`, and `dataset-update-sql`. `dataset-fields-upload` and `dataset-add-source-table` always write the online version.

### dataset-draft

Save dataset edits as an unpublished draft, review them, then publish the draft to online. This mirrors the dataManage editor's "save draft" and "publish online" actions.

```bash
# Save an edit as a draft (dataset-add-fields / dataset-update-fields / dataset-remove-fields / dataset-update-sql)
bytedcli aeolus dataset-update-fields -r cn --app-id <appId> --dataset-id <dataSetId> \
  --field "accuracy=[right_count]/nullIf([total_count], 0)" --save-as draft --yes

# Check draft state and saved versions
bytedcli aeolus dataset-draft get -r cn --app-id <appId> --dataset-id <dataSetId>

# Preview the publish request (default dry-run), then publish
bytedcli --json aeolus dataset-draft publish -r cn --app-id <appId> --dataset-id <dataSetId>
bytedcli aeolus dataset-draft publish -r cn --app-id <appId> --dataset-id <dataSetId> --yes
```

**Options (`get`):** `-r, --region`, `--app-id`, `--dataset-id` (all required).

**Options (`publish`):**

- `-r, --region <region>`, `--app-id <appId>`, `--dataset-id <dataSetId>` (required)
- `--dependencies resolve|keep` - Hive schedule deps on publish. Joined datasets must pass one explicitly (`resolve` only checks the first node). For a single-node dataset the default is `resolve`: a custom SQL node sends the `getSubDependencyList` result (this matches the web editor's save), a table node sends an empty list, and the dry-run lists those Dorado upstreams in `dependencyTasks`. `keep` sends the model's `dependencyConfList`, which the editor read does not return, so it is normally an empty list.
- `--yes` - Publish; **default is dry-run**

**Notes:**

- `--save-as draft` reads the model like the editor (`allDataSetInfoV2?enableDraftDataSet=true`). When a draft exists, the edit is applied on top of it, so earlier unpublished draft edits are kept. Without a draft, the online version is the base and the save creates a draft.
- A draft save sends `PUT /dataFactory/dataSetV2` with `enableSaveWithoutMigrate=true`, `enableDraftDataSet=true`, `dataSetVersionType=<online|draft>` (the version being edited), `dataSetVersionId` when Aeolus reports one, and `dc=<baseConf.dc>`. After `--yes` it reads the editor model back (up to about 10 seconds) and fails with `AEOLUS_DATASET_DRAFT_READBACK_FAILED` unless the draft contains this edit: added fields present, removed fields absent, updated expressions or SQL equal to the new value. The error carries `details.writeAccepted: true` because the PUT itself was accepted.
- When `dataset-add-fields`, `dataset-remove-fields`, or `dataset-update-sql` retries a draft save after `saveForbidden`/`updating`, it first re-reads the editor version; if another draft appeared or the draft version changed, it stops with `AEOLUS_DATASET_DRAFT_CHANGED` instead of overwriting it. Check the draft, then re-run the command to build on the latest draft. `dataset-update-fields` instead re-reads the latest draft on each retry and re-applies the expression update before saving.
- If the dataset does not report `draftDataSetVersionType`, `--save-as draft` fails with `AEOLUS_DATASET_DRAFT_UNSUPPORTED` before any write.
- Default `--save-as online` keeps the direct online save. When an unpublished draft exists, the result carries a warning: the online change does not update the draft, and publishing that draft later replaces the online change.
- `publish` requires an unpublished draft (`AEOLUS_DATASET_DRAFT_NOT_FOUND` otherwise). It prechecks the draft fields and sends `PUT dataSetV2` with `enableSaveWithoutMigrate=true`, `enableDraftDataSet=false`, and `dataSetVersionType=draft`. After `--yes` it reads the editor model back and fails with `AEOLUS_DATASET_DRAFT_PUBLISH_UNVERIFIED` unless the online version is reported again. The web page publishes without a confirmation dialog, so review the dry-run first.
- Publishing re-syncs the dataset's Dorado sync task and regenerates pending sync instances. Review `dependencyTasks` in the dry-run first; `resolve` fails with `AEOLUS_DATASET_DEPENDENCY_UNRESOLVED` before any write if the requested node is missing from the result or reports `obtainSuccess=false`.
- `get` shows whether a draft exists, the editor version, and the version-panel list (`dataFactory/getVersionList` for the current user). A failed version list only adds a warning.

### dataset-delete / dataset-restore

Delete or restore a Dataset with guarded lifecycle commands. Deletion is recoverable by default; `--permanent` is irreversible.

```bash
# Preview the default recoverable deletion; exact name is a required safety lock
bytedcli aeolus dataset-delete -r sg --app-id <appId> --dataset-id <dataSetId> --expect-name "demo-canary"

# Apply the recoverable deletion after reviewing the dry-run
bytedcli aeolus dataset-delete -r sg --app-id <appId> --dataset-id <dataSetId> --expect-name "demo-canary" --yes

# Restore a recycled Dataset; add --target-folder-id when the original folder is unavailable
bytedcli aeolus dataset-restore -r sg --app-id <appId> --dataset-id <dataSetId> --expect-name "demo-canary" --target-folder-id 0 --yes

# Permanently delete only a recycle-bin Dataset; irreversible and double-confirmed
bytedcli aeolus dataset-delete -r sg --app-id <appId> --dataset-id <dataSetId> --expect-name "demo-canary" --permanent --confirm-id <dataSetId> --yes
```

### dataset-folder / dataset-move

```bash
# List the dataset folder tree; folder ids feed --target-folder-id and dataset-create --parent-id
bytedcli aeolus dataset-folder list -r cn --app-id <appId>

# Restrict the folder listing to one space (public, private, share, official)
bytedcli aeolus dataset-folder list -r cn --app-id <appId> --space public

# Preview moving datasets into a folder; the target space is derived from --target-folder-id
bytedcli aeolus dataset-move -r cn --app-id <appId> --id <dataSetId> --target-folder-id <folderId>

# Apply the move for several datasets at once
bytedcli aeolus dataset-move -r cn --app-id <appId> --id 100,101 --target-folder-id <folderId> --yes

# Move datasets back to a space root; folder id 0 needs an explicit --space
bytedcli aeolus dataset-move -r cn --app-id <appId> --id <dataSetId> --target-folder-id 0 --space public --yes
```

---

### query

Execute SQL query against a dataset.

```bash
bytedcli aeolus query <datasetId> [sql] [options]
```

**Arguments:**

- `datasetId` - Dataset ID
- `sql` - SQL query string; provide exactly one of this argument or `--sql-file`

**Options:**

- `-r, --region <region>` - Region: cn, sg, va, euttp, euttp2, eupipo, mycis, jplark, mybd, sglark, uspipo, usttpusts, usbd (required)
- `--sql-file <path>` - Read SQL from a regular UTF-8 file up to 1 MiB; mutually exclusive with positional SQL
- `--json` is a global option and must appear before `aeolus`
- `--version <version>` - API version (default: "v2")
- `--limit <limit>` - Limit rows in output (default: 100)

`--sql-file` is the safe transport for callers that must keep SQL out of argv and shell history. Directories, FIFOs, sockets, devices, unreadable files, files larger than 1 MiB, and files containing only whitespace or a BOM are rejected before any query request. Submitted SQL is withheld from text/JSON command output, debug logs, backend error details, and HTTP traces.

**Important:** there are two query paths:

- **Logical dataset SQL**: may work for some datasets, especially simpler pre-materialized ones.
- **Physical-table SQL**: often the reliable path for report/dataQuery URLs and for datasets whose semantic fields do not map directly to queryable identifiers.

**Examples:**

```bash
# Logical dataset SQL may work for some datasets
bytedcli aeolus query -r va "$AEOLUS_DATASET_ID" "SELECT \`[p_date]\`, \`[scene]\` FROM \`[DatasetName]\` WHERE \`[p_date]\` = '2026-03-01' LIMIT 5"

# Keep multiline or sensitive SQL out of argv
bytedcli aeolus query -r va <datasetId> --sql-file ./query.sql

# Physical-table SQL is the reliable fallback when logical SQL fails
bytedcli aeolus query -r va "$AEOLUS_DATASET_ID" "SELECT product_id, max(amount) AS amount FROM \`aeolus_data_db_xxx\`.\`aeolus_data_table_xxx\` WHERE p_date = '2026-03-01' GROUP BY product_id ORDER BY amount DESC LIMIT 10"
```

**Output:**

- Column headers
- Data rows in table format
- Text mode also prints the resolved region as `input -> normalized`; JSON mode returns both `inputRegion` and `normalizedRegion`

**Large integer (Int64) handling:**

ClickHouse / Hive 19-digit ID columns (e.g. `order_id`, `user_id`, `shop_id`) exceed JS `Number.MAX_SAFE_INTEGER` (2^53−1). A naive `JSON.parse` would round them into a `...000` float. bytedcli parses Aeolus query responses through `json-bigint` with `storeAsString: true`, which decides per literal at parse time and emits any long integer as a string so precision is never lost:

- Bare Int64 literal from the backend → returned as a **quoted string** in `--json` output (full 19 digits).
- Explicit `cast(col as String)` in SQL → also returned as a string.
- Short numeric literals stay as JSON numbers. The threshold is based on the JSON numeric literal's character length (json-bigint emits a string when `string.length > 15`, including the sign), which is slightly more conservative than `MAX_SAFE_INTEGER` but always within float64's safe range.
- This parser is not Aeolus column-type-aware: non-Int64 long numeric literals (for example 16-digit safe integers or long decimal literals returned as JSON numbers) may also be returned as strings.

Guidance for LLM / agent consumers:

- Treat long IDs as strings end-to-end. **Do not** call `Number(id)` or `parseInt(id)` — that re-introduces float64 precision loss.
- When forwarding IDs to downstream APIs (order lookup, etc.), pass the string through verbatim.
- You do not need to distinguish "bare Int64" from "cast-as-String" — both arrive as strings on the wire.

Example (`--json` output excerpt):

```json
{
  "rows": [
    ["6926335196492169868", 3998],
    ["6926341275722939951", 2039]
  ]
}
```

---

## SQL Syntax

Aeolus uses ClickHouse SQL syntax, but the table/field syntax depends on whether you are querying a logical dataset alias or the backing physical table.

### Logical dataset names may not be queryable

Some datasets accept logical SQL like:

```sql
FROM `[Dataset Name]`
SELECT `[field_name]`
```

But many report/dataQuery-backed datasets do **not**. Common failure signatures include:

- `unknownTable`
- `unknownIdentifier` / missing field errors
- `SELECT * LIMIT 1` only returning `dummy`

When you see those signals, switch to physical-table discovery instead of continuing to debug the logical alias.

### Physical-table SQL

The reliable fallback is to query the physical table directly after locating it via `dataset-model-info` and `system.query_log`:

```sql
FROM `aeolus_data_db_xxx`.`aeolus_data_table_xxx`
SELECT product_id, sum(amount_cents/100) AS cost
```

### Partition Fields

If a dataset or physical table has partition fields (for example `p_date`), include them in the `WHERE` clause whenever applicable:

```sql
WHERE p_date = '2026-03-01'
```

### Recommended workflow for report/dataQuery URLs

1. Use `resolve-report` to map the URL to dataset IDs.
2. Use `dataset-fields` to inspect semantic fields and partition fields.
3. Use `dataset-model-info` to inspect `nodeConf[].query`, lineage, and source-table hints.
4. If logical SQL fails or only returns `dummy`, query `system.query_log` to find the backing physical table.
5. Query the physical `aeolus_data_db_*`.`aeolus_data_table_*` table directly.

### End-to-end fallback example

```bash
# Resolve the report URL
bytedcli aeolus resolve-report --url "$AEOLUS_REPORT_URL"

# Inspect the dataset fields
bytedcli aeolus dataset-fields -r va <DATASET_ID>

# Inspect the model / source logic
bytedcli aeolus dataset-model-info -r va --app-id <APP_ID> --dataset-id <DATASET_ID>

# Locate the physical table from query_log
bytedcli aeolus query -r va "$AEOLUS_DATASET_ID" "SELECT event_time, query FROM system.query_log WHERE query LIKE '%aeolus_data_table_%' ORDER BY event_time DESC LIMIT 50"

# Query the physical table directly
bytedcli aeolus query -r va "$AEOLUS_DATASET_ID" "SELECT product_id, sum(amount_cents/100) AS cost FROM \`aeolus_data_db_xxx\`.\`aeolus_data_table_xxx\` WHERE p_date = '2026-04-07' AND category = 'demo-category' GROUP BY product_id ORDER BY cost DESC LIMIT 5"
```

### Extra `aeolus query` failure signatures

- `unknownTable` when using a logical dataset name or dataset ID as the table
- `unknownIdentifier` / missing field errors even though the field exists in `dataset-fields`
- `SELECT * LIMIT 1` or `select dummy` only returning a `dummy` column
- `指标内含有非聚合字段 ...`：bracket 形式的指标显示名（`[指标名]`）会自动展开成**非聚合表达式**，外面要么包一层聚合函数，要么改用物理表裸列自己写聚合。
- `聚合函数中包含聚合函数`：该 bracket 字段本身已是预聚合指标，不要再套 `sum()` / `count()`。
- `SQL语法错误，请检查面板中字段的语法是否正确`（无行列号）：常见于 `[日期]` 这类分区宏用法不对，或 ORDER BY 里引用了 SELECT 别名；逐段删减定位，不要按普通 ClickHouse 语法错误排查。
- `存在未知字段、或缺失字段权限`（`SELECT *` 触发）：显式列出需要的字段，不要 `SELECT *`；该错误不会告诉你具体是哪个字段。
- `引擎查询失败`（无任何细节）：常见原因是数据集需要特定队列/权限，或保存的查询配置已失效。`aeolus query` 将 SQL 请求体和响应体视为敏感数据，`--http-debug` 只显示请求元数据，不显示原始 SQL 或响应正文。
- `不支持参数{params}取值为{value}`（占位符未插值）：数据集不支持当前请求形态（典型如不支持 Open API SQL 直查的受限数据集类型）；CLI 会附带 hint。

Do not stop at `SELECT * LIMIT 1` returning only `dummy`; that usually means you still need the physical table, not that the dataset is unusable.

---

## Dataset VizQuery (无需写 SQL 的数据集可视化查询)

`aeolus viz-query` 对应浏览器里 Aeolus 报表/数据集页面发起的 `POST /aeolus/vqs/api/v2/vizQuery/query`，
走和 `aeolus query` 一致的 Titan Passport cookie 鉴权。因此它在 `hrbi_mycis` 等
没有 Query Editor 权限的 region 上也能工作，非常适合：

- 只想快速拿某个 dataset 的 row count / 单维度聚合结果；
- 浏览器抓到一份 payload，想复用结构化参数而不是自己拼 SQL；
- 需要和 Aeolus 前端行为完全一致（含权限与过滤下推）。

默认情况下不需要显式传 `--data-source-id`。当某些数据集在 CLI 构造请求下仍返回
`aeolus/unknown`，并且你在浏览器抓到的成功 payload 明确包含 `dataSourceId` 时，
再把该值作为 `--data-source-id` 传入，或直接复用整份 `--body-file`。

实现和排障上还有几个关键点：

- 鉴权优先复用 Titan Passport cookie（与 `aeolus query` 同一路径），避免依赖 QE session，这样才能覆盖 `hrbi_mycis` 等没有 Query Editor 权限的 region。
- 请求体需要补齐顶层 `schema`、`display`、`originalSchema`；服务端会校验这些字段是否存在。
- 响应的真实数据行通常在 `data.vizData.datasets[]`，键名是各字段 `unique_id` 的字符串形式；解析时需要结合 `data.columns[]` 元数据重建列顺序。
- 若无 `--body-file`，默认构造应尽量贴近浏览器 payload：维度列优先使用原始 `dimMetId` 作为 `id` / `groupById` / `locations.dimensions`，指标列保留聚合前缀 id（如 `count_159...`），并默认带浏览器常见的 table `display.conf` / `fieldsFormat` 与 schema where filter 包装。

### VizQuery quick start

一维 count（昨日数据条数）：

```bash
bytedcli --site i18n-bd aeolus viz-query \
  -r hrbi_mycis --app-id "$AEOLUS_APP_ID" --dataset-id "$AEOLUS_DATASET_ID" \
  --dim-met '{"dimMetId":101,"name":"app_id","expr":"`app_id`","roleType":1,"aggregation":"count(","dataType":"int"}' \
  --where '{"dimMetId":102,"name":"partition_date","op":"lastSync","val":[1],"valOption":{"datetimeUnit":"day","anchorOffset":0}}'
```

参数说明：

- `--dim-met`（可重复）：一个维度或指标，推荐 JSON 对象形式。必填 `dimMetId` / `name` / `expr`；
  `roleType=0` 为维度、`1` 为指标。指标的聚合函数处理要看 `expr`：
  - 当 `expr` 为原始列（如 `dau`、`dnu`）时，需补 `aggregation`（如 `count(` / `sum(`）。
  - 当 `expr` 已自带聚合（如 `sum(amount)/count(distinct p_date)` 这类"日均/比率"指标）时，**不要再传 `aggregation`**，否则后端会报"参数类型不应为 Date"等校验错误。判别依据：在 `aeolus dataset-fields` 输出中 `expr` 已含 `sum(`/`count(`/`avg(` 等。
  - 也支持紧凑的 `dimMetId=1,name=xxx,expr=\`xxx\`,roleType=1,aggr=count(`。
  - **map 类型字段（如 `map<string,int>` 的 flag 计数列）必须按 key 访问**：加 `"mapKey":"<key>"`，此时 `name`/`expr` 可省略（缺省为 key 本身）。例如
    `--dim-met '{"dimMetId":123,"roleType":1,"aggregation":"sum(","mapKey":"my_flag"}'`
    等价于页面上「求和(map_field.my_flag)」。不带 `mapKey` 直接对 map 列做 `sum(` 会被引擎报
    `Illegal type Map(String, Int64) of argument for aggregate function sum` 拒绝。
    ⚠️ Aeolus 平台 report 原始 JSON（`reqJson`）里的 roleType 语义是 `1=维度、2=指标`，与 CLI 的 `0=维度、1=指标` 不同；从浏览器 payload 或 `report resolve` 输出照抄 dimMet 时必须换算，照抄会被 `roleType must be 0 (dim) or 1 (metric)` 拒绝。
- `--where`（可重复）：筛选条件 JSON，需 `name` / `dimMetId` / `op`。`val` 在 preset / `is_null` / `is_empty` 上可省略。
  `op` 可用 `thisWeek` / `last` / `last:week` / `contains` / `not_in` / `having:>` 等别名，CLI 编成 VQS wire。
  绝对日期区间可传 `{"op":"range","val":["2026-08-01","2026-08-03"],"dataTypeName":"date"}`；
  CLI 会规范化为页面/VQS 使用的 `between`、完整日边界时间与 `dateMode:absolute`。
- `--limit`：行数上限，默认 1000。
- `--timeout-ms`：单次请求超时，单位毫秒；适合大数据集或高峰期查询较慢时显式放宽。
- `--transform`：`table`（默认）或 `chart`。
- 响应里的 `queryHistoryId` 可拼成 `<region baseUrl>/pages/dataQuery?appId=<appId>&id=<queryHistoryId>&sid=<datasetId>` 打开 web 页面复现该次查询；CLI 取数与 web 端"展示 X 条"结果一致。`<region baseUrl>` 取 SKILL.md Regions 表里对应行的 host（例如 `va` → `https://aeolus-va.tiktok-row.net`、`cn` → `https://data.bytedance.net`、`jplark` → `https://aeolus-jp-lark.bytedance.net` 等），实现侧以 `src/api/aeolus/site.ts` 的 `REGION_CONFIG[region].baseUrl` 为准。

### `hrbi_mycis` 使用提示

- 如果 `dataset-fields` 在 `hrbi_mycis` 返回 `aeolus/clickhouse/invalidRequest`，优先改查同名的迁移数据集。
- 很多 ClickHouse 数据集会强制要求命中日期分区；直接执行 `viz-query` 时，优先补 `partition_date` 过滤，否则容易报 `force_index_by_date`。
- 例如按最新分区筛选，查询数据集的 `sample_id` 字段：

```bash
bytedcli --site i18n-bd aeolus viz-query \
  -r hrbi_mycis --app-id "$AEOLUS_APP_ID" --dataset-id "$AEOLUS_DATASET_ID" \
  --dim-met '{"dimMetId":101,"name":"sample_id","expr":"`sample_id`","roleType":0,"dataType":"string"}' \
  --where '{"dimMetId":102,"name":"partition_date","op":"lastSync","val":[1],"valOption":{"datetimeUnit":"day","anchorOffset":0}}'
```

### 复用浏览器 payload

如果直接抓到浏览器的完整 payload，可以整段丢给 `--body` 或 `--body-file`：

```bash
bytedcli --site i18n-bd aeolus viz-query \
  -r hrbi_mycis --app-id "$AEOLUS_APP_ID" --dataset-id "$AEOLUS_DATASET_ID" \
  --timeout-ms 90000 \
  --body-file ./payload.json
```

`requestId` 会自动替换为 CLI 生成的新值；旧的 `encryptedReqJson` 会被移除，`schema` 中缺失或不兼容的 web pill 元数据会被归一化，避免生成的 dataQuery history 在 web 端丢失维度、指标或筛选。归一化可能纠正 `isMetric` / `type`，并补齐指标 `format.dataTypeName` / `numFormat`；其余有效字段保持不变。

---

## Authentication (dataset-specific)

By default, Dataset / report / dashboard / chart commands reuse a personal ByteCloud JWT to mint a Titan Passport. In production (`BYTEDCLI_NETWORK_PROFILE=prod`), when `SEC_TOKEN_STRING` or `SEC_TOKEN_PATH` is available, the CLI first exchanges ZTI for a personal JWT using the site mapped from the selected Aeolus region. ZTI exchange unavailable (`AUTH_REQUIRED`) falls back to the same-site `bytedcli auth login` path; after a ZTI JWT is obtained, Titan/Aeolus rejection does not fetch another SSO JWT. Office/default environments continue to use SSO only. Query Editor is excluded from this ZTI path and keeps the browser/session authentication in [query-editor.md](query-editor.md).

For most Dataset API commands, you can optionally configure region-specific `ClientID/ClientSecret` in `.aeolus.env` or environment variables. When present, CLI will prefer those credentials, which is useful for automation:

1. Visit the Aeolus Developer Console to get your ClientID and ClientSecret（域名以租户为准，常见如下）:
   - **CN region**: [data.bytedance.net](https://data.bytedance.net/aeolus/pages/developer/console/certification)
   - **SG region**: [aeolus-sg.tiktok-row.net](https://aeolus-sg.tiktok-row.net/pages/developer/console/certification)
   - **VA region**: [aeolus-va.tiktok-row.net](https://aeolus-va.tiktok-row.net/pages/developer/console/certification)
   - **EU-TTP region (`euttp`)**: [aeolus-eu-ttp.tiktok-eu.net](https://aeolus-eu-ttp.tiktok-eu.net/pages/developer/console/certification)
   - **EU PIPO region (`eupipo`)**: [aeolus-clover-pipo.tiktok-eu.net](https://aeolus-clover-pipo.tiktok-eu.net/pages/developer/console/certification)
2. Create `.aeolus.env` file (choose one location):
   - **Global**: `~/.bytedcli/.aeolus.env` (recommended for npm global install)
   - **Local**: `./.aeolus.env` in current working directory (overrides global)

```bash
# Region-specific credentials
BYTEDCLI_AEOLUS_CN_CLIENT_ID=your_cn_client_id
BYTEDCLI_AEOLUS_CN_CLIENT_SECRET=your_cn_client_secret
BYTEDCLI_AEOLUS_SG_CLIENT_ID=your_sg_client_id
BYTEDCLI_AEOLUS_SG_CLIENT_SECRET=your_sg_client_secret
BYTEDCLI_AEOLUS_VA_CLIENT_ID=your_va_client_id
BYTEDCLI_AEOLUS_VA_CLIENT_SECRET=your_va_client_secret
BYTEDCLI_AEOLUS_EUTTP_CLIENT_ID=your_euttp_client_id
BYTEDCLI_AEOLUS_EUTTP_CLIENT_SECRET=your_euttp_client_secret
BYTEDCLI_AEOLUS_EUPIPO_CLIENT_ID=your_eupipo_client_id
BYTEDCLI_AEOLUS_EUPIPO_CLIENT_SECRET=your_eupipo_client_secret
```

### Open API v3 token (`dataset-dim-met-map`)

`aeolus dataset-dim-met-map` targets the `/aeolus/openApi/v3` gateway, which authenticates with a standalone token instead of the `bytedcli auth login` session or the `ClientID/ClientSecret` pair above. It is the only Aeolus command with this auth model today.

```bash
# Issued per Aeolus app from the console Open API settings page
export BYTEDCLI_AEOLUS_OPEN_API_TOKEN=<token>

# Optional: point at a self-hosted or dev deployment instead of a built-in region host
export BYTEDCLI_AEOLUS_OPEN_API_BASE_URL=https://demo-dev.example.net/aeolus/openApi/v3
```

- `--app-id` is required and travels in the `App-Id` header; the gateway rejects the call without it.
- The token has no CLI flag by design — keeping it in the environment avoids leaking it into shell history and the process list.
- Missing token fails fast with `AEOLUS_OPEN_API_TOKEN_MISSING` and a hint, before any HTTP request is sent.

Additional ClientID env vars (same `.aeolus.env` locations):

```bash
BYTEDCLI_AEOLUS_MYCIS_CLIENT_ID=your_mycis_client_id
BYTEDCLI_AEOLUS_MYCIS_CLIENT_SECRET=your_mycis_client_secret
BYTEDCLI_AEOLUS_MYBD_CLIENT_ID=your_mybd_client_id
BYTEDCLI_AEOLUS_MYBD_CLIENT_SECRET=your_mybd_client_secret
BYTEDCLI_AEOLUS_SGLARK_CLIENT_ID=your_sglark_client_id
BYTEDCLI_AEOLUS_SGLARK_CLIENT_SECRET=your_sglark_client_secret
BYTEDCLI_AEOLUS_USTTPUSTS_CLIENT_ID=your_usttpusts_client_id
BYTEDCLI_AEOLUS_USTTPUSTS_CLIENT_SECRET=your_usttpusts_client_secret
```

Console links also exist for MYCIS (`https://aeolus-mycis.byteintl.net/#/developer/console/certification`), SGLARK, and USTTPUSTS. Default Dataset API commands mint a Titan Passport (production + `SEC_TOKEN_*` prefers ZTI→personal JWT; ZTI exchange unavailable falls back to `bytedcli auth login`, but a rejected ZTI JWT does not; office stays on SSO). ClientID/ClientSecret is an optional automation override that still wins when configured. `dataset-dim-met-map` is the only command that uses `BYTEDCLI_AEOLUS_OPEN_API_TOKEN` instead.
