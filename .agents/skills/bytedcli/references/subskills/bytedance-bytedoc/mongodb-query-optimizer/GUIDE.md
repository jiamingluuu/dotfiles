# ByteDoc MongoDB 查询优化指南

当用户表示 ByteDoc / Mongo 查询慢、超时、扫描数据过多、排序慢，或请求 index/query 优化时，使用本指南。

本指南将 MongoDB 官方 `mongodb-query-optimizer` agent-skill 规则适配到 ByteDoc 场景。upstream 映射和排除项见 `../references/mongodb-upstream-adaptation.md`。

## 需要收集的证据

- ByteDoc 数据库身份：service PSM、site、backend 和 vregion。缺少 site 时按 `../references/selection-guards.md` 澄清；backend/vregion 只能由用户提供或搜索/resolver 证明唯一。
- Query shape：filter、sort、projection、limit 和操作类型。
- 慢查询证据：`bytedcli --json --site <site> --vregion <confirmed-vregion> bytedoc slow-query overview --service <psm> --backend <confirmed-backend> ...`，以及可用的 detail / fingerprint 数据。
- 慢查询命令细节优先加载 `slow-query/GUIDE.md`；本指南只负责 query shape、index 和 schema 诊断。
- Collection 证据：schema / sample 字段、现有 index、可用的数据量信息，以及近期错误信息。
- 运行时证据：调用方是 local/devbox/TCE/FaaS，以及延迟主要来自连接建立还是查询执行。

## 分析流程

1. 先确认 site、backend/vregion 和 collection；缺少 site 时询问用户，backend/vregion 多值时展示候选让用户选择。
2. 使用 `bytedoc sdk plan` 确认访问路径；连接路径问题不是 query optimizer 问题。
3. 归一化 query shape，描述时移除用户专属字面值。
4. 检查谓词和 sort key 是否能使用现有 index。
5. 查找无边界扫描、缺少 tenant/account/time filter、无锚点 regex、大 `$in`、内存排序等症状。
6. 查询过宽时，优先建议 query shape 调整，再考虑新增 index。
7. 如果建议 index，说明它精确支持的 query shape，以及写入/存储 trade-off。

## ByteDoc 命令

```bash
# 慢查询概览（使用已确认 backend/vregion）
bytedcli --json --site cn --vregion China-North bytedoc slow-query overview --service "example.bytedoc.demo_orders" --backend classic --millis 100

# 慢查询详情
bytedcli --json --site cn --vregion China-North bytedoc slow-query detail --service "example.bytedoc.demo_orders" --backend classic --ids "<fingerprint>"

# 列出集合（使用已确认 backend/vregion）
bytedcli --json --site cn --vregion China-North bytedoc collections --service "example.bytedoc.demo_orders" --backend classic

# shell 查询（使用已确认 backend/vregion）
bytedcli --json --site cn --vregion China-North bytedoc shell --service "example.bytedoc.demo_orders" --backend classic --collection "demo_items" --query 'find({"tenant":"demo"}).limit(10)'
```

## 查询优化示例

```bash
# 场景：用户说"demo_orders 的查询特别慢"

# Step 1: 确认 site 后解析目标数据库
bytedcli --json --site cn bytedoc search --keyword "example.bytedoc.demo_orders"
# → 确认唯一候选：backend=classic, vregion=China-North

# Step 2: 查看慢查询
bytedcli --json --site cn --vregion China-North bytedoc slow-query overview --service "example.bytedoc.demo_orders" --backend classic --millis 100

# Step 3: 查看集合 schema 和索引
bytedcli --json --site cn --vregion China-North bytedoc collections --service "example.bytedoc.demo_orders" --backend classic

# Step 4: 基于证据给出优化建议
```

## 优化规则

- 适用时使用 ESR 思路：equality predicate、sort field、range predicate。
- 不要为每个字段盲目建议 index；每个 index 都必须映射到重复出现的 query shape。
- 在 query shape 和 index 问题被证据排除前，不要优先调连接池大小或 timeout。
- 不要依赖 Atlas Performance Advisor；使用 ByteDoc slow-query 和元数据面。
- 如果 explain 不可用或不安全，说明建议基于 slow-query / schema / index 证据，而不是执行计划。

## 输出格式

- 总结当前 query shape。
- 列出已收集证据和缺口。
- 优先给安全 query rewrite。
- 只有在说明 trade-off 时才给 index 建议。
- 提供变更后可由用户或 Agent 执行的验证命令。

## DO / DON'T

| 场景 | ✅ DO | ❌ DON'T |
| --- | --- | --- |
| 用户问"查询慢怎么办" | 先收集 slow-query 证据 | 不要直接说"加索引" |
| 建议索引 | 说明它精确支持的 query shape 和 trade-off | 不要为每个字段盲目建 index |
| explain 不可用 | 基于 slow-query / schema 证据分析 | 不要说"无法分析" |
| 用户想调连接池 | 先排除 query shape 和 index 问题 | 不要把连接池作为首选优化 |
| ESR 原则 | equality → sort → range 顺序建议 | 不要把 range 放在 sort 前面 |
