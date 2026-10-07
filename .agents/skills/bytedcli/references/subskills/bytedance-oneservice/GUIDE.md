---
name: bytedance-oneservice
description: |
  Manage OneService (OS) via bytedcli by module — API: list/create/update/get/test/publish, test records, ready-time, version parameters, promotion, multi-region lifecycle; metric: Nuwa discovery, guide/script/table creation, version update/raw conversion/save-as; logic table: search/get/query/create/two-phase update, owner/editor, Fabric, Hive materialization, schema compare, ready-time; physical table: metadata/fields, field update, ready-time, owner/editor; datasource: list/search, regions/property enums, secret-redacted config; lineage: upstream/downstream asset lineage; search: global resource search; project: list API-creatable projects, search by name, permission get, webhook update; folder: list/create; auth: unified API and logic-table grants/applications for application, user, and department subjects, plus application registration. Use when user mentions OneService, OS.
---

# bytedcli OneService

> Detailed command parameters: `references/oneservice.md`
> Invocation guide: `../../invocation.md`
> Error code reference: `references/errors.md`
> API type rules (script/guide/origin/...): `references/api-types.md`
> Version semantics (is_published / draft / copy): `references/api-version-flow.md`

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

- 搜索 OneService IDE 的资源名称、query/SQL ID 或其它关键词
- API 的列表 / 创建 / 更新 / 获取 / 测试 / 发布
- API 版本的列表 / 创建 / 更新 / 拷贝（4 步链）/ 参数模型 / 晋级 / 多区域发布
- API 测试记录与 Ready Time 的只读查询
- Nuwa 元数据发现、Guide/Script/Table 指标 API 创建、指标版本更新/转 raw 与另存
- API 服务的 PSM / 个人 / 部门授权、审批申请、权限校验、PSM 授权列表和 PSM 应用注册
- 项目的列表 / 搜索 / 创建权限检查 / webhook 更新
- 文件夹的列表 / 创建（`api create` 可自动 ensure）
- 逻辑表搜索 / 详情 / 创建 / 两阶段更新
- 逻辑表 Owner / Editor、Fabric、Hive 物化、Schema 对比和 Ready Time
- 物理表详情、字段两阶段更新、Owner / Editor 和多区域 Ready Time
- 数据源的列表 / 搜索、区域元信息、属性枚举与强制脱敏的连接配置
- 数据源、物理表、逻辑表、API 和应用之间的上下游血缘查询

## 前置条件

- 使用通用调用方式：`../../invocation.md`

> 执行前缀见 `../../invocation.md`；下面示例直接写 `bytedcli`。

## Quick start

命令分 10 组（按模块顺序）：`oneservice api` / `oneservice metric` / `oneservice logic` / `oneservice physical` / `oneservice datasource` / `oneservice lineage` / `oneservice search` / `oneservice project` / `oneservice folder` / `oneservice auth`。

```bash
# api — CRUD、直接 AGW 查询与版本生命周期
bytedcli oneservice api list   --project-id <pid> [--keyword <kw>]
bytedcli oneservice api get    --api-id <id> [--version <n>]
bytedcli oneservice api create --project-id <pid> --name "demo_query" --type script \
  --sql "SELECT user_id FROM dwd_user WHERE dt = #{dt}" --logic-table-name dwd_user
bytedcli oneservice api create --project-id <pid> --name "demo_optional" --type script \
  --sql "SELECT dt, value FROM t WHERE dt = #{dt} AND region IN #{regions}" \
  --param 'regions:string[]?' --return-field dt --return-field value
bytedcli oneservice api update --api-id <id> --name <name>           # 仅认 name/qps/cache-rate-limit/owner
bytedcli oneservice api test   --api-id <id> --request-data '{"dt":"2026-04-29"}' --dryrun
bytedcli --site cn oneservice api query --api-id <id> [--params '<json>'] [--region CN] [--env online]
bytedcli --site cn oneservice api sql-query --api-id <id> --sql 'SELECT ...' [--params '<json>'] [--region CN] [--env online]
bytedcli oneservice api list-versions  --api-id <id>
bytedcli oneservice api create-version --api-id <id> --sql "..." [--allow-draft] [--param <name:type[?]>]
bytedcli oneservice api update-version --api-id <id> --version-id <vid> --sql "..." [--param <name:type[?]>]
bytedcli oneservice api copy-version   --api-id <id>                 # 4 步链：list→get→logic detail×N→create
bytedcli oneservice api publish        --api-id <id> --env ONLINE
bytedcli oneservice api unpublish      --api-id <id> --env BOE
bytedcli oneservice api version-params get --version-id <vid>
bytedcli oneservice api version-params update --version-id <vid> --description "reviewed"
bytedcli oneservice api version-params set --version-id <vid> --target request --path user_id --type string
bytedcli oneservice api promote --api-id <id> --version-id <vid> --env PPE --publish-region CN
bytedcli oneservice api promote-online --api-id <id> --version-id <vid> --publish-region CN
bytedcli oneservice api multi-region-versions list --api-id <id>
bytedcli oneservice api test-record list --api-id <id>
bytedcli oneservice api test-record get --record-id <record-id>
bytedcli oneservice api ready-time get --api-id <id> --query-region CN

# metric — Nuwa 发现、指标 API 创建与指标版本生命周期
bytedcli oneservice metric business-line list --project-id <pid> [--business-id <business-id>]
bytedcli oneservice metric topic list --business-id <business-id> [--query <keyword>]
bytedcli oneservice metric view list --business-id <business-id> --topic-id <topic-id>
bytedcli oneservice metric view-detail get --view-id <view-id>
bytedcli oneservice metric operator list
bytedcli oneservice metric object get --metric-id <id> [--dimension-id <id>]
bytedcli oneservice metric engine-grammar-type get --logic-table-id <logic-id>
bytedcli oneservice metric guide create --payload-json @metric-guide.json
bytedcli oneservice metric script create --payload-json @metric-script.json --sql 'SELECT ...'
bytedcli oneservice metric table create --payload-json @metric-table.json
bytedcli oneservice metric version get --version-id <version-id>
bytedcli oneservice metric version update --version-id <version-id> --payload-json @metric-update.json
bytedcli oneservice metric version convert --version-id <version-id> --payload-json @raw-selection.json
bytedcli oneservice metric version create --source-version-id <version-id>
bytedcli oneservice metric api create --source-version-id <version-id> --name <new-name>

# logic table
bytedcli oneservice logic search --keyword dwd_user [--project-id <pid>]
bytedcli oneservice logic get    --logic-table-id <id>
bytedcli --site cn oneservice logic query --logic-table-id <id> --sql 'SELECT * FROM sample_table LIMIT 10'
bytedcli oneservice logic create --project-id <pid> --logic-table-name dwd_user \
  --type clickhouse --database demo_db --table dwd_user --cluster demo_cluster
bytedcli oneservice logic create --project-id <pid> --logic-table-name dwd_user_doris \
  --type doris --database demo_db --table dwd_user_doris --cluster demo_cluster \
  --namespace cn
bytedcli oneservice logic update --logic-table-id <id> --comment "reviewed" # 先预览
bytedcli oneservice logic update --logic-table-id <id> --comment "reviewed" \
  --confirm-token <preview-token>
bytedcli oneservice logic owner update  --logic-table-id <id> --owner zhangsan
bytedcli oneservice logic editor update --logic-table-id <id> --editor lisi
bytedcli oneservice auth logic grant --logic-table-id <id> \
  --user sample-user --department "Sample Department" --app example.demo.service \
  --reason "Cross-project API integration"
bytedcli oneservice auth logic apply --logic-table-id <id> \
  --user sample-user --reason "Data consumption" --valid-period 30
bytedcli oneservice logic schema compare --logic-table-id-a <id-a> --logic-table-id-b <id-b>
bytedcli oneservice logic ready-time get --logic-table-id <id> [--region SG]
bytedcli oneservice logic materialize region list --datasource-type clickhouse
bytedcli oneservice logic materialize draft --logic-table-id <id> \
  --datasource-type clickhouse --hive-db sample_db --hive-table sample_table
bytedcli oneservice logic materialize submit --logic-table-id <id> --project-id <pid> \
  --datasource-type clickhouse --meta-json @materialization.json
bytedcli oneservice logic materialize progress --logic-table-id <id>

# datasource (read-only)
bytedcli oneservice datasource list --project-id <pid> [--keyword <kw>] [--ds-region CN]
bytedcli oneservice datasource search --project-id <pid> [--keyword <kw>] [--ds-region CN]
bytedcli oneservice datasource property list [--name source|type|region]
bytedcli oneservice datasource region list --datasource-id <id>
bytedcli oneservice datasource config get --datasource-id <id> --ds-region CN

# lineage (read-only, no login required)
bytedcli --site cn oneservice lineage get \
  --asset-type logical_table --asset-id <id> [--last-call-period last_90d] [--online-only]

# physical table
bytedcli oneservice physical get --physical-table-id <id>
bytedcli oneservice physical field update --physical-table-id <id> \
  --logic-table-id <logic-id> --fields '[{"name":"id","comment":"reviewed"}]'
bytedcli oneservice physical ready-time get --physical-table-id <id> [--region SG]
bytedcli oneservice physical ready-time-option list --physical-table-id <id>
bytedcli oneservice physical ready-time update --physical-table-id <id> --config '<json>'
bytedcli oneservice physical owner update --physical-table-id <id> \
  [--owner zhangsan] [--editor lisi]

# search — 全局搜 OneService 全部资源类型（API/逻辑表/物理表/数据源等）
bytedcli oneservice search     --project-id <pid> --keyword <name-or-sql-id> [--page <n>] [--page-size <n>]

# project
bytedcli oneservice project list [--keyword <kw>]
bytedcli oneservice project search [--keyword <kw>]
bytedcli oneservice project permission get --project-id <pid>
bytedcli oneservice project webhook update --project-id <pid> \
  --webhook-url https://example.com/oneservice-hook --event publish_success

# folder（项目内）
bytedcli oneservice folder list   --project-id <pid>
bytedcli oneservice folder create --project-id <pid> --name <folder>

# auth（应用 / 个人 / 部门授权）
bytedcli oneservice auth api grant  --api-id <id> --user zhangsan
bytedcli oneservice auth api grant  --api-id <id> --app my.service.psm \
  --department example.department
bytedcli oneservice auth api apply  --api-id <id> --user zhangsan \
  --reason "Need access for validation"
bytedcli oneservice auth api access get --api-id <id> --user zhangsan
bytedcli oneservice auth api access list --project-id <pid> --user zhangsan
bytedcli oneservice auth api list   --api-id <id>
bytedcli oneservice auth logic grant --logic-table-id <id> --app my.service.psm
bytedcli oneservice auth logic apply --logic-table-id <id> --app my.service.psm \
  --reason "Data consumption"
bytedcli oneservice auth app create --app my.service.psm
```

## Command surface

| Group        | Verbs                                                                                                                                                                                                                                                                                              | 说明                                                          |
| ------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------- |
| `api`        | `list`, `create`, `update`, `get`, `test`, `query`, `sql-query`, `list-versions`, `create-version`, `update-version`, `copy-version`, `version-params get/update/set`, `publish`, `unpublish`, `promote`, `promote-online`, `multi-region-versions list`, `test-record list/get`, `ready-time get` | API CRUD、直接 AGW 查询、测试记录、Ready Time 与版本生命周期  |
| `metric`     | `business-line list`, `topic list`, `view list`, `view-detail get`, `operator list`, `object get`, `engine-grammar-type get`, `guide/script/table create`, `version get/update/convert/create`, `api create`                                                                                       | Nuwa 发现、指标 API 创建与指标版本生命周期                    |
| `logic`      | `search`, `get`, `query`, `create`, `update`, `owner update`, `editor update`, `fabric create/update`, `materialize create/draft/submit/update/get/progress`, `materialize region/hive-db/hive-table/hive-schema/hsql/cluster/cluster-info/target-db/queue`, `schema compare`, `ready-time get`    | 逻辑表直查与生命周期、Fabric、Hive 物化、Schema 和 Ready Time |
| `physical`   | `get`, `field update`, `ready-time get`, `ready-time-option list`, `ready-time update`, `owner update`                                                                                                                                                                                             | 物理表字段、权限主体和多区域 Ready Time                       |
| `datasource` | `list`, `search`, `property list`, `region list`, `config get`                                                                                                                                                                                                                                     | 数据源只读元信息与强制脱敏配置                                |
| `lineage`    | `get`                                                                                                                                                                                                                                                                                              | 资产上下游血缘树查询                                          |
| `search`     | `search`                                                                                                                                                                                                                                                                                           | IDE 返回的混合资源搜索，支持名称、query/SQL ID 与其它关键词   |
| `project`    | `list`, `search`, `permission get`, `webhook update`                                                                                                                                                                                                                                               | 项目发现、创建权限检查与 webhook 配置                         |
| `folder`     | `list`, `create`                                                                                                                                                                                                                                                                                   | 项目内的文件夹管理                                            |
| `auth`       | `api grant/apply/access get/access list/list`, `logic grant/apply`, `app create`                                                                                                                                                                                                                   | API、逻辑表和应用的统一授权入口                               |

## Notes

- CRUD、版本、`api test` 与搜索等控制面命令仅支持 `cn` / `i18n-tt` / `i18n-bd`。直接 AGW 命令 `api query` / `api sql-query` / `logic query` 独立支持 `cn` / `i18n-tt` / `i18n-bd` / `eu-ttp` / `us-ttp`，并用本地 `--region` 与 `--env online|ppe|boe` 选路；region 缺省值由 `--site` 决定，`i18n-bd` 不支持 BOE
- 需要结构化输出加 `--json`（全局选项，放在子命令之前，如 `bytedcli --json oneservice api list ...`）
- `search` 用 `--keyword` 搜索 OneService IDE 返回的全部资源类别；名称、query/SQL ID 与其它关键词都可直接传入。`--project-id` 是 IDE/BFF 必需的项目上下文，必须是数字。命令按 `--page` / `--page-size` 从后端 cursor 读取对应页，二者均接受 1 到 100（默认分别为 1 和 20）。JSON 返回 `items`、`page`、`page_size`、`page_count`、`has_more`，不会伪造总数。每条 item 固定包含 `id`、`name`、`type`、`sub_type`、项目字段和 `owners[]`。该能力走 IDE/BFF `resource/search`，目前只支持 `--site cn`，CLI 会自动换取 Titan Passport，不接收或保存浏览器 cookie
- 遇到 `fetch failed` / 请求超时（常见于 SG/跨区链路偶发抖动）时，可用全局 `--http-timeout-ms <ms>` 临时加大单次请求超时（默认 20000），并配合 `--http-retry-count <n>` 增加重试次数。示例：`bytedcli --http-timeout-ms 60000 --site i18n-tt oneservice api test --api-id <id> --version <version>`
- `api create` 的 `--type` 必须用字面枚举 `script|guide|origin|workflow|http|httpscript`，旧的数字 `--query-type` 仅内部使用
- `api create` 支持 `--project-name` 代替 `--project-id`，内部走 `listProjects` 解析；找不到时抛 `ONESERVICE_PROJECT_NOT_FOUND`。同时 `--folder <name>` 会自动 ensure：先调 `listFolders`，缺失则 `createFolder`，再下发创建
- `api create --type script` 在 SQL 含 `#{name}` 占位符时会自动填充 `filter_fields`，默认 `type=string,isRequired=true`，并按 SELECT 列推断 `return_fields`；可用 `--param <name:type[?]>` 覆盖 SQL 参数类型和必填性，例如 `--param 'regions:string[]?'` / `--param 'budget_source_ids:int[]'`
- `filter_fields` 支持完整 schema 覆盖：`--filter-field-json` / `--filter-fields-file`；JSON object/array 中未知字段会原样透传。`return_fields` 后端只接受 string 数组，支持 `--return-field` 和 JSON string/array，不支持 return field object schema。默认 filter 字段必须匹配 SQL `#{name}`，只有 raw filter schema 可用 `--allow-extra-filter-fields` 显式放行非占位符字段
- `api test --json` 会保留原始 `result`，并额外输出固定结构的 `normalized_result`：`rendered_sql`、`dryrun_sql`、`fields`、`rows`、`data_count`、`time_cost`、`cluster_name`、`query_id`；缺失字段为 `null`，`rows` 内部的 `null` 会原样保留，便于排查“后端返回 0 / 无数据 / 查询没命中”
- `api query` 直接调用 AGW `/invoker_engine/query_with_params`；`api sql-query` 调用 `/invoker_engine/sql_query`，仅适用于支持 origin/裸 SQL 的 API。二者用 ByteCloud JWT 写入请求体 `Option-200`，不发送 `x-jwt-token`，并无损保留 `--params` 与返回 `Data` 中的 int64
- `logic query` 直查逻辑表：传一个或多个 `--logic-table-id` 和 `--sql`，调用 AGW `/invoker_engine/query`。该命令只读，但仍要求当前用户拥有每张逻辑表的查询权限；表 ID 与结果中的 int64 全程保真
- `api create` / `api create-version` / `api update-version` 的 `--param` 只接受 SQL 中实际出现的 `#{name}`；raw filter schema 默认也必须匹配 SQL，占位符缺失、同名冲突、JSON 非法或字段 schema 非法会抛 `ONESERVICE_SQL_PARAM_OVERRIDE_INVALID`
- `--type origin` 不存 SQL，调用方在 `api test` 时通过 `--request-data '{"Sql":"SELECT ..."}'`（大写 S）传入；origin API 不支持 SQL field override flags
- `api update` 后端只认 4 个字段：`--name` / `--qps`（字符串）/ `--cache-rate-limit` / `--owner`，其它字段静默丢弃
- `api create-version` 是非幂等调用，收到含 `version_id` 的响应即视为成功，不要重试。handler 默认带草稿 guard，命中 `not_publish` 版本时抛 `ONESERVICE_API_VERSION_DRAFT_EXISTS`；用户明确确认后用 `--allow-draft` 跳过
- `api update-version` 必须同时传 `--version-id` 和 `--api-id`，handler 据此自动 `is_published` 自检；命中已发布版本抛 `ONESERVICE_API_VERSION_PUBLISHED`，恢复路径是用相同 flags 调 `api create-version`，**不要**先 `api unpublish` 下线再改
- `api copy-version` 是 4 步链编排（`list-versions → get → logic detail × N → create-version`），用户只需一条命令即可把已有版本完整克隆为新草稿
- `api version-params update/set` 先完成全部读取、状态和指标版本校验，再写入完整参数模型。`set` 只对所选的完整 `request_params` 或 `response_params` 列表做 read-modify-write；选择 request 时，后端会把空或纯空白元数据物化为 `field=name`、`operator="="`、`type="string"`。这是良性矫正，空 `field` 本就不可执行。输入 JSON 只接受 `description/sql/logic_table_name/query_settings/nuwa_config/request_params/response_params/base_conf`；19 位 ID 保持 string，只有后端要求 i64 的嵌套字段才序列化成裸 JSON number
- `api publish/unpublish` 不带 `--publish-region` 时保持 legacy 单区域行为；带 `--publish-region` 时进入两阶段多区域流程，第一次只返回 `confirm_token` 且不写，第二次必须回传同一 token。`--version` 与 `--version-id` 互斥
- `api promote/promote-online` 复用同一两阶段确认；任一步写失败会返回 `completed_steps`、`partial_success` 和恢复提示，必须先 readback 再补未完成步骤，禁止整链盲重放
- `api test-record list` 默认只列记录摘要，不做逐条详情 N+1；需要详情时用返回的 ID 调 `api test-record get`
- `logic materialize` 是 Hive 到 ClickHouse/Doris/Abase/ByteES 的一站式物化流程。`draft` 只生成配置、不持久化；`submit` 必须显式传回完整 `--meta-json`。`update` 写前读取当前状态并返回 `before` 与写结果。业务 ID 保持十进制 string；`meta` 内混合 string/raw int64，因此 CLI 验证顶层对象后保留原始 JSON 文本，不做 parse/re-stringify
- 物化控制面 site 仅 `cn/i18n-tt/i18n-bd`。物化 region 使用 datasource 专属矩阵，不复用 logic ready-time；`i18n-tt` 的 ClickHouse/Doris 后端矩阵包含 `GCP`。`progress` 不接受 `--region`，因为当前后端进度接口没有 region 维度
- `api ready-time get` 的 site×region 为 `cn→CN`、`i18n-tt→SG/TTP/VA/US_TTP2/EU_TTP2/GCP`、`i18n-bd→ASIA_SOUTHEASTBD`。分区查询必须同时传 `--with-partition --partition-field --partition-value`
- `project search` 只按项目名检索，省略 `--keyword` 时返回当前站点和租户范围内的后端结果；不承诺包含无权限项目。`project permission get` 精确检查当前 JWT 用户的 API 创建权限
- `project webhook update` 是完整替换写入，必须同时提供至少一个 HTTPS webhook URL 和 event；没有通用 readback/恢复契约时，不对共享项目自动执行该命令
- `api create` 名称冲突（`ONESERVICE_API_NAME_CONFLICT` / 后端 1219）时停止重试，向用户索取新 `--name`，不要自动加后缀
- `auth api grant` 可同时传 `--app` / `--user` / `--department`，至少传一类。应用值是三段式 PSM，但 CLI 输入和输出统一称 app；后端 wire 仍使用 `psm`。响应按主体返回 `results[]`；只要有一个失败即为 `partial_success` 并非 0 退出，全部失败则报错。读取 `verification_commands`，用 `auth api access get` 逐类验证成功项；`auth api list` 只能列应用，不能验证个人或部门授权
- `auth api apply` 为当前调用者创建审批单并返回 int64-string `order_id`。等待当前审批节点处理，只有 `auth api access get` 确认后才能宣称授权已生效
- `auth api access get --api-id <id>` 查询指定 API 的有效权限；`auth api access list` 按主体和项目分页列出已授权 API。`--user` 一次只接一个用户，部门不会从用户身份自动推导，需显式传 `--department`
- `auth api grant` 命中 `ONESERVICE_AUTH_PSM_NOT_REGISTERED`（后端 `code=-1` + `"no app found"`）时，应用尚未注册。agent **必须先和用户确认**，确认后按 `error.details.recoveryCommands` 串 `auth app create --app <psm>` + 重试 `auth api grant`，**不要**静默自动注册
- `logic search` 命中多结果时返回 `next_action.kind = MULTIPLE_RESULTS_SELECT_ONE`，应将全部结果展示给用户由其选择，禁止自动选第一条
- `logic search` 默认全局搜索；只有需要项目内收窄时才传 `--project-id`
- `auth logic grant` 至少传 `--user` / `--department` / `--app` 之一，三者均可重复或逗号分隔。应用使用三段式 PSM 标识。后端逐主体返回 `results[]`；部分成功时 CLI 返回 `partial_success` 且非 0 退出，全部失败时报错。顶层成功不能替代逐条检查 `success` / `err_msg`
- `auth logic apply` 为当前调用者申请逻辑表调用权限，不要求逻辑表修改权限；必须传非空 `--reason` 和至少一类主体。`--valid-period` 范围 1 到 365，省略时后端默认 365。成功仅表示创建审批单，需通过 `order_detail_url` 等待审批，禁止直接宣称已授权；已授权或已有待审批工单的主体会令整批申请被拒绝
- `logic create --type` 支持 `clickhouse|doris|abase|krypton|mysql`。Krypton 密码只从 `--krypton-secret-file`、TTY masked prompt 或非 TTY stdin 读取，禁止放入命令行 flag
- `logic update` 是两阶段写入：第一次只返回 diff 和 `confirm_token`；第二次必须带同一组变更和 token。字段删除或隐藏还需 `--allow-field-delete`
- Owner 和 Editor 是两条独立写路径；`owner update` 不改 Editor，`editor update` 不改 Owner。`editor update` 必须传至少一个 `--editor`，不支持清空 Editor
- `logic ready-time get` 使用 Invoke Common canonical region；合法 site×region 为 `cn→CN`、`i18n-tt→SG/TTP/VA/US_TTP2/EU_TTP2`、`i18n-bd→ASIA_SOUTHEASTBD`
- `physical field update` 是强制两阶段写入：第一次返回完整 active 字段 target、diff 和 `confirm_token`，第二次带相同 patch、逻辑表 ID 和 token 才写；不支持删除字段
- `physical ready-time update` 也是两阶段完整配置替换。后端跨区域写入非事务；若返回 `region_errors`，必须读取各区域实际状态后再确认恢复，禁止盲重试
- `physical ready-time get` 聚合当前配置、区域 ready time、Dorado 任务和项目 ready-time functions；未指定 region 时只查配置中已有区域
- `physical owner update` 的 `--owner` / `--editor` 至少传一类，也可同时传；空列表表示不修改，不支持清空
- `datasource list` 返回跨区域去重的数据源列表（每个数据源一行）；`datasource search` 返回当前或 `--ds-region` 指定的单一区域视图。两者都要求 `--project-id`，并支持 `--page`（页码，从 1 起）与 `--page-size`（每页 1 到 100）
- `datasource config get` 永久强制脱敏 credential-like 字段，JSON、文本与 MCP 均不会返回明文，也没有解除脱敏的 flag。`--site` 选择控制面，`--ds-region` 选择数据源配置区域
- `lineage get` 查询 `data_source|physical_table|logical_table|api|app` 的上下游树，只接受全局 `--site cn|i18n-tt|i18n-bd`，不接收 `--region`，也不要求 `bytedcli auth login`。文本模式忠实展示树；`--json` 返回结构化 `entry/projects/upstream/downstream`。资产 ID 全程按 string 保真
- 接 OneService 这类 int64 ID 时，CLI 内部仍应把用户输入按 string 保存到最后一跳；如果后端硬要求 JSON number，只能用原始 JSON 字符串拼接数字字面量，测试也要避免 `JSON.parse` 这些字段导致精度截断
- 指标 API 必须使用 `metric` 命令组。先用 business-line→topic→view→view-detail 明确选择 Nuwa 对象；禁止替用户猜业务线、topic、view、metric 或 dimension
- `metric guide create` 在任何写前补齐 view detail、校验显式 selection，并从 `table_structure` 重建 guide 派生配置和缺省 response params。普通 metric `extra` 是 opaque 字符串；只有 guide 富化会按 os_ai 语义 parse/merge/compact
- metric 的 business/view/object/API/version 等 ID 全程按 string 保存；仅后端硬要求的 `nuwa_config.topic_id` 与 guide `dimensionIdList` 通过 JSONbig 输出无引号裸整数，禁止 `Number()` 或原生 `JSON.parse/stringify` 处理这些字段
- `metric version create` / `api create` 是非幂等写；后端返回名称冲突后必须停下并向用户索取新名称。`api create` 仅在明确的页面 create payload 下回退到对应 create endpoint，不猜 multi-guide

## Error reference

| Code                                     | Trigger                                                                                                                                                                                 | Recovery                                                                                                                                                                |
| ---------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `ONESERVICE_AUTH_EXPIRED`                | Token expired                                                                                                                                                                           | `bytedcli auth login` for the active site                                                                                                                               |
| `ONESERVICE_RESOURCE_SEARCH_INPUT_ERROR` | `search` 的 `--project-id` 不是数字、`--keyword` 为空，或分页参数不在 1 到 100                                                                                                          | 传数字 project ID、非空关键词和 1 到 100 的分页参数后重试                                                                                                               |
| `ONESERVICE_API_NAME_CONFLICT`           | API name already exists                                                                                                                                                                 | Ask user for a new `--name`; no auto-retry                                                                                                                              |
| `ONESERVICE_API_VERSION_DRAFT_EXISTS`    | `create-version` while draft exists                                                                                                                                                     | `update-version` the existing draft, or pass `--allow-draft` after explicit user confirmation                                                                           |
| `ONESERVICE_API_VERSION_PUBLISHED`       | `update-version` on published version                                                                                                                                                   | Call `create-version` instead; do not publish-offline first                                                                                                             |
| `ONESERVICE_API_TEST_SQL_REQUIRED`       | `api test` on origin API without SQL                                                                                                                                                    | Pass `--request-data '{"Sql":"SELECT ..."}'`                                                                                                                            |
| `ONESERVICE_API_TEST_PARAMS_MISSING`     | `api test` missing required params (backend listed them in `missing_params`)                                                                                                            | Read `error.details.missingParams`, fill in `--request-data`, retry                                                                                                     |
| `ONESERVICE_API_BUILD_FAILED`            | `create-version` / `update-version` build/validation failure (logic table unresolved, invalid SQL, malformed filter_fields). Backend's real reason is in `error.message` / `error.hint` | Read `error.message` and `error.details.backendMessage`; for `logic table not found` run `oneservice logic search` to verify the table; for SQL issues fix in IDE first |
| `ONESERVICE_SQL_PARAM_OVERRIDE_INVALID`  | SQL field override flags are invalid: malformed `--param`, invalid JSON/file schema, duplicate field names, or filter fields not present in SQL `#{name}` placeholders                  | Fix `--param` / filter schema / return schema inputs; use `--allow-extra-filter-fields` only for intentional raw filter fields that are not SQL placeholders            |
| `ONESERVICE_AUTH_PSM_NOT_REGISTERED`     | `auth api grant` for an application not yet in OneService App table                                                                                                                     | Confirm with user, then run `auth app create --app <psm>`, then retry `auth api grant`                                                                                  |
| `ONESERVICE_PERMISSION_DENIED`           | No project_admin / query_develop permission                                                                                                                                             | Ask user to apply for the missing permission                                                                                                                            |

Full table: `references/errors.md`.

## References

- `references/oneservice.md` — full command parameters and request body fields
- `../../invocation.md` — bytedcli invocation patterns and global flags
- `references/api-types.md` — script / guide / origin / workflow / http / httpscript rules
- `references/api-version-flow.md` — version lifecycle, copy semantics, draft guard
- `references/errors.md` — full error code list with examples
