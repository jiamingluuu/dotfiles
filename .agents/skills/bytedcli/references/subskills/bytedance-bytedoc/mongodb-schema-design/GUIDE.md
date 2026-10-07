# ByteDoc MongoDB Schema 设计指南

当任务涉及审查 ByteDoc collection 结构、决定 embed/reference、诊断 document 增长，或为生成的 SDK 代码提供 schema/index 设计建议时，使用本指南。

本指南将 MongoDB 官方 `mongodb-schema-design` agent-skill 规则适配到 ByteDoc 场景。更新规则见 `../references/mongodb-upstream-adaptation.md`。

## ByteDoc 边界

- bytedcli 只提供 schema 和设计建议；不得自动修改业务 schema。
- 除非用户明确请求该操作并确认目标环境，否则不要创建 collection、index、validator 或 migration script。
- 任何 schema 调查都必须先按 `../references/selection-guards.md` 确认 `site`、backend 和 vregion；backend/vregion 只能由用户提供或搜索/resolver 证明唯一。
- `BYTEDOC_AMBIGUOUS` / `agent_protocol.next_state=ASK_USER` 是硬边界：展示候选表，不要自行选择后继续 schema 调查。
- 如果遇到 `BYTEDOC_ACCESS_REQUIRED`，切换到 `access-workflows/GUIDE.md`；如果遇到 `BYTEDOC_UNSAFE_OPERATION_BLOCKED`，立即停止。

## DO / DON'T

| 场景 | ✅ DO | ❌ DON'T |
| --- | --- | --- |
| 审查 schema | 先收集 sample、query shape 和访问模式 | 不要凭字段名直接重构 |
| 建议 index/validator | 说明 trade-off，并作为单独确认任务 | 不要直接执行创建命令 |
| 缺少 site | 先询问 site | 不要猜 backend 或 vregion |
| 需要迁移 | 给步骤和验证方式 | 不要生成会直接改库的脚本并执行 |

## 需要收集的证据

- Collection 名和有代表性的 sample documents。
- 字段基数、数组增长风险、典型查询 filter / sort。
- 当问题涉及性能时，收集现有 index 和慢查询 fingerprint。
- TTL、归档、保留周期、合规等数据生命周期要求。

## 设计规则

- 围绕 access pattern 建模，不要默认按关系型范式拆分。
- 对总是一起读取且增长有界的数据使用 embed。
- 当内嵌数组可能无界增长、更新频率差异很大或 ownership boundary 不同时，使用 reference。
- 避免在热点 document 中放无界数组；对用户/事件驱动增长使用 child collection 或 bucketing pattern。
- 保持 document 小于 MongoDB 文档大小限制，默认避免返回大子树。
- 只有 retention 语义明确且目标 ByteDoc backend 支持时，才建议 TTL 或归档设计。

## ByteDoc 专属指导

- 推荐 schema 变更前，使用 `mongodb-natural-language-querying/GUIDE.md` 推导真实 query shape。
- 当 schema 问题由慢查询触发时，使用 `mongodb-query-optimizer/GUIDE.md`。
- 对生成的 Go SDK 代码，struct 保持最小化，并与实际读写字段对齐。
- 优先给增量迁移建议和验证步骤；不要一开始就建议破坏性 schema rewrite。

## 输出格式

- 说明观察到的 access pattern 和 schema 证据。
- 识别 document 增长、cardinality 和 index 风险。
- 在 trade-off 有意义时，推荐一个主方案和一个备选方案。
- 包含 migration / verification 步骤，但执行必须作为单独的用户确认任务。
