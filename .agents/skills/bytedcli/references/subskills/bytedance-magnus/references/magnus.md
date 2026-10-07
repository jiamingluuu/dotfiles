# Magnus

## Contents

- [Table deletion](#table-deletion)
- Current capability index and local reference refresh
- Global asset search and filtering
- Metadata, catalog/database/table creation, column evolution, and property commands
- Advanced governance configuration: use the bytedance-magnus skill and its governance reference
- CN permission diagnosis and repair
- CN table-content routing and execution
- Overseas metadata routing

Magnus GLS global asset search and metadata queries for catalogs, databases, tables, and schemas, guarded catalog/database creation, and guarded CN and overseas
primary-key/non-primary-key table creation, guarded table/data deletion, plus nested schema column creation/deletion, table-property, advanced governance configuration, and branch/tag/snapshot mutations, CN adhoc reads through HSQL execution surfaces (Aeolus by
default, with TQS direct or Dorado HSQL adhoc when already available) when Catalog
Service or an exact Hive table exposes the target, plus all other CN table-content access
through Dorado Spark Notebook.

命令跟随全局 `--site` / `BYTEDCLI_CLOUD_SITE` 访问对应的 CN、ByteCloud
overseas proxy 或 overseas GLS 接口。表内容访问先按操作类型分流；adhoc 只读查询
再按 no-catalog/Hive 条件选择 HSQL 执行面。`magnus query` 复用 Dorado Notebook，
当前仅支持 CN，且不依赖 Hive 表。

## 当前能力索引

| 需求                              | 命令入口                                                                               | 行为与边界                                                                                             |
| --------------------------------- | -------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------ |
| Catalog / Database / Table 元数据 | `catalog list\|get\|exists`、`database list\|get\|exists`、`table list\|get\|exists`   | Table `get --detail` 读取详细信息；database 使用 `--db-name`                                           |
| 全局资产搜索与筛选                | `asset search`                                                                         | `--scope all\|mine\|favorite`；可组合 catalog、database、owner、关键词和多标签筛选，按过滤后的结果分页 |
| 创建 Catalog / Database           | `catalog create`、`database create`                                                    | 默认 dry-run；Catalog 需要 `--warehouse`，Database 使用 `--db-name`；参数与权限限制见下文              |
| 创建表                            | `table create`                                                                         | 主键表与非主键表；CN 与海外可用，BOE 不支持                                                            |
| Schema 元数据与列变更             | `schema columns\|partitions\|properties\|column-types`、`schema column create\|delete` | 嵌套列定义使用 `--column-file`                                                                         |
| 删除表及数据                      | `table delete`                                                                         | `--name catalog.db.table`；默认 dry-run，`--yes` 提交，保留后端副本和下游引用限制                      |
| 表属性变更                        | `schema property create\|update\|delete`                                               | 创建/更新用 `--property key=value`，删除用 `--key`                                                     |
| Branch                            | `branch list\|create\|delete`                                                          | 创建可选择 snapshot                                                                                    |
| Tag                               | `tag list\|get\|create\|delete`                                                        | 创建从 snapshot 或 branch 二选一                                                                       |
| Snapshot                          | `snapshot list\|get\|rollback\|revert`                                                 | ID 保持字符串；回退当前/默认分支，revert 依赖后端支持                                                  |
| 高级治理配置                      | `config get\|update`                                                                   | 使用配置文件；完整字段与策略见 bytedance-magnus 的治理参考资料                                         |
| 权限诊断与修复                    | `permission diagnose\|execute`                                                         | 仅 CN；要求 DataLake 管理员权限                                                                        |
| 表内容查询与代码执行              | `query setup\|exec`                                                                    | 仅 CN，通过 Dorado Spark Notebook；adhoc 只读查询按下文 HSQL 条件分流                                  |

以上入口均以 `bytedcli magnus` 为前缀。GLS 元数据修改命令默认 dry-run，仅
`--yes` 提交；`query setup` 会创建 Notebook，`query exec` 会查找或使用已有 Notebook 并执行代码，
二者没有通用的 `--yes` 预览保护，不能把它们当作纯元数据查询。

### 从已有表创建空表

`table create --name demo_catalog.demo_db.demo_copy --like demo_catalog.demo_db.demo_source --location hdfs://demo-ns/warehouse/demo_copy`
默认预览，仅 `--yes` 提交；`--like` 与 `--spec-file`、`--primary-key`、`--bucket-count` 互斥。
支持 HADOOP 表的普通列、identity 分区及统一主键分桶。嵌套列、identifier/附加 Metadata、其他变换、
分区独立桶数和需要外部路径重映射的配置会被拒绝，不会静默降级。
目标必须使用新名称及独立 HDFS 路径。源备份引用、创建者/项目与治理配置会移除，表标识改为目标名。
仅复制空表定义，不复制数据、快照、历史、权限或治理作业；提交后回读 `table get --detail` 确认。
完整示例见上级 SKILL.md 的“从已有表创建空表”。

### CN 表迁移作业

`magnus migration create|list|get|wait|cancel` 支持 CN HADOOP 表迁移，复用当前登录认证。
`create --source <完整源表名> --target <完整目标表名> --cluster <集群> --queue <队列>` 自动解析 ID 和 Location；
目标须已存在且无当前快照，源目标路径须独立。默认预览，仅 `--yes` 提交。
`--scope latest|all` 默认 latest；latest 不固定版本，也不保证按快照文件清单复制，持续写入可能导致文件未关闭错误。
`get|wait|cancel` 使用 `--source` 和 `--job-id`，get 自动翻页定位；list 使用 1-based page/page-size。
wait 默认 600000ms 预算、5000ms 间隔，完整查询后不存在的作业立即报 NOT_FOUND，失败或超时退出非零；超时不取消远端任务，在途请求可能超出预算。
cancel 默认预览，--yes 提交并回读父任务；仍需独立确认 Zeus 子任务停止。
不提供 SKIP_COPY、快照固定或自动验收；SUCCESS 后仍需验证快照、结构、独立路径和内容，并修正目标身份属性。
完整命令示例见上级 SKILL.md 的“CN 表迁移作业”。

## 本地参考资料与 CLI 不一致时

若本地副本仍写着“首版 CN GLS 元数据只读”，先核对实际使用的 CLI 版本、
命令帮助和随该 CLI 分发的参考资料，不据此认定写能力或表内容查询缺失：

```bash
bytedcli --version
bytedcli magnus --help
bytedcli magnus schema property --help
bytedcli magnus branch --help
bytedcli magnus tag --help
bytedcli magnus snapshot --help
bytedcli magnus query --help
bytedcli self skill get bytedance-magnus/references/magnus.md
```

`self skill get` 直接读取当前 CLI 包内的资料，无需安装独立 skill。如果 CLI
本身需要升级，先运行 `bytedcli self update --check`，按需使用 `bytedcli self update`。
对于由 `self skill` 管理的全局安装副本，按实际安装名称定向刷新：

```bash
bytedcli self skill list --installed -g
bytedcli self skill update -s bytedance-magnus -g
# 使用总路由 skill 时，选择其实际安装名称
bytedcli self skill update -s bytedcli -g
```

项目级安装省略 `-g`。未安装 Magnus skill 时可使用
`bytedcli self skill install -s bytedance-magnus -a codex -g` 安装供 Codex 使用。
手工复制、旧路径或其他安装器管理的副本不一定在 `self skill` 登记范围内；
需要按其安装来源同步，并核对 Agent 实际加载的文件。刷新后重新加载 skill
或开启新会话，避免继续使用上下文中的旧内容。

仓库维护时修改 `skills/bytedance-magnus/` 源文档，再运行 `npm run build:assets`
同步总路由 reference 与 bytedcli / doubao 镜像，不手工维护多份命令清单。

```bash
bytedcli magnus catalog list
bytedcli --site cn magnus permission diagnose --name demo_catalog.demo_db.demo_table --subject-type user --subject demo.user --permission read
bytedcli --site cn magnus permission execute --name demo_catalog.demo_db.demo_table --subject-type service --subject example.service.api --permission write
bytedcli --site cn magnus permission execute --name demo_catalog.demo_db.demo_table --subject-type service --subject example.service.api --permission write --yes
bytedcli magnus database list --catalog demo_catalog
bytedcli magnus database list --no-catalog
bytedcli magnus database get --catalog demo_catalog --db-name demo_db
bytedcli magnus table list --catalog demo_catalog --db-name demo_db --page 1 --page-size 20
bytedcli magnus table get --name demo_catalog.demo_db.demo_table
bytedcli magnus table get --name demo_catalog.demo_db.demo_table --detail
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
bytedcli magnus branch create --name demo_catalog.demo_db.demo_table --branch experiment --snapshot-id 12345678901234567890 --yes
bytedcli magnus tag create --name demo_catalog.demo_db.demo_table --tag release-1 --branch main --yes
bytedcli magnus snapshot list --name demo_catalog.demo_db.demo_table
bytedcli magnus snapshot rollback --name demo_catalog.demo_db.demo_table --snapshot-id 12345678901234567890 --yes
bytedcli magnus snapshot revert --name demo_catalog.demo_db.demo_table --snapshot-id 12345678901234567890 --yes
bytedcli --json magnus query setup --project-id 12345 --dc demo-dc --cluster demo-cluster --queue root.demo_queue
bytedcli --json magnus query exec --code $'%%hql\nSET spark.sql.catalog.seed=com.bytedance.featurestore.sql.GlsCatalog;\nSELECT * FROM seed.demo_db.demo_table LIMIT 10' --project-id 12345
bytedcli --site i18n-bd magnus table get --name demo_catalog.demo_db.demo_table
bytedcli --site us-ttp magnus table get --name demo_catalog.demo_db.demo_table
```

## 全局资产搜索与筛选

```bash
bytedcli magnus asset search --scope all --keyword events
bytedcli magnus asset search --scope mine --catalog demo_catalog --db-name demo_db --tag tier=gold --tag team=demo
bytedcli --json magnus asset search --scope favorite --owner demo.user --page 2 --page-size 10
```

- 资产指 GLS 表元数据；Catalog/Database 均可省略以跨目录检索。默认 `--scope all`，查询用户可见的资产。
- `mine` 使用当前认证站点的真实 username 筛选 CreatorId；显式 `--owner` 必须与该身份一致。`--owner` 是邮箱前缀精确匹配，不做模糊用户名检索。
- `--keyword` 使用 GLS SearchKey；`--tag key=value` 可重复，多条同时满足，大小写与值中的 `=` 原样保留。
- `favorite` 读取当前认证用户的收藏，再分批限定收藏表名执行同样的后端筛选；过滤后计算总数与分页，并保持收藏顺序。不会增删收藏。
- `--page` 从 1 开始，`--page-size` 默认 20。JSON 包含 `assets`、`total`、`pages`、`page`、`page_size`；资产 ID 为字符串，标签 map 原样保留。
- 搜索为只读操作，无需 `--yes`。命令复用全局站点路由；后端不支持资产检索参数时显式返回错误。

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

常用入口：

- `bytedcli magnus catalog list|get|exists|create`
- `bytedcli magnus database list|get|exists|create`
- `bytedcli magnus table list|get|exists|create|delete`
- `bytedcli magnus schema columns|partitions|properties|column-types`
- `bytedcli magnus schema column create|delete`
- `bytedcli magnus schema property create|update|delete`
- `bytedcli magnus branch list|create|delete`
- `bytedcli magnus tag list|get|create|delete`
- `bytedcli magnus snapshot list|get|rollback|revert`
- `bytedcli magnus query setup|exec`（仅支持 CN）

列 database 时，`--catalog <name>` 与 `--no-catalog` 必须且只能选择一个；
`--no-catalog` 以空 Catalog 请求 GLS 的 no-catalog 暴露列表。database 入参统一使用
`--db-name`。

`table create` 支持 CN 与海外站点（不支持 BOE），并接受 `--name catalog.database.table` 与
`--spec-file <path>`。省略 `--primary-key` 创建非主键表；传
`--primary-key <column>` 创建主键表，且该字段必须位于 `columns` 而不是
`partitions`，类型必须是 `string`。主键表可用 `--bucket-count <n>` 指定正整数桶数。
默认只做存在性预检并输出精确 GLS 请求，添加 `--yes` 才提交。

```json
{
  "location": "hdfs://example-ns/warehouse/demo_table",
  "catalogType": "HADOOP",
  "columns": [
    { "name": "id", "type": "string", "isOptional": false, "comment": "identifier" },
    { "name": "value", "type": "double", "isOptional": true }
  ],
  "partitions": [{ "name": "ds", "type": "string", "isOptional": false }],
  "properties": { "owner": "demo_owner" }
}
```

`location` 与非空 `columns` 必填；`catalogType` 默认 `HADOOP`，其他顶层字段可省略。
字段名必须唯一，partition 不得重复出现在 columns。主键表由 CLI 写入
`Properties["pk.column.name"]`；可选桶数写入
`Properties["magnus.table.bucket.number"]`，且 `--bucket-count` 只能和
`--primary-key` 一起使用。spec 禁止直接设置这两个保留键。CLI 不自动补
`_magnus_row_deleted`、`_magnus_bucket` 或 `magnus.is_magnus`。

```bash
bytedcli magnus table create \
  --name demo_catalog.demo_db.demo_table \
  --spec-file ./table.json
bytedcli magnus table create \
  --name demo_catalog.demo_db.demo_pk_table \
  --spec-file ./table.json \
  --primary-key id \
  --bucket-count 64 \
  --yes
bytedcli magnus table exists --name demo_catalog.demo_db.demo_pk_table
```

CN table-create 通过 ByteCloud `https://cloud.bytedance.net/api/v1/datalake/gls` 网关提交，
并使用 `cn` 站点的 Cloud JWT；海外提交使用所选站点的 Cloud JWT。元数据查询和存在性
预检同样使用 Cloud JWT。POST 不自动重试；超时或断连后先用 `table exists` /
`table get` 确认结果。

属性创建/更新使用可重复的 `--property key=value`，删除使用可重复的
`--key name`。创建拒绝已有键，更新和删除拒绝不存在的键。三个写命令默认
dry-run，只有添加 `--yes` 才提交。

GLS 没有独立属性删除 API。删除会读取当前 property map、移除指定键，再以
`RemoveUncoverProperties=true` 写入完整剩余 map。该读改写没有 CAS；并发修改
可能被覆盖，应检查 dry-run 中的 before、after 和 request，并尽快提交。

branch/tag 创建删除与 snapshot rollback/revert 也是受保护写操作：默认 dry-run，只有
显式 `--yes` 才提交。创建 branch 可选 `--snapshot-id`，省略时使用当前 snapshot；
创建 tag 必须且只能传 `--snapshot-id` 或 `--branch` 之一。

```bash
bytedcli --json magnus branch list --name demo_catalog.demo_db.demo_table
bytedcli magnus branch create --name demo_catalog.demo_db.demo_table --branch experiment --snapshot-id 12345678901234567890
bytedcli magnus branch delete --name demo_catalog.demo_db.demo_table --branch experiment --yes
bytedcli --json magnus tag get --name demo_catalog.demo_db.demo_table --tag release-1
bytedcli magnus tag create --name demo_catalog.demo_db.demo_table --tag release-1 --branch main --yes
bytedcli --json magnus snapshot get --name demo_catalog.demo_db.demo_table --snapshot-id 12345678901234567890
bytedcli magnus snapshot rollback --name demo_catalog.demo_db.demo_table --timestamp-ms 1700000000000 --yes
bytedcli magnus snapshot revert --name demo_catalog.demo_db.demo_table --snapshot-id 12345678901234567890 --yes
```

snapshot ID 必须使用 GLS 返回的 `SnapshotIdStr`，并以十进制字符串原样传递；不要转成
JavaScript number。rollback 的目标可用 snapshot ID 或 epoch-millisecond timestamp
二选一，revert 只接受 snapshot ID。GLS rollback API 没有 branch selector，所以二者都
操作当前/默认分支，不能指定 named branch。revert 支持依赖后端版本；不支持时 bytedcli
原样返回 GLS backend 错误，不自动改成 rollback。写请求不自动重试；结果不确定时先重新
执行 `magnus snapshot list` 检查当前状态。

查询 Magnus 表内容时先分流：非 adhoc 查询以及 DDL、DML 一律使用
`magnus query setup|exec`。只有一次性只读 adhoc 查询才按顺序检查：

1. `magnus database list --no-catalog` 是否精确返回目标 database。
2. 若未命中，Hive 是否存在 database 和 table 都同名的 `HiveTable`。

```bash
bytedcli --json magnus database list --no-catalog --page 1 --page-size 100
bytedcli --json hive detail demo_db demo_table --type HiveTable --region cn
```

前两项任一满足时走 HSQL，并使用 `database.table` 两段式表名。所有执行面都必须
在同一次 SQL 提交中设置 `spark.sql.magnus.enable = true` 和
`spark.gluten.enabled = false`。默认使用 Aeolus Query Editor：

```bash
bytedcli --json aeolus query-editor queues -r cn
bytedcli --json aeolus query-editor query one \
  -r cn --queue <queue> --idc <idc> --rows 10 --no-wait \
  --sql $'set spark.sql.magnus.enable = true;\nset spark.gluten.enabled = false;\nSELECT * FROM demo_db.demo_table LIMIT 10;'

bytedcli --json aeolus query-editor query status \
  -r cn --task-id <taskId> --file-id <fileId> --folder-id <folderId> --rows 10
bytedcli --json aeolus query-editor query logs -r cn --task-id <taskId>
```

使用 `query one` 返回的 `taskId`、`fileId`、`folderId` 轮询。日志先出现 Presto、
随后回退到 SparkCli 是允许的，应以最终状态为准。连续数分钟保持 `RUNNING / 0%`
且没有 Spark 进展时，确认或更换 queue/IDC；不要先改 SQL。若 Spark 最终报
`org/apache/iceberg/spark/source/metrics/NumSplits`，检查 job conf 是否包含
`spark.gluten.enabled=false`。

已有执行载体时可选 TQS direct 或 Dorado HSQL adhoc，仍使用相同的两个 Spark 配置：

```bash
bytedcli --json tqs execute \
  --sql $'set spark.sql.magnus.enable = true;\nset spark.gluten.enabled = false;\nSELECT * FROM demo_db.demo_table LIMIT 10;'
bytedcli --json dorado adhoc exec \
  $'set spark.sql.magnus.enable = true;\nset spark.gluten.enabled = false;\nSELECT * FROM demo_db.demo_table LIMIT 10;' \
  --task-id <adhoc-task-id> --region cn
```

前两项都不满足时使用 `magnus query`，先创建配置好 Magnus SDK 的 Notebook：

```bash
bytedcli --json magnus query setup \
  --project-id <project-id> --dc <dc> --cluster <cluster> --queue <queue>
```

setup 返回 `nodeId`、`taskId`、`notebookName`、`notebookUrl`。exec 的
`--notebook-node-id` 可选；省略 `--notebook-node-id` 时必须传 `--project-id`，CLI
按精确 `--notebook-name`（默认 `bytedcli-magnus-query`）和 setup 配置签名自动
发现 Notebook：

```bash
bytedcli --json magnus query exec \
  --code $'%%hql\nSET spark.sql.catalog.seed=com.bytedance.featurestore.sql.GlsCatalog;\nSELECT * FROM seed.demo_db.demo_table LIMIT 10;' \
  --project-id <project-id>
```

已知节点时也可传 `--notebook-node-id <node-id>`。支持 HSQL、Python、Scala
cell，以及 `--code-file`、`--cell-index`。源码原样交给 Dorado Notebook；SQL
限制、SELECT 查询结果和错误行为均以 Dorado Notebook 为准。查询其他 catalog
时在 cell 中执行对应的 `SET spark.sql.catalog...` 配置。

`i18n` / `i18n-bd` / `i18n-tt` 默认通过 ByteCloud SG proxy 访问 GLS；
`i18n` / `i18n-tt` 携带 `--vregion US-East` 时通过 ByteCloud Maliva proxy
访问。`us-ttp` / `us-ttp-bdee` / `us-ttp-usts` / `eu-ttp` 的 ByteCloud
gateway 尚未注册 GLS schema，继续访问
`http://openstudio-overseas.byted.org/gls`。认证前使用同一个 `--site` 执行
`auth login`；legacy `--site i18n --vregion US-East` 改用 `i18n-tt` JWT，
需先执行 `bytedcli --site i18n-tt auth login`，新调用推荐直接使用
`--site i18n-tt --vregion US-East`。

不要使用 `magnus data list`。adhoc 只读查询按 no-catalog/Hive 条件选择 HSQL 或
`magnus query`；不满足条件、非 adhoc、DDL、DML 使用 CN-only 的 `magnus query exec`。

## Schema column create/delete

```bash
# 默认 dry-run：读取完整 Schema 并打印精确请求
bytedcli magnus schema column create --name demo_catalog.demo_db.demo_table --column-file column.json
bytedcli magnus schema column create --name demo_catalog.demo_db.demo_table --column-file column.json --yes
bytedcli magnus schema column delete --name demo_catalog.demo_db.demo_table --column payload
bytedcli magnus schema column delete --name demo_catalog.demo_db.demo_table --column payload --yes
```

`--column-file` 接收一个 JSON 列对象，使用 lower camel case 字段。例子为
`struct -> list -> map` 的复杂嵌套类型：

```json
{
  "name": "payload",
  "type": "struct",
  "comment": "Event payload",
  "subColumns": [
    {
      "name": "events",
      "type": "list",
      "subColumns": [
        {
          "name": "element",
          "type": "map",
          "subColumns": [
            { "name": "key", "type": "string" },
            { "name": "value", "type": "double" }
          ]
        }
      ]
    }
  ]
}
```

- 普通类型可用 `{"name":"label","type":"string"}`；primitive 类型兼容性由 GLS 最终校验。
- `struct` 至少一个子字段，`list` 恰好一个 element，`map` 恰好两个子项，按 key、value 顺序排列。
  struct 子字段名称和描述通过递归 `SubColumns` 传给 GLS；list/map 的子项按位置解释。
- `comment` 可选；`isOptional` 默认 `true`。GLS 的 map value 始终为 optional，map key 始终为 required；
  list element 的 optional 标记由 GLS 读取。已有数据的表新增 required 列可能不兼容。
- 使用递归 `subColumns`，不接收 `struct<...>` / `list<...>` / `map<...>` 内联类型字符串。
  最大嵌套深度为 32，最多 10000 个字段；同层子字段不得重名。
- 只操作顶层普通列；不支持向已有 struct 内添加/删除子字段。列名不得含点号或使用 `_magnus_` 前缀。
  不接收 `isPrimary`、分区 transform 或自定义字段 ID。
- 创建拒绝已存在的列；删除拒绝缺失列、分区列及其源列、`IsPrimary` / `pk.column.name` 标记的主键。
  预检要求表详情含明确的 columns、partitions、properties，读取失败或响应不完整时不提交。
- 仅 `--yes` 提交。删除使用 `IsLogicalDelete=false` 从 Schema 移除列，不会立即擦除已有数据文件。
  预检与写入不是原子操作，最终兼容性与权限由 GLS 校验；写请求不自动重试，超时后先读取 Schema 确认状态。
- `--json` 输出包括 `dry_run` / `success`、`submitted`、`dryRun`、`plan.request` 和 `warnings`。

## 创建 Catalog / Database

```bash
# 预览；读取 exists，但不提交创建请求
bytedcli magnus catalog create --catalog demo_catalog --warehouse hdfs://example-ns/warehouse/demo --description "Demo catalog" --property team=demo
bytedcli magnus database create --catalog demo_catalog --db-name demo_db --description "Demo database" --property team=demo
# 确认后提交，再读取验证
bytedcli magnus catalog create --catalog demo_catalog --warehouse hdfs://example-ns/warehouse/demo --description "Demo catalog" --property team=demo --yes
bytedcli magnus catalog exists --catalog demo_catalog
bytedcli magnus database create --catalog demo_catalog --db-name demo_db --description "Demo database" --property team=demo --yes
bytedcli magnus database get --catalog demo_catalog --db-name demo_db
```

- 名称只接受字母、数字、下划线；`--property key=value` 可重复，键和值保持大小写，值可包含 `=` 或为空。重复键、空键和冲突的 Warehouse/描述会拒绝。
- Catalog 通过 GLS `catalog/register` 创建 HADOOP catalog；`--warehouse` 同时写入 `Uri` 与 `Properties.warehouse`，`--description` 写入 `Properties.description`。省略描述时保留显式 property 中的 description，否则默认为空。
- Database 通过 GLS `database/create` 创建；`--description` 写入 `Comment`，位置由 GLS 基于所属 Catalog 推导。先创建所属 Catalog。
- 复用全局站点路由与 Cloud JWT。已按 CN DataLake 前端及 GLS 后端字段核验；各站点可用性与权限由对应 GLS 服务决定。HDFS Warehouse 需要当前用户读写权限；TOS Catalog 的后端额外要求 TOS AK/SK，本命令不接收这些凭据，TOS 创建仍需使用具备该凭据链路的入口。
- 默认 dry-run、只有 `--yes` 提交。存在性检查失败或资源已存在时拒绝提交；POST 不自动重试。超时后先用 `get` / `exists` 核对资源，避免重复创建。预览不会检查 Warehouse 权限，服务端在实际提交时校验。

## Table deletion

```bash
# Preview: checks table existence and shows the exact request without deleting
bytedcli magnus table delete --name demo_catalog.demo_db.demo_table
# Submit deletion of the actual table and underlying data
bytedcli magnus table delete --name demo_catalog.demo_db.demo_table --yes
# Verify metadata removal after submission or an uncertain response
bytedcli magnus table exists --name demo_catalog.demo_db.demo_table
```

`table delete` 复用当前站点的 GLS endpoint 和 Cloud JWT。请求为 `POST /api/v1/table/delete`，
显式设置 `UpdateActualTable=true`、`DeleteData=true`、`ForceDeleteReplica=false`，删除实际 Catalog 表及底层数据。
后端继续执行权限、副本和下游引用检查。Hadoop Catalog 会在删除表时直接移除表目录；其他 Catalog 的数据清理可能异步执行。
JSON 预览返回 `status: dry_run`、`submitted: false`、`result: null`，并包含 `plan.name`、完整 `plan.request` 和 `warnings`；
显式提交后返回 `submitted: true` 与后端操作结果。表不存在或存在性检查失败时停止，不提交删除。
该命令无法撤销删除；`SUCCESSFUL` 表示后端删表调用成功，不保证异步数据清理完成。删除 POST 不自动重试，
遇到超时或断连先检查 `table exists`，避免盲目重放；存在性读取与提交之间没有事务性锁，确认表名与并发操作后再提交。
