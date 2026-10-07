---
name: bytedance-bamboo
description: "Create, list, update, and inspect Bamboo data quality rules through bytedcli. Use when tasks mention Bamboo offline/Hive rules, rule IDs, offline result details, abnormal Hive rows, or Bamboo interfaces 1, 2, 3, 34, and 39."
---

# bytedcli Bamboo

## When to use

- 按规则 ID 获取 Bamboo Hive 规则详情
- 按空间与筛选条件查询 Bamboo 离线规则
- 创建或编辑 Bamboo 离线规则
- 按结果 ID 获取 Bamboo 离线规则结果详情
- 查看规则 SQL、调度、owner、分区配置或告警配置
- 查看离线校验状态、实际 SQL、异常数据行与重复告警数据

这些开放接口不需要执行 `auth login`，但运行环境需要能访问字节办公网。创建和更新默认只预览请求，只有显式传入 `--yes` 才会发送 POST。

## Commands

```bash
# 按空间查询 Hive 规则；--space-id 为必填项
bytedcli bamboo hive-rule list --space-id demo-space-id

# 按显式用户上下文筛选关注状态
bytedcli bamboo hive-rule list --space-id demo-space-id --followed true --user-id 10001 --email demo.user

# 获取 Hive 规则详情
bytedcli bamboo hive-rule get --id 12345

# 校验并预览创建请求，不发送 POST
bytedcli bamboo hive-rule create --payload-file ./demo-bamboo-rule-create.json

# 校验并预览完整更新请求，不发送 POST
bytedcli bamboo hive-rule update --id 12345 --payload-file ./demo-bamboo-rule-update.json

# 获取离线规则结果详情
bytedcli bamboo offline-result get --id 67890

# 推荐 Agent 使用结构化输出；--json 是全局参数，放在 bamboo 前
bytedcli --json bamboo hive-rule list --space-id demo-space-id --page 1 --page-size 20
bytedcli --json bamboo hive-rule create --payload-file ./demo-bamboo-rule-create.json
bytedcli --json bamboo offline-result get --id 67890
```

`--id` 必须是正整数。`hive-rule get/update` 接受规则 ID，`offline-result get` 接受离线结果 ID，两类 ID 不可互换。创建与更新的 payload 使用 camelCase 规范化字段，完整模板和条件必填规则见 [`references/hive-rule-write-payloads.md`](references/hive-rule-write-payloads.md)。

使用 `hive-rule list --followed <true|false>` 时，必须同时传 `--user-id <employee-id>` 与 `--email <email-prefix>`，明确指定按谁的关注状态筛选；接口本身不会从登录态推导当前用户。

## Result interpretation

- Hive 规则位于 JSON 的 `data.hive_rule`，请求 ID 会以 `id` 返回。
- Hive 规则详情中的告警、规则类型、调度频率等无后缀字段使用与写入 payload 相同的语义值；原始数字保存在 `*Code` 字段，原始 `是`/`否` 保存在 `*Text` 字段。
- 规则列表位于 `data.hive_rules`，分页上下文为 `page`、`page_size` 与上游 `total`。
- 创建或更新未带 `--yes` 时返回 `status: "dry_run"`、`mode: "preview"`、`applied: false` 和最终 POST request；此时没有写入。
- 创建成功返回 `mode: "created"` 与 `rule.ruleId`；更新成功返回 `mode: "updated"` 与目标 `rule.id`。
- 离线结果位于 `data.offline_result`，其中 `rulesId` 是关联规则 ID。
- `countThreshold` 是规则配置的结果条数阈值，不是本次核对的实测行数。
- `instanceStatusCode` / `resultStatusCode` 是状态枚举；`spaceName` 是空间中文名，不是资源 ID。
- `falseReason` 与 `repeatReason` 的列由规则 SQL 动态决定，不要假设固定字段。
- `falseDataLength` / `repeatFalseDataLength` 是后端声明的异常总数；对应的 `falseDataTruncated` / `repeatFalseDataTruncated` 为 `true` 时，当前详情响应只包含部分行，为 `null` 时表示后端未提供总数。
- 这两个详情接口不提供完整结果下载能力。需要完整数据时，不要把预览行当作全量结果。

## Safety

- 输出可能包含业务 SQL、表名、owner 与异常数据，只在授权范围内使用或转发。
- 不要为这些开放接口添加或要求 Cookie、JWT、SSO token。
- Agent 不得自行给创建或更新命令添加 `--yes`。先展示 dry-run 的最终请求；仅在用户明确确认该 payload 后执行同一命令并添加 `--yes`。
- 带 `--yes` 的 POST 出现超时或网络中断时，结果可能已经落库。先用 `hive-rule list/get` 核对，不要盲目重试造成重复规则或覆盖。
- 找不到资源时先确认 ID 类型和来源，不要在规则 ID 与结果 ID 之间反复猜测。

## References

执行 Bamboo 命令时优先使用下列专用 reference；若通用 reference 的登录、SSO 或 token 建议与其冲突，以 Bamboo 无鉴权、仅需办公网的约定为准。

- 执行命令或解释结构化输出时读取：[`references/bamboo-invocation.md`](references/bamboo-invocation.md)
- 准备创建或更新 payload 时读取：[`references/hive-rule-write-payloads.md`](references/hive-rule-write-payloads.md)
- 遇到命令、网络或响应错误时读取：[`references/bamboo-troubleshooting.md`](references/bamboo-troubleshooting.md)
