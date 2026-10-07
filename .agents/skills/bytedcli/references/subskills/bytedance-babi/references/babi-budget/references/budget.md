# 预算命令

查询预算版本：

```bash
bytedcli babi budget version list --budget-area cn --format json
```

`--budget-area` 只允许 `cn` 或 `oversea`, 返回 `Result[]` 预算版本字符串列表。

enum BudgetVersionStatus {
  /** 生效中 */
  validated = 2
  /** 失效 */
  invalidated = 3,
}

export enum BudgetTypeKey {
  /**年度预算 */
  year = 0
  /**预算调整 */
  reconcile = 1
  /**滚动预测 */
  rollingEstimate = 2,
}

按预算单元名称模糊查 ID：

```bash
bytedcli babi budget source search --budget-area oversea --budget-source-name demo-business --format json
```

命令固定 `Permission=overview_read`，请求 `GET /v3/budget_source/ListBudgetSource`，从 `Result[].BudgetSourceName` 做模糊匹配并返回所有命中的 `budget_source_id`、`budget_source_name`、`category_type`、`group_key`、`upper_source_id`。多个候选必须让用户确认后再用于预实消耗明细查询。

`category_type` 预算单元分类枚举：`0=APP`、`1=中台`、`2=架构`、`3=系统部`、`4=外采`、`5=火山`。

## 预算窗口期列表

```bash
bytedcli babi budget window list \
  --budget-area cn \
  --budget-version 2026-M08 \
  --limit 100 \
  --offset 0 \
  --format json
```

命令请求 `POST /v4/budget/budget_window/list`。`--budget-area` 和 `--budget-version` 必填，均可重复传入或使用逗号分隔；还可通过 `--budget-type` 和 `--status` 进一步筛选。

- 预算类型：`0=年度预算`、`1=预算调整`、`2=预测`。
- 窗口期状态：`0=待生效`、`1=初始化中`、`2=生效中`、`3=已失效`。
- 返回 `budget_window_list[]`，包含预算大区、窗口期版本、预算类型、状态、继承版本、优化目标、基准月、账单月、可填报月范围、历史月范围、子窗口数量、版本备注、创建时间、初始化时间、开启时间、关闭时间、更新时间和更新人。
- 注意，基准月、账单月、可填报月范围、历史月范围的格式展示时应该是 `YYYY-MM`。
- 分页字段为 `total`、`offset`、`limit`。

## 按账号查询预算单元列表

```bash
bytedcli babi budget source list \
  --budget-area cn \
  --account-type app \
  --account-name demo-business \
  --limit 100 \
  --offset 0 \
  --format json
```

命令先请求 `searchAccountTree`，按账号名称做忽略大小写的模糊匹配，并按账号类型筛选账号 ID；随后请求 `getBudgetSourceMainList`接口 查询这些账号关联的预算单元。没有匹配账号时直接返回空的 `RecordList`，不会发起无账号条件的预算单元查询。

`--account-type` 对齐预算单元页面的“账号类型”，支持：

- `app` / `应用` / `0`
- `product_line` / `产品线` / `1`
- `second_product_line` / `二级产品线` / `5`
- `sub_product` / `子产品` / `6`
- `product` / `goods` / `商品` / `2`
- `functional_department` / `func_dept` / `职能部门` / `4`

返回 `RecordList[]` 预算单元树以及 `Total`、`Offset`、`Limit` 分页信息。预算单元记录包含 ID、名称、大区、大类、账号类型、关联账号 ID、状态和子预算单元等接口字段。

预算填报表格的全量校验、错误列回写和红色单元格标记流程见[表格全量校验](sheet-full-check.md)。
