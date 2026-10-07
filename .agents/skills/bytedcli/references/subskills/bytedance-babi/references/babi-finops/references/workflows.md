# BABI FinOps 多步编排

只执行用户需要的链路；占位符必须替换为真实值，不要使用示例 ID 查询生产数据。

## 定位治理对象

- 账号名：加载 [babi-account 指南](../../babi-account/GUIDE.md)，解析稳定 `account_id`。
- 团队名：运行 `finops team search`，多候选等待用户选择 `team_id`。
- 服务树名称或路径：加载 `bytedance-bytetree`，执行 `bytedcli --json bytetree search` 获取候选并消歧稳定节点 ID。
- 商品详情：加载 [babi-product 指南](../../babi-product/GUIDE.md)；不要用 `optimization suggestion products` 替代 Product 主数据。

## 查询单位成本与 CD 配置

单位成本数据由 [babi-bill 指南](../../babi-bill/GUIDE.md) 的 `bill cost list` 返回：

1. `group_keys` 至少包含 `cost_driver_type`。
2. `cost_driver_value` 是指标值，`cost_driver_name` 是展示名称。
3. CD 行可能重复携带金额，汇总前按账期和业务维度去重。
4. 查口径配置再调用 `cost-driver caliber/data-config list`；`Filters[].Key` 使用 snake_case。

## 查询优化建议

1. 确定优化对象类型和稳定 ID。
2. 需要商品范围时先运行 `suggestion products`。
3. 需要规则范围时运行 `rule list`。
4. 总体判断用 `suggestion overview`，具体记录用 `suggestion list`。

```bash
bytedcli babi finops optimization suggestion overview \
  --period 2 --optimization-object-type 2 --optimization-object-id "<team-id>"
```

优化建议是待治理线索，不能单独证明成本波动根因。

## 查询容量与利用率

容量明细只能选择 PSM、服务树或业务域之一；趋势需要 PSM、资源类型和 1-30 天窗口。

```bash
bytedcli babi finops capacity list --psm-list "<psm>" --type-list tce --date "<yyyy-MM-dd>"
bytedcli babi finops capacity trend --psm-list "<psm>" --type-list tce --end-date "<yyyy-MM-dd>" --days 7
```

`vregion/vdc`、账单 `area/region` 和 `babi` 前的宿主全局 `--vregion/--site` 属于不同层级，不能互换。容量结果要注明它是主因、反证还是辅助排除。

## 分析输出

1. `结论`：正常、异常、未确认或无数据，并给关键数值/对象。
2. `发生了什么`：时间、范围、方向和影响。
3. `证据与限制`：区分 Bill、CD、优化、容量和 Platform 监控证据。
4. `下一步`：只给与命中证据对应的动作。
5. `查询口径`：稳定 ID、时间、维度、分页及 `logId` / `RequestId`。
