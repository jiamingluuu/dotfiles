# Query Editor

Router: this skill's SKILL.md (named GUIDE.md in the bytedcli mirror). This file is the command body for Query Editor folders, files, templates, temporary tables, tasks, engines, and QE auth. Do not treat [aeolus.md](aeolus.md) as command body.

Ad-hoc SQL under `aeolus query-editor`. Uses QE HTTP APIs under `{baseUrl}/qe/v2/api/...` from the region map in `src/api/aeolus/site.ts`. CN Query Editor uses `https://data.bytedance.net` in both office and production-network profiles because the production CN dataset gateway does not expose the QE path; SG/VA follow their selected network profile host.

Query Editor does not support region-specific `ClientID/ClientSecret`. It defaults to `cn`; pass `-r/--region` to switch. For `hrbimycis`, use `aeolus viz-query` in [dataset.md](dataset.md) instead of Query Editor or `aeolus query`.

**Hive yarn defaults:** the Hive `run` body's `yarn.{cluster_id, idc}` is derived per region, and a mismatch is accepted with `code:0` but never scheduled onto a worker. Known non-default mappings: `sglark` → `shark` / `SGSAAS1LARKIDC1`, `usttpusts` → `default` / `USEAST5`, `eupipo` → `default` / `IE2`, `euttp2` → `wyodel01` / `NO1A` (queue `root.bytecloud_batch_no1a`); everything else defaults to `default` / `LF`. `--idc` overrides the idc; `cluster_id` is always region-derived.

**QE App ID:** Request header `x-qe-appid` defaults from `QE_APP_ID` or `BYTEDCLI_AEOLUS_QE_APP_ID` (CLI default in code if unset). Match the **Query Editor page URL `appId=`** when reproducing browser runs.

## Table of contents

- [EU-TTP (euttp) and US-TTP (usttpusts)](#eu-ttp-euttp-and-us-ttp-usttpusts)
- [EU-TTP2 / NO1A (euttp2)](#eu-ttp2--no1a-euttp2)
- [Query Editor authentication](#query-editor-authentication)
- [Query Editor quick start](#query-editor-quick-start)
- [Query Editor: Hive 日期占位符与多日 batch 查询](#query-editor-hive-日期占位符与多日-batch-查询)
- [Query Editor: HTTP 406 解码](#query-editor-http-406-解码)
- [Recommended usage: query one vs full Query Editor workflow](#recommended-usage-query-one-vs-full-query-editor-workflow)
- [Query Editor command structure](#query-editor-command-structure)
- [aeolus query-editor tmp-table create](#aeolus-query-editor-tmp-table-create)
- [aeolus query-editor folder cleanup-temp](#aeolus-query-editor-folder-cleanup-temp)
- [aeolus query-editor query run](#aeolus-query-editor-query-run)
- [aeolus query-editor query parse](#aeolus-query-editor-query-parse)
- [aeolus query-editor query status](#aeolus-query-editor-query-status)
- [aeolus query-editor query logs](#aeolus-query-editor-query-logs)
- [aeolus query-editor query cancel](#aeolus-query-editor-query-cancel)
- [aeolus query-editor task rename](#aeolus-query-editor-task-rename)
- [aeolus query-editor task delete](#aeolus-query-editor-task-delete)
- [aeolus query-editor task result](#aeolus-query-editor-task-result)
- [aeolus query-editor query one](#aeolus-query-editor-query-one)
- [ClickHouse example (align with browser QE)](#clickhouse-example-align-with-browser-qe)
- [Custom datasource example (user-defined DORIS etc.)](#custom-datasource-example-user-defined-doris-etc)
- [aeolus query-editor template](#aeolus-query-editor-template)
- [aeolus query-editor login](#aeolus-query-editor-login)

### EU-TTP (`euttp`) and US-TTP (`usttpusts`)

|                    | US-TTP (`usttpusts`)        | EU-TTP (`euttp`)                                      |
| ------------------ | --------------------------- | ----------------------------------------------------- |
| Cloud site         | `--site us-ttp-usts`        | `--site eu-ttp`                                       |
| Office Aeolus host | `aeolus-tx.tiktok-usts.net` | `aeolus-eu-ttp.tiktok-eu.net`                         |
| Query Editor `-r`  | `usttpusts`                 | `euttp`                                               |
| Primary auth       | Compliance product session  | EU-scoped Titan Passport from `do.tiktok-eu.net`      |
| Login prerequisite | `aeolus query-editor login` | `bytedcli --site eu-ttp auth login`                   |
| Product fallback   | Required session path       | `aeolus query-editor login` only if Titan is rejected |

Do not reuse a ROW `i18n-tt` Titan Passport for EU-TTP. `euttp` exchanges against the EU issuer and scopes the cookie to the EU Aeolus host.

### EU-TTP2 / NO1A (`euttp2`)

`euttp2` is a separate EU deployment behind the NO1A gateway `aeolus-no.tiktok-eu.net`. It shares the `eu-ttp` cloud site with `euttp` but is **not** interchangeable with it: the two resolve to different clusters and different Hive catalogs, so a table that exists in one may not exist in the other.

|                   | EU-TTP (`euttp`)                | EU-TTP2 (`euttp2`)                    |
| ----------------- | ------------------------------- | ------------------------------------- |
| Query Editor `-r` | `euttp`                         | `euttp2` (aliases `eu-ttp2` / `no1a`) |
| Aeolus host       | `aeolus-eu-ttp.tiktok-eu.net`   | `aeolus-no.tiktok-eu.net`             |
| Cloud site        | `--site eu-ttp`                 | `--site eu-ttp` (same)                |
| Titan issuer      | `do.tiktok-eu.net` (`clover/`)  | `do-no.tiktok-eu.net` (`no/`)         |
| Default Hive yarn | `cluster_id` per region default | `cluster_id=wyodel01`, `idc=NO1A`     |
| Typical queue     | `root.bytecloud_trade`          | `root.bytecloud_batch_no1a`           |
| Origin override   | `BYTEDCLI_AEOLUS_EUTTP_ORIGIN`  | `BYTEDCLI_AEOLUS_EUTTP2_ORIGIN`       |

```bash
# euttp2 needs no extra login beyond the eu-ttp ByteCloud JWT
bytedcli --site eu-ttp auth login
bytedcli aeolus query-editor whoami -r euttp2
bytedcli aeolus query-editor queues -r euttp2
bytedcli aeolus query-editor query one -r euttp2 --queue root.bytecloud_batch_no1a --sql "SELECT 1"
```

Agent Guidance:

- **The NO1A gateway only accepts a `no/`-prefixed `titan_passport_id`.** The issuer used by `euttp` (`do.tiktok-eu.net`) mints `clover/...`, which NO1A rejects with HTTP 401 `[Titan] Invalid Params: Invalid titan_passport_id`. A new Aeolus host of this kind therefore needs its **host and Titan issuer added as a pair** — pointing an existing region's origin at the new host is not enough.
- `euttp2` authenticates with the ordinary `--site eu-ttp` ByteCloud JWT. It is **not** a session-auth region: do not run `aeolus query-editor login` for it, and do not expect `BYTEDCLI_AEOLUS_COOKIE` (that variable is bound to `usttpusts` only).
- Hive `run` on `euttp2` derives `yarn.cluster_id=wyodel01` / `idc=NO1A`. A mismatched cluster/idc is accepted with `code:0` but never gets a worker, so the task silently never finishes. `--idc` can override the idc; `cluster_id` is always derived from the region.
- `euttp` and `euttp2` are different data planes. Confirm which one actually holds the table before concluding data is missing: the same query can return `SEMANTIC_ERROR ... not found` on one and succeed on the other (their SQL engines report different catalog prefixes).

### Query Editor authentication

```bash
# One-time login
bytedcli auth login

# EU-TTP: EU-scoped Titan Passport (primary)
bytedcli --site eu-ttp auth login

# Query Editor on mycis / mybd / usbd
bytedcli --site i18n-bd auth login --session

# EU-TTP fallback only when Titan Passport is rejected
bytedcli --site eu-ttp aeolus query-editor login

# US-TTP compliance product session
bytedcli --site us-ttp-usts aeolus query-editor login

# Headless/agent fallback after a trusted runtime injects the Aeolus Cookie secret
bytedcli aeolus query-editor whoami -r usttpusts
```

`query-editor login` defaults to `--mode password`: it prompts your SSO username/password/OTP in the terminal and signs in over HTTP, so it works over SSH / headless hosts with no browser window. If password mode cannot establish a session (for example the compliance gateway requires an interactive sign-in), retry with `--mode browser`, which opens a temporary browser window on the compliance host. That window starts from a copy of your signed-in Chromium profile, so it is usually already logged in and finishes on its own.

For `usttpusts`, `BYTEDCLI_AEOLUS_COOKIE` has priority over the local session jar. Its value is the complete `Cookie` request-header value from an authenticated Query Editor browser request, without the `Cookie:` prefix. bytedcli binds it to the built-in `usttpusts` HTTPS origin, validates it against `/qe/v2/api/user`, never persists it, and fails closed when it is malformed, expired, or rejected. Other regions ignore this variable.

A human or managed secret store must inject the Cookie outside the Agent conversation. Agents must never request, paste, echo, log, or place the value in argv, scripts, skill files, or repositories. For a local interactive shell, paste it through a hidden `read -rs BYTEDCLI_AEOLUS_COOKIE` prompt, then `export` the variable; unset it after the command. Managed Agent runtimes should use their secret environment injection mechanism.

For `euttp`, the CLI first verifies the EU-scoped Titan Passport against `/qe/v2/api/user`, refreshes it once if needed, then tries an existing compliance product session. For `euttp2`, the CLI verifies the NO1A-scoped Titan Passport (`do-no.tiktok-eu.net`) the same way; there is no product-session fallback to run for it, so a persistent failure there means the `--site eu-ttp` JWT itself is missing or invalid. For `mycis`, `mybd`, and `usbd`, make sure the `i18n-bd` browser session is ready first. For `usttpusts`, use `query-editor login` on `aeolus-tx.tiktok-usts.net`, or use the injected session in headless/agent execution. For `hrbimycis`, use `aeolus viz-query` instead of Query Editor or `aeolus query`.

For `eupipo`, use `bytedcli --site eu-ttp auth login`; if Aeolus still returns a product-login page, run `bytedcli --site eu-ttp auth login --session --auto --yes` once to seed the Clover/PIPO product cookie, then retry with `-r eupipo`.

### Query Editor quick start

```bash
# Check current user
bytedcli aeolus query-editor whoami
bytedcli aeolus query-editor whoami --region sg

# Folder management
bytedcli aeolus query-editor folder list
bytedcli aeolus query-editor folder list --region va
bytedcli aeolus query-editor folder tree
bytedcli aeolus query-editor folder create --name "my-queries"
bytedcli aeolus query-editor folder cleanup-temp --region mycis --dry-run
bytedcli aeolus query-editor folder cleanup-temp --region mycis --keep-id <folderId> --yes

# File management
bytedcli aeolus query-editor file create --name "test" --folder-id 123
bytedcli aeolus query-editor file write-sql --file-id 456 --sql "SELECT 1"
bytedcli aeolus query-editor file search --keyword "test"

# SQL execution
bytedcli aeolus query-editor queues
bytedcli aeolus query-editor query parse --sql "SELECT 1"
bytedcli aeolus query-editor query run --file-id 456 --folder-id 123 --queue <your_queue> --sql "SELECT 1"
bytedcli aeolus query-editor query run --file-id 456 --folder-id 123 --queue <your_queue> --file ./queries/demo.sql
# Direct Feishu sheet export or CSV download from query run
bytedcli aeolus query-editor query run --file-id 456 --folder-id 123 --queue <your_queue> --sql "SELECT 1" --feishu
bytedcli aeolus query-editor query run --file-id 456 --folder-id 123 --queue <your_queue> --sql "SELECT 1" --output ./result.csv
# Multi-day Hive batch date range: keep the ${date} placeholder in SQL; QE expands one task per date.
bytedcli aeolus query-editor query run --file-id 456 --folder-id 123 --queue root.demo_queue \
  --sql "SELECT id FROM demo_db.sample_table WHERE date = '\${date}'" \
  --batch-start-date 2026-08-06 --batch-end-date 2026-08-12 --batch-concurrency 7
# One-shot temp query can run the same multi-day batch without explicit file/folder IDs.
bytedcli aeolus query-editor query one --queue root.demo_queue \
  --sql "SELECT id FROM demo_db.sample_table WHERE date = '\${date}'" \
  --batch-start-date 2026-08-06 --batch-end-date 2026-08-12 --batch-concurrency 7
# Single-day query date: keep ${date}/${DATE} in SQL; QE uses --adhoc-date from the request.
bytedcli aeolus query-editor query run --file-id 456 --folder-id 123 --queue root.demo_queue \
  --sql "SELECT id FROM demo_db.sample_table WHERE date = '\${date}'" \
  --adhoc-date 2026-08-12
bytedcli aeolus query-editor query status --task-id 789 --file-id 456 --folder-id 123
bytedcli aeolus query-editor query logs --task-id 789
bytedcli aeolus query-editor query cancel --task-id 789

# Task result & export: get results, export to Feishu sheet, or download CSV
bytedcli aeolus query-editor task result --task-id 789
bytedcli aeolus query-editor task result --task-id 789 --feishu
bytedcli aeolus query-editor task result --task-id 789 --output ./result.csv

# Task record management: rename tasks and dry-run/delete noisy records
bytedcli aeolus query-editor task rename --task-id 789 --name "sample-task-name"
bytedcli aeolus query-editor task delete --task-id 789
bytedcli aeolus query-editor task delete --task-id 789 --yes

# One-shot query (auto-creates file, runs SQL, returns results, supports --feishu / --output)
bytedcli aeolus query-editor query one --queue <your_queue> --sql "SELECT 1"
bytedcli aeolus query-editor query one --queue <your_queue> --file ./queries/demo.sql
bytedcli aeolus query-editor query one --queue <your_queue> --sql "SELECT 1" --feishu
bytedcli aeolus query-editor query one --queue <your_queue> --sql "SELECT 1" --output ./out.csv
# Submit without polling; JSON includes engine, taskId, fileId, folderId, status, and taskUrl.
bytedcli --json aeolus query-editor query one --queue <your_queue> --sql "SELECT 1" --no-wait

# Custom datasource (user-defined, e.g. DORIS): list sources, then query (no --queue)
export QE_APP_ID=<yourWorkspaceAppId>   # custom datasources are appId-scoped
bytedcli aeolus query-editor datasources
# by name (resolved to id+type via the datasources list):
bytedcli aeolus query-editor query one --engine datasource --datasource-name <datasourceName> --sql "select * from sample_db.sample_tbl limit 10"
# or directly by id+type (works without the workspace appId):
bytedcli aeolus query-editor query one --engine datasource --datasource-id <datasourceId> --datasource-type DORIS --sql "select * from sample_db.sample_tbl limit 10"
```

### Query Editor: Hive 日期占位符与多日 batch 查询

Hive `query run` 和 `query one` 都支持 `--sql` 内联 SQL 或 `--file` 读取本地 SQL 文件；两者同时提供时 `--file` 优先。SQL 中可保留 `${date}` 或 `${DATE}` 占位符：`--adhoc-date` 是单日日期便捷参数，CLI 会把日期放进 QE run 请求体，SQL 文本保持原样；QE 后端会按同日 `range` 执行占位符替换。`--batch-start-date` / `--batch-end-date` 会提交 QE 多日 `query_type=BATCH`，由 QE 按日期展开子任务。`--batch-concurrency <N>` 只适用于多日 BATCH，会写入 QE `max_tasks`，取值 `1-120`；省略时默认使用 `min(日期天数, 120)`。`query one` 会自动复用/创建 `_bytedcli_temp` 目录和临时文件，因此不需要显式传 `--file-id` / `--folder-id`。两个命令默认等待执行结束；传 `--no-wait` 时会在提交后立即返回，JSON 输出包含后续查询状态所需的 `engine`、`taskId`、`fileId`、`folderId` 和 `taskUrl`。不传任何日期参数时保持普通 `ADHOC` 查询体验；如果 SQL 写死了日期而没有 `${date}` / `${DATE}`，日期参数不会报错，但基本不会改变查询结果。

```bash
bytedcli aeolus query-editor query run --file-id 456 --folder-id 123 --queue root.demo_queue \
  --sql 'SELECT id FROM demo_db.sample_table WHERE date = '\''${date}'\''' \
  --batch-start-date 2026-08-06 --batch-end-date 2026-08-12 --batch-concurrency 7

bytedcli aeolus query-editor query one --queue root.demo_queue \
  --sql 'SELECT id FROM demo_db.sample_table WHERE date = '\''${date}'\''' \
  --batch-start-date 2026-08-06 --batch-end-date 2026-08-12 --batch-concurrency 7

bytedcli aeolus query-editor query run --file-id 456 --folder-id 123 --queue root.demo_queue \
  --sql 'SELECT id FROM demo_db.sample_table WHERE date = '\''${date}'\''' \
  --adhoc-date 2026-08-12
```

日期占位符参数仅支持默认 Hive runner；`--engine ch` 或 `--engine datasource` 请移除这些参数。`--batch-start-date` 与 `--batch-end-date` 必须至少跨 2 天；同一天请改用 `--adhoc-date`。多日批量提交会生成父任务和按日期展开的子任务，后续仍使用父 `taskId` 查询状态和预览合并结果。预览结果可能被 `--rows` 截断，JSON 输出里的 `rowCount`、`returnedRows`、`truncated` 用来判断是否需要改用下载或调大预览上限。

### Query Editor: `HTTP 406` 解码

`query run` / `query one` 报 **`HTTP 406`** 时，先保留本次响应、错误码和任务标识，不要仅凭状态码判断原因。

**Hive** 可检查所查表的权限，以及 YARN `--queue` / `--idc` 是否与目标机房匹配；这些不是 CH 自动模式的必填参数。

**CH** 的 406 不能唯一归因于权限、集群名或 region。若已有 task ID，使用同一 `-r` / `--engine ch` 的 `query status` 只读确认；任务状态不明时不重提 SQL、不换集群。确需进一步执行验证时，须另行确认，仅用 `SELECT 1 AS test_value;`，不要为获取调试日志直接重跑业务 SQL。

### Recommended usage: `query one` vs full Query Editor workflow

- Use `aeolus query-editor query one` for one-off or exploratory SQL where you only need to run a small number of temporary queries quickly.
- If historical one-shot runs created many `_bytedcli_temp` folders, use `aeolus query-editor folder cleanup-temp` first with `--dry-run`, then rerun with `--yes` after confirming the retained folder ID.
- Use the full Query Editor workflow when you are analyzing one system or topic and expect multiple related SQL queries over time.
- The full workflow avoids creating a new temporary folder on every query, lets you reuse the same folder/file IDs, and keeps related SQL under one theme directory so you can search and review query history later.
- In the full workflow, prefer passing SQL directly to `query run --sql ...` or `query run --file ...`. Writing SQL into the file first is optional, not required for execution.
- Under the hood, both `query run --sql ...` and `query run --file ...` call the same Query Editor `run` API with the same `page_id` / `block_id`; **Hive** (default) sends `yarn` queue fields, while **`--engine ch`** uses platform automatic cluster selection unless a cluster is specified. The only difference between `--sql` and `--file` is where `query` / `query_template` text comes from.
- A practical organization pattern is: create one folder for the overall analysis theme, create multiple files for different sub-scenarios under that theme, and then reuse the same `file-id` for multiple `query run` executions when one sub-scenario needs several SQL variants.
- Rename submitted tasks with `aeolus query-editor task rename` so task history makes the SQL purpose clear when several runs live in the same file.
- When the user explicitly wants to cancel or remove noisy Query Editor tasks, first capture the task status fields that preserve lower-level history (`runtime_info.application_id`, `runtime_info.execute_id`, `runtime_info.tracking_url_list`, `query_id`, and the SQL), then run `aeolus query-editor task delete --task-id <taskId> --yes` to keep the Query Editor folder clean.
- Deleting a Query Editor task removes the QE task record/status entry; lower-level Presto/TQS/Spark history may still be reachable only through identifiers captured before deletion.
- In that model, `folder-id` is the theme container, and `file-id` is closer to a reusable query context for one sub-scenario than a hard binding to exactly one SQL statement.

Recommended persistent workflow:

```bash
# 1) Create or reuse a theme folder once
bytedcli aeolus query-editor folder create --name "demo-analysis"

# 2) Create one or more query files inside that folder
bytedcli aeolus query-editor file create --name "partitions" --folder-id 123
bytedcli aeolus query-editor file create --name "daily-sample" --folder-id 123
bytedcli aeolus query-editor file create --name "rootcause-drilldown" --folder-id 123

# 3) Run queries against the same reusable file/folder IDs
bytedcli aeolus query-editor query run --file-id 456 --folder-id 123 --queue <your_queue> --sql "SHOW PARTITIONS demo_db.sample_table"
bytedcli aeolus query-editor query run --file-id 457 --folder-id 123 --queue <your_queue> --sql "SELECT * FROM demo_db.sample_table WHERE date = '20260412' LIMIT 100"
bytedcli aeolus query-editor query run --file-id 457 --folder-id 123 --queue <your_queue> --file ./queries/daily-sample.sql
bytedcli aeolus query-editor query run --file-id 458 --folder-id 123 --queue <your_queue> --sql "SELECT protocol, date FROM demo_db.sample_events WHERE date = '20260412' LIMIT 10"
bytedcli aeolus query-editor query run --file-id 458 --folder-id 123 --queue <your_queue> --sql "SELECT to_service, count(*) FROM demo_db.sample_events WHERE date = '20260412' GROUP BY to_service LIMIT 20"

# 4) Optionally persist SQL into the file body for later viewing/editing in Query Editor UI
bytedcli aeolus query-editor file write-sql --file-id 456 --sql "SHOW PARTITIONS demo_db.sample_table"
bytedcli aeolus query-editor file write-sql --file-id 457 --sql "SELECT * FROM demo_db.sample_table WHERE date = '20260412' LIMIT 100"

# 5) Inspect task status / logs, rename meaningful task records, and search historical SQL files later
bytedcli aeolus query-editor query status --task-id 789 --file-id 456 --folder-id 123
bytedcli aeolus query-editor query logs --task-id 789
bytedcli aeolus query-editor task rename --task-id 789 --name "partition-check-sample"
bytedcli aeolus query-editor query cancel --task-id 789
# Before deleting a noisy task, record runtime_info.application_id / execute_id / tracking_url_list from status.
bytedcli aeolus query-editor task delete --task-id 789 --yes
bytedcli aeolus query-editor file search --keyword "demo-analysis"
```

Notes:

- `query one` is optimized for convenience, not long-term organization.
- `query run` should include `--sql` or `--file` when you want to execute against an existing `file-id` / `folder-id`.
- For repeated analysis, prefer naming folders by topic/system (for example `demo-analysis`, `demo-metrics-debug`, `demo-dashboard-rootcause`).
- Query Editor commands default to `cn`, and support `-r/--region` to switch host/domain consistently with Aeolus dataset/report APIs.

### Query Editor command structure

```
aeolus query-editor
  ├── whoami / queues / datasources
  ├── folder   list|tree|create|rename|move|delete|cleanup-temp
  ├── file     get|create|write-sql|rename|move|delete|search
  ├── tmp-table create
  ├── template list|get
  ├── task     rename|delete|result
  └── query    parse|run|status|logs|cancel|one
```

Command option tables, ClickHouse / custom-datasource examples, tmp-table flags, and template API details follow.

---

### `aeolus query-editor tmp-table create`

Upload a local CSV file, preview the inferred schema, and create a Query Editor temporary table. The command defaults to dry-run and only previews the upload / preview / create plan. Pass `--yes` to execute the browser flow: `POST /tmp_table/upload?db_name=...` (multipart `file`) → `POST /tmp_table/preview` → `POST /tmp_table/create`.

```bash
bytedcli aeolus query-editor tmp-table create \
  --file ./sample.csv \
  --table-name demo_tmp \
  --db-name facade_qe_tmp_table \
  --ttl 30 \
  --delimiter ','

bytedcli aeolus query-editor tmp-table create \
  --file ./sample.tsv \
  --table-name demo_tmp_tsv \
  --delimiter $'\t' \
  --ttl 7 \
  --yes
```

- `--file <path>` and `--table-name <name>` are required.
- `--db-name` defaults to `facade_qe_tmp_table`.
- `--ttl` defaults to `30` days.
- `--delimiter` defaults to comma; use `$'\t'` for TSV.
- The default is dry-run. Pass `--yes` to upload and create the table.
- `--idc` defaults to `LF`; pass `--overwrite` with `--yes` to send `over_write:true`.
- The command reuses Query Editor auth and `x-qe-appid`; set `QE_APP_ID` / `BYTEDCLI_AEOLUS_QE_APP_ID` to the page `appId=` when creating temp tables in a non-default workspace.

### `aeolus query-editor folder cleanup-temp`

Clean duplicate Query Editor temp folders, primarily historical `_bytedcli_temp` folders created by one-shot queries. The command is a write operation and defaults to dry-run.

```bash
bytedcli aeolus query-editor folder cleanup-temp -r mycis --dry-run
bytedcli aeolus query-editor folder cleanup-temp -r mycis --keep-id <folderId> --yes
```

**Options:** `-r/--region`, `--name <name>` (default `_bytedcli_temp`), `--keep-id <id>`, `--dry-run`, `--yes`, `--include-non-empty`.

Default behavior: keep the most recently updated matching folder, delete only empty duplicates, and skip non-empty folders. Pass `--keep-id` to choose the retained folder explicitly. Pass `--include-non-empty` only after inspecting the dry-run output.

### `aeolus query-editor query run`

```bash
bytedcli aeolus query-editor query run [options]
```

**Required (soft-required by CLI):**

- `--file-id <id>` — Query file (`block_id` in API body)
- `--folder-id <id>` — Folder (`page_id` in API body)

**Common options:**

- `-r, --region <region>` — `cn` | `sg` | `va` | `euttp` | `euttp2` | `eupipo` | `mycis` | `mybd` | `sglark` | `usttpusts` | `usbd` (default `cn` if omitted)
- `--sql <sql>` — Inline SQL
- `--file <path>` — SQL from disk (if neither `--sql` nor `--file`, CLI may read SQL from the file record)
- `--queue <name>` — **Hive (default): required.** YARN queue name in `yarn.queue` (use `aeolus query-editor queues` to list). **CH (`--engine ch`):** maps to `cluster_name` unless `--cluster-name` is set. **datasource (`--engine datasource`): not used.**
- `--idc <idc>` — **Hive only:** IDC in `yarn.idc`
- `--engine <engine>` — `hive` (default), `ch` (ClickHouse runner: `/ch/task/run`), or `datasource` (user-defined datasource e.g. DORIS: `/datasource/task/run`)
- `--cluster-name <name>` — **CH only:** takes precedence over `--queue`. Omit both for platform automatic selection, or pass `automatically` (case-insensitive, ignoring surrounding whitespace) to select automatic mode even when `--queue` is set. The automatic alias is never sent as a cluster name.
- `--ch-region <code>` — **CH only:** explicit request body `region` (e.g. `VA`), preserved in both automatic and explicit-cluster modes. If omitted, derived from `-r` only for an explicit cluster; automatic mode omits it. This flag does not select the Aeolus site.
- `--datasource-id <id>` — **datasource only:** `datasource_id` from `aeolus query-editor datasources` (e.g. a user-defined DORIS source). Required unless resolved from `--datasource-name`
- `--datasource-type <type>` — **datasource only:** `datasource_type`, e.g. `DORIS`. Required unless resolved from `--datasource-name`
- `--datasource-name <name>` — **datasource only:** resolve `datasource_id` + `datasource_type` by name via `aeolus query-editor datasources`. Needs `QE_APP_ID` set to your Query Editor workspace appId (custom datasources are appId-scoped). `--datasource-id` takes precedence when both are given
- `--adhoc-date <date>` — **Hive only:** set one query date (`YYYY-MM-DD`) for SQL placeholders such as `${date}` or `${DATE}` without changing the SQL text
- `--batch-start-date <date>` / `--batch-end-date <date>` — **Hive only:** submit a multi-day QE batch date range (`YYYY-MM-DD`, inclusive; must span at least two dates)
- `--batch-concurrency <N>` — **Hive only:** multi-day QE batch concurrency, sent as `max_tasks` (`1-120`; default `min(date count, 120)`)
- `--output <path>` — Download and save query results as a CSV file to `<path>` upon completion
- `--feishu` — Export query results directly to a Feishu/Lark online spreadsheet upon completion (automatically cleans Hive `"NULL"` / `"\\N"` string literals into empty string `""`)
- `--no-wait` — Submit only; do not poll
- `--rows <N>` — Poll/display row cap for status polling path
- `--timeout <seconds>` — Poll timeout

**Engines:**

| `--engine`       | Submit URL suffix      | Body highlights                                                                                                                          |
| ---------------- | ---------------------- | ---------------------------------------------------------------------------------------------------------------------------------------- |
| `hive` (default) | `/hive/task/run`       | `query_type`: `ADHOC` by default or `BATCH` with `range` and `max_tasks` for date placeholder runs; `yarn`: `queue`, `idc`, `cluster_id` |
| `ch`             | `/ch/task/run`         | `page_id`, `block_id`, `query`, `query_template`, `task_name`, `template_conf`; optional `cluster_name`, `region`                       |
| `datasource`     | `/datasource/task/run` | `datasource_id`, `datasource_type`, `page_id`, `block_id`, `query`, `query_template`, `task_name`, `template_conf`                       |

For **`ch`**, automatic mode omits `cluster_name` and, unless `--ch-region` is explicit, `region`. Explicit clusters retain the site-derived region default (for example, `-r euttp` gives body `region=EU`). **EU GCP uses `-r euttp`**: omitting body `region` does not change the Aeolus site, and the CLI never falls back to another site or cluster. `query-editor queues` lists **Hive YARN queues**, not CH clusters.

Submission failures (including HTTP 406), network errors, missing task IDs, and unknown task states do not trigger another SQL submission. The existing exception is a clear HTTP 401: refresh authentication and retry once at the same site. If polling times out, use `query status` with the returned task ID and the same `-r` / `--engine`; do not resubmit SQL while its state is unknown.

For **`datasource`**, identify the source either by **`--datasource-id` + `--datasource-type`** directly, or by **`--datasource-name`** (resolved to id+type via `aeolus query-editor datasources`). No `--queue` / `--idc` is sent. Custom datasources only appear in the list — and name resolution only works — when **`QE_APP_ID`** matches the Query Editor workspace that owns the source (see below).

**Hive date placeholders:** pass `--adhoc-date` for one date; the CLI keeps SQL text unchanged and sends the date through the QE run request as a same-day `range` with `max_tasks=1` so QE can expand `${date}` / `${DATE}`. SQL that already contains `${date}` or `${DATE}` can be used as-is; no source SQL rewrite is needed. If the SQL has no date placeholder and uses a fixed literal, `--adhoc-date` and batch date options are still accepted but usually do not change the query result. Pass `--batch-start-date` + `--batch-end-date` only for a multi-day inclusive range; then the CLI sends `query_type:"BATCH"`, `range.start_date`, `range.end_date`, and `max_tasks` from `--batch-concurrency` or the default `min(date count, 120)`. If date options are omitted, the request remains the legacy `query_type:"ADHOC"` and no date/range fields are sent. Date placeholder options are rejected for `--engine ch` and `--engine datasource`; same-day start/end ranges are rejected and should use `--adhoc-date` instead.

```bash
# Multi-day Hive batch: QE expands ${date}; max_tasks controls batch concurrency.
bytedcli aeolus query-editor query run --file-id <fileId> --folder-id <folderId> --queue root.demo_queue \
  --sql "SELECT id FROM demo_db.sample_table WHERE date = '\${date}'" \
  --batch-start-date 2026-08-06 --batch-end-date 2026-08-12 --batch-concurrency 7

# Single-day query date: keep ${date}/${DATE} in SQL; --adhoc-date is sent through the QE request.
bytedcli aeolus query-editor query run --file-id <fileId> --folder-id <folderId> --queue root.demo_queue \
  --sql "SELECT id FROM demo_db.sample_table WHERE date = '\${date}'" \
  --adhoc-date 2026-08-12
```

QE multi-day batch submission creates one parent task plus date-expanded child tasks. Use the parent `taskId` returned by `query run` with `query status`; the status/result path still returns the merged preview for that parent. In JSON output, inspect `rowCount`, `returnedRows`, and `truncated` to distinguish full vs capped previews.

**`HTTP 406` responses:** retain the response and any task ID before investigating. Hive permission and YARN queue/IDC checks do not imply that CH needs a cluster selector. A CH 406 alone does not identify the failing field: read the existing task status at the same site when its ID is known, and do not resubmit or switch clusters while the outcome is unknown. Any further execution needs separate confirmation and must use only `SELECT 1 AS test_value;`.

### `aeolus query-editor query parse`

Parse/check SQL through the same Query Editor endpoint used by the browser Parse button. This does **not** submit or run a task.

```bash
bytedcli aeolus query-editor query parse [options]
bytedcli aeolus query-editor query parse --sql "SELECT 1"
bytedcli aeolus query-editor query parse --file ./queries/demo.sql
bytedcli aeolus query-editor query parse --engine ch --cluster-name <cluster_name> --ch-region VA --sql "SELECT 1"
bytedcli aeolus query-editor query parse --engine datasource --datasource-name <datasourceName> --sql "select * from sample_db.sample_tbl limit 1"
bytedcli aeolus query-editor query parse --engine datasource --datasource-id <datasourceId> --datasource-type DORIS --sql "select 1"
```

**Input:** `--sql <sql>` or `--file <path>`

**Options:** `-r/--region`, `--idc` for Hive, **`--engine` / `--cluster-name` / `--ch-region`** for ClickHouse (CH also accepts `--start-date` / `--end-date`, mapping to `query_start_date` / `query_end_date`), and **`--datasource-id` / `--datasource-type` / `--datasource-name`** for a user-defined datasource (see `query run` for how the datasource identity is resolved; `--datasource-name` needs `QE_APP_ID`).

**Endpoint mapping:**

| `--engine`       | Parse URL suffix           | Body highlights                                                                  |
| ---------------- | -------------------------- | -------------------------------------------------------------------------------- |
| `hive` (default) | `/hive/task/explain`       | `query`, `idc` (defaults from the same region mapping used by Hive run)          |
| `ch`             | `/ch/task/explain`         | `query`, optional `cluster_name`, `region`, `query_start_date`, `query_end_date` |
| `datasource`     | `/datasource/task/explain` | `query`, `datasource_id`, `datasource_type` (no `queue` / `idc`)                 |

`status=SUCCESS` means the SQL passed the Query Editor parse/check path. Semantic errors are returned as a successful CLI response with `ok:false`, `status`, `displayMessage`, and `rawErrorMessage`, matching the browser's non-submitting parse behavior.

For **`--engine datasource`**, the check runs against the real custom datasource (e.g. DORIS): a valid query returns the resolved output columns in `fields` (`ok:true`), while a missing table / syntax error returns `ok:false` with the backend message. This is the correct way to parse DORIS SQL — the default (hive) parser cannot see custom-datasource tables and will misreport them as "not found".

CH parse accepts the same `automatically` cluster alias. It never derives body `region` from `-r`, even for explicit clusters, and has no `--queue` fallback. In automatic mode its JSON output reports `clusterName: null`.

### `aeolus query-editor query status`

```bash
bytedcli aeolus query-editor query status [options]
```

**Required:** `--task-id`, `--file-id`, `--folder-id`

**Options:** `-r/--region`, `--rows`, and the same **`--engine` / `--cluster-name` / `--ch-region` / `--datasource-id` / `--datasource-type`** as `query run`. **Must match the engine used for submit**, otherwise the wrong `/hive/task/.../status` vs `/ch/task/.../status` vs `/datasource/task/.../status` path is used.

### `aeolus query-editor query logs`

```bash
bytedcli aeolus query-editor query logs [options]
```

**Required:** `--task-id`

**Options:** `-r/--region`, **`--engine`** (and optional `--cluster-name`, `--ch-region`, `--datasource-id`, `--datasource-type` for consistency with other QE commands). **Must match the engine used for submit.**

### `aeolus query-editor query cancel`

```bash
bytedcli aeolus query-editor query cancel [options]
```

**Required:** `--task-id`

**Options:** `-r/--region`, **`--engine`** (and optional `--cluster-name`, `--ch-region`, `--datasource-id`, `--datasource-type` for consistency with other QE commands). **Must match the engine used for submit**, otherwise the wrong `/hive/task/.../cancel` vs `/ch/task/.../cancel` vs `/datasource/task/.../cancel` path is used.

### `aeolus query-editor task rename`

Rename a Query Editor task record after it has been submitted. This mirrors the browser task rename action and calls `PUT /qe/v2/api/task/{taskId}/rename?id={taskId}&name={name}` with an empty JSON body. Use it after `query run` when several related SQL variants share the same file/folder and the default task name is not descriptive enough.

```bash
bytedcli aeolus query-editor task rename --task-id <taskId> --name "sample-task-name"
```

**Required:** `--task-id`, `--name`

**Options:** `-r/--region`

### `aeolus query-editor task delete`

Delete one or more Query Editor task records. The command mirrors the browser bulk-delete action and calls `DELETE /qe/v2/api/task/batch?task_ids=...`. Default mode is dry-run; pass `--yes` only after confirming the task IDs. Before deleting a task that may be referenced later, record `query status` fields such as `runtime_info.application_id`, `runtime_info.execute_id`, `runtime_info.tracking_url_list`, `query_id`, and the SQL, because the Query Editor task record/status path returns `ResourceDeletedException` after deletion while lower-level Presto/TQS/Spark history is only reachable through those recorded identifiers.

```bash
bytedcli aeolus query-editor task delete --task-id <taskId>
bytedcli aeolus query-editor task delete --task-id <taskId> --yes
bytedcli aeolus query-editor task delete --task-id <taskIdA> --task-id <taskIdB> --yes
```

**Required:** `--task-id` (repeatable; comma-separated values are also accepted)

**Options:** `-r/--region`, `--dry-run`, `--yes`

### `aeolus query-editor task result`

Fetch the execution results of a Query Editor task, with optional direct export to a Feishu/Lark spreadsheet (`--feishu`) or CSV file download (`--output`). Automatically sanitizes Hive `"NULL"` / `"\\N"` string literals to empty string `""`.

```bash
bytedcli aeolus query-editor task result --task-id <taskId>
bytedcli aeolus query-editor task result --task-id <taskId> --feishu
bytedcli aeolus query-editor task result --task-id <taskId> --output ./result.csv
bytedcli aeolus query-editor task result --task-id <taskId> --feishu --output ./result.csv
```

**Required:** `--task-id`

**Options:** `-r/--region`, `--file-id`, `--folder-id`, `--rows <N>`, `--feishu`, `--output <path>`, `--engine`, `--cluster-name`, `--datasource-id`, `--datasource-type`, `--datasource-name`

### `aeolus query-editor query one`

Creates a temp folder + file, writes SQL, then runs `query run`. It waits for completion by default; `--no-wait` returns after submission.

**SQL input (required):** `--sql` or `--file` (`--file` takes precedence when both are provided)

**Options:** `-r/--region`, `--folder`, `--name`, `--queue` (**Hive required**), `--idc`, `--no-wait`, `--timeout`, `--rows`, **`--output <path>`**, **`--feishu`**, **`--adhoc-date`**, **`--batch-start-date`**, **`--batch-end-date`**, **`--batch-concurrency`**, plus **`--engine`**, **`--cluster-name`**, **`--ch-region`**, **`--datasource-id`**, **`--datasource-type`**, **`--datasource-name`** (forwarded to the internal `query run`).

`query one` accepts the same `--sql` / `--file` SQL inputs and Hive date placeholder controls as `query run`, but auto-resolves/creates a temp folder and file first, so callers do not need explicit `--file-id` / `--folder-id`:

```bash
bytedcli aeolus query-editor query one --queue root.demo_queue \
  --sql "SELECT id FROM demo_db.sample_table WHERE date = '\${date}'" \
  --batch-start-date 2026-08-06 --batch-end-date 2026-08-12 --batch-concurrency 7

bytedcli aeolus query-editor query one --queue root.demo_queue --file ./queries/demo.sql

# CH automatic selection in EU GCP; no cluster_name or body region is sent.
bytedcli aeolus query-editor query one -r euttp --engine ch --sql 'SELECT 1 AS test_value;'

# Explicit alias for the same automatic mode.
bytedcli aeolus query-editor query one -r euttp --engine ch --cluster-name automatically --sql 'SELECT 1 AS test_value;'
```

Both `query run` and `query one` now show the resolved region as `input -> normalized` in text mode, and include `inputRegion` / `normalizedRegion` in JSON output. Errors also carry the normalized region in `error.details`.

### ClickHouse example (align with browser QE)

```bash
export QE_APP_ID=<appIdFromQueryEditorUrl>
# Often for VA/SG on TikTok row:
# export BYTEDCLI_CLOUD_SITE=i18n-tt

# Automatic selection with an existing query file in EU GCP.
bytedcli aeolus query-editor query run -r euttp --engine ch \
  --folder-id <folderId> --file-id <fileId> --sql 'SELECT 1 AS test_value;'

# Explicit cluster; --queue is also supported as a compatibility selector.
bytedcli aeolus query-editor query run -r va --engine ch \
  --cluster-name demo-cluster \
  --folder-id <folderId> --file-id <fileId> \
  --file ./query.sql

bytedcli aeolus query-editor query status -r va --engine ch \
  --task-id <taskId> --file-id <fileId> --folder-id <folderId>

bytedcli aeolus query-editor query cancel -r va --engine ch \
  --task-id <taskId>
```

### Custom datasource example (user-defined DORIS etc.)

List your custom datasources, then submit SQL against one — either by `--datasource-name` (resolved to id+type) or directly by `datasource_id` + `datasource_type`:

> **Custom datasources are appId-scoped.** `aeolus query-editor datasources` only lists a user-defined source (and `--datasource-name` only resolves it) when `QE_APP_ID` equals the Query Editor workspace appId that owns the source. The appId is the `appId=` in the Query Editor page URL (`.../queryEditor/files/<fileId>?appId=<appId>`). There is currently no CLI command to enumerate your appIds; read it from that URL. Submitting by explicit `--datasource-id` does not require the right appId.

```bash
# 1) List your datasources (custom sources show name + owner). Set QE_APP_ID first.
export QE_APP_ID=<yourWorkspaceAppId>
bytedcli aeolus query-editor datasources -r cn

# 2a) One-shot query by NAME (no --queue needed; needs QE_APP_ID set as above)
bytedcli aeolus query-editor query one -r cn --engine datasource \
  --datasource-name <datasourceName> \
  --sql "select * from sample_db.sample_tbl limit 10"

# 2b) Or identify the source directly by id+type (works without the workspace appId)
bytedcli aeolus query-editor query one -r cn --engine datasource \
  --datasource-id <datasourceId> --datasource-type DORIS \
  --sql "select * from sample_db.sample_tbl limit 10"

# Explicit run/status flow (status must reuse --engine datasource)
bytedcli aeolus query-editor query run -r cn --engine datasource \
  --datasource-name <datasourceName> \
  --folder-id <folderId> --file-id <fileId> \
  --sql "select * from sample_db.sample_tbl limit 10"
bytedcli aeolus query-editor query status -r cn --engine datasource \
  --task-id <taskId> --file-id <fileId> --folder-id <folderId>
```

Other `query-editor` subcommands (`login`, `whoami`, `queues`, `datasources`, `folder`, `file`, `tmp-table`, `template`) are unchanged by `--engine`; only **`query parse` / `run` / `status` / `logs` / `cancel` / `one`** accept engine flags.

### `aeolus query-editor template`

Browse templates saved in Query Editor. These are separate from Shuttle project templates:

```bash
# List templates under a folder/node (defaults: --parent-id 0, --department public)
bytedcli aeolus query-editor template list -r cn
bytedcli aeolus query-editor template list -r cn --parent-id <nodeId> --department public
# Paginate (defaults: --page 1, --page-size 20)
bytedcli aeolus query-editor template list -r cn --page 2 --page-size 50

# Get a template's SQL by its template_id (from list output)
bytedcli aeolus query-editor template get -r cn --template-id <templateId>
```

- `template list` → `POST /qe/v2/api/template/templateNodeList`; the response is a bare JSON array of nodes (`id`, `template_id`, `parent_id`, `name`, `node_type`, `department`, `owner`, …). Since the backend returns no total count, the output exposes `page`/`page_size`/`current_count`/`has_more` (a full page implies more may exist) instead of a faked `total`.
- `template get` → `GET /qe/v2/api/template/selectQuery/<template-id>`; the `query` field holds the SQL.

### `aeolus query-editor login`

Compliance Aeolus QE product session (`euttp`, `usttpusts` only). For `euttp`, use this only when the primary EU-scoped Titan Passport path still fails. For `usttpusts`, use this login path or an injected browser session. Login defaults to `--mode password`: prompts SSO username/password/OTP in the terminal and signs in over HTTP (no browser window — works over SSH / headless hosts). Use `--mode browser` to open a temporary browser window on the compliance host instead. That window is started from a copy of your own signed-in Chromium profile cookie store (pruned to the domains this flow needs), so it is normally already authenticated and the command completes without any interaction; if a login page does appear, sign in there. On success the cookies are merged into the SSO jar; on failure retry with the other mode.

```bash
bytedcli --site eu-ttp aeolus query-editor login
bytedcli --site us-ttp-usts aeolus query-editor login
# Force the temporary-browser flow:
bytedcli --site eu-ttp aeolus query-editor login --mode browser
# After a trusted runtime injects BYTEDCLI_AEOLUS_COOKIE:
bytedcli aeolus query-editor whoami -r usttpusts
```

When browser/CDP cookie extraction is unavailable, a human or managed secret store may inject the complete Cookie request-header value through `BYTEDCLI_AEOLUS_COOKIE` (without the `Cookie:` prefix). The variable has priority over the local `usttpusts` session jar, is accepted only for the built-in `usttpusts` HTTPS origin, is verified through `/qe/v2/api/user`, and is never persisted; other regions ignore it. A malformed, expired, or rejected value fails closed without falling back to local credentials. Agents must not request, paste, echo, log, or place the Cookie in argv, scripts, docs, or repositories. In a trusted interactive shell outside the Agent conversation, use a hidden `read -rs BYTEDCLI_AEOLUS_COOKIE`, export it, run the command, then unset it.
