# BABI FinOps 命令

当前 flags、枚举和响应字段以命令 `--help` 为准；多步查询读取 [多步编排](workflows.md)。

## 团队

```bash
bytedcli babi finops team search --team-name 'demo-team'
bytedcli babi finops team search --team-name 'demo' --permitted-only=false --display-objective-year
```

稳定 ID 是 `team_id`。`--permitted-only` 默认 `true`；多个候选必须展示 ID、名称和路径并等待用户确认。

### 团队关联规则

```bash
bytedcli babi finops team rule list --team-id <team_id> --format json
bytedcli babi finops team rule list --team-id <team_id> --format table
bytedcli babi finops team rule list --data '{"team_id":<team_id>}' --format json
```

团队关联规则定义账号、服务树等成本范围条件，使用 `team rule list`；优化建议规则使用下文的 `optimization rule list`。

- 已有团队 ID 时直接查询。只有名称时先执行 `finops team search --team-name '<名称>'`，保持默认 `permitted-only=true`；唯一精确匹配时使用返回的 `team_id` 继续，多个候选展示 ID、名称、路径并等待选择，零候选说明“未找到当前可见的匹配团队”并请求补充名称或路径，不能编造 ID 或断言团队全局不存在。
- `team_id` 必须是正 int64，最大 `9223372036854775807`；`--data` 与 flag 同等校验，显式 flag 覆盖 JSON 同名字段后再校验。不自行转换或四舍五入大整数 ID。接口无分页，不添加 `limit` / `offset`。
- 使用 JSON 作为解释依据。成功响应保留 `status_code`、`status_msg`、`data.team_info`、`data.rules`；table 用于人工查看，csv/ndjson 仅按 `data.rules` 投影行。`--dry-run` 只生成请求预览，不是查询证据。

逐条解释返回的条件，并保留规则 ID 与对象 ID：

| 字段 | 含义 |
| --- | --- |
| `customer_account_list` | 消费方 BABI 账号 |
| `bytetree_list` / `exclude_bytetree_list` | 关联服务树 / 排除服务树，保留返回的路径 |
| `bind_type` | `1=单一`、`2=递归`，描述本条规则的服务树绑定方式 |
| `option_type` | `1=包含`、`2=排除` |
| `area_list` | 大区 |
| `provider_l1_account_list` | 成本产品线 |
| `product_flavor_list` | 成本商品及其 `flavors` 计费单元 |

查询范围仅为指定团队**自身当前有效规则**，不查询父子团队或历史版本，也不计算最终成本覆盖范围。规则中的“递归”不表示递归查询子团队。未知枚举保留原值，名称缺失时保留 ID；不补造名称、空条件语义、规则间逻辑或继承关系。

仅当命令成功且 `team_info` 存在、`rules=[]` 时，说明“该团队当前无自身关联规则”；不能据此判断无成本、无权限或没有继承范围。`data=null`、字段缺失或结构异常属于查询失败。权限拒绝与其他业务失败分别说明，保留实际错误码、消息及可用诊断 ID，不把失败解释成空规则或团队不存在，不在无新证据时重复查询。

## CostDriver

```bash
bytedcli babi cost-driver caliber list --data '{"Filters":[{"Key":"group_entity","Operator":"in","Value":["<group_entity>"]}],"Limit":10,"Offset":0}'
bytedcli babi cost-driver data-config list --data '{"Filters":[{"Key":"group_entity","Operator":"in","Value":["<group_entity>"]},{"Key":"data_source","Operator":"eq","Value":["Nuwa"]}],"Limit":10,"Offset":0}'
```

`Filters[].Key` 使用后端 snake_case，例如 `group_entity`、`cost_driver_type`、`status`；顶层字段保持接口定义的 `Filters`、`Limit`、`Offset`、`OrderItems`。

## 优化建议

```bash
bytedcli babi finops optimization rule list --team-ids <team_id> --limit 10
bytedcli babi finops optimization suggestion products --optimization-object-type 1 --optimization-object-id <optimization_object_id>
bytedcli babi finops optimization suggestion overview --period 2 --optimization-object-type 2 --optimization-object-id <optimization_object_id>
bytedcli babi finops optimization suggestion list --period 2 --optimization-object-type 2 --optimization-object-id <optimization_object_id> --status-list 1,4 --limit 20
```

- `period`：`1=日`、`2=月`。
- `optimization_object_type`：`1=账号`、`2=团队`、`3=服务树`。
- `optimization_rule_state`：`1=启用`、`2=停用`。
- `status_list`：`1=待处理`、`2=已处理`、`3=已忽略`、`4=处理中`。
- `opt_amount_type_list`：`1=可优化`、`2=不优化`、`3=扩容`、`4=缩容`。

分页 `limit` 范围 1-1000，`offset` 从 0 开始。`is_template` 默认 `false`，表示规则实例。

## 容量

```bash
bytedcli babi finops capacity list --biz-domain-list demo-domain --date 2026-07-18 --page-size 100
bytedcli babi finops capacity trend --psm-list example.psm --type-list tce --end-date 2026-07-18 --days 7
```

容量明细必须且只能提供 `psm_list`、`bytetree_id_list`、`biz_domain_list` 中的一种；`date_list` 最多 10 个日期。趋势查询要求 `type_list`、`psm_list` 和 1-30 天的 `days`，PSM 最多 30 个。

## 归因辅助

```bash
bytedcli babi finops attribution ticket list --data-range-type 3 --data-range 25 --is-resolved 0
bytedcli babi finops oncall url --trigger-message '成本异动归因' --attribution-ticket-id <attribution_ticket_id>
bytedcli babi finops lark user resolve --emails owner@example.com --include-resigned
```

`lark user resolve` 同时返回 user ID 和可发送的 `<at user_id="...">...</at>`。完整写入和证据链读取 [归因闭环](insight-attribution.md) 与 [写操作安全](writes.md)。

固定归因文案和 HTML：

```bash
bytedcli babi finops attribution report render \
  --input ./report.json \
	--reply-output ./final-reply.md \
  --markdown-output ./conclusion.md \
  --output ./report.html \
  --format json
```

`report.json` 使用 `babi_finops_attribution_v1`；返回的 `input_sha256` 相同时，`reply_sha256` / `final-reply.md` 与 `conclusion_sha256` / `conclusion.md` 必须分别相同。完整字段和禁止改写规则见 [固定输出契约](attribution-output-contract.md)。

上述查询保留 `--data '<JSON object>'` 兼容旧脚本，显式 flag 覆盖同名字段。JWT 和 headers 由命令与宿主注入。
