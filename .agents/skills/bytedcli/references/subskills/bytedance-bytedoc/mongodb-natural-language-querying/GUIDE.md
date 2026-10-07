# ByteDoc MongoDB 自然语言查询指南

当用户用自然语言描述希望从 ByteDoc collection 查询的数据时使用本指南，例如“查询一条订单”、“找最近失败的任务”或“帮我写一个筛选条件”。

本指南将 MongoDB 官方 `mongodb-natural-language-querying` agent-skill 规则适配到 ByteDoc 场景。维护说明见 `../references/mongodb-upstream-adaptation.md`。

## 证据优先

- 先按 `../references/selection-guards.md` 确认 `site`，再使用 `bytedcli --json --site <site> bytedoc search --keyword <psm>` 或 resolver 命令确认目标数据库的 backend/vregion 是否唯一。
- `backend` 和 `vregion` 没有默认值：只能由用户明确提供，或由搜索/resolver 证明唯一；任一维度多值时必须让用户选择。
- 不猜 collection 名；如果用户未提供 collection，先询问，或在 site/backend/vregion 已确认后列集合。
- 生成 filter、projection 或 sort key 前，先用安全只读命令查看 schema / sample data。
- 优先使用 `--json` 输出，并在推理中保留原始证据。

## 查询生成规则

- 默认生成只读查询：`findOne`、`find`、`countDocuments` 或等价 ByteDoc 安全查询命令。
- `find` 必须显式加 limit；除非用户要求更小数量，否则使用 `limit 10`。
- 使用从已观察字段推导出的选择性 filter；除非明确做 sample exploration，否则避免空 filter。
- 当用户只需要少量字段时，使用 projection 避免返回大字段或敏感字段。
- 字段名、tenant/account scope、时间范围或 collection 名存在歧义时，先问澄清问题。

## ByteDoc CLI 流程

```bash
# 列出集合（使用已确认 backend/vregion）
bytedcli --json --site cn --vregion China-North bytedoc collections --service "example.bytedoc.demo_orders" --backend classic

# 结构化文档查询（使用已确认 backend/vregion）
bytedcli --json --site cn --vregion China-North bytedoc document list --service "example.bytedoc.demo_orders" --backend classic --collection "demo_items" --filter-json '{"tenant":"demo"}' --limit 10

# shell 查询（使用已确认 backend/vregion）
bytedcli --json --site cn --vregion China-North bytedoc shell --service "example.bytedoc.demo_orders" --backend classic --collection "demo_items" --query 'find({"tenant":"demo"}).limit(10)'
```

## 自然语言查询示例

```bash
# 场景：用户说"查一下 demo_orders 里最近失败的任务"

# Step 1: 确认 site 后解析目标数据库
bytedcli --json --site cn bytedoc search --keyword "example.bytedoc.demo_orders"
# → 确认唯一候选：backend=classic, vregion=China-North

# Step 2: 列出集合
bytedcli --json --site cn --vregion China-North bytedoc collections --service "example.bytedoc.demo_orders" --backend classic

# Step 3: 根据集合结构生成安全只读查询
bytedcli --json --site cn --vregion China-North bytedoc shell --service "example.bytedoc.demo_orders" --backend classic --collection "tasks" --query 'find({"status":"failed"}).sort({"created_at":-1}).limit(10)'
```

## 安全规则

- 不要运行 `deleteMany`、`drop`、`renameCollection`、drop index 等破坏性命令。
- 除非用户明确请求写操作，并确认目标 service、collection 和 filter，否则不要生成写查询。
- 最终答复中不要暴露敏感 sample document 字段；改为总结结构和相关字段名。
- 不要在未展示所用证据的情况下，把自然语言生成的查询描述为必然正确。

## 交接到代码生成

- SDK 代码场景下，在 `sdk plan` 支持后运行 `bytedcli --json --site <site> bytedoc sdk generate ...`。
- 将基于证据得到的 filter / projection / sort 应用到生成的代码示例中。
- driver 代码需与 `mongodb-connection/GUIDE.md` 保持一致。

## DO / DON'T

| 场景 | ✅ DO | ❌ DON'T |
| --- | --- | --- |
| 用户说"查最近的订单" | 生成 `find({}).sort({"created_at":-1}).limit(10)` | 不要生成无 limit 的全表查询 |
| 不确定 collection 名 | 先用 `bytedoc collections` 查看 | 不要猜 collection 名 |
| 需要聚合 | 用 `shell --query 'aggregate([{$match:...},{$group:...}])'` | 不要说"不支持 aggregate" |
| 用户要删数据 | 拒绝，说明只生成只读查询 | 不要生成 deleteMany |
| 字段名不确定 | 先 `document list --limit 1` 看 schema | 不要猜字段名 |

## Aggregate 查询示例

```bash
# 场景：用户说"统计每个状态的订单数量"

# Step 1: 确认集合结构
bytedcli --json --site cn --vregion China-North bytedoc document list --service "example.bytedoc.demo_orders" --backend classic --collection "orders" --limit 1
# → 看到 {"status": "active", "amount": 100, ...}

# Step 2: 生成聚合查询
bytedcli --json --site cn --vregion China-North bytedoc shell --service "example.bytedoc.demo_orders" --backend classic --collection "orders" --query 'aggregate([{"$group":{"_id":"$status","count":{"$sum":1}}}])'
# → 返回 [{_id:"active",count:150},{_id:"failed",count:23}]
```
