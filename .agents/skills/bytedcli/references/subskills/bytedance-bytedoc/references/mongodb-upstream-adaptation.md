# MongoDB Upstream Skill 适配说明

ByteDoc 复用 MongoDB driver 和查询概念，但 ByteDoc 访问受 PSM 授权、Consul / Mesh 路由、ByteDoc 控制面元数据，以及 BOE / CN / vRegion 网络边界约束。下面这些 guide 将选定的 MongoDB 官方 agent-skills 适配进 `bytedance-bytedoc` skill，用户不需要额外安装 upstream MongoDB skills。

Go SDK 代码生成必须遵循 ByteDoc 官方 SDK 文档，并使用 `code.byted.org/bytedoc/mongo-go-driver`。upstream MongoDB skills 和文档只作为 API 形态与质量规则参考，不作为依赖选择依据。

## Upstream 来源

- Repository：`https://github.com/mongodb/agent-skills/tree/main/skills`
- ByteDoc SDK 文档：以 `bytedoc sdk plan` / `bytedoc sdk generate` 返回的固定 `references[]` 为准，不在 Skill 中固化具体文档 token。
- 适配规则：在有助于映射时保留 upstream skill 边界名称，但示例和决策规则必须重写为 ByteDoc 场景。
- 更新流程：upstream 变化时，对比对应 upstream `SKILL.md` 与 ByteDoc 子 `GUIDE.md`；保留通用 MongoDB 建议，拒绝 Atlas-only 或 MongoDB-MCP-only 流程，除非 ByteDoc 已有等价 bytedcli 能力。

## 已纳入的 Skill

- `mongodb-connection` -> `../mongodb-connection/GUIDE.md`
  - 纳入原因：client 生命周期、timeout、凭证处理、连接池建议和连接故障排查。
  - 适配内容：使用 `bytedoc sdk plan` / `sdk generate`、ByteDoc PSM、token、开发调试账号密码、Consul、Mesh 和网络边界证据。
- `mongodb-natural-language-querying` -> `../mongodb-natural-language-querying/GUIDE.md`
  - 纳入原因：将用户意图转换为安全只读查询。
  - 适配内容：生成 filter 或 projection 前必须获取 ByteDoc schema / sample / index 证据。
- `mongodb-query-optimizer` -> `../mongodb-query-optimizer/GUIDE.md`
  - 纳入原因：慢查询、explain、filter shape、sort 和 index 分析。
  - 适配内容：使用 ByteDoc slow-query 和 collection/index 元数据，而不是 Atlas Performance Advisor。
- `mongodb-schema-design` -> `../mongodb-schema-design/GUIDE.md`
  - 纳入原因：embed vs reference、无界数组、TTL、validation 等数据模型取舍。
  - 适配内容：只输出建议；bytedcli 不得自动修改业务 schema。

## 排除的 Skill

- `mongodb-atlas-stream-processing`
  - 排除原因：Atlas Stream Processing 不是 ByteDoc 接入路径。
  - 仅当 ByteDoc 通过 bytedcli 暴露等价 streaming 或 change-stream 产品面后再重新评估。
- `mongodb-search-and-ai`
  - 排除原因：Atlas Search、Vector Search 和 AI search setup 并非 ByteDoc 普遍可用能力。
  - 仅当 ByteDoc 文档化支持的 search/vector 能力，并提供安全 CLI 检查命令后再重新评估。
- `mongodb-mcp-setup`
  - 排除原因：ByteDoc 工作流不应要求用户配置 MongoDB MCP。
  - ByteDoc 工作流应优先使用 `bytedcli bytedoc ...` 命令和 bytedcli 已内置的 ByteDoc MCP / skill 表面。

## 维护检查清单

- 当 guide 映射 upstream skill 时，可以在子 guide 目录名中保留 upstream skill 名称。
- ByteDoc 专属约束优先：授权、site/vRegion 路由、网络边界和写操作安全高于通用 MongoDB 建议。
- 不要加入 Atlas-only 产品步骤，除非存在 ByteDoc 等价能力和安全 bytedcli 命令。
- 示例 PSM 使用 `example.bytedoc.demo_orders` 等占位值；不要在 guide 示例中硬编码真实生产 PSM。
- 编辑这些 guide 后运行 `npm run validate:skills`。
