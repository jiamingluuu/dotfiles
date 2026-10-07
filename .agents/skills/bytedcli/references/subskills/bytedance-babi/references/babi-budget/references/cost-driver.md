# Cost Driver 预实分析

## 预算单元与核心 CD 映射（前置，关键）

部分预算单元及其子预算单元的核心 CD 由业务单独维护在飞书文档《抖音预算单元和CD的映射关系》中，`budget cost-driver search` 的下拉级联不覆盖这类子单元。因此，**当用户查询某个预算单元或其子预算单元的 CD（CD 名称、CD 预实、CD 执行率、预实偏差报告的 CD 章节）时，必须先依据该映射文档确定对应的核心 CD，再进行后续查询**。

- 映射文档（真源，动态读取以获取最新映射）：
  https://bytedance.larkoffice.com/wiki/R4EwwRENXiTuARkHZCXcqB0MnBc
- 读取前遵守[飞书资源的用户权限边界](lark-cli-install.md#飞书资源的用户权限边界)。该文档是 `/wiki/` 链接背后的电子表格。按 `lark-doc` / `lark-shared` 规则先用 `lark-cli wiki spaces get_node --as user` 解析出真实 `obj_token`（sheet），再用 `lark-cli sheets +read --as user` 读取；两个步骤都必须使用当前请求用户身份。表格列为 `预算单元 | 预算子单 | 核心CD | CD所属预算单元`；`核心CD` 为空或 `NULL` 表示该子单元未配置 CD。`CD所属预算单元` 指该子单元的 CD 数值应到哪个预算单元下查询（业务口径，如“抖音短视频”），与预实成本里的子预算单元不是同一实体。
- 使用顺序：
  1. 先在映射文档中按预算单元/子预算单元名称匹配，得到该子单元的 `核心CD` 和 `CD所属预算单元` 两个值；`核心CD` 为空/`NULL` 时标注“未确认/无数据”。
  2. 用 `budget cost-driver search --cost-driver-name <核心CD>` 获取 CD 的 ID 与 `budget_source_list`/`cost_drivers` 级联。映射文档的 CD 名可能与系统 CD 名不完全一致（例如文档写“AI投稿总量”，系统为“AI特效投稿总量”），命中多个或不精确时展示候选让用户确认，不要默认取第一项。
  3. 在 `search` 结果中找到与映射文档 `CD所属预算单元` 对应的 `budget_source_id`，用 `CD_ID:该预算单元ID` 组成 `--cost-drivers`（例如 用户使用时长=2、抖音短视频=1 → `--cost-drivers <cost_driver_id>:<budget_source_id>`）。禁止用子预算单元自身的 source ID 拼装（实测子单元 source ID 查 CD 预实返回 0 行）。
  4. 用 `budget cost-driver actual-budget list` 查该级联对的 `forecast_count`（预测 CD）、`actual_count`（实际 CD）、`actual_execution_rate`（CD 执行率）月度序列；脱敏增幅用 `masked-actual-budget list`。详见下文命令。
  5. `CD所属预算单元` 在 `search` 的 `budget_source_list` 中找不到，或 `actual-budget list` 返回空时，标注“未确认/无数据”，不得用默认名称或反推伪造。
- 无法确认当前用户身份、缺少用户授权或文档读取失败时，明确告知“CD 映射不可访问”及原因，停止依赖该映射的 CD 查询。不得改用 bot/shared 身份、其他用户或其缓存/导出结果兜底，也不要凭 `search` 级联或经验猜测子单元的核心 CD。报告中保留 CD 章节并说明限制，继续生成当前用户有权限且不依赖该文档的部分。权限拒绝不能解释为映射缺失、无 CD 或数值为 0；报告审计状态见[预实偏差分析报告](../../babi-finops/references/budget-variance-report.md#costdriver-口径)。

## 通用筛选参数

- `--budget-area`：预算区域，只允许 `cn` 或 `oversea`。
- `--budget-version`：预算版本，必须来自用户输入或 `budget version list` 的结果。
- `--cost-drivers`：可选的 Cost Driver 与预算单元级联筛选。每项必须是 `CD_ID:BUDGET_SOURCE_ID`，可用逗号分隔或重复传入。例如 `--cost-drivers <cost_driver_id>:<budget_source_id>` 会转换为后端字段 `cost_driver=[[1,1],[1,3],[4,2]]`。禁止只传 Cost Driver ID。
- `--areas`：可选的大区筛选，可用逗号分隔或重复传入。它映射后端字段 `area`，取值由 `--budget-area` 决定：
  - `--budget-area cn`：只能传 `cn`（中国）。
  - `--budget-area oversea`：可传 `us`（美国）、`ap`（海外其他）、`OCI`（美国 TTP）、`eu`（欧洲 TTP）、`global`。
- `--start-month` / `--end-month`：月份第一天的毫秒时间戳，闭区间，开始时间不得晚于结束时间。向用户询问时只需要到月份即可。
- 列表命令使用页码分页：`--page` 从 `1` 开始，`--size` 范围为 `1-1000`，默认分别为 `1` 和 `100`。

## 查询 Cost Driver 级联 ID

若用户按名称指定 Cost Driver，必须先查询候选：

```bash
bytedcli babi budget cost-driver search \
  --budget-area cn \
  --budget-version 2026-M08 \
  --cost-driver-name DAU \
  --format json
```

命令请求 `POST /v4/budget/biz/report/budget_cost_mannual/costDriverDropList`，再对返回的 `data[].name` 做忽略大小写的模糊匹配。每个候选保留 `id`、`name`、完整的 `budget_source_list`，并额外生成 `cost_drivers` 级联数组。例如 Cost Driver `DAU` 的 ID 为 `1`，预算单元 ID 为 `1` 和 `192` 时，输出 `cost_drivers=[[1,1],[1,192]]`。

后续查询只能传用户选中的“Cost Driver + 预算单元”组合。例如用户选择 DAU 下的示例业务 A 和示例业务 B，应传 `--cost-drivers <cost_driver_id>:<budget_source_id>`。多个 Cost Driver 或预算单元候选必须展示名称与稳定 ID 并等待用户确认，禁止默认选择第一项。如果用户指定选中某个一级Cost Driver，说明需要把整个CD下面所有的都传入

## CD 预实

查询明细及汇总：

```bash
bytedcli babi budget cost-driver actual-budget list \
  --budget-area cn \
  --budget-version 2026-M08 \
  --cost-drivers <cost_driver_id>:<budget_source_id> \
  --areas cn \
  --start-month 1785513600000 \
  --end-month 1790784000000 \
  --metrics actual_count,forecast_count,actual_execution_rate \
  --page 1 \
  --size 100 \
  --format json
```
`--metrics` 默认全选，除非用户指定一个：
枚举值如下：
- `actual_count`：实际。
- `forecast_count`：预测。
- `actual_execution_rate`：实际执行率。

命令将两个响应的 `data` 合并后一次返回：`data.cost_driver_detail_list[]` 和 `data.total` 来自明细接口，`data.cost_driver_detail_sum` 来自汇总接口。明细包含 Cost Driver、预算单元、单位和大区；`actual_count[]`、`forecast_count[]`、`actual_execution_rate[]` 的第一个元素为合计，后续元素按 `--start-month` 至 `--end-month` 的自然月顺序排列。

不要将当前页明细自行相加替代 `data.cost_driver_detail_sum`；

## CD 脱敏预实

```bash
bytedcli babi budget cost-driver masked-actual-budget list \
  --budget-area oversea \
  --budget-version 2026-M08 \
  --cost-drivers <cost_driver_id>:<budget_source_id> \
  --areas us,OCI \
  --rise-base-type forcast \
  --rise-base-month 1785513600000 \
  --start-month 1785513600000 \
  --end-month 1790784000000 \
  --metrics actual_rise_ratio,forecast_rise_ratio,diff_ratio \
  --page 1 \
  --size 100 \
  --format json
```
- `--rise-base-month`：基准月份第一天的毫秒时间戳。注意，这个字段需要用户单独指出，不能默认使用当前月份或者开始月份。

`--rise-base-type` 可选值为 `actual` 或 `forcast`，默认 `forcast` 。
- `actual`：以基准月实际 CD 为基准。
- `forcast`：以基准月预测 CD 为基准。


`--metrics` 默认全选，除非用户指定一个：
枚举值如下：
- `actual_rise_ratio`：当月实际 CD / 基准月 CD。
- `forecast_rise_ratio`：当月预测 CD / 基准月 CD。
- `diff_ratio`：实际/基准比例减预测/基准比例。

返回的三个比例数组按 `--start-month` 至 `--end-month` 的自然月顺序排列；对应的 `*_sum` 字段是接口返回的汇总比例。比例值可能是数值、数字字符串或百分数字符串，展示时应保留接口原值或明确说明换算方式，不要把 `0.1` 和 `10%` 混为同一原始格式。

## 原始请求体兼容

```bash
bytedcli babi budget cost-driver actual-budget list \
  --data '{"budget_area":"cn","budget_version":"2026-M08","cost_driver":[[1,1],[1,3],[4,2]],"area":["cn"],"start_month":1785513600000,"end_month":1790784000000,"metric":["forecast_count"],"page":1,"size":100}' \
  --format json
```
