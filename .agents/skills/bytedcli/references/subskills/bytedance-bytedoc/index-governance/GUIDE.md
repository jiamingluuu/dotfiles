# ByteDoc 索引治理指南

当任务涉及查看 ByteDoc 索引列表、查询索引创建/删除/TTL 修改状态、创建经典版索引工单，或从慢查询推荐推进到建索引治理时，使用本指南。

如果入口来自慢查询分析后的主动治理推进，先加载 `../playbooks/GUIDE.md` 的“慢查到索引治理”流程。本指南只描述索引原子能力；跨阶段是否继续、是否进入建索引 dry-run，必须由 playbook 的阶段门禁决定。用户直接要求索引列表、状态查询或创建索引 dry-run 时，按本指南执行，不需要额外套 playbook。

## 范围

- 当前只支持经典版 ByteDoc 索引治理。Volc/火山版 与 cloud-native 建索引工单暂不执行；其中 Volc/火山版 建索引不是 BPM 工单路径，应按 `../mongo-ops/GUIDE.md` 通过 DBW `bytedoc shell --backend volc` 执行 mongoshell 建索引命令。
- `bytedoc index list/task list/task get` 是控制面查询。
- `bytedoc index create` 是 BPM 工单创建能力：默认 dry-run；dry-run 会读取 BPM workflow config 校验 workflow 是否为 ByteDoc 建索引流程，因此也需要 BPM 读权限。只有用户确认后才允许追加 `--execute --yes-i-know-this-is-live`。这里保留双确认 flag 是为了防止索引工单误提交或 workflow 误路由；不要简化成单 `--execute`。
- 设置 `BYTEDCLI_NETWORK_PROFILE=prod` 时，索引列表和任务查询仍允许；`bytedoc index create` 等变更意图（包括 dry-run）返回 `BYTEDOC_PROD_NETWORK_READ_ONLY`。收到后停止，不要取消 profile、切 ByteDoc 域名或改走 DMS/DBW 绕过。
- 创建索引 live 当前只开放已确认到具体工单 workflow 的经典版 route：CN（`workflowConfigId=12076` / `index_create`）、BOE China-BOE（`10671` / `create_index_boe`）、I18N-BD Asia-SouthEastBD（`913` / `create_index`）、I18N-TT Singapore-Central/SGALI（`1838` / `create_index_sg`）、US-TTP OVA/US-TTP（`1158` / `create_index_ttp`）、EU-TTP2/no1a（`1138` / `create_index`）。
- BOE2、BOEI18N/US-BOE、I18N-TT MVA/EU/其他 SG 变体、US-TTP OVA2 当前只允许 dry-run 和状态查询。
- 删除索引和修改 TTL 当前只支持状态查询，不提供 live 执行命令。
- 创建索引只对已确认 CreateIndex workflow 的经典站点/vregion 开放；未确认映射的站点会返回 `BYTEDOC_INDEX_UNSUPPORTED_REGION`，不要猜测 workflow id。

## 命令

```bash
# 查询某个 collection 的索引列表
bytedcli --json --site cn --vregion China-North bytedoc index list --service "example.bytedoc.demo_orders" --backend classic --db-name "demo_orders" --collection "demo_items"

# 查询创建索引任务列表
bytedcli --json --site cn --vregion China-North bytedoc index task list --service "example.bytedoc.demo_orders" --backend classic --db-name "demo_orders" --operation create --status doing --collection "demo_items"

# 查询单个 BPM record / index task 状态
bytedcli --json --site cn --vregion China-North bytedoc index task get --service "example.bytedoc.demo_orders" --backend classic --db-name "demo_orders" --ticket-id 24680

# 创建索引工单 dry-run：不会提交 BPM
bytedcli --json --site cn --vregion China-North bytedoc index create --service "example.bytedoc.demo_orders" --backend classic --db-name "demo_orders" --collection "demo_items" --keys-json '{"tenant":1,"createdAt":-1}' --name "tenant_1_createdAt_-1"

# 用户确认 dry-run payload 后，才允许提交真实 BPM 工单
bytedcli --json --site cn --vregion China-North bytedoc index create --service "example.bytedoc.demo_orders" --backend classic --db-name "demo_orders" --collection "demo_items" --keys-json '{"tenant":1,"createdAt":-1}' --name "tenant_1_createdAt_-1" --execute --yes-i-know-this-is-live

# TTL / unique / partialFilterExpression / collation
bytedcli --json --site cn --vregion China-North bytedoc index create --service "example.bytedoc.demo_orders" --backend classic --db-name "demo_orders" --collection "demo_items" --keys-json '{"expireAt":1}' --ttl-seconds 86400 --partial-filter-json '{"expireAt":{"$exists":true}}' --collation-json '{"locale":"simple"}'

# 用户确认进入索引治理阶段后，慢查询索引推荐到 dry-run 命令：只生成 bytedoc index create dry-run 命令，不提交 BPM
bytedcli --json --site cn --vregion China-North bytedoc slow-query index-recommend --service "example.bytedoc.demo_orders" --backend classic --apply-index-dry-run
```

## Dry-Run / Live 协议

1. 首次创建索引必须不带 `--execute`，查看 JSON 中的 `data.result.payload`、`confirmation.requiredReview`、`confirmation.internalCommand` 和 `nextActions`。
2. dry-run 阶段会调用 BPM `getWorkflowConfig` 做 workflow 校验；如果失败或 403，先处理 BPM 登录/权限/路由问题，不要进入 live，也不要改用内部 `index_manager` 回调口。
3. Agent 必须向用户展示 service、db、cluster、collection、keys、unique、TTL、partialFilterExpression、collation、workflowConfigId、region。
4. 用户明确确认后，才运行 dry-run 输出的确认命令；确认命令必须同时包含 `--execute --yes-i-know-this-is-live`。`--execute` 表示从 dry-run 进入 live，`--yes-i-know-this-is-live` 表示用户已经审阅 payload/workflow 并确认提交真实 BPM 工单，两者缺一不可。
5. live 成功后输出 `ticket.ticketId` 和 `ticket.url`，再用 `bytedoc index task get` 或 `bytedoc index task list --operation create --status doing|finished` 跟踪。
6. 如果 workflow config 校验失败，命令会返回 `BYTEDOC_INDEX_WORKFLOW_MISMATCH`；不要改用内部 index_manager 回调口，也不要猜另一个 workflow id。
7. `payload.config.index` 对应表单里的“索引配置”列；`payload.config.idx_name` 对应“索引名”。`payload.config.create_index_command` 只对应表单底部“可选配置”，只能放 `partialFilterExpression`、`collation` 等 MongoDB createIndex 选项，不能重复放索引列或索引名。
8. live 提交前会重新读取 BPM workflow config，并按当前 site/vregion 精确校验 `workflow_key`、`target_system` 和表单字段；如果返回的是旧流程或其他系统流程，即使 workflow 名称里有“索引创建”，也必须停止。
9. 如果 dry-run 返回 `confirmation.canExecute=false` 或 live 返回 `BYTEDOC_INDEX_LIVE_UNVERIFIED`，说明该 route 尚未完成控制面创建表单验证；不要继续尝试 `--execute`。

## 约束

- 建索引 live 验证或生产执行前，必须先确认 collection 存在；CLI 会调用 collections 能力做校验。
- 只能在用户指定或明确允许的新临时 collection 上做 live 验证；不要在原有业务 collection 上建索引验证。
- `cluster_id` 使用控制面展示的 cluster name，例如 `12345`，不是拓扑内部数字 id。
- `--keys-json`、`--partial-filter-json`、`--collation-json` 都必须是 JSON object；不要传数组或字符串。
- 不带 `--partial-filter-json` / `--collation-json` 等可选项时，BPM payload 不应包含 `create_index_command`；不要为了“补全”把 `keys` 或 `name` 塞进该字段。
- TTL 索引必须传正整数 `--ttl-seconds`。
- 经典版 DMS shell 中的 `createIndex/createIndexes/ensureIndex` 会返回 `BYTEDOC_INDEX_CREATION_REQUIRES_BPM`，必须改走本指南的 `bytedoc index create` dry-run / BPM 工单链路；不要用 `shell --query-file`、DMS direct helper 或脚本绕过。
- Volc/火山版 建索引不使用本指南的 `bytedoc index create`；确认 `backend=volc`、vregion、service、collection 和索引参数后，按 Mongo 写操作确认流程运行 DBW `bytedoc shell --backend volc --query 'db.<collection>.createIndex(...)'`。
- 慢查询推荐结果转成 `indexCreateDryRuns[]` 时，只是生成 dry-run 命令。来自慢查询分析时，必须先按 `../playbooks/GUIDE.md` 询问用户是否进入索引治理阶段；在运行具体 `bytedoc index create` dry-run 前，还要让用户确认要为哪个候选索引准备 dry-run。dry-run 成功后仍然必须展示 payload、等待用户确认后才 live。
- 未列入 live 开放矩阵的 BOE/海外 route 必须先补齐该场景实际 ByteDoc 服务页、创建索引入口页、临时 collection、成功/失败 record 证据；未补齐前不要绕过 `BYTEDOC_INDEX_LIVE_UNVERIFIED`。
- 如果返回 `BYTEDOC_INDEX_UNSUPPORTED_REGION`，说明当前 site/vregion 暂无安全映射；不要切换 site/vregion 猜测。

## DO / DON'T

| 场景                   | ✅ DO                                                                                          | ❌ DON'T                                 |
| ---------------------- | ---------------------------------------------------------------------------------------------- | ---------------------------------------- |
| 用户问“当前有哪些索引” | 用 `bytedoc index list`，必须带已确认 selector 和 collection                                   | 用 Mongo shell `getIndexes()` 绕过控制面 |
| 用户问“索引创建到哪了” | 用 `index task list` 或 `index task get`                                                        | 只看 BPM ticket 文本状态就下结论         |
| 用户要求建索引         | 先 dry-run，展示 payload 和确认命令，等用户确认后再 live                                       | 首次命令直接加 `--execute`               |
| 用户要用 DMS shell 建索引 | 告知 classic DMS 已禁用 `createIndex/createIndexes/ensureIndex`，改用 `index create` dry-run                | 用 `shell`、query-file、DMS direct API 或脚本绕过 |
| 用户要求 Volc/火山版 建索引 | 走 `mongo-ops/GUIDE.md`，通过 DBW `bytedoc shell --backend volc` 执行 mongoshell 建索引命令，并按真实写入先确认 | 套用 classic `index create` BPM 工单 |
| 慢查询推荐出索引       | 按 `playbooks/GUIDE.md` 分阶段推进：先问是否进入索引治理，再问是否为具体候选生成 `index create` dry-run | 把推荐结果当成已建索引，或直接提交 BPM   |
| workflow config 不匹配 | 停止并报告 `BYTEDOC_INDEX_WORKFLOW_MISMATCH`                                                   | 调 index_manager 的 BPM 回调 API         |
