# OneService CLI 命令参考

> 所有命令都以 `bytedcli oneservice` 开头。全局 flag（`--json` / `--site` / `--http-debug`）必须放在子命令**前面**：`bytedcli --json oneservice ...`
>
> 控制面命令支持：`--site cn`（默认，CN 生产）| `i18n-tt`（SG / TikTok）| `i18n-bd`（MYBD / ByteIntl）；其它站点会抛 `ONESERVICE_SITE_UNSUPPORTED`。
> 直接 AGW 命令 `api query` / `api sql-query` 额外支持 `eu-ttp`（EU-TTP）和 `us-ttp`（US-TTP）。BOE 通过 `--env boe` 选择，不是控制面 `--site`。

---

## physical table

```text
bytedcli oneservice physical get --physical-table-id <id>
bytedcli oneservice physical field update --physical-table-id <id>
  --fields <json-array>
  (--logic-table-id <id> | --logic-table-ids <id,id...>)
  [--confirm-token <token>]
bytedcli oneservice physical ready-time get --physical-table-id <id> [--region <region> ...]
bytedcli oneservice physical ready-time-option list --physical-table-id <id>
bytedcli oneservice physical ready-time update --physical-table-id <id>
  --config <json-object> [--confirm-token <token>]
bytedcli oneservice physical owner update
  (--physical-table-id <id> | --physical-table-ids <id,id...>)
  [--owner <userCode> ...] [--editor <userCode> ...]
```

- `field update` 的 `--fields` 是新增/修改 patch；允许 `name`、`type`、`comment`/`description`、`is_pk`、`is_realtime`、`private_level`。不允许 ID、deleted 或关联字段，也不支持删除
- `field update` 首次只预览完整 target 和 diff；第二次必须带预览返回的 `confirm_token`。当前字段、目标或关联逻辑表 ID 漂移时 token 失效
- `ready-time get` 的 `--region` 可重复或逗号分隔；只接受 Invoke Common canonical region。未传时只查询当前配置中的 region，不猜默认海外区域
- `ready-time-option list` 返回当前配置、分区字段、项目处理函数、Dorado 区域映射和环境选项
- `ready-time update` 接完整 ReadyTimeConfig，首次只预览。跨区域写入非原子；出现 `region_errors` 时先重读全部区域并对比 before，再确认恢复
- `owner update` 的 Owner / Editor 至少传一类，也可同时传。只修改提供的类别，不支持清空
- 物理表 ID、字段 ID、逻辑表 ID、ready-time ID 与 `config.partitions[].idx` 在 CLI 内均保持 string；后端要求 JSON number 的字段由 CLI 直接构造数字字面量，不经过 JavaScript Number

```bash
bytedcli --json oneservice physical get --physical-table-id 1234567890123456789
bytedcli --json oneservice physical field update --physical-table-id 1234567890123456789 \
  --logic-table-id 2234567890123456789 --fields '[{"name":"id","comment":"reviewed"}]'
bytedcli --json oneservice physical ready-time get --physical-table-id 1234567890123456789 --region SG
bytedcli --json oneservice physical ready-time-option list --physical-table-id 1234567890123456789
bytedcli --json oneservice physical owner update --physical-table-id 1234567890123456789 \
  --owner zhangsan --editor lisi
```

---

## project

```
bytedcli oneservice project list [--keyword <substring>]
bytedcli oneservice project search [--keyword <keyword>]
bytedcli oneservice project permission get --project-id <projectId>
bytedcli oneservice project webhook update --project-id <projectId> \
  --webhook-url <url> [--webhook-url <url> ...] \
  --event <event> [--event <event> ...]
```

列出当前用户有创建权限的所有 OneService 项目。

- `--keyword`：在项目名上做客户端子串匹配（大小写不敏感）
- 返回字段：`id`、`name`、`business_id`，后端返回描述时归一为 `description`；不从 `creator` 推导 `owner`
- `search`：只按项目名检索；省略 `--keyword` 时返回当前站点和租户范围内的后端结果，不承诺包含调用者无权限的项目
- `permission get`：精确检查当前 JWT 用户是否拥有目标项目的 API 创建角色
- `webhook update`：完整替换 webhook URL 与事件订阅；事件支持 publish/offline audit、success 与 publish pre-check。该命令没有通用 readback/恢复接口，不得自动修改共享项目

```bash
bytedcli oneservice project list
bytedcli --json oneservice project list --keyword demo
bytedcli oneservice project search
bytedcli oneservice project search --keyword demo
bytedcli oneservice project permission get --project-id 1234567890123456789
bytedcli oneservice project webhook update --project-id 1234567890123456789 \
  --webhook-url https://example.com/oneservice-hook --event publish_success
```

---

## folder list / folder create

```
bytedcli oneservice folder list   --project-id <projectId>
bytedcli oneservice folder create --project-id <projectId> --name <folderName>
```

- `list` 返回项目下每个文件夹的 `title` 和 `file_count`
- `create` 不允许重名。`oneservice api create --folder` 已经会自动 ensure 文件夹，所以这条命令很少直接用

```bash
bytedcli oneservice folder list --project-id 1234567890123456789
bytedcli oneservice folder create --project-id 1234567890123456789 --name ai_generated
```

---

## datasource

```
bytedcli oneservice datasource list --project-id <projectId>
  [--keyword <keyword>] [--type <type>] [--source <source>] [--ds-region <region>]
  [--page <n>] [--page-size <1-100>]
bytedcli oneservice datasource search --project-id <projectId>
  [--keyword <keyword>] [--type <type>] [--source <source>] [--ds-region <region>]
  [--page <n>] [--page-size <1-100>]
bytedcli oneservice datasource property list [--name source|type|region]
bytedcli oneservice datasource region list --datasource-id <datasourceId>
bytedcli oneservice datasource config get --datasource-id <datasourceId> --ds-region <region>
```

- `list` 是跨区域去重的 panel 视图；`search` 是当前或 `--ds-region` 指定的单一区域视图。
- 全局 `--site cn|i18n-tt|i18n-bd` 选择控制面；`--ds-region` 过滤或定位数据源存储区域，两者不要混用。
- `config get` 在 API/parser 边界强制脱敏 password、token、keytab、krb5conf、access key 等 credential-like 字段。文本、JSON、MCP 都只会看到 `[REDACTED]` 和 `redacted_fields`，没有明文旁路。
- 所有 datasource ID / project ID 在 CLI 内保留 string，避免 int64 精度丢失。

---

## lineage

```text
bytedcli oneservice lineage get --asset-id <id> --asset-type <type>
  [--last-call-period last_1d|last_3d|last_7d|last_14d|last_30d|last_60d|last_90d]
  [--online-only]
```

- `--asset-type` 支持 `data_source|physical_table|logical_table|api|app`；默认调用窗口为 `last_90d`
- 命令只读并直连 OneService lineage OpenAPI，不要求 `bytedcli auth login`，也不会发送 JWT。用全局 `--site cn|i18n-tt|i18n-bd` 选择控制面，不提供 `--region`
- 文本模式展示从入口资产向数据源的 upstream 树，以及从入口资产向应用的 downstream 树；`--json` 返回结构化 `entry`、`projects`、`upstream`、`downstream`
- `app` 作为入口时，后端可能不返回对应节点。此时改用该应用调用的 API 作为入口
- 资产 ID 与项目 ID 全程按 string 保真；无关系边、空数组或后端 `null` 列表均返回空树，不伪造关系

```bash
bytedcli --site cn oneservice lineage get \
  --asset-type logical_table --asset-id 1234567890123456789
bytedcli --json --site i18n-tt oneservice lineage get \
  --asset-type api --asset-id 2234567890123456789 \
  --last-call-period last_30d --online-only
```

---

## metric

```text
bytedcli oneservice metric business-line list --project-id <projectId> [--business-id <id>]
bytedcli oneservice metric topic list --business-id <businessId> [--query <keyword>]
bytedcli oneservice metric view list --business-id <businessId> --topic-id <topicId>
  [--include-no-sql]
bytedcli oneservice metric view-detail get --view-id <viewId>
bytedcli oneservice metric operator list
bytedcli oneservice metric object get
  [--metric-id <id> ...] [--dimension-id <id> ...]
bytedcli oneservice metric engine-grammar-type get
  [--version-id <id>] [--logic-table-id <id> ...] [--logic-table-id-single <id>]
  [--ds-type <type>] [--view-type <type>] [--api-id <id>]

bytedcli oneservice metric guide create --payload-json <json|@file>
  [--project-id <id> | --project-name <name>] [--name <name>]
bytedcli oneservice metric script create --payload-json <json|@file>
  [--project-id <id> | --project-name <name>] [--name <name>] [--sql <sql>]
bytedcli oneservice metric table create --payload-json <json|@file>
  [--project-id <id> | --project-name <name>] [--name <name>]
  [--logic-table <name> ... | --logic-table-id <id> ...]
  [--selected-fields-json <json|@file>]

bytedcli oneservice metric version get (--version-id <id> | --api-id <id> [--version <n>])
bytedcli oneservice metric version update --version-id <id>
  [--payload-json <json|@file>] [field and Nuwa overrides]
bytedcli oneservice metric version convert --version-id <id>
  [--payload-json <json|@file>] [field and Nuwa overrides]
bytedcli oneservice metric version create
  (--source-version-id <id> | --payload-json <json|@file>) [overrides]
bytedcli oneservice metric api create
  (--source-version-id <id> | --payload-json <json|@file>) --name <newName>
  [--project-id <id> | --project-name <name>] [overrides]
```

- `guide create` / `script create` / `table create` 接受完整页面 `--payload-json`，显式 flag 覆盖 JSON 中的同名字段。最终请求必须包含非空 `name`，并且 `project_id` / `project_name` 恰好提供一个
- Guide 创建会先读取 `view-detail`，再按 os_ai 语义重建 `select_metric.list`、`originData`、`metricMap` 和缺省 `response_params`；缺少明确 selection 时在任何写入前失败
- `script create` 最终请求必须包含非空 SQL；`table create` 必须恰好提供逻辑表名称或逻辑表 ID 其中一种，并包含非空 `selected_fields`
- `object get` 至少提供一个 metric ID 或 dimension ID。`engine-grammar-type get` 至少提供一个实际 selector；`--api-id` 只提供上下文，单独使用不构成 selector
- `version update` 支持 Guide / Script / Table / Raw 参数和 metric filter rename；filter rename 会先读取当前版本再写入。`version convert` 会把 Guide 版本转换为 Raw 参数形态
- `version create` 与 `api create` 是非幂等写。后端返回名称冲突后停止并换新名称；`api create` 只在明确页面 create payload 时回退到对应 create endpoint，不猜测 multi-guide
- 所有 metric / Nuwa / view / API / version ID 在 CLI 内保留 string。只有后端硬要求的 `nuwa_config.topic_id` 和 Guide `dimensionIdList` 通过 JSONbig 输出无引号整数；禁止用 JavaScript `Number` 或原生 `JSON.stringify` 处理这些字段

```bash
bytedcli --json oneservice metric business-line list \
  --project-id 1234567890123456789
bytedcli --json oneservice metric topic list --business-id 1 --query revenue
bytedcli --json oneservice metric view list --business-id 1 \
  --topic-id 2234567890123456789
bytedcli --json oneservice metric view-detail get --view-id 3234567890123456789
bytedcli --json oneservice metric guide create --payload-json @metric-guide.json
bytedcli --json oneservice metric version get --version-id 4234567890123456789
```

---

## logic table

```
bytedcli oneservice logic search --keyword <kw> [--project-id <projectId>]
bytedcli oneservice logic get    --logic-table-id <logicTableId>
bytedcli --site cn oneservice logic query --logic-table-id <logicTableId> --sql 'SELECT ...' \
  [--logic-table-id <logicTableId2>] [--params '<json-object>'] \
  [--region CN] [--env online|ppe|boe]
bytedcli oneservice auth logic grant --logic-table-id <logicTableId> \
  --user <email-prefix> [--department <department>] [--app <three-segment-psm>] \
  [--reason <reason>]
bytedcli oneservice auth logic apply --logic-table-id <logicTableId> \
  --user <email-prefix> [--department <department>] [--app <three-segment-psm>] \
  --reason <reason> [--valid-period <days>]
bytedcli oneservice logic create --project-id <projectId>
  --logic-table-name <logicTableName>
  [--type clickhouse|doris|abase|krypton|mysql]
  --database <database>
  --table <table>
  [--cluster <cluster>]
  [--namespace <dorisNamespace>]
  [--abase-logical-table-name <name>]
  [--krypton-user <name>]
  [--krypton-secret-file <path>]
  [--folder-id <folderId>]
  [--api-control 0|1|2]
  [--is-accept-alarm-app 0|1]
  [--is-constraint 0|1]
  [--constraint <field[,field...]> ...]

bytedcli oneservice logic update --logic-table-id <logicTableId>
  ([--params <json>] | [convenience flags])
  [--allow-field-delete]
  [--confirm-token <token>]

bytedcli oneservice logic owner update
  (--logic-table-id <id> | --logic-table-ids <id,id...>) --owner <userCode> [...]
bytedcli oneservice logic editor update
  (--logic-table-id <id> | --logic-table-ids <id,id...>) --editor <userCode> [...]

bytedcli oneservice logic fabric create --project-id <projectId> --fabric-name <name>
  --source-logic-table-id <id> --source-physic-table-id <id> --fields <json>
  [--source-logic-table-name <name>] [--folder-id <id>]
bytedcli oneservice logic fabric update --logic-table-id <id> --version <version>
  --source-logic-table-id <id> --source-physic-table-id <id> --fields <json>
  [--source-logic-table-name <name>]

bytedcli oneservice logic schema compare --logic-table-id-a <id> --logic-table-id-b <id>
bytedcli oneservice logic ready-time get --logic-table-id <id> [--region <canonicalRegion>]

bytedcli oneservice logic materialize create --project-id <projectId> --name <name>
  --datasource-type clickhouse|doris|abase|bytees [--region <region>]
bytedcli oneservice logic materialize draft --logic-table-id <id> --datasource-type <type>
  ((--hive-db <db> --hive-table <table>) | --hsql <sql|@file>) [--region <region>]
bytedcli oneservice logic materialize submit --logic-table-id <id> --project-id <projectId>
  --datasource-type <type> --meta-json <json|@file> [--region <region>]
bytedcli oneservice logic materialize update --logic-table-id <id>
  --meta-json <json|@file> [--task-id <id>] [--region <region>]
bytedcli oneservice logic materialize get --logic-table-id <id>
  [--task-id <id>] [--region <region>]
bytedcli oneservice logic materialize progress --logic-table-id <id>
  [--interval <seconds>] [--timeout <seconds>]

bytedcli oneservice logic materialize region list --datasource-type <type>
bytedcli oneservice logic materialize hive-db list [--keyword <keyword>] [--region <region>]
bytedcli oneservice logic materialize hive-table list --db <db>
  [--keyword <keyword>] [--region <region>]
bytedcli oneservice logic materialize hive-schema get --tables-json <json|@file>
  [--region <region>] [--logic-table-id <id>]
bytedcli oneservice logic materialize hsql get --hive-db <db> --hive-table <table>
  [--region <region>]
bytedcli oneservice logic materialize cluster list --datasource-type <type>
  [--project-id <id>] [--region <region>]
bytedcli oneservice logic materialize cluster-info get --datasource-type <type>
  --cluster-name <name> [--region <region>]
bytedcli oneservice logic materialize target-db list --datasource-type <type>
  [--cluster-name <name>] [--region <region>]
bytedcli oneservice logic materialize queue list [--project-id <id>]
  [--dorado-project-id <id>] [--queue-app-type <n>] [--tenant-id <id>] [--region <region>]
```

- `search` 默认全局搜索；传 `--project-id` 才按项目收窄。多结果返回 `next_action.kind = MULTIPLE_RESULTS_SELECT_ONE`（成功，退出 0），**必须展示全部结果，不要自动选第一条**
- `get` 返回完整可更新元数据、Owner / Editor、绑定物理表和 `fields[]`
- `query` 直查一个或多个逻辑表。SQL 引用的每张表都必须用 `--logic-table-id` 显式列出；该参数可重复或使用逗号分隔
- `create` 的条件参数：ClickHouse / Doris / Krypton 需要 `--cluster`；Doris 需要 `--namespace`；Abase 需要 `--abase-logical-table-name`；Krypton 需要 `--krypton-user`
- Krypton 密码不会进入 argv、日志或输出：优先读取 `--krypton-secret-file`，否则 TTY masked prompt，非 TTY 从 stdin 读取；拒绝空值和大于 64 KiB 的输入
- `create` 用全局 `--site` 选择 OneService 控制面，CLI 内部按 site 推导后端 region
- `update` 可用 `--params` 传完整可编辑对象，也可使用 `--comment`、`--main-phy-table-id`、`--api-control`、`--is-constraint`、`--constraint`、`--limit`、`--private-level`、`--authorized-app-id`、`--virtual-logic-table-id`、`--join-info`、`--hide-field`、`--show-field`；两种方式不可混用
- `materialize draft` 与 `submit` 是显式两阶段。draft 只计算目标表和同步任务配置；submit 必须传完整 `--meta-json`，不会自动重跑 draft。`update` 写前先读取当前配置，成功结果包含 `before` 与后端 mutation result
- `--meta-json` 顶层必须是 object。物化 `MaterializedTable` 同时含 JSON string int64 和裸 int64，CLI 保留验证后的原始文本，不用 JavaScript `Number` 或 parse/re-stringify 处理。`--tables-json` 必须是非空数组，字段名严格使用 `dbName` / `tableName`
- 物化区域合同独立于 logic ready-time：`cn`、`i18n-tt`、`i18n-bd` 仍是 control-plane site；datasource region 按后端专属矩阵校验。`i18n-tt` 的 ClickHouse/Doris 支持 `SG/VA/EU_TTP2/GCP/TTP`。`progress` 没有 `--region`，多区域记录若后端无法唯一解析会 fail-loud
- `progress` 默认每 5 秒轮询、600 秒超时。仅 `status=SUCCESS && req_status=DONE` 成功；失败立即报错；超时返回最后快照并标 `timed_out:true`，同时进程退出非零
- `update` 第一次仅输出 diff 和 `confirm_token`；第二次带同一组参数和 token 才写入。快照漂移会令 token 失效；删除或隐藏字段还必须显式传 `--allow-field-delete`
- `--params` 可编辑键为 `id`、`name`、`project_id`、`main_phy_table_id`、`comment`、`is_constraint`、`constraint`、`limit`、`api_control`、`is_accept_alarm_app`、`private_level`、`authorized_app_id_list`、`virtual_logic_table_ids`、`join_info`（兼容 `logic_join_info`）、`fields`；`name` 不可变
- Owner / Editor 更新彻底分离：`owner update` 只替换 Owner，`editor update` 只替换 Editor；`editor update` 必须传非空 Editor 列表，不支持清空
- Fabric create/update 都提交完整单源 graph；`--fields` 是至少含 `name` / `type` 的 JSON array。update 的 `--version` 必须使用目标 Fabric 当前版本
- `schema compare` 输出 added / removed / changed 和 primary-key diff
- `ready-time get` 只接受 Invoke Common canonical region。site×region：`cn→CN`；`i18n-tt→SG/TTP/VA/US_TTP2/EU_TTP2`（默认 SG）；`i18n-bd→ASIA_SOUTHEASTBD`
- 接 OneService 这类 int64 ID 时，CLI 内部仍应把用户输入按 string 保存到最后一跳；如果后端硬要求 JSON number，只能用原始 JSON 字符串拼接数字字面量，测试也要避免 `JSON.parse` 这些字段导致精度截断

```bash
bytedcli oneservice logic search --project-id 1234567890123456789 --keyword order
bytedcli --json oneservice logic get --logic-table-id 12345
bytedcli --site cn oneservice logic query --logic-table-id 12345 \
  --sql 'SELECT * FROM sample_table LIMIT 10'
bytedcli --json oneservice auth logic grant --logic-table-id 12345 \
  --user sample-user --department "Sample Department" --app example.demo.service
bytedcli --json oneservice auth logic apply --logic-table-id <logicTableId> \
  --app example.demo.service --reason "Data consumption" --valid-period 30
bytedcli oneservice logic create --project-id 1234567890123456789 \
  --logic-table-name demo_budget_measure --type clickhouse \
  --database demo_db --table demo_budget_measure --cluster demo_cluster \
  --folder-id 1234567890123456789
bytedcli oneservice logic create --project-id 1234567890123456789 \
  --logic-table-name demo_doris_measure --type doris \
  --database demo_db --table demo_doris_measure --cluster demo_cluster \
  --namespace cn --folder-id 1234567890123456789
bytedcli --json oneservice logic update --logic-table-id 12345 --comment "reviewed"
bytedcli oneservice logic owner update --logic-table-id 12345 --owner zhangsan
bytedcli oneservice logic editor update --logic-table-id 12345 --editor lisi
bytedcli --site i18n-tt oneservice logic ready-time get --logic-table-id 12345 --region EU_TTP2
```

---

## api list

```
bytedcli oneservice api list --project-id <projectId> [--keyword <substring>]
```

- `--keyword`：在 API 名上做客户端子串匹配
- 返回字段：`id`、`name`。后端目前只填这两项，`description` / `query_type` / `folder_name` 在响应里通常为空，如果需要这些字段请改用 `api get --api-id <id>` 拿完整 `ApiInfo`

---

## search（IDE 全资源搜索）

```
bytedcli oneservice search --project-id <projectId> --keyword <keyword> [--page <n>] [--page-size <n>]
```

- `--keyword` 支持资源名称、OneService query ID（IDE 中常称 SQL ID）以及其它 IDE 关键词；只有 `--project-id` 必须是完整数字 ID
- 命令调用 IDE 的 `resource/search`，资源类型不只 API。`--page`（默认 1）和 `--page-size`（默认 20）均接受 1 到 100，由 CLI 转换为后端 cursor；JSON 输出为 `items`、`page`、`page_size`、`page_count`、`has_more`，不伪造总数。每条 item 固定包含 `id`、`name`、`type`、`sub_type`、项目字段与 `owners[]`（owner user code）
- 这是 CN IDE/BFF 能力，当前只能使用 `--site cn`；CLI 自动获取 Titan Passport 登录态，不支持传入、保存或复用浏览器 cookie

```bash
bytedcli oneservice search --project-id 1234567890123456789 --keyword "demo resource"
bytedcli --json oneservice search --project-id <projectId> --keyword <queryOrSqlId> --page 2 --page-size 20
```

可能错误：`ONESERVICE_RESOURCE_SEARCH_INPUT_ERROR` / `ONESERVICE_SITE_UNSUPPORTED` / `ONESERVICE_AUTH_EXPIRED`

---

## api create

```
bytedcli oneservice api create
  --name <name>                          # 必填，项目内唯一
  (--project-id <id> | --project-name <kw>)
  [--type script|guide|origin|workflow|http|httpscript]   # 默认 script
  [--sql <sql>]                          # script 必填，guide / origin 不允许
  [--logic-table-name <name1> [<name2> ...]]  # technical name 数组（注意：不是 ID）
  [--folder <name>]                      # 缺失时自动 ensure
  [--description <desc>]
  [--param <name:type[?]>]               # repeatable；覆盖 SQL 参数类型和必填性
  [--filter-field-json <json>]           # repeatable；追加 filter_fields object/array
  [--filter-fields-file <file>]          # JSON object/array 文件
  [--allow-extra-filter-fields]          # raw filter schema 可包含非 SQL 占位符字段
  [--return-field <name>]                # repeatable；覆盖 return_fields string
  [--return-field-json <json>]           # repeatable；追加 return_fields JSON string/array
  [--return-fields-file <file>]          # JSON string/array 文件
```

请求体组装成 `CreateApiBody`：

| 字段               | 来源                                                                                                                                                                                   | 备注                |
| ------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------- |
| `project_id`       | `--project-id`（或从 `--project-name` 解析）                                                                                                                                           | string              |
| `name`             | `--name`                                                                                                                                                                               | 项目内唯一          |
| `query_type`       | `QUERY_TYPE_TO_NUMBER[--type]`                                                                                                                                                         | 数字 1..6           |
| `sql`              | `--sql`                                                                                                                                                                                | 只 script 用        |
| `logic_table_name` | `--logic-table-name`（variadic）                                                                                                                                                       | technical name 数组 |
| `folder_name`      | `--folder`                                                                                                                                                                             | 可选                |
| `description`      | `--description`                                                                                                                                                                        | 可选                |
| `filter_fields`    | 从 SQL 中所有 `#{name}` 占位符自动提取，可被 `--param` / `--filter-field-json` / `--filter-fields-file` 覆盖                                                                           | `FilterField` 数组  |
| `return_fields`    | 从 SELECT 列表自动提取（`SELECT *` → `["*"]`），可被 `--return-field` / `--return-field-json` / `--return-fields-file` 覆盖；后端只接受 string 数组，不支持 return field object schema | `Array<string>`     |

```bash
bytedcli oneservice api create --project-id 1234567890123456789 \
  --name demo_query --type script \
  --sql "SELECT user_id FROM dwd_user WHERE dt = #{dt}" \
  --logic-table-name dwd_user

bytedcli oneservice api create --project-id 1234567890123456789 \
  --name demo_budget_measure --type script \
  --sql "SELECT dt, value FROM demo_budget WHERE dt = #{dt} AND region IN #{regions}" \
  --param 'regions:string[]?' --return-field dt --return-field value
```

`--param <name:type[?]>` 是常用 shorthand：`string` / `int` / `float` / `bool` 及其 `[]` 数组形态；末尾 `?` 表示 `isRequired=false`。例如 `--param 'budget_source_ids:int[]' --param 'regions:string[]?'`。

完整 schema 入口用于平台字段：`--filter-field-json '{"name":"regions","type":"array","items":{"type":"string"},"isRequired":false}'`、`--filter-fields-file ./filter-fields.json`、`--return-field-json '"usage"'`、`--return-fields-file ./return-fields.json`。文件只支持 JSON；filter 文件支持 object 或 array，raw filter object 中未知字段原样透传；return 文件只支持 string 或 string array。

默认所有 filter field 都必须匹配 SQL 中真实存在的 `#{name}`，raw filter schema 如需包含非占位符字段，必须显式加 `--allow-extra-filter-fields`。`--param` 始终必须匹配 SQL。filter 按 `name` 去重，return 按字段名去重；同名冲突直接抛 `ONESERVICE_SQL_PARAM_OVERRIDE_INVALID`，不会后传覆盖先传。

可能错误：`ONESERVICE_API_NAME_CONFLICT` / `ONESERVICE_PROJECT_NOT_FOUND` / `ONESERVICE_SQL_PARAM_OVERRIDE_INVALID`

---

## api update

```
bytedcli oneservice api update --api-id <apiId>
  [--name <name>]
  [--qps <number>]
  [--cache-rate-limit <rate>]
  [--owner <user1> [<user2> ...]]
```

**后端只认这 4 个字段，其它字段静默丢弃**：

| CLI flag             | 请求体路径                   | 类型                                     |
| -------------------- | ---------------------------- | ---------------------------------------- |
| `--name`             | `name`                       | string                                   |
| `--qps`              | `base_conf.qps`              | string（CLI 收数字，序列化时转成字符串） |
| `--cache-rate-limit` | `base_conf.cache_rate_limit` | string                                   |
| `--owner`            | `owner`                      | string[]                                 |

要改 SQL / logic-table，用 `api create-version` 或 `api update-version`，不要用 `api update`。

---

## api get

```
bytedcli oneservice api get --api-id <apiId> [--version <versionNumber>]
```

两种调用形态：

- **传 `--version`** — 返回该 API 指定版本的完整 `ApiInfo` 详情；JSON 输出形如 `{ api_id, version, detail }`，文本模式渲染 KV 表。
- **不传 `--version`** — 返回该 API 所有版本的元信息数组；JSON 输出形如 `{ api_id, count, versions: ApiInfo[] }`，文本模式渲染版本摘要表（`Version` / `Version ID` / `Query Type` / `Version Publish Env` / `Modifier`）。不要再假设默认是 `0`/latest——后端不带 `version` 时返回的是完整版本列表。

单版本详情常用字段：

| 字段                                          | 类型            | 说明                                                                                     |
| --------------------------------------------- | --------------- | ---------------------------------------------------------------------------------------- |
| `id` / `uid`                                  | number / string | `id` 是 number 形式（受 JSON 大整数精度影响），`uid` 是 string 形式，下游建议用 `uid`    |
| `name`                                        | string          | API 名称                                                                                 |
| `query_type`                                  | string          | 字面枚举：`"script"` / `"guide"` / `"origin"` / `"workflow"` / `"http"` / `"httpscript"` |
| `version`                                     | number          | 当前版本号                                                                               |
| `version_id`                                  | number          | 版本 ID（同样受精度影响）                                                                |
| `project_id_str`                              | string          | project ID 的 string 形式（推荐用这个）                                                  |
| `creator` / `modifier`                        | string          | 创建者 / 最后修改者 user_code                                                            |
| `engineGrammarType`                           | string          | SQL 引擎类型，如 `"mysql"`                                                               |
| `param_info.sql_text`                         | string          | API 的 SQL 文本（不是顶层 `sql`，且 origin 类型为空）                                    |
| `param_info.logic_table_ids`                  | number[]        | logic table ID 数组（嵌套在 `param_info` 内，不在 detail 顶层）                          |
| `param_info.request_param` / `response_param` | array           | 请求 / 响应字段定义                                                                      |
| `base_conf`                                   | object          | `qps` / `cache_rate_limit` / `time_out` 等                                               |
| `query_settings`                              | object          | `cache_strategy` / `cache_ttl` / `enable_page` 等                                        |
| `query_publish_env`                           | string          | API 发布环境，**逗号分隔**：`"ONLINE,PPE"` / `"BOE,PPE,ONLINE"`                          |
| `version_publish_env`                         | string          | 当前版本的发布环境（同样逗号分隔）                                                       |
| `folder_id` / `folder_name`                   | number / string | 所在文件夹                                                                               |

> `param_info.logic_table_ids` 是只读输出。创建 / 更新 API 时必须用 `--logic-table-name` 传 **name**，不能传这里的 ID。
> 已知问题：后端不返回 `ide_url`；`logic_table_ids` 数组里的元素是 number，存在 JSON 大整数精度截断问题，无法直接喂给 `logic get --logic-table-id <id>`，需要从 UI 复制完整 string ID。

---

## api query / api sql-query（直接 AGW）

```bash
bytedcli --site cn oneservice api query --api-id <apiId> \
  [--params '<json-object>'] [--region CN] [--env online|ppe|boe]

bytedcli --site cn oneservice api sql-query --api-id <apiId> --sql 'SELECT ...' \
  [--params '<json-object>'] [--region CN] [--env online|ppe|boe]
```

- `query` 调用 `/invoker_engine/query_with_params`；`sql-query` 调用 `/invoker_engine/sql_query`，且目标 API 必须是原生式（元信息 `query_type=raw`）才支持 sql-query，即 API 接受 origin / 裸 SQL。
- 支持站点：`cn`、`i18n-tt`、`i18n-bd`、`eu-ttp`、`us-ttp`。`--region` 必须属于当前 `--site`；不传时分别默认 `CN`、`SG`、`ASIA_SOUTHEASTBD`、`EU_TTP2`、`TTP`。各 `--site` 可用的 `--region`（首个为默认）：
  - `cn`：`CN` / `CHINA_EAST` / `CHINA_NORTH6`
  - `i18n-tt`：`SG` / `VA` / `MY_COMPLIANCE` / `US_COMPLIANCE`
  - `i18n-bd`：`ASIA_SOUTHEASTBD` / `ASIA_CIS`
  - `eu-ttp`：`EU_TTP2` / `GCP` / `EU_TTP` / `EU_COMPLIANCE` / `EU_COMPLIANCE2`
  - `us-ttp`：`TTP` / `US_TTP2` / `US_TTP3`
- `--env` 默认 `online`，也可选 `ppe` / `boe`；`i18n-bd` 不支持 BOE。必要时可用 `--agw-base-url <https-origin>` 在已登记的 OneService AGW 主机间覆盖 origin；未知主机 fail-closed，避免 ByteCloud JWT 发往其它服务。
- JWT 由 CLI 自动获取并仅放在请求体 `Option-200` 中。`--params` 必须是 JSON object；原始参数和返回 `Data` 中的 int64 都会作为精确字符串保留。
- 这两条命令不替代 `api test`：`api test` 仍走 OneService 控制面 `/query/test`，支持版本与 dryrun。

可能错误：`ONESERVICE_AGW_INPUT_INVALID` / `ONESERVICE_AGW_ROUTE_INVALID` / `ONESERVICE_AGW_QUERY_FAILED`

---

## logic query（直查逻辑表）

```bash
bytedcli --site cn oneservice logic query --logic-table-id <logicTableId> --sql 'SELECT ...' \
  [--logic-table-id <logicTableId2>] [--params '<json-object>'] \
  [--region CN] [--env online|ppe|boe]
```

- 调用 `POST /invoker_engine/query`，请求体为 `Tables`（逻辑表 ID 字符串数组）、`Sql` 与可选 `Params`；JWT 由 CLI 自动写入请求体 `Option-200`，不发送 `x-jwt-token`。
- `--logic-table-id` 可重复或逗号分隔。SQL 引用的每张逻辑表都必须显式列出；至少一张表、SQL 非空，且所有 ID 必须是正整数字符串，否则请求前 fail-loud。
- 命令只读，但运行时仍校验当前用户对每张逻辑表的查询权限。`Tables` 全程使用字符串，返回的 `fields` / `rows` 通过通用 AGW 解析器保留 int64 精度。
- site、region、env 与可信 `--agw-base-url` 规则和 `api query` / `api sql-query` 相同。

可能错误：`CLI_INPUT_ERROR` / `ONESERVICE_AGW_INPUT_INVALID` / `ONESERVICE_AGW_ROUTE_INVALID` / `ONESERVICE_AGW_QUERY_FAILED`

---

## api test

```
bytedcli oneservice api test --api-id <apiId>
  [--version <versionNumber>]
  [--request-data <json>]    # 测试参数 JSON 字符串；不是 --json
  [--dryrun]                 # 只渲染 SQL 不执行
```

- `--request-data` 接一个 JSON 对象，key 是 SQL 占位符名
- **origin（`type=origin`）API 必须传 `--request-data '{"Sql": "SELECT ..."}'`（大写 S）**：origin 的 SQL 是逐次调用现传，不存在 API 上
- `--dryrun` 渲染解析后的 SQL 但不执行
- `--json` 输出会保留原始 `result`，并额外输出固定结构的 `normalized_result`。字段固定为：`rendered_sql`、`dryrun_sql`、`fields`、`rows`、`data_count`、`time_cost`、`cluster_name`、`query_id`；缺失字段为 `null`。`rows` 中的 `null` 会原样保留，便于区分 0、NULL 和无行。

```bash
bytedcli oneservice api test --api-id 12345 --request-data '{"dt":"2026-04-29"}'
bytedcli oneservice api test --api-id 67890 --request-data '{"Sql":"SELECT 1"}'   # origin
```

可能错误：`ONESERVICE_API_TEST_SQL_REQUIRED` / `ONESERVICE_API_TEST_PARAMS_MISSING`

---

## api list-versions

```
bytedcli oneservice api list-versions --api-id <apiId>
```

返回 `Version[]`：`id`、`version`（数字）、`status[]`（如 `["ONLINE", "PPE"]` 或 `["not_publish"]`）、`description`、`creator`、`create_time`、`is_published`（派生：`status` 含 `ONLINE` / `PPE` / `BOE` 任意一个时为 `true`）。

---

## api create-version

```
bytedcli oneservice api create-version --api-id <apiId>
  [--source-version <versionNumber>]   # 从这个版本继承参数
  [--sql <sql>]
  [--logic-table-name <name...>]
  [--description <desc>]
  [--allow-draft]                      # 绕过草稿 guard
  [--param <name:type[?]>]
  [--filter-field-json <json>]
  [--filter-fields-file <file>]
  [--allow-extra-filter-fields]
  [--return-field <name>]
  [--return-field-json <json>]
  [--return-fields-file <file>]
```

草稿 guard：CLI 默认会先调 `listVersions`，如果已经有未发布草稿就直接拒绝，抛 `ONESERVICE_API_VERSION_DRAFT_EXISTS`。`--allow-draft` 必须在用户明确确认后才能加。详见 `api-version-flow.md`。

SQL field override flags 的含义与 `api create` 相同，用于覆盖由 SQL 自动生成的 `filter_fields` / `return_fields`。`filter_fields` 可用完整 object schema；`return_fields` 只能传字段名 string。

---

## api update-version

```
bytedcli oneservice api update-version
  --api-id <apiId>           # is_published 自检需要
  --version-id <versionId>
  [--sql <sql>]
  [--logic-table-name <name...>]
  [--description <desc>]
  [--param <name:type[?]>]
  [--filter-field-json <json>]
  [--filter-fields-file <file>]
  [--allow-extra-filter-fields]
  [--return-field <name>]
  [--return-field-json <json>]
  [--return-fields-file <file>]
```

`--api-id` 是必填，因为 handler 会通过 `listVersions` 做 `is_published` 自检。如果目标版本已发布，CLI 抛 `ONESERVICE_API_VERSION_PUBLISHED` —— 恢复路径是用同样的 flag 调 `api create-version`。

SQL field override flags 的含义与 `api create` 相同，用于覆盖由 SQL 自动生成的 `filter_fields` / `return_fields`。`filter_fields` 可用完整 object schema；`return_fields` 只能传字段名 string。

---

## api copy-version

```
bytedcli oneservice api copy-version --api-id <apiId> [--source-version <versionNumber>]
```

一条用户视角的命令，内部由 `services/oneservice/orchestration.ts` 串起 4 步后端调用：

1. `listVersions` —— 解析源版本（不传 `--source-version` 时取最新）
2. `getApi` —— 读源版本的 SQL 和 `logic_table_ids`
3. `getLogic` × N —— 把每个 logic-table ID 反查回 technical name
4. `createVersion` —— 写一条新草稿，沿用同样的 SQL / 参数

用户只需跑这一条命令，**不要**手动串这 4 步。

---

## api publish / api unpublish

发布与下线拆成两个独立子命令；不再通过 `--status 0|1` 切换语义。

```
bytedcli oneservice api publish   --api-id <apiId>
  --env ONLINE [PPE BOE ...]   # variadic，至少传一个
  [--version <versionNumber>]  # 默认最新
  [--version-id <versionId>]   # 仅 multi-region；与 --version 互斥
  [--publish-region <region>]  # repeatable / comma-separated；启用两阶段 multi-region
  [--confirm-token <token>]

bytedcli oneservice api unpublish --api-id <apiId>
  --env ONLINE [PPE BOE ...]   # 要下线的环境
  [--version <versionNumber>]  # 默认最新
  [--version-id <versionId>]
  [--publish-region <region>]
  [--confirm-token <token>]
```

```bash
bytedcli oneservice api publish   --api-id 12345 --env ONLINE
bytedcli oneservice api unpublish --api-id 12345 --env BOE
bytedcli oneservice api publish   --api-id 12345 --env ONLINE PPE --version 3
bytedcli oneservice api publish   --api-id 12345 --env ONLINE \
  --version-id 1234567890123456789 --publish-region CN
```

不带 `--publish-region` 时严格走原有 `/query_version/publish` 单区域路径。显式传 region 时第一次调用只返回 preview 和 `confirm_token`，不发写请求；确认后用完全相同的参数加 `--confirm-token`，CLI 才调用 multi-region publish 并逐区域 readback。confirm token 只在客户端校验，不进入后端 body。

---

## api version-params / promote

```bash
bytedcli oneservice api version-params get --version-id <versionId>
bytedcli oneservice api version-params get --api-id <apiId> [--version <version>]
bytedcli oneservice api version-params update --version-id <versionId> \
  [--mutation-json <jsonOrAtFile>] [--sql <sql>] [--description <description>] [--allow-draft]
bytedcli oneservice api version-params set --version-id <versionId> \
  --target request|response --path <path> [--type <type>] [--upsert]
bytedcli oneservice api promote --api-id <apiId> (--version <version> | --version-id <versionId>) \
  --env <ONLINE|PPE|BOE...> --publish-region <region> [--confirm-token <token>]
bytedcli oneservice api promote-online --api-id <apiId> \
  (--version <version> | --version-id <versionId>) --publish-region <region> [--confirm-token <token>]
```

- `version-params update` 通过 `--mutation-json` 接受完整 JSON，或使用便捷 flags；顶层白名单为 `description/sql/logic_table_name/query_settings/nuwa_config/request_params/response_params/base_conf`。`--json` 始终只控制全局结构化输出
- 所有读取、权限、状态、草稿、指标版本与确认校验都在任何写之前完成。ONLINE 参数更新创建新版本；PPE/BOE 参数更新成功后恢复原发布环境
- `set` 先读取完整模型，再对单个参数 patch，然后只回写所选的完整 `request_params` 或 `response_params` 列表；选择 request 时，后端会把空或纯空白元数据物化为 `field=name`、`operator="="`、`type="string"`。这是良性矫正，空 `field` 本就不可执行。response path 不支持嵌套 struct
- `promote` 必须显式选择环境；`promote-online` 默认 ONLINE。两者都是两阶段操作，部分成功时读取 `completed_steps` 和 `recovery_hint`，先 readback 再恢复

---

## api multi-region / test records / ready-time

```bash
bytedcli oneservice api multi-region-versions list --api-id <apiId> [--query-region <region>]
bytedcli oneservice api test-record list --api-id <apiId> [--page <n>] [--page-size <n>]
bytedcli oneservice api test-record get --record-id <recordId>
bytedcli oneservice api ready-time get --api-id <apiId> --query-region <region> \
  [--env ONLINE|PPE] [--with-partition --partition-field <field> --partition-value <value>]
```

- `test-record list` 只返回摘要，不默认逐条补详情；JSON 分页字段为顶层 `page/page_size/current_count`，后端不提供总数；`--call-type` 使用 `http|rpc` 语义值，CLI 会映射为后端枚举；记录 ID、API ID 和版本 ID 全程按 string 保真
- ready-time 的控制面矩阵：`cn→CN`；`i18n-tt→SG/TTP/VA/US_TTP2/EU_TTP2/GCP`；`i18n-bd→ASIA_SOUTHEASTBD`。这里只接受 canonical region，不应用 publish 的 `EU_TTP`/`EUTTP` 别名；请传 `EU_TTP2`

---

## auth api grant

```
bytedcli oneservice auth api grant
  --api-id <apiId>
  [--app <psm>]               # repeatable / comma-separated
  [--user <user>]             # repeatable / comma-separated
  [--department <department>] # repeatable / comma-separated
  [--qps <number>]            # 只对 PSM 生效
  [--invoke-owner <user>]
  [--auth-desc <description>]
```

`--app` / `--user` / `--department` 至少传一类，也可一次混合授予。`--app` 接三段式 PSM 标识，但 CLI 输入与输出统一使用应用术语；后端 wire 仍是 `psm`。`--user` 接 user code 或邮箱前缀；`--qps` 只作用于应用，个人和部门沿用平台策略。调用者必须拥有该 API 的 `APP_AUTH` 权限。

后端按主体返回 `results[]`。CLI 会计算 `success_count` / `failed_count`：全部成功返回 `success`；部分成功返回 `partial_success` 并设置非 0 退出码；全部失败报错。成功项对应的 `verification_commands` 使用 `auth api access get` 校验，不要用 `auth api list` 验证个人或部门授权。

---

## auth api apply

```
bytedcli oneservice auth api apply
  --api-id <apiId>
  --reason <reason>
  [--app <psm>]
  [--user <user>]
  [--department <department>]
  [--qps <number>]
  [--valid-period <days>]      # -1 表示永久
  [--invoke-owner <user>]
```

`--app` / `--user` / `--department` 至少传一类。命令为当前调用者创建审批单，响应中的 `order_id` 和 `api_id` 均按 int64-string 保留。等待当前审批节点处理；只有后续 `auth api access get` 确认后才能把授权视为生效。

---

## auth api access get

```
bytedcli oneservice auth api access get
  --api-id <apiId>
  [--user <user>]              # 单个用户；缺省为 JWT 当前用户
  [--app <psm>]
  [--department <department>]
```

`--user` 一次只接受一个用户。部门不会从用户身份自动推导；验证部门授权时必须显式传 `--department`。响应里的 `api_id` / `auth_id` 按 int64-string 保留。

---

## auth api access list

```
bytedcli oneservice auth api access list
  [--user <user>]              # 单个用户；缺省为 JWT 当前用户
  [--app <psm>]
  [--department <department>]
  [--project-id <projectId>]
  [--page <number>]
  [--page-size <number>]
```

`--user` 一次只接受一个用户。部门不会从用户身份自动推导；查询部门授权时必须显式传 `--department`。请求分页字段为 `page_size`，响应分页字段为 `pageSize`，CLI 输出统一为 `page_size`。响应里的 `api_id` / `auth_id` 按 int64-string 保留。

---

## auth api list

```
bytedcli oneservice auth api list --api-id <apiId>
```

返回应用授权 `AuthEntry[]`：`auth_id`、`app`、`qps_limit`、`invoke_owner`、`create_time`。该接口不返回个人或部门授权；这两类必须用 `auth api access get/list`。

---

## auth app create

```
bytedcli oneservice auth app create --app <psm>
```

注册一个新应用（三段式 PSM 标识），后续可以用 `auth api grant` 给它授权。即使应用已注册过，后端也会返回友好的「已存在」消息，CLI 视为成功，直接进入 `auth api grant` 即可。

## auth logic grant

```bash
bytedcli oneservice auth logic grant --logic-table-id <logicTableId> \
  [--user <emailPrefix>] [--department <name>] [--app <psm>] \
  [--reason <reason>]
```

三类主体至少传一类，均可重复或逗号分隔。后端逐主体返回 `results[]`；部分成功时 CLI 返回 `partial_success` 且非 0 退出。

---

## auth logic apply

```bash
bytedcli oneservice auth logic apply --logic-table-id <logicTableId> \
  [--user <emailPrefix>] [--department <name>] [--app <three-segment-psm>] \
  --reason <reason> [--valid-period <days>]
```

三类主体至少传一类，均可重复或逗号分隔。`--reason` 必须非空；`--valid-period` 范围为 1 到 365，省略时后端默认 365。命令调用 `POST /openapi-ai/v1/logic/auth/subjects/apply`，不要求申请人拥有逻辑表修改权限。返回的 `order_id` / `logic_table_id` 按 int64-string 保留，并提供 `order_detail_url`。创建工单不等于已经授权，必须等待审批完成；已授权或已有待审批工单的主体会令整批申请被拒绝，不产生部分成功。

---

## logic table 使用注意

- `--logic-table-name <name1> [<name2> ...]` 接一个或多个 **technical name**（即 `oneservice logic search` / `get` 返回的 `name` 字段），不接 ID。CLI 内部把它们组装成请求体里的 `logic_table_name: string[]`。Flag 名特意带 `-name` 后缀，与 `logic get --logic-table-id` 区分，避免歧义
- `param_info.logic_table_ids` 是 `api get` 返回的**只读**字段（嵌套在 `param_info` 内，不在 detail 顶层）。**不要**把这里的 ID 反过来再喂给 create / update —— 先用 `logic get --logic-table-id <id>` 翻成 name 再传
- `services/oneservice/orchestration.ts` 在 `copy-version` 内部已经自动做了 ID → name 的反查
