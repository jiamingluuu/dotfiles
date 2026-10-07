# ByteDoc 慢查询指南

当任务涉及 slow-query overview、detail、subscribers、metrics 和 index recommend 时，使用本指南。

## 命令

```bash
# 慢查询概览（使用已确认 backend/vregion）
bytedcli --json --site cn --vregion China-North bytedoc slow-query overview --service "example.bytedoc.demo_orders" --backend classic --millis 100

# 用户明确时间窗时必须透传 --start / --end
bytedcli --json --site cn --vregion China-North bytedoc slow-query overview --service "example.bytedoc.demo_orders" --backend classic --start "2026-06-15 00:00:00" --end "2026-06-15 23:59:59" --millis 100

# Volc 慢日志概览（走 ByteDoc Cloud DescribeSlowLogs）
bytedcli --json --site cn --vregion China-North bytedoc slow-query overview --service "example.bytedoc.demo_volc" --backend volc --millis 100

# Volc 指定组件（对应控制台慢日志页的“组件”下拉）
bytedcli --json --site cn --vregion China-North bytedoc slow-query overview --service "example.bytedoc.demo_volc" --backend volc --component "mongo-shard-demo-s0-0" --millis 100

# Volc 调大返回上限
bytedcli --json --site cn --vregion China-North bytedoc slow-query overview --service "example.bytedoc.demo_volc" --backend volc --limit 500 --millis 100

# Volc 拉取全量慢日志（按组件和时间窗自动切片；必要时可再配合 --component）
bytedcli --json --site cn --vregion China-North bytedoc slow-query overview --service "example.bytedoc.demo_volc" --backend volc --fetch-all --millis 100

# 慢查询指标
bytedcli --json --site cn --vregion China-North bytedoc slow-query metrics --service "example.bytedoc.demo_catalog" --backend cloud-native --interval 5m

# 订阅者
bytedcli --json --site cn --vregion China-North bytedoc slow-query subscribers --service "example.bytedoc.demo_catalog" --backend cloud-native

# 索引推荐
bytedcli --json --site cn --vregion China-North bytedoc slow-query index-recommend --service "example.bytedoc.demo_catalog" --backend cloud-native

# 原子能力：用户直接要求索引推荐 dry-run 时可执行；从慢查结果主动推进时，先按 playbook 询问是否进入索引治理阶段
bytedcli --json --site cn --vregion China-North bytedoc slow-query index-recommend --service "example.bytedoc.demo_orders" --backend classic --apply-index-dry-run
```

## 慢查询诊断示例

```bash
# 场景：用户说"看一下 example_db 最近的慢查询"
bytedcli --json --site cn bytedoc search --keyword "example.bytedoc.example_db"
# → 确认唯一候选：backend=classic, vregion=China-North

bytedcli --json --site cn --vregion China-North bytedoc slow-query overview --service "example.bytedoc.example_db" --backend classic
# 如果搜索或 resolver 返回 BYTEDOC_AMBIGUOUS，展示候选给用户选择，不执行慢查询
```

## 约束

- slow-query 前必须确认 `site`、`backend` 和 `vregion`；缺少 `site` 时按 `../references/selection-guards.md` 询问。
- `backend` 和 `vregion` 没有默认值：只能由用户明确提供，或由搜索/resolver 证明唯一；任一维度多值时必须让用户选择。
- `BYTEDOC_AMBIGUOUS` / `agent_protocol.next_state=ASK_USER` 是硬边界：展示候选表，不要自行选择后继续。
- `overview` 支持 classic / cloud-native / Volc。Volc 不走 cloud-native slowquery 平台接口，而是通过 ByteDoc Cloud `DescribeSlowLogs` 读取 DBW / Multi Cloud Mongo 慢日志，并按组件/pod 汇总；未指定 `--component` 时，CLI 会从 `GetVolcInfo` 解析 ConfigServers、Mongos、Shards 下的组件并逐个查询，不会只查 config server。
- Volc 用户明确提供控制台“组件”值时，使用 `--component <component>` 原样传入；这会只查询该组件对应的 `DescribeSlowLogs.podName`。
- Volc 默认 `--limit` 是 100，只表示最终返回的日志条数上限，不是全量慢日志证明；不要把默认前 100 条当作全量。需要扩大样本时传 `--limit <n>`；需要全量分析时传 `--fetch-all`，CLI 会按组件和时间窗切片，JSON 里用 `fetch_all`、`fetched_count`、`backend_total`、`truncated`、`exhaustive`、`incomplete_ranges` 说明是否拉全。`total` 仅保留为 `fetched_count` 的兼容别名；判断上游总量用 `backend_total`。
- 如果 `--fetch-all` 后仍有 `incomplete_ranges` 或 `exhaustive=false`，必须向用户说明该时间窗仍不可穷尽，不要直接下全量结论。
- `overview` 未传 `--start` / `--end` 时默认查询近 24 小时。JSON 输出会回显 `queryWindow`；Agent 回复用户时必须说明实际窗口，例如“在默认近 24 小时窗口内未发现 ≥100ms 慢查询”。
- 用户明确给出时间范围时，必须把该范围透传为 `--start` / `--end`，不要退回默认窗口。
- `detail` / `scope` 是 classic / cloud-native slow-query 平台能力；Volc 没有等价的 fingerprint detail 或 scope 列表，CLI 会返回结构化 `unsupported` / `BYTEDOC_UNSUPPORTED_BACKEND`，Agent 应转而使用 `overview`。
- `subscribers` / `metrics` 仅支持 cloud-native。`index-recommend` 支持 classic / cloud-native；Volc 库会返回 `BYTEDOC_UNSUPPORTED_BACKEND`。
- `index-recommend --apply-index-dry-run` 仅支持经典版，只把推荐结果转换为 `indexCreateDryRuns[]` 里的 `bytedoc index create` dry-run 命令，不会提交 BPM 工单。cloud-native 推荐可以继续不带该 flag 查询。用户直接要求该原子能力时可按本指南执行；如果是 Agent 从慢查结果主动推进到建索引治理，必须加载 `../playbooks/GUIDE.md` 和 `../index-governance/GUIDE.md`，先完成慢查证据摘要，询问用户是否进入索引治理阶段，用户确认后才允许生成候选索引和执行 `index create` dry-run。
- 某些慢查询接口在没有数据时会返回结构化空结果：`result.status=no_data`，并带 `agent_protocol.next_state=STOP`、`retryable=false`。这表示当前时间窗/阈值下没有可用慢查询数据；向用户说明结果为空，必要时询问是否调整时间窗或阈值，不要原命令重试。
- 慢查询返回 `BYTEDOC_PLATFORM_SCHEMA_ERROR` 时，表示 ByteDoc 平台网关/schema tagging 拒绝了该 endpoint。报告 endpoint/request_id/上游响应，按 `agent_protocol.next_state=STOP` 停止；不要通过切换 backend/vregion、猜 dbName 或申请权限来绕过。
- Volc 页面上的日志、备份、参数视图属于 DBW / Volc 详情面；当前 `bytedoc slow-query overview --backend volc` 只覆盖慢日志概览，不代表支持 classic/cloud-native 的全部 slow-query 子能力。不要尝试 classic/cloud-native fallback。
- classic detail 接受 ObjectId 风格的 id，并可自动展开 overview fingerprint id。
- 如果用户在获得 SDK 代码后追问查询为什么慢，将本指南和 `mongodb-query-optimizer/GUIDE.md` 结合使用。

## 成功结果后的治理链路

`slow-query overview` 成功且存在慢查询数据时，不要只把慢日志列表或 top query shape 原样抛给用户就结束。默认先做证据摘要；只有用户已经表达 CPU 高、接口超时、任务耗时、客户投诉、优化/治理等业务问题场景，或用户明确要求文档时，才展开完整治理结论。

1. 先用 3-6 条摘要说明事实：查询窗口、阈值、backend/vregion、慢查询总量或采样量、最重的 collection/query shape、主要调用方、耗时/扫描量/返回量等证据。
2. 如果用户没有说明业务问题场景，只追加一句询问是否需要继续治理分析或生成治理文档，不要强行展开长模板。
3. 如果用户表示需要，按 [`governance.md`](governance.md) 的结构输出 Markdown 文档；只有用户明确要求飞书、Wiki 或客户分享版时，才进入对应文档创建/脱敏流程。
4. 如果证据指向需要建索引治理，加载 [`../playbooks/GUIDE.md`](../playbooks/GUIDE.md) 的“慢查到索引治理”流程。除非用户已经明确要求准备建索引工单或 dry-run，否则必须先询问是否进入索引治理阶段；不要在慢查结果后直接运行 `bytedoc index create` dry-run。用户直接要求某个慢查询原子命令时，不需要额外套 playbook。

如果慢查询结果 `truncated=true`、`fetch_all=false` 或 `exhaustive=false`，生成文档前要先说明当前结论基于采样；需要全量治理结论时，建议先用 `--fetch-all` 或更窄时间窗重新拉取。若用户仍要求立即生成文档，文档中的 `慢查描述` 必须显式标注“非全量样本”。

## DO / DON'T

| 场景                   | ✅ DO                                                                                | ❌ DON'T                               |
| ---------------------- | ------------------------------------------------------------------------------------ | -------------------------------------- |
| 用户说"查慢查询"       | 先搜索/解析 backend 与 vregion，唯一后执行 `slow-query overview --backend <backend>` | 不要直接按 classic 或任意 vregion 查询 |
| 需要查看某条慢查询详情 | 先从 overview 拿到 id，再用 `slow-query detail --ids <id>`                           | 不要猜测 id 格式                       |
| backend=volc 的慢查询  | 使用 `slow-query overview --backend volc` 查看慢日志概览；用户指定组件时追加 `--component <component>`；需要全量时追加 `--fetch-all` | 不要尝试 classic/cloud-native fallback，也不要只查 config server，或把默认前 100 条当作全量 |
| backend=volc 的 scope/detail/metrics/subscribers/index-recommend | 报告 CLI 的 unsupported 结果，必要时建议改用 overview | 不要拿 cloud-native 平台路径伪装成 Volc 结果 |
| `result.status=no_data` | 报告当前窗口无数据，必要时询问是否换时间窗或阈值                                     | 不要原命令反复重试                     |
| 用户未声明时间窗 | 使用 CLI 默认近 24 小时窗口，并在回答中说明 `queryWindow` | 不要笼统说“最近没有慢查询” |
| 用户声明时间窗 | 传入 `--start` / `--end` 并按回显窗口回答 | 不要忽略用户时间范围 |
| `BYTEDOC_PLATFORM_SCHEMA_ERROR` | 报告 endpoint/request_id 和上游 schema 拒绝信息，停止自动化 | 不要切 backend/vregion、猜 dbName 或申请权限 |
| 用户问"怎么优化"       | 结合 `mongodb-query-optimizer/GUIDE.md` 给建议                                       | 不要只说"加索引"而不给证据             |
| 慢查询成功且有数据 | 总结证据；用户有治理意图或要求文档时按 `governance.md` 继续 | 不要只返回慢日志列表或 top query 后结束，也不要在用户只想看结果时强行展开长文档 |
| 用户要求治理文档 | 按 `governance.md` 的“慢查描述 / 问题分析 / 整改方案 / 验证标准”输出 Markdown，并标注数据是否全量 | 不要生成没有证据表、没有验证标准的泛泛文档 |
| 慢查证据显示可能需要索引 | 先询问用户是否进入建索引治理阶段；确认后按 `playbooks/GUIDE.md` 继续 | 直接运行 `bytedoc index create` dry-run 或提交 BPM |
| `--millis` 参数        | `--millis 100` 表示过滤执行时间 ≥100ms 的查询                                        | 不要把它理解为采样窗口                 |

## 端到端示例：慢查询诊断到优化建议

```bash
# 场景：用户说"demo_orders 最近查询很慢，帮我看看"

# Step 1: 解析目标数据库
bytedcli --json --site cn bytedoc search --keyword "example.bytedoc.demo_orders"
# → 确认唯一候选：backend=classic, vregion=China-North

# Step 2: 查看慢查询概览
bytedcli --json --site cn --vregion China-North bytedoc slow-query overview --service "example.bytedoc.demo_orders" --backend classic --millis 100
# → 返回 fingerprint 列表，如 [{ "id": "abc123", "namespace": "demo_orders.orders", "avgMs": 2500, "count": 340 }]

# Step 3: 查看最慢的 fingerprint 详情
bytedcli --json --site cn --vregion China-North bytedoc slow-query detail --service "example.bytedoc.demo_orders" --backend classic --ids "abc123"
# → 返回该 query shape 的详细信息（filter、sort、scanType 等）

# Step 4: 阶段门禁：先问用户是否进入索引治理阶段
# Agent 先说明慢查证据和建索引可能性；用户确认后，才查看索引推荐并生成建索引 dry-run 命令
bytedcli --json --site cn --vregion China-North bytedoc slow-query index-recommend --service "example.bytedoc.demo_orders" --backend classic --apply-index-dry-run
# → 返回推荐索引列表和 indexCreateDryRuns[]；命令仍需按 dry-run 协议展示并等待用户确认

# Step 5: 对具体候选再次确认后，才运行 index create dry-run
# Agent 解读：该 query 在 orders 集合上做了全表扫描（COLLSCAN），建议加 index
# 加载 mongodb-query-optimizer/GUIDE.md 给出 ESR 建议
```
