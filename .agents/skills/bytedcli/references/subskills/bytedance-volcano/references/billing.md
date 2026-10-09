# 费用中心账单：按自定义时间范围下钻与对账（只读）

查询火山账号自身的已出账费用。时间范围由用户定义：整月、跨月日期段、精确到分钟的时段、包含当天都只是不同的起止时间；结果按天、产品、项目、计费项、实例下钻，并用 Decimal 对账。

内部成本中心、服务树或团队成本、预算执行、成本异动归因属于 BABI 内部成本口径，使用 `bytedcli babi ...`（bytedance-babi），不要用本流程替代。

## 1. 固定身份与范围

```bash
ve sts GetCallerIdentity
bytedcli --json volcano auth list-accounts
```

- 按主 SKILL 使用默认身份；只有用户指定 profile 时才传 `--profile`，不要自行切换。
- 时间一律按东八区解释；结束时间晚于当前时间时截至查询时刻。
- 报告写明账号、范围、查询时刻与币种；范围包含当天时写明“已出账截至”时间。

## 2. 用脚本下钻（推荐）

`scripts/billing_drilldown.py` 只调用 `ve billing ListBillDetail`、`ve billing ListBillOverviewByProd` 与 `ve sts GetCallerIdentity`，需要 python3 和已登录的 ve。

```bash
# 整月：已结束的账期会额外与产品总账做第三层核对
python3 scripts/billing_drilldown.py --start 2026-09 --end 2026-09 --output text
# 跨月日期段：--end 为日期时包含该日整天
python3 scripts/billing_drilldown.py --start 2026-09-25 --end 2026-10-03
# 从某天到现在：包含当天，输出已出账截至时间
python3 scripts/billing_drilldown.py --start 2026-10-01
# 只看今天
python3 scripts/billing_drilldown.py --start today --output text
# 精确到分钟的时段：结束时刻不包含
python3 scripts/billing_drilldown.py --start "2026-10-03 10:00" --end "2026-10-03 12:00"
# 按产品、财务托管 Owner 过滤，并把汇总和明细写入目录
python3 scripts/billing_drilldown.py --start 2026-09 --product <Product> --owner-id <owner-account-id> --out-dir ./billing-report
```

| 写法                    | 作为 `--start`  | 作为 `--end`                        |
| ----------------------- | --------------- | ----------------------------------- |
| `YYYY-MM`               | 当月 1 日 00:00 | 包含整月                            |
| `YYYY-MM-DD`            | 当天 00:00      | 包含整天                            |
| `YYYY-MM-DD HH:MM[:SS]` | 该时刻          | 不包含该时刻                        |
| `today`                 | 今天 00:00      | 包含今天（截至查询时刻）            |
| `now`                   | 查询时刻        | 查询时刻（省略 `--end` 时的默认值） |

脚本按天规划数据来源：

- 整天：用每日产品（`GroupPeriod=1, GroupTerm=2`）与每日计费项（`GroupTerm=0`）互相核对。同一账期内整天数不少于 10 时按整个账期查询再按 `ExpenseDate` 过滤，否则按天带 `--ExpenseDate` 查询。
- 当天：同样用每日汇总计费，另取当天明细（`GroupPeriod=2`），以最大 `ExpenseEndTime` 作为已出账截至时间。
- 精确到分钟的部分时段：用明细按 `ExpenseBeginTime`/`ExpenseEndTime` 落入窗口计费；跨越窗口边界的明细无法拆分，单独列出且不计入合计；同时核对全天明细与每日产品。
- 某账期整月（当前账期为 1 日至今）都在范围内时，再与产品总账（`ListBillOverviewByProd`）核对。
- 跨账期时按 `BillPeriod` 分别查询再拼接；每页 `Limit 300`、`NeedRecordNum 1`，检查 `ResponseMetadata.Error`、`Total`、空页、重复页和 `Total` 变化。
- 金额用 `Decimal` 按币种加总；无法解析的金额单独计数，不当作 0；差异原样报告，不调整数值。

默认输出 JSON，`--output text` 输出可读摘要。字段包括 `totals`（应付、已付、未付）、`as_of`、`complete`、`reconciliation.checks`、`by_day`、`by_product`、`by_project`、`by_billing_mode`、`top_charge_items`、`top_instances`、`layers`（每层行数、`Total`、页数、RequestId）与 `warnings`。`--out-dir` 另写 `summary.json`、`items.csv`，有跨边界明细时写 `boundary.csv`。

退出码：0 成功（对账有差异也返回 0，以 `reconciliation.ok` 判断）；1 参数错误；2 ve 调用或接口错误。`reconciliation.ok` 只统计已出账完整的天和账期；当天与当前账期的检查标记为 `in_progress`，层间短暂不一致属于出账进行中，稍后重跑通常会收敛。

## 3. 口径与易错点

- 默认以 `PayableAmount`（应付）报费用；`OriginalBillAmount`、`PreferentialBillAmount`、`DiscountBillAmount` 分别是原价、优惠、折后；抹零在产品总账为 `RoundBillAmount`、明细为 `RoundAmount`；`CouponAmount`、`PointDeductAmount` 是代金券、积分抵扣；`PaidAmount`、`UnpaidAmount`、`SettlementType` 与费用统计分开说明。
- 内部测试账号常见 `SettlementType=非结算`：应付大于 0，已付与未付为 0。表述为“已出账费用”，不是个人扣款或欠费。
- 出账时效：上月完整账单在每月第 2 个自然日 12:00 后可取；当天明细按 5 分钟、1 小时等粒度滚动出账，以输出的截至时间为准；最近两天可能补出账，复查时重新查询。
- `ListCostAnalysisOpenApi` 的按天数据存在延迟，最近 1 到 2 天可能为 0 或偏小；不要用于当天或最近两天，只能作为更早日期的交叉参考。
- `BillingMode` 请求参数用数字（1 包年包月、2 按量计费、3 合同计费、4 履约计费），响应是中文字符串。
- 数组参数写 `--Product.1 <Product>` 或 JSON 数组；`--Product <Product>` 会报 `expected JSON for array`。
- `--Project` 只对计费项明细维度生效，不能用于跨层对账；按项目看费用使用脚本输出的 `by_project`。
- 财务托管账号不传 `OwnerID` 时可能包含绑定的子账号；先核对返回的 `OwnerID`、`PayerID`，需要时用 `--owner-id`。
- 免费资源包的购入与按量使用分开统计；`Count`、`DeductionCount` 按 `Unit`、`PriceUnit` 解释，不跨单位相加；千 tokens 与 tokens 明确换算，缓存与输入是否重叠确认定义后再合计。

## 4. 手动下钻（脚本不覆盖时）

```bash
# 产品总账（单账期）
ve billing ListBillOverviewByProd --BillPeriod <YYYY-MM> --Limit 300 --NeedRecordNum 1 --Offset <OFFSET>
# 每日产品与每日计费项；--ExpenseDate 必须在账期内，建议填写以提升性能
ve billing ListBillDetail --BillPeriod <YYYY-MM> --GroupPeriod 1 --GroupTerm 2 --ExpenseDate <YYYY-MM-DD> --Limit 300 --NeedRecordNum 1 --Offset <OFFSET>
ve billing ListBillDetail --BillPeriod <YYYY-MM> --GroupPeriod 1 --GroupTerm 0 --ExpenseDate <YYYY-MM-DD> --Limit 300 --NeedRecordNum 1 --Offset <OFFSET>
# 明细：含 ExpenseBeginTime / ExpenseEndTime
ve billing ListBillDetail --BillPeriod <YYYY-MM> --GroupPeriod 2 --GroupTerm 0 --ExpenseDate <YYYY-MM-DD> --Limit 300 --NeedRecordNum 1 --Offset <OFFSET>
# 单个计费实例
ve billing ListBillDetail --BillPeriod <YYYY-MM> --GroupPeriod 1 --GroupTerm 0 --InstanceNo <instance-no> --Limit 300 --NeedRecordNum 1 --Offset 0
```

`GroupPeriod`：0 账期、1 按天、2 明细；`GroupTerm`：0 计费项、1 实例、2 产品、3 账号。不传 `NeedRecordNum` 时 `Total` 为 -1，无法证明完整；`Offset` 按已取条数前进，直到达到 `Total`。

## 5. 资源回读与归因边界

- 用账单的 `InstanceNo`、`ResourceID`、`InstanceName`、`Project`、`Region` 定位资源，再用对应产品的只读 Describe/Get 读取当前状态与规格。历史费用、当前配置和业务调用是不同证据层。
- AgentKit 未进入 ve metadata，按 [扩展 API](extend-apis.md) 的 `--force` 规则调用，并用 `--query` 只投影白名单字段；不要保存或输出完整 `GetRuntime`，其中包含 `Envs`、`AuthorizerConfiguration` 等敏感字段。

```bash
ve agentkit ListRuntimes --version 2025-10-30 --endpoint open.volcengineapi.com --method POST --force \
  --body '{"MaxResults":100}' \
  --query 'Result.{NextToken:NextToken,Runtimes:AgentKitRuntimes[].{Id:RuntimeId,Name:Name,Status:Status,Project:ProjectName}}'
ve agentkit GetRuntime --version 2025-10-30 --endpoint open.volcengineapi.com --method POST --force \
  --body '{"RuntimeId":"<runtime-id>"}' \
  --query 'Result.{Id:RuntimeId,Name:Name,Status:Status,Project:ProjectName,CpuMilli:CpuMilli,MemoryMb:MemoryMb,MinInstance:MinInstance,MaxInstance:MaxInstance}'
```

- 常驻成本用连续完整日的实测账单与当前最小实例数解释；推算 30 天时写明“配置与费率不变”等条件和未包含的费用，不称为月度最终预测。
- 模型计费实例（如 `muti-` 开头）不等于推理接入点；`Project` 为 `-` 或无标签时，只能给出模型、日期、计费项级结论。按应用分摊需要调用日志、API Key 级用量统计（只取统计，不读密钥）或项目、标签映射；不要凭模型名或时间吻合归因到具体应用。

## 6. 不在本流程内的写操作

`ve billing` 下的 `PayOrder`、`CancelOrder`、`RenewInstance`、`UnsubscribeInstance`、`SetRenewalType`、`CommonBuy`、`CreateDropShippingOrder`、`CreateBudget`、`UpdateBudget`、`DeleteBudget`、`CreateFinancialRelation`、`DeleteFinancialRelation`、`CleanUpFinancialRelation`、`HandleInvitation`、`CancelInvitation`、`UpdateAuth` 会产生交易或修改配置，不属于下钻流程；确有需要时按主 SKILL 的写入与破坏性规则单独确认。为降低费用而停止资源、调整实例数或退订，同样需要用户另行授权。

## 7. 交付与验收

交付顺序：账号、范围、查询时刻、已出账截至时间、币种与应付合计 → 对账结论（含 `in_progress` 与未解释差异）→ 按天 → 按产品 → 按项目 → 计费项与实例 Top → 归因限制与提示。

验收：分页完整，没有 `Total` 异常提示；Decimal 对账结论明确，差异原样披露；范围包含当天时标注截至时间；未把免费资源包购入当作用量；未把应付表述为实付；未输出密钥或运行时敏感字段；没有任何云资源或账单写操作。
