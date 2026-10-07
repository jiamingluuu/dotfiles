---
name: bytedance-manta
description: "Operate Manta (DataLeap) data profiling, table monitor query/result/trial-run/create/update, alarm record queries, and two-table comparison via bytedcli: list namespaces and YARN queues, list/get/run/create/update table monitor rules, query monitor alarm results, query alarm records by alarm time, create profiling rules, list/get profiling jobs, create/list comparison jobs, query comparison job summaries and execution logs, and manage data quality tasks. Use when tasks mention Manta, DataLeap data profiling, monitor rules, monitor alarm results, alarm records, monitor rule trial runs, monitor rule creation/updates, data comparison, comparison job lists, comparison result summaries, comparison execution logs, data quality checks, profiling results, or profiling/comparison rules."
---

# bytedcli Manta

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

- DataLeap Manta 数据探查（Profiling）任务管理
- 查询 Manta namespace（`namespaces`）、表监控规则（`monitor list/get`）、试跑监控规则（`monitor run`）、监控报警结果（`monitor result list`）、单条监控结果详情（`monitor result get`）、多维报警明细（`monitor result alarm-detail`）、报警记录明细（`alarm-record list`）、创建监控规则（`monitor create`）、更新监控规则（`monitor update`）和数据探查任务（`profile job list/result`）
- 创建数据探查规则（`profile rule create`）
- 两表数据对比（`comparison job create`）
- 查询两表对比任务列表（`comparison job list`，默认只看我的任务）
- 查询两表对比结果（`comparison job get`，支持 `--view summary|overview`）
- 查询两表对比任务执行日志（`comparison job log`）
- 查询指定字段的 diff SQL（`comparison job diff-sql`）
- SQL 数据比对，自动处理 map/array 字段（`comparison sql create`）
- 数据质量检查与分析

## Agent Guidance

**鉴权前置：** Manta 由 bytedcli 自动完成鉴权（ByteCloud SSO JWT 自动换取 Dataleap JWT，写入 `x-dataleap-jwt-token`），**无需浏览器登录、无需 cookie**。执行任何 Manta 命令前，只需确保已完成对应站点的 SSO 登录：

1. CN / SGLARK 站点（`cn`、`sglark`）：`bytedcli auth login`
2. TikTok 站点（`sg`、`va`、`eu`）：`bytedcli --site i18n-tt auth login`
3. ByteIntl 站点（`mycis`、`mybd`、`jplark`、`uspipo`）：`bytedcli --site i18n-bd auth login`
4. `mycis` 属于 built-in region，站点映射到 `i18n-bd`，不要再按 `i18n-tt` 口径引导登录

**yarn 队列（自动探测）：** `--yarn-cluster` 和 `--yarn-queue` 是创建探查任务的必填参数。不同区域的队列完全不同，**禁止猜测或编造队列名**。正确做法：

1. 先通过 `bytedcli manta yarn-queues --region <region>` 列出用户有权限的队列
2. 从返回结果中选取合适的队列（优先选 load_rate 较低的）
3. 将队列的 `yarn_cluster` 和 `yarn_queue` 字段分别传给 `--yarn-cluster` 和 `--yarn-queue`

**标准操作流程（数据探查）：**

1. `bytedcli manta yarn-queues --region <region>` — 探测可用队列
2. `bytedcli manta profile rule create --region <region> --yarn-cluster <cluster> --yarn-queue <queue> ...` — 创建探查任务

**MYCIS profile create 注意点：** Manta MYCIS 的 profile `create-rule` 接口 host 按 `mycis` 路由，但请求体中的后端 profile region 与对外 region 不完全一致。CLI 会自动转换；如果使用 `--body-file` 手写完整请求体，先通过 `bytedcli manta namespaces --region mycis` 确认可用 namespace，不要直接把外部 region 硬编码进 payload。`list` / `yarn-queues` 与 `create` 的 region 语义可能不同，联调时要分别验证。

**标准操作流程（两表对比）：**

1. `bytedcli manta comparison job create --region <region> --db-name-old <db> --tb-name-old <tb> --partition-old <p> --db-name-new <db> --tb-name-new <tb> --partition-new <p> --primary-keys "<keys>"` — 创建对比任务
2. `bytedcli manta comparison job get --region <region> --instance-id <id> [--view summary|overview]` — 查询对比任务概要或 overview 结果
3. `bytedcli manta comparison job log --region <region> --instance-id <id>` — 查询对比任务执行日志

**两表对比区域参数：**

- 同机房模式中，`--region-name-old <name>` 与 `--region-name-new <name>` 必须同时提供，分别设置请求体 `table_region_old` 与 `table_region_new`；都不传时，两侧默认使用 `--region`。
- 未加 `--cross-region` 时，这两个参数只设置表区域元数据；API 路由、鉴权、两侧 schema 和队列查询继续使用 `--region`。
- `--body-file` 继续覆盖结构化参数；但只传一侧区域参数仍会报错，即使同时指定了 `--body-file`。

**跨机房两表对比（SG / VA）：**

- 加 `--cross-region`，并同时指定 `--region-name-old` / `--region-name-new`；此模式使用 `region_old` / `region_new`，不发送单区域 `region` 或 `table_region_old/new`。不加此标记时，原有表区域参数语义不变，不能用于跨机房执行。
- `--region` 是请求入口，必须与旧表机房一致。SG 使用 `sg`；VA 接受 `va` 或 `i18n` 作为两侧区域参数（大小写不敏感），请求体使用 `i18n`，schema 和队列查询走 `va`。目前只支持 SG 与 VA 之间的跨机房组合。
- `--yarn-queue-old` 配置旧表队列，`--yarn-queue-new` 配置新表队列；跨机房格式必须为 `region/idc/cluster/queue`，VA 队列区域必须为 `va`。`--yarn-queue` 保留为旧表队列的兼容别名，不能与 `--yarn-queue-old` 同时提供不同值。省略时分别查询各自机房的可用队列并选取低负载队列，提示会标明 old/new 和所选队列；禁止编造队列。
- 两侧 schema 分别查询；同机房和跨机房均可省略 `--primary-keys`，从共有 schema 优先选择 `id` 或 `<新表名>_id`，否则使用未被显式指定为对比列的共有字段组成联合主键；无候选字段时报错。显式参数优先，自动推测不验证唯一性；预览会展示最终主键。跨机房主键和显式对比列必须存在于对应 schema。
- 跨机房默认只预览请求，使用 `--yes` 提交；`--dry-run` 始终仅预览，即使同时传入 `--yes`。同机房保留原有直接提交行为，`--yes` 不额外改变行为。预览后提交必须移除 `--dry-run`，跨机房还需加 `--yes`。
- `--body-file` 支持原始跨机房 JSON（`region_old/new`、`extra_conf.queue/queue_new`）；入口通过 `--region` 指定或文件的 `region` 设置。跨机房文件同样默认预览，`--yes` 才提交。文件与结构化参数生成的请求共用 API 校验，预览和提交均检查两侧区域、队列与主键；跨机房文件不能混用 `table_region_old/new`。
- 提交后读取 summary 和 log，确认 `region_old/new` 与双侧执行机房，不能仅凭创建成功或 diff=0 判定跨机房验证成功。

```bash
bytedcli manta comparison job create --region sg --cross-region --region-name-old sg --region-name-new i18n --db-name-old demo_db --tb-name-old demo_table --partition-old date=20260909 --db-name-new demo_db --tb-name-new demo_table --partition-new date=20260909 --primary-keys id --yarn-queue-old sg/virtual/virtual-sg/root.demo --yarn-queue-new va/virtual/virtual-va/root.demo
# 确认预览后，对同一条命令加 --yes 提交
```

**两表对比字段明细与队列：**

- 推荐使用 `--further-detail` 将全部对比字段的 `further_detail` 设为 `true`，适用于同机房、跨机房、自动/显式对比列和 `--body-file`；不增加字段，也不改变 `diff_types`。不传时保留原有逐列配置及默认值。 与 `--body-file` 合用时，文件必须包含 `field_details` 数组；该参数不自动查询或补全文件中的字段。
- `--comparison-columns` 兼容逐列格式 `col_old,col_new,absolute_equal,detail`，仅第 3 个及之后的 `detail` token 开启该字段明细；前两个位置是列名，因此名为 `detail` 的列不会自动开启明细。可结合 `--dry-run` 检查最终请求。
- 同机房 `--yarn-queue-old`（兼容别名 `--yarn-queue`）支持裸队列名或完整 `region/idc/cluster/queue`；包含 `/` 时必须为 4 个非空段，错误格式会在本地报错。裸队列名沿用当前 region 的 `virtual` IDC 与 `virtual-<region>` cluster。跨机房必须使用完整格式。

**两表对比结果命名约定：**

- 对比任务列表使用 `bytedcli manta comparison job list --region <region> [--keyword <keyword>] [--business-date <yyyymmdd>]`，默认等价页面的“只看我自己”，需要全量时传 `--all`
- 对比结果查询统一收敛为资源化读命令：概要或 overview 使用 `bytedcli manta comparison job get --region <region> --instance-id <id> [--view summary|overview]`
- 对比执行日志使用 `bytedcli manta comparison job log --region <region> --instance-id <id>`，用于查看 Manta comparison 后端提交与执行明细
- 指定字段的差异 SQL 使用 `bytedcli manta comparison job diff-sql --region <region> --instance-id <id> --old-column <name> --new-column <name>`
- 对外命令不要直接暴露后端 endpoint 名字，如 `instance-list`、`result-info`、`result-overview`、`diff/sql`；这些路径只作为 API 层实现细节保留

**标准操作流程（SQL 比对 — 适合含 map/array 字段的表）：**

1. 如果用户已明确 `--map-keys` / `--json-keys`，直接跳到步骤 4
2. 若用户不清楚哪些字段是复杂结构体（map/array），先探查表 schema：
   - `bytedcli --json hive detail <db> <table> --region <region>` — 从返回的 `fields[].dataType` 中识别 `map<>`、`array<>` 类型字段
   - 将找到的复杂字段及其类型告知用户
3. 若存在 `map<>` 字段，需要了解 map 内部有哪些 key 才能展开对比。此时**询问用户是否要执行 adhoc 查询来发现 map key**：
   - 若用户同意，**要求用户提供 Dorado 临时查询 task-id 或 DataLeap 任务链接**（格式如 `https://dataleap-<region>.tiktok-row.net/dorado/development/query/<task-id>?project=...`，从 URL 路径中提取 `<task-id>`）
   - 使用 `bytedcli dorado adhoc exec` 查询每个 map 字段的 key 分布，例如：
     ```
     bytedcli --json dorado adhoc exec \
       "SELECT k, COUNT(1) as cnt FROM <db>.<table> LATERAL VIEW explode(<map_col>) t AS k, v WHERE <filter> GROUP BY k ORDER BY k" \
       --task-id <task-id> --region <region>
     ```
   - 若源表和目标表的过滤条件不同，分别查询两侧的 key，取并集
   - 将发现的 key 列表组装为 `--map-keys "col=key1,key2,..."`
   - 若用户拒绝查询，可以不指定 `--map-keys`，map 列将作为原始字符串整体对比
4. `bytedcli manta comparison sql create --region <region> --source-table <db.table> --target-table <db.table> --source-filter "<condition>" --target-filter "<condition>" --join-keys "<keys>" --map-keys "<spec>" --dry-run` — 先 `--dry-run` 预览 SQL
5. 确认 SQL 无误后，去掉 `--dry-run` 正式提交

**缺参时优先追问：**

- `--region`：用户要操作哪个区域
- 探查：`--db-name` + `--tb-name` + `--partitions`
- 对比：`--db-name-old/new` + `--tb-name-old/new` + `--partition-old/new` + 可选 `--primary-keys`（优先使用用户指定值；省略时由 CLI 从两侧共有 schema 自动推断，不验证唯一性）
- SQL 比对：`--source-table` + `--target-table` + `--join-keys`（关联键必须由用户指定或确认）

**监控规则查询/创建/更新经验：**

- 查询具体表的监控规则时，如果已知项目归属，优先显式传 `--project-id`
- 在 `mycis` 等区域，仅传 `--table-name-query` 或不带项目过滤时，`manta monitor list` 后端可能返回 `50005`
- 推荐命令：`bytedcli manta monitor list --region <region> --project-id <id> --table-name-query <db.table>`
- `manta monitor list` 与 `manta monitor result list` 默认都应携带 `--project-id`；CLI 会在缺失时直接报参数错误
- 查询监控报警结果使用 `bytedcli manta monitor result list`；`--mode template` 查询 Hive 模板规则结果，`--mode custom` 查询自定义 SQL 规则结果，默认 `--mode all` 同时查询两类结果
- 查询“按报警时间筛选的报警记录明细”使用 `bytedcli manta alarm-record list`；需要显式传 `--alarm-time-start` + `--alarm-time-end`，并建议始终带 `--project-id`
- 常用过滤：`--business-date-start <yyyymmdd>` + `--business-date-end <yyyymmdd>` 组成日期范围（必须成对出现）；`--rule-id <id>` 按业务规则 ID 搜索，`--mine` 只看我的结果，`--only-alarm` 只看已报警结果，`--project-id <id>` 可重复指定项目
- `alarm-record list` 的常用过滤：`--status all|unresponded|responding|processed`、`--mine`、`--night-alarm`、`--project-id <id>`（可重复）以及 `--alarm-time-start <yyyy-mm-dd>` + `--alarm-time-end <yyyy-mm-dd>`（必须成对出现）
- 单条结果下钻：`monitor result list` / `alarm-record list` 拿到 `history_id` 后，先 `bytedcli manta monitor result get --region <region> <history_id>` 查看主体配置与任务状态，再 `bytedcli manta monitor result alarm-detail --region <region> <history_id>` 获取逐维度报警明细行（对应页面"详情"弹窗数据）
- 查询某条规则详情：`bytedcli manta monitor get --region cn --rule-id <id>`（`--mode` 可选，默认 `custom`）
- 试跑规则使用 `bytedcli manta monitor run --region cn --rule-id <id> --date "YYYY-MM-DD HH:mm:ss"`；`--rule-id` 可重复传多个，试跑结果用 `manta monitor result list --business-date-start ... --business-date-end ... --rule-id ... --project-id ...` 查询
- 创建规则统一使用 `bytedcli manta monitor create --mode <custom|template> ...`
  - `--mode custom` → `POST /monitor/batch_create_monitor`
  - `--mode template` → `POST /monitor/batch_create_monitor_with_object`
  - 不传 `--body-file` 时，至少需要 `--project-id`、`--monitor-name`、`--monitor-type`；`custom` 模式还需要 `--rule-sql`
  - 传 `--body-file` 时，请求体完整直传并覆盖结构化参数
- 更新规则时，`--body-file` 为完整请求体直传；不传 `--body-file` 时，CLI 会先读取当前规则详情并合并本次传入字段后提交。模板分区更新仅调用 `update_monitor` 往往不会真正生效；CLI 在检测到模板规则分区变化时，会先把请求体里的分区归一到顶层 `part_name`，再额外调用对象分区接口 `/monitor/object/partition/modify`。若更新请求中的 `monitor_state` 与当前状态不同，CLI 还会在完整更新后调用启停接口
- 修改报警渠道与收件人用结构化参数：`--alarm-channels lark,phone,sms`（`lark`=飞书→`normal`，`phone`/`sms`→`critical`，即电话+短信+飞书=`alarm_level:"normal,critical"`），`--alarm-roles table-owner,task-owner,specified-user`（→`user_alarm_roles` 的 `TABLE_OWNER`/`DORADO_TASK_OWNER`/`CONCRETE_PERSON`），`--alarm-users <名单>`，`--alarm-groups <群id>`（→`alarm_conf.groups`），`--alarm-duty-plans <值班计划>`（→`alarm_conf.duty_plan_list`）。注意 `--alarm-conditions` 改的是阈值规则、不是渠道；且改收件人时后端以 `user_list` 为准，CLI 会自动同时写 `users`/`user_ids`/`user_list`；只覆盖你传入的 alarm_conf 字段，其余保留
- 关闭监控规则时，使用 Manta 后端枚举值 `DISABLE`；CLI 通过监控规则启停接口提交状态变更

**`custom + --body-file` 已验证可用结构（推荐）：**

```bash
bytedcli manta monitor create --region cn --mode custom --body-file skills/bytedance-manta/references/demo-manta-custom-monitor-sources.json
```

- 示例请求体文件：`skills/bytedance-manta/references/demo-manta-custom-monitor-sources.json`
- 自定义 SQL 规则在 `--body-file` 模式下优先使用 `monitor_sources[].monitor_conf_list[]` 结构，比扁平字段更稳妥。
- 模板规则在 `--body-file` 模式下也应优先使用同一层级结构：顶层 `alarm_conf` + `monitor_sources[]`，并将单条规则放在 `monitor_sources[].monitor_conf_list[]` 中；不要把 `monitor_name`、`monitor_type`、`alarm_conditions`、`queue_conf`、`monitor_conf` 等字段直接平铺到顶层。
- `template + --body-file` 已验证可用时，`monitor_sources[]` 内至少应包含：`db_name`、`tb_name`、`project_id`、`region`、`part_name`、`bind_tasks`；`monitor_conf_list[]` 内至少应包含：`monitor_name`、`monitor_type`、`alarm_conditions`，通常还需要 `launch_type`、`timeout`、`queue_conf`。
- 模板规则如果走任务触发，`bind_tasks.tasks[].task_frequency` 需要与任务真实频率一致（例如 `daily`）；若改成非任务触发或手工构造 body，仍需保证后端能推导出合法 frequency，否则可能返回 `The frequency [null] is not supported`。
- 推荐优先复用示例请求体文件：`skills/bytedance-manta/references/demo-manta-template-monitor-sources.json`。

## 前置条件

- 使用通用调用方式：`../../invocation.md`
- **必须先完成对应站点的 SSO 登录**（CN/SGLARK：`bytedcli auth login`；TikTok：`bytedcli --site i18n-tt auth login`；ByteIntl：`bytedcli --site i18n-bd auth login`）。bytedcli 会自动用 SSO 凭据换取 Dataleap JWT，无需浏览器、无需 cookie。
- 跨机房对比需具备 SG 与 VA 两侧表的读取权限和各自可用队列的使用权限；可分别运行 `bytedcli manta yarn-queues --region sg` 与 `bytedcli manta yarn-queues --region va` 检查队列，队列不可用时需选择有权限的队列。

> 执行前缀见 `../../invocation.md`；下面示例直接写 `bytedcli`。

## Quick start

Commands are grouped under `manta namespaces`, `manta yarn-queues`, `manta monitor`, `manta profile`, and `manta comparison` (including `comparison job` and `comparison sql`).

```bash
# 步骤 1：查看可用的 YARN 队列
bytedcli manta yarn-queues --region va

# 查看 namespace 或历史数据探查任务
bytedcli manta namespaces --region va
bytedcli manta monitor list --region va --table-name-query demo_db.demo_table --project-id 1234567
bytedcli manta monitor result list --region cn --mode all --business-date-start 20260518 --business-date-end 20260519 --rule-id 123456 --mine --only-alarm --project-id 1234567 --page-size 50
bytedcli manta alarm-record list --region cn --project-id 1234567 --alarm-time-start 2026-05-20 --alarm-time-end 2026-05-26 --mine
bytedcli manta monitor get --region cn --rule-id 1552347
bytedcli manta monitor run --region cn --rule-id 1552347 --date "2026-05-19 00:00:00"
bytedcli manta monitor create --region cn --mode custom --project-id 1085 --monitor-name demo_rule --monitor-type Custom_SQL --rule-sql "select 1"
bytedcli manta monitor create --region cn --mode template --project-id 1085 --monitor-name demo_template_rule --monitor-type Table_Lines
bytedcli manta monitor update --region cn --rule-id 1552347 --description sample-update
bytedcli manta profile job list --region va --table-name-query demo_table --limit 20
bytedcli manta profile job result --region va --instance-id 123456

# 步骤 4a：创建数据探查规则（省略 --columns 会自动探查全部字段，YARN 队列自动选择）
bytedcli manta profile rule create --region va --db-name demo_db --tb-name demo_table --partitions date=20260401

# 步骤 4a（多级分区）：用 / 分隔多级分区
bytedcli manta profile rule create --region va --db-name demo_db --tb-name demo_table --partitions date=20260401/asset_type=sdk/metrics_tag=basic_info

# 步骤 4b：创建两表对比任务（可显式指定主键和对比列，或使用 CLI 自动推断并查看预览）
bytedcli manta comparison job create --region va --db-name-old demo_db --tb-name-old demo_table --partition-old date=20260401 --db-name-new demo_db --tb-name-new demo_table --partition-new date=20260402 --primary-keys "id"

# 查看我的对比任务列表
bytedcli manta comparison job list --region va --page-size 10

# 查看对比任务概要
bytedcli manta comparison job get --region va --instance-id 123456

# 查看对比任务 overview
bytedcli manta comparison job get --region va --instance-id 123456 --view overview

# 查看对比任务执行日志
bytedcli manta comparison job log --region va --instance-id 123456

# 查看指定字段的 diff SQL
bytedcli manta comparison job diff-sql --region va --instance-id 123456 --old-column obj_type --new-column obj_type

# 步骤 4b（多级分区）：用 / 分隔多级分区
bytedcli manta comparison job create --region va --db-name-old demo_db --tb-name-old demo_table --partition-old "date=20260401/asset_type=sdk/metrics_tag=v1" --db-name-new demo_db --tb-name-new demo_table --partition-new "date=20260401/asset_type=sdk/metrics_tag=v2" --primary-keys "id"
```

更多示例：

```bash
# 列出 SG 区域的队列
bytedcli manta yarn-queues --region sg

# 通过 JSON 文件创建探查（可跳过显式参数）
bytedcli manta profile rule create --body-file ./demo-profile-rule.json

# 两表对比：指定主键和对比列
bytedcli manta comparison job create --region sg --db-name-old demo_db --tb-name-old demo_table --partition-old date=20260402 --db-name-new demo_db --tb-name-new demo_table --partition-new date=20260403 --primary-keys "upstream_id;downstream_id" --comparison-columns "col_a;col_b;col_c"

# 两表对比：显式指定请求体两侧表区域
bytedcli manta comparison job create --region sg --region-name-old sg --region-name-new i18n --db-name-old demo_db --tb-name-old demo_old_table --partition-old date=20260402 --db-name-new demo_db --tb-name-new demo_new_table --partition-new date=20260403 --primary-keys "id"

# 两表对比：通过 JSON 文件
bytedcli manta comparison job create --body-file ./demo-comparison.json

# SQL 比对：自动处理 map/array 字段
bytedcli manta comparison sql create --region cn --source-table demo_db.demo_table --target-table demo_db.demo_table --source-filter "date='20260405' and type='A'" --target-filter "date='20260405' and type='B'" --join-keys user_id

# SQL 比对：展开 map 字段并预览 SQL
bytedcli manta comparison sql create --region cn --source-table demo_db.demo_table --target-table demo_db.demo_table --source-filter "date='20260405'" --target-filter "date='20260404'" --join-keys user_id --map-keys "metrics=cpu,mem" --dry-run
```

## Supported Regions

| Region   | Description        | Endpoint                      |
| -------- | ------------------ | ----------------------------- |
| `cn`     | China (default)    | data.bytedance.net            |
| `sg`     | Singapore          | dataleap-sg.tiktok-row.net    |
| `va`     | US East (Virginia) | dataleap-va.tiktok-row.net    |
| `eu`     | EU                 | dataleap.tiktok-eu.net        |
| `mycis`  | MYCIS              | dataleap-mycis.byteintl.net   |
| `mybd`   | MY (ByteIntl)      | dataleap-mybd.byteintl.net    |
| `sglark` | SG Lark            | dataleap-sglark.bytedance.net |
| `jplark` | JP Lark            | dataleap-jp.byteintl.net      |
| `uspipo` | US PIPO            | dataleap-pipo-us.byteintl.net |

## Authentication

Manta 由 bytedcli **自动鉴权**：用 ByteCloud SSO JWT 通过 DataLeap `/user/jwt` 接口换取 Dataleap JWT，写入请求头 `x-dataleap-jwt-token`，**无需浏览器登录、无需 cookie**。执行命令前只需完成对应站点的 SSO 登录：

```bash
# CN / SGLARK 站点（cn、sglark）
bytedcli auth login

# TikTok 站点（sg、va、eu）
bytedcli --site i18n-tt auth login

# ByteIntl 站点（mycis、mybd、jplark、uspipo）
bytedcli --site i18n-bd auth login
```

Region-to-SSO 站点映射：

- `cn`、`sglark` -> `cn` 站点（ByteDance SSO）
- `sg`、`va`、`eu` -> `i18n-tt` 站点（TikTok SSO）
- `mycis`、`mybd`、`jplark`、`uspipo` -> `i18n-bd` 站点（ByteIntl SSO）

> 多机房 `/user/jwt` 直接换取已知差异：`cn`、`sg` 用裸 ByteCloud JWT 即可换出 Dataleap JWT；`sglark`（cn 站，但 issuer authMode=session）、`mycis` / `mybd` / `jplark` / `uspipo`（i18n-bd 站）需要 cookie-gated bootstrap，CLI 已通过 Dorado session bootstrap 自动兜底。如果某 region 仍返回「用户未登录」类错误，请先确认对应站点 SSO 已登录。

## Notes

- 需要结构化输出加 `--json`（全局参数，放在 `manta` 前面）
- `monitor list` 通过 `POST /monitor/object/find_monitors` 查询规则；文本模式会按“表/分区/规则/状态”展开 `parts[].monitors[]`
- `monitor run` 通过 `POST /monitor/dry_run` 试跑规则，请求体包含 `monitor_id_list` 和 `date`；`--date` 使用 `YYYY-MM-DD HH:mm:ss`
- `monitor result list` 查询监控报警结果；`--mode template` 走 Hive 模板结果接口，`--mode custom` 走自定义 SQL 结果接口，默认 `all` 合并两类结果；文本模式输出扁平表格，`--json` 保留原始响应
- `monitor result get <result-id>` 走 `GET /instance/detail/instance_monitor`，返回单条结果主体（监控/任务/表/分区/报警状态）；`monitor result alarm-detail <result-id>` 走 `GET /instances/multi-dimension-detail`，返回该结果触发的逐维度报警明细（`dimension_header` + `index_header` + `content` 行）；两者共用 `monitor result list` 输出的 `history_id`
- `alarm-record list` 查询报警记录详情，按报警时间范围过滤；`--status all|unresponded|responding|processed` 分别映射全部、未响应、响应中、已处理，`--mine` 只看当前用户作为报警接收人的记录
- `monitor create` 统一走单命令 + `--mode`：`custom` 调 `POST /monitor/batch_create_monitor`，`template` 调 `POST /monitor/batch_create_monitor_with_object`；传 `--body-file` 时请求体完整直传
- `--columns` 支持简写格式 `name:type,...` 和完整 JSON 数组两种形式；省略时自动获取表 schema 并探查全部字段
- `--partitions` 可重复传入多个分区；多级分区用 `/` 分隔，例如 `date=20260401/asset_type=sdk/metrics_tag=basic_info`
- `--partition-old` / `--partition-new` 同样支持多级分区格式，例如 `date=20260401/asset_type=sdk/metrics_tag=v1`
- `profile rule create` 在创建成功后会输出 report URL，可直接打开查看 Profiling 结果
- YARN 队列：探查和对比都会自动从用户可用队列中选取负载最低的，无需手动指定；也可通过 `--yarn-cluster`/`--yarn-queue`（探查）或 `--yarn-queue-old region/idc/cluster/queue`（两表对比，跨机房另有 `--yarn-queue-new`）显式指定
- `comparison job create` 在创建成功后会输出对比 report URL
- `comparison job list` 走 `POST /comparison/instance-list`，默认 `is_myself=true`，支持 `--keyword`、`--business-date`、`--page`、`--page-size`，传 `--all` 时查询全部可见任务
- `comparison job get` 默认走 `GET /comparison/result-info`；传 `--view overview` 时走 `GET /comparison/result-overview`；两种结果都会附带 report URL
- `comparison job log` 走 `GET /comparison/log`，按 `instance_id` 返回执行日志；文本模式优先输出 `tracking_url` 和 `detail_log`，若日志未就绪会提示稍后重试同一条命令
- `comparison job diff-sql` 走 `GET /comparison/diff/sql`，按 `instance_id + old_column + new_column` 获取指定字段的 diff SQL
- 对比任务的 `--primary-keys` 控制 JOIN 匹配行，`--comparison-columns` 控制对比哪些字段；两者用 `;` 分隔多项
- 优先使用用户指定的业务主键；同机房和跨机房省略时 CLI 均会自动推断并发出警告。用户选择自动推断时可使用该逻辑，不能把推断结果当作唯一性校验
- `comparison sql create` 生成自定义 SELECT SQL 并提交到 Manta SQL 比对端点，适合含 `map<>`/`array<>` 复杂类型字段的表
- `--map-keys` 格式为 `col=key1,key2;col2=key3,key4`，指定 map 字段需要展开的 key；未指定时保留原始列
- `comparison sql create --dry-run` 仅生成 SQL 并输出列信息，不提交任务

## References

- `references/manta.md`
