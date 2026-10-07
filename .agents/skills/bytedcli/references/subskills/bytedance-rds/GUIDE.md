---
name: bytedance-rds
description: "Operate RDS via bytedcli: list starred DBs, search databases, list tables, run SQL, view diagnostics, and manage BPM work orders. Use when tasks mention RDS or database operations."
---

# bytedcli RDS

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

- 搜索/列出数据库
- 查看表、执行 SQL
- 数据库诊断和监控
- BPM 工单管理（DDL/DML 变更）

## 前置条件

- 使用通用调用方式：`../../invocation.md`
- 需要鉴权时先登录：`bytedcli auth login`
- `rds db` 等命令底层会使用 db-cli。实际执行数据库操作前，Agent 默认先尝试运行 `bytedcli db +update`，以使用最新的 db-cli 能力和修复；这是推荐的版本准备步骤，不是强制要求。若用户明确不更新、当前环境不便更新或更新失败，应说明情况并继续使用当前本地版本，不要因此阻断用户任务

> 执行前缀见 `../../invocation.md`；下面示例直接写 `bytedcli`。

## Quick start

Commands are grouped under `rds db`, `rds slow`, `rds alert`, `rds ops`, and `rds bpm`. Old flat names (e.g. `rds list-starred-db`, `rds get-db-overview`, `rds bpm apply-permission`, `rds bpm update-sql`) still work as hidden aliases.

```bash
# 默认先尝试更新底层 db-cli；更新失败时仍可继续使用当前版本
bytedcli db +update

# 列出收藏的数据库（自动按 VRegion 路由 DBW 或 RDS）
bytedcli rds db list --region cn

# 搜索数据库
bytedcli rds db search "keyword" --region cn --page 0 --page-size 50

# 列出表；DBW 路由可用 --page / --page-size 分页
bytedcli rds db table list "dbname" --region cn --page 1 --page-size 100

# 执行 SQL
bytedcli rds db query "dbname" "SELECT * FROM users LIMIT 10" --region cn

# 分片键范围查询仅在用户明确接受风险后使用确认参数；该参数透传给底层 db-cli
bytedcli --site boe rds db query "demo_db" \
  "SELECT * FROM orders WHERE user_id BETWEEN 1 AND 100" \
  --confirm-risky-shard-query

# i18n-bd vregion display names are accepted and mapped to RDS regions
bytedcli --site i18n-bd rds db query "demo_db" "SELECT 1" --region US-EE
bytedcli --site i18n-bd rds db query "demo_db" "SELECT 1" --region Asia-SouthEastBD

# 数据库概览（详情 + 拓扑，可选 QPS）
bytedcli rds db overview "dbname" --region cn --qps

# BOE vedb / 多云库读取
bytedcli --site boe rds db table list "dbname"
bytedcli --site boe rds db table schema "dbname" "table"
bytedcli --site boe rds db query "dbname" "SHOW TABLES"

# 已迁移到 db-cli 的 RDS 读命令统一使用 --mode 覆盖自动路由
bytedcli --site cn rds db search "keyword" --vregion ChinaSinf-North --region huabei2 --mode legacy
bytedcli --site boe rds db table list "dbname" --mode dbw

```

## BPM 工单管理

```bash
# 创建 DDL 工单（推荐：不传 --workflow-config-id，让 CLI 按 VRegion 选择后端）
# - China-BOE / China-BOE2：火山 DDL/DML 与字节云 DDL/DML 直连 DBW
# - ChinaSinf-North / Asia-SouthEastBD：火山 DDL/DML 与字节云 DML 直连 DBW，字节云 DDL 走 RDS/BPM
# - 其他 VRegion：字节云实例走 target_system=rds 的 BPM；火山实例暂不支持程序化提单
bytedcli --site boe rds bpm create \
  --ticket-type alter \
  --dbname "demo_db" \
  --sql "ALTER TABLE demo_table ADD COLUMN age INT;" \
  --background "添加年龄字段"

# 创建 ChinaSinf-North/huabei2 火山实例的 DBW DDL 工单（直连 DBW）
# 建议显式提供 --instance-id；未传时 CLI 会尝试从 RDS 元数据解析
bytedcli --site cn --vregion ChinaSinf-North --vdc huabei2 rds bpm create \
  --ticket-type alter \
  --dbname "demo_db" \
  --sql "ALTER TABLE demo_table ADD COLUMN age INT;" \
  --background "变更原因" \
  --instance-id "vedbm-xxx"

# 申请个人库权限工单（支持 maliva 等区域；示例使用 i18n-bd 站点）
bytedcli --site i18n-bd rds bpm permission apply \
  --dbname "demo_db" \
  --region "maliva" \
  --user-list "user1,user2" \
  --background "Apply for dev usage"

# 创建 DDL 工单 - CREATE
bytedcli --site boe rds bpm create \
  --ticket-type create \
  --dbname "demo_db" \
  --sql "CREATE TABLE IF NOT EXISTS demo_table (id INT PRIMARY KEY);" \
  --background "创建新表"

# 创建火山 DML 工单：支持区域统一调用 DBW CreateTicket，预检通过后提交
bytedcli --site boe rds bpm create \
  --dbname "demo_db" \
  --sql "UPDATE users SET status = 1 WHERE id = 100;" \
  --background "数据修复；回滚：UPDATE users SET status = 0 WHERE id = 100;" \
  --instance-id "vedbm-xxx"

# 字节云 DML：China-BOE / China-BOE2 走 DBW，其余 VRegion 按 region 查询 RDS/BPM workflow
bytedcli --site boe rds bpm create \
  --dbname "demo_db" \
  --sql "DELETE FROM users WHERE id = 100;" \
  --background "删除错误数据；回滚：重新插入原记录"

# 其他 VRegion 的 DML 同样走 RDS/BPM
bytedcli --site cn rds bpm create \
  --dbname "demo_db" \
  --sql "DELETE FROM users WHERE id = 100;" \
  --background "删除错误数据；回滚：重新插入原记录"

# US-TTP / US-TTP2 的 DDL 工单：--region 支持 vregion 展示名，US-TTP 映射 ova，US-TTP2 映射 useast8
bytedcli --site us-ttp rds bpm create \
  --ticket-type create \
  --region US-TTP \
  --dbname "demo_db" \
  --sql "CREATE TABLE IF NOT EXISTS demo_table (id BIGINT PRIMARY KEY);" \
  --background "同步 demo 表结构"

# US-TTP 必须关自动执行：该机房自动执行完不释放锁，工单会永久卡住
bytedcli --site us-ttp rds bpm create \
  --ticket-type create \
  --region US-TTP \
  --no-auto-execute \
  --dbname "demo_db" \
  --sql "CREATE TABLE IF NOT EXISTS demo_table (id BIGINT PRIMARY KEY);" \
  --background "同步 demo 表结构"

# 一条 DDL 同时提交到多个区域：--target-regions 可逗号分隔或重复传，必须包含 --region 对应的区域
# 产出的是 ByteHeart 变更单（change_record_id），不是 DDL 工单
bytedcli --site us-ttp rds bpm create \
  --region US-TTP \
  --target-regions US-TTP,US-TTP2 \
  --no-auto-execute \
  --dbname "demo_db" \
  --sql "ALTER TABLE demo_table ADD COLUMN age INT;" \
  --background "多区域同步字段"

# 推进变更单：子流程依次走 ack 和 apply_rds_ddl，所以要跑两次
# 第二次之后输出里才有各区域真正的 DDL 工单号和链接
bytedcli --site us-ttp rds bpm change-record execute 12574
bytedcli --site us-ttp rds bpm change-record execute 12574

# 只看状态不推进；--region 可限定单个区域
bytedcli --site us-ttp rds bpm change-record get 12574
bytedcli --site us-ttp rds bpm change-record execute 12574 --region US-TTP2

# 查看 TTP Review 子单：位置参数传 DDL 工单号或 Review 工单号都能识别
bytedcli --site us-ttp rds bpm ttp-review get 4712345

# 指派 TTP Review 审批人：默认 NoC 组；选 SRE 必须同时传 --assignee
bytedcli --site us-ttp rds bpm ttp-review assign 4712345
bytedcli --site us-ttp rds bpm ttp-review assign 4712345 --approver-type SRE --assignee "demo_user"

# 审批通过后工单停在 waiting_execute，手动执行
bytedcli --site us-ttp rds bpm execute 4712345

# 查看字节云 RDS BPM 工单详情
bytedcli --site cn rds bpm get 3935899

# 查看 China-BOE / China-BOE2 / ChinaSinf-North / Asia-SouthEastBD 直连 DBW 工单详情
bytedcli rds bpm dbw ticket get --ticket-id "<ticket_id>" --instance-id "vedbm-xxx"

# 列出字节云 RDS BPM 工单
bytedcli --site cn rds bpm list --db-name "demo_db"

# 取消工单
bytedcli --site boe rds bpm cancel 3935899 --reason "不再需要"

# 更新工单 SQL（重试）
bytedcli --site boe rds bpm update 3935899 --sql "新的 SQL"

# DBW 工单兼容入口：参数会翻译为 db ticket，并由 db-cli 创建 / 查询 / 预检 / 提交 / 自审批 / 取消
# DDL 使用 CreateTicket → DescribePreCheckDetail → SubmitTicket；火山实例传 instance-id，China-BOE/China-BOE2 字节云可省略 instance-id
bytedcli rds bpm dbw ticket create-ddl \
  --instance-id "vedbm-xxx" \
  --database "demo_db" \
  --sql-file "./ddl.sql" \
  --memo "create demo table" \
  --vregion ChinaSinf-North \
  --region-id huabei2

bytedcli rds bpm dbw ticket create-dml \
  --instance-id "vedbm-xxx" \
  --database "demo_db" \
  --sql "UPDATE users SET status = 1 WHERE id = 100;" \
  --memo "repair user status" \
  --vregion ChinaSinf-North \
  --region-id huabei2

bytedcli rds bpm dbw ticket precheck --ticket-id "<ticket_id>" --instance-id "vedbm-xxx"
bytedcli rds bpm dbw ticket submit --ticket-id "<ticket_id>" --instance-id "vedbm-xxx"
bytedcli rds bpm dbw ticket approve --ticket-id "<ticket_id>" --workflow-id "<workflow_id>" --instance-id "vedbm-xxx"
bytedcli rds bpm dbw ticket cancel --ticket-id "<ticket_id>" --instance-id "vedbm-xxx" --reason "不再需要"

# 字节云 ByteRDS 工单不需要 instance-id
bytedcli --site boe rds bpm dbw ticket get --ticket-id "<ticket_id>" --instance-type ByteRDS
```

## Notes

- `bytedcli db +update` 由 bytedcli 更新本地 db-cli。Agent 在每次 RDS 数据库任务开始、首次调用依赖 db-cli 的命令前默认尝试一次即可，不需要在同一任务的每条命令前重复更新，也不能把更新成功作为继续执行的硬性条件
- 需要结构化输出加 `--json`（全局选项，放在子命令之前，如 `bytedcli --json rds db list`）
- `workflow-config-id` 与站点强相关，且可能复用/变更；建议优先不传，让 CLI 自动选择并做流程校验（避免误提到非 RDS 的工单）
- `rds bpm create` 显式传 `--ticket-type create|alter|dml` 时会强制走对应的 DDL 或 DML 路径，不再根据 SQL 判断；未传时才解析 SQL：`INSERT` / `UPDATE` / `DELETE` 走 DML，`CREATE` 走 DDL create，其余结构变更走 DDL alter
- `China-BOE`、`China-BOE2`、`ChinaSinf-North`、`Asia-SouthEastBD` 的火山实例 DDL/DML 通过 `db ticket create-ddl|create-dml` 访问 DBW；db-cli 会按数据库、VRegion 和可选实例 ID 调用 `DescribeInstances`，解析真实 `InstanceType`（支持 `VeDBMySQL`、`MySQL`、`MySQLSharding`）和 VDC 后建单。所有这些 MySQL 兼容火山实例统一执行 `CreateTicket → DescribePreCheckDetail → SubmitTicket`
- `rds bpm dbw ticket create-ddl|create-dml` 均要求显式传 `--memo` 说明变更背景；`--instance-type` 默认均为 `VeDBMySQL`，可显式覆盖为 DBW 支持的实例类型；在支持的 VRegion 中省略 `--instance-id`、`--instance-type`、`--ds-type` 时，兼容入口会按 ByteRDS 工单推断并传递 `--instance-type ByteRDS`。MySQLSharding DDL 默认按普通表提交；`create-ddl` 显式传 `--sharding --sharding-key <key> --sharding-key-type <int|varchar|string>` 时创建分片表，并将分片键及类型透传给 db-cli；`--sharding-key-type` 接受 `int`（归一化为 `Int`）、`varchar` 或 `string`（归一化为 `String`），大小写不敏感，开启 `--sharding` 时该参数必填。非分片表 DDL 及所有 DML 无需传这些参数
- 通过 bytedcli 创建 DBW DDL/DML 工单时，标题会统一追加 `<bytedcli>` 来源标记；未传 `--title` 时标题为 `<bytedcli>`。该规则覆盖 `db ticket create-ddl|create-dml`、`rds bpm dbw ticket create-ddl|create-dml` 以及 `rds bpm create` 的 DBW 分支
- 字节云 DDL/DML 使用独立能力表路由 DBW：DDL 当前为 `China-BOE`、`China-BOE2`；DML 当前为 `China-BOE`、`China-BOE2`、`ChinaSinf-North`、`Asia-SouthEastBD`。调用 `db ticket create-ddl|create-dml` 时可省略实例上下文，db-cli 会先用 `DescribeInstances` 自动识别 ByteRDS，且不传命令行 instance-id；内部使用 `CreateTicket`（协议字段 `InstanceId` 填数据库名），轮询 `DescribePreCheckDetail`，通过后调用 `SubmitTicket`。其他字节云 DDL/DML 走 RDS/BPM
- 火山实例显式提供 `--instance-id` 时可直接路由；未传时 CLI 会查询 RDS 元数据并尝试解析实例 ID。DBW 未覆盖 VRegion 的字节云 DDL/DML 会从 RDS `worksheets/types/` 自动解析 workflow 后走 BPM；火山实例的 DDL 与 DML 都仅支持 DBW 覆盖的 VRegion，其他 VRegion 会在请求 BPM 前直接拒绝。`--workflow-config-id` 仅用于 BPM 路径的显式覆盖
- 显式 `--vregion` 会覆盖 `--site` 的默认 VRegion；VRegion 不属于当前 site 时会在任何查询或提单前报错
- BPM wrapper record 的审批/拒绝请使用 BPM Web UI；`rds bpm dbw ticket approve` 只适用于直连 DBW ticket-id，不适用于 BPM record-id
- `rds bpm dbw ticket create-ddl|create-dml|get|precheck|submit|approve|cancel` 由 rds 层翻译参数后调用 `db ticket`；创建时 db-cli 会按数据库和 VRegion 先自动识别 ByteRDS，未命中再解析火山实例。支持范围内的字节云 DDL/DML 无需命令行 instance-id。参数校验、DBW 请求、输出、错误和退出码均由同一个 db-cli 二进制负责
- DBW 后续操作按实例类型校验：Volc/默认 `VeDBMySQL` 必须提供 `--instance-id`，字节云 `ByteRDS` 可以省略；显式 `--site`、`--vregion`、`--region-id` 会覆盖默认映射
- DBW detail 返回 `WorkflowId` 时，审批必须透传 `--workflow-id`；缺少该字段可能触发 DBW 内部错误或拿不到真实权限错误
- DBW 直连工单的 `--ticket-id` 必须保留为字符串，避免 19 位工单号精度丢失
- `rds bpm create` 可省略 `--ticket-type` 让 CLI 按 SQL 识别；需要覆盖识别结果时传 `create`、`alter` 或 `dml`
- `rds bpm create` 与 `db bpm create` 共享同一套 VRegion、DDL/DML、实例类型、workflow 和 RDS/DBW 路由逻辑；`rds bpm change-record get|execute` 与 `db bpm change-record get|execute` 的校验和输出也保持一致
- `rds bpm create` 成功后输出 `record_id`、`workflow_config_id` 和 `url`；`url` 是工单详情页地址，必须带 region 段（`/rds/worksheet-bpm/detail/<region>/<record_id>`），只用 record_id 拼出的地址会渲染成空白页
- `--site us-ttp` 支持 US-TTP 与 US-TTP2 两个机房：`--region` 可直接写 vregion 展示名，`US-TTP` 映射到 `ova`、`US-TTP2` 映射到 `useast8`。该站点 DDL 走 `alter_bdee` 流程，工单字段名是 `secure_sql` 而非 `sql`，CLI 会按站点自动改写，调用方始终只传 `--sql`
- `rds bpm create --target-regions <regions>` 把同一条 DDL 一次提交到多个区域，取值是 vregion 展示名（逗号分隔或重复传，例如 `--target-regions US-TTP,US-TTP2`），且必须包含 `--region` 对应的区域，否则会在发请求前报 `RDS_BPM_INPUT_ERROR`。它产出的是 ByteHeart **变更单**（输出 `change_record_id`）而不是 DDL 工单。该参数只支持字节云 RDS/BPM 的 DDL 链路，DML 与 DBW / 火山实例链路会直接报错
- `rds bpm change-record get <change_record_id>` 只读展示变更单下各区域子流程的当前节点；`rds bpm change-record execute <change_record_id>` 执行当前节点。两条都支持 `--region <vregion>` 限定单个区域。读写拆成两个动词，查看状态不会意外推进流程。子流程要依次走 `ack` 和 `apply_rds_ddl` 两个节点，**真正的 DDL 工单是 `apply_rds_ddl` 执行后才生成的**，所以一张变更单通常要 `execute` 两次，第二次之后才能从输出里拿到各区域的工单号和链接。只有 `WAIT` 状态的节点会被执行，`DOING` / `SUCCESS` 会跳过并回报状态（对 `DOING` 节点重复执行会返回 HTTP 500 `action execute is not allowed`）；某个区域失败不影响其他区域继续
- `rds bpm create --no-auto-execute` 建单时关闭自动执行，工单在审批通过后停在 `waiting_execute`，需要 `rds bpm execute <record_id>` 才会开始执行。**US-TTP 上这是必须的**：该机房自动执行路径有已知缺陷，DDL 应用完之后不释放锁，工单永久卡住且 retry 无效（上游在 workflow config 672 修复，尚未部署到 TTP）。不传该参数时平台默认自动执行，其他站点无需改变习惯
- TTP DDL 完整时序是 create -> DB Owner 审批（人工）-> TTP Review 指派审批人 -> NoC 审批（人工）-> `waiting_execute` -> 执行 -> `end`。TTP Review 是独立子单，只有工单进入 TTP Reviewing 节点后才存在：`rds bpm ttp-review get <id>` 解析并展示子单，`rds bpm ttp-review assign <id>` 指派审批人（`--approver-type NoC|SRE`，默认 `NoC`；`SRE` 必须带 `--assignee`）。两条子命令的位置参数既接受 DDL 工单号也接受 Review 工单号，内部按 `workflow_key` 区分。多区域场景在最前面多一段：create `--target-regions` 产出变更单 -> `change-record execute` 两次生成各区域 DDL 工单 -> 之后每张工单各自走上面的流程
- 如果要发起 BES 元信息修改工单，请改用顶层命令：`bytedcli bes metadata update --config <json-object>`
- Flag renames: `--db-name` is a hidden alias; prefer `--dbname` in new scripts
- 多站点操作：`--site <cn|boe|i18n|i18n-bd|i18n-tt|us-ttp|eu-ttp>` 切换 ByteCloud 站点（默认为 cn，或环境变量 `BYTEDCLI_CLOUD_SITE`；`prod` 是 `cn` 的别名）；非法值会直接报错，不会回退到环境变量或默认站点
- RDS 读命令只会在未显式传 `--region` 时按站点补默认值；显式传入的 `--region` 会按内置 alias 归一化后传给 RDS API
- `--site i18n-bd` 不传 `--region` 时默认使用 `mycis`；也支持按 vregion 展示名显式传入并映射为 RDS region：`US-EE -> awsva`、`Asia-SaaS -> jpsaas`、`Singapore-SaaS -> sgsaas1larkidc1`、`Singapore-Common -> sgcomm1`、`Asia-CIS -> mycis`、`Asia-SouthEastBD -> sinf-my`。其中 `Asia-SouthEastBD/sinf-my` 会使用 `BYTECLOUD_HOST_I18N_BD_SINF_BPM + /api/v1/rds-sinf`，其他 i18n-bd RDS 读请求使用 `BYTECLOUD_HOST_I18N_BD + /api/v1/rds`
- `--site i18n-tt` 的 RDS 读命令默认 region 为 `alisg`；如需 `maliva` 等其他区域，请显式传 `--region <value>`
- `--site cn` 访问 ChinaSinf-North 区域库时，未替换的原生 RDS 读命令仍需经 `-r/--region` 传入地域。已由 db-cli 执行的 `rds db list|search|get|topology|qps|overview|query|table list|table schema`、`rds ops detail`、`rds slow list|diag` 可使用全局 `--vregion`，其中 `rds db list|search|get|topology|qps|overview` 也支持命令级 `--vregion`；显式值覆盖 site 默认 VRegion，命令级 `--region` 作为该 VRegion 的 VDC/region 传递
- 已由 db-cli 执行的 `rds db list|search|get|topology|qps|overview|query|table list|table schema`、`rds ops detail`、`rds slow list|diag` 统一支持 `--mode auto|legacy|dbw`；默认 `auto`，其中 `legacy` 强制 RDS、`dbw` 强制 DBW，只在排障或已知特殊库时显式覆盖
- `rds db table list` 支持 `--page <n>`、`--page-size <n>` 并透传到 DBW `ListTables`；仅 DBW 路由使用分页，`legacy` 的 RDS 直连固定使用 `all=1` 获取全部表
- `rds db query` 仅接受单条只读 SQL：`SELECT`、`SHOW TABLES`、`SHOW CREATE TABLE`、`EXPLAIN SELECT`。DDL、DML、事务、锁与多语句会在请求前被拒绝；需要变更数据或结构请使用 `rds bpm create` 提工单
- `rds db query` 底层调用 db-cli，支持 `--confirm-risky-shard-query`。`MySQLSharding` 和 `is_sharding=true` 的 `ByteRDS` 会检查分片键：只有单值等值查询默认执行；`IN`、范围/非等值条件会在真实 SQL 发出前报错并提示多/全分片慢 SQL 风险。这是预期安全保护，不是服务异常；优先改写为单值等值，只有用户明确接受风险时才带该参数重试。Agent 可以提示用户为当前任务设置适用于全部分片风险查询的免确认分片数量阈值；用户尚未明确给出并确认阈值时，Agent 不得自行添加确认参数。设置后，也只有能够可靠判断本次涉及的分片数严格小于阈值时才可自动添加，达到/超过阈值或无法判断时仍需确认。元数据检查失败会告警并 fail-open 继续执行
- 部分特殊数据库被登记为禁止通过 bytedcli 执行 SQL：`rds db query` 与 DBW 变更工单链路命中禁入清单时会以 `DB_SQL_BLOCKED` 错误拒绝（错误信息包含登记原因）。此时应改用该库负责方自己的工具，不要尝试绕过；清单登记方式见仓库 `CONTRIBUTING.md` 的「DB SQL 操作禁入清单」
- `rds db query` 的 `auto` 模式与 database-toolbox `execute_sql` 对齐：`China-North`、`China-North5`、`ChinaSinf-North`、`China-East`、`China-Fintech`、`China-BOE`、`Singapore-Central` 走 `db sql execute` / DBW；其余 VRegion 仍走 RDS 原生 `run_sql`。在 DBW VRegion 中，火山 MySQL（`VeDBMySQL`、`MySQL`、`MySQLSharding`）使用 RDS 元数据解析到的实例 ID/类型，字节云使用 `ByteRDS`；db-cli 会再以 `DescribeInstances` 校验字节云的真实实例 ID 和 VDC。显式 `--vregion` 覆盖 site 默认值，`--vdc` 覆盖 DBW VDC；VRegion 与 site 不匹配会直接报错
- `rds db list` 已由 `db list` 执行：默认仍只列出当前用户收藏的库，保持 `--page` / `--page-size` 和 RDS JSON envelope 兼容。自动路由中，`China-North`、`China-North5`、`ChinaSinf-North`、`China-East`、`China-Fintech`、`China-BOE`、`Singapore-Central` 走 DBW `DescribeInstances`；其他 VRegion 走 RDS 的收藏列表接口。命令级 `--region` 会反解为 VRegion/VDC；`ce`、`multicloud`、`huabei2`、`sgcompliance` 等 VDC 使用对应的 RDS API region，`nonttap` / `sinf-my` 使用 i18n-bd 的 `rds-sinf` 专用路径
- `--site boe` 查询 `vedb` / 多云库时，`db table list`、`db table schema`、`db query` 会自动按库详情里的实际 `volc_region` 路由到 DBW；推荐省略 `--region` 或显式传 `boe`
- 如果显式传 `--site boe --region cn`，CLI 会按 `cn` 原样请求，不会自动改写到 BOE DBW 读链路
- 对 BOE 多云库，`db params`、`alert rules`、`slow config` 当前会直接返回 `RDS_MULTI_CLOUD_UNSUPPORTED`；`slow list` 已由 db-cli 按 VRegion 路由 DBW/RDS

## References

- `references/rds.md`
