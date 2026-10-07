# 问题补齐、租户分类与追踪工单

进入 Oncall 流程后，按本文件完成第 1–4 步。除缺少关键信息或等待扩大租户搜索授权外，不中途要求用户逐项选择。

## 目录

- 1. 补齐问题信息
- 2. 选择产品租户
- 3. 选择区域和问题分类
- 4. 创建内部追踪工单

`flow create` 成功后，后续面向用户展示当前工单 ID 时统一使用 Markdown 链接：`[<oncall_flow_id>](https://cloud.bytedance.net/oncall/admin/review/all?id=<oncall_flow_id>&picked_detail=<oncall_flow_id>)`。链接只传 `id` 和 `picked_detail`，两者都使用当前工单 ID；不要追加租户、资源账号、区域、分页、筛选条件或其他页面状态参数。命令参数和代码块中的工单 ID 仍使用纯值。历史工单优先使用 `flow search` 实际返回的链接，不要用当前追踪工单 ID 覆盖。

## 1. 补齐问题信息

- 从用户描述中提取独立的产品、模块或服务关键词作为 `tenant_keyword`，不要使用整段问题描述。
- P0 缺少影响范围时只追问 `urgent_description`；问题描述不完整时只追问 `trigger_message`。
- 已进入流程并等待字段时，将用户下一轮回复优先补入该字段，不要误判为新意图。

## 2. 选择产品租户

用户已明确提供租户 ID 时直接使用；否则搜索：

```bash
bytedcli oncall tenant search \
  --keyword "<tenant_keyword>" \
  --page-size 10 \
  --format json
```

- 空结果时读取 `empty_reason`：`no_match` 表示关键词确实没有数据，按下方规则换别名；`whitelist_filtered` 表示匹配到的租户尚未加入当前灰度列表，此时告知用户可在授权后扩大搜索范围。
- `--skip-tenant-whitelist` 是需要用户授权的查询参数。只有 `empty_reason=whitelist_filtered` 时才可建议使用，使用时询问：“当前匹配到的租户还不在我们的灰度列表中。是否授权我扩大搜索范围，继续查找该租户？”
- 用户明确回复“确认”“允许”“可以”等肯定表达后，才执行：

```bash
bytedcli oncall tenant search \
  --keyword "<tenant_keyword>" \
  --page-size 10 \
  --skip-tenant-whitelist \
  --format json
```

- 唯一候选直接选用；多个候选结合产品/模块名、缩写、故障对象、接口或服务名以及候选描述选择最匹配项。
- `empty_reason=no_match` 时换用 1–3 个更短的别名或模块名重试，仍无可用候选时才请用户补充产品信息。
- 记录 `tenant_id`、`tenant_name` 和具体选择依据，然后查询能力开关：

```bash
bytedcli oncall tenant get --id <tenant_id> --format json
```

## 3. 选择区域和问题分类

```bash
bytedcli oncall question-type list \
  --tenant-id <tenant_id> \
  --regions-only \
  --format table

bytedcli oncall question-type list \
  --tenant-id <tenant_id> \
  --region "<region>" \
  --format table
```

- 按“区域 → 分类”选择，但不中途请用户确认。唯一项直接选用；多个候选根据地域、故障现象、操作目标、影响范围和分类含义选择。
- 首次无区域或分类时重试并查询全部区域；只有整个租户仍无可用分类时才请用户确认租户或补充信息。
- 保存区域、分类、选择依据、`type_action` 及服务端实际返回的后续处理字段。不要自行拼接或猜测链接、群聊、目标租户。

## 4. 创建内部追踪工单

```bash
bytedcli oncall flow create \
  --tenant-id <tenant_id> \
  --message "<trigger_message>" \
  --format json
```

保存本次返回的 `oncall_flow_id`，供智能问答和最终建群使用。
