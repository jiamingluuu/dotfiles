# ByteDoc

ByteDoc 数据库搜索、列表、详情、关注、集合查看、允许的文档读写、安全 Mongo shell 风格命令、慢查询分析与经典版索引治理统一收敛在 `bytedoc <action>`。

业务代码 review、提交前检查或 MR diff 中出现 ByteDoc/Mongo 用法时，加载 ByteDoc skill 根目录下的 `code-review/GUIDE.md`。保留宿主通用 review，发现业务查询后确认库和集合并请求只读查库授权，结合真实线上索引、可用 schema 和版本补充 ByteDoc 专项 findings。

在字节内部，用户泛称 `mongo`、`MongoDB`、Mongo 库、集合、文档、慢查询、索引、连接、SDK 或权限时，默认按 ByteDoc 处理；只有用户明确说 DMS、DMS 控制台、DMS `db-id` 或非 ByteDoc 的 MySQL/Redis/DMS 统一查询时，才切到其它数据库 skill。

旧的 `bytedoc db <action>` 兼容入口仍可使用；新示例和新脚本优先使用 flat 命令。

## 常见命令

```bash
# 搜索数据库（用于确认 backend/vregion 是否唯一）
bytedcli --site cn bytedoc search --keyword "demo_orders"
bytedcli --site cn bytedoc search --keyword "bytedoc.demo_catalog" --backend cloud-native
bytedcli --site cn bytedoc search --keyword "bytedoc.demo_catalog" --backend volc
bytedcli --site i18n-tt bytedoc search --keyword "demo_orders"

# 查看我关注的库 / 数据库详情
bytedcli --json --site cn bytedoc list
bytedcli --json --site boe --vregion China-BOE bytedoc list --backend volc
bytedcli --json --site cn bytedoc list --all --deploy-mode cloud-native
bytedcli --json --site cn bytedoc get --db-name "demo_orders"
bytedcli --json --site cn bytedoc get --service "example.bytedoc.demo_orders"
bytedcli --json --site cn --vregion China-North bytedoc get --service "demo_orders" --backend classic

# 数据库访问授权角色 / 权限检查（跟随全局 --site / --vregion）
bytedcli --json --site cn --vregion China-North bytedoc access role list --service "example.bytedoc.demo_orders" --backend classic
bytedcli --json --site cn --vregion China-North bytedoc access permission get --db-name "demo_orders" --backend classic --role-name "bytedoc.data_reader.cn"
bytedcli --site i18n-tt --json --vregion VA bytedoc access role list --db-name "demo_orders" --backend classic

# PSM/User 接入授权工单（classic；只示例 dry-run；用户确认后按 CLI 协议内部提交）
bytedcli --json --site cn --vregion China-North bytedoc access psm list --db-name "demo_orders" --backend classic --account "example.caller.psm"
bytedcli --json --site cn --vregion China-North bytedoc access ticket create --db-name "demo_orders" --backend classic --account "example.caller.psm"
bytedcli --json --site cn --vregion China-North bytedoc access ticket create --db-name "demo_orders" --backend classic --account "example.caller.psm" --reviewers "alice" --roles "read" --reason "Need read access for service integration"

# PSM 授权管理：classic 走 ByteDoc ticket，Volc / 多云走经校验的 BPM workflow
bytedcli --site boe --json --vregion China-BOE bytedoc access psm list --service "example.bytedoc.demo_volc" --backend volc
bytedcli --site boe --json --vregion China-BOE bytedoc access psm list --service "example.bytedoc.demo_volc" --backend volc --account "example.caller.psm"
bytedcli --json --site cn --vregion China-North bytedoc access psm create --db-name "demo_orders" --backend classic --operation apply --account "example.biz.psm" --reviewers "alice" --roles "read" --reason "Need PSM read authorization"
bytedcli --json --site cn --vregion China-North bytedoc access psm create --db-name "demo_orders" --backend classic --operation modify --account "example.biz.psm" --reviewers "alice" --roles "readWrite" --reason "Update PSM authorization"
bytedcli --json --site cn --vregion China-North bytedoc access psm create --db-name "demo_orders" --backend classic --operation delete --account "example.biz.psm" --reviewers "alice" --roles "read" --reason "Remove PSM authorization"
bytedcli --site boe --json --vregion China-BOE bytedoc access psm create --service "example.bytedoc.demo_volc" --backend volc --operation apply --account "example.biz.psm" --roles "readWrite" --reason "Need confirmed Volc PSM authorization"

# IAM 用户权限管理：授权、改期、回收、自助申请（classic / Volc）
bytedcli --json --site cn --vregion China-North bytedoc access user grant --db-name "demo_orders" --backend classic --role-name "bytedoc.viewer.cn" --principal "demo.user" --principal-type user --duration 30d --reason "Need temporary view access"
bytedcli --json --site cn --vregion China-North bytedoc access user update --db-name "demo_orders" --backend classic --role-name "bytedoc.viewer.cn" --principal "demo.user" --duration 7d --reason "Shorten authorization"
bytedcli --json --site cn --vregion China-North bytedoc access user revoke --db-name "demo_orders" --backend classic --role-name "bytedoc.viewer.cn" --principal "demo.user" --reason "Access no longer needed"
bytedcli --json --site cn --vregion China-North bytedoc access user apply --db-name "demo_orders" --backend classic --role-name "bytedoc.viewer.cn" --duration 180d --reason "Need self-service view access"

# 集合与慢查询（使用已确认 backend/vregion）
bytedcli --json --site cn --vregion China-North bytedoc collections --service "demo_orders" --backend classic
bytedcli --json --site cn --vregion China-North bytedoc collections --db-name demo_catalog --backend cloud-native
bytedcli --json --site boe --vregion China-BOE bytedoc collections --service "example.bytedoc.demo_volc" --backend volc
bytedcli --json --site cn --vregion China-North bytedoc collection create --service "example.bytedoc.demo_catalog" --backend cloud-native --collection "demo_items"
bytedcli --json --site cn --vregion China-North bytedoc slow-query overview --service "demo_orders" --backend classic --millis 100
bytedcli --json --site cn --vregion China-North bytedoc slow-query overview --service "demo_volc" --backend volc --component "mongo-shard-demo-s0-0" --millis 100
bytedcli --json --site cn --vregion China-North bytedoc slow-query overview --service "demo_volc" --backend volc --fetch-all --limit 500 --millis 100
bytedcli --json --site cn --vregion China-North bytedoc slow-query metrics --service "demo_catalog" --backend cloud-native --interval 5m
# 原子能力：用户直接要求索引推荐 dry-run 时可执行；从慢查结果主动推进治理时，先询问用户是否进入索引治理阶段
bytedcli --json --site cn --vregion China-North bytedoc slow-query index-recommend --service "example.bytedoc.demo_orders" --backend classic --apply-index-dry-run

# 经典版索引治理（创建索引默认 dry-run；用户确认后才追加 --execute --yes-i-know-this-is-live）
bytedcli --json --site cn --vregion China-North bytedoc index list --service "example.bytedoc.demo_orders" --backend classic --db-name "demo_orders" --collection "demo_items"
bytedcli --json --site cn --vregion China-North bytedoc index task list --service "example.bytedoc.demo_orders" --backend classic --db-name "demo_orders" --operation create --status doing --collection "demo_items"
bytedcli --json --site cn --vregion China-North bytedoc index task get --service "example.bytedoc.demo_orders" --backend classic --db-name "demo_orders" --ticket-id 24680
bytedcli --json --site cn --vregion China-North bytedoc index create --service "example.bytedoc.demo_orders" --backend classic --db-name "demo_orders" --collection "demo_items" --keys-json '{"tenant":1,"createdAt":-1}' --name "tenant_1_createdAt_-1"

# Mongo shell 风格命令（site/backend/vregion 必须确认）
bytedcli --json --site cn --vregion China-North bytedoc shell --service "demo_orders" --backend classic --collection "demo_records" --query 'find().limit(10)'
bytedcli --json --site cn --vregion China-North bytedoc shell --service "demo_orders" --backend classic --collection "demo_records" --query-file ./query.mongo
bytedcli --json --site cn --vregion China-North bytedoc shell --db-name demo_catalog --backend cloud-native --collection "demo_items" --query 'find().limit(10)'
bytedcli --json --site boe --vregion China-BOE bytedoc shell --service "example.bytedoc.demo_catalog" --backend volc --collection "demo_items" --query 'find().limit(10)'
bytedcli --json --site boe --vregion China-BOE bytedoc shell --service "example.bytedoc.demo_catalog" --backend volc --query 'db.getCollectionNames()'

# 文档操作（classic / cloud-native / Volc Mongo；insert/update 默认返回 dry-run 确认预览）
bytedcli --json --site cn --vregion China-North bytedoc document list --service "example.bytedoc.demo_catalog" --backend cloud-native --collection "demo_items" --filter-json '{"tenant":"demo"}' --limit 10
bytedcli --json --site cn --vregion China-North bytedoc document insert --service "example.bytedoc.demo_catalog" --backend cloud-native --collection "demo_items" --doc-json '{"tenant":"demo","value":1}'
bytedcli --json --site cn --vregion China-North bytedoc document update --service "example.bytedoc.demo_catalog" --backend cloud-native --collection "demo_items" --filter-json '{"tenant":"demo"}' --update-json '{"$set":{"value":2}}'
```

## 说明

### 后端分类

- `backend=classic`：传统 ByteDoc；Mongo 查询、允许的集合操作和文档操作走 DMS subscribe / evaluate，搜索、列表、关注、详情、慢查询走 classic ByteDoc API。
- `backend=cloud-native`：cloud-native ByteDoc；Mongo 查询、允许的集合操作和文档操作走 DMS subscribe / evaluate，搜索走 legacy cloud-native 平台搜索，慢查询走 cloud-native slowquery API。
- `backend=volc`：DBW / Volc Mongo，Cloud Service Search 原始 `mode=volc`；实例信息来自 `instance_id`、`instance_type`、`region`、`vregion`，集合、查询和允许的文档/集合写操作走 DBW Mongo 执行链路。
- 例外：`site=us-ttp|eu-ttp` 的 classic / cloud-native ByteDoc 当前不支持 DMS 数据查询。`bytedoc collections`、`bytedoc shell`、`bytedoc collection create`、`bytedoc document <list|insert|update>` 会返回 `BYTEDOC_UNSUPPORTED_SITE`；搜索、详情、关注、IAM 等控制面能力不受影响。收到该错误后停止，不要猜 dc、改 DMS endpoint、切 backend 或 vregion。
- 区域限制：`i18n-bd / Asia-SouthEastBD` 的 classic/cloud-native DMS 数据面当前不支持，需要实际执行 DMS 的数据操作在 DMS 请求前返回 `BYTEDOC_UNSUPPORTED_SITE`。`collections` 仍走控制面；dry-run 可能先返回预览，不代表 DMS 可用。显式、配置或默认区域及既有别名均按 `agent_protocol.next_state=STOP` 停止并报告，不要重试、猜 dc、改 endpoint 或切 backend/vregion。搜索、详情、IAM、Volc/DBW 与 `Asia-CIS` / `US-EastBD` 不受该限制。
- `mode` 是部分搜索来源返回的原始字段；`backend` 是 CLI 对外的严格三态选择器；`deployMode` 是 legacy 平台路由字段，仅有 `classic|cloud-native` 两态。

### 命令链路

- ByteDoc 允许不同 backend 或不同 vregion 下存在同名数据库；除搜索/list 这类发现命令外，目标操作前必须明确 `backend` 和 `vregion`，但这个确认应优先由 CLI resolver 完成，不应先让用户猜 backend。
- `backend` 和 `vregion` 没有默认值：只能由用户明确提供，或由搜索/resolver 证明唯一。`bytedoc get --db-name` / `bytedoc get --service` 是详情/基本信息请求的 resolver-backed 首选路径；任一维度多值、或单条候选包含多个 vregion 时，Agent 才必须展示候选让用户选择。
- `bytedoc search --backend classic|cloud-native` 使用对应 legacy 平台搜索；显式 `--backend volc` 使用当前站点的 Cloud Service Search / DBW 搜索；未指定 backend 时会合并 legacy classic、legacy cloud-native 与当前站点支持的 Volc 搜索结果。显式 `--backend volc` 且未指定全局 `--vregion` 时，CLI 会扩展到该站点已知的 Volc 候选 vregion，避免非默认区域漏查；`--deploy-mode` 仅作为 legacy 两态兼容过滤项。
- `bytedoc search` 是候选发现，不是详情查询。JSON 中 `sourceTotal` 是上游声称的命中数，`usableCandidateCount` 是 CLI 当前返回的可执行候选数；`sourceTotal>0` 但 `usableCandidateCount=0` 时，不要切换 backend/vregion 或把裸 dbName 改写成 PSM，详情意图应改走同 site 的 `bytedoc get --db-name`。
- 海外控制面（例如 `--site i18n-tt`）如果没有 Volc Cloud Service 搜索来源，仍会保留 classic / cloud-native 平台搜索结果；此时 `--backend volc` 不返回结果。
- `bytedoc list` 默认展示关注列表；未显式传筛选项时会合并 classic、cloud-native，以及当前站点支持 Cloud Service 时的 Volc 关注列表。只看 Volc 关注项时使用 `--backend volc`。
- Volc 关注列表来自 Cloud Service subscriptions 全量拉取后的本地过滤分页；JSON 会带 `paginationMode: "client-side"` 与 `filteredTotal`，不要把它当作服务端分页 total 判断是否还有下一页。
- `bytedoc list --all` 展示 legacy 平台全量数据库；支持 classic / cloud-native，不支持把 Volc 搜索结果伪装成全量 inventory。不要把 list 的兼容行为当成后续目标操作的 backend 默认值。
- `bytedoc follow` 支持 classic / cloud-native / Volc，Volc 走 Cloud Service 关注链路；后续目标操作仍要保留已确认的 `backend=volc` 和 `vregion`。
- `bytedoc slow-query overview --backend volc` 走 ByteDoc Cloud `DescribeSlowLogs` 读取 DBW / Multi Cloud Mongo 慢日志概览；未指定 `--component` 时会从 `GetVolcInfo` 展开 ConfigServers、Mongos、Shards 组件逐个查询，用户要对齐控制台“组件”下拉时传 `--component <component>`。默认 `--limit` 是 100，不要把默认前 100 条当作全量；需要扩大返回量用 `--limit <n>`，需要全量分析用 `--fetch-all`。Volc 的日志、备份、参数等仍属于 DBW / Volc 详情面，不等同于 classic/cloud-native slow-query 平台全量能力。
- `bytedoc get` 可以传 `--db-name` 或 `--service`；classic / cloud-native 返回平台详情，Volc Mongo 只在解析到 DBW 元信息时返回 Cloud Service / DBW summary，且不返回 classic usage。
- `bytedoc collections` 不需要 `--deploy-mode`；后续命令应显式携带已确认的 `--backend classic|cloud-native|volc` 和全局 `--vregion`。`backend=volc` 时走 DBW `ListTables`，不是 classic IAM 权限接口。
- `bytedoc shell` 不需要 `--deploy-mode`；后续命令应显式携带已确认的 `--backend classic|cloud-native|volc` 和全局 `--vregion`；`--deploy-mode` 只能区分 legacy `classic|cloud-native` 两态。
- `bytedoc collection create` 与 `bytedoc document <list|insert|update>` 面向 classic / cloud-native / Volc Mongo；classic / cloud-native 使用 DMS，Volc 使用 DBW。`collection create`、`document insert/update` 与写入型 `shell` 是真实写入与变更；CLI 默认返回 dry-run 确认预览，不执行写入。Agent 必须展示 `data.result.confirmation.reviewTable` 和 `data.result.confirmation.warning`，warning 必须包含：`注意：写入与变更相关功能仅建议在测试库使用。Agent 幻觉可能导致误操作，若用于生产环境，风险由用户自行承担。` 如果 Agent 先基于只读查询自行生成业务预览并询问用户，确认问题里也必须完整展示同一句注意提示。用户明确确认后，Agent 才可追加 `--execute --yes-i-understand-agent-write-risk` 重新执行。
- 所有站点下，`bytedoc collection drop/rename`、`bytedoc document delete`、以及 `bytedoc shell/query` 中的 `drop`、`renameCollection`、`deleteOne`、`deleteMany`、`remove`、`findOneAndDelete`、drop index 和 `bulkWrite` 删除都会被本地拒绝，不会请求 DMS 或 DBW；BOE 也不是例外。收到 `BYTEDOC_UNSAFE_OPERATION_BLOCKED` 后，不得改用 BOE、DBW、DMS direct helper、query-file 或脚本绕过。classic DMS shell 中的 `createIndex/createIndexes/ensureIndex` 会返回 `BYTEDOC_INDEX_CREATION_REQUIRES_BPM`，必须改走 `bytedoc index create` dry-run / BPM 工单链路，不得用 query-file、DMS direct helper 或脚本绕过。Volc/火山版 建索引不走 classic BPM 工单，按 DBW mongoshell 路径运行 `bytedoc shell --backend volc --query 'db.<collection>.createIndex(...)'`，默认返回写入确认预览，用户确认后才追加 `--execute --yes-i-understand-agent-write-risk`。
- `bytedoc document list` 是结构化文档查询入口；`bytedoc document find` / `query` 仍可作为兼容别名使用。
- `bytedoc access role list` 会读取 IAM resource info 和角色绑定，输出可供 Agent 展示给用户选择的角色列表；支持 `--db-name`、`--service`、`--backend` 消歧。classic 通过 ByteDoc static_info 解析 IAM node；Volc 通过搜索结果里的 `byteTreeId/source-tree-id` 进入 ByteCloud IAM ACL。
- `bytedoc access permission get` 会校验当前操作者是否具备发起授权流程的前置权限。classic / Volc IAM 用户角色授权均可使用；`--role-name`、`--role-names`、`--env` 不能证明 caller PSM 已授权，也不能用于证明 Volc PSM/token 授权。
- `bytedoc access ticket create` 会读取已验证的 classic `apply_account` 表单 schema，JSON 输出在 `data.result` 下包含审批人和账号权限可选项、payload preview、`confirmation.requiredReview`、`confirmation.reviewTable`、`nextActions` 与 `agentProtocol`；默认 dry-run，不提交工单。Volc PSM/token 授权使用 `access psm create`，Volc IAM 用户/角色授权使用 `access user apply` dry-run，不要用 PSM 工单替代。
- `bytedoc access psm list` 用于主动查询 PSM/token 当前授权状态，并给出 `psm create` dry-run 的下一步动作。需先通过 search/resolver 确认目标 `--db-name <db>` 或 `--service <target.psm>` 唯一，并携带已确认的 `--backend <confirmed-backend>`；传 `--account <caller.psm>` 后读取 `data.result.kind=psm_authorization_inspection`、`accountCheck.status`、`accountCheck.authorized`（若返回）与 `accountCheck.roles`。先完成以下任一命令，再根据结果决定是否进入 `ticket create` / `psm create` dry-run：
  - `bytedoc access psm list --db-name <db> --backend <confirmed-backend> --account <caller.psm>`
  - `bytedoc access psm list --service <target.psm> --backend <confirmed-backend> --account <caller.psm>`
    PSM/token 当前授权真源按 backend 区分：classic 使用 ByteDoc `get_db_accounts`，`inspection.source=classic_get_db_accounts`；cloud-native 使用 `get_account`，`inspection.source=cloud_native_get_account`；Volc / DBW 使用 ByteDoc multi-cloud `GetAccount`，`inspection.source=bytedoc_multicloud_get_account`。不要用 ByteCloud IAM ACL node、`role-bindings/list-by-resource`、`permission get` 或 BPM ticket 历史判定 caller PSM 当前权限。
- 如果当前授权真源接口未确认或读取失败，权限列表 / 巡检命令必须返回结构化 `inspection.status=unknown`、明确 `inspection.source` / `inspection.reason` 和下一步动作；不得用 BPM 历史工单、Mongo 内部表或其他非实时来源伪装当前权限。
- `bytedoc access psm create --operation apply|modify|delete` 用于 PSM 授权新增、更新和删除；classic 使用 ByteDoc ticket `apply_account` / `modify_account` / `delete_account`，Volc / 多云按站点选择并校验 ByteDoc `multi_clound_grant` BPM workflow，payload 内 `operation=1|2|3`、`auth_type=3`。如果 workflow 校验失败，CLI 会在生成可提交 dry-run 预览或创建真实工单前停止。
- `bytedoc access user grant` 给指定 principal 授权，`update` 修改有效期，`revoke` 回收权限，`apply` 给当前登录用户申请 IAM role。classic / Volc IAM 用户角色授权都走 ByteCloud IAM ACL；如果 Volc 资源缺失 `byteTreeId/source-tree-id`，CLI 会返回终止性错误，且不得恢复为 `access psm create`。
- `bytedoc access user <grant|update|apply> --duration` 支持纯秒数、`h/H` 小时和 `d/D` 天，例如 `10800`、`3h`、`180d`；不支持 `m/M`，分钟级请换算成秒，按月有效期请换算成固定天数。
- Agent 必须先按 `data.result.nextActions` 把 dry-run 的可选项展示给用户并让用户选择，再用 `data.result.confirmation.reviewTable` 渲染表格给用户做最终确认，不能把字段挤成单行；用户确认页不要暴露隐藏执行材料。用户明确同意后，Agent 才可按 CLI 协议进入内部提交路径。
- `ticket create` 当前固定使用 ByteDoc 控制台已验证的 `user_type=PSM / User` 与 `mesh_method=Token + Mesh`；账号权限来自 schema 选项，例如 `read`、`readWrite`、`readWriteNoDrop`、`dbOwner`。
- 如果 `bytedoc shell`、`bytedoc collections`、`bytedoc document *` 返回 `BYTEDOC_ACCESS_REQUIRED`，Agent 应读取 `error.details.setup_commands` 并继续执行推荐的查询 / dry-run 命令，不需要让用户重新发现授权命令；Volc 场景的 setup commands 会先查询 `bytedoc access psm list`，再准备 `psm create` dry-run。
- IAM 用户角色授权与权限管理按三步走：先 `role list` 展示可选项，再 `permission get` 检查前置权限，最后运行目标写命令 dry-run 展示完整 IAM 字段；classic 和 Volc 都可使用这条链路。Volc PSM/token 授权必须走 `access psm list/create --backend volc`，不要用 PSM 工单替代 Volc IAM 用户/角色授权。只有用户确认 `data.result.confirmation.reviewTable` 后，Agent 才可按 CLI 协议进入内部提交路径。
- `bytedoc access` 后续命令必须保留当前全局 `--site` / `--vregion` 路由参数；用户确认页不要展示隐藏执行材料或底层 live 命令。
- `bytedoc slow-query overview` 支持 classic / cloud-native / Volc；Volc overview 返回 `source=bytedoc_cloud_describe_slow_logs`、`logs[]`、`pods{}`、`fetched_count`、`backend_total`、`truncated`、`exhaustive` 等慢日志信息，并支持 `--component <component>` 只查指定组件。`total` 仅保留为 `fetched_count` 的兼容别名；判断上游总量用 `backend_total`。Volc 默认只返回前 100 条；需要更多样本用 `--limit <n>`，需要全量时用 `--fetch-all` 并检查 `incomplete_ranges`。`detail` / `scope` 是 classic / cloud-native slow-query 平台能力；Volc 没有等价的 fingerprint detail 或 scope 列表，CLI 会返回结构化 unsupported。`subscribers` / `metrics` 仅支持 cloud-native；`index-recommend` 支持 classic / cloud-native，Volc 会返回 `BYTEDOC_UNSUPPORTED_BACKEND`。`index-recommend --apply-index-dry-run` 仅支持经典版，只生成 `indexCreateDryRuns[]` 里的 `bytedoc index create` dry-run 命令，不提交 BPM；cloud-native 推荐不要加该 flag。执行前必须确认 backend/vregion，多值时让用户选择。用户直接要求该原子能力时可执行；若 Agent 从慢查证据主动推进建索引治理，先按 `playbooks/GUIDE.md` 询问用户是否进入索引治理阶段，用户确认前不要运行 `bytedoc index create` dry-run。若返回 `result.status=no_data` 且 `agent_protocol.next_state=STOP`，说明当前窗口没有可用慢查询数据，Agent 应报告空结果或询问是否换时间窗，不要原命令重试。若 overview 成功且有慢查询数据，Agent 先摘要证据，不要只返回慢日志列表；用户有治理/优化意图或要求文档时，按 `slow-query/governance.md` 生成治理文档或治理结论。
- `bytedoc index list/task list/task get/create` 当前只覆盖经典版索引治理。`index create` 默认 dry-run，dry-run 会读取 BPM workflow config 校验 workflow 正确性，因此需要 BPM 读权限；如果这里返回 403，先处理 BPM 登录/权限/路由问题，不要进入 live。dry-run 输出 workflowConfigId、region、payload、confirmation 和 nextActions；用户明确确认后才允许运行带 `--execute --yes-i-know-this-is-live` 的命令。双确认 flag 是防误提交和防 workflow 误路由的安全边界，不要简化成单 `--execute`；也不要直接调用 index_manager 的 BPM 回调 API。Volc/火山版 建索引不使用该命令组，走 DBW `bytedoc shell --backend volc`。
- `bytedoc slow-query detail` 在 classic 下既支持直接传 24 位 ObjectId，也支持传 `overview` 里的 fingerprint id；CLI 会自动尝试把 fingerprint 展开成 `_ids` 再查询 detail。
- `bytedoc shell` 的输入是 Mongo shell 风格 `--query` / `--query-file`；未以 `db.` 开头的查询需要 `--collection`，会自动改写成 `db.<collection>.<query>` 后再发给 DMS 或 DBW。以 `db.` 开头的库级只读命令（如 `db.getCollectionNames()`）不需要 `--collection`，但它走 ExecuteSQL 权限，不是 `collections` 主链路的等价替代。
- classic / cloud-native 不再走 legacy `web_query` 文本归一化链路；`bytedoc query` 和旧的 `bytedoc db query` 仍可作为 `shell` 别名使用。
- 复杂 aggregate / distinct / index 命令优先使用 `--query-file`。

## 选择器与权限枚举

- 定位阶段必须确认 `site`，并通过搜索/resolver 确认 `backend` 和 `vregion` 是否唯一；只有唯一候选才能进入后续目标操作。详见 `selection-guards.md`。
- 授权和写入阶段仍必须按对应 GUIDE 执行 role 枚举、access dry-run/review 或 Mongo dry-run 确认预览；不要把“只需确认 site”理解成可以跳过授权和写入确认。Mongo `document insert/update` 和 `shell updateOne` 首次命令只应返回 dry-run 确认预览，用户确认后才追加执行 flag。
- PSM 授权 role 固定选项：`read`、`readWrite`、`readWriteNoDrop`、`dbOwner`、`dbOwnerNoDrop`、`enableShardingOnly`。
- IAM role-name 常用选项按 site 的 IAM region 选择：`site=cn` / `site=boe` 使用 `bytedoc.data_reader.cn`、`bytedoc.data_writer.cn`、`bytedoc.viewer.cn`、`bytedoc.operator.cn`、`bytedoc.owner.cn`、`owner`；`site=i18n-bd` / `site=i18n-tt` 使用 `bytedoc.data_reader.i18n`、`bytedoc.data_writer.i18n`、`bytedoc.viewer.i18n`、`bytedoc.operator.i18n`、`bytedoc.owner.i18n`、`owner`；`site=us-ttp` 以 `access role list` 返回的真实 role 为准，当前已验证默认可选 role 是 `owner.tx`；`site=eu-ttp` 以 `access role list` 返回的真实 role 为准，当前已验证默认可选 role 是 `owner`。不要把 `.cn` role 用到 i18n 站点，否则可能触发 `role region and iam region not match`；US-TTP 不要猜 `.cn` / `.i18n` / `.tx` role；不要根据默认枚举或请求参数合成/猜测 role。
- `US-BOE` 是 `site=boe` 下的区域，不是 site 值。
