---
name: bytedance-bytegraph
description: "Use ByteGraph V3 APIs to inspect deployment, table, vertex, edge, TTL, and index metadata or run read-only Gremlin Extended queries through bytedcli across CN, Singapore, EU BDEE, and US BDEE control planes."
---

# bytedcli ByteGraph

本 skill 只对应 ByteGraph V3 控制面与 V3 API（`/bytegraph/fe-api/v3`），不兼容 ByteGraph V2 接口。

## 前置条件

- `metadata get` 查看集群部署机房、表，以及指定表的点、边、TTL 和索引 Schema；无需 `--vdc`。
- `metadata get --schema-only` 只请求指定表的 Schema，必须同时传 `--table`。
- `query` 执行 Gremlin Extended 只读查询，需要全局 `--vdc`。
- 用全局 `--site` 选择控制面 JWT，用全局 `--vregion` 选择实际部署；全局参数都放在 `bytegraph` 前。
- 每个控制面必须使用自己的 ByteCloud 用户 JWT。首次调用前执行 `bytedcli --site <site> auth login`。
- 每条查询都必须显式限制结果规模，例如 `.limit(10)`。
- EU/US BDEE 受限员工控制面只支持 metadata/schema，不能执行 Gremlin `query`。`eu-ttp`、`eu-ttp-limited` 和 `us-ttp-bdee` 均只支持 metadata/schema；`eu-ttp-full` 不属于该限制。

## Quick start

```bash
bytedcli --json --site i18n --vregion Singapore-Central bytegraph metadata get --psm example.graph --table sample_table
bytedcli --json --site eu-ttp --vregion EU-TTP2 bytegraph metadata get --psm example.graph --table sample_table
bytedcli --json --site us-ttp-bdee --vregion US-TTP2 bytegraph metadata get --psm example.graph --table sample_table
bytedcli --json --site cn --vregion China-East bytegraph metadata get --psm example.graph --table sample_table
bytedcli --json --site cn --vregion China-North bytegraph metadata get --psm example.graph --table sample_table
bytedcli --json --site eu-ttp-limited --vregion EU-TTP2 bytegraph metadata get --psm example.graph --table sample_table --schema-only
bytedcli --site i18n --vregion Singapore-Central --vdc sample-vdc bytegraph query --psm example.graph --table sample_table --query 'g.V().limit(10)'
```

## Agent Guidance

- 控制台 URL 中 `/clusters/<psm>/<vregion>` 对应 `--psm` 与全局 `--vregion`；查询页面选中的 IDC/VDC 对应全局 `--vdc`。
- ByteGraph 只接受以下 `site` / `vregion` 组合：`i18n` 或 `i18n-tt` + `Singapore-Central`；`eu-ttp` / `eu-ttp-limited` / `eu-ttp-full` + `EU-TTP2` 或 `US-EastRed`；`us-ttp-bdee` + `US-TTP` 或 `US-TTP2`；`cn` + `China-East` 或 `China-North`。矩阵外组合返回 `BYTEGRAPH_INPUT_ERROR`；`i18n-bd`、`us-ttp`、`us-ttp-usts` 暂不支持 ByteGraph。
- 每个控制面从自己的 ByteCloud credential partition 获取用户 JWT，不要跨控制面复用或 fallback。EU BDEE 与 `US-EastRed` 走 EU BDEE 网关，`US-TTP` / `US-TTP2` 走 US BDEE 网关，CN 与 SG 走各自控制面。
- EU/US BDEE 受限员工环境只能读取部署、表和 schema 元数据。不要为 `--site eu-ttp` / `--site eu-ttp-limited` 或 `--site us-ttp-bdee` 生成 `bytegraph query`；该限制不是重复登录或申请普通 RBAC 可以解决的。
- 保留用户提供的 Gremlin 原文，不自动补写 label、边类型或业务过滤条件。
- `query` 会拒绝 `addV`、`addE`、`property`、`drop` 等写步骤，并要求原查询显式包含 `.limit(...)`。
- 查询报 401/403 时，先登录同一个 `--site`，再确认目标 PSM/table 的 RBAC 权限。
- 查询报 `BYTEGRAPH_API_ERROR` 时，检查 Gremlin 语法以及 PSM、table、Vregion、VDC 是否匹配。

## References

- 不确定全局参数放置、JSON 输出或调试参数时，读取 `../../invocation.md`。
- 认证、权限或查询错误排查见 `../../troubleshooting.md`。
