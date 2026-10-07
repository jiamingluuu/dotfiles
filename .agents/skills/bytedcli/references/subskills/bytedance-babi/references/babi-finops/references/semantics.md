# FinOps 字段与证据口径

## 对象边界

| 对象 | 稳定字段 | 用途 |
|---|---|---|
| BABI 账号 | `account_id` | 账号成本、优化对象 |
| FinOps 团队 | `team_id` | 团队成本、优化对象 |
| 服务树节点 | 节点 ID | 服务树成本、容量、优化对象 |
| Product 商品 | `product_id` | 主数据和账单商品维度 |
| 优化对象 | `optimization_object_type` + `optimization_object_id` | 规则与建议 |
| 监控对象 | `entity_type` + `entity_id` | Platform 报警与负责人 |

这些对象不可互换。名称先交给对应资源 skill 解析，接口未返回名称时不要猜。

## 证据层级

- Bill 成本/收入：金额、用量和单位成本事实。
- CostDriver 配置：指标口径和数据源配置，不等于当前账期事实值。
- 优化建议：治理候选，不能单独作为波动根因。
- 容量/利用率：资源侧证据，需要说明对象与时间窗口。
- Platform 报警：数据完整性或计量链路证据，未命中不构成业务正常证明。
- Insight 归因树：按实例和分析维度返回的归因证据，需要保留范围与限制。

## 区域边界

- Bill：`area` / `region`。
- Capacity：`vregion` / `vdc`。
- CLI 网关：按 [BABI 通用调用与写入规则](../../babi-invocation.md)，使用 `babi` 前的宿主全局 `--vregion` / `--site`。

名称相似也不能互相替换。用户描述无法唯一映射时先确认目标层级。
