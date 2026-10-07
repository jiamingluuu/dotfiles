# FinOps Insight 归因闭环

本流程适用于“成本异动归因”“成本劣化归因”“分析账单波动”和明确要求解释两期成本差异的任务。命中任一表述时，必须先关联或准备 released Insight 实例，不得仅查询普通账单明细后结束。执行前同时读取：

- [归因派生规则](attribution-derived-rules.md)
- [固定输出契约](attribution-output-contract.md)

## 0. 固定对象和时间口径

1. 用户明确说 BABI 账号、团队或服务树时，分别用 `account list`、`finops team search` 或 ByteTree 指南解析稳定 ID。
2. 只给普通业务名且主体不明确时，同时解析账号与服务树候选；两类同时命中时展示类型、ID、名称、路径并等待选择。
3. 固定 `data_range_type`：`1=账号`、`2=团队`、`3=服务树`。后续 Insight、工单、监控和报告不得改变主体。
4. 固定本期、基准期、时区、统计周期、结算口径和金额口径。“本月”必须先确定完整自然月或月初至今。
5. Insight 实例匹配与归因工单使用不同时间单位：`bill insight instance prepare` 的四个边界
   必须由 Agent 传 Unix 秒级、前闭后闭 `[begin, end]`；工单 create/update 的时间字段仍按
   命令约定传毫秒。禁止把工单的毫秒或前闭后开边界直接复用给 Insight。

## 1. 匹配报告配置并准备 released Insight 实例

加载 [babi-bill 指南](../../babi-bill/GUIDE.md)。必须先查询通用洞察报告配置，不能直接从 `instance prepare` 开始：

```bash
bytedcli babi bill insight report list \
  --data-range-type "<1|2|3>" --data-range "<stable-id>" \
  --statistic-period day --statistic-time-grading day \
  --bill-amount-types "<0|1|2>" --limit 1000 --format json
```

逐项检查每个返回报告，并形成“已校验 `report_id` 集合”：

- `report_type` 必须为 `6`；命令已过滤非 6 和缺失值，但仍不得自行放宽。
- `data_range_type` 必须一致，规范化后的 `data_range` 集合必须与目标对象集合完全相同；
  仅包含目标 ID、父子对象命中、名称相似都不算匹配。
- `statistic_period`、`statistic_time_grading` 必须与第 0 节固定值一致。
- 对已经固定的 `bill_amount_type`、`settlement_type`、`contain_instant_true_up`、
  `billing_range_filter_type`、`report_agg_type`、`areas` 和 `analysis_causes` 逐项比较；
  显式口径字段缺失或不同即不匹配，列表类字段按集合比较。
- 禁止选择第一项或最相似项。保留所有完全匹配的 `report_id`；没有完全匹配项时明确记录
  “无匹配报告”，不得使用其他报告已有实例或 `re_calculate` 候选。

然后只读查找实例；有完全匹配项时，把全部 `report_id` 传给 `--candidate-report-ids`：

```bash
bytedcli babi bill insight instance prepare \
  --data-range-type "<1|2|3>" --data-range "<stable-id>" \
  --candidate-report-ids "<validated-report-id[,report-id...]>" \
  --report-time-begin "<begin-seconds>" --report-time-end "<inclusive-end-seconds>" \
  --base-time-begin "<begin-seconds>" --base-time-end "<inclusive-end-seconds>" \
  --statistic-period day --statistic-time-grading day \
  --settlement-type 1 --limit 100 --format json
```

- 四个边界必须使用 Unix **秒级**时间戳和**前闭后闭**语义。单日 `end` 是当地时区
  `23:59:59`，禁止传下一日 `00:00:00`；CLI 兼容毫秒只为旧调用兜底，Agent 不得生成毫秒。
- `Asia/Shanghai` 下，`2026-07-16` 对比 `2026-07-09` 的正确边界分别是
  `1784131200..1784217599`、`1783526400..1783612799`。
- `release/released/success/succeeded` 归一为 `state=ready`，只有 ready 实例可进入正式归因。
- 只接受 `report_id` 属于已校验集合的 `exact_instances` 和候选；集合外结果必须忽略并保留
  诊断信息。多个已校验报告都存在 ready 实例时，展示报告 ID、名称和口径并等待选择。
- 没有完全匹配报告时，可以省略 `--candidate-report-ids` 只读获取创建计划，但不得接受命令
  返回的已有实例或 `re_calculate` 候选；需要创建时按写入安全流程显式选择 `report_modify`。
- `pending` 用 `bill insight instance get --instance-id` 有界轮询；`failed` 停止并报告错误与 `logId`。
- `candidate_ready` 先展示候选及 `recommended_operation`。需要 `report_modify` / `re_calculate` 时，按 [babi-bill 指南](../../babi-bill/GUIDE.md) 写白名单单独说明并取得授权。
- 不得为省事改查相邻日期或更换统计周期。

## 2. 只复用工单身份，不复用历史结论

先把问题规范化为固定字符串：`<正式对象名称> <当期> vs <基准期> 成本异动归因`。取得 `report_id` 和 `instance_id` 后，按主体一次性查询已有工单：

```bash
bytedcli babi finops attribution ticket list \
  --data-range-type "<1|2|3>" --data-range "<stable-id>" \
  --page-size 1000 --current-page 1 --format json
```

按 `ticket_id` 升序检查 `initial_question`、`reports[].report_id/instance_id` 和时间范围：

- 精确命中同一规范化问题和同一实例时，复用最小 `ticket_id`，禁止新建。
- 复用工单只代表复用 `ticket_id`、完整 Insight 关联和 Oncall 链接，不代表复用内容。
- `attribution_conclusion`、`attribution_conclusion_html`、`final_conclusion` 和 `related_owners`
  都可能被人工修改，不得作为本次即席分析的证据、根因输入或最终回复，也不得因其非空
  而结束任务。无论是否命中已有工单，下一步都必须执行第 3 节的完整 Insight 证据链。
- 工单列表只查询一次，不得为了提取历史结论重复执行 `ticket list`。只有进入第 7 节、
  准备更新现有工单时，才允许按 `ticket_id` 再精确读取一次以保留完整 Insight 关联；该次
  返回的历史结论字段仍不得进入 `report.json`。
- 只有没有精确命中时才进入创建；创建先 dry-run，再单独取得授权：

```bash
bytedcli babi finops attribution ticket create \
	--initial-question "<正式对象名称> <当期> vs <基准期> 成本异动归因" \
  --data-range-type "<1|2|3>" --data-range "<stable-id>" \
  --report-id "<report-id>" --instance-id "<instance-id>" \
  --base-time-begin "<base-begin-millis>" --base-time-end "<base-end-millis>" \
  --current-time-begin "<current-begin-millis>" --current-time-end "<current-end-millis>" \
  --confirm-write --dry-run --format json
```

用户确认后去掉 `--dry-run` 并保留 `--confirm-write`。每个对象 + 周期 + 实例只创建一次；命令结果不明时先恢复输出或重新 list，禁止重跑写操作。

仅当用户明确要求“查看历史归因结论”“返回已有工单结论”“不要重新分析”或“复用历史结果”
时，才进入历史内容读取模式并停止即席分析。此时必须在回复中标注 `ticket_id`、工单
`updated_at`（接口未返回则明确说明）以及“历史工单内容，非本次即席分析”，不得把历史
文本描述成当前 Insight 的实时结论。

创建或复用后，用同一个规范化问题和 `ticket_id` 生成稳定 Oncall URL：

```bash
bytedcli babi finops oncall url \
  --trigger-message "<正式对象名称> <当期> vs <基准期> 成本异动归因" \
  --attribution-ticket-id "<ticket-id>" --format json
```

## 3. 收集完整 Insight 证据

这是默认归因意图的必经步骤，不能被已有工单或已有结论短路。先保存当前 released 实例的
详情、分大区总览和异常贡献：

```bash
bytedcli babi bill insight instance get --instance-id "<instance-id>" --format json
bytedcli babi bill insight analysis overview --instance-id "<instance-id>" --format json
bytedcli babi bill insight analysis contributors --instance-id "<instance-id>" --format json
```

同时查询上涨和下降，默认 Top5，至少执行两条互补路径：

```bash
bytedcli babi bill insight analysis attribution-tree \
  --instance-id "<instance-id>" \
  --analysis-causes '[{"analysis_type":1,"analysis_cause_dims":["cost_product","bytetree","charge_item"]}]' \
  --fluctuation-change-types rise,fall --limit 5 \
  --max-depth 12 --max-nodes 10000 --service-tree-psm-depth 3 \
  --min-monthly-fluctuated-value 5000 --include-raw --format json

bytedcli babi bill insight analysis attribution-tree \
  --instance-id "<instance-id>" \
  --analysis-causes '[{"analysis_type":1,"analysis_cause_dims":["cost_product","charge_item","bytetree"]}]' \
  --fluctuation-change-types rise,fall --limit 5 \
  --max-depth 12 --max-nodes 10000 --service-tree-psm-depth 3 \
  --min-monthly-fluctuated-value 5000 --include-raw --format json
```

服务树汇总仍不闭合时补 `bytetree -> cost_product -> charge_item`。定点查询某个对象时使用 `target_filters` 并把剪枝阈值设为 0。

保存并检查：

- `node_count`、`request_count`、`truncated`、`errors`、`analysis_paths`；
- `tree` 用于递归关系，`flat` 用于 TopN 和跨路径收敛；
- 每个节点的 `id/name/full_name`、`main_contributor`、全部 `contributors`、当期/基准期/波动值；
- `truncated=true` 或 `errors` 非空时不得声称完全闭合。
- 将每次结果的 `analysis_paths` 中 `analysis_cause_dims`、`node_count/request_count/truncated/errors` 原样写入 `attribution_path_audits[]`；renderer 会拒绝缺少规定互补维度组合、截断或含错误的 v1 输入。

## 4. 核查 Platform 数据完整性

加载 [babi-platform 指南](../../babi-platform/GUIDE.md)。出现本期缺失、NaN、推量数变化、计费项整体异常，或用户要求监控证据时，对同向 Top 贡献商品分别覆盖基准期和本期：

```bash
bytedcli babi platform monitor alarm list \
  --entity-ids "<product-id>" --entity-types product \
  --monitor-item-keys report_measure_failed,report_measure_delay,report_measure_number \
  --start-bill-time "<begin-millis>" --end-bill-time "<end-exclusive-millis>" \
  --size 1000 --format json
bytedcli babi platform monitor measure_owner get --product-ids "<product-id>"
bytedcli babi finops lark user resolve --emails "<owner-email>"
```

- 商品 ID 必须来自 Insight，不用名称猜 ID。
- 命中只能解释对应商品和金额，不得泛化到整棵服务树。
- 未命中不能证明无业务异常。
- 责任人来源与 `action_object` 必须一致；归类责任人前单独确认。

## 5. 派生主因和责任主体

严格应用 [归因派生规则](attribution-derived-rules.md)：

1. 分开同向主因和反向抵消；反向项只解释净额。
2. 用互补路径确认共同大区、共同服务树、共同计费项和主因因子。
3. 计算深层叶子覆盖率；低覆盖率 raw 节点不得进入主链路。
4. 先判断数据质量门禁，再判断业务方/商品方责任。
5. BABI 账号补总体和逐商品单位 CD 成本判断，只展示波动幅度与判断，禁止输出 CD 原值。
6. 每个事件生成自己的 `root_causes[]` 和 `impact_scope_top5`，不得复用全局 Top5。

## 6. 生成固定 Markdown 和 HTML

按 [固定输出契约](attribution-output-contract.md) 填写 `babi_finops_attribution_v1`。`meta` 必须带时区、统计/结算/金额口径、`report_id`、`instance_id` 和 ready 状态；只填结构化事实，不手写 `结论/What happened/Why/How to resolve`。

```bash
bytedcli babi finops attribution report render \
  --input ./report.json \
	--reply-output ./final-reply.md \
  --markdown-output ./conclusion.md \
  --output ./report.html \
  --format json
```

命令返回：

- `input_sha256`：规范化证据指纹；
- `reply_sha256`：面向用户的精简固定回复指纹；
- `conclusion_sha256`：固定 Markdown 指纹；
- `reply_output_path`、`markdown_output_path` 和 `output_path`。

相同对象、时间口径和规范化证据的 `input_sha256` 相同时，`reply_sha256` / `final-reply.md` 与 `conclusion_sha256` / `conclusion.md` 必须分别逐字相同。禁止修改任一文件，禁止让模型二次润色或另写一版摘要。

## 7. 回填并复核

若准备更新现有工单，按 `ticket_id` 精确读取一次并只提取完整 Insight 关联等更新所需元数据；
不得把当前工单中的历史结论或历史负责人写入本次分析证据。然后 dry-run，单独取得更新授权：

```bash
bytedcli babi finops attribution ticket update \
  --ticket-id "<ticket-id>" \
  --attribution-conclusion-file ./conclusion.md \
  --attribution-html-file ./report.html \
  --insights '<完整现有-insights-json>' \
  --related-owners '<confirmed-owner-json>' \
  --confirm-write --dry-run --format json
```

确认后去掉 `--dry-run` 并保留 `--confirm-write`。更新后按 `ticket_id` 复读并校验 Markdown、HTML、Insight 关联和负责人。`--insights` 是全量覆盖；必须传入刚刚读取并保留的全部现有关联，漏传或只传本次单条关联都会丢数据。不要自动设置 `is_resolved=1`。

## 8. 最终回复

默认最终回复直接读取并输出本次即席分析生成的精简 `final-reply.md`，不把完整 7 段 `conclusion.md` 原样贴给用户，除非用户明确要求完整工单内容。历史工单文本不得替代该文件。命令失败时报告失败阶段、保留 `logId` / `RequestId` 和已有工单链接，不用自由文本伪造完整归因。

人工确认节点相互独立：主体消歧、Insight 写入、工单创建、责任人归类、本地覆盖、工单更新和解决状态，前一次确认不授权后一次写入。
