---
name: bytedance-magnus
description: "Magnus GLS metadata and table-content access via bytedcli: catalog/database/table/schema lookup, global asset search with scope/owner/tag filters, guarded catalog/database creation, table creation (primary-key or non-primary-key), create-like empty copies, deletion and CN migration jobs, nested schema column creation/deletion, table-property, advanced governance configuration, and branch/tag/snapshot mutations, CN adhoc-read routing through HSQL execution surfaces (Aeolus by default, with TQS direct or Dorado HSQL adhoc when already available) when Catalog Service or an exact Hive table exposes the target, and Dorado Spark Notebook setup/execution for all other queries, DDL, DML, Python, or Scala cells. Use when tasks mention Magnus, GLS metadata, snapshots, branches, tags, Magnus table creation/deletion (建表/删表) or data/content, GlsCatalog, or Magnus governance configuration, cleanup, compaction, data expiration, snapshot expiration, or Magnus mutations, or CN DataLake permission diagnosis/repair."
---

# bytedcli Magnus

## 如何调用 bytedcli

先选择一种调用方式。下面所有示例默认直接写 `bytedcli`。

```bash
# 方式 1：直接用 npx 运行最新版
NPM_CONFIG_REGISTRY=http://bnpm.byted.org npx -y @bytedance-dev/bytedcli@latest <command> [options]

# 方式 2：先全局安装，再直接调用 bytedcli
NPM_CONFIG_REGISTRY=http://bnpm.byted.org npm install -g @bytedance-dev/bytedcli@latest
bytedcli <command> [options]
```

- 使用 `npx` 时，把后文示例里的 `bytedcli` 替换成 `NPM_CONFIG_REGISTRY=http://bnpm.byted.org npx -y @bytedance-dev/bytedcli@latest`
- 已全局安装时，直接按后文示例执行 `bytedcli ...`

## When to use

- 查询 Magnus/GLS catalog 列表、详情或存在性。
- 查询 database 列表、详情或存在性。
- 创建 Catalog（Warehouse、Properties、描述）或 Database（Catalog、Properties、描述）。
  参数映射、权限限制和提交后验证见 `references/magnus.md` 的“创建 Catalog / Database”。
- 查询 table 列表、基础信息或 detail 信息。
- 跨 Catalog/Database 检索资产，按 mine/favorite/all 范围与 owner、标签、关键字筛选。
- 在 CN 或海外站点创建主键表或非主键表。
- 删除 Magnus 表及底层数据：`magnus table delete` 默认 dry-run，仅 `--yes` 提交；
  删除不可撤销，数据清理可能异步完成，详见 `references/magnus.md` 的“Table deletion”。
- 查询表 columns、partitions、properties 或可用 column types。
- 添加包含 struct/list/map 嵌套类型的普通列，或删除普通顶层列。
- 创建、更新或删除表 property 键值。
- 列出、创建或删除表 branch，列出、查看、创建或删除 tag，以及查看、rollback 或
  revert snapshot。
- 在 CN 查询或读写 Magnus 表内容：一次性只读查询按 no-catalog/Hive 条件分流到
  HSQL 执行面（默认 Aeolus；已有执行载体时可用 TQS direct 或 Dorado HSQL adhoc）或
  `magnus query`；非 adhoc、DDL、DML、Python、Scala cell 使用 `magnus query`。

## Scope

Magnus GLS metadata queries for catalogs, databases, tables, and schemas; guarded catalog/database creation; guarded CN and
overseas primary-key/non-primary-key table creation, guarded table/data deletion, plus nested schema column creation/deletion, table-property, advanced governance configuration, and branch/tag/snapshot mutations; CN adhoc reads through HSQL execution surfaces (Aeolus by
default, with TQS direct or Dorado HSQL adhoc when already available) when the target is
visible to Catalog Service or has an exact Hive table; and all other CN table-content
access through a managed Dorado Spark Notebook.

命令跟随全局 `--site` / `BYTEDCLI_CLOUD_SITE` 访问对应的 CN ByteCloud gateway、
overseas proxy 或 overseas GLS 接口。table 创建支持 CN 与海外站点，但不支持 BOE；Catalog/Database 创建默认 dry-run，仅 `--yes` 提交；不更新或删除
catalog/database，也不更新 table。`table delete` 默认 dry-run，只有 `--yes` 才删除实际表及底层数据。其他 GLS 写能力包括 Schema 添加/删除列、表 property、branch、tag，
以及高级治理配置和当前/默认分支上的 snapshot rollback/revert。`magnus query` 不走 GLS 原生数据查询，
而是复用 Dorado Notebook，当前仅支持 CN。

## Capability and reference checks

完整能力索引与本地资料刷新方法见 `references/magnus.md` 的“当前能力索引”和
“本地参考资料与 CLI 不一致时”。本地副本声称仅支持 CN 元数据只读时，先读取
`bytedcli magnus --help` 与 `bytedcli self skill get bytedance-magnus/references/magnus.md`，
再判断能力缺口。表属性、branch/tag、snapshot 回退及 CN Notebook 执行均已有命令。
GLS 元数据修改默认 dry-run、仅 `--yes` 提交；`query setup|exec` 有实际创建/执行效果，
没有通用的 `--yes` 预览保护。

## Quick start

```bash
bytedcli magnus asset search --scope all --keyword events
bytedcli magnus asset search --scope mine --tag tier=gold
bytedcli magnus asset search --scope favorite --owner demo.user
bytedcli magnus catalog list
bytedcli magnus catalog create --catalog demo_catalog --warehouse hdfs://example-ns/warehouse/demo --description "Demo catalog" --property team=demo
bytedcli magnus database create --catalog demo_catalog --db-name demo_db --description "Demo database" --property team=demo
bytedcli --site cn magnus permission diagnose --name demo_catalog.demo_db.demo_table --subject-type user --subject demo.user --permission read
bytedcli --site cn magnus permission execute --name demo_catalog.demo_db.demo_table --subject-type service --subject example.service.api --permission write
bytedcli --site cn magnus permission execute --name demo_catalog.demo_db.demo_table --subject-type service --subject example.service.api --permission write --yes
bytedcli magnus database list --catalog demo_catalog
bytedcli magnus database list --no-catalog
bytedcli magnus database get --catalog demo_catalog --db-name demo_db
bytedcli magnus table list --catalog demo_catalog --db-name demo_db --page 1 --page-size 20
bytedcli magnus table get --name demo_catalog.demo_db.demo_table
bytedcli magnus table create --name demo_catalog.demo_db.demo_table --spec-file ./table.json
bytedcli magnus table create --name demo_catalog.demo_db.demo_pk_table --spec-file ./table.json --primary-key id --bucket-count 64 --yes
bytedcli magnus config get --name demo_catalog.demo_db.demo_table
bytedcli magnus config update --name demo_catalog.demo_db.demo_table --config-file governance.yaml
bytedcli magnus config update --name demo_catalog.demo_db.demo_table --config-file governance.yaml --yes
bytedcli magnus schema columns --name demo_catalog.demo_db.demo_table
bytedcli magnus schema column create --name demo_catalog.demo_db.demo_table --column-file column.json
bytedcli magnus schema column delete --name demo_catalog.demo_db.demo_table --column payload
bytedcli magnus schema property create --name demo_catalog.demo_db.demo_table --property owner=demo_owner
bytedcli magnus schema property create --name demo_catalog.demo_db.demo_table --property owner=demo_owner --yes
bytedcli magnus schema property update --name demo_catalog.demo_db.demo_table --property owner=new_owner --yes
bytedcli magnus schema property delete --name demo_catalog.demo_db.demo_table --key owner --yes
bytedcli magnus branch list --name demo_catalog.demo_db.demo_table
bytedcli magnus branch create --name demo_catalog.demo_db.demo_table --branch experiment --snapshot-id 12345678901234567890
bytedcli magnus branch create --name demo_catalog.demo_db.demo_table --branch experiment --snapshot-id 12345678901234567890 --yes
bytedcli magnus tag create --name demo_catalog.demo_db.demo_table --tag release-1 --branch main --yes
bytedcli magnus snapshot list --name demo_catalog.demo_db.demo_table
bytedcli magnus snapshot rollback --name demo_catalog.demo_db.demo_table --snapshot-id 12345678901234567890
bytedcli magnus snapshot revert --name demo_catalog.demo_db.demo_table --snapshot-id 12345678901234567890 --yes
bytedcli --json magnus query setup --project-id 12345 --dc demo-dc --cluster demo-cluster --queue root.demo_queue
bytedcli --json magnus query exec --code $'%%hql\nSET spark.sql.catalog.seed=com.bytedance.featurestore.sql.GlsCatalog;\nSELECT * FROM seed.demo_db.demo_table LIMIT 10' --project-id 12345
bytedcli --site i18n-bd magnus table get --name demo_catalog.demo_db.demo_table
bytedcli --site us-ttp magnus table get --name demo_catalog.demo_db.demo_table
```

## CN 表迁移作业

使用 `migration create` 将源表数据复制到已创建的空 HADOOP 表。源目标表名和 HDFS 路径必须独立；
目标目录必须专用且未被其他作业使用，迁移期间不要写入目标。CLI 从表详情读取 ID 和 Location，复用 CN 登录认证。
默认只预览，添加 `--yes` 提交一次；请求超时或断连后先用 `migration list` 检查，不能直接重复提交。
保存返回的 `jobId`，再用 `get` 或 `wait` 跟进。`list` 使用 1-based `--page` / `--page-size`；`get` 自动翻页按 ID 精确匹配，未找到返回 `job:null`，扫描超过 1000 页会报错。

```bash
bytedcli --site cn magnus migration create --source demo_catalog.demo_db.demo_source --target demo_catalog.demo_db.demo_target --cluster demo-cluster --queue root.demo_queue
bytedcli --site cn magnus migration create --source demo_catalog.demo_db.demo_source --target demo_catalog.demo_db.demo_target --cluster demo-cluster --queue root.demo_queue --yes
bytedcli --site cn magnus migration list --source demo_catalog.demo_db.demo_source --page 1 --page-size 20
bytedcli --site cn magnus migration get --source demo_catalog.demo_db.demo_source --job-id 12345
bytedcli --site cn magnus migration wait --source demo_catalog.demo_db.demo_source --job-id 12345 --timeout-ms 600000
bytedcli --site cn magnus migration cancel --source demo_catalog.demo_db.demo_source --job-id 12345
bytedcli --site cn magnus migration cancel --source demo_catalog.demo_db.demo_source --job-id 12345 --yes
```

`--scope latest` 为默认值，只选择后端最新快照；它不会固定版本，也不保证底层仅复制快照引用文件。
持续写入可能造成 `FILE_UNDER_CONSTRUCTION`。`--scope all` 请求复制全部快照，需评估资源和存储量。
当前不提供 `--snapshot-id`、`SKIP_COPY`、断点续传或自动验收。`wait` 只在任务 `SUCCESS` 时返回成功，完整查询确认作业不存在时立即报 NOT_FOUND，
失败/取消/超时返回非零退出码；超时仅结束等待，不取消服务端任务，可用相同 ID 继续等待。
默认间隔 5000ms、等待预算 600000ms，单次在途 HTTP 请求可能超出预算。
`cancel` 默认预览，仅 `--yes` 提交并回读父任务；仍需确认 Zeus 子任务已结束才能复用目标。
任务上下文包含后端提供的复制子任务信息，但 CLI 不查询子任务执行状态。
迁移成功后必须独立核验实际复制快照、结构、文件路径及内容；源表身份属性可能被复制，
需要回读并按目标名称修正。任务成功不等于验收通过。

## Command groups

- `magnus migration`: `create|list|get|wait|cancel`；仅 CN，详见上文
- `magnus asset`: `search`；支持全局、当前用户与收藏范围，详见 reference
- `magnus config`: `get|update`
- `magnus catalog`: `list|get|exists|create`
- `magnus database`: `list|get|exists|create`
- `magnus table`: `list|get|exists|create|delete`; `get --detail` 读取 detail endpoint
- `magnus schema column`: `create|delete`，复杂类型使用递归 `subColumns`
- `magnus schema`: `columns|partitions|properties|column-types`
- `magnus schema property`: `create|update|delete`
- `magnus branch`: `list|create|delete`
- `magnus tag`: `list|get|create|delete`
- `magnus snapshot`: `list|get|rollback|revert`
- `magnus permission`: `diagnose|execute`；仅支持 CN 管理员操作，目标为完整表名
- `magnus query`: `setup|exec`；当前仅支持 CN

## CN 权限诊断与修复

使用 `permission diagnose` 检查指定表的 DB / Kani / ACP 权限链路。必须指定
`--name catalog.database.table`、`--subject-type user|service`、`--subject` 和
`--permission read|write|owner`。用户使用邮箱前缀，服务使用 PSM；CLI 把 user 显式
映射为 employee。命令要求 DataLake 管理员授权，复用 CN Cloud JWT；其他站点不支持。

`permission execute` 默认只读诊断，并输出 `dry_run`、诊断结果和完整修复请求预览。
仅显式 `--yes` 提交。后端可能补建缺失的 Kani/ACP 资源、同步元数据和 owners，
并补齐指定对象的所选权限；预览列出可能动作，诊断不构成原子变更计划。

JSON 与文本保留 `brief`、分步骤 `steps` 和 `appliedFixes`。`submitted=true` 仅代表
请求已提交，不代表所有权限修复成功；结合摘要、失败步骤和已应用修复判断结果。
部分失败或超时后先重新 `diagnose`，再决定是否重试；POST 不自动重试。
本入口仅支持表目标，不支持 catalog/database 级目标。

## 从已有表创建空表

使用 `table create --name <目标表> --like <源表> --location <独立 HDFS 路径>`，无需生成 spec 文件。
默认预览完整请求，仅 `--yes` 提交。不能同时使用 `--spec-file`、`--primary-key` 或 `--bucket-count`。
支持 HADOOP 表的普通列、identity 分区和主键上的统一桶数；嵌套列、列 identifier/附加 Metadata、其他分区变换、分区独立桶数
及需要外部存储路径重映射的属性会明确拒绝。桶数从实际分区变换读取，并核对相关属性。
源目标名称及路径必须独立；不同 HDFS authority 可能是同一集群别名，调用方仍需确认物理目录不重叠。
目标表会使用新表标识，移除源表的备份引用、创建者/项目及 `magnus.table-maintenance.*` 治理配置属性。其他属性在预览中完整展示，确认适用于目标环境后再提交。
仅创建空表，不复制数据、快照、历史、权限或治理作业。提交后用 `table get --detail` 回读结构和空表状态；超时后先查询目标，避免重复提交。

```bash
bytedcli magnus table create --name demo_catalog.demo_db.demo_copy --like demo_catalog.demo_db.demo_source --location hdfs://demo-ns/warehouse/demo_copy
bytedcli magnus table create --name demo_catalog.demo_db.demo_copy --like demo_catalog.demo_db.demo_source --location hdfs://demo-ns/warehouse/demo_copy --yes
bytedcli magnus table get --name demo_catalog.demo_db.demo_copy --detail
```

## 创建主键表或非主键表（CN 与海外）

`table create` 使用 `--name catalog.database.table` 和 `--spec-file <path>`。命令默认
dry-run：先确认目标表不存在，再打印精确 GLS 请求；只有添加 `--yes` 才提交。省略
`--primary-key` 创建非主键表；传 `--primary-key <column>` 创建主键表，且主键列类型必须
是 `string`。主键表可用 `--bucket-count <n>` 指定正整数桶数。

示例 `table.json`：

```json
{
  "location": "hdfs://example-ns/warehouse/demo_table",
  "catalogType": "HADOOP",
  "columns": [
    { "name": "id", "type": "string", "isOptional": false, "comment": "identifier" },
    { "name": "value", "type": "double", "isOptional": true }
  ],
  "partitions": [{ "name": "ds", "type": "string", "isOptional": false }],
  "properties": {
    "owner": "demo_owner"
  }
}
```

`location` 和至少一个 `columns` 项是必填项；`catalogType` 默认 `HADOOP`，
`partitions`、`properties`、字段 `comment` 可省略。每个 column/partition 都必须声明
`name`、`type`、`isOptional`。partition 只放在 `partitions`，不能同时出现在
`columns`；主键必须是 `columns` 中类型为 `string` 的非分区字段。

```bash
# 非主键表：先预览，再提交
bytedcli magnus table create \
  --name demo_catalog.demo_db.demo_table \
  --spec-file ./table.json
bytedcli magnus table create \
  --name demo_catalog.demo_db.demo_table \
  --spec-file ./table.json \
  --yes

# 主键表：--primary-key 指向 columns 中的 string 字段；--bucket-count 指定桶数
bytedcli magnus table create \
  --name demo_catalog.demo_db.demo_pk_table \
  --spec-file ./table.json \
  --primary-key id \
  --bucket-count 64 \
  --yes

bytedcli magnus table exists --name demo_catalog.demo_db.demo_pk_table
```

主键表通过 `--primary-key` 生成 `Properties["pk.column.name"]`，通过可选的
`--bucket-count` 生成 `Properties["magnus.table.bucket.number"]`；后者不能脱离
`--primary-key` 使用。不要在 spec 的 `properties` 中直接写这两个保留键。CLI 不自动添加 `_magnus_row_deleted`、
`_magnus_bucket` 或 `magnus.is_magnus`。CN table-create 通过 ByteCloud
`https://cloud.bytedance.net/api/v1/datalake/gls` 网关提交，并使用 `cn` 站点的 Cloud JWT；
海外提交使用所选站点的 Cloud JWT。BOE 不支持 table create。POST 不自动重试；元数据
预检和查询同样使用所选站点的 Cloud JWT。
若提交超时或断连，先执行 `table exists` / `table get` 确认状态，再决定是否重试。

## Branch、tag 与 snapshot 操作

表级资源统一使用 `--name catalog.database.table`。先用只读命令取得精确状态：

```bash
bytedcli --json magnus branch list --name demo_catalog.demo_db.demo_table
bytedcli --json magnus tag list --name demo_catalog.demo_db.demo_table
bytedcli --json magnus tag get --name demo_catalog.demo_db.demo_table --tag release-1
bytedcli --json magnus snapshot list --name demo_catalog.demo_db.demo_table
bytedcli --json magnus snapshot get --name demo_catalog.demo_db.demo_table --snapshot-id 12345678901234567890
```

所有 snapshot ID 都必须取返回值中的 `SnapshotIdStr`，并作为十进制字符串原样传给
`--snapshot-id`。不要把它转成 JavaScript number；GLS 的 64 位 ID 可能超过安全整数范围。

创建 branch 时可传 `--snapshot-id`；省略时由 GLS 使用当前 snapshot。创建 tag 时必须且
只能指定一个来源：`--snapshot-id` 或 `--branch`。创建/删除和 snapshot 变更默认都是
dry-run，会先校验现状并打印精确 GLS 请求；确认后加 `--yes`：

```bash
bytedcli magnus branch create --name demo_catalog.demo_db.demo_table --branch experiment --snapshot-id 12345678901234567890
bytedcli magnus branch create --name demo_catalog.demo_db.demo_table --branch experiment --snapshot-id 12345678901234567890 --yes
bytedcli magnus branch delete --name demo_catalog.demo_db.demo_table --branch experiment --yes
bytedcli magnus tag create --name demo_catalog.demo_db.demo_table --tag release-1 --branch main --yes
bytedcli magnus tag create --name demo_catalog.demo_db.demo_table --tag release-2 --snapshot-id 12345678901234567890 --yes
bytedcli magnus tag delete --name demo_catalog.demo_db.demo_table --tag release-1 --yes
bytedcli magnus snapshot rollback --name demo_catalog.demo_db.demo_table --timestamp-ms 1700000000000 --yes
bytedcli magnus snapshot revert --name demo_catalog.demo_db.demo_table --snapshot-id 12345678901234567890 --yes
```

rollback 支持 snapshot ID 或 epoch-millisecond timestamp，二选一；revert 只接受 snapshot
ID。GLS 的 rollback API 不接受 branch selector，因此两者都作用于表的当前/默认分支，
不能指定 named branch。revert 还依赖表的后端版本：部分 GLS Iceberg 后端支持，部分版本
会返回 unsupported；bytedcli 原样报告 GLS 错误，不自动改走 rollback。POST 不自动重试；
若超时或断连，先重新执行 `snapshot list` 确认状态，再决定是否重试。

## 读写 Magnus 表内容：先选择路径（CN only）

先判断操作类型，再判断表是否可被原生 HSQL 发现。不要只根据“能否在 GLS 查到表”
选择执行路径。

1. 只要是**非 adhoc 查询**，或 SQL 包含 **DDL / DML**，直接使用
   `magnus query setup|exec`。不要走 TQS 或 `dorado adhoc exec`。
2. 只有一次性、只读的 adhoc 查询（例如 `SELECT`）才继续检查下面两项：
   1. 运行 `magnus database list --no-catalog`。目标 database 与返回项精确同名，
      表示该 database 已切 Catalog Service 白名单，可直接走 HSQL。
   2. 如果不在 no-catalog 列表，检查 Hive 是否存在 database、table 都精确同名的
      `HiveTable`。存在时也可直接走 HSQL。
3. 前两项都不满足时，使用 `magnus query setup|exec`。

### 检查 no-catalog 和同名 Hive 表

```bash
# 检查目标 database 是否在 Catalog Service 的 no-catalog 暴露列表中
bytedcli --json magnus database list --no-catalog --page 1 --page-size 100

# 仅在上一步没有精确命中时检查同名 HiveTable；显式 --type 可避免回退到其他资产类型
bytedcli --json hive detail demo_db demo_table --type HiveTable --region cn
```

只接受 database 名称的精确匹配；列表不止一页时继续翻页，不能因为第一页没找到就
判定未切白名单。Hive 检查只接受命令成功返回的精确 `HiveTable`，ClickHouse、Doris
或只有 database/只有 table 同名都不满足条件。

### 路径一：HSQL（仅满足条件的 adhoc 只读查询）

所有 HSQL 执行面都必须在同一次 SQL 提交中设置下面两个配置，并使用
`database.table` 两段式表名：

```sql
set spark.sql.magnus.enable = true;
set spark.gluten.enabled = false;
```

关闭 Gluten 可避免 Spark fallback 读取部分 Hive/Iceberg 映射时出现
`org/apache/iceberg/spark/source/metrics/NumSplits` 依赖错误。

对 agent，优先使用 Aeolus Query Editor 的 `query one`：它自动创建临时 folder/file，
并复用 `bytedcli auth login` 会话，不要求用户预先配置 TQS App 凭证。先列队列，再使用
匹配的 queue 和 IDC 提交；如果返回多个候选或 queue/IDC 不明确，向用户确认，不要猜：

```bash
# 1. 列出当前账号可用的队列
bytedcli --json aeolus query-editor queues -r cn

# 2. 先提交并保留 task/file/folder ID，避免长时间等待时丢失任务定位信息
bytedcli --json aeolus query-editor query one \
  -r cn \
  --queue <queue> \
  --idc <idc> \
  --rows 10 \
  --no-wait \
  --sql $'set spark.sql.magnus.enable = true;\nset spark.gluten.enabled = false;\nSELECT * FROM demo_db.demo_table LIMIT 10;'

# 3. 使用 query one 返回的 ID 查询最终状态和日志
bytedcli --json aeolus query-editor query status \
  -r cn --task-id <taskId> --file-id <fileId> --folder-id <folderId> --rows 10
bytedcli --json aeolus query-editor query logs -r cn --task-id <taskId>
```

日志可能先出现 `switch to new engine: Presto`，随后回退到 `SparkCli`；这是允许的，
应以最终任务状态为准。任务连续数分钟保持 `RUNNING / 0%` 且日志没有 Spark 进展时，
优先确认或更换 queue/IDC，不要先改 SQL。最终失败若包含 `NumSplits`，检查本次提交的
job conf 是否确实包含 `spark.gluten.enabled=false`。

已有 TQS 凭证或 Dorado 临时查询 task 时，也可使用下面的执行面；SQL 仍必须带两个配置：

```bash
# TQS direct：需要已配置 TQS_APP_ID / TQS_APP_KEY
bytedcli --json tqs execute \
  --sql $'set spark.sql.magnus.enable = true;\nset spark.gluten.enabled = false;\nSELECT * FROM demo_db.demo_table LIMIT 10;'

# Dorado HSQL adhoc：需要已有的临时查询执行载体
bytedcli --json dorado adhoc exec \
  $'set spark.sql.magnus.enable = true;\nset spark.gluten.enabled = false;\nSELECT * FROM demo_db.demo_table LIMIT 10;' \
  --task-id <adhoc-task-id> \
  --region cn
```

Aeolus、TQS direct 和 Dorado HSQL adhoc 是同一 HSQL 分支下的不同执行面。默认使用
Aeolus；只有已有相应凭证或 task 时才切到另外两种执行面。

### 路径二：`magnus query`（其他查询及所有 DDL / DML）

`magnus query setup` 创建一个配置好 Magnus SDK 的 Dorado Spark Notebook。首次
setup 必须由用户明确提供 `--project-id`、`--dc`、`--cluster`、`--queue`，不要猜测：

```bash
bytedcli --json magnus query setup \
  --project-id <project-id> \
  --dc <dc> \
  --cluster <cluster> \
  --queue <queue>
```

setup 的 JSON 结果包含 `nodeId`、`taskId`、`notebookName` 和 `notebookUrl`。默认
Notebook 名为 `bytedcli-magnus-query`；可在 setup 时用 `--notebook-name <name>`
自定义，并在后续自动发现时传同一个名称。需要放到指定目录时加
`--parent-uri <uri>`。

这条路径不依赖 Hive 表。HSQL cell 里配置 `GlsCatalog`，再用
`catalog.database.table` 三段式表名直接查询 Magnus：

```bash
bytedcli --json magnus query exec \
  --code $'%%hql\nSET spark.sql.catalog.seed=com.bytedance.featurestore.sql.GlsCatalog;\nSELECT * FROM seed.demo_db.demo_table LIMIT 10;' \
  --project-id <project-id>
```

`--notebook-node-id` 可选：

- 省略 `--notebook-node-id` 时，必须传 `--project-id`。CLI 会按精确
  `--notebook-name`（默认 `bytedcli-magnus-query`）、Notebook 类型和 Magnus
  Spark 配置签名，自动查找 `magnus query setup` 创建的 Notebook。
- 已知 node ID 时可直接传
  `--notebook-node-id <node-id>`；这条路径不要求 `--project-id`。若同时传
  `--project-id`，结果中的 Notebook URL 会带完整 project 参数。
- 自动发现找不到、找到多个或配置签名不匹配时会失败，不会随便选择项目中的
  普通 Notebook。此时使用 setup 返回的 `nodeId`，或为 setup/exec 指定唯一的
  `--notebook-name`。

exec 使用 `--code <code>` 传入完整 HSQL、Python 或 Scala cell，也支持
`--code-file <path>`，或用 `--cell-index <index>` 执行 Notebook 中已有的 cell。
例如：

```bash
bytedcli magnus query exec --code $'print(spark.sql("SELECT 1").collect())' --project-id <project-id>
bytedcli magnus query exec --code $'%%scala\nprintln(spark.sql("SELECT 1").collect())' --project-id <project-id>
```

cell 源码会原样交给 Dorado Notebook，不在 bytedcli 侧禁止 SQL 或限制 SELECT
结果。查询结果、错误、display data 等行为以 Dorado Notebook 为准。需要查询
其他 catalog 时，直接在 cell 中执行相应的 SQL `SET spark.sql.catalog...` 配置。

## Agent Guidance

- 表级资源名统一传 `--name catalog.database.table`，例如 `demo_catalog.demo_db.demo_table`。
- `table create` 支持 CN 与海外站点，但不支持 BOE。省略 `--primary-key` 创建非主键表；传入它时必须引用
  spec `columns` 中类型为 `string` 的非分区字段。主键表可用 `--bucket-count <n>` 指定正整数桶数；默认 dry-run，仅 `--yes` 提交。
- 不要在 spec 中直接设置 `pk.column.name` 或 `magnus.table.bucket.number`，也不要补
  `_magnus_row_deleted`、`_magnus_bucket` 或 `magnus.is_magnus`；CLI 会按参数生成主键属性和可选桶数属性。
- 列 database 时，`--catalog <name>` 与 `--no-catalog` 必须且只能选择一个；
  `--no-catalog` 以空 Catalog 请求 GLS 的 no-catalog 暴露列表。
- database 入参统一使用标准 flag `--db-name`，不要使用 `--database-name`。
- 需要机器可读输出时使用全局 `--json`，并把它放在 `magnus` 前面：`bytedcli --json magnus table get --name demo_catalog.demo_db.demo_table`。
- 分页命令使用 `--page` 与 `--page-size`；CLI 侧页码从 1 开始。
- 属性创建/更新用可重复的 `--property key=value`；值中的后续 `=` 会原样保留。创建会拒绝已有键，更新会拒绝不存在的键。
- 属性删除用可重复的 `--key name`，会拒绝不存在的键。
- 三个属性写命令默认都是 dry-run：读取当前属性并打印 before、after 和精确 GLS 请求，但不提交。确认预览后添加 `--yes` 才执行写入。
- branch/tag 的创建删除及 snapshot rollback/revert 同样默认 dry-run，只有 `--yes` 才提交。
- snapshot ID 必须使用 GLS 返回的 `SnapshotIdStr`，以十进制字符串原样传递。
- rollback/revert 只操作当前/默认分支，不支持指定 branch；revert 是否可用取决于后端版本。
- GLS 只有属性更新 API，没有独立删除 API。删除会读取当前 map、移除指定键，再以 `RemoveUncoverProperties=true` 写入完整剩余 map；GLS 不提供 CAS，并发修改可能在读取与写入之间被覆盖，因此应检查 dry-run 并尽快提交。
- Magnus 表内容访问必须先按「读写 Magnus 表内容：先选择路径」分流：只有
  no-catalog 精确命中或存在同名 HiveTable 的 adhoc 只读查询可走 HSQL，并同时设置
  `spark.sql.magnus.enable = true` 和 `spark.gluten.enabled = false`；默认执行面是
  Aeolus Query Editor。不满足条件、非 adhoc、DDL、DML 都使用 `magnus query setup|exec`。
- `magnus query` 当前仅支持 CN；不要把海外 metadata 的 `--site` 路由规则套到
  Notebook query 上。
- `--site cn` 通过 ByteCloud CN GLS gateway
  `https://cloud.bytedance.net/api/v1/datalake/gls` 访问 metadata 和 table-create。
- `--site i18n`、`--site i18n-bd` 与 `--site i18n-tt` 默认通过 ByteCloud SG
  proxy 访问 GLS；`--site i18n --vregion US-East` 与
  `--site i18n-tt --vregion US-East` 通过 ByteCloud Maliva proxy 访问。
- `--site us-ttp`、`--site us-ttp-bdee`、`--site us-ttp-usts` 与
  `--site eu-ttp` 的 ByteCloud gateway 尚未注册 GLS schema，继续访问
  `http://openstudio-overseas.byted.org/gls`。
- 元数据查询与 table-create 预检复用所选站点的 bytedcli Cloud JWT。未登录时先执行
  `bytedcli --site <site> auth login`。legacy `--site i18n --vregion US-East`
  会改用 `i18n-tt` JWT，需先执行 `bytedcli --site i18n-tt auth login`；
  新调用推荐直接使用 `--site i18n-tt --vregion US-East`。
- CN table-create 通过 ByteCloud CN GLS gateway 提交，并使用 `cn` 站点的 Cloud JWT；
  已执行 `bytedcli auth login` 且 CN Cloud JWT 有效时不需要额外的 doas/SSO 授权。
- 海外 table-create 经对应 GLS 路由发送，并使用所选站点的 Cloud JWT。

## Schema column create/delete

添加或删除列时，先阅读 [Schema column create/delete](references/magnus.md#schema-column-createdelete) 的 JSON 示例与边界说明。
使用 `magnus schema column create --column-file column.json` 添加一个顶层列，复杂类型通过递归 `subColumns` 表达；
使用 `magnus schema column delete --column payload` 删除普通顶层列。两者都需要 `--name catalog.db.table`，
默认 dry-run，只有 `--yes` 提交；分区列、分区源列和主键禁止删除。

## 高级治理配置

使用 `magnus config get` 查看配置及关联 Dorado 任务 ID，使用 `magnus config update --config-file governance.yaml` 预览变更，确认具体变更已获用户授权后加 `--yes` 提交。读取 [治理配置参考](references/governance.md) 获取完整 YAML 示例、字段单位、替换语义和后端可观测性限制。

## Table deletion

删除单张表时，先阅读 [Table deletion](references/magnus.md#table-deletion) 的数据删除语义与失败处理。
`magnus table delete --name demo_catalog.demo_db.demo_table` 默认先检查表存在，再预览完整请求；
只有加 `--yes` 才删除实际 Catalog 表及底层数据。后端继续检查权限、副本和下游引用，CLI 不强制绕过。
数据清理可能异步继续，提交成功不等于全部文件已清除；请求失败或超时时，先用 `table exists` 核验状态再决定是否重试。
