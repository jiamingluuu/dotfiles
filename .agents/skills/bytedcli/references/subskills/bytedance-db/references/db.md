# db

`bytedcli db` 目前支持以下命令。参数缺省时会从 `db context` 当前上下文读取。

## 数据库鉴权

`bytedcli db` 支持个人账号和服务账号两类 ByteCloud 鉴权。两类凭据可以同时存在；全局 `--as auto|user|app` 控制数据库命令使用的身份。

```bash
# 个人账号登录、状态与登出
bytedcli --site cn auth login
bytedcli --site cn --json auth status
bytedcli --site cn auth logout

# 保存、检查和清除当前认证 site 的服务账号 AK/SK
bytedcli --site cn auth app set --access-key-id <AK>
bytedcli --site cn auth app status --refresh
bytedcli --site cn auth app clear --yes

# 显式选择数据库命令的身份
bytedcli --site cn --as user db list
bytedcli --site cn --as app db list
```

- `auth app set` 不接受 SK 命令行参数。未传 `--secret-file` 时，交互终端使用隐藏输入，非交互场景从 stdin 读取。
- `auth logout` 默认只清理个人登录态并保留服务账号；`auth logout --reset-app` 同时清理当前认证 site 的 AK/SK。
- bytedcli 与独立安装的 `db-cli` 使用不同的 AppKey 和凭据目录，持久化登录态互不读取或清除；使用哪个入口，就通过该入口单独登录。`bytedcli db ...` 启动其下载的 db-cli 子进程时会为该次调用注入当前 JWT，但不会把 bytedcli 登录态保存到独立 db-cli 目录。
- 凭据按认证 site 隔离。服务账号不会继承个人 IAM 或数据库权限；涉及申请人、审批人或人工审计语义的操作优先使用个人身份。
- 只有用户明确要求获取 JWT 文本时才执行 `bytedcli auth get-bytecloud-jwt-token`，且不要记录、转发或复述输出。

## 上下文管理（db context）

本地维护一组数据库上下文，命令缺省的 `--database`/`--type`/`--vdc` 均从当前上下文读取。

```bash
# 新增一个数据库上下文（--type、--vdc 必填；首个添加的库会成为默认库）
bytedcli db context add mydb --type mysql --vdc lf

# 查看当前默认库
bytedcli db context --current

# 列出全部已配置的库（当前库前带 * 标记）
bytedcli db context list

# 查看指定库详情（省略库名时等价于查看当前默认库）
bytedcli db context get otherdb

# 切换当前库
bytedcli db context set otherdb

# 删除一个库（别名 rm）
bytedcli db context delete otherdb

# 切回上一个库
bytedcli db context -
```

- `--type`：数据库类型，例如 `mysql`、`redis`、`bytedoc`
- `--vdc`：机房标识，例如 `lf`、`cn`、`ce`、`boe`；会映射为 VRegion（`cn`/`lf` → `China-North`，`ce` → `China-East`，`boe`/`boe2` → `boe`）

## 表结构（db schema）

```bash
# 列出当前库下的所有表
bytedcli db schema list

# 指定实例/类型/机房，并按关键字过滤、翻页
bytedcli db schema list --database mysql-xxxx --type mysql --vdc lf --query user --page 1 --page-size 50

# 查看指定表的建表 SQL 与字段结构
bytedcli db schema get --table users

# 以 DDL 形式输出建表语句
bytedcli db schema get --table users --database mysql-xxxx --type mysql --vdc lf --format ddl

# 不发真实请求，仅返回响应示例
bytedcli db schema list --dry-run
bytedcli db schema get --table users --dry-run
```

- `schema list` flags：`--database`、`--type`、`--vdc`、`--query`（表名搜索关键字）、`--page`、`--page-size`、`--format`（默认 table）、`--dry-run`
- `schema get` flags：`--table`（表名，必填）、`--database`、`--type`、`--vdc`、`--vregion`、`--mode {auto|legacy|dbw}`（仅 ByteRDS/MySQL）、`--format {table|json|ddl}`、`--dry-run`

### Schema Diff

`db schema diff` 比较两份 MySQL Schema，生成把 before/target（当前态）变为 after/source（期望态）的增量 DDL。输入可以是 SQL 文件或在线库，支持文件与在线库的任意组合。

```bash
# 文件与文件
bytedcli db schema diff \
  --before before.sql --after after.sql \
  --format sql --output delta.sql

# 在线库与文件；--table 可重复或使用逗号分隔
bytedcli --site boe --json db schema diff \
  --target current_db --source desired.sql \
  --vregion China-BOE --vdc boe --route auto \
  --type ByteRDS --table users,orders

# 在线库与在线库
bytedcli --site boe db schema diff \
  --before current_db --after desired_db \
  --vregion China-BOE --vdc boe --route auto \
  --type ByteRDS --format sql
```

- `--before`/`--target` 表示当前态，`--after`/`--source` 表示期望态；同组参数是别名，不可同时传。
- `--format sql|json` 控制增量 SQL 或结构化计划；`-o, --output` 将结果写入文件。
- 在线来源复用 `schema list/get` 的 DBW/RDS 路由，只读取 Schema。命令没有 `--apply`，不会向数据库执行生成的 DDL。
- SQL 输出会标记 destructive/rewrite 风险，JSON 输出在 `safety_report` 中提供结构化标记；结果必须人工审阅后再通过工单执行。
- 当前只支持完整 MySQL `CREATE TABLE` 定义。rename、视图、存储过程、函数、触发器、事件、函数索引、不可见索引和 FULLTEXT/VECTOR/COLUMNAR 索引不支持。

## 执行 SQL（db sql execute）

```bash
# 执行 SQL（--sql 必填），缺省从当前上下文取库/地域
bytedcli db sql execute --sql "select * from users limit 10"

# MySQL 查询（无需 --type，自动识别实例类型）
bytedcli db sql execute --database demo_db --region cn --sql "select 1" --format json

# ByteRedis 查询（传 --psm 自动识别，无需 --type）
bytedcli db sql execute --psm cache.demo --vregion China-North --sql 'GET demo-key' --format json

# ByteDoc/Mongo 查询（必须显式传 --type）
bytedcli db sql execute --type ByteDoc --database demo_db --vregion China-BOE --sql 'db.demo_collection.find({})' --format json

# 干跑，仅返回响应示例
bytedcli db sql execute --sql "select 1" --dry-run

```

`db sql execute` 仅接受单条只读 SQL：`SELECT`、`SHOW TABLES`、`SHOW CREATE TABLE`、`EXPLAIN SELECT`。DDL、DML、事务、锁与多语句会在请求前被拒绝；需要变更请改用 DBW/RDS 工单命令。

### `--type` 参数使用规则

| 实例类型                        | 是否需要 `--type` | 说明                                                                              |
| ------------------------------- | ----------------- | --------------------------------------------------------------------------------- |
| **MySQL / ByteRDS / VeDBMySQL** | 不需要            | 实例类型通过 `DescribeInstances` API 自动识别，显式值会被服务端返回的真实类型覆盖 |
| **MySQLSharding（分片库）**     | 不需要            | 自动识别为 `MySQLSharding`，分片键风险拦截自动生效                                |
| **ByteRedis**                   | 不需要            | 传 `--psm <redis-psm>` 即自动识别为 Redis 查询模式                                |
| **ByteDoc / Mongo**             | **必须传**        | 使用 `--type ByteDoc` 或 `--type Mongo` 区分路由模式                              |

- flags：`--sql`（必填，待执行的 SQL）、`--database`（逻辑库名；DBW 路由自动解析真实实例 ID）、`--db-name`（逻辑库名，默认等于 `--database`）、`--type`（仅 ByteDoc/Mongo 查询需要）、`--region`（地域）、`--vregion`（VRegion）、`--psm`（ByteRedis PSM）、`--confirm-risky-shard-query`（确认执行分片键 `IN`、范围/非等值查询）、`--format`（默认 table）、`--dry-run`

### 分片键范围查询保护

`db sql execute` 对 `MySQLSharding`，以及 RDS v3 元数据中 `is_sharding=true` 的 `ByteRDS` 启用分片风险检查。确认是分片库后，命令通过当前 DBW/RDS 路由执行 `dbatman show 'table' info` 获取 SQL 涉及表的分片键，再判断 SELECT 是否对分片键使用了 `IN`、范围或非等值条件；不依赖 Engine/NDB 字段。

```bash
# 分片键单值等值命中单分片，正常放行
bytedcli --site boe db sql execute --type MySQLSharding \
  --database shard_db --vregion China-BOE \
  --sql "SELECT * FROM shard_t1 WHERE id = 1 LIMIT 1"

# 分片键 IN、范围/非等值默认被拦截并提示慢 SQL 风险
bytedcli --site boe db sql execute --type MySQLSharding \
  --database shard_db --vregion China-BOE \
  --sql "SELECT * FROM shard_t1 WHERE id IN (1, 2, 3) LIMIT 1"

# 确需执行 IN/范围查询时加 --confirm-risky-shard-query 放行
bytedcli --site boe db sql execute --type MySQLSharding \
  --database shard_db --vregion China-BOE \
  --sql "SELECT * FROM shard_t1 WHERE id IN (1, 2, 3) LIMIT 1" \
  --confirm-risky-shard-query
```

- `MySQLSharding` 按实例类型直接确认；所有 `ByteRDS` 都查询 RDS v3 详情，只有 `is_sharding=true` 才进入分片键判定。详情接口失败或缺少字段时会告警，并按非分片库继续执行
- 只有分片键单值等值（`shard_key = xxx`）默认放行；`IN (...)`、`BETWEEN`/`NOT BETWEEN`、`> < >= <=`、`!=`/`<>`、`NOT IN`、`LIKE`/`NOT LIKE` 等均提示风险
- 命中风险且未加 `--confirm-risky-shard-query` 时，命令在真实 SQL 发出前报错并给出改写建议。这是用于避免多/全分片扇出、慢 SQL 和 DBAS Kill 的预期保护，不是 RDS/DBW 服务异常，不应无确认地循环重试
- 优先改写为分片键单值等值；只有用户明确接受风险时才加 `--confirm-risky-shard-query`。该 flag 跳过本次分片识别和分片键检查，原 SQL 随后照常执行
- Agent 可以提示用户为当前任务设置“免二次确认的分片数量阈值”，例如“预计涉及少于 5 个分片时无需再次确认”。它适用于 `IN`、`BETWEEN`、比较、`LIKE`、`NOT IN` 等全部分片风险查询。用户尚未明确给出并确认阈值时，Agent 不得自行添加 `--confirm-risky-shard-query`；用户设置后，只有能够基于分片元数据、路由规则或用户提供的映射可靠判断本次查询涉及的分片数严格小于阈值时，才可自动添加。达到/超过阈值或无法判断时仍需再次确认。该阈值只属于当前任务中的 Agent 预授权，不是 CLI 参数或持久化配置，不得跨任务沿用
- 检测 fail-open：非 SELECT、SQL 未引用表、dbatman 调用失败或没有拿到相关表的分片键时不拦截；元数据失败会输出警告后继续执行

## SQL 评估（db sql eval）

SQL 评估提供两个建议入口，当前必须显式选择下一级子命令，不要直接使用裸 `db sql eval`：

| 入口                      | 作用                                                      | 当前数据库支持范围                      |
| ------------------------- | --------------------------------------------------------- | --------------------------------------- |
| `db sql eval security`    | 调用 DBW `SqlReview`，检查 SQL 是否命中安全规则并返回建议 | 支持 MySQL/VeDBMySQL；不支持 PostgreSQL |
| `db sql eval performance` | 调用 PG Rewrite，分析 SQL 并在需要时返回 rewrite 建议     | 只支持 PostgreSQL                       |

两种入口都不会执行 SQL，也不会自动采用建议，是否接受由用户自行决定。裸 `db sql eval` 在代码中保留了 Security 与 Performance 的兼容/组合路由，但两项能力当前支持的数据库类型不相交，因此不能对同一个 PostgreSQL 实例完成双视角检查，也不应作为实际业务入口。

### Security 安全审核

Security 逐条返回是否通过、风险等级（High/Middle/Low）与命中的规则，用于 MySQL/VeDBMySQL 变更前的静态检查。DDL/DML 均可送审。

```bash
# 审核单条 SQL（--instance/--type/--database/--sql 必填）
bytedcli db sql eval security \
  --instance vedbm-sample --type VeDBMySQL --database demo_db \
  --vregion ChinaSinf-North \
  --sql "CREATE TABLE demo_table(id INT, name VARCHAR(64), content TEXT)"

# 审核多条：重复 --sql（单次最多 10 条）
bytedcli db sql eval security \
  --instance vedbm-sample --type VeDBMySQL --database demo_db --vregion ChinaSinf-North \
  --sql "ALTER TABLE demo_table ADD COLUMN age INT" \
  --sql "UPDATE demo_table SET age = 0 WHERE age IS NULL"

# JSON 输出（含完整 SQL 与命中规则明细）
bytedcli --json db sql eval security --instance vedbm-sample --type VeDBMySQL --database demo_db \
  --vregion ChinaSinf-North --sql "select 1"

# 干跑，仅返回响应示例
bytedcli db sql eval security --instance vedbm-sample --type VeDBMySQL --database demo_db \
  --vregion ChinaSinf-North --sql "select 1" --dry-run
```

- flags：`--instance`（必填，实例 ID，如 `vedbm-xxxx`）、`--type`（必填，实例类型，如 `VeDBMySQL`/`ByteRDS`）、`--database`（必填，库名）、`--sql`（必填，待审核 SQL；**可重复传入以提交多条，单次最多 10 条**）、`--vregion`（机房路由；缺省取全局 `--vregion` 或站点默认）、`--region`（实例所在 VDC，如 `huabei2`/`boe`，用于后端定位实例；缺省按 VRegion 推导默认 VDC）、`--format`（默认 table）、`--dry-run`
- `--sql` 按“不切分逗号”的方式解析：含逗号的完整 SQL（如多列 DDL）会作为**一条**送审，不会被逗号误拆；多条务必用重复的 `--sql`，不要在一个 `--sql` 里用逗号拼接
- table 输出先给总体审核结论，再按 SQL 逐条列出风险计数（High/Middle/Low），最后展开命中规则明细；`--format json` 保留每条 SQL 的完整语句与规则字段
- 与 `sql execute` 共用一套机房路由：`--vregion` 决定网关站点（`X-TOP-Region`/JWT host），并连同 `--region`（VDC）一起用于后端定位实例；`ChinaSinf-North` 默认 VDC 为 `huabei2`

### Performance 性能分析与 rewrite

Performance 每次只接受一条 PostgreSQL SQL，并要求 `--db-metadata` 提供相关表的 DDL。默认提交 PG Rewrite 异步任务并等待终态；也可以只提交、查询一次或等待已有任务。

```bash
# 默认 submit + wait
bytedcli --json db sql eval performance \
  --instance postgres-sample \
  --sql "SELECT * FROM orders WHERE user_id IN (SELECT id FROM users)" \
  --db-metadata '{"demo":{"orders":{"ddl":"CREATE TABLE orders(id bigint, user_id bigint)"},"users":{"ddl":"CREATE TABLE users(id bigint PRIMARY KEY)"}}}'

# 只提交，立即返回服务端 task ID
bytedcli --json db sql eval performance --async \
  --instance postgres-sample --sql "SELECT 1" \
  --db-metadata '{"demo":{"sample_table":{"ddl":"CREATE TABLE sample_table(id int)"}}}'

# 查询一次，或等待已有任务进入终态
bytedcli --json db sql eval performance --task-id sqlrewrite_pg_sample
bytedcli --json db sql eval performance --task-id sqlrewrite_pg_sample --wait --poll 2 --max-wait 1800

# 仅在显式排障时检查 PG Rewrite 服务健康状态
bytedcli --json db sql eval performance health
```

- 默认执行 `submit + wait`；`--async` 只 submit；`--task-id` 单次 get；`--task-id --wait` 持续轮询
- `--db-metadata` 必须是 `{database: {table: {ddl: string}}}` JSON object；创建任务时必须提供，查询已有任务时不需要
- `status=succeeded` 且 `result.code=0` 表示产生 rewrite 建议；`result.code=1001` 表示无需改写，两者都属于成功结果
- 正常 submit/get/wait/rewrite 不会自动执行 health。遇到服务不可达、请求超时或 HTTP 5xx 时，再由用户显式运行 `db sql eval performance health`

## 慢日志（db slow-log get）

```bash
# 获取慢日志明细（时间为秒级 epoch）
bytedcli db slow-log get \
  --region cn \
  --database mysql-xxxx \
  --type mysql \
  --start-time 1700000000 \
  --end-time 1700003600
```

- 必填：`--region`（地域）、`--database`（实例 ID）、`--start-time`、`--end-time`（秒级时间戳）
- 选填：`--type`（数据库类型）、`--page-number`、`--page-size`、`--search-param`、`--sort-by`、`--order-by`、`--node-id` 等；`--format` 控制输出格式

## 聚合慢日志、表空间与事务锁

这四个只读命令由 db-cli 实现，并按照 database-toolbox 的能力范围在 DBW 与 RDS 之间路由：

```bash
# 聚合指定时间范围内的慢日志
bytedcli --site boe db slow-log aggregate demo_db \
  --vregion China-BOE --region boe \
  --start-time 1700000000 --end-time 1700003600 \
  --page 1 --page-size 10 --route auto

# 查询数据库表空间；可用 --table-name 精确过滤表名
bytedcli --site boe db space table demo_db \
  --vregion China-BOE --region boe \
  --table-name demo_table --page 1 --page-size 10 --route auto

# 查询最近一次死锁；DBW 路径不传 --node-id 时自动选择 Primary
bytedcli --site boe db trx-lock deadlock demo_db \
  --vregion China-BOE --region boe --route auto

# 查询实时事务与锁；DBW 路径不传 --node-id 时自动选择 Primary
bytedcli --site boe db trx-lock transaction-list demo_db \
  --vregion China-BOE --region boe \
  --page 1 --page-size 10 --route auto
```

### 路由规则

四个命令共享以下 DBW 能力范围：

| VRegion             | `--route auto` |
| ------------------- | -------------- |
| `China-North`       | DBW            |
| `China-North5`      | DBW            |
| `ChinaSinf-North`   | DBW            |
| `China-East`        | DBW            |
| `China-Fintech`     | DBW            |
| `China-BOE`         | DBW            |
| `Singapore-Central` | DBW            |
| 其他已登记 VRegion  | RDS            |

- `--route auto`：使用上表切流；DBW 范围之外回退 RDS。
- `--route dbw`：强制 DBW；VRegion 不在上表范围时在发请求前明确失败，不静默回退 RDS。
- `--route rds`：强制 RDS，即使当前 VRegion 已支持 DBW。
- `--vregion` 决定能力切流和目标区域；`--region` 是目标 VDC/RDS region。两者同时提供时必须属于同一组映射，否则在发请求前失败。
- 未传 `--vregion` 时，先尝试从 `--region` 反推；仍无法确定时使用全局 `--vregion` 或 `--site` 的默认 VRegion。未传 `--region` 时使用目标 VRegion 的默认 VDC/RDS region。

特殊 VDC 到 RDS API region 的映射由 db-cli 处理：

| VDC/输入 region | RDS API region    | 说明                                       |
| --------------- | ----------------- | ------------------------------------------ |
| `ce`            | `China-East`      | VDC 与 API region 不同                     |
| `multicloud`    | `ChinaSinf-North` | VDC 与 API region 不同                     |
| `huabei2`       | `sinf`            | VDC 与 API region 不同                     |
| `sgcompliance`  | `awssg`           | VDC 与 API region 不同                     |
| `nonttap`       | `sinf-my`         | 使用 Asia-SouthEastBD 的特殊 RDS host/path |

### 每条命令的后端执行链路

| 命令                           | DBW 路径                                                          | RDS 路径                                                                   |
| ------------------------------ | ----------------------------------------------------------------- | -------------------------------------------------------------------------- |
| `db slow-log aggregate`        | `DescribeInstances → DescribeAggregateSlowLogs`                   | RDS aggregate slow-log API                                                 |
| `db space table`               | `DescribeInstances → DescribeTableSpace`                          | RDS `ExecuteSQL`，只执行内置的 `SELECT ... FROM information_schema.tables` |
| `db trx-lock deadlock`         | `DescribeInstances → DescribeInstanceNodes → DescribeDeadlock`    | RDS Topology → Engine Status，本地解析 `LATEST DETECTED DEADLOCK`          |
| `db trx-lock transaction-list` | `DescribeInstances → DescribeInstanceNodes → DescribeTrxAndLocks` | RDS Topology → Engine Status，本地解析 `TRANSACTIONS` 并分页               |

DBW 请求使用目标 VRegion 作为 OpenAPI `Region`，并按控制面站点设置 `X-TOP-Region`；RDS 业务请求使用 `X-BCGW-VRegion` / `X-BCGW-Region`，不携带 `X-TOP-Region`。

### 参数说明

- 四个命令的第一个位置参数均是逻辑数据库名 `<dbname>`，不是实例 ID。
- 公共 flags：`--vregion`、`-r/--region`、`--route {auto|dbw|rds}`、`--format {table|json}`。
- `slow-log aggregate`：`--start-time`、`--end-time` 为必填秒级 Unix 时间戳；支持 `--page`、`--page-size`、`--order-by`、`--sort-by`、`--users`、`--source-ips`、`--keywords`、`--tables`、`--sql-methods`、`--group-ignored`、`--min-query-time`、`--max-query-time`。
- `space table`：支持 `--table-name`、`--page`、`--page-size`；RDS 路径只执行命令内置的只读表空间查询，不接受用户 SQL。
- `trx-lock deadlock`：支持 `--node-id`；仅影响 DBW 路径，省略时自动查找 Primary 节点。
- `trx-lock transaction-list`：支持 `--node-id`、`--page`、`--page-size`；RDS 路径在本地解析和分页。
- 文本和 JSON 输出都会标明 `DBW API` 或 `RDS API`；JSON 还提供 `route` 与 `api_endpoint` 字段。

## 运维与实时诊断（db ops / db slow）

```bash
# 获取数据库运维详情
bytedcli db ops detail demo_db --region cn

# 获取实时慢执行会话；--instance 兼容 RDS 实例 IP，也接受 DBW NodeId
bytedcli db slow list demo_db --region cn --instance <ip-or-node-id> --port 3306

# 执行并获取最近五分钟健康诊断
bytedcli db slow diag demo_db --region cn --page 0 --page-size 20
```

- 三个命令均支持 `--vregion`、`--region`、`--route auto|dbw|rds` 和 `--format table|json`
- `auto` 按 database-toolbox 的 ByteRDS 能力范围选择 DBW 或 RDS；特殊 VDC/region 映射（含 `nonttap` / `sinf-my`）由 db-cli 统一处理
- DBW 会话响应使用生成的 `DescribeDialogInfosResp` 解码，再归一化为稳定的 `{total,sessions,node_id}` JSON；健康诊断输出为 `{instance_id,node_ids,metrics}`
- `rds ops detail`、`rds slow list`、`rds slow diag` 是兼容入口，参数翻译后调用同一 db-cli 实现；其 `--mode auto|legacy|dbw` 分别映射为 `--route auto|rds|dbw`

## BPM 工单（db bpm）

以下命令由 db-cli 统一执行。`create` 会根据 VRegion、SQL 类型和实例来源选择 RDS/BPM 或 DBW；其他 BPM 操作直接请求对应工作流接口。参数和输出与同名的 `rds bpm` 入口保持一致。

```bash
# 创建 DDL/DML 工单；可省略 --ticket-type 按 SQL 自动识别
bytedcli --site boe db bpm create \
  --dbname demo_db \
  --sql "ALTER TABLE demo_table ADD COLUMN c INT" \
  --background "sample schema change"

# 多区域 DDL 会返回 change_record_id；get 只读，execute 才推进当前 WAIT 节点
bytedcli --site us-ttp db bpm create \
  --region US-TTP --target-regions US-TTP,US-TTP2 \
  --dbname demo_db --sql "ALTER TABLE demo_table ADD COLUMN c INT" \
  --background "sample multi-region change" --no-auto-execute
bytedcli --site us-ttp db bpm change-record get 12574
bytedcli --site us-ttp db bpm change-record execute 12574 --region US-TTP2

# 申请数据库权限；未传 --user-list 时使用当前登录用户
bytedcli --site boe db bpm permission apply \
  --dbname demo_db \
  --region boe \
  --user-list sample.user

# 查询列表与详情
bytedcli --site boe db bpm list --db-name demo_db --finished 0
bytedcli --site boe db bpm get 12345

# 取消工单、更新 SQL 后重新校验、查看 workflow 配置
bytedcli --site boe db bpm cancel 12345 --reason "sample reason"
bytedcli --site boe db bpm update 12345 --sql "ALTER TABLE demo_table ADD COLUMN c INT"
bytedcli --site boe db bpm get-workflow-config 1147
```

- `create` 必填 `--dbname`、`--sql`、`--background`；显式 `--ticket-type create|alter|dml` 优先，否则按 SQL 识别。`--target-regions` 只支持字节云多区域 DDL，且必须包含 `--region` 对应区域
- `change-record get|execute` 使用 change record ID 位置参数，可用 `--region` 限定单个区域。`get` 不会推进流程；`execute` 只执行当前 `WAIT` 节点，其他状态会跳过并说明原因
- `permission apply` 必填 `--dbname`、`--region`；`--db-psm-list` 可显式指定逗号分隔的数据库 PSM，未传时默认使用 `toutiao.mysql.<dbname>_read` 和 `toutiao.mysql.<dbname>_write`；其他选填参数包括 `--workflow-config-id`、`--user-list`、`--expiration-days`、`--db-level`、`--action`、`--background`、`--additional-function`
- `list` 支持 `--page`、`--page-size`、`--target-system`、`--workflow-config-id`、`--status`、可重复的 `--finished`、`--creator`、`--db-name`、`--keyword`
- `get`、`cancel`、`update` 使用工单 ID 位置参数；`update` 还必须传 `--sql`
- `get-workflow-config` 使用 workflow config ID 位置参数

## ByteDoc 工单（db bytedoc ticket）

`db bytedoc ticket` 创建 ByteDoc 变更工单，仅支持 `China-BOE`/`China-BOE2` 的火山 Mongo。

```bash
# Mongo shell 数据变更
bytedcli --site boe db bytedoc ticket --database demo_db --vregion China-BOE \
  --operate-type DataChange --collection demo_collection \
  --memo "update demo records; rollback: reverse update" \
  --sql 'db.demo_collection.updateMany({status: 0}, {$set: {status: 1}})' --format json

# 创建索引；--index-key 可重复
bytedcli --site boe db bytedoc ticket --database demo_db --vregion China-BOE \
  --operate-type CreateIndex --collection demo_collection \
  --index-key user_id:ASC --index-key created_at:DESC --index-name idx_demo \
  --memo "create demo index; rollback: dropIndex" --format json
```

- 支持 `DataChange`、`EnableShardCollection`、`DropCollection`、`CreateIndex`、`ModifyIndex`、`DropIndex`
- Collection/Index 变更未传 `--sql` 时，由 DBW 生成工单脚本后执行创建、预检和提交
- 其他 ByteDoc 实例模式不走程序化创建，应使用命令返回的控制台入口

## ByteRedis（db redis）

ByteRedis 没有程序化工单 API；`db redis ticket` 只返回控制台入口，不会创建工单。`db redis big-keys list` 用于查询大 Key。

```bash
# 返回扩缩容、执行命令、删 Key 等控制台工单入口
bytedcli db redis ticket --psm cache.demo --vregion China-North --format json

# 查询指定日期的大 Key；BOE 站点及映射到 BOE 的 VRegion 不支持
bytedcli db redis big-keys list --psm cache.demo --date 2026-08-01 \
  --begin 00:00:00 --end 23:59:59 --page 1 --page-size 10 \
  --key-type string --vregion China-North --format json
```

## DBW 工单（db ticket）

以下命令由 db-cli 直接请求 DBW。`rds bpm dbw ticket ...` 兼容入口会翻译参数并调用同一个 db-cli 二进制。

```bash
# 使用 CreateTicket → DescribePreCheckDetail → SubmitTicket 创建火山 DDL 工单
bytedcli --site cn db ticket create-ddl \
  --instance-id vedbm-sample \
  --database demo_db \
  --sql "CREATE TABLE demo_table(id BIGINT PRIMARY KEY)" \
  --memo "create demo table" \
  --vregion ChinaSinf-North

# 火山实例使用 CreateTicket 并轮询预检后提交
bytedcli --site cn db ticket create-dml \
  --instance-id vedbm-sample \
  --database demo_db \
  --sql "UPDATE demo_table SET status = 1 WHERE id = 100" \
  --memo "repair demo data" \
  --vregion ChinaSinf-North

# China-BOE / China-BOE2 字节云 DDL 使用 CreateTicket，无需命令行 instance-id
bytedcli --site boe db ticket create-ddl \
  --database demo_db \
  --sql "CREATE TABLE demo_table(id BIGINT PRIMARY KEY)" \
  --memo "create demo table" \
  --vregion China-BOE

# 字节云 DML 使用 CreateTicket，无需命令行 instance-id
bytedcli --site boe db ticket create-dml \
  --database demo_db \
  --sql "DELETE FROM demo_table WHERE id = 100" \
  --memo "remove invalid data" \
  --vregion China-BOE

# 查询、预检和提交
bytedcli --site cn db ticket get --ticket-id "<ticket_id>" --instance-id vedbm-sample
bytedcli --site cn db ticket precheck --ticket-id "<ticket_id>" --instance-id vedbm-sample
bytedcli --site cn db ticket submit --ticket-id "<ticket_id>" --instance-id vedbm-sample

# 字节云 ByteRDS 工单不需要 instance-id
bytedcli --site boe db ticket get --ticket-id "<ticket_id>" --instance-type ByteRDS

# 审批、执行和取消
bytedcli --site cn db ticket approve \
  --ticket-id "<ticket_id>" \
  --instance-id vedbm-sample \
  --workflow-id sample-workflow \
  --comment "sample approval"
bytedcli --site cn db ticket execute \
  --ticket-id "<ticket_id>" \
  --instance-id vedbm-sample
bytedcli --site cn db ticket cancel \
  --ticket-id "<ticket_id>" \
  --instance-id vedbm-sample \
  --reason "sample reason"
```

- `create-ddl` 支持火山/DBW 实例以及 `China-BOE`/`China-BOE2` 的字节云 DDL；`create-dml` 支持火山/DBW 以及 `China-BOE`、`China-BOE2`、`ChinaSinf-North`、`Asia-SouthEastBD` 的字节云 DML。省略实例上下文时会先用 `DescribeInstances` 自动识别 ByteRDS，未命中再解析火山 MySQL 兼容实例；查不到或有歧义时再显式提供 `--instance-type` / `--instance-id`。ByteRDS 无需命令行 `--instance-id`；其余 VRegion 的字节云 DDL/DML 请使用 `rds bpm create` 走 RDS/BPM。DDL/DML 创建都要求 `--database`、`--memo`，以及 `--sql` / `--sql-file` 二选一
- `--ticket-execute-type` 控制预检通过后的执行方式：直接入口 `db ticket create-ddl|create-dml` 沿用 db-cli 默认值 `Manual`；兼容入口 `rds bpm dbw ticket create-ddl` 的 bytedcli 包装器默认 `Auto`，`create-dml` 默认 `Manual`；也可显式使用 `Auto`、`Manual` 或 `Cron`
- 所有后续操作必填 `--ticket-id`；Volc/默认 `VeDBMySQL` 还必须提供 `--instance-id`，字节云 `ByteRDS` 可省略；`cancel` 额外要求 `--reason`
- `execute` 调用 `ExecuteTicket`，仅用于审批后处于 `TicketWaitExecute` 的手动执行工单；`Result.AllPass=false` 时命令按失败退出并展示 `ErrMessage` 和 `Request ID`
- `--site`、`--vregion`、`--region-id` 使用用户显式值；未传时才按站点和 VRegion 补默认值
- `China-BOE` 默认使用 `RegionId=boe`；`China-BOE2` 默认使用 `RegionId=boe2`；`ChinaSinf-North` 默认使用 `RegionId=huabei2`；`Asia-SouthEastBD` 默认使用 `RegionId=bdsgdt`
- 旧 `--request-region-id` 仅为 `rds` 兼容解析，不会下发给 DBW
- 工单 ID 按字符串传递；默认表格字段顺序与 `rds bpm dbw ticket` 保持一致

## 元命令

```bash
# 更新本地 db-cli 到最新版本，或指定版本
bytedcli db +update
bytedcli db +update 0.1.4
```

- `+update` 使用 `+` 前缀，不会与库名/表名冲突
- `+update` 完全在 bytedcli 层处理，用于更新 `~/.local/share/bytedcli/dependency/db/` 下的 db-cli

## Notes

- 结构化输出：对 `list`/`search`/`get`/`topology`/`qps`/`overview`/`ops`/`bpm`/`bytedoc`/`redis`/`slow`/`schema`/`sql`/`slow-log`/`space`/`ticket`/`trx-lock`，全局 `--json` 会由 bytedcli 自动转换成 db-cli 的 `--format json`。`context` 等本地命令不支持结构化输出
- `schema`、`slow-log` 的 `--database` 是实例 ID（如 `mysql-67245173607b`）；`sql execute` 的 `--database` 是逻辑库名，DBW 路由会自动解析真实实例 ID。`sql eval security` 需同时给 `--instance`（实例 ID）、`--type`、`--database`（库名）和 `--sql`，并用 `--vregion` + 可选 `--region` 定位机房；`sql eval performance` 创建任务时使用 PostgreSQL `--instance`、单条 `--sql` 和 `--db-metadata`，查询已有任务时使用 `--task-id`
- `context`、`ops`、`bpm`、`bytedoc`、`redis`、`slow`、`schema`、`sql`、`slow-log`、`space`、`trx-lock`、`ticket` 透传到 db-cli Go 二进制，其 flag 命名与 bytedcli 标准字典存在差异；`bpm` 的 bare group help 仍由 bytedcli 本地渲染，实际动作由 db-cli 执行并与 `rds bpm` 保持一致。使用 Go 命令组时以本文档为准：
  - 时间范围用 `--start-time` / `--end-time`（不是标准的 `--start` / `--end`），且为秒级 epoch
  - 分页用 `--page-number` / `--page-size`（`slow-log get`）与 `--page` / `--page-size`（schema list、slow-log aggregate、space table、trx-lock transaction-list）
  - 地域/机房用 `--region`（sql/slow-log）与 `--vdc`（schema），不是标准的统一 `--region`
  - 数据库类型用 `--type`；除 `sql execute` 外，实例标识用 `--database`
