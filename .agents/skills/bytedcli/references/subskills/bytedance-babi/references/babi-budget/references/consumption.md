# 预实消耗相关命令

## 字段声明

`--status` 资源人力枚举值，默认纯资源 = `1`：

- `0`：资源+人力
- `1`：纯资源
- `2`：纯人力

`--group-by` 分组聚合字段，默认全选：`CustomerBudgetSourceId,CustomerBudgetDepartmentId,CustomerBudgetCategoryType,BudgetDepartmentId,BudgetSourceId,Product,Flavor,Region,Period,BillType,BudgetCategoryType`。

- `CustomerBudgetCategoryType`：需求方大类
- `CustomerBudgetDepartmentId`：1级需求方
- `CustomerBudgetSourceId`：需求方预算单元
- `BudgetCategoryType`：供给方大类
- `BudgetDepartmentId`：1级供给方
- `BudgetSourceId`：商品预算单元
- `Product`：商品
- `Flavor`：组合计费单元
- `Region`：售卖区域
- `BillType`：计费项口径
- `Period`：填报口径

查询成本消耗筛选项：

```bash
bytedcli babi budget consumption cost filter list \
  --budget-area oversea \
  --budget-version 2026-M08 \
  --begin-month 1785513600000 \
  --end-month 1827590400000 \
  --budget-source-ids 1 \
  --status 1 \
  --format json
```

成本 Filter 命令请求 `GET /v3/budget_consumption/getCostConsumptionDetailFilter`。必填：`--budget-area`、`--budget-version`、`--begin-month`、`--end-month`。`--budget-source-ids` 可选，`--status` 默认 `1`。输出按 `categories` 分为“供给方”和“需求方”，每个字段包含 `display_field`、`request_field`、`options[]`。

查询收入消耗筛选项：

```bash
bytedcli babi budget consumption income filter list \
  --budget-area cn \
  --budget-version 2026-M08 \
  --begin-month 1785513600000 \
  --end-month 1827590400000 \
  --budget-source-ids 6 \
  --status 0 \
  --format json
```

收入 Filter 命令请求 `GET /v3/budget_consumption/getConsumptionDetailFilterItem`，入参与输出结构和成本 Filter 一致。

查询预实消耗概览：

```bash
bytedcli babi budget consumption execution-overview get \
  --budget-area cn \
  --budget-version 2026-M77 \
  --budget-source-ids 6,7 \
  --begin-month 1767196800000 \
  --end-month 1788192000000 \
  --status 0 \
  --limit 9 \
  --offset 0 \
  --format json
```

预实消耗概览不区分成本/收入，请求 `GET /v3/budget_consumption/getBudgetExecutionOverview`，自动写死 `Indicate=ProfitRate,IncomeBudgetAmount,CostBudgetAmount,IncomeBudgetExecutionRate,CostBudgetExecutionRate,IncomeBillAmount,CostBillAmount,Profit`，调用时不需要传入 `Indicate`。返回只处理 `Details`，不展示接口返回的 `Sum`。输出按预算单元和指标展开，每行包含 `预算单元`、`指标`、`value`、`合计` 和月份列。

查询成本消耗明细：

```bash
bytedcli babi budget consumption cost detail \
  --budget-area oversea \
  --budget-version 2026-M08 \
  --budget-source-ids 1 \
  --begin-month 1785513600000 \
  --end-month 1827590400000 \
  --status 0 \
  --group-by CustomerBudgetSourceId,CustomerBudgetDepartmentId,CustomerBudgetCategoryType,BudgetDepartmentId,BudgetSourceId,Product,Flavor,Region,Period,BillType,BudgetCategoryType \
  --limit 9 \
  --offset 0 \
  --format json
```

成本明细命令请求 `GET /v3/budget_consumption/getCostConsumptionDetail`。输出会依次处理接口返回的 `Details`，并将 `Sum` 作为末行返回；汇总行使用与明细相同的维度和 `指标` 结构。

查询收入消耗明细：

```bash
bytedcli babi budget consumption income detail \
  --budget-area oversea \
  --budget-version 2026-M08 \
  --budget-source-ids 1 \
  --begin-month 1785513600000 \
  --end-month 1827590400000 \
  --status 0 \
  --group-by CustomerBudgetSourceId,CustomerBudgetDepartmentId,CustomerBudgetCategoryType,BudgetDepartmentId,BudgetSourceId,Product,Flavor,Region,Period,BillType,BudgetCategoryType \
  --limit 9 \
  --offset 0 \
  --format json
```

收入明细命令请求 `GET /v3/budget_consumption/getIncomeConsumptionDetail`。输出会依次处理接口返回的 `Details`，并将 `Sum` 作为末行返回；汇总行使用与明细相同的维度和 `指标` 结构。

查询成本消耗概览：

```bash
bytedcli babi budget consumption cost overview get \
  --budget-area cn \
  --budget-version 2026-M08 \
  --budget-source-ids 1 \
  --begin-month 1785513600000 \
  --end-month 1827590400000 \
  --status 1 \
  --format json
```

成本消耗概览命令请求 `GET /v3/budget_consumption/getCostConsumptionSummary`，返回 `BillAmount`、`BudgetAmount`、`ConsumptionRate`、`Currency`、`Status`、`TimeRate` 概览字段。

查询收入消耗概览：

```bash
bytedcli babi budget consumption income overview get \
  --budget-area cn \
  --budget-version 2026-M77 \
  --budget-source-ids 6,7 \
  --begin-month 1767196800000 \
  --end-month 1788192000000 \
  --status 0 \
  --limit 9 \
  --offset 0 \
  --format json
```

收入消耗概览命令请求 `GET /v3/budget_consumption/getIncomeConsumptionOverview`，自动写死与预实消耗概览相同的 `Indicate`，调用时不需要传入 `Indicate`。返回只处理 `Details`，不展示接口返回的 `Sum`。输出结构与预实消耗概览一致。

查询成本消耗 Top 15 商品：

```bash
bytedcli babi budget consumption cost top-product list \
  --budget-area cn \
  --budget-version 2026-M08 \
  --budget-source-ids 1 \
  --begin-month 1785513600000 \
  --end-month 1827590400000 \
  --status 1 \
  --format json
```

成本 Top 商品命令会依次请求 `GET /v3/budget_consumption/getCostBillTopProduct` 和 `GET /v3/budget_consumption/getCostBudgetTopProduct`，两个接口入参相同。返回列表只保留 `Type`、`ProductName`、`Rate`、`Amount` 字段，其中 `Type` 标识数据来自 `账单` 还是 `预算`。

查询收入消耗 Top 15 商品：

```bash
bytedcli babi budget consumption income top-product list \
  --budget-area cn \
  --budget-version 2026-M77 \
  --budget-source-ids 6 \
  --begin-month 1767196800000 \
  --end-month 1788192000000 \
  --status 0 \
  --format json
```

收入 Top 商品命令会依次请求 `GET /v3/budget_consumption/getIncomeBillTop15BudgetSourceInfo` 和 `GET /v3/budget_consumption/getIncomeBudgetTop15BudgetSourceInfo`，两个接口入参相同。返回列表只保留 `Type`、`ProductName`、`Rate`、`Amount` 字段，其中 `Type` 标识数据来自 `账单` 还是 `预算`。

查询策略：

- 当用户询问预算单元的预实消耗概览、预实执行概览、按月概览表时，优先请求 `budget consumption execution-overview get`。
- 当用户明确询问成本消耗明细、成本消耗概览或成本消耗 Top 商品时，分别请求 `budget consumption cost detail`、`budget consumption cost overview get`、`budget consumption cost top-product list`。
- 当用户明确询问收入消耗明细、收入消耗概览或收入消耗 Top 商品时，分别请求 `budget consumption income detail`、`budget consumption income overview get`、`budget consumption income top-product list`。
- 当用户给出具体筛选项（例如供给方、需求方、商品、组合计费单元、区域等）或需要明细行时，基于用户意图选择 `cost detail` 或 `income detail`。
- 如果用户只提供预算单元名称，先用 `budget source search` 查预算单元 ID；如果缺少可用筛选项，基于用户意图先用 `budget consumption cost filter list` 或 `budget consumption income filter list` 查看可选 `request_field`。

必填参数：

- `--budget-area`：预算区域，例如 `cn`、`oversea`。
- `--budget-version`：预算版本，例如 `2026-M08`。
- `--budget-source-ids`：预算单元 ID，可先用 `budget source search` 获取。
- `--begin-month` / `--end-month`：毫秒时间戳。
- `--status`：资源+人力 = 0, 纯资源 = 1, 纯人力 = 2, 默认 1=纯资源。
- `--group-by`：维度列表，使用后端字段名，默认全选: CustomerBudgetSourceId,CustomerBudgetDepartmentId,CustomerBudgetCategoryType,BudgetDepartmentId,BudgetSourceId,Product,Flavor,Region,Period,BillType,BudgetCategoryType。

`budget consumption execution-overview get` 和 `budget consumption income overview get` 不需要 `--group-by`，支持 `--budget-source-ids 6,7` 或重复传入预算单元 ID，并支持 `--limit` / `--offset` 分页。

可选筛选参数来自 `budget consumption cost filter list` / `budget consumption income filter list` 的 `request_field`：

- 供给方：`--category-types`、`--department-source-ids`、`--provider-budget-source-ids`、`--product-ids`、`--flavors`、`--regions`。
- 需求方：`--customer-category-types`、`--customer-department-source-ids`、`--customer-budget-source-ids`。


```bash
bytedcli babi budget consumption cost detail \
  --data '{"BudgetArea":"cn","BudgetVersion":"2026-M08","BudgetSourceIds":"1","BeginMonth":1785513600000,"EndMonth":1827590400000,"Status":1,"DepartmentSourceIds":"55","GroupBy":"CustomerBudgetSourceId,BudgetDepartmentId","Limit":9,"Offset":0}' \
  --format json
```

输出为列表。先返回 `Details` 明细行；接口存在 `Sum` 时，将其转换为列表末尾的汇总行。每行包含维度字段：需求方大类、1级需求方、需求方预算单元、供给方大类、1级供给方、商品预算单元、商品、组合计费单元、售卖区域、计费项口径、填报口径。

每行的 `指标` 包含 8 个子指标：预算金额、账单金额、金额消耗占比、预算全量、账单用量、用量消耗占比、预算月度用量、账单月度用量。每个子指标包含 `value`、`合计` 和按月份展开的值，例如 `2026-08`、`2026-09`、`2026-10`。
