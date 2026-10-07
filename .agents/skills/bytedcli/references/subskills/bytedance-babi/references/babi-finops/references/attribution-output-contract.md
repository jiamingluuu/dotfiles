# 固定归因输出契约

`babi_finops_attribution_v1` 把“收集证据”和“生成文案”分离。智能体只填写事实，`bytedcli babi` 负责排序、措辞、精简用户回复、完整工单 Markdown 和 HTML；禁止智能体重新组织最终文案。

## 目录

1. [一致性边界](#一致性边界)
2. [输入 Schema](#输入-schema)
3. [固定文案](#固定文案)
4. [生成命令](#生成命令)
5. [回填和最终回复](#回填和最终回复)
6. [校验清单](#校验清单)

## 一致性边界

以下条件同时相同时，输出必须逐字一致：

- 分析对象类型、稳定 ID 和正式名称；
- 当期、基准期、时区、统计周期、结算口径、金额口径和同一个 released Insight 实例；
- 归因、监控、单位 CD 成本、负责人和链接证据；
- `schema_version=babi_finops_attribution_v1`。

renderer 会规范化受支持的数组顺序，返回：

- `input_sha256`：规范化证据指纹；
- `reply_sha256`：精简用户回复指纹；
- `conclusion_sha256`：生成 Markdown 指纹。

`input_sha256` 相同而 `reply_sha256` 或 `conclusion_sha256` 不同属于回归，测试必须失败。
完全相同的对象、当期、基准期和 `instance_id` 必须优先复用原工单的最小 `ticket_id`、
完整 Insight 关联和 Oncall 链接，但默认仍要基于当前 released Insight 实例重新收集证据并
生成本次 `input_sha256`。已保存的 `attribution_conclusion`、HTML、`final_conclusion` 和
`related_owners` 不是 renderer 输入，也不得替代本次生成的 `final-reply.md`。只有用户明确
要求查看或复用历史结果时才返回这些历史字段，并标注为历史工单内容而非本次即席分析。

## 输入 Schema

从 [attribution-report-v1.example.json](attribution-report-v1.example.json) 复制模板并替换全部占位符、示例 `0` 金额与审计计数。原始模板不能直接渲染。不要新增自由文本结论字段。

### 必填

- `schema_version`：固定为 `babi_finops_attribution_v1`。
- `meta.analysis_object`：正式对象名称。
- `meta.analysis_object_id`：稳定 ID。
- `meta.analysis_object_type`：`account`、`team` 或 `service_tree`。
- `meta.current_period` / `meta.base_period`：已经固定的本期和基准期。
- `meta.timezone` / `meta.statistic_period` / `meta.settlement_type` / `meta.amount_type`：完整 Insight 口径；时区必须是合法 IANA 名称，例如 `Asia/Shanghai`。
- `meta.report_id` / `meta.instance_id` / `meta.insight_state`：必须指向同一个 ready/released Insight；renderer 将 ready 同义状态归一为 `ready`。
- `attribution_path_audits[]`：至少包含 `cost_product -> bytetree -> charge_item` 与 `cost_product -> charge_item -> bytetree` 两条互补 `analysis_cause_dims`；每条必须有正数 `node_count/request_count`，且 `truncated=false`、`errors=[]`。
- `events[]`：至少一个事件；每个事件必须有日期/标题、非零数值金额和至少一条 `root_causes[]`。

### `events[]`

- `status=confirmed` 只用于 released Insight 且原因已由证据闭合；否则使用 `pending`。
- `amount` 是用于排序和占比计算的数值，单位固定为“万”。
- `amount_text/rate_text/current_cost_text/baseline_cost_text` 是最终展示值，必须提前换算并带单位。
- `root_causes[]` 是事件级 Why，按 [归因派生规则](attribution-derived-rules.md) 生成。
- `details[]` 是异常闭环、同向 Top5 和反向 Top5 的数据来源。
- `event_url` 没有实际链接时留空；renderer 固定输出“未绑定，证据为当前洞察实例”。

### `root_causes[]`

- `cause`：已证实原因或明确标记待复核的原因。
- `amount/amount_text`：该原因能解释的金额。
- `share_text`：可省略；省略时 renderer 用原因金额 / 事件金额计算绝对占比。
- `event_label/event_url`：具体事件及链接。
- `impact_scope_top5`：只包含本原因的同口径 Top5；没有时使用空数组。
- `action/owner_role`：直接承接原因和 `action_object`。

### `details[]`

- `object` 使用正式名称、稳定 ID 和完整路径；商品尽量补计费方式和产品线。
- `cause_path` 必须是门禁后的业务链路，不是最深 raw path。
- `owners` 只放实际查询结果；没有时用空数组，renderer 固定写“负责人未返回”。
- 同向和反向由 `event.amount` 与 `detail.amount` 符号决定，不靠模型写标签猜测。
- BABI 账号逐商品填写 `unit_cd_cost_assessments`；不得包含 CD 原值。
- BABI 账号的总体 `meta.unit_cd_cost_assessments` 必填；每个同向 Top 成本商品必须有匹配的 `details[]`、稳定商品 ID 和逐商品单位 CD 成本判断，否则 renderer 拒绝生成 confirmed 文案。
- 可用的单位 CD 判断必须有 `indicator/summary/status/driver`；`status` 仅允许“正常/异常/未判断”。不可用时设置 `available=false` 并填写 `reason`，不能用空对象占位。

### 表格与证据

- `dimension_tables[key=area_summary]` 生成“分大区汇总”。
- `dimension_tables[key=data_quality]` 生成“监控报警与数据完整性”。
- `attribution_path_records` 只放实际执行的路径。
- `attribution_path_audits` 从每次 `attribution-tree` 返回的 `analysis_paths/node_count/request_count/truncated/errors` 填写，不能手工写成功值。
- `evidence` 放剪枝、截断、接口限制、监控边界和 logId 等补充证据。

## 固定文案

renderer 从同一输入生成两个 Markdown。`final-reply.md` 只包含第一屏精简闭环：

```markdown
[拉起 Oncall](<oncall_url>)

结论：...
What happened：...
Why：...
How to resolve：...
```

`conclusion.md` 包含相同摘要块和以下完整工单证据，固定顺序和标题：

```markdown
[拉起 Oncall](<oncall_url>)

结论：<对象>在<当期>较<基准期>成本<上涨/下降><波动>，幅度<幅度>；主因是<原因>，当前由<责任主体>优先处理。
What happened：<当期/基准期/波动/单位 CD 成本>。
Why：
1. <事件>
   - 原因结论（已有）：<原因、金额、占比>。
   - 具体事件（+链接）：<链接或固定兜底>。
   - 影响范围 Top5（如有）：<本事件 Top5 或固定兜底>。
How to resolve：<处置动作>。

1. What happened
2. Why - 主因拆解
3. 异常明细闭环
4. 分大区汇总
5. Top5 同向贡献商品 + 下钻
6. Top5 反向贡献商品 + 下钻
7. 监控报警与数据完整性
附录：证据与链接
```

固定兜底：

- 无事件链接：`未绑定，证据为当前洞察实例`。
- 无事件 Top5：`暂无可分摊 Top5`。
- 无负责人：`负责人未返回`。
- 无大区：`暂无可分摊大区数据`。
- 无监控：`未发现已绑定的数据完整性证据；未命中监控不等于没有业务异常，需继续按主贡献对象复核`。

模型不得替换标题、改变顺序、合并 Why、删掉反向贡献或另写一个“更简洁版本”。

## 生成命令

首次生成使用新路径，避免意外覆盖：

```bash
bytedcli babi finops attribution report render \
  --input ./report.json \
	--reply-output ./final-reply.md \
  --markdown-output ./conclusion.md \
  --output ./report.html \
  --format json
```

需要机器读取文案时使用：

```bash
bytedcli babi finops attribution report render \
  --input ./report.json \
	--return-reply --return-markdown \
  --format json
```

- `--reply-output` / `--return-reply` / `--markdown-output` / `--return-markdown` 只接受 v1 schema。
- 已有文件只有用户确认后使用 `--force`。
- HTML 的“固定结论文案”与 Markdown 来自同一次 composer。
- legacy JSON 仍可只生成旧 HTML，但不具备固定结论文案保证。

## 回填和最终回复

1. 工单的 `attribution_conclusion` 使用 `conclusion.md` 原文。
2. 工单的 `attribution_conclusion_html` 使用同次生成的 `report.html`。
3. 最终回复读取本次即席分析生成的精简 `final-reply.md` 原文；默认不粘贴完整 7 段工单证据，不加前言、改写或另一套表格，也不读取历史工单结论代替它。
4. 保存 renderer 返回的三个 SHA；复算时先比 `input_sha256`。
5. 相同输入需要再次生成时使用新临时路径或得到覆盖授权，不手工复制后修改。

## 校验清单

生成前：

- 主体和时间口径已冻结；实例 ready。
- 同向/反向 Top5、互补路径、覆盖率和数据质量门禁已完成。
- BABI 账号总体和逐商品单位 CD 成本判断齐全且无原值。
- `root_causes[]` 与 `details[]` 来自同一版证据。

生成后：

- `input_sha256`、`reply_sha256`、`conclusion_sha256` 非空。
- Markdown 与 HTML 都包含“原因结论（已有）/具体事件（+链接）/影响范围 Top5”。
- 金额单位、正负号、当期/基准期没有颠倒。
- 工单回填使用 `conclusion_sha256`，最终回复使用同次生成的 `reply_sha256`；两者的 `input_sha256` 必须相同。
