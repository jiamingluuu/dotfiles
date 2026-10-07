---
name: bytedance-fundeye
description: "Use bytedcli for FundEye / Fullink / TCheck workflows: run Risk-O business change analysis, get rule details, list or create rules, inspect diffs and alarms, and resolve business ownership paths to IDs. Trigger this skill whenever the user mentions FundEye, Fullink, TCheck, reconciliation rules, business ownership, biz path, rule_id, diff_id, alarm_order_id, 资金安全风险分析, Risk-O, or asks to investigate discrepancies, alarms, risk analysis, or rule configuration in these systems."
---

# bytedcli FundEye

## 如何调用 bytedcli

先选择一种调用方式。下面所有示例默认直接写 `bytedcli`。

```bash
# 方式 1：直接用 npx 运行最新版
NPM_CONFIG_REGISTRY=http://bnpm.byted.org npx -y @bytedance-dev/bytedcli@latest <command> [options]

# 方式 2：先全局安装，再直接调用 bytedcli
NPM_CONFIG_REGISTRY=http://bnpm.byted.org npm install -g @bytedance-dev/bytedcli@latest
bytedcli <command> [options]
```

- 使用 `npx` 时，把后文示例里的 `bytedcli` 替换成 `NPM_CONFIG_REGISTRY=http://bnpm.byted.org npx -y @bytedance-dev/bytedcli@latest`
- 已全局安装时，直接按后文示例执行 `bytedcli ...`

## When to use

- 触发业务变更资金安全风险分析（Risk-O）
- 查询 FundEye / Fullink 核对规则详情
- 按产品类型分页查询规则列表
- 保存 TCheck 规则草稿（save-draft）
- 发布 TCheck 规则（publish）
- 按业务归属名称路径查询 `business_ownership` ID
- 查询某条 diff 的明细
- 按规则分页查询 diff 列表
- 标记/处理 diff（update）
- 查询告警列表
- 查询 TCheck 核对记录
- 重跑 TCheck 核对记录
- 用户提到 `rule_id`、`diff_id`、`alarm_order_id`、`business_ownership`、业务归属路径、核对规则、规则列表、差异详情、差异列表、FundEye、Fullink、TCheck

## 能力范围

当前 skill 覆盖以下命令：

- Risk-O 业务变更分析：`fundeye risko trigger`
- 规则详情：`fundeye rule get`
- 规则列表：`fundeye rule list`
- 标签查询：`fundeye tag search`
- Fullink 子规则创建/查询/更新：`fundeye rule single|double|udf create|get|update`
- Fullink 双流子规则整体调试：`fundeye rule double debug`
- TCheck SQL 解析：`fundeye tcheck sql-parse`
- TCheck ad-hoc 调试与结果监听：`fundeye tcheck debug --watch`
- 整条规则创建（TCheck 优先 / Fullink 兜底）：`fundeye rule create`
- TCheck 全量创建：`fundeye rule full-create`
- 规则保存草稿：`fundeye rule save-draft`
- 规则发布：`fundeye rule deploy`
- 业务归属查询：`fundeye biz get`
- 差异详情：`fundeye diff get`
- 差异列表：`fundeye diff list`
- 差异处理：`fundeye diff update`
- 差异重试：`fundeye diff retry`
- 告警列表：`fundeye alarm list`
- 核对记录列表：`fundeye check-record list`
- 核对记录重跑：`fundeye check-record rerun`

## 前置条件

- 使用通用调用方式：`../../invocation.md`
- 先直接执行目标命令；只有返回明确鉴权错误时才恢复 bytedcli 登录态，并仅重试同一请求一次
- FundEye 请求依赖当前登录态自动补 `x-jwt-token` 和 `UserName`
- `fundeye tcheck sql-parse` 与 `fundeye tcheck debug` 仅支持 Volc，必须显式或默认使用 `--sitename volc`；不得回退其他站点

- 默认站点是 `cn`；如需海外机房可显式传 `--sitename sg`、`--sitename us-ttp`、`--sitename eu-ttp`，火山云继续使用 `--sitename volc/火山云`
- `fundeye rule get`、`fundeye rule list`、`fundeye rule deploy` 等读取/查询类命令支持 `cn`、`sg`、`us-ttp`、`eu-ttp` 与火山云别名；其中 `us-ttp` 映射到 `fundeye-usttp.tiktok-us.net`，`eu-ttp` 映射到 `fundeye-ie2-be.tiktok-eu.net`
- `fundeye rule create` 支持 `cn` 和 `sinf`（火山云/volc）；传入 `--sitename sinf`、`--sitename volc` 或 `--sitename 火山云` 时，后端收到 `site_name: "sinf"`；`sg`、`us-ttp`、`eu-ttp` 等其他站点会被拒绝
- `fundeye rule full-create` 目前仅支持 `cn`；它直接走 tcheck 底层 create + update 接口
- 新建 Fullink 时，默认优先判断子规则链路：`fundeye rule double create`、`fundeye rule udf create`、`fundeye rule single create`；只有在用户明确要求整条规则一次创建，或只提供了 legacy `rule create` 参数结构时，才回退到 `fundeye rule create --product-type fullink --rule-owner <owner> --params '<json>'`
- `fundeye risko trigger` 未显式传 `--user-name` 时，会回退到当前 bytedcli 登录用户；若仍拿不到则直接报错，要求传 `--user-name` 或先登录；未显式传 `--git-repo` / `--branch` / `--commit-id` 时，默认从 `--repo-dir`（缺省为当前目录）自动读取

- `fundeye biz get` 使用 `-` 连接层级路径；如果节点名有重名，必须传完整路径避免歧义
- `fundeye diff list` 需要提供 `--rule-id`；排查 `fullink` 告警或按 `--alarm-order-id` 过滤时，推荐显式传 `--start`、`--end`

> 执行前缀见 `../../invocation.md`；下面示例直接写 `bytedcli`。

## 工作流约定

1. 需要机器可读输出时默认加 `--json`，并把它放在 `fundeye` 前面。
2. 规则详情优先用 `fundeye rule get --rule-id <id>`。
3. 业务归属筛选优先走两步：先用 `fundeye biz get --path '<层级1-层级2>'` 拿到 `value`，再把该值传给 `fundeye rule list --business-ownership <value>`。
4. 规则列表优先用 `fundeye rule list --product-type fullink|tcheck`；默认查询 `fullink`，需要时再补 `--name`、`--owner`、`--status`、`--business-ownership`，`tcheck` 还支持 `--period`、`--tag-id`。
5. 新建 Fullink 时，优先走子规则创建，不要默认走整条 `rule create`：先判断能否落到 `fundeye rule double create`，其次 `fundeye rule udf create`，再看 `fundeye rule single create`。只有在用户明确要求整条 Fullink 规则一次创建，或输入天然就是 legacy `data_sources/join/check_logic` 结构时，才回退到 `fundeye rule create --product-type fullink --rule-owner <owner> --params '<json>'`。
6. Fullink 子规则创建/查询/更新使用新链路：`fundeye rule single|double|udf create|get|update`。`create` 支持 `--payload` 或 `--payload-file`；不传 `--scene-id` 时会新建 scene，传了则往已有 scene 追加。`update/get` 需要 `--scene-id` 和 `--sub-rule-id`。其中 single 的 `sub-rule-id` 对应 `single_ds_check_id`，double 的 `sub-rule-id` 使用边序号 `edge_seq`。安全 payload 样例见 `references/subrule-payload-examples.md`。
7. 双流子规则整体调试使用 `fundeye rule double debug --rule-id <id> --rule-version <version> --edge-seq <seq>`，并通过 `--upstream-data|--upstream-data-file` 与 `--downstream-data|--downstream-data-file` 各提供一份样例 JSON。CLI 会查询指定版本规则，按边序号自动补齐完整 `edge_table_join` 及对应的两个 `vertex_table_list` 节点；不要让用户手工拼控制台请求体。非聚合核对传单个对象；聚合核对按边的聚合方向把对应一侧传成对象数组。
8. 单流 single 的 payload 直接传原 open single_rule 字段；double 的 payload 形如 `{"edge_table_join": {...}, "vertex_table_list": [...]}`；udf 的 payload 形如 `{"udf": {...}, "vertex_table_list": [...], "edge_table_join_list": [...]}`。若 UDF 涉及多数据源关联，CLI 会要求并补齐 `edge_table_join_list`，并默认把边的上下游触发都设为 `NOTRIGGER`。
9. double 子规则里若 vertex 是 MQ 类型（RocketMQ/Kafka/Tea），且用户未显式传 `mq_uniq_index`，CLI 会优先按 `edge_table_join.join_expression` 的同侧关联键自动补齐该字段，避免用户感知平台内部“快照唯一标识”概念。
10. Fullink 子规则涉及脚本时，Agent 先判断脚本类型：`govaluate` 用于 filter、join、唯一键、触发条件等表达式字段；Go/Yaegi 用于 `Verify` 这类核对主逻辑。不要把复杂核对逻辑直接塞进 `govaluate`。
11. 生成 `govaluate` 时，优先使用环境里已安装的 `govaluate_script_gen` skill 或现有脚本手册；生成后必须先调用现有校验接口，确认语法和约束通过，再继续 `create/update`。
12. 生成 Go/Yaegi 脚本时，也先按现有脚本手册生成，再调用现有校验/编译接口确认入口函数和依赖可通过，最后再把脚本写入 payload。
13. `single` 常见脚本位于 `filter_script` 与 `golang_check_script.script`；`double` 常见脚本位于 `edge_table_join.join_expression`、`vertex_table_list[].filter` 与 `edge_table_join.check_logic`；`udf` 常见脚本位于 `payload.udf.script` 以及各 vertex 的过滤表达式。
14. 如果用户要写 Fullink Go 函数，先区分函数场景：`Filter`、`Generate`、双参数 `Verify`、聚合 `Verify`、单流 `Verify`；再确认入参类型是 `map[string]interface{}` 还是 `string`。
15. 生成 Fullink Go 函数时，严格遵守平台约束：不要写 `package`；不要 import 已预导入包；日志只用 `log.Info`；如果需要主动查数，可直接使用 `tcc`、`rpc`、`redis`、`abase`、`metrics`。
16. Fullink Go 函数在交付前必须跑编译检查；若编译失败，要按报错自动修正后重试，直到通过。
17. 新建整条 TCheck 规则优先用 `fundeye rule create --product-type tcheck --rule-owner <owner> --params '<json>'`；支持 `cn` 和 `sinf`（火山云/volc）机房，`--params` 只传业务参数对象，CLI 会自动包装成 `source + agent_task_list` 请求体；需要等最终落规则时再加 `--poll`。
18. 需要完全对齐前端 tcheck 编辑页字段、直接走底层 `/t_check/rule` + `/t_check/rule/:id` 时，用 `fundeye rule full-create --params '<json>'`；CLI 会自动补齐 create 阶段和依赖推导字段。
19. 需要仅保存 `tcheck` 规则草稿时，用 `fundeye rule save-draft --product-type tcheck --rule-id <id> --params '<json>'`；这一步不会发布规则。CLI 会先读取当前规则，再把 `--params` 里的字段覆盖到最新草稿上后保存，因此日常只需要传这次要更新的字段。
20. TCheck 候选 SQL 在 Volc 上先执行 `fundeye tcheck sql-parse --sql-file <path> --data-source-type krypton|hive --sitename volc`；解析只做语法检查，不执行查询或修改规则。
21. 解析通过后使用 `fundeye tcheck debug --rule-id <id> --sql-file <path> --date <value> --data-source-type krypton|hive --watch --sitename volc`。候选 SQL 仅通过本次 ad-hoc 请求的 `hsql` 提交，不保存到规则；`--watch` 优先按提交响应 `data.debug_id` 精确查找同 ID 的运行中与终态记录，因此同一 `rule_id` / operator 下可安全并发。若旧响应没有 `debug_id`，CLI 才回退到提交前最大 debug_id、rule_id 和当前 operator 的串行关联，并显式返回 `correlationMode=legacy_watermark`、`concurrencySafe=false`。目标规则 `update_time` 漂移时停止。
22. 调试回执必须保留顶层 `debugId`、`correlationMode`、`concurrencySafe`、requested/returned SQL SHA-256、`exact|normalized|mismatch|unavailable` 匹配分类、终态、结果行数和错误文本；精确模式返回 `correlationMode=exact_debug_id`、`concurrencySafe=true`。FundEye 可能归一化表名，不能把返回 SQL 文本完全相等作为关联条件。
23. 如果用户没有给清楚样例数据、字段名、返回值或脚本类型，Agent 应先追问，不要臆造脚本。
24. 需要发布 `tcheck` 规则时，用 `fundeye rule deploy --sitename volc --product-type tcheck --rule-id <id>`
25. diff 明细优先用 `fundeye diff get --diff-id <id> --rule-id <id>`。
26. diff 列表必须提供 `--rule-id`，默认查询 `fullink`；查 `tcheck` 时加 `--product-type tcheck`，其中 `--rule-version` 可省略且默认按 `0` 请求；排查 `fullink` 告警、尤其按 `--alarm-order-id` 过滤时，优先补 `--start`、`--end` 时间窗，再视情况加 `--rule-version`。
27. 需要标记/处理 diff 时，用 `fundeye diff update --reason <parent||child> (--diff-list '<json>' | --alarm-order-id-list '<json>')`；其中 `diff_id`/`diff_version` 从 `fundeye diff list --json` 返回的 `diffs[].diff_id`/`diffs[].diff_version` 获取；status 固定为 `PROCESS_RESULT`。
28. 需要重试 diff 时，用 `fundeye diff retry --try-list '<json>'`；其中 `try_list` 是 diff_id 的 JSON 数组字符串，可从 `fundeye diff list --json` 的 `diffs[].diff_id` 获取。
29. 按规则查 TCheck 核对记录或重跑历史时段时，推荐流程是：先执行 `fundeye check-record list --rule-id <rule-id>`，需要重跑时再执行 `fundeye check-record rerun --rule-id <rule-id> --business-time <yyyy-MM-dd HH:mm:ss>`。
30. 如果服务端返回 500，优先保留 `request_id` 给后端排查；`fullink diff list` 还要先确认是否遗漏了时间窗。
31. 需要对 git 仓库当前变更触发资金风险分析时，优先用 `fundeye risko trigger`；若只想核对请求体，用 `--dry-run` 输出最终 snake_case payload，再决定是否真实触发。

## Quick start

```bash
# 规则详情
bytedcli --json fundeye rule get --rule-id 2604202570843580

# 规则列表
bytedcli --json fundeye rule list \
  --product-type fullink \
  --status RUNNING \
  --owner demo-owner \
  --page 1 \
  --page-size 10

# 标签查询
bytedcli --json fundeye tag search --name 风险 --product tcheck --page 1 --page-size 10

# 先用业务归属路径换取 business_ownership ID
bytedcli --json fundeye biz get --path '财经-数据平台'

# 触发业务变更资金安全风险分析
bytedcli --json fundeye risko trigger \
  --psm example/demo_order_service \
  --git-repo 'git@example.invalid:example/demo_order_service.git' \
  --branch feature/demo-analysis \
  --commit-id 0123456789abcdef0123456789abcdef01234567 \
  --user-name demo-user

# 再按 business_ownership 过滤规则
bytedcli --json fundeye rule list \
  --product-type fullink \
  --business-ownership 7000000000000000000 \
  --page 1 \
  --page-size 10

# Fullink 创建优先走子规则 create；先看 double
bytedcli --json fundeye rule double create \
  --scene-name demo-scene \
  --payload '{"edge_table_join":{"edge_seq":1,"from_vertex":1,"to_vertex":2},"vertex_table_list":[{"vertex_seq":1,"vertex_name":"up"},{"vertex_seq":2,"vertex_name":"down"}]}'

# 按规则版本和边序号加载配置，只传上下游样例数据
bytedcli --json fundeye rule double debug \
  --rule-id demo-rule \
  --rule-version 7 \
  --edge-seq 1 \
  --upstream-data-file /tmp/demo-upstream.json \
  --downstream-data-file /tmp/demo-downstream.json

# 其次看 udf create
bytedcli --json fundeye rule udf create \
  --scene-name demo-scene \
  --payload-file /tmp/demo-udf.json

# 再看 single create
bytedcli --json fundeye rule single create \
  --scene-name demo-scene \
  --payload-file /tmp/demo-single.json

# 仅在 legacy/兜底场景下，才使用 fullink 参数格式整条创建规则
bytedcli --json fundeye rule create \
  --product-type fullink \
  --rule-owner demo-owner \
  --params '{"owner":"demo-owner","rule_type":"double_check","data_sources":[{"vertex":"up","db_name":"sample_upstream_db","tb_name":"sample_upstream_table","filter_logic":"status == 98","is_trigger":true},{"vertex":"down","db_name":"sample_downstream_db","tb_name":"sample_downstream_table","filter_logic":"pay_status == \"SUCCESS\"","is_trigger":true}],"join":[{"from_vertex":"up","to_vertex":"down","join_info":"[{\"upstream\":\"order_id\",\"downstream\":\"out_order_no\"}]"}],"check_logic":"[up.total_amount] == [down.total_amount]"}' \
  --poll \
  --max-retries 30 \
  --interval 3

# 使用 tcheck 参数格式创建规则并轮询到 rule_link
bytedcli --json fundeye rule create \
  --product-type tcheck \
  --rule-owner demo-owner \
  --params '{"data_source_type":"krypton","check_tables":["sample_db.sample_table_a","sample_db.sample_table_b"],"user_check_requirement":"关联键: sample_key_a 和 sample_key_b; 核对规则: 筛选上游有记录但下游无匹配记录的异常数据; 输出字段: sample_field_a、sample_field_b"}' \
  --poll \
  --max-retries 30 \
  --interval 3

# 使用前端字段风格全量创建 tcheck 规则
bytedcli --json fundeye rule full-create \
  --params '{"name":"demo-tcheck-rule","illustration":"demo desc","period":"daily","daily_run_time":"00:00:00","owner_list":["demo-owner"],"member_list":["demo-member"],"permission_group":["group.demo"],"business_ownership":"demo-biz","receiver":"demo-owner","lark_group_id":"oc_demo_group","priority":"P1","diff_limit":100,"sql":"select 1","check_tables":["sample_db.ods_demo_table"],"depend":{"upstream_depend":[{"dorado_id":123,"name":"demo task","frequency":"daily","offset_type":"set","offset":[0]}]}}'

# 保存 tcheck 规则草稿（仅更新，不发布）
bytedcli --json fundeye rule save-draft \
  --product-type tcheck \
  --rule-id 20260601_1234567890000 \
  --params '{"tag_ids":["tag-a","tag-b"]}'

# 发布 tcheck 规则
bytedcli --json fundeye rule deploy \
  --product-type tcheck \
  --rule-id 20260601_1234567890000

# 在 Volc 解析一条 Krypton TCheck SQL；只检查语法，不执行或修改规则
bytedcli --json fundeye tcheck sql-parse \
  --sql-file /tmp/candidate.sql \
  --data-source-type krypton \
  --sitename volc

# 将 SQL 仅作为本次 hsql 执行，并等待关联的终态调试记录
bytedcli --json fundeye tcheck debug \
  --rule-id 20260601_1234567890000 \
  --sql-file /tmp/candidate.sql \
  --date '20260819 14:30' \
  --hour '' \
  --minute 30 \
  --data-source-type krypton \
  --watch \
  --sitename volc

# diff 明细
bytedcli --json fundeye diff get \
  --diff-id "DOUBLE_DS_CHECK#^#0#^#demo-diff" \
  --rule-id 2601142357560097

# diff 列表
bytedcli --json fundeye diff list \
  --rule-id 2601142357560097 \
  --product-type fullink \
  --rule-version 11 \
  --start "2026-04-21 00:00:00" \
  --end "2026-04-21 23:59:59" \
  --page 1 \
  --page-size 20

# diff 处理（update）
bytedcli --json fundeye diff update \
  --reason "BIZ_ISSUES||NEW_BIZ_DEPLOY" \
  --remark "demo remark" \
  --diff-list '[{"diff_id":"DOUBLE_DS_CHECK#^#0#^#demo","diff_version":1}]'

# 告警单批量标记原因
bytedcli --json fundeye diff update \
  --reason "BIZ_ISSUES||NEW_BIZ_DEPLOY" \
  --remark "demo remark" \
  --alarm-order-id-list '["TCheck##demo-alarm-order-id"]'

# diff 重试（retry）
bytedcli --json fundeye diff retry \
  --try-list '["DOUBLE_DS_CHECK#^#0#^#demo"]'

# 告警列表
bytedcli --json fundeye alarm list --page 1 --page-size 20
bytedcli --json fundeye alarm list --alarm-priority P1 --alarm-priority P2
bytedcli --json fundeye alarm list --alarm-user demo-user
bytedcli --json fundeye alarm list --start '2026-08-01 00:00:00' --end '2026-08-31 23:59:59'

# 核对记录列表
bytedcli --json fundeye check-record list --rule-id 20260528_1779959586985 --date 2026-06-10

# 核对记录重跑
bytedcli --json fundeye check-record rerun --rule-id 20260528_1779959586985 --business-time "2026-06-10 00:00:00"
```

## 常见工作流

### 1. 查看规则

- 使用 `fundeye rule get --rule-id <id>`
- 优先关注 `baseInfo` 和 `graphData`

### 2. 按产品类型列规则

- 使用 `fundeye rule list --product-type fullink|tcheck`
- 默认查询 `fullink`
- `fullink` 支持 `--name`、`--owner`、重复 `--status`、`--business-ownership`
- `tcheck` 额外支持 `--period`、重复 `--tag-id`

### 3. 创建规则

- 创建 Fullink 时，默认优先走 `fundeye rule double create`、`fundeye rule udf create`、`fundeye rule single create`，尽量不要先用 `fundeye rule create --product-type fullink --rule-owner <owner> --params '<json>'`
- 只有在用户明确要求整条 Fullink 规则一次创建，或输入天然就是 legacy `data_sources/join/check_logic` 结构时，才回退到 `fundeye rule create --product-type fullink --rule-owner <owner> --params '<json>'`
- CLI 的 `--params` 只传业务参数对象，不需要手动包 `source`、`agent_task_list`

- `fundeye rule create` 支持 `cn` 和 `sinf`（火山云/volc）；传入 `--sitename sinf`、`--sitename volc` 或 `--sitename 火山云` 时，后端收到 `site_name: "sinf"`；`sg`、`us-ttp`、`eu-ttp` 等其他站点会被直接拒绝
- `fundeye rule full-create` 目前仅支持 `cn`；显式传入非 `cn` 的 `--sitename`（如 `sg`、`us-ttp`、`eu-ttp`、`volc/火山云`）会直接报不支持

- `fullink` 的 `--params` 至少包含：`owner`、`rule_type`、`data_sources`、`join`、`check_logic`
- `fullink` 的 `join[].join_info` 需要传字符串，字符串内容通常仍是 JSON 数组
- `tcheck` 的 `--params` 至少包含：`data_source_type`、`check_tables`、`user_check_requirement`
- 如果规则或子规则涉及脚本，先区分 `govaluate` 与 Go/Yaegi：前者用于表达式约束，后者用于核对主逻辑
- 推荐 Agent 流程：先生成脚本，再调用现有校验/编译接口确认通过，最后再发 `create` / `update`
- 若环境中已安装 `govaluate_script_gen`，生成 `govaluate` 时优先使用；若不可用，则先参考现有脚本手册或向用户追问字段与约束
- 需要自定义幂等单号时加 `--out-biz-no`；需要轮询最终 `rule_link` 时加 `--poll`

### 3.1 TCheck 全量创建

- 使用 `fundeye rule full-create --params '<json>'`
- `--params` 传前端编辑页 update body 风格字段；命令会先 POST `/api/t_check/rule`，再 PUT `/api/t_check/rule/:rule_id`
- 至少提供：`name`、`business_ownership`、`receiver`、`lark_group_id` 或 `lark_group_list`、`priority`、`diff_limit`、`sql`
- `owner_list` 可省略；缺省时回退为当前登录用户
- `period` 为必填；若 `period=daily` 还需提供 `daily_run_time`，若 `period=hourly` 还需提供 `hourly_run_minute`
- `data_source_type` 可省略；CLI 会按 `check_tables` 推断 `hive`/`krypton`，显式传入时会先统一转成小写再参与后续逻辑
- `task_run_time` 无需手填：`daily` 从 `daily_run_time` 推导，`hourly` 从 `hourly_run_minute` 推导，其他周期默认空串
- `task_pending_alarm` 对 hive 类数据源缺省时自动补：`hourly -> 3`、其他 -> `16`；`krypton/clickhouse` 会固定为 `1`，不接受覆盖

### 3.2 保存规则草稿（save-draft）

- 当前仅支持 `tcheck`
- 该命令只保存草稿，不会发布规则
- `--params` 必须是 JSON 对象字符串
- CLI 会先调用 `fundeye rule get` 读取当前规则，再把 `--params` 里的字段覆盖到最新规则体上，然后调用保存草稿接口
- 因此日常只需要传这次要更新的字段，例如：
  - 只改标签：`{"tag_ids":["tag-a","tag-b"]}`
  - 只改接收人：`{"receiver":"demo-owner"}`
  - 同时改多个字段：`{"tag_ids":["tag-a"],"priority":"P1"}`
- 支持 `--sitename volc/火山云` 路由到火山环境

#### Agent Guidance: Govaluate 脚本生成与校验

- `govaluate` 只用于表达式脚本，不用于 Go/Yaegi 的 `Verify` 主逻辑；用户提到筛选条件、过滤表达式、核对表达式、join 条件、binlog 状态流转时优先走这条链路
- 优先判断 3 类场景：
  - 单数据源筛选：字段直接使用，不加前缀
  - 双数据源核对：字段通过 `up.` / `down.` 区分
  - Binlog 变更：同一条记录同时存在 `field` 和 `before__field`
- 每轮只追问 1 到 2 个关键问题，优先拿到字段列表或 JSON 样例，再确认日期格式、金额精度、是否可能为空、是否需要抽样
- 最终输出脚本时，代码块语言标识统一用 `javascript`，但脚本本身不能写注释；解释放在代码块外
- 最终交付前必须先 `cd` 到当前 skill 目录，再执行：

```bash
node -r ts-node/register/transpile-only scripts/check_govaluate.ts "<生成的脚本>"

如需走 PPE，只能通过 bytedcli 全局 `--http-header` 透传 `x-tt-env` / `x-use-ppe`；FundEye 相关脚本与命令示例里不要写死任何具体 PPE lane。
```

- 如果返回 `data.ok = false`，必须根据 `data.error` 自动修正脚本并重新检查，直到通过才交付
- 详细工作流、避坑规则、UDF 与语法参考见：
  - `references/govaluate-script-gen.md`
  - `references/udf_functions.md`
  - `references/govaluate-syntax.md`

#### Agent Guidance: Fullink Go 函数生成与编译检查

- 用户提到 Fullink Go 函数、Filter / Generate / Verify、主动查数、TCC / RPC / Redis / Abase / Metrics 时，优先阅读：
  - `references/fullink-go-func.md`
  - `references/external-apis.md`
- 先确认两件事：
  - 场景：`Filter` / `Generate` / 双参数 `Verify` / 聚合 `Verify` / 单流 `Verify`
  - 入参类型：`map[string]interface{}` 或 `string`
- 生成代码时必须遵守平台规则：
  - 不要写 `package`
  - 不要 import 已预导入包
  - 日志只能使用 `log.Info`
  - 仅允许 import 未预导入的 Go 标准库；第三方库禁止使用
- 如果需要主动查数，直接使用平台内置客户端：`tcc`、`rpc`、`redis`、`abase`、`metrics`
- 最终交付前必须先 `cd` 到当前 skill 目录，再执行：

```bash
node -r ts-node/register/transpile-only scripts/compile_check.ts \
  --script "func Verify(up map[string]interface{}, down map[string]interface{}) (bool, error) { return true, nil }" \
  --param-types "map[string]interface{}" "map[string]interface{}" \
  --func-name "Verify"
```

- 如果返回 `data.ok = false`，必须根据 `data.error` 自动修正代码并重新检查，直到通过才交付

#### Agent Guidance: `data_source_type` 推断规则

`data_source_type` 合法值为 `"krypton"` 或 `"hive"`。若用户显式指定，以用户为准；未指定时，根据 `check_tables` 中的库名/表名自动推断，按以下优先级判断：

1. **Krypton DB 前缀白名单（最强信号，零误判）**：库名前缀命中以下任一，判定为 `"krypton"`：
   `noveldb`、`novel_op`、`novel_original`、`novel_bookdb`、`novelsale_distributordb`、`parallel_commerce`、`lvideo_compass`、`pgcincome`、`ocean_story`、`ocean_story_split`、`dpa_data`

2. **Hive 表名分层关键字（100% Hive）**：表名含以下任一分层前缀，判定为 `"hive"`：
   `ods_`、`ods_mysql_`、`dwd_`、`dim_`、`dm_`、`ads_`、`dwm_`、`dwa_`

3. **Hive 高频 DB 前缀**：库名前缀命中以下，判定为 `"hive"`：
   `webcast`、`open`、`aweme`、`pgc`、`ies_wallet`、`ad_star`、`dm_ttgame`、`dm_effect_platform`、`toutiao_dw`、`caijing_dw`

4. **无法判断时**：主动询问用户，不要猜测。提示："请确认数据源类型：krypton（业务在线库/MySQL 镜像）还是 hive（离线数仓）？"

### 4. 先查业务归属，再筛规则

- 业务归属名称路径已知时，先执行 `fundeye biz get --path '<层级1-层级2>'`
- 推荐传完整层级路径，例如 `财经-数据平台-会员`
- 成功后取返回中的 `value`
- 再执行 `fundeye rule list --business-ownership <value>`

### 5. 查看某条 diff

- 已知 `diff_id` 且知道所属规则时，用 `fundeye diff get`
- 如果只有告警单和规则信息，先用 `fundeye diff list` 缩小范围，再取具体 `diff_id`

### 6. 按规则排查 diff

- 使用 `fundeye diff list --rule-id <id>`
- 默认查询 `fullink`，查 `tcheck` 时加 `--product-type tcheck`
- `tcheck` 的 `--rule-version` 可省略；未传时默认按 `0` 请求上游
- 排查 `fullink` 时优先补 `--start`、`--end` 时间窗
- 需要进一步缩小范围时，加 `--rule-version` 或 `--alarm-order-id`
- 对结果中的 `diff_id` 再调用 `fundeye diff get`

### 7. 先看告警，再查 diff

- 先执行 `fundeye alarm list`
- 取返回里的 `alarmOrderId`、`ruleId`
- 再执行 `fundeye diff list --rule-id ... --alarm-order-id ... --start ... --end ...`

## Notes

- `--json` 是全局参数，必须放在 `fundeye` 前面，例如 `bytedcli --json fundeye rule get --rule-id ...`
- `fundeye tcheck sql-parse` 和 `fundeye tcheck debug` 只支持 Volc；两者均接受 `--sql` 或 `--sql-file`，但不能同时提供
- `fundeye tcheck debug --watch` 只提交一次 ad-hoc debug，不保存草稿、不发布、不启停或正式重跑规则；提交网络超时也不会自动重试，避免创建无法确认的重复任务
- 新响应按唯一 `debug_id` 精确分页查找结果；旧响应缺少该字段时保留水位回退，但该模式只适合串行调用，并会明确标记 `concurrencySafe=false`
- `fundeye rule create` 发送给服务端的请求体会自动包装成 `{"source":"platform_api","agent_task_list":[...]}`；CLI 侧 `--params` 只需要传单条任务里的业务参数对象
- `fundeye diff` 现在是分组命令；详情请用 `fundeye diff get`，列表请用 `fundeye diff list`
- `fundeye biz get` 返回的是 `{ path, value }`；其中 `value` 就是后续传给 `--business-ownership` 的 ID
- 业务归属树里可能有重名节点；只给单层标题时可能报歧义，必须传完整路径
- `fundeye diff list` 缺少必填参数时会返回结构化 help JSON
- `fundeye diff list --json` 的 `diffs[]` 字段名为 snake_case（例如 `diff_id`、`rule_id`），不再输出 camelCase 版本（例如 `diffId`、`ruleId`）
- `fullink diff list` 排查告警时，优先显式传 `--start`、`--end`，再观察是否仍返回 `HTTP 500`
- 如果 diff/list 仍返回 `HTTP 500`，优先记录 `request_id`

## References

- `references/fundeye.md`
- `references/govaluate-script-gen.md`
- `references/udf_functions.md`
- `references/govaluate-syntax.md`
- `references/fullink-go-func.md`
- `references/external-apis.md`
- `../../invocation.md`
- `../../troubleshooting.md`

也支持 `fundeye risko trigger`、`fundeye rule full-create`、`fundeye rule save-draft`、`fundeye tag search`、`fundeye check-record list` 与 `fundeye check-record rerun`。
