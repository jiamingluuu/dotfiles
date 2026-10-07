# BABI Bill Insight 命令

## 先匹配报告配置

```bash
bytedcli babi bill insight data-range list
bytedcli babi bill insight report list \
  --data-range-type "<1|2|3>" --data-range "<stable-id>" \
  --statistic-period "<period>" --statistic-time-grading "<grading>" \
  --bill-amount-types "<0|1|2>" --limit 1000 --format json
bytedcli babi bill insight instance get --instance-id "<instance-id>"
```

`data_range_type`：`1=账号`、`2=团队`、`3=服务树`。报告期和基准期的 begin/end 必须成对提供。

`bill insight report list` 默认只返回当前服务端分页结果中 `report_type=6` 的通用洞察报告；
非 6 或缺少 `report_type` 的报告不会出现在输出中。

关联实例前必须先执行该命令，并从返回项中建立“已校验 `report_id` 集合”：

- `data_range_type` 必须一致，规范化后的 `data_range` 集合必须与目标对象集合完全相同；仅包含
  目标 ID、名称相似或父子对象命中都不能视为相同对象。
- `statistic_period`、`statistic_time_grading` 必须一致；对本次已经固定的
  `bill_amount_type`、`settlement_type`、`contain_instant_true_up`、
  `billing_range_filter_type`、`report_agg_type`、`areas` 和 `analysis_causes` 逐项比较。
  显式要求的字段缺失或不同即不匹配；列表类字段按集合比较。
- 禁止按报告名、返回顺序或“最接近”的配置选择。保留所有完全匹配项；没有完全匹配项时，
  明确记录“无匹配报告”，不得把其他报告的实例当作目标实例。

## 准备实例

`prepare` 默认只读：查报告与目标周期实例，返回精确匹配和候选写计划。不传 `--confirm-write` 不会创建或回溯。

```bash
bytedcli babi bill insight instance prepare \
  --data-range-type 3 --data-range "<node-id>" \
  --candidate-report-ids "<validated-report-id[,report-id...]>" \
  --report-time-begin "<begin-seconds>" --report-time-end "<inclusive-end-seconds>" \
  --base-time-begin "<begin-seconds>" --base-time-end "<inclusive-end-seconds>" \
  --statistic-period day --statistic-time-grading day
```

- 有完全匹配报告时，把全部已校验 `report_id` 传给 `--candidate-report-ids`；只接受
  `report_id` 属于该集合的 `exact_instances` 和候选。若出现集合外结果，忽略并保留诊断信息。
- 没有完全匹配报告时，可以只读运行 `prepare` 获取创建计划，但不得接受其已有报告实例或
  `re_calculate` 候选；需要生成报告时只能按写入安全流程显式选择 `report_modify`。
- Agent 构造参数时必须使用 Unix **秒级**时间戳；CLI 兼容毫秒只为承接旧调用，不是推荐口径。
- 四个时间边界都是**前闭后闭** `[begin, end]`。`end` 是目标周期最后一秒，禁止把下一周期
  起点作为前闭后开的结束值。
- 例如 `Asia/Shanghai` 的 `2026-07-16` 对比 `2026-07-09` 应传
  `1784131200..1784217599` 和 `1783526400..1783612799`；不得传
  `1784131200000..1784217600000` 或 `1783526400000..1783612800000`。
- 实例精确匹配会同时比较 `report_time_begin/end` 和 `base_time_begin/end`，任一边界差一秒
  都不能视为同一周期。
- 查找待匹配报告时携带 `report_type=6`，并在合并所有结果后再次强制过滤；只有
  `report_type=6` 的通用报告会进入实例匹配和候选选择。`--candidate-report-ids` 只补充
  通用报告，非 6 或缺少 `report_type` 的报告会被忽略。
- `exact_instance_found`：选择 `state=ready`；`pending` 轮询，`failed` 先排障。
- `candidate_ready`：检查候选与 `recommended_operation`，多候选用 `--selected-report-id` 消歧。
- 需要写入时读取 [写操作安全](writes.md)。

## 查询分析证据

```bash
bytedcli babi bill insight analysis overview --instance-id "<instance-id>"
bytedcli babi bill insight analysis contributors --instance-id "<instance-id>"
bytedcli babi bill insight analysis attribution-tree \
  --instance-id "<instance-id>" \
  --analysis-causes '[{"analysis_type":1,"analysis_cause_dims":["bytetree","cost_product","charge_item"]}]'
```

`statistic_period/compare_span` 不传或传 `auto` 时会从实例详情解析。需要创建工单、查询监控证据并回填完整归因结论时，加载 [babi-finops 指南](../../babi-finops/GUIDE.md)。
