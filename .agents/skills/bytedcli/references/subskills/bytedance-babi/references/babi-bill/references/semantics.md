# BABI Bill 字段口径

## 对象和 ID

| 对象 | 稳定 ID/参数 | 用途 |
|---|---|---|
| BABI 买方账号 | `account_id` / `consumer_type=1` | 成本与用量 |
| FinOps 治理团队 | `team_id` / `consumer_type=2` | 团队成本 |
| 服务树节点 | 节点 ID / `consumer_type=3` | 服务树成本 |
| Product 商品 | `product_id` | 商品分组与主数据补齐 |
| 卖方账号 | `provider_account_id` | 收入查询 |

这些 ID 不可互换。自然语言名称必须经过对应资源 skill 解析，多候选时等待用户确认。

## 金额、用量和单位成本

| 字段 | 语义 | 汇总注意事项 |
|---|---|---|
| `bill_amount` | 买方账单成本 | 只对互斥分组行求和；CD 行可能重复携带金额 |
| `income_amount` | 卖方收入 | 不要用 `bill_amount` 代替 |
| `count` | 用量 | 结合 `count_unit` / `unit`；单位未返回时不要猜 |
| `unit_price` | 实际单价 | 与折前单价、梯度单价区分 |
| `un_discount_unit_price` | 折前单价 | 不等于实际单价 |
| `un_discount_unit_price_interval` | 折前梯度单价 | 按接口返回字符串展示 |
| `cost_driver_name` | CD 指标展示名称 | 只用于展示或分组 |
| `cost_driver_value` | 单位成本/CD 指标值 | 不要再次除以成本或用量 |

单位成本查询的 `group_keys` 必须包含 `cost_driver_type`。用户未指定具体 CD 时省略 `--cost-driver-types`。

## 分组与过滤字段中文映射

`--group-keys` 控制返回结果按哪些维度聚合；`filter.key` 控制保留哪些明细。两者使用同一批英文数据字段，但白名单不同，不能因为某个 key 可分组就推断它也可过滤。`—` 表示该场景不支持。

| Key | 中文业务含义 | `group_keys` 可用范围 | `filter.key` 可用范围 |
|---|---|---|---|
| `dynamic_date` | 账期时间 | cost、income | — |
| `area` | 账单大区 | cost、income | — |
| `region` | 售卖区域 | cost、income | — |
| `flavor` | 计费单元/规格 | cost、income | — |
| `billing_account_id` | 计费账号 ID；成本查询中用于服务树节点，后端内部对应 `service_tree_node_id`，不是 BABI 买方账号 ID | cost、income | — |
| `product_id` | 成本商品 ID；需要名称时交给 [babi-product 指南](../../babi-product/GUIDE.md) 查询 | cost | — |
| `provider_l1_account_id` | 成本产品线账号 ID（卖方 L1） | cost、income | cost、income |
| `provider_l2_account_id` | 成本二级产品线账号 ID（卖方 L2） | cost、income | cost、income |
| `provider_l3_account_id` | 成本产品账号 ID（卖方 L3） | cost、income | cost、income |
| `provider_l4_account_id` | 成本子产品账号 ID（卖方 L4） | cost、income | cost、income |
| `provider_l5_account_id` | 成本商品账号 ID（卖方 L5） | cost、income | cost、income |
| `provider_l6_account_id` | 成本商品子账号 ID（卖方 L6） | cost、income | cost、income |
| `customer` | 消费方 Customer 文本；接口原字段，可单独用 `--customer` 做模糊筛选 | cost | —；使用 `--customer` |
| `cost_driver_type` | 成本驱动/CD 类型；指标名称和值分别看 `cost_driver_name`、`cost_driver_value` | cost | —；使用 `--cost-driver-types` |
| `customer_l1_account_id` | 消费方产品线、App 或职能部门账号 ID（L1） | cost、income | cost、income |
| `customer_l2_account_id` | 消费方二级产品线或 App 子账号 ID（L2） | cost、income | cost、income |
| `customer_l3_account_id` | 消费方产品或 App 子账号 ID（L3） | cost、income | cost、income |
| `customer_l4_account_id` | 消费方子产品或 App 子账号 ID（L4） | cost、income | cost、income |
| `customer_l5_account_id` | 消费方商品账号 ID（L5） | cost、income | cost、income |
| `customer_l6_account_id` | 消费方商品子账号 ID（L6） | cost、income | cost、income |
| `unit_price` | 实际单价 | cost、income | cost、income |
| `un_discount_unit_price` | 折前单价/未折扣单价 | cost、income | cost、income |
| `un_discount_unit_price_interval` | 折前梯度单价 | cost、income | cost、income |
| `charge_item` | 计费项 | cost、income | cost、income |
| `measure_function` | 计费方式 | cost、income | cost、income |
| `count_unit` | 用量单位 | cost、income | cost、income |
| `unit` | 通用单位；与 `count_unit` 分开返回 | cost、income | cost、income |

`provider_*` 与 `customer_*` 表示交易的两个方向，不能互换：前者是卖方成本来源，后者是
消费方账号层级。两个方向现在都是 cost 与 income 的公共分组与过滤维度。
成本查询需要发现或保留消费主体时直接使用 `customer_*`，收入查询需要按卖方拆分时直接使用
`provider_*`，不能因为命令名是 `bill cost list` 就只用 `provider_*`。只有同时取得
`flavor` 和 `region` 时才可称为完整计费项。

自然语言到 key 的例子：

- “按成本二级产品线和实际单价分组” → `--group-keys provider_l2_account_id,unit_price`。
- “筛选成本产品账号且实际单价大于等于 1.5” → `provider_l3_account_id` 与 `unit_price` 两个 cost filter 叶子节点。
- “按收入的消费方产品分组” → `--group-keys customer_l3_account_id`。
- “多个消费方商品账号之间对比成本” → 按 `customer_l5_account_id` 分组（cost 与 income 均支持）。
- “多个服务树节点之间对比成本” → 按公开 key `billing_account_id` 分组；不要传内部字段名 `service_tree_node_id`。

## 过滤操作符中文映射

| 值 | 名称 | 中文含义 |
|---:|---|---|
| `1` | `EQ` | 等于 |
| `2` | `NE` | 不等于 |
| `3` | `GT` | 大于 |
| `4` | `LT` | 小于 |
| `5` | `GE` | 大于等于 |
| `6` | `LE` | 小于等于 |
| `7` | `GT_OR_LT` | 大于或小于 |
| `8` | `IN` | 属于给定集合；省略 `operator` 时的默认值 |
| `9` | `NOT_IN` | 不属于给定集合 |
| `10` | `IS_NULL` | 为空；可省略 `value` |
| `11` | `IS_NOT_NULL` | 不为空；可省略 `value` |
| `12` | `LIKE` | 模糊匹配 |
| `13` | `LEFT_LIKE` | 左侧模糊匹配 |
| `14` | `RIGHT_LIKE` | 右侧模糊匹配 |
| `15` | `NOT_LIKE` | 非模糊匹配 |
| `16` | `RECURSIVE_LIKE` | 递归模糊匹配 |
| `17` | `APPLY` | 应用型匹配；仅在业务明确要求该后端语义时使用 |
| `18` | `MAP` | 映射型匹配；仅在业务明确要求该后端语义时使用 |
| `19` | `CURRENT_NODE_ONLY` | 仅当前节点 |
| `20` | `CHILD_NODES_ONLY` | 仅子节点 |
| `21` | `ABS_LE` | 绝对值小于等于 |
| `22` | `ABS_GE` | 绝对值大于等于 |
| `23` | `ABS_LT` | 绝对值小于 |
| `24` | `ABS_GT` | 绝对值大于 |

除 `IS_NULL` / `IS_NOT_NULL` 外，其他 operator 必须传字符串数组 `value`。完整 JSON 树结构与白名单见[账单命令](bill.md)。

名称只能来自接口返回。缺失时写 `名称未返回 (ID: xxx)`，不要根据 ID、路径或计费单元猜测。
