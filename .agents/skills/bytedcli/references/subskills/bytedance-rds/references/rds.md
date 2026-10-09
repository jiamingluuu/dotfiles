# RDS

## 章节索引

- [数据库查询](#数据库查询)：只读 SQL、分片保护、OG tagging 与 Watchdog
- [数据库详情](#数据库详情)
- [慢查询与诊断](#慢查询与诊断)
- [BPM 工单管理](#bpm-工单管理)
- [Notes](#notes)

## 数据库查询

```bash
# 列出收藏的数据库（自动按 VRegion 路由 DBW 或 RDS）
bytedcli rds db list --region cn --page 1 --page-size 50

# 搜索数据库
bytedcli rds db search "keyword" --region cn --page 0 --page-size 50

# 列出表；DBW 路由可用 --page / --page-size 分页
bytedcli rds db table list "dbname" --region cn --page 1 --page-size 100

# 执行 SQL
bytedcli rds db query "dbname" "SQL" --region cn

# 分片键范围查询仅在用户明确接受风险后确认执行
bytedcli --site boe rds db query "demo_db" \
  "SELECT * FROM orders WHERE user_id BETWEEN 1 AND 100" \
  --confirm-risky-shard-query

# i18n-bd vregion display names are accepted and mapped to RDS regions
bytedcli --site i18n-bd rds db query "demo_db" "SELECT 1" --region US-EE
bytedcli --site i18n-bd rds db query "demo_db" "SELECT 1" --region Asia-SouthEastBD

# BOE vedb / 多云库读取
bytedcli --site boe rds db table list "dbname"
bytedcli --site boe rds db query "dbname" "SHOW TABLES"

# 已迁移到 db-cli 的 RDS 读命令统一使用 --mode 覆盖自动路由
bytedcli --site cn rds db search "keyword" --vregion ChinaSinf-North --region huabei2 --mode legacy
bytedcli --site boe rds db table list "dbname" --mode dbw

# EU-Compliance2（ie2）读取：走 eu-ttp 站 + tiktok-eu 网关
bytedcli --site eu-ttp --vregion ie2 rds db query "dbname" "SELECT 1" --region ie2

```

`rds db query` 仅接受单条只读 SQL：`SELECT`、`SHOW TABLES`、`SHOW CREATE TABLE`、`EXPLAIN SELECT`。DDL、DML、事务、锁与多语句会在请求前被拒绝；需要变更请改用 `rds bpm create`。

### 分片键范围查询保护

`rds db query` 底层透传到 db-cli，支持 `--confirm-risky-shard-query`。`MySQLSharding` 按实例类型直接确认；所有 `ByteRDS` 都查询 RDS v3 详情，只有 `is_sharding=true` 才启用分片键检查。确认是分片库后，通过当前 DBW/RDS 路由执行 `dbatman show 'table' info` 获取相关表的分片键。

- 只有分片键单值等值（`shard_key = xxx`）默认执行
- 分片键使用 `IN (...)`、`BETWEEN`/`NOT BETWEEN`、`> < >= <=`、`!=`/`<>`、`NOT IN`、`LIKE`/`NOT LIKE` 等条件时，命令会在真实 SQL 发出前报错，提示多/全分片扫描、慢 SQL 或 DBAS Kill 风险
- 该提示是合理且在预期范围内的安全保护，不是 RDS/DBW 服务异常。优先改写为分片键单值等值，不要无确认地循环重试
- 只有用户明确接受跨分片扫描风险时，才加 `--confirm-risky-shard-query`；该参数由 `rds db query` 透传给 db-cli，跳过本次分片识别和分片键检查后执行原 SQL
- Agent 可以提示用户为当前任务设置“免二次确认的分片数量阈值”，例如“预计涉及少于 5 个分片时无需再次确认”。它适用于 `IN`、`BETWEEN`、比较、`LIKE`、`NOT IN` 等全部分片风险查询。用户尚未明确给出并确认阈值时，Agent 不得自行添加 `--confirm-risky-shard-query`；用户设置后，只有能够基于分片元数据、路由规则或用户提供的映射可靠判断本次查询涉及的分片数严格小于阈值时，才可自动添加。达到/超过阈值或无法判断时仍需再次确认。该阈值只属于当前任务中的 Agent 预授权，不是 CLI 参数或持久化配置，不得跨任务沿用
- RDS v3 分片元数据或 dbatman 获取失败时，CLI 会输出警告并 fail-open 继续执行；应向用户说明安全检查未完成及潜在风险

`rds db query` 的默认 `auto` 路由与 database-toolbox `execute_sql` 对齐：`China-North`、`China-North5`、`ChinaSinf-North`、`China-East`、`China-Fintech`、`China-BOE`、`Singapore-Central` 经 `db sql execute` 调用 DBW；其他 VRegion 继续调用 RDS 原生 `run_sql`。DBW 区域中，火山 MySQL（`VeDBMySQL`、`MySQL`、`MySQLSharding`）按 RDS 元数据传递真实实例 ID/类型；字节云使用 `ByteRDS`，再由 db-cli 通过 `DescribeInstances` 解析真实实例 ID 与 VDC。全局 `--vregion` 选择该 query 路由，`--vdc` 覆盖 DBW VDC。`rds db table list/schema` 也会把全局 `--vregion` 交给 db-cli 选择 DBW 或 RDS；命令级 `--region` 映射为 db-cli VDC。

### OG tagging 拒绝时使用 Watchdog

如果 `rds db query` 返回 HTTP 403，且同时包含 OG/tagging 文案和 schema 缺失或字段未打标信息，不要切换 `auto` / `legacy` / `dbw` 反复重试。HTTP 401 或只有 tagging 字样、没有 schema/字段证据的报错应先检查站点认证，不要切换到 Watchdog。对 Watchdog 支持区域内的只读核验，按以下顺序执行：

```bash
# 1. ROW 可返回明文：先取得后续断言使用的已知预期值
bytedcli --json --site i18n-tt watchdog db execute \
  --db-name demo_db \
  --region Singapore-Central/alisg \
  --sql 'SELECT id, extra FROM sample_table WHERE id=1'

# 2. US 合规区只返回断言结果；US-TTP2 时改用 US-TTP2/useast8
bytedcli --json --site us-ttp watchdog db execute \
  --db-name demo_db \
  --region US-TTP/ova \
  --sql 'SELECT id, extra FROM sample_table WHERE id=1' \
  --assert 'id = 1' \
  --assert 'extra.sample.value = expected-value'

# 3. EU 合规区同样使用已知预期值做断言
bytedcli --json --site eu-ttp watchdog db execute \
  --db-name demo_db \
  --region EU-TTP2/no1a \
  --sql 'SELECT id, extra FROM sample_table WHERE id=1' \
  --assert 'id = 1' \
  --assert 'extra.sample.value = expected-value'
```

合规区不返回业务明文；Watchdog 只适用于有界只读查询，必须保留主键等值等限制条件，不得改成扫表来验证。完整地区映射、JSON 路径断言与返回语义见 `bytedance-watchdog` skill。

`rds db table list` 支持 `--page <n>` 和 `--page-size <n>`。它们会透传到 DBW `ListTables`；只有 DBW 路由使用分页，`--mode legacy` 的 RDS 直连固定使用 `all=1` 获取全部表。

`rds db list` 已改由 `db list` 执行，但命令语义不变：默认只返回当前用户收藏的库，且 `--page` / `--page-size` 与 RDS JSON envelope 保持兼容。自动路由中，`China-North`、`China-North5`、`ChinaSinf-North`、`China-East`、`China-Fintech`、`China-BOE`、`Singapore-Central` 走 DBW `DescribeInstances`；其他 VRegion 走 RDS 收藏列表接口。命令级 `--region` 会反解为 VRegion/VDC；`ce`、`multicloud`、`huabei2`、`sgcompliance` 等特殊 VDC 会转换为相应的 RDS API region，`nonttap` / `sinf-my` 使用 i18n-bd `rds-sinf` 专用路径。

已由 db-cli 执行的 `rds db list|search|get|topology|qps|overview|query|table list|table schema`、`rds ops detail`、`rds slow list|diag` 统一使用 `--mode auto|legacy|dbw` 覆盖路由：`auto` 按 VRegion 自动选择，`legacy` 强制 RDS，`dbw` 强制 DBW。`rds db list|search|get|topology|qps|overview` 同时支持命令级 `--vregion`；显式值覆盖全局 VRegion/site 默认值，此时 `--region` 表示该 VRegion 的 VDC/region。

## 数据库详情

```bash
# 获取数据库基本信息
bytedcli rds db get "dbname" --region cn

# 数据库概览（详情 + 拓扑，可选 QPS）
bytedcli rds db overview "dbname" --region cn --qps

# 获取拓扑信息
bytedcli rds db topology "dbname" --region cn

# 获取 QPS
bytedcli rds db qps "dbname" --region cn

# 获取 SLA
bytedcli rds db sla "dbname" --region cn

# 获取表结构
bytedcli rds db table schema "dbname" "table" --region cn

# BOE vedb / 多云库表结构
bytedcli --site boe rds db table schema "dbname" "table"

# 需要覆盖自动路由时，可显式指定实验性 --mode
bytedcli --site boe rds db table schema "dbname" "table" --mode dbw

# 获取参数配置
bytedcli rds db params "dbname" --region cn

```

## 慢查询与诊断

```bash
# 获取慢查询配置
bytedcli rds slow config "dbname" --region cn

# 列出慢查询 SQL
bytedcli rds slow list "dbname" --region cn --instance <ip> --port 3306 --mode auto

# 查询被 kill 的慢 SQL（时间戳为秒级）
bytedcli rds slow kill-sql "dbname" --start-ts <start_epoch> --end-ts <end_epoch> --region cn

# 执行并获取数据库健康诊断
bytedcli rds slow diag "dbname" --region cn --page 0 --page-size 20 --mode auto

# 列出告警
bytedcli rds alert list "dbname" --region cn

# 列出监控告警
bytedcli rds alert rules "dbname" --region cn

# 获取运维详情
bytedcli rds ops detail "dbname" --region cn --mode auto
```

`rds ops detail`、`rds slow list`、`rds slow diag` 已替换为对应的
`db ops detail`、`db slow list`、`db slow diag`。文本模式直接透传 db-cli 输出；
JSON 模式保留 bytedcli 的 `{status,data,error,context}` envelope，`data` 为同一
db-cli 命令的完整 JSON，`context.api_endpoint` 反映实际 DBW/RDS 路由。
三个兼容命令均支持 `--mode auto|legacy|dbw`：`auto` 按 VRegion 自动选择，
`legacy` 强制走 RDS，`dbw` 强制走 DBW。

## BPM 工单管理

```bash
# 创建 DDL 工单（推荐：不传 workflow-config-id，让 CLI 按 VRegion 选择后端）
# - China-BOE / China-BOE2：火山 DDL/DML 与字节云 DDL/DML 直连 DBW
# - ChinaSinf-North / Asia-SouthEastBD：火山 DDL/DML 与字节云 DML 直连 DBW，字节云 DDL 走 RDS/BPM
# - 其他 VRegion：字节云实例走 target_system=rds 的 BPM；火山实例暂不支持程序化提单
bytedcli --site boe rds bpm create \
  --ticket-type alter \
  --dbname "demo_db" \
  --sql "ALTER TABLE demo_table ADD COLUMN age INT;" \
  --background "变更原因"

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

# 创建 DML 工单：支持区域的火山实例统一调用 DBW CreateTicket，预检通过后提交
bytedcli --site boe rds bpm create \
  --dbname "demo_db" \
  --sql "UPDATE users SET status = 1 WHERE id = 100;" \
  --background "数据修复；回滚：UPDATE users SET status = 0 WHERE id = 100;" \
  --instance-id "vedbm-xxx"

# 字节云 DML：China-BOE / China-BOE2 走 DBW，其余 VRegion 按 region 查询 RDS/BPM workflow
bytedcli --site boe rds bpm create \
  --dbname "demo_db" \
  --sql "UPDATE users SET status = 1 WHERE id = 100;" \
  --background "数据修复"

# 其他 VRegion 的 DML 同样走 RDS/BPM
bytedcli --site cn rds bpm create \
  --dbname "demo_db" \
  --sql "DELETE FROM users WHERE id = 100;" \
  --background "删除错误数据；回滚：重新插入原记录"

# 创建 i18n-bd地区小机架机房 sinf-my DDL 工单 - ALTER
bytedcli --site i18n-bd --vregion sinf-my rds bpm create \
--workflow-config-id 396  \
--dbname "dbname" \
--sql "alter sql"  \
--background "表结构修复"

# 创建 i18n-bd地区小机架机房 sinf-my DML 工单
bytedcli --site i18n-bd --vregion sinf-my rds bpm create \
--workflow-config-id 397  \
--dbname "dbname" \
--sql "update/insert/delete sql"  \
--background "数据修复"

# 创建 EU TTP DDL 工单（region 可选 ie / no1a / us_east_gcp；建议显式 --region）
# 默认走 EU DDL workflow=261，无需 --workflow-config-id
bytedcli --site eu-ttp rds bpm create \
  --ticket-type alter \
  --region no1a \
  --dbname "demo_db" \
  --sql "ALTER TABLE demo_table ADD COLUMN age INT;" \
  --background "变更原因"

# 查看 / 列出 EU TTP 工单
bytedcli --site eu-ttp rds bpm get <record_id>
bytedcli --site eu-ttp rds bpm list --db-name "demo_db"

# 查看字节云 RDS BPM 工单详情
bytedcli --site cn rds bpm get <record_id>

# 查看 China-BOE / China-BOE2 / ChinaSinf-North / Asia-SouthEastBD 直连 DBW 工单详情
bytedcli rds bpm dbw ticket get --ticket-id "<ticket_id>" --instance-id "vedbm-xxx"

# 列出字节云 RDS BPM 工单
bytedcli --site cn rds bpm list --db-name "demo_db"
bytedcli --site cn rds bpm list --workflow-config-id <workflow_config_id> --status pending

# 取消工单
bytedcli --site boe rds bpm cancel <record_id> --reason "取消原因"

# 更新工单 SQL
bytedcli --site boe rds bpm update <record_id> --sql "新的 SQL"

# 获取工作流配置
bytedcli --site boe rds bpm get-workflow-config <workflow_config_id>

# DBW 工单兼容入口：翻译为 db ticket，并使用 CreateTicket → DescribePreCheckDetail → SubmitTicket
# DDL 的 TicketExecuteType 默认 Auto
bytedcli rds bpm dbw ticket create-ddl \
  --instance-id "vedbm-xxx" \
  --database "demo_db" \
  --sql-file "./ddl.sql" \
  --memo "create demo table" \
  --vregion ChinaSinf-North \
  --region-id huabei2 \
  --title "create demo table"

# DBW DML 兼容入口：使用 CreateTicket → DescribePreCheckDetail → SubmitTicket
bytedcli rds bpm dbw ticket create-dml \
  --instance-id "vedbm-xxx" \
  --database "demo_db" \
  --sql "UPDATE users SET status = 1 WHERE id = 100;" \
  --memo "repair user status" \
  --vregion ChinaSinf-North \
  --region-id huabei2 \
  --title "repair user status"

# DBW 工单兼容入口：由 db-cli 查询 / 预检 / 提交 / 自审批 / 取消
bytedcli rds bpm dbw ticket get --ticket-id "<ticket_id>" --instance-id "vedbm-xxx"
bytedcli rds bpm dbw ticket precheck --ticket-id "<ticket_id>" --instance-id "vedbm-xxx"
bytedcli rds bpm dbw ticket submit --ticket-id "<ticket_id>" --instance-id "vedbm-xxx"
bytedcli rds bpm dbw ticket approve --ticket-id "<ticket_id>" --workflow-id "<workflow_id>" --instance-id "vedbm-xxx" --comment "LGTM"
bytedcli rds bpm dbw ticket cancel --ticket-id "<ticket_id>" --instance-id "vedbm-xxx" --reason "不再需要"

# 字节云 ByteRDS 工单不需要 instance-id
bytedcli --site boe rds bpm dbw ticket get --ticket-id "<ticket_id>" --instance-type ByteRDS
```

## Notes

- `workflow-config-id` 与站点强相关，且可能复用/变更；建议优先不传，让 CLI 自动选择并做流程校验（避免误提到非 RDS 的工单）
- `rds bpm create` 显式传 `--ticket-type create|alter|dml` 时会强制走对应的 DDL 或 DML 路径，不再根据 SQL 判断；未传时才解析 SQL：`INSERT` / `UPDATE` / `DELETE` 走 DML，`CREATE` 走 DDL create，其余结构变更走 DDL alter
- `China-BOE`、`China-BOE2`、`ChinaSinf-North`、`Asia-SouthEastBD` 的火山实例 DDL/DML 通过 `db ticket create-ddl|create-dml` 访问 DBW；db-cli 会按数据库、VRegion 和可选实例 ID 调用 `DescribeInstances`，解析真实 `InstanceType`（支持 `VeDBMySQL`、`MySQL`、`MySQLSharding`）和 VDC 后建单。所有这些 MySQL 兼容火山实例统一执行 `CreateTicket → DescribePreCheckDetail → SubmitTicket`
- `rds bpm dbw ticket create-ddl|create-dml` 均要求显式传 `--memo` 说明变更背景；`--instance-type` 默认均为 `VeDBMySQL`，可显式覆盖为 DBW 支持的实例类型；在支持的 VRegion 中省略 `--instance-id`、`--instance-type`、`--ds-type` 时，兼容入口会按 ByteRDS 工单推断并传递 `--instance-type ByteRDS`。MySQLSharding DDL 默认按普通表提交；`create-ddl` 显式传 `--sharding --sharding-key <key> --sharding-key-type <int|varchar|string>` 时创建分片表，并将分片键及类型透传给 db-cli；`--sharding-key-type` 接受 `int`（归一化为 `Int`）、`varchar` 或 `string`（归一化为 `String`），大小写不敏感，开启 `--sharding` 时该参数必填。非分片表 DDL 及所有 DML 无需传这些参数
- 通过 bytedcli 创建 DBW DDL/DML 工单时，标题会统一追加 `<bytedcli>` 来源标记；未传 `--title` 时标题为 `<bytedcli>`。该规则覆盖 `db ticket create-ddl|create-dml`、`rds bpm dbw ticket create-ddl|create-dml` 以及 `rds bpm create` 的 DBW 分支
- 字节云 DDL/DML 使用独立能力表路由 DBW：DDL 当前为 `China-BOE`、`China-BOE2`；DML 当前为 `China-BOE`、`China-BOE2`、`ChinaSinf-North`、`Asia-SouthEastBD`。调用 `db ticket create-ddl|create-dml` 时可省略实例上下文，db-cli 会先用 `DescribeInstances` 自动识别 ByteRDS，且不传命令行 instance-id；内部使用 `CreateTicket`（协议字段 `InstanceId` 填数据库名），轮询 `DescribePreCheckDetail`，通过后调用 `SubmitTicket`。其他字节云 DDL/DML 走 RDS/BPM
- 火山实例显式提供 `--instance-id` 时可直接路由；未传时 CLI 会查询 RDS 元数据并尝试解析实例 ID。DBW 未覆盖 VRegion 的字节云 DDL/DML 会从 RDS `worksheets/types/` 自动解析 workflow 后走 BPM；火山实例的 DDL 与 DML 都仅支持 DBW 覆盖的 VRegion，其他 VRegion 会在请求 BPM 前直接拒绝。`--workflow-config-id` 仅用于 BPM 路径的显式覆盖
- 显式 `--vregion` 会覆盖 `--site` 的默认 VRegion；VRegion 不属于当前 site 时会在任何查询或提单前报错
- `--site i18n-bd` 不传 `--region` 时默认使用 `mycis`；也支持按 vregion 展示名显式传入并映射为 RDS region：`US-EE -> awsva`、`Asia-SaaS -> jpsaas`、`Singapore-SaaS -> sgsaas1larkidc1`、`Singapore-Common -> sgcomm1`、`Asia-CIS -> mycis`、`Asia-SouthEastBD -> sinf-my`。其中 `Asia-SouthEastBD/sinf-my` 会使用 `BYTECLOUD_HOST_I18N_BD_SINF_BPM + /api/v1/rds-sinf`，其他 i18n-bd RDS 读请求使用 `BYTECLOUD_HOST_I18N_BD + /api/v1/rds`
- `--site i18n-tt` 会自动将 RDS 读命令 region 映射为 `alisg`；如需 `maliva` 等其他区域，请显式传 `--region <value>`
- `--site eu-ttp`（EU TTP / EU-Compliance2）的 RDS 读/查询请求会走 `bc-iedt-gw.tiktok-eu.net` 受限网关；也支持按 vregion 展示名显式传入并映射为 RDS region：`EU-TTP -> no1a`、`EU-TTP2 -> no1a`、`EU-Compliance -> de`、`EU-Compliance2 -> ie2`
- `--site cn` 访问 ChinaSinf-North 区域库时，未替换的原生 RDS 读命令仍需经 `-r/--region` 传入地域。已由 db-cli 执行的 `rds db list|search|get|topology|qps|overview|query|table list|table schema`、`rds ops detail`、`rds slow list|diag` 可使用全局 `--vregion`，其中 `rds db list|search|get|topology|qps|overview` 也支持命令级 `--vregion`；显式值覆盖 site 默认 VRegion，命令级 `--region` 作为该 VRegion 的 VDC/region 传递
- BPM wrapper record 的审批/拒绝请使用 BPM Web UI；`rds bpm dbw ticket approve` 只适用于直连 DBW ticket-id，不适用于 BPM record-id
- `rds bpm dbw ticket create-ddl|create-dml|get|precheck|submit|approve|cancel` 由 rds 层翻译参数后调用 `db ticket`；创建时 db-cli 会按数据库和 VRegion 先自动识别 ByteRDS，未命中再解析火山实例。支持范围内的字节云 DDL/DML 无需命令行 instance-id。参数校验、DBW 请求、输出、错误和退出码均由同一个 db-cli 二进制负责
- DBW 后续操作按实例类型校验：Volc/默认 `VeDBMySQL` 必须提供 `--instance-id`，字节云 `ByteRDS` 可以省略；显式 `--site`、`--vregion`、`--region-id` 会覆盖默认映射
- DBW detail 返回 `WorkflowId` 时，审批必须透传 `--workflow-id`；缺少该字段可能触发 DBW 内部错误或拿不到真实权限错误
- DBW 直连工单的 `--ticket-id` 必须保留为字符串，避免 19 位工单号精度丢失
- `rds bpm create` 可省略 `--ticket-type` 让 CLI 按 SQL 识别；需要覆盖识别结果时传 `create`、`alter` 或 `dml`
- `rds bpm create` 与 `db bpm create` 共享同一套 VRegion、DDL/DML、实例类型、workflow 和 RDS/DBW 路由逻辑；`rds bpm change-record get|execute` 与 `db bpm change-record get|execute` 的校验和输出也保持一致
- RDS 读命令只会在未显式传 `--region` 时按站点补默认值；显式传入的 `--region` 会按内置 alias 归一化后传给 RDS API
- 已由 db-cli 执行的 `rds db list|search|get|topology|qps|overview|query|table list|table schema`、`rds ops detail`、`rds slow list|diag` 统一支持 `--mode auto|legacy|dbw`；默认 `auto`，其中 `legacy` 强制 RDS、`dbw` 强制 DBW，只在排障或已知特殊库时显式覆盖
- `--site boe` 查询 `vedb` / 多云库时，`db table list`、`db table schema`、`db query` 会自动按库详情里的实际 `volc_region` 路由到 DBW；推荐省略 `--region` 或显式传 `boe`
- 如果显式传 `--site boe --region cn`，CLI 会按 `cn` 原样请求，不会自动改写到 BOE DBW 读链路
- 对 BOE 多云库，`db params`、`alert rules`、`slow config` 当前会直接返回 `RDS_MULTI_CLOUD_UNSUPPORTED`；`slow list` 已由 db-cli 按 VRegion 路由 DBW/RDS
