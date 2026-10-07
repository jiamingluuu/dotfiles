# BABI Bill 账单编排

示例占位符必须替换为用户提供或上一步返回的真实值，不要用示例 ID 执行真实查询。

## 先定位对象，再查询账单

- 只有业务名称：加载 [babi-account 指南](../../babi-account/GUIDE.md)，运行 `account list`；唯一候选或用户确认后使用 `consumer_type=1`。
- 只有团队名称：加载 [babi-finops 指南](../../babi-finops/GUIDE.md)，运行 `finops team search`；确认 `team_id` 后使用 `consumer_type=2`。
- 服务树名称或路径：加载 `bytedance-bytetree`，执行 `bytedcli --json bytetree search` 获取候选并消歧稳定节点 ID；已有 ID 后使用 `consumer_type=3`。

不要把账号、团队和服务树 ID 混用。按需传 `--service-tree-node-search-mode`：`1=本节点递归`、`2=仅本节点`、`3=仅子节点`。

### 多主体对比

多个 `consumer_ids` 需要逐主体对比时，优先在同一次成本查询中增加主体业务维度：

1. `consumer_type=1`：先用 `account list --account-ids <consumer_id,...> --limit <N>` 批量补查账号层级；能确认同一层级时选择对应
   `customer_lN_account_id`，层级混合或仍不确定时选择全部 `customer_l1_account_id` 至 `customer_l6_account_id`。
2. `consumer_type=3`：选择 `billing_account_id`，其后端内部语义是
   `service_tree_node_id`。
3. `provider_*` 只表示卖方成本来源，不能用于保留输入消费主体。
4. 先看 `bill cost list --help`；若字段尚未暴露，或后端返回 `10201006`，说明能力尚未在
   当前环境上线。此时明确报告限制，禁止把未分组聚合结果当作逐主体对比结果。

不要默认拆成多个单主体请求。只有用户明确接受客户端拼接，或当前环境尚未支持主体分组且
业务必须继续时，才把拆分查询作为降级方案，并明确说明分页和合并发生在客户端。

```bash
bytedcli babi bill cost list \
  --begin-date "<begin-millis>" --end-date "<end-millis>" \
  --consumer-type "<1|2|3>" --consumer-ids "<stable-id>" \
  --amount-type 0 --group-keys dynamic_date \
  --settlement-type "<resolved-settlement-type>" --time-span 2
```

用户未指定结算类型时，先按[账单命令](bill.md#用户未指定结算类型)检查最后账期月是否
已经封账：检查下一个自然月的第 5 个工作日结束边界，已越过使用 `2`，否则使用 `1`。
不能只因账期自然月已经结束就选择月正式或声称结算完成。

## 按商品名称查询成本

用户提供消费主体、区域和自然语言商品名时，不能先按 Product 名称搜索后把空结果解释为
成本为 0。金额事实来自账单，商品主数据只用于稳定映射后的补全展示。

1. 先按本页规则解析消费主体、结算类型、日期、区域和地域口径。
2. 执行 `bill cost list` 时在 `--group-keys` 中保留 `provider_l5_account_id`，同时保留
   用户要求的日期、区域和地域维度。按 `data.pagination` 拉取所有分页。
3. 从完整账单行收集并去重 `provider_l5_account_id`。它是卖方 L5 商品账号 ID，不能直接
   当作 `product_id`；先用 `account list --account-ids <provider_l5_account_id,...> --account-type goods --limit <N>`
   查询对应账号，并用返回的 `account_id -> entity_id` 作为稳定映射证据。`N` 不得小于本批
   ID 数量，单批超过 `account list` 限制时分批查询。
4. 只有通过账号列表或用户提供的其它已验证来源拿到稳定商品 ID 后，才查询权威商品快照：

   ```bash
   bytedcli babi product get \
     --product-id "<product-id[,product-id...]>" \
     --format json
   ```

5. 用已经验证并匹配用户目标的稳定商品 ID 或用户确认的账单维度筛选原始账单行，再汇总金额。
   Product 名称查询只用于补充候选或展示，不能代替账单金额证据。

自然语言匹配得到多个候选时，展示已验证来源提供的稳定 ID、名称和 Product 站点信息并等待
用户确认，禁止默认选择第一项。若需要先辅助搜索商品名称，加载 [babi-product 指南](../../babi-product/GUIDE.md)，未指定站点时
直接使用 `product get` 的默认三站点范围，但仍要回到上述稳定商品 ID 或用户确认的账单维度确认金额范围。

### 成本为 0 的判定

只有以下两种情况可以输出成本为 0：

1. 已通过稳定 `provider_l5_account_id` 或用户确认的映射锁定目标，完整账单结果中的匹配
   行金额合计为 0。
2. 已锁定稳定目标，账单请求成功且全部分页完成，没有返回目标对应的账单行。

Product 名称搜索为空、只查询 BABI 站点、只读取账单第一页、`account list` 未返回对应映射、
后端返回权限/路由/参数/超时错误或多个候选尚未确认时，结果必须
标记为“未确认”，不能输出 0 元。

## 查询收入

收入使用卖方账号 ID，不使用买方 `account_id`：

```bash
bytedcli babi bill income list \
  --begin-date "<begin-millis>" --end-date "<end-millis>" \
  --provider-account-ids "<provider-account-id>" \
  --amount-type 0 --group-keys dynamic_date \
  --settlement-type "<resolved-settlement-type>" --time-span 2
```

## 查询单位成本

1. `--group-keys` 至少包含 `cost_driver_type`，通常同时保留 `dynamic_date`。
2. 用户指定 CD 类型时传 `--cost-driver-types`；未指定时省略，让后端返回可用指标。
3. `cost_driver_value` 是指标值，`cost_driver_name` 是展示名称；不要再次相除。
4. CD 行可能重复携带同一分组的 `bill_amount`，汇总金额前按账期和业务维度去重。

查询 CostDriver 口径配置、优化建议或容量证据时切换到 [babi-finops 指南](../../babi-finops/GUIDE.md)。

## 输出顺序

1. 结论：正常、异常、未确认或无数据。
2. 发生了什么：时间、对象、方向和影响。
3. 证据与限制：区分事实和推断。
4. 查询口径：稳定 ID、时间、分组、分页及 `logId` / `RequestId`。
5. 部分金额脱敏时说明可见合计与完整总额的差别，并按[问题反馈](../../feedback.md)处理尚未解决的问题。
