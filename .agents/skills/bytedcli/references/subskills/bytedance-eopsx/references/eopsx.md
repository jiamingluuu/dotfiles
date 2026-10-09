# EOpsX Domain Reference

EOpsX（电商运维）平台 9 个子域的方法映射、字段字典、枚举码表与 jq 路径。所有命令通过 `bytedcli eopsx <domain> <cmd>` 调用。示例中的 PSM、用户名、ID、URL 均为占位值（`demo-*` / `example.*`），实际使用请替换为真实值。

## 公共约定

- **认证**：复用 bytedcli 全局 ByteCloud 登录（`bytedcli auth login`），命令自动注入 `x-jwt-token`。固定头 `X-Call-Source: byted-cli`。
- **传参格式**：字符串/整型直传；列表用逗号分隔（如 `--psm-list a,b`）或 `--body-string` 里写 JSON array；对象字段用 `--body-string '<json>'` 整体透传。CLI 有专用语义枚举 option 时传枚举名并由 CLI 映射；JSON/body 内的后端字段传数值编码。
- **`--region`**：默认 `cn`。`limit` 域使用独立的 `--region-code <n>` 过滤后端数字 region code，无默认。
- **分页**：统一使用 `--page`/`--page-size`。`event homepage` 会把 `--page-size` 映射为后端 `size`；BCP 两个列表命令会把 `--page` 映射为后端 `page_number`。
- **写操作**：`bcp` / `risk` 的写命令默认 dry-run，必须 `--yes` 提交。
- **空结果不算成功**：结合 `total` / 列表长度判断；输出建议用 `字段中文名(field_name)` 形式。

---

## meta — 元数据 / CMDB / 链路（5 命令，只读）

| 子命令                     | 后端方法                 | HTTP | path                                         | 用途                                             |
| -------------------------- | ------------------------ | ---- | -------------------------------------------- | ------------------------------------------------ |
| `get-biz-line-node-tree`   | GetRiskBizLineTree       | GET  | `/risk/biz_line/node_tree`                   | 电商业务线树（无参）                             |
| `get-service-tree-nodes`   | LoadRiskTree             | GET  | `/risk/tree/nodes`                           | 全量风险对象树（无参）                           |
| `search-arch-scope-object` | SearchArchScopeObjectRaw | POST | `/arch/object/search_scope_object_raw`       | 服务对象元数据（ES 原始文档）                    |
| `search-arch-chain`        | SearchArchChain          | POST | `/arch/link/dependency/arch_chain/search`    | 链路元数据列表（`--service-tree-id-paths` 必填） |
| `search-arch-edge-info`    | SearchArchEdgeInfoRaw    | POST | `/arch/dependency/search_arch_edge_info_raw` | 调用对/边（ES 原始文档）                         |

**关键字段与响应**

- `get-biz-line-node-tree` → `data[].node.info`：`biz_line_id`、`name`、`tree_paths`（名称路径）、`service_tree_id_paths`（ID 路径）、`biz_id_path`、`name_path`；`children` 递归。
- `get-service-tree-nodes` → 单根 `data`：`id`（风险对象树 ID）、`name`、`byte_tree_id`（Bytetree 原始 ID）、`children`；无 id_path，需遍历拼接。
- `search-arch-*-raw` → `data`（ES `source_json` 列表）、`total`、`has_more`。

**枚举码表**

- **filter_op（FilterOperateType）**：1 Equal / 2 NotEqual / 3 In / 4 NotIn / 5 Like / 6 NotLike / 7 GreaterThan / 8 GreaterThanEqual / 9 LessThan / 10 LessThanEqual / 17 IsEmpty / 18 IsNotEmpty
- **scope_type**：1 Service / 2 Method / 3 DB / 4 DBTable / 5 SQL / 6 Redis / 7 RedisKey / 8 ES / 9 ESIndex / 10 ESQuery / 11 MQ / 12 MQProducer / 13 MQConsumer / 14 MQCluster / 15 Abase
- **ServiceType**：1 TCE / 2 FaaS / 3 CronJob / 4 MySQL / 5 Redis / 6 ES / 7 MQ
- **CallPairType**：1 Four（四元组）/ 2 Six（六元组）
- **DependType（强弱依赖）**：-2 未调用 / -1 弱依赖 / 0 未标记 / 1 强依赖
- **DependencyMarkStatus**：0 未标记 / 1 无需人工确认 / 2 待人工确认 / 3 人工确认完成
- **DependencyMarkSource**：1 人工 / 2 演练 / 3 Argos / 4 AIME / 5 其他 AI

**jq / 用法要点**

- 服务树路径必须用 **ID 路径**：名称 `|电商|业务平台|商品中心|商品发布|demo.service.api` → ID `|25|702118|702141|762639|29355`（示例 ID 为占位）。
- nested 查询需带 `nested_path`（如 `chains`、`mysql_extra.cpu_idle_cn`、`redis_extra.cpu_used_cn`、`upstream_services`、`timeout`、`limit.rate_limit`）。
- ES 派生指标：MySQL `cpu_idle` → CPU 利用率 = `100 - idle`；Redis `cpu_used` 直接用；`timeout` 空按默认 `conn_timeout_ms=50` / `rpc_timeout_ms=1000`；`0` 值可能不可靠。
- zone 口径：`CN`/`China-North`=华北、`China-East`=华东、`China-North6`=华北6。
- 业务域串联：`get-biz-line-node-tree` 拿 `service_tree_id_paths` → 传入 `search-arch-chain --service-tree-id-paths`；路径前缀去重合并。

---

## alarm — 监控告警（4 命令，只读）

`event-list` 查询告警事件；`list-tag-meta` / `get-tag-meta` / `tag-search` 见下文「alarm-tag」小节。

| 子命令       | 后端方法       | HTTP | path                                     |
| ------------ | -------------- | ---- | ---------------------------------------- |
| `event-list` | AlarmEventList | POST | `/ops/api/event_center/alarm/event_list` |

**入参**（`--page`/`--page-size` 必填）：`--start-timestamp`/`--end-timestamp`（秒级，默认最近 1h）、`--service-tree-path-list`、`--psm-list`、`--alarm-level-list`、`--alarm-status-list`、`--order-by`（`event_create_time`\|`last_notice_time`）、`--order`（asc\|desc）。更多平台/类型过滤用 `--body-string`（`alarm_platform_list`、`alarm_type_list`、`rule_id_list`、`user_receiver_list`、`lark_group_receiver_names` 等）。

**响应**：`alarm_list`（list<AlarmEventRuleGroup>，下钻 `.alarm_event_list`）、`total`、`statistics`（`total_alarm_count`/`pending_count`/`processing_count`/`recovered_count`/`ack_rate`/`mttr_seconds`）。

**枚举码表**

- **alarm_platform_list**（默认 `["AlarmEventArgos"]`）：`AlarmEventArgos`（argos）/ `AlarmEventKepler`（kepler）/ `ArgosDutyEvent`（Argos Duty）/ `EmergencyEventGoC`（GOC）。
- **alarm_level_list**（与平台强相关，不跨平台混传）：Argos → `critical`/`warning`；Kepler → `L1`/`L2`/`L3`/`L4`；GoC → `P0`/`P1`/`P2`/`P3`/`P4`/`notice`。
- **alarm_status_list**（默认不传，优先中文值）：`持续中`（未恢复）/ `处理中`（跟进中）/ `已恢复`。
- **alarm_type_list**（组件叶子值，非平台）：RMQ→`InfMQRocketMQ`、BMQ→`InfMQKafka`、Redis→`InfStorageRedis`、MySQL→`InfStorageMySQL`、Abase→`InfStorageAbase`、ByteFaas→`InfCalcByteFaas`；应用类 `SvcErrLog`/`SvcAppE2EQPS`/`SvcAppE2ESLA`/`SvcAppE2ERT`/`SvcRuntimePanic`/`SvcRuntimeCPU` 等。

**jq / JSON Path**

- 统计：`$.statistics.total_alarm_count` / `.recovered_count` / `.processing_count` / `.pending_count`
- 列表：`$.alarm_list[*].event_name`（标题）/ `.alarm_level` / `.alarm_platform_name` / `.alarm_status` / `.event_create_time`（开始）/ `.event_end_time`（恢复，空=未恢复）/ `.last_notice_time`
- `extra`（JSON 字符串，需先反序列化）：`$.mark_rca_accurate`、`$.mark_alarm_accurate`（1 有效/0 噪音）、`$.callback_type`、`$.lark_group_id`、`$.rca_flow_result.alarm_summary`（归因结论）
- 业务错误码：`40302`=飞书授权缺失（用群名反查 chat_id 时，回传 `response_headers.Auth_url`）；`40005`=通用业务错误。

---

## event — 变更事件中心（2 命令，只读）

| 子命令        | 后端方法      | HTTP | path                                             | 用途           |
| ------------- | ------------- | ---- | ------------------------------------------------ | -------------- |
| `homepage`    | EventHomepage | POST | `/ops/api/event_center/event/query`              | 变更事件列表   |
| `search-info` | SearchInfo    | POST | `/ops/api/event_center/frontend_view/searchInfo` | 视图名→id 搜索 |

**入参**（`homepage`）：`--start-timestamp`/`--end-timestamp`（默认 1h）、`--page`/`--page-size`（后端 `size`≤500）、`--psm-list`、`--service-tree-path-list`、`--user-name`、`--event-type-list`（数字）。更多过滤用 `--body-string`（`department_list`、`region_list`、`keywords`、`only_upgrade` 默认 true、`change_event_only` 默认 true、`event_filter`）。

**响应**：`event_info_list`（`event_id`/`event_psm`/`event_type`/`event_user`/`service_tree`/`event_stage_info_list`）、`total`、`link`。

**枚举码表**

- **EventType 高频**（默认 `[1,2,7,9,10,11,17,18,31,32,33,35,38,39,40,48,49,50,344]`）：1 Tce / 2 Tcc / 7 Libra / 9 Tlb / 10 Neptune / 11 ByteFaas / 17 Agw / 18 MeshPlatform / 31 Mysql / 32 Redis / 33 Abase / 35 Rmq / 40 BMQ / 48 ES / 49 ByteSet / 50 Lego / 344 Fornax。
- **EventSubType 高频**：Tce 1001 服务升级/1002 更新集群/1008 回滚工单；Tcc 2001 发布配置/2004 回滚配置；Neptune 10004 单实例限流/10005 简单集群限流/10012 熔断。
- **SearchType**：1 PageName / 2 PageAddress / 3 Btm / 4 BizLine / 5 SubDomain（视图搜索固定传 5）。
- **event_filter**：形如 `[{"key":"bid","value":["ecom"],"op_type":1}]`，`value` 必须数组；OpType：1 In / 2 Equals / 3 HasPrefix / 4 HasSuffix / 5 Contains。

**用法要点**：空结果三段法——先 `--page/--page-size`，再加时间窗，再逐步加 `--service-tree-path-list`/`--psm-list`/`--user-name`。

---

## fatal — 稳定性度量（3 命令，只读）

| 子命令                        | 后端方法                 | HTTP | path                                | 用途                          |
| ----------------------------- | ------------------------ | ---- | ----------------------------------- | ----------------------------- |
| `search-stability-summary`    | SearchStabilitySummary   | POST | `/arch/portal/stability/summary`    | 事故数&应急效率&业务 SLA 总结 |
| `search-stability-sla-detail` | SearchStabilitySLADetail | POST | `/arch/portal/stability/sla_detail` | 业务 SLA 明细列表             |
| `search-stability-detail`     | SearchStabilityDetail    | POST | `/arch/portal/stability/detail`     | 事故数&应急效率核心指标明细   |

**入参**：`--condition '<json>'`（TopCondition，对象含数组，推荐整体传）、`--compare-type`（summary/detail 用）。

**枚举码表（全数值）**

- `condition.period`（PoPeriodType）：1 年 / 2 季 / 3 月 / 4 半年
- `condition.period_value`：与 period 配对——年 `2026`、季 `2026-Q1`、月 `2026-01`（**成对必给，缺则报 `unsupported period type: 0` 或 `未能提取到年份`**）
- `condition.issue_type`（list）：1 服务稳定性 / 2 资损 / 3 安全
- `condition.client_type`（list）：1 前端 / 2 服务端 / 3 客户端
- `compare_type`：1 环比（MOM）/ 2 同比（YOY）
- SLAPriority（响应）：1 L0 / 2 L1 / 3 L2 / 4 L3

**响应**：`data.overall_perform`/`data.ecom_sla`（summary）；`data.to_b_sla[]`/`to_c_sla[]`（sla_detail，含 link/priority/current_sla）；`data.overall_issue`/`overall_efficiency`/`issues`/`efficiencies`（detail）。

---

## alarm-tag — 应急标签元信息与检索（3 命令，只读）

上述命令位于 `eopsx alarm` 命令组下（与 `event-list` 同级）。

| 子命令          | 后端方法                             | HTTP | path                                     | 用途                         |
| --------------- | ------------------------------------ | ---- | ---------------------------------------- | ---------------------------- |
| `list-tag-meta` | ListAlarmTagFields                   | POST | `/ops/ts_facade/alarm_tag/field/list`    | 查询标签字段元信息集合       |
| `get-tag-meta`  | GetAlarmTagField                     | POST | `/ops/ts_facade/alarm_tag/field/get`     | 查询单个标签字段元信息详情   |
| `tag-search`    | ListAlarmTagFields + SearchAlarmTags | POST | `/ops/ts_facade/alarm_tag/field/list` 等 | 检索应急标签并返回字段元信息 |

### 应急标签字段元信息

```bash
# 查询字段元信息集合
bytedcli --json eopsx alarm list-tag-meta \
  --field-level L1 --storage-target event --only-enabled

# 查询单字段详情
bytedcli --json eopsx alarm get-tag-meta --field-code event_status
```

- `list-tag-meta` 调用 ListAlarmTagFields；支持 `--field-level L1|L2|L3`、`--storage-target`、`--only-enabled`、`--only-meta`。后端一次性返回全量、无分页，JSON 输出为 `{fields, current_count, has_more}`（`has_more` 恒为 `false`）。
- `get-tag-meta --field-code <code>` 调用 GetAlarmTagField，列表过滤项不参与详情请求；JSON 输出为 `{field}`，未命中时 `field` 为 `null`。

### 应急标签检索

`tag-search` 是组合命令：先查询完整字段元信息并在本地校验输入，再执行标签检索。任一步失败都会整体报错，不返回部分结果。

```bash
bytedcli --json eopsx alarm tag-search \
  --field event_level --field root_cause \
  --filters-json '[{"field":"event_level","op":"in","values":["P0","P1"]}]' \
  --record-status confirmed \
  --page 1 --page-size 20
```

- `--field <code>`：必填，可重复或逗号分隔；控制返回字段。
- `--filters-json`：筛选数组，元素为 `{"field":"<code>","op":"<operator>","values":["..."]}`。多个条件按 AND 组合。
- 操作符：`eq`、`ne`、`in`、`not_in`、`gt`、`gte`、`lt`、`lte`、`like`、`exists`、`not_exists`。`exists/not_exists` 不传 values，`in/not_in` 可传多个值，其余操作符传一个值。
- 可选范围：`--event-uid`、`--record-status`、`--tag-version` 均可重复或逗号分隔；`--start-time/--end-time` 是 Unix 毫秒。
- 默认只查当前版本；`--include-history` 包含历史版本。`--tag-version` 指定版本时由后端版本过滤优先。
- JSON 结果中的 `fields` 只包含返回字段和筛选字段的并集；`items[].values.<code>` 同时提供解析后的 `value`、原始 JSON 字符串 `raw` 和 `locked`。

#### `process_timeline` / `extern_process_timeline`

两个字段解码后均为时间线节点数组。`process_timeline` 表示本事件处理过程，`extern_process_timeline` 表示外部问题处理过程。

每个节点固定包含：

| 字段            | 含义                                   |
| --------------- | -------------------------------------- |
| `node_time`     | 节点时间，格式为 `YYYY-MM-DD HH:mm:ss` |
| `node_operator` | 操作人或来源标识                       |
| `category`      | 节点类型，见下表                       |
| `content`       | 节点内容                               |
| `source`        | 节点信息来源，见下表                   |

`source` 映射：

|  值 | 来源       |
| --: | ---------- |
|   1 | 群聊记录   |
|   2 | 会议逐字稿 |
|   3 | 复盘文档   |

`category` 映射：

|  值 | 含义             |
| --: | ---------------- |
|   1 | 故障发现         |
|   2 | 应急响应或升降级 |
|   3 | 止损或限流降级   |
|   4 | 根因定位或确认   |
|   5 | 恢复             |
|   8 | 影响范围         |

查询与展示边界：

- CLI 已在每个节点补充 `category_label` / `source_label`（按上表映射，未知枚举为 `null`）；直接读取该字段即可。
- 保留后端返回的节点、顺序、时间、操作人和内容。
- 不与 `detected_at`、`recovered_at` 或 `extern_*` 字段做一致性检查。
- 不判断节点内容是否符合其 category，不推断缺失节点，也不修正、合并或重新分类。

---

## limit — 限流子配置（2 命令，只读）

> 注意：`--region-code <n>` 是数字 region code 过滤，无默认；非控制面 region。

| 子命令                   | 后端方法             | 用途             | 必填        |
| ------------------------ | -------------------- | ---------------- | ----------- |
| `query-cluster-sub-conf` | 集群限流子配置分页   | 集群维度限流查询 | `--tce-psm` |
| `query-custom-sub-conf`  | 自定义限流子配置分页 | 自定义限流查询   | `--tce-psm` |

**入参**：`--module-id`、`--source-psm`、`--source-cluster`、`--cluster`、`--method`、`--limit-status`、`--caller-region`、`--callee-region`（cluster）；`--resource-name`、`--env`、`--accurate-search-resource-name`、`--dfl-rule-name`、`--is-cluster-limit`、`--is-dynamic-feature-limit`（custom）；均支持 `--page`/`--page-size`/`--body-string`。

---

## voc — VOC 客诉感知预警（5 命令，只读）

> 跨两个 host：VocAlertService 走 `https://ehome.bytedance.net`；VocAgentService 走 `https://ecom-ai.bytedance.net`。

| 子命令              | 后端方法           | HTTP | path                                    | 必填                                 |
| ------------------- | ------------------ | ---- | --------------------------------------- | ------------------------------------ |
| `search-event-page` | SearchEventPage    | POST | `/ops/api/voc/event/page`               | `--start-time`、`--end-time`（秒级） |
| `get-event-detail`  | GetEventDetail     | GET  | `/ops/api/voc/event/detail`             | `--event-id`                         |
| `query-alert-rules` | QueryVocAlertRules | POST | `/ops/api/voc/alert/rules`              | —                                    |
| `get-agent-list`    | GetAgentList       | GET  | `/api/custom-issue-insight/list`        | `--platform`                         |
| `get-agent-detail`  | GetAgentDetail     | GET  | `/api/custom-issue-insight/find-detail` | `--id`                               |

**入参**（`search-event-page`）：`--page`/`--page-size`、`--level`、`--biz-line`、`--event-type`、`--event-scene-path`、`--event-ids`、`--event-name`、`--time-window`、`--alert-rule-name`、`--agent-name`、`--ticket-category`、`--agent-id`。

**枚举码表**

- `level`：P0/P1/P2/P3/P4/Notice/未定级
- `event_type`（客诉分类）：0 未标记 / 1 Bug / 2 热点 case / 3 事故
- `biz_line`（客诉分类）：0 商服 / 1 达服 / 2 消费者
- `time_window`：`1h` / `5m`；`sort.key`：`last_alert_time` / `feedback_cnt`
- VocAlertRuleStatus：1 启用 / 2 禁用

**用法要点**：`get-agent-list` 一次返回约 650 条无分页，拿到后本地 `jq` 按 `name`/`tree_node_name`/`owner_names` 过滤；事件详情主键 `event_id`，agent 详情主键 `id`。

---

## sla — 链路 SLA（16 命令，只读）

| 子命令                           | 后端方法                    | HTTP | path                                           |
| -------------------------------- | --------------------------- | ---- | ---------------------------------------------- |
| `search-link-list`               | SearchLinkList              | POST | `/arch/link/search_link_list`                  |
| `search-slo-config-list`         | SearchSloConfigList         | POST | `/arch/link/slo/search`                        |
| `get-biz-link-detail`            | GetBizLinkDetail            | POST | `/arch/link/overview/biz/link_detail`          |
| `get-biz-sla-detail`             | GetBizSlaDetail             | POST | `/arch/link/overview/biz/sla_detail`           |
| `get-biz-sla-metrics`            | GetBizSlaMetrics            | POST | `/arch/link/overview/biz/sla_metrics`          |
| `get-biz-sla-rank`               | GetBizSlaRank               | POST | `/arch/link/overview/biz/sla_rank`             |
| `search-biz-downstream-link`     | SearchBizDownstreamLink     | POST | `/arch/link/overview/downstream/link/search`   |
| `get-biz-downstream-sla-metrics` | GetBizDownstreamSlaMetrics  | GET  | `/arch/link/overview/downstream/sla_metrics`   |
| `get-biz-downstream-sla-rank`    | GetBizDownstreamSlaRank     | GET  | `/arch/link/overview/downstream/sla_rank`      |
| `search-unavailable-event`       | SearchUnavailableEvent      | POST | `/arch/link/search_link_unavailable_event`     |
| `get-unavailable-event-detail`   | GetUnavailableEventDetail   | GET  | `/arch/link/get_link_unavailable_event_detail` |
| `unavailable-event-rca-analysis` | UnavailableEventRcaAnalysis | POST | `/arch/link/unavailable_event/rca_analysis`    |
| `search-ticket-list`             | SearchTicketList            | POST | `/arch/workbench/data_measure/search`          |
| `get-ticket-distribute`          | GetTicketDistribute         | POST | `/arch/workbench/data_measure/distribute`      |
| `query-gw-approval-records`      | QueryGwApprovalRecords      | POST | `/arch/workbench/approval/records`             |
| `get-approval-distribute`        | GetApprovalDistribute       | POST | `/arch/workbench/approval/distribute`          |

**共用入参**：`--biz-line-id-path`、`--period`、`--period-value`、`--sub-period`、`--sub-period-count`、`--page`/`--page-size`、`--body-string`；`unavailable-event-*` 用 `--event-id`。

**枚举码表（全数值）**

- **SlaPeriodType（`period`/`sub_period`）**：1 季度 / 2 年 / 3 月 / 4 双周 / 5 周 / 6 日 / 7 日期范围 / 8 自定义周 / 9 自定义双周
- **ObjectType**：1 自身（Link）/ 2 下游（LinkPair）
- **TicketType（`source_type`）**：1 稳定性 / 2 成本 / 3 架构效率 / 4 风险 / 5 特性 / **6 SLA** / 7 链路
- **EntityType**：1 工单 / 2 专项 / 3 巡检项 / **4 SLA 不可用事件** / 5 链路 SLA 对象 / 6 服务 / 7 链路 / 8 四元组 / 9 审批记录 / 10 六元组
- **ApprovalType**：1 完成处理 / 2 误报 / 3 屏蔽 / 4 暂缓 / 5 豁免 / 6 自动豁免 / 7 链路 SLA 不可用暂缓 / 8 变更服务等级
- **LinkLevel**：1 L0 / 2 L1 / 3 L2 / 4 L3；**LinkType**：1 HTTP / 2 RPC；**SlaPassStatus**：1 达标 / 2 不达标；**ApprovalStatus**：1 待审批 / 2 已通过 / 3 已驳回 / 4 已取消

**用法要点**：`biz_line_id_path` 用 ID path，名称 `电商-商品中心-发布` → `1-102-10203`（示例）；SLA 场景固定 `source_type=6` + `entity_type=4`。

---

## bcp — 业务异常检测（23 命令：14 读 + 9 写）

**只读（14）**

| 子命令                            | 后端方法                   | HTTP | path                                 | 必填                                                    |
| --------------------------------- | -------------------------- | ---- | ------------------------------------ | ------------------------------------------------------- |
| `get-source`                      | GetSource                  | GET  | `/bcp3/source/detail`                | `--source-id`                                           |
| `query-source-list`               | QuerySourceList            | POST | `/bcp3/source/list`                  | `--page`、`--page-size`                                 |
| `get-hsap-source-delay-info`      | GetHsapSourceDelayInfo     | POST | `/bcp3/source/hsap_delay_info`       | `--checker-id`                                          |
| `get-checker-detail`              | GetCheckerDetail           | POST | `/bcp3/checker/detail`               | `--checker-id`                                          |
| `query-checker-list`              | QueryCheckerList           | POST | `/bcp3/checker/list`                 | `--page`、`--page-size`                                 |
| `get-sql-model-info`              | GetSqlModelInfo            | POST | `/bcp3/checker/sql_model_info`       | `--checker-id`                                          |
| `get-nrt-snapshot-dry-run-result` | GetNrtSnapshotDryRunResult | POST | `/bcp3/checker/dry_run_result`       | `--executor-task-id`、`--checker-id`                    |
| `search-execute-record`           | SearchExecuteRecord        | POST | `/bcp3/execute/search`               | `--rule-id`、`--start-time`、`--end-time`               |
| `search-diff-record`              | SearchDiffRecord           | POST | `/bcp3/diff_record/search`           | `--rule-id`、`--start-time`、`--end-time`（仅近 10 天） |
| `get-compensate-record`           | GetCompensateRecord        | POST | `/bcp3/compensate/list`              | `--checker-id`、`--execute-record-id`                   |
| `get-alarm-detail`                | GetAlarmDetail             | GET  | `/bcp3/alarm/detail`                 | `--alarm-record-id`、`--checker-id`                     |
| `search-alarm-record`             | SearchAlarmRecord          | POST | `/bcp3/alarm/search`                 | `--rule-id`、`--start-time`、`--end-time`               |
| `get-recommendation-task`         | GetRecommendationTask      | GET  | `/recon_mng_api/recommendation/task` | `--hql`                                                 |
| `get-fsm-transited-status`        | GetFSMTransitedStatus      | GET  | `/bcp3/fsm/status`                   | —                                                       |

**写（9，默认 dry-run，需 `--yes`）**

| 子命令                        | 后端方法               | HTTP | path                                   | 必填                                                                                            |
| ----------------------------- | ---------------------- | ---- | -------------------------------------- | ----------------------------------------------------------------------------------------------- |
| `submit-nrt-snapshot-dry-run` | CheckNrtSnapshotDryRun | POST | `/bcp3/checker/check_snapshot_dry_run` | `--checker-id`、`--execute-record-id`                                                           |
| `batch-update-diff-record`    | BatchUpdateDiffRecord  | POST | `/bcp3/diff_record/update`             | `--checker-id`、`--operator`；`--diff-record-ids`/`--search-param` 至少一个，同时提供时前者优先 |
| `execute-batch-compensate`    | BatchCompensate        | POST | `/bcp3/compensate/batch`               | `--checker-id`、`--execute-record-id`、`--diff-record-ids`、`--user-name`                       |
| `execute-instance-compensate` | InstanceCompensate     | POST | `/bcp3/compensate/instance`            | `--checker-id`、`--execute-record-id`、`--user-name`                                            |
| `create-checker`              | CreateChecker          | POST | `/bcp3/checker/create`                 | `--user-name`（+`--checker` JSON）                                                              |
| `batch-update-checker`        | BatchUpdateChecker     | POST | `/bcp3/checker/batch_update`           | `--checker-ids`、`--user-name`                                                                  |
| `ascribe-alarm`               | AscribeAlarm           | POST | `/bcp3/alarm/ascribe`                  | `--alarm-record-id-list`、`--rule-id`、`--operator`                                             |
| `create-note`                 | CreateNote             | POST | `/bcp3/note/add`                       | （`--op-type` 只允许 1/101）                                                                    |
| `transit-status`              | TransitStatus          | POST | `/bcp3/fsm/transit`                    | —                                                                                               |

**枚举码表**

- **SourceType**：3 StreamMQJson / 4 StreamBinlog / 5 StreamBytedoc / 101 NearRealTimeRds / 102 NearRealTimeRmq / 103 NearRealTimeBmq / 201 OfflineHive
- **RuleType**：1 GoValuate / 2 GoFunc / 3 RPC（实时秒级）/ 101 HiveQL（离线小时）/ 201 KryptonSQL（准实时分钟）
- **AlarmLevel**：0 Notice / 1 Warning / 2 Critical
- **UrgentType**：0 不加急 / 1 告警升级（后端未实现，勿传）/ 2 飞书 / 3 短信 / 4 电话
- **EntityType**：1 Source / 2 Checker / 3 Diff / 4 Alarm / 5 Execution / 6 AlarmConfig
- **NoteType（op_type）**：1 AlarmComment / 101 DiffComment（CreateNote 只允许这两个）
- **AscribeAlarm `--valid`**：1 有效 / 2 有效-资损 / 3 无效-攻防 / 4 无效-噪音（0=未确认，读出值，不作入参）
- **DiffStatus**：1 Todo / 2 Done；**DiffCompensateFlag**：0 无需 / 1 待复核 / 2 失败 / 3 成功；**DiffType**：1 新增 / 2 存量
- **写命令语义枚举**：`--status` 用 `todo`/`done`；`--valid-flag` 用 `valid`/`invalid`；`--compensate-type` 用 `batch`/`instance`/`auto`；`--compensate-flag` 用 `not-needed`/`awaiting`/`failed`/`success`；`--diff-type` 用 `new`/`existing`；`--compensate-execute-type` 用 `not-executed`/`manual`/`auto`。CLI 会映射为后端数字枚举。
- **ExecuteRecordStatus**：0 未开始 / 1 进行中 / 2 成功 / 3 失败

**场景编排（给 Agent）**

- 主键未知时先 list/search 再 detail，不猜 `source_id`、`checker_id`、`rule_id`、`execute_record_id` 或 `alarm_record_id`。
- 常规排查：`query-checker-list` → `get-checker-detail`/`get-sql-model-info` → `search-execute-record` → `search-diff-record`/`get-compensate-record`；告警先 `search-alarm-record`，再 `get-alarm-detail`。
- 离线/准实时通用复核：两类规则执行完成后都可由平台延迟进入 `CompensateAndAlarm`，按 Checker 配置自动复核；手动操作时用 `search-execute-record` → `search-diff-record` → `execute-batch-compensate`/`execute-instance-compensate` → `get-compensate-record` 回读。
- 准实时专属延迟诊断/SQL 试跑：仅 `RuleType=201` 使用 `get-hsap-source-delay-info` 和 `submit-nrt-snapshot-dry-run` → `get-nrt-snapshot-dry-run-result`；这条 HSAP 链路不适用于离线规则。提交先预览、确认后 `--yes`；`status=0` 继续等待，`status=1` 读取剩余异常，`status=2` 查看 `diagnose`。默认等待 30 秒、每 2 秒轮询，可调整 `--wait-ms`/`--poll-interval-ms`，或用 `--wait-ms 0` 只提交。

**写接口约束（关键）**

- `BatchUpdateChecker` 成功判定：`.failure_count == 0` 且 `.failures` 为空（不能只看顶层 code）。
- `BatchUpdateDiffRecord` 成功判定：除顶层 `code` 外，`.data.success` 必须为 `true`。设置 `--is-noise` 会把记录标记为噪音，提交前必须先检查 dry-run payload。
- `execute_record_id`、`diff_record_ids`、`executor_task_id` 都按十进制字符串传递，避免 19 位 ID 被 JavaScript Number 截断。
- `CreateChecker` 通用必填：`user_name`、`checker.checker_name`、`owner`、`tree_node`、`timeliness`、`checker_status=1`、`rule_type`、`is_asset_loss`；离线额外 `common_extra.process_version=2`、`offline_rule_content.hql`/`.cron`；准实时 `near_realtime_rule_content.krypton_sql`/`.cron`；alarm_config 接收对象三选一 `send_user`/`send_lark_group_id`/`duty_plan_id`。
- 状态流转：从 `get-fsm-transited-status` 的 `.transited_status_data.current_status` 与 `.operation_events[].event`/`.action_form[].key` 取值回填 `transit-status`。

---

## risk — 风险巡检（21 命令：11 读 + 10 写）

**只读（11）**

| 子命令                            | 后端方法                    | HTTP | path                                   |
| --------------------------------- | --------------------------- | ---- | -------------------------------------- |
| `get-risk-item-table`             | GetRiskItemTable            | POST | `/risk/home/simplified_item`           |
| `get-risk-item-info`              | GetRiskItemInfo             | GET  | `/risk/home/item_info`                 |
| `get-risk-category-tree`          | GetRiskCategoryTree         | GET  | `/risk/home/category_tree`             |
| `get-issue-list`                  | GetIssueList                | POST | `/risk/issue/issues`                   |
| `get-risk-issue-detail`           | GetRiskIssueDetail          | POST | `/risk/object/issues/details`          |
| `get-risk-issue-note`             | GetRiskIssueNote            | POST | `/risk/object/issues/note`             |
| `query-risk-projects`             | QueryRiskProjects           | POST | `/risk/project/query`                  |
| `get-overview-table-v2`           | GetOverviewTableV2          | POST | `/risk/data_overview_v2/table`         |
| `get-risk-insight-key-conclusion` | GetRiskInsightKeyConclusion | POST | `/risk/risk_insight_v2/conclusion`     |
| `get-risk-insight-table`          | GetRiskInsightTable         | POST | `/risk/risk_insight_v2/table`          |
| `get-risk-insight-red-black-list` | GetRiskInsightRedBlackList  | POST | `/risk/risk_insight_v2/red_black_list` |

**写（10，默认 dry-run，需 `--yes`）**

| 子命令                        | 后端方法                 | HTTP | path                                           | 必填                                                                                        |
| ----------------------------- | ------------------------ | ---- | ---------------------------------------------- | ------------------------------------------------------------------------------------------- |
| `add-risk-item`               | AddRiskItem              | POST | `/risk/home/item_info`                         | `--risk-item`、`--category-id`                                                              |
| `update-risk-item`            | UpdateRiskItem           | PUT  | `/risk/home/item_info`                         | `--risk-item`、`--item-id`                                                                  |
| `add-risk-issue`              | AddRiskIssue             | POST | `/risk/object/issues/add`                      | `--risk-name`、`--risk-item-key`、`--risk-object-key`、`--priority`、`--detail`、`--eta` 等 |
| `update-risk-issue-fixers`    | UpdateRiskIssueFixers    | POST | `/risk/object/issues/update_fixers`            | `--record-id`、`--fixers`                                                                   |
| `add-comment`                 | AddComment               | POST | `/risk/object/issues/add_note`                 | `--record-id`、`--comment`                                                                  |
| `update-risk-issue`           | UpdateRiskIssue          | POST | `/risk/object/issues/info`                     | `--record-id`                                                                               |
| `update-risk-record-priority` | UpdateRiskRecordPriority | POST | `/risk/record/priority`                        | `--record-id`、`--priority`、`--comment`                                                    |
| `create-meego`                | CreateMeego              | POST | `/risk/object/issues/create_meego`             | `--record-id`                                                                               |
| `create-gw-tag`               | CreateGwTag              | POST | `/arch/link/dependency/gw_tag/create`          | `--tag-name`、`--entity-ids`                                                                |
| `delete-gw-tag-relation`      | DeleteGwTagRelation      | POST | `/arch/link/dependency/gw_tag/relation/delete` | `--relation-ids`                                                                            |

**枚举码表**

- **GetRiskItemTable.status**：0 已全量 / 1 待上线 / 2 灰度中 / 3 已停用（归档）/ 4 删除；搜索固定 `node_type="1"`。
- **source_type**：official / user_defined / ai_defined；**priority**：P0/P1/P2。
- **IssueStatus（filters.status）**：0 全部 / 11 待处理 / 12 处理中 / 13 审核中 / 14 已暂缓 / 15 已处理 / 16 已取消 / 17 人工确认。
- **risk_type 可选值**：ABASE/BMQ/BYTEDOC/BYTEGRAPH/BYTEKV/BYTETABLE/CODEBASE/CRONJOB/DORADO/ES/FAAS/MYSQL/REDIS/RMQ/TCC/TCE/TLB/TOS/YARN。
- **TicketType**：4 RISK（create-meego/create-gw-tag 固定 4）；**NodeType**：1 分类 / 2 风险项。
- **filters 时间口径（易混）**：请求 `detect_time_*`=最近一次检出、`insert_time_*`=首次检出；返回 `detect_time`=首次检出、`latest_detect_time`=最近一次检出；格式 `YYYY-MM-DD HH:MM:SS`。

**jq / 用法要点**

- 写接口成功判定：`data == true`。
- 删标签：`get-risk-issue-detail` → `data.tags[].relation_id` → `delete-gw-tag-relation`。
- `get-issue-list` → `data.issues[]`/`data.total`/`data.has_more`，提取真实 `record_id`。
- 业务域补全：`meta get-biz-line-node-tree` 的 `node.info.biz_line_id` → risk 的 `biz_line_id`/`query-risk-projects --biz-line-ids`；`node.info.tree_paths` → `get-issue-list` 的 `filters.biz_lines`（**不要把 service_tree_id_paths 误传给 biz_lines**）。

---

## guard — EPS go_guard

`guard` 域通过 `bytedcli eopsx guard ...` 访问 EPS go_guard，使用 BDSSO browser session，不复用 ByteCloud JWT。首次使用先运行 `bytedcli auth login --session`；访问 BOE 时使用全局 `--site boe` 登录对应站点。

常用查询：

```bash
bytedcli --json eopsx guard source-tree get --system-id <id> --env-id <id> --terminal default
bytedcli --json eopsx guard env list --system-id <id> --page 1 --page-size 20
bytedcli --json eopsx guard role list --system-id <id> --env-id <id>
bytedcli --json eopsx guard perm list --system-id <id> --env-id <id>
```

CLI/Skill 资源使用现有 source CRUD 命令，资源类型分别为 `cli` 和 `skill`：

```bash
bytedcli --json eopsx guard source create \
  --system-id <id> --env-id <id> --source-type cli \
  --cli-name "Sample CLI resource" --cli-menu-id <menu_id> \
  --cli-account-type all \
  --cli-keys "bytedcli eopsx guard source list,bytedcli eopsx guard source get"

bytedcli --json eopsx guard source update \
  --system-id <id> --env-id <id> --source-id <source_id> --source-type skill \
  --skill-name "Sample Skill resource" --skill-menu-id <menu_id> \
  --skill-account-type master --skill-keys "api-to-cli"

bytedcli --json eopsx guard source get \
  --system-id <id> --env-id <id> --source-id <source_id> --source-type cli

bytedcli --json eopsx guard source delete \
  --system-id <id> --env-id <id> --source-id <source_id> --source-type skill
```

`perm source-relation-update` replaces the complete permission-source relation set. Pass every relation that must remain, including `--cli-source-ids` and `--skill-source-ids`; omitted resource types are cleared. The current backend `get_perm_source_list` implementation may omit CLI/Skill (`source_type=4/5`) during readback, so do not use an incomplete response as the input to a replacement update until the backend fix is deployed.
`env change-table-get --publish-id 0` means the current environment's unpublished change table. Other publish endpoints, including `env publish-info-get` and `env publish-change-list-get`, require `--publish-id` to be greater than 0.

CN → BOE 全量同步使用显式目标确认，默认 dry-run：

```bash
bytedcli eopsx guard sync full \
  --source-system-id <cn_system_id> --source-env-id <cn_env_id> \
  --target-system-id <boe_system_id> --target-env-id <boe_env_id> \
  --source-site cn --target-site boe \
  --confirm-target boe:<boe_system_id>:<boe_env_id> \
  --dry-run
```

安全边界：

- `guard` 只允许 `cn|boe` 站点，host 来自内置白名单。
- `env` 域不暴露最终发布、回滚、白名单、灰度比例和 pipeline 写操作；这些动作必须在 go_guard 控制台人工完成。
- `sync full` 会同步资源、权限和角色关系；真正写入前先看 dry-run workload 与 warnings。
