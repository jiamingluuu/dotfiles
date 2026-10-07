---
name: bytedance-cloud-approval
description: "查询和处理 Approval / Cloud Ticket 审批工单，并识别权限错误后路由到 IAM 或 AI Auth。用于通过 bytedcli cloud-approval 查询我发起、待我审批、审批历史和可见工单，查看详情，创建、通过、拒绝、退回、知会、加签、移交或撤销，以及处理权限不足、Forbidden、next_action、provider=iam、provider=AI 策略管控（AgentGate） 等场景。"
---

# Approval CLI

## When to use

- 查询我发起的工单、与我审批相关的工单、当前身份可见的工单
- 查看工单详情、表单参数和审批历史
- 创建通用审批工单
- 执行审批动作：通过、拒绝、退回、知会、加签
- 移交审批节点
- 撤销申请
- 查询平台支持的站点和 VRegion
- 处理权限拦截：IAM 权限路由或 AI 策略管控（AgentGate）逃逸自动建单

## Quick start

```bash
# 查询工单
bytedcli cloud-approval apply list --page 1 --page-size 10
bytedcli cloud-approval audit list --ticket-status-list 3 --page 1 --page-size 10
bytedcli cloud-approval notice list --approval-source iam --keyword permission

# 查看工单详情
bytedcli cloud-approval ticket get --ticket-id '1000000000000000001' --flow-type 1

# 审批动作（先预览，确认后追加 --yes）
bytedcli cloud-approval ticket execute --ticket-id '1000000000000000001' --flow-type 1 --action pass --desc approved
```

## Agent execution rules

- 查询类命令可直接执行。写命令不带 `--yes` 时默认 dry-run，不发送写请求。
- 向用户展示预览并核对工单、流程、节点、动作和接收人；只有用户明确确认后，保持业务参数不变并追加 `--yes`。
- `ticket execute` 不能代替 `ticket cancel` 或 `ticket auditor update`；撤销和移交必须使用各自的独立命令。
- 写请求超时或结果不明确时，先用 `ticket get` 回查状态，不盲目重试。
- 分页查询只取所需页；若需遍历全量结果，逐页递增 `--page` 直到返回空列表或达到 `total`，不要一次请求超大 `--page-size`。
- `error.retryable=true` 时可自动退避重试（建议最多 2 次、间隔 2-5 秒），其余错误不自动重试。
- 参数或输出不确定时优先查看对应命令的 `--help`，不要猜测位置参数。
- 遇到 `AUTH_REQUIRED` 或 `authenticated failed` 时，不要直接判定为"失败"——输出错误中的 `auth_command`（如 `bytedcli --site <site> auth login`）引导用户认证，告知认证后可重试。
- 用户 Query 中提到站点（如"USTTP工单""i18nTT工单""EUTTP工单""i18nBD工单"）时，自动映射为对应 `--site`（us-ttp、i18n-tt、eu-ttp、i18n-bd），不要在 cn 站点查询其他站点的工单。
- 需要 `--flow-type` 但用户未提供时，按顺序尝试：`audit list --ticket-id`、`notice list --ticket-id`、`apply list --ticket-id`；取命中结果中的 flow_type。三者都命中 0 条时才报无法确认。
- `ticket create` 信息不足时（缺 flow-id/form-id/apply-params），列出缺失的必填参数向用户追问，不要直接拒绝执行。

## Agent safety rules

- 把 `--ticket-id` 和 `--node-instance-id` 始终作为字符串；不得转成 JavaScript `Number` 或浮点数。
- `--node-instance-id` 可重复；只使用可信工单详情中的节点。
- 不得把工单 ID、节点配置 ID 和节点实例 ID 混用。
- 稳定消费结果时使用 `--json`，并把全局参数放在 domain/command 前面。
- 认证状态按 Binary/Host 隔离；`bytedcli cloud-approval` 使用宿主注入的 JWT，独立入口使用各自 Binary 的登录态。
- 不输出或记录 JWT、Cookie、Authorization header 或其他凭据。

## Intent mapping

| 用户意图 | 命令 |
|---|---|
| `pass`（通过） | `ticket execute --action pass` |
| `reject`（拒绝） | `ticket execute --action reject` |
| `notice`（知会） | `ticket execute --action notice` |
| `transfer`（移交） | `ticket auditor update` |
| `cancel`（撤销申请） | `ticket cancel` |
| `remind`（催办） | `ticket reminder send`（自动校验可催办状态后发送） |

`notice list` 是当前身份可见工单的查询命令，不会执行知会；知会使用 `ticket execute --action notice`。`revert` 是审批人把节点退回，`cancel` 是申请人撤销申请，两者不能替代。

## Command groups

| Area | Commands |
|---|---|
| 工单列表 | `apply list`, `audit list`, `notice list` |
| 工单操作 | `ticket get`, `ticket create`, `ticket execute`, `ticket auditor update`, `ticket cancel`, `ticket reminder send` |
| 平台元数据 | `platform vregion list` |

## 权限错误路由

遇到权限报错（结构化 next_action、普通 stderr 或用户转述）时，按以下信号识别 provider 并切换到对应 Skill：

### IAM 权限 → 读取 [ai-approval-iam/SKILL.md](ai-approval-iam/GUIDE.md)

触发信号：`permission denied`、`authorization denied`、RBAC/SCP 拦截、缺少权限点、`next_action.provider == "iam"`、用户主动查询/申请 IAM 角色或策略。

### AI 策略管控（AgentGate）逃逸 → 读取 [ai-approval-ai-auth/SKILL.md](ai-approval-ai-auth/GUIDE.md) 并立即执行

触发信号：错误码 `40008`、`blocked_by_strategy`、错误信息包含「命中管控策略」、`StrategyMsg`、`RecoveryURL` 指向 `cloud.bytedance.net/open/explorer/ai-policy/apply`、URL 含 `/ai-policy`、`agentgate`、`策略管控`、`AI策略`、`next_action.provider == "ai-auth"`、用户提到策略逃逸/策略审批。

**自动触发规则**：一旦识别到上述任一信号，不要停在"被拦截了"的诊断输出——必须立即读取并执行 `ai-approval-ai-auth/SKILL.md` 中定义的安全建单流程（提取证据 → 严格校验原始 RecoveryURL → 询问并确认参数 → 通过内置 helper 自动提交 → 输出工单链接）。不需要用户额外说"帮我建单"才触发。

### 识别原则

- 不要把 AI 策略管控拦截当成 IAM 权限问题；40008 + `blocked_by_strategy` 是策略管控，不是 IAM RBAC。
- 裸 401/403 不能单独证明 provider；无法可靠识别时报告 `provider_unknown` 并停止路由。
- 不从错误文本补造 provider、BRN、策略 ID 或审批上下文。

## References

- [cloud-approval.md](./references/cloud-approval.md)
- [invocation.md](./../../invocation.md)
- [providers.md](./references/providers.md)
- [troubleshooting.md](./../../troubleshooting.md)
