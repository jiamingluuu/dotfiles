---
name: bytedance-hive
description: "Search, explore, create, and modify Hive/Clickhouse/Doris data assets via bytedcli, and use Hive Copilot for managed Spark Application diagnosis, comparison, tuning, skew/Shuffle/resource analysis, or CN Spark/Hive runtime knowledge Q&A. Use when tasks mention Hive, DataLeap, data catalog, table schema, column metadata, Dorado producer tasks, data lineage, creating/modifying Hive or Doris tables, or when the user gives Spark application_* and asks to diagnose failures/slowness or compare Spark jobs. Raw Spark UI evidence belongs to bytedance-megatron."
---

# bytedcli Hive (DataLeap Data Catalog)

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

- Search for Hive databases and tables in DataLeap
- Get CREATE TABLE DDL for Hive tables via `hive ddl`
- Get detailed table/database information including schema and columns
- Locate upstream producer Dorado task IDs from a Hive table or entity
- Check partition row counts and top partitions for Hive tables
- Preview Hive table sample data (columns and rows)
- Query physical storage replicas and cross-region sync distribution for Hive tables
- View data lineage relationships
- Explore Clickhouse and Doris data assets
- Create new Hive tables with fields, partition keys, TTL, and storage settings
- Create Doris tables through `hive create --type DorisTable` using raw DDL plus namespace metadata
- Modify table field definitions (column names, types, comments, security labels)
- Update Hive table alias / description / business metadata / project binding / TTL through `hive table update`
- List Coral projects available for Hive table binding
- Use Hive Copilot when the user gives Spark `application_*` and asks to diagnose failures/slowness, compare Spark jobs, analyze data skew/Shuffle/resource configuration, or explicitly asks Hive Copilot / Hive Agent for CN Spark/Hive runtime knowledge Q&A

Route raw Spark UI evidence, Stage/Task/Executor details, or event-log forensics to `bytedance-megatron`. For Hive tables, schema, partitions, lineage, and DataLeap/Coral assets, stay in this `bytedance-hive` skill and use the metadata commands below.

### SQL 执行路由

`bytedcli hive` 仅提供元数据，不提供 SQL 执行引擎：
- **查表结构**：`bytedcli hive ddl <db> <table>`（无血缘延迟）。
- **执行 SQL**：`bytedcli magibook sql execute --sql "..."`；导出飞书/CSV 走 `bytedcli aeolus query-editor query one`。
- **离线任务**：`bytedcli dorado adhoc exec --task-id <id> --yes`。

## 前置条件

- 使用通用调用方式：`../../invocation.md`
- 在 ByteDance 生产网环境下调用 sg region 前，`export BYTEDCLI_NETWORK_PROFILE=prod`。

> 执行前缀见 `../../invocation.md`；下面示例直接写 `bytedcli`。

## Hive Copilot / Hive Agent 托管诊断

Hive Copilot 是 `bytedcli hive` 下的诊断子能力，不是独立一级 skill。处理 Spark Application 托管诊断、作业对比、性能调优、数据倾斜/Shuffle/资源配置分析，或 CN Spark/Hive 运行时知识问答时，先阅读 `references/copilot.md`。

核心调用形态：

```bash
bytedcli --site cn hive copilot create-session \
  --name "Hive Copilot diagnosis"

bytedcli --site cn hive copilot \
  --session-id sample-session \
  --query "请诊断 application_example_001，分析失败原因并给出修复建议" \
  --max-wait-seconds 3600
```

诊断默认把经过筛选的 SSE 事件计数与活跃时间写到 stderr，最终文本或 JSON 仍写到 stdout；进度不会包含原始事件 payload、工具参数或模型中间正文。需要安静运行时传 `--no-progress`。`i18n-tt` 只支持 SG Application 诊断。首次诊断前必须先显式创建 Session；继续下钻时复用同一个 `--session-id`。

## Search Asset Types

`hive search --type` filters by DataLeap / Coral asset `typeName`.

| Type                      | Description              |
| ------------------------- | ------------------------ |
| `HiveTable`               | Hive tables              |
| `ClickhouseTable`         | Clickhouse tables        |
| `BmqTopic`                | BMQ topics               |
| `RocketmqTopic`           | RocketMQ topics          |
| `DorisTable`              | Doris tables             |
| `ABaseLogicalTable`       | ABase logical tables     |
| `AeolusDashboard`         | Aeolus dashboards        |
| `AeolusDataset`           | Aeolus datasets          |
| `MySQLTable`              | MySQL tables             |
| `FlinkLogicalTable`       | Flink logical tables     |
| `EsIndex`                 | Elasticsearch indexes    |
| `NuwaNgMetric`            | Nuwa metrics             |
| `NuwaNgDimension`         | Nuwa dimensions          |
| `NuwaApplication`         | Nuwa applications        |
| `BPPortal`                | BP portals               |
| `GalleryMetricGroup`      | Gallery metric groups    |
| `DataPowerDataset`        | DataPower datasets       |
| `DataPowerDashboard`      | DataPower dashboards     |
| `Api`                     | APIs                     |
| `LogicalTable`            | Logical tables           |
| `HiveDB`                  | Hive databases           |
| `ClickhouseDB`            | Clickhouse databases     |
| `NuwaNgTheme`             | Nuwa themes              |
| `AeolusDashboardReportV2` | Aeolus dashboard reports |
| `ByteIOEvent`             | ByteIO events            |
| `Term`                    | Terms                    |
| `AeolusMetadataMetric`    | Aeolus metadata metrics  |
| `GaiaPortalSite`          | Gaia portal sites        |
| `DataAlbum`               | Data albums              |
| `AssetAlbum`              | Asset albums             |
| `DataTopics`              | Data topics              |

## Supported Regions

| Region                   | Description      | Endpoint / notes                                                                        |
| ------------------------ | ---------------- | --------------------------------------------------------------------------------------- |
| `cn`                     | China (default)  | data.bytedance.net                                                                      |
| `sg`                     | Singapore ROW    | dataleap-sg.tiktok-row.net                                                              |
| `gcp` / `eu`             | GCP / US-EastRed | API `dataleap.tiktok-eu.net` (cid=5); console `dataleap-gcp.tiktok-row.net`             |
| `eu-compliance2` / `ie2` | IE2              | API `dataleap-gp-ttp-eu.tiktok-eu.net` (cid=31); console `dataleap-ie2…`; auth `eu-ttp` |
| `va`                     | us-east, maliva  | dataleap-va.tiktok-row.net                                                              |
| `mycis`                  | MYCIS            | dataleap-mycis.example.net                                                              |
| `mybd`                   | MYBD             | dataleap-mybd.example.net                                                               |

## Quick start

```bash
# Search for Hive databases
bytedcli hive search --query "my_database" --type HiveDB --region cn

# Search for Hive tables
bytedcli hive search --query "user" --type HiveTable --region gcp

# Get database details
bytedcli hive detail my_database --region cn

# Get table details with full schema and producer Dorado task IDs
bytedcli hive detail my_database my_table --region gcp

# Get CREATE TABLE DDL (columns, types, comments, and partition keys; best for SQL generation)
bytedcli hive ddl my_database my_table --region sg

# Get Doris table details when the Doris namespace / cluster is known
bytedcli hive detail my_database my_doris_table --type DorisTable --namespace doris_demo_cn --region cn

# Get entity details by GUID (from search results)
bytedcli hive get <guid> --region cn

# Get partition row counts for a table (shows total rows and top 20 partitions)
bytedcli hive rows my_database my_table --region cn

# Preview sample data for a Hive table
bytedcli hive preview my_database my_table --region cn
bytedcli hive preview --database my_database --table my_table --limit 20 --region sg

# Query physical storage replicas and cross-region sync distribution for a Hive table
bytedcli hive replicas my_database my_table --region sg
bytedcli hive replicas --database my_database --table my_table --region va

# View data lineage
bytedcli hive lineage <guid> --region cn --depth 3

# Modify table fields (columns) via standard DDL SQL text (supports --dry-run, CASCADE, and RESTRICT)
# Note: Specify CASCADE to cascade column changes to partition metadata, or RESTRICT to update table schema only.
bytedcli hive modify field --ddl "ALTER TABLE demo_db.demo_table REPLACE COLUMNS (id bigint COMMENT 'ID', name string COMMENT 'name') CASCADE;" --region cn --dry-run
bytedcli hive modify field --ddl "ALTER TABLE demo_db.demo_table REPLACE COLUMNS (id bigint COMMENT 'ID', name string COMMENT 'name') RESTRICT;" --region cn

# Modify table fields via DDL SQL file
bytedcli hive modify field --file /path/to/alter.sql --region ie2

# Modify table fields (columns) by GUID with raw JSON (backward-compatible)
bytedcli hive modify field --guid <guid> --fields '[{"typeName":"HiveColumn","name":"col1","dataType":"string","comment":"description"}]' --region cn

# Prefer database/table on IE2 (eu-compliance2); aliases: ie2, eucompliance2.
# Do not pass --partition-keys to modify field: partition keys are immutable here.
bytedcli hive modify field --database demo_db --table demo_table --fields '[{"typeName":"HiveColumn","name":"col1","dataType":"string","comment":"description"}]' --region ie2

# Update table-level attributes through the aggregated entry point
bytedcli hive table update --database demo_db --table demo_table --alias "demo alias" --description "demo description" --business-line demo-line --data-layer demo-layer --data-category demo-category --storage-strategy demo-strategy --ttl 7 --region cn

# List Coral projects that can be bound to a Hive table
bytedcli hive project list --region cn --keyword demo

# Create a new Hive table (fields + partition keys explicit)
bytedcli hive create \
  --database demo_db \
  --table demo_table \
  --ttl 365 \
  --fields '[{"name":"psm","dataType":"string","comment":"service name"},{"name":"qps","dataType":"double","comment":"qps"}]' \
  --partition-keys '[{"name":"date","dataType":"string","comment":"date"}]' \
  --region cn

# IE2 (eu-compliance2): auth with --site eu-ttp; owner + business contact match console form
bytedcli --site eu-ttp auth login
bytedcli hive create \
  --database demo_db \
  --table demo_table \
  --ttl 30 \
  --fields '[{"name":"data","dataType":"string","comment":"data"}]' \
  --partition-keys '[{"name":"date","dataType":"string","comment":"date"}]' \
  --owner demo.owner \
  --business-contact demo.contact \
  -r ie2

# GCP / US-EastRed: same slim create form; auth site i18n-tt (do not use -r ie2)
bytedcli hive create \
  --database demo_db \
  --table demo_table \
  --ttl 30 \
  --fields '[{"name":"test","dataType":"string","comment":"test"}]' \
  --partition-keys '[{"name":"date","dataType":"string","comment":"date"}]' \
  --owner demo.owner \
  --business-contact demo.contact \
  -r gcp

# US-TTP (Texas, cid=9): slim create form under Texas OG; non-US operators bind US compliance owner
bytedcli hive create \
  --database demo_db \
  --table demo_table \
  --ttl 30 \
  --fields '[{"name":"data","dataType":"string","comment":"data"}]' \
  --partition-keys '[{"name":"p_date","dataType":"string","comment":"partition date"}]' \
  --owner demo.us_owner \
  --business-contact demo.real_user \
  --specified-real-user demo.real_user \
  -r us-ttp

# Create a new Hive table from DDL (fields and partition keys parsed automatically)
bytedcli hive create \
  --database demo_db \
  --table demo_table \
  --ttl 365 \
  --ddl "CREATE TABLE IF NOT EXISTS \`demo_db\`.\`demo_table\` (\`psm\` string COMMENT 'psm') PARTITIONED BY (\`date\` string COMMENT 'date')" \
  --region cn

# Create a bucketed Hive table from raw DDL. DDL mode preserves CLUSTERED BY,
# SORTED BY, bucket count, SerDe, and other engine-specific clauses verbatim.
bytedcli hive create \
  --database demo_db \
  --table demo_bucketed_table \
  --ttl 7 \
  --region sg \
  --ddl $'CREATE TABLE `demo_db`.`demo_bucketed_table` (\n  `id` STRING COMMENT \'id\',\n  `col1` BIGINT COMMENT \'value\'\n) PARTITIONED BY (`date` STRING COMMENT \'date\')\nCLUSTERED BY (`id`)\nSORTED BY (`id` ASC)\nINTO 128 BUCKETS\nROW FORMAT SERDE \'org.apache.hadoop.hive.ql.io.parquet.serde.ParquetHiveSerDe\''

# Create a new Doris table from raw DDL
bytedcli hive create \
  --database demo_db \
  --table demo_doris_table \
  --type DorisTable \
  --namespace doris_demo_cn \
  --alias "demo table" \
  --ddl "$(cat /tmp/demo_doris.sql)" \
  --region cn
```

## Notes

- 只改普通 Hive 非分区列说明时，优先使用 `bytedcli coral hive table update --region cn --db-name example_db --table-name example_table --column-comments '{"sample_col":"字段说明"}'`。默认预览，获得写入授权后加 `--yes`，无需自行构造完整字段数组。该命令会保留 schema、补齐缺失的安全标签 CID，并在单次提交后回读 Coral 元数据；分区列说明暂不支持。原 `hive modify field` 同样会修正安全标签缺失/NULL 的 CID，显式数值 CID 保持不变。

- Use `--json` for structured JSON output
- Default region is `cn` if not specified
- Default asset type for search is `HiveDB`
- `hive detail --type` is intentionally narrower than `hive search --type`; detail supports `HiveDB`, `HiveTable`, `ClickhouseDB`, `ClickhouseTable`, and `DorisTable`.
- The `detail` and `get` commands show full schema including column names, types, comments, and producer Dorado task IDs when upstream lineage contains `DoradoTask`.
- `hive detail <db> <table>` defaults to `HiveTable`. If the Hive asset is missing, the CLI searches exact `ClickhouseTable` / `DorisTable` candidates for the same database and table name, auto-uses a unique match, and reports retry commands when multiple non-Hive assets match.
- For exact Doris metadata lookup, pass `--type DorisTable --namespace <doris_namespace>`. Doris qualified names use `DorisTable:///{namespace}/{database}/{table}@{cid}`, so type alone is not always enough to build the exact lookup path.
- The `rows` command shows the total row count and the top 20 partitions by row count
- Lineage shows upstream and downstream data dependencies
- The `modify field` command updates field definitions; pass `--guid` or `--database` + `--table`, and use `--fields` for the full non-partition column array as JSON. Each item must use `typeName: "HiveColumn"` and `dataType` (not `type`). Do not pass `--partition-keys`: the Hive fields endpoint does not support partition-key mutation, and malformed partition-key objects can clear the table's partition definition. Get the current fields first via `hive detail <db> <table>` (preferred on IE2 / `eu-compliance2`, where `hive get <guid>` may hit OG schema 403 on `/entities/{guid}`), then submit the updated array. For IE2 auth use `bytedcli --site eu-ttp auth login`; region aliases include `ie2` / `eucompliance2`. GCP (`-r gcp`) is US-EastRed on `dataleap.tiktok-eu.net` (cid=5), not IE2 — do not reuse `-r ie2` for GCP console tables. `--business-contact` applies on restricted create forms and on Hive DDL-mode create.
- Use `hive table update` for table-level metadata updates.
- `hive table update` does not use empty strings to clear text fields. `--alias`, `--description`, and `--project` must be non-empty when provided. For `--data-category`, empty or whitespace-only entries are ignored rather than treated as clear.
- Use `hive project list` before `hive table update --project <name>` when you need to discover the exact Coral project name in the current region.
- The `create` command requires `--database` and `--table`; `--ttl` is required for `HiveTable` but not for `DorisTable`.
- For `HiveTable`, fields/partition-keys can be provided via `--fields`/`--partition-keys` (JSON arrays) or derived automatically from `--ddl`. DDL mode preserves the supplied SQL verbatim, including Hive-specific clauses such as `CLUSTERED BY`, `SORTED BY`, `INTO ... BUCKETS`, SerDe, and `TBLPROPERTIES`.
- For `DorisTable`, use `--type DorisTable --namespace <name> --ddl <sql>`. Doris creation submits the raw DDL directly and does not use Hive field parsing or the Hive explain endpoint.
- When passing Doris DDL that contains backticks or multiple lines, prefer loading it from a file, e.g. `--ddl "$(cat /tmp/demo_doris.sql)"`, to avoid shell command substitution corrupting the SQL.
- Owner defaults to the current SSO user.
- Before submitting a `HiveTable`, `create` performs local schema checks and server-side DDL validation via `POST /bridge/hive/explain`. When `--ddl` is used, it additionally runs the Coral table check before creating the table; all checks receive the exact supplied DDL.
- A `code=0` response from `management/data-store` only means the asynchronous request was accepted. `hive create` first proves the exact target is absent, then waits for a bounded, route-affine `data-stores` readback and reports success only after the table materializes. `HIVE_CREATE_STATE_INDETERMINATE` means the bounded check could not verify the final state; do not resubmit until a read-only detail or platform job check proves the table is absent.

## References

- `references/hive.md`
- `references/copilot.md`
- `../../invocation.md`
