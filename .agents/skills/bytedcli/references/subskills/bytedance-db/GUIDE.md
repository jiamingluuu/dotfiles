---
name: bytedance-db
description: "Operate databases via bytedcli db: manage local database context, inspect or compare schema, run read-only SQL, inspect slow logs, and manage BPM or DBW work orders. Use when tasks mention db-cli, database context, table schema or Schema Diff, running SQL, slow logs, database authentication, or database tickets through bytedcli."
---

# bytedcli db

`bytedcli db` 的数据库操作由 db-cli 提供，运行时按需拉取到 `~/.local/share/bytedcli/dependency/db/`，无需手动安装插件；`db bpm` 的 BPM 工单命令和 `db ticket` 的 DBW 工单命令也由 db-cli 执行。

支持 macOS、Linux 和 Windows 的 AMD64/ARM64；Windows 会按需下载并执行对应的 `.exe` 运行时。

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

- 管理本地数据库上下文（新增/切换/查看当前默认库）
- 列出当前库下的表、查看表结构（字段/索引/主键）
- 比较两份 MySQL Schema 并生成增量 DDL
- 在指定实例上执行 SQL
- 获取慢日志明细
- 申请数据库权限，以及管理 BPM、DBW 工单

## 前置条件

- 使用通用调用方式：`../../invocation.md`
- 需要鉴权时先登录：`bytedcli auth login`
- 实际执行数据库操作前，Agent 默认先尝试运行 `bytedcli db +update`，以使用最新的 db-cli 能力和修复；这是推荐的版本准备步骤，不是强制要求。若用户明确不更新、当前环境不便更新或更新失败，应说明情况并继续使用当前本地版本，不要因此阻断用户任务
- 多数命令的 `--database`/`--type`/`--vdc`/`--region` 可省略，缺省时从 `db context` 当前上下文读取；建议先用 `bytedcli db context add ...` 设置默认库

> 执行前缀见 `../../invocation.md`；下面示例直接写 `bytedcli`。

## 数据库鉴权

`bytedcli db` 支持个人账号和服务账号两类 ByteCloud 鉴权；两类凭据可以同时存在，通过全局 `--as auto|user|app` 选择身份。bytedcli 与独立安装的 `db-cli` 使用不同的 AppKey 和凭据目录，持久化登录态互不读取；使用哪个入口，就通过该入口单独登录。bytedcli 调用其下载的 db-cli 子进程时会为单次执行注入已解析的 JWT，这不会写入独立 db-cli 的登录态。

```bash
# 个人账号
bytedcli --site cn auth login
bytedcli --site cn --json auth status
bytedcli --site cn --as user db list

# 服务账号；交互终端会隐藏输入 SK
bytedcli --site cn auth app set --access-key-id <AK>
bytedcli --site cn auth app status --refresh
bytedcli --site cn --as app db list
```

SK 不支持命令行明文参数，应从隐藏终端、stdin 或 `--secret-file` 输入。服务账号不继承个人权限；涉及申请人、审批人或人工审计语义的数据库操作优先使用个人账号。不要要求用户在对话中粘贴 AK/SK、refresh token 或 JWT。详细命令和清理行为见 [references/db.md](references/db.md#数据库鉴权)。

使用 ByteRDS 前，前往“RDS 授权管理 > 平台授权列表”，确保拥有 `rds.viewer` 或更高权限的角色。
执行 SQL 还需申请 write PSM 权限；DBW 实际执行查询时默认使用 read PSM。

## Quick start

命令分组：`db context`、`db schema`、`db sql`、`db ops`、`db slow`、`db slow-log`、`db space`、`db trx-lock`、`db bpm`、`db ticket`、`db bytedoc`、`db redis`，以及更新命令 `db +update`。

```bash
# 默认先尝试更新到最新 db-cli；更新失败时仍可继续使用当前版本
bytedcli db +update

# 上下文管理：新增一个默认库（--type 数据库类型，--vdc 机房，二者必填）
bytedcli db context add mydb --type mysql --vdc lf

# 查看当前默认库 / 列出全部 / 查看指定库详情 / 切换 / 删除 / 切回上一个
bytedcli db context --current
bytedcli db context list
bytedcli db context get otherdb
bytedcli db context set otherdb
bytedcli db context delete otherdb
bytedcli db context -

# 列出当前库下的表（可用 --query 过滤、--page/--page-size 翻页）
bytedcli db schema list
bytedcli db schema list --database mysql-xxxx --type mysql --vdc lf --query user --page 1 --page-size 50

# 查看指定表结构（表名用 --table）
bytedcli db schema get --table users
bytedcli db schema get --table users --database mysql-xxxx --type mysql --vdc lf --format ddl

# 比较 MySQL Schema 并生成增量 DDL；只生成计划，不执行 DDL
bytedcli db schema diff --before before.sql --after after.sql --output delta.sql
bytedcli --site boe --json db schema diff \
  --target current_db --source desired.sql \
  --vregion China-BOE --vdc boe --route auto \
  --table users,orders

# 执行 SQL（--sql 必填）
bytedcli db sql execute --sql "select * from users limit 10"
bytedcli db sql execute --database mysql-xxxx --type ByteRDS --region cn --sql "select 1" --format json

# 分片键范围查询仅在用户明确接受风险后使用确认参数
bytedcli db sql execute --database demo_db --vregion China-BOE \
  --sql "SELECT * FROM orders WHERE user_id BETWEEN 1 AND 100" \
  --confirm-risky-shard-query

# SQL 安全审核：当前支持 MySQL/VeDBMySQL，不支持 PostgreSQL
bytedcli db sql eval security --instance vedbm-sample --type VeDBMySQL --database demo_db --vregion ChinaSinf-North \
  --sql "CREATE TABLE demo_table(id INT, name VARCHAR(64), content TEXT)"

# SQL 性能分析与 rewrite：当前只支持 PostgreSQL
bytedcli --json db sql eval performance --instance postgres-sample \
  --sql "SELECT * FROM orders WHERE user_id IN (SELECT id FROM users)" \
  --db-metadata '{"demo":{"orders":{"ddl":"CREATE TABLE orders(id bigint, user_id bigint)"},"users":{"ddl":"CREATE TABLE users(id bigint PRIMARY KEY)"}}}'

# 获取慢日志明细（--region/--database/--start-time/--end-time 必填，时间为秒级 epoch）
bytedcli db slow-log get --region cn --database mysql-xxxx --type mysql --start-time 1700000000 --end-time 1700003600

# 聚合慢日志、表空间、死锁和实时事务锁（按 VRegion 自动选择 DBW/RDS）
bytedcli --site boe db slow-log aggregate demo_db --vregion China-BOE --region boe \
  --start-time 1700000000 --end-time 1700003600
bytedcli --site boe db space table demo_db --vregion China-BOE --region boe --page 1 --page-size 10
bytedcli --site boe db trx-lock deadlock demo_db --vregion China-BOE --region boe
bytedcli --site boe db trx-lock transaction-list demo_db --vregion China-BOE --region boe \
  --page 1 --page-size 10

# ByteDoc 变更工单（仅 China-BOE/China-BOE2 的火山 Mongo）
bytedcli --site boe db bytedoc ticket --database demo_db --vregion China-BOE \
  --operate-type DataChange --collection demo_collection \
  --memo "update demo records; rollback: reverse update" \
  --sql 'db.demo_collection.updateMany({status: 0}, {$set: {status: 1}})'

# ByteRedis 工单入口和大 Key 查询（ticket 只返回控制台入口，不会创建工单）
bytedcli db redis ticket --psm cache.demo --vregion China-North
bytedcli db redis big-keys list --psm cache.demo --date 2026-08-01 \
  --begin 00:00:00 --end 23:59:59 --page 1 --page-size 10 --vregion China-North

# 运维详情、实时慢会话与健康诊断（按 VRegion 自动选择 DBW/RDS）
bytedcli db ops detail demo_db --region cn
bytedcli db slow list demo_db --region cn --port 3306
bytedcli db slow diag demo_db --region cn --page 0 --page-size 20

# BPM 工单：创建 SQL 变更、查看/推进多区域变更单、申请权限和查询工单
bytedcli --site boe db bpm create --dbname demo_db \
  --sql "ALTER TABLE demo_table ADD COLUMN c INT" --background "sample schema change"
bytedcli --site us-ttp db bpm change-record get 12574
bytedcli --site us-ttp db bpm change-record execute 12574 --region US-TTP2
bytedcli --site boe db bpm permission apply --dbname demo_db --region boe --user-list sample.user
bytedcli --site boe db bpm list --db-name demo_db
bytedcli --site boe db bpm get 12345

# DBW 工单：创建 DDL/DML、查询、预检、提交、审批、执行、取消
bytedcli --site cn db ticket create-ddl \
  --instance-id vedbm-sample \
  --database demo_db \
  --sql "CREATE TABLE demo_table(id BIGINT PRIMARY KEY)" \
  --memo "create demo table" \
  --vregion ChinaSinf-North
bytedcli --site cn db ticket create-dml \
  --instance-id vedbm-sample \
  --database demo_db \
  --sql "UPDATE demo_table SET status = 1 WHERE id = 100" \
  --memo "repair demo data" \
  --vregion ChinaSinf-North
bytedcli --site cn db ticket get --ticket-id "<ticket_id>" --instance-id vedbm-sample
bytedcli --site cn db ticket precheck --ticket-id "<ticket_id>" --instance-id vedbm-sample
bytedcli --site cn db ticket submit --ticket-id "<ticket_id>" --instance-id vedbm-sample
bytedcli --site cn db ticket approve --ticket-id "<ticket_id>" --instance-id vedbm-sample --workflow-id sample-workflow
bytedcli --site cn db ticket execute --ticket-id "<ticket_id>" --instance-id vedbm-sample
bytedcli --site cn db ticket cancel --ticket-id "<ticket_id>" --instance-id vedbm-sample --reason "sample reason"

# 字节云 ByteRDS 工单不需要 instance-id
bytedcli --site boe db ticket create-ddl --database demo_db \
  --sql "CREATE TABLE demo_table(id BIGINT PRIMARY KEY)" --memo "create demo table" --vregion China-BOE
bytedcli --site cn db ticket create-dml --database demo_db \
  --sql "UPDATE demo_table SET status = 1 WHERE id = 100" --memo "repair demo data" --vregion ChinaSinf-North
bytedcli --site boe db ticket get --ticket-id "<ticket_id>" --instance-type ByteRDS

# 更新 db-cli 到最新（或指定版本）
bytedcli db +update
bytedcli db +update 0.1.4
```

## Notes

- 结构化输出：对 `list`/`search`/`get`/`topology`/`qps`/`overview`/`ops`/`bpm`/`bytedoc`/`redis`/`slow`/`schema`/`sql`/`slow-log`/`space`/`ticket`/`trx-lock`，全局 `--json` 会由 bytedcli 统一转换成 db-cli 的 `--format json`。`context` 等本地命令不支持结构化输出
- `db slow-log aggregate`、`db space table`、`db trx-lock deadlock`、`db trx-lock transaction-list` 支持 `--route auto|dbw|rds`。`auto` 在 `China-North`、`China-North5`、`ChinaSinf-North`、`China-East`、`China-Fintech`、`China-BOE`、`Singapore-Central` 走 DBW，其余已登记 VRegion 走 RDS；`dbw` 强制 DBW，目标 VRegion 不在该范围时明确失败；`rds` 强制 RDS
- 四个命令的 DBW 路径会先通过 `DescribeInstances` 解析实例；事务锁命令还会通过 `DescribeInstanceNodes` 自动选择 Primary。RDS 路径分别使用 RDS 聚合慢日志、只读 `information_schema.tables` 查询，或 Topology + Engine Status。特殊 VDC/region 映射（包括 `nonttap` / `sinf-my`）由 db-cli 统一处理
- `db bpm create` 根据 VRegion、SQL 类型和实例来源选择 RDS/BPM 或 DBW；`db bpm change-record get|execute` 分别只读查看和显式推进 ByteHeart 多区域变更单。它们与 `rds bpm` 同名入口使用同一套路由、校验与输出逻辑
- `db bpm permission apply` 以及 `db bpm get|list|cancel|update|get-workflow-config` 由 db-cli 直接请求 BPM；参数和文本输出顺序与对应的 `rds bpm` 命令保持一致
- `db ticket create-ddl|create-dml|get|precheck|submit|approve|execute|cancel` 直接请求 DBW；创建 DDL/DML 必须传 `--memo` 说明变更背景；`execute` 用于执行审批后处于 `TicketWaitExecute` 的手动执行工单，并以 `Result.AllPass` 判定请求是否成功
- `--ticket-execute-type` 控制预检通过后的执行方式：直接入口 `db ticket create-ddl|create-dml` 沿用 db-cli 默认值 `Manual`；兼容入口 `rds bpm dbw ticket create-ddl` 的 bytedcli 包装器默认 `Auto`，`create-dml` 默认 `Manual`。`Auto` 表示预检/审批通过后由 DBW 自动执行；`Manual` 需人工触发，且部分安全规则如“添加唯一索引”只允许手动执行；`Cron` 在指定时间窗内定时执行
- `db ticket create-ddl` 的 `--execute-mode`：**平时不要带**。仅当 DDL 添加唯一键索引、预检通过后才触发——此时命令不自动提交，而在提交前返回结构化信号（`action: precheck_execute_mode_required`，含 `execute_mode_enum`、`execute_mode_default`、`execute_mode_hint`），无论是否 `--format json` Agent 都能看到。收到该信号时须把风险与两种执行方式展示给用户，让其选择后带参数**从头重新执行** `create-ddl`（新工单）：`unlock`（无锁执行，默认 → `IsUnlock=true`；有重复键只保留一条、其余丢失）、`native`（原生执行 → `IsUnlock=false`；有重复键索引添加直接失败）。带 `--execute-mode` 重跑时按所选方式提交、仅 stderr 提示风险；传非 `unlock`/`native` 值报错
- 支持区域内的 MySQL 兼容火山实例 DDL/DML 统一执行 `CreateTicket → DescribePreCheckDetail → SubmitTicket`。创建时省略实例上下文会先用 `DescribeInstances` 自动识别 ByteRDS，未命中再解析火山 MySQL 兼容实例；查不到或有歧义时再显式提供 `--instance-type` / `--instance-id`。字节云 DML 在 `China-BOE`、`China-BOE2`、`ChinaSinf-North`、`Asia-SouthEastBD` 可用；字节云 DDL 在 `China-BOE`、`China-BOE2` 可用；其余 VRegion 的字节云 DDL/DML 走 RDS/BPM。`ChinaSinf-North` 默认使用 `RegionId=huabei2`，`Asia-SouthEastBD` 默认使用 `RegionId=bdsgdt`，旧 `--request-region-id` 仅为兼容解析，不会下发给 DBW
- 工单后续操作同样区分实例类型：Volc/默认 `VeDBMySQL` 必须提供 `--instance-id`，字节云 `ByteRDS` 可以省略；显式 `--site`、`--vregion`、`--region-id` 优先于默认映射
- `db bytedoc ticket` 创建 ByteDoc 变更工单，仅支持 `China-BOE`/`China-BOE2` 的火山 Mongo；支持 `DataChange`、`EnableShardCollection`、`DropCollection`、`CreateIndex`、`ModifyIndex`、`DropIndex`，其他 ByteDoc 模式使用命令返回的控制台入口
- ByteRedis 没有程序化工单 API；`db redis ticket` 只返回扩缩容、执行命令、删 Key 等控制台工单入口。`db redis big-keys list` 查询大 Key，BOE 站点及映射到 BOE 的 VRegion 不支持该能力
- 参数语义：`--database` 是数据库实例 ID（如 `mysql-67245173607b`）；`--type` 是数据库类型（如 `mysql`、`ByteRDS`、`bytedoc`）；`schema` 系列用 `--vdc`（机房，如 `lf`/`cn`/`ce`/`boe`），`sql execute` 与 `slow-log get` 用 `--region`（地域）
- `sql execute` 对 `MySQLSharding` 和 RDS 元数据中 `is_sharding=true` 的 `ByteRDS` 启用分片键风险检查。只有分片键单值等值查询默认执行；`IN (...)`、`BETWEEN`、`NOT BETWEEN`、`> < >= <=`、`!=`/`<>`、`NOT IN`、`LIKE`/`NOT LIKE` 等会在真实 SQL 发出前报错并提示跨分片慢 SQL 风险。这是合理且在预期范围内的安全保护，不是服务异常；优先改写为单值等值，只有用户明确接受风险时才加 `--confirm-risky-shard-query`。Agent 可以提示用户为当前任务设置适用于全部分片风险查询的免确认分片数量阈值；用户尚未明确给出并确认阈值时，Agent 不得自行添加确认参数。设置后，也只有能够可靠判断本次涉及的分片数严格小于阈值时才可自动添加，达到/超过阈值或无法判断时仍需确认。RDS 分片元数据或 dbatman 不可用时会告警并 fail-open 继续执行，需向用户说明潜在风险
- SQL 评估必须显式选择下一级入口：`db sql eval security` 调用 DBW `SqlReview`，当前支持 MySQL/VeDBMySQL、不支持 PostgreSQL；`db sql eval performance` 调用 PG Rewrite，当前只支持 PostgreSQL。两者都只返回建议，不执行 SQL，也不自动采用建议
- 裸 `db sql eval` 在实现上保留 Security 与 Performance 的兼容/组合路由，但两项能力当前支持的数据库类型不相交，不能作为完整的 PostgreSQL 双视角检查。实际使用不要直接调用裸 `eval`，应分别调用 `security` 或 `performance`
- context 的 `--vdc` 会映射为 VRegion：`cn`/`lf` → `China-North`，`ce` → `China-East`，`boe`/`boe2` → `boe`；其他值原样保留
- `schema list`、`schema get`、`sql execute` 和 `sql eval security` 支持 `--dry-run`，不发真实请求、只返回响应示例，便于确认参数；ByteRDS/MySQL 的 `schema list/get` 还支持 `--vregion` 与 `--mode auto|legacy|dbw`：默认按 VRegion 选择 DBW 或 RDS，`legacy` 强制 RDS，`dbw` 强制 DBW
- `db context add <dbname>` 的 `--type` 与 `--vdc` 均为必填；未设置当前上下文时首个添加的库会成为默认库
- `+update` 是元命令（`+` 前缀），不会与库名/表名冲突；`+update` 完全在 bytedcli 层处理，用于更新本地 db-cli。Agent 在每次数据库任务开始、首次调用 db-cli 前默认尝试一次即可，不需要在同一任务的每条命令前重复更新，也不能把更新成功作为继续执行的硬性条件
- 部分特殊数据库被登记为禁止通过 bytedcli 执行 SQL：`sql execute` 与 `ticket create-ddl|create-dml` 命中禁入清单时会以 `DB_SQL_BLOCKED` 错误拒绝（错误信息包含登记原因）。此时应改用该库负责方自己的工具，不要尝试绕过；清单登记方式见仓库 `CONTRIBUTING.md` 的「DB SQL 操作禁入清单」

## References

- `references/db.md`
- `../../invocation.md`
