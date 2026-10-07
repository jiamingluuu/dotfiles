# 权限错误识别与领域路由

Approval 可以识别结构化权限错误、普通 CLI 错误和用户的自然语言描述，但只有可靠的 provider 证据才能触发领域路由。识别权限问题不等于自动提交申请。

## 收集证据

保留经过脱敏的原始证据：

- 来源命令和用户正在执行的动作；
- 原始错误文本、退出码、HTTP 状态和稳定业务错误码；
- `request_id`、log ID 或 trace ID；
- 结构化 `next_action` 和 `approval_context`；
- 明确出现的 provider、服务和资源线索。

删除 token、Cookie、密码、Authorization header 等凭据。不要把来源命令、通用 HTTP 状态或模糊错误文案当作 provider 结论。

结构化错误示例：

```json
{
  "error": {
    "type": "authorization",
    "request_id": "req_001",
    "next_action": {
      "kind": "approval",
      "provider": "iam",
      "operation": "iam.role.apply"
    },
    "approval_context": {
      "domain_fields": "opaque to approval"
    }
  }
}
```

当 `next_action.kind=approval` 且 provider 存在时，按 provider 路由；把 `operation`、`approval_context` 和 `request_id` 原样交给目标领域，不在 Approval 中解释或补全领域字段。

## Provider 判定顺序

1. 使用结构化 `next_action.provider`。
2. 使用错误中明确的 provider、稳定错误码或目标领域给出的安全动作。
3. 查询原业务 Skill、当前 CLI 帮助或可信文档对权限归属的明确说明。
4. 用户明确指出 provider 时，允许路由目标领域复核，但仍不自动申请。
5. 证据仍不足时报告 `provider_unknown`，保留证据并停止。

裸 `401`、`403`、`Forbidden`、`Permission Denied`，或者仅仅来自 RDS、DBW 等某个命令，都不足以默认映射到 IAM。证据表明是 token 过期或未登录时，回到原入口做认证排障。

## IAM

当 provider 可靠确定为 `iam` 时：

1. 保留并脱敏来源错误、`operation`、`approval_context`、request/log/trace ID。
2. 切换到 `bytedcli iam` Skill / CLI 进行鉴权、角色或策略分类、申请和结果重查。
3. 由 IAM 的实时结果决定申请类型和参数；Approval 不解释 IAM 业务字段。
4. IAM 能力不可用时，说明缺失依赖并停止，不用 `ticket create` 代替。

不要根据 `next_action.operation` 自行推导角色申请、策略例外、BRN 或权限范围。

## AI Auth（AgentGate）

当 provider 可靠确定为 `ai-auth`（错误码 40008、`blocked_by_strategy`、Message 含「命中管控策略」）时：

1. 保留并脱敏原始上下文（策略 ID、account_id、api_id、管控动作、管理员列表）。
2. 立即切换到 `ai-approval-ai-auth` Skill 执行安全自动建单流程（提取证据 → 严格校验原始 RecoveryURL → 询问并确认参数 → 通过内置 helper 提交 → 输出工单链接）。
3. 不调用通用 `ticket create`——AgentGate 有独立工单接口。

## 行为矩阵

| 输入 | 行为 |
|---|---|
| `next_action.provider=iam` | 路由 `bytedcli iam`，原样传递脱敏证据 |
| 用户明确说明是 IAM | 路由 IAM 做实时复核，不自动申请 |
| `next_action.provider=ai-auth` 或 40008 `blocked_by_strategy` | 路由 `ai-approval-ai-auth` 校验 RecoveryURL、确认参数并自动提交逃逸工单 |
| 裸 403 / Permission Denied | 继续识别；无可靠证据则 `provider_unknown` |
| 401 且证据表明认证过期 | 回到原 CLI 认证，不进入审批路由 |
| provider 无法确认 | 保留证据、报告 `provider_unknown`、停止 |
