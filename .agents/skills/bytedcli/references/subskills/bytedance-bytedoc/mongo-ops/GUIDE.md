# ByteDoc Mongo 操作指南

当任务涉及集合查看、安全 Mongo shell 风格查询，以及 classic、cloud-native、Volc Mongo 的结构化文档操作时，使用本指南。

## 首屏规则

- classic / cloud-native Mongo 操作走 DMS。
- Volc Mongo 操作走 DBW。
- 读取和写入前都必须确认 `site`，并按 `../references/selection-guards.md` 解析目标数据库的 `backend` 和 `vregion`。
- 如果 site + backend + vregion + service 已由用户完整提供，`collections`、`document list`、`shell` 等 Mongo 目标命令都是 resolver-backed，可以直接执行目标命令并保留全部 selector；不要为了重复确认而单独执行 `bytedoc search`。
- 自动化或 traced wrapper 场景中，wrapper 只是替换 `bytedcli` 二进制；固定模板是 `<bytedcli-or-wrapper> --json --site <site> [--vregion <vregion>] bytedoc <subcommand> ...`，全局参数必须放在 `bytedoc` 前。
- 如果命令会被 wrapper 记录到 trace，只把真实 Mongo 业务命令交给 wrapper；不要通过 wrapper 执行 `--help`。
- `backend` 和 `vregion` 没有默认值：只能由用户明确提供，或由搜索/resolver 证明唯一；任一维度多值时必须让用户选择。
- `BYTEDOC_AMBIGUOUS` / `agent_protocol.next_state=ASK_USER` 是硬边界：展示候选表，不要自行选择后继续。
- 不要用 `--deploy-mode` 解决 Volc 歧义；`deployMode` 无法表示 Volc。
- `backend=volc` 的集合查看和 Mongo 查询走 DBW。Volc/火山版 建索引也走 DBW mongoshell：确认 service/vregion/collection/keys/options 后，先运行不带 `--execute` 的 `bytedoc shell --backend volc --query 'db.<collection>.createIndex(...)'` 获取写入确认预览；展示 `confirmation.warning` 和 `confirmation.reviewTable`，用户明确确认后才追加 `--execute --yes-i-understand-agent-write-risk`。`collections` 失败时不要改用 classic IAM `access role list`；只有返回 `BYTEDOC_ACCESS_REQUIRED` 或 setup_commands 时才进入授权流程。
- 普通 `document insert` 不自动执行 `document list` 查重；只有用户明确要求先查重、避免重复、不存在才插入、或确保某条记录存在，并且提供 stable key / 业务 id / 唯一 filter 时，才进入显式查重流程。collection 未知时仍先用 `collections` 做前置检查。
- `bytedoc shell` 支持库级 `db.*` 只读命令；例如 `db.getCollectionNames()` 不需要 `--collection`，但它走 ExecuteSQL 权限，不能替代 `collections` 主链路。未以 `db.` 开头的查询才需要 `--collection`。
- 设置 `BYTEDCLI_NETWORK_PROFILE=prod` 时，只允许可通过严格语法白名单证明为只读的 ByteDoc Mongo 命令，例如结构化 `document list`，以及参数只含静态 BSON/JSON 值的 `find` / `findOne` / `count` / `distinct` / 只读 `aggregate` shell。带 `$out` / `$merge` 的聚合、结构化写入、其他写入型 shell、未知或动态表达式 shell、多语句 shell（包括 dry-run）都会返回 `BYTEDOC_PROD_NETWORK_READ_ONLY`；收到后停止，不要取消 profile、切换域名、改走 DMS/DBW 或换命令形态绕过。
- 默认只做只读探查；`collection create`、`document insert`、`document update` 和 `bytedoc shell` 里的 `insertOne`/`insertMany`/`updateOne`/`updateMany`/`replaceOne`/`createCollection`/Volc `createIndex` 都是对业务数据或结构的真实写入与变更。CLI 默认只返回 dry-run 确认预览，Agent 必须展示 `confirmation.reviewTable` 和 `confirmation.warning`，其中 warning 必须完整包含：`注意：写入与变更相关功能仅建议在测试库使用。Agent 幻觉可能导致误操作，若用于生产环境，风险由用户自行承担。` 如果 Agent 基于只读查询自行生成写入预览并向用户确认，确认问题里也必须完整展示这句注意提示。用户明确确认后，才追加 `--execute --yes-i-understand-agent-write-risk` 执行。
- 写入确认时序是硬约束：`document list` / `shell find` 等只读结果只能用于确认影响范围，不能作为最终确认问题。查到待变更记录后，禁止直接问“是否继续/确认执行”；必须先运行最终写入命令的 CLI dry-run（不带 `--execute`），展示 CLI 返回的 `confirmation.reviewTable` 和 `confirmation.warning` 后再问用户。若最终计划执行多条 `updateOne`，优先用写入型 `shell` `bulkWrite([...])` 或等价 `document update` dry-run 生成同一份 CLI 确认材料。
- `BYTEDOC_COLLECTION_NOT_FOUND` 是终止态。不要把缺失集合包装成普通“待插入确认”；先报告 collection 不存在，并询问用户选择已有集合或是否先创建集合。
- `BYTEDOC_COLLECTION_STATUS_UNKNOWN` 是终止态。它表示 `document list` 命中了 DMS 的可疑空 cursor，且 bytedcli 无法确认 collection 是否存在；不要把它说成“0 条数据”，先报告无法确认集合状态。
- `document list` 返回空结果时，只有 CLI 已确认 collection 存在（例如 JSON 中带 `collection_check.status=exists`，或普通空结果不属于可疑空 cursor）才可以向用户说明“没有匹配数据”。
- `BYTEDOC_NOT_FOUND` 且 `agent_protocol.next_state=ASK_USER` 是路由未确认终止态。停止并让用户确认 service/site/backend/vregion；不要继续改 keyword、去掉 backend、直接 `shell findOne()` 或把资源别名当 service 试错。
- `BYTEDOC_SCHEMA_ERROR` 是控制面/schema 失败终止态。报告 endpoint、failedSources/request context；不要用 `collections`/`shell` 变体绕过未解析的 Volc 路由。
- `resources.agent.json.databases.*` 的 key 是执行资源别名，不是真实 service PSM。真实 service 只能取 `databases.<alias>.service` 或用户明确给出的 PSM。
- classic DMS shell 禁止执行 `createIndex/createIndexes/ensureIndex`；收到 `BYTEDOC_INDEX_CREATION_REQUIRES_BPM` 后停止，并改走 `../index-governance/GUIDE.md` 的 `bytedoc index create` dry-run / BPM 工单链路。不要用 query-file、DMS direct API 或脚本绕过。
- `BYTEDOC_UNSAFE_OPERATION_BLOCKED` 是终止态；不要换 BOE、DBW、DMS direct API、query file 或脚本绕过。
- `BYTEDOC_PROD_NETWORK_READ_ONLY` 是生产网只读终止态；不要取消 `BYTEDCLI_NETWORK_PROFILE=prod`、切 ByteDoc 域名、改走 DMS/DBW、query file 或脚本绕过。
- `site=us-ttp|eu-ttp` 的 classic / cloud-native DMS 数据面不支持查询；收到 `BYTEDOC_UNSUPPORTED_SITE` 且 `details.site=us-ttp|eu-ttp` 时停止，不要猜 dc、改 DMS endpoint、切 backend/vregion 或申请权限。搜索、详情、IAM 等控制面能力不受该限制。
- `i18n-bd / Asia-SouthEastBD` 的 classic/cloud-native DMS 数据面当前不支持；仅在数据操作需要实际执行 DMS 时，于 DMS 请求前返回 `BYTEDOC_UNSUPPORTED_SITE`，按 `agent_protocol.next_state=STOP` 停止并报告该区域限制。`collections` 仍走控制面；dry-run 可能先返回预览，不代表 DMS 可用。既有区域别名、配置和默认区域同样受限；不要重试、猜 dc、改 endpoint、切 backend/vregion 或申请权限。搜索、详情、IAM、Volc/DBW 与其他受支持的 i18n-bd 区域不受该限制。
- `BYTEDOC_DMS_ERROR` 是 DMS subscribe/evaluate 阶段的终止态。报告 stage、endpoint、request_id 和上游响应；不要原命令重试、切 backend/vregion、猜库名、改走权限申请，或改用 `bytedoc shell` / `document` 变体继续同一个 Mongo 读写操作（例如 `document update` 超时后再跑 `shell updateOne`）。

## 查询示例

```bash
# 用户说"查一下 example_db 库的 users 集合"
bytedcli --json --site cn bytedoc search --keyword "example.bytedoc.example_db"

# 只有确认唯一候选后，后续命令才显式携带已确认的 backend/vregion
bytedcli --json --site cn --vregion China-North bytedoc shell --service "example.bytedoc.example_db" --backend classic --collection "users" --query 'find().limit(5)'

# 如果用户已完整给出 site + backend + vregion + service，可直接执行 resolver-backed 目标命令
bytedcli --json --site boe --vregion boei18n bytedoc collections --service "example.bytedoc.example_db" --backend classic

# 如果搜索或 resolver 返回 BYTEDOC_AMBIGUOUS，展示候选给用户选择，不执行查询
```

## 安全命令

```bash
# 列出集合（使用已确认 backend/vregion）
bytedcli --json --site cn --vregion China-North bytedoc collections --service "example.bytedoc.demo_orders" --backend classic
bytedcli --json --site boe --vregion China-BOE bytedoc collections --service "example.bytedoc.demo_volc" --backend volc

# shell 查询（使用已确认 backend/vregion）
bytedcli --json --site cn --vregion China-North bytedoc shell --service "example.bytedoc.demo_orders" --backend classic --collection "demo_items" --query 'find().limit(10)'
bytedcli --json --site cn --vregion China-North bytedoc shell --service "example.bytedoc.demo_orders" --backend classic --collection "demo_items" --query-file ./query.mongo
bytedcli --json --site boe --vregion China-BOE bytedoc shell --service "example.bytedoc.demo_volc" --backend volc --query 'db.getCollectionNames()'

# Volc/火山版 建索引是真实写入；先获取 CLI 确认预览并展示 warning/reviewTable，用户确认后再追加执行 flag
bytedcli --json --site boe --vregion China-BOE bytedoc shell --service "example.bytedoc.demo_volc" --backend volc --query 'db.demo_items.createIndex({"tenant":1},{"name":"tenant_1"})'

# 文档查询（使用已确认 backend/vregion）
bytedcli --json --site cn --vregion China-North bytedoc document list --service "example.bytedoc.demo_orders" --backend classic --collection "demo_items" --filter-json '{"tenant":"demo"}' --limit 10

# 文档更新默认返回 dry-run 确认预览；展示 confirmation.warning/reviewTable，用户确认后再追加 --execute --yes-i-understand-agent-write-risk
bytedcli --json --site cn --vregion China-North bytedoc document update --service "example.bytedoc.demo_orders" --backend classic --collection "demo_items" --filter-json '{"tenant":"demo"}' --update-json '{"$set":{"value":2}}'
```

## 显式查重写入流程

默认边界：用户只要求“插入一条文档”时，不要主动追加查重链路；已知 collection 时直接展示待写入摘要并等待用户确认，确认后执行真实 insert。只有用户明确要求先查重，或明确表达“不存在才插入”“避免重复”“确保这条记录存在”这类语义，并且提供 stable key、业务 id 或唯一 filter 时，才使用本流程。

1. 仍然先确认 site/backend/vregion/service；缺 selector 时通过 `bytedoc search` 或 resolver 解析唯一 backend/vregion。site + backend + vregion + service 已完整时，不要为了重复确认而单独执行 `bytedoc search`。
2. 明确要求查重且 collection + 查重 filter/stable key 已知时，使用 `document list` 携带同一 filter 和 `--limit 1` 查重，不要为了查重先运行 `collections`。
3. 命中已有文档时，向用户报告“记录已存在”，不要执行 insert，也不要进入写入确认。
4. 空结果且已确认 collection 存在时，展示待写入摘要，等用户确认后再执行真实 insert。
5. 如果 `document list` 返回 `BYTEDOC_COLLECTION_NOT_FOUND`，这是终止态：报告 collection 不存在或不可访问，询问用户选择已有集合或是否先创建集合。
6. 如果 `document list` 返回 `BYTEDOC_COLLECTION_STATUS_UNKNOWN`，这是终止态：报告 collection 状态无法确认，不要把空 cursor 当作“0 条数据”。
7. 如果 `document list` 返回 `BYTEDOC_ACCESS_REQUIRED`、`BYTEDOC_DMS_ERROR`、`AUTH_REQUIRED` 或其它结构化错误，按对应错误的 `agent_protocol.next_state` 处理，不要切 backend/vregion 或改用完整文档查重。

未明确要求查重时，已知 collection 的普通 insert 不先运行 `document list`；展示待写入摘要，等用户确认后再执行真实 insert。`collections` 仍用于 collection 未知、用户明确要求列集合、通用写入前集合确认，或查重失败后用户要求诊断。未知 collection 或通用写入前 `collections` 返回 HTTP_ERROR/timeout 时，报告集合前置检查失败并停止等待用户决定，不要进入 insert/update 确认。

## 危险操作停止规则

- CLI 会在到达 DMS 或 DBW 前拦截破坏性 delete/drop/rename 操作。
- 被拦截的例子包括 collection drop/rename、document delete、`drop`、`renameCollection`、`deleteOne`、`deleteMany`、`remove`、`findOneAndDelete`、drop index 和包含 delete 的 `bulkWrite`。
- classic DMS 会在到达 DMS 前拦截 `createIndex/createIndexes/ensureIndex`，返回 `BYTEDOC_INDEX_CREATION_REQUIRES_BPM`。经典版建索引必须走 `bytedoc index create` dry-run 和 BPM 工单链路；不要通过 `shell --query-file`、DMS direct API 或脚本绕过。Volc/火山版/DBW 建索引仍使用 DBW mongoshell，不受该 classic DMS 限制影响。
- `BYTEDOC_UNSAFE_OPERATION_BLOCKED` 是终止态。不要改用 BOE、DBW、DMS direct API、query file 或脚本重试。
- 如果用户确实需要破坏性管理操作，请引导用户走 bytedcli 之外的专门审核管理流程。

## 访问错误

- 如果 Mongo 命令返回 `BYTEDOC_ACCESS_REQUIRED`，切换到 `access-workflows/GUIDE.md` 并遵循 `error.details.setup_commands`。
- 如果 Mongo 命令返回 `BYTEDOC_INDEX_CREATION_REQUIRES_BPM`，说明用户正在 classic DMS shell 里建索引；按 `agent_protocol.next_state=STOP` 停止，加载 `index-governance/GUIDE.md`，用 `bytedoc index create` 先生成 dry-run。不要换 query-file、DMS direct API 或脚本继续同一建索引意图。
- 如果 Mongo 命令返回 `BYTEDOC_DMS_ERROR`，说明失败发生在 DMS 传输或 DMS 上游处理阶段；按 `agent_protocol.next_state=STOP` 停止，并把 stage/endpoint/request_id 报给用户。不要把失败的 `document update` 改写成 `bytedoc shell ... updateOne(...)`，也不要把失败的 `shell updateOne` 改写成 `document update`；这些是同一个 Mongo 写入意图的变体。
- 如果 Mongo 命令返回 `BYTEDOC_COLLECTION_NOT_FOUND`，说明目标 collection 不存在或当前后端不可用；按 `agent_protocol.next_state=STOP` 停止，不要继续插入、更新或把它当作查重通过。
- 如果 Mongo 命令返回 `BYTEDOC_COLLECTION_STATUS_UNKNOWN`，说明 bytedcli 无法确认 collection 是否存在；按 `agent_protocol.next_state=STOP` 停止，不要把 `documents=[]` 包装成空结果。
- 如果 Mongo 命令返回 `BYTEDOC_NOT_FOUND` 且 `agent_protocol.next_state=ASK_USER`，说明 service/backend/vregion 路由未确认；停止并询问用户，不要再执行 search、collections、document list 或 shell 变体。
- 如果 Mongo 命令返回 `BYTEDOC_SCHEMA_ERROR`，说明搜索/控制面响应结构异常；按 `agent_protocol.next_state=STOP` 停止并报告 endpoint/failedSources，不要用数据面命令绕过。
- 不要把访问失败解释成 schema、collection 或 routing 猜测。
- 如果缺少 site/backend/vregion 或权限 role，先澄清或展示候选，不要切换 backend/site/vregion/role 重试。

## DO / DON'T

| 场景                                                                                 | ✅ DO                                                                                                                                                                                                                                                                                                                                                     | ❌ DON'T                                                                                                                              |
| ------------------------------------------------------------------------------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------- |
| 查询文档                                                                             | `bytedoc shell --query 'find({"status":"active"}).limit(10)'`                                                                                                                                                                                                                                                                                             | 不要省略 `.limit()`，避免全表扫描                                                                                                     |
| 写入文档                                                                             | 先运行不带 `--execute` 的写命令获取 CLI dry-run 预览，展示 `confirmation.warning` 和 `confirmation.reviewTable`；如果先自行生成业务预览并询问用户，确认问题里也必须展示完整“注意：写入与变更相关功能仅建议在测试库使用。Agent 幻觉可能导致误操作，若用于生产环境，风险由用户自行承担。”；用户确认后才追加 `--execute --yes-i-understand-agent-write-risk` | 不要首次命令就带执行 flag，也不要在 DMS_ERROR 后改用 `shell updateOne` / `document update` 变体绕过；不要向用户确认写入时省略风险提示 |
| classic DMS 建索引                                                                   | 使用 `bytedoc index create` dry-run，用户确认后通过 BPM 工单 live                                                                                                                                                                                                                                                                                         | 不要运行 `shell createIndex/createIndexes/ensureIndex`、query-file、DMS direct helper 或脚本                                          |
| Volc/火山版 建索引                                                                   | 通过 DBW `bytedoc shell --backend volc --query 'db.<collection>.createIndex(...)'` 获取 dry-run 确认预览，展示 warning/reviewTable，用户确认后再追加执行 flag                                                                                                                                                                                             | 不要改走 classic `index create` BPM 工单                                                                                              |
| 收到 UNSAFE_OPERATION_BLOCKED                                                        | 停止，告知用户走管理流程                                                                                                                                                                                                                                                                                                                                  | 不要换 BOE 或 DMS 直连绕过                                                                                                            |
| 收到 ACCESS_REQUIRED                                                                 | 执行 `setup_commands`                                                                                                                                                                                                                                                                                                                                     | 不要切换 backend 重试                                                                                                                 |
| US-TTP / EU-TTP 返回 UNSUPPORTED_SITE                                                | 告知用户对应 TTP 站点不支持 DMS 数据查询并停止                                                                                                                                                                                                                                                                                                            | 不要猜 dc、改 endpoint、切 backend/vregion                                                                                            |
| i18n-bd / Asia-SouthEastBD DMS 返回 UNSUPPORTED_SITE                                 | 告知用户该区域 classic/cloud-native DMS 当前不支持并停止                                                                                                                                                                                                                                                                                                  | 不要重试、猜 dc、改 endpoint、切 backend/vregion                                                                                      |
| 收到 DMS_ERROR                                                                       | 报告 stage/endpoint/request_id 并停止                                                                                                                                                                                                                                                                                                                     | 不要重试、切 backend/vregion、申请权限，或改用 `shell` / `document` 变体继续同一 Mongo 操作                                           |
| 用户明确要求先查重/不存在才插入/避免重复，且已知 collection + 查重 filter/stable key | 使用 `document list` 携带同一 filter 和 `--limit 1` 查重                                                                                                                                                                                                                                                                                                  | 不要把普通 insert 自动升级成查重写入                                                                                                  |
| 未知 collection 或通用写入前 `collections` 返回 HTTP_ERROR/timeout                   | 报告集合前置检查失败，停止等待用户决定                                                                                                                                                                                                                                                                                                                    | 不要进入插入/更新确认                                                                                                                 |
| 收到 COLLECTION_NOT_FOUND                                                            | 报告 collection 不存在，询问用户选择已有集合或先创建集合                                                                                                                                                                                                                                                                                                  | 不要继续插入/更新，也不要当作查重通过                                                                                                 |
| 收到 COLLECTION_STATUS_UNKNOWN                                                       | 报告 collection 状态无法确认，等待用户确认或修复 auth/network                                                                                                                                                                                                                                                                                             | 不要把可疑空 cursor 说成“0 条数据”                                                                                                    |
| 收到 NOT_FOUND + ASK_USER                                                            | 报告路由未确认，询问 service/site/backend/vregion                                                                                                                                                                                                                                                                                                         | 不要继续 search/shell 变体试错                                                                                                        |
| 收到 SCHEMA_ERROR                                                                    | 报告 schema/endpoint/failedSources 并停止                                                                                                                                                                                                                                                                                                                 | 不要去掉 backend 或直接 shell                                                                                                         |
| 资源文件里有 alias                                                                   | 读取 `databases.<alias>.service`                                                                                                                                                                                                                                                                                                                          | 不要把 alias key 当作 `--service`                                                                                                     |
| Volc `collections` 失败                                                              | 读取 DBW 错误；必要时用 `shell --query 'db.getCollectionNames()'` 复核，但注意它需要 ExecuteSQL 权限                                                                                                                                                                                                                                                      | 不要改用 classic `access role list` 证明权限                                                                                          |
| 用户要删数据                                                                         | 告知被 CLI 安全拦截，引导审核流程                                                                                                                                                                                                                                                                                                                         | 不要尝试用 `updateMany + $unset` 绕过                                                                                                 |
| 需要 aggregate 查询                                                                  | 用 `shell --query 'aggregate([...])'`                                                                                                                                                                                                                                                                                                                     | 不要因为没有 aggregate 子命令就拒绝                                                                                                   |

## 端到端示例：写入文档流程

```bash
# 场景：用户说"确保 demo_orders 的 logs 集合里存在 id=demo-001 的测试数据"

# Step 1: 确认 site 后先解析目标数据库
bytedcli --json --site cn bytedoc search --keyword "example.bytedoc.demo_orders"
# → 确认唯一候选：backend=classic, vregion=China-North

# Step 2: 用户明确要求“确保存在”，且 collection 已知、有稳定查重 filter，先查重，不先跑 collections
bytedcli --json --site cn --vregion China-North bytedoc document list --service "example.bytedoc.demo_orders" --backend classic --collection "logs" --filter-json '{"id":"demo-001"}' --limit 1
# → 如果命中已有文档，报告“记录已存在”，不要执行 insert
# → 如果返回 BYTEDOC_COLLECTION_NOT_FOUND，停止并让用户选择已有集合或先创建集合

# Step 3: 空结果且已确认 collection 存在时，先运行写入命令的 dry-run 预览，不带执行 flag
bytedcli --json --site cn --vregion China-North bytedoc document insert --service "example.bytedoc.demo_orders" --backend classic --collection "logs" --doc-json '{"id":"demo-001","type":"test","message":"hello","ts":"2024-01-01T00:00:00Z"}'
# → 展示 data.result.confirmation.reviewTable 和 data.result.confirmation.warning 后，询问用户是否确认
# warning 必须包含：注意：写入与变更相关功能仅建议在测试库使用。Agent 幻觉可能导致误操作，若用于生产环境，风险由用户自行承担。

# Step 4: 用户确认后才执行真实写入
bytedcli --json --site cn --vregion China-North bytedoc document insert --service "example.bytedoc.demo_orders" --backend classic --collection "logs" --doc-json '{"id":"demo-001","type":"test","message":"hello","ts":"2024-01-01T00:00:00Z"}' --execute --yes-i-understand-agent-write-risk

# Step 5: 如果返回 BYTEDOC_ACCESS_REQUIRED
# → 遵循 error.details.setup_commands 申请权限
```
