---
name: ai-approval-ai-auth
description: "AI 策略管控逃逸（AgentGate）。当感知到 AI 策略管控相关场景时——包括 AI API 调用被策略拦截、错误码 40008、blocked_by_strategy、StrategyMsg、agentgate 相关报错——提取证据、确认逃逸范围，并通过安全 helper 自动提交 AgentGate 逃逸工单。"
---

# AgentGate 策略逃逸自动建单

感知策略管控拦截 → 提取证据 → 校验 RecoveryURL → 询问并确认申请参数 → 安全提交 AgentGate 工单。

## 触发条件

| 场景类型 | 典型表现 |
|---|---|
| AI API 调用被策略拦截 | 错误码 `40008`；`Type: blocked_by_strategy`；响应含 `RecoveryURL` |
| 策略命中提示 | 错误信息包含「命中管控策略」、策略名称、策略管理员 |
| 策略审批/逃逸申请 | 用户说"帮我申请工单"、"提交逃逸"、"申请策略审批" |
| AgentGate 关键词 | `agentgate`、`策略管控`、`AI策略`、`管控策略`、`ai-policy` |
| 结构化路由信号 | `next_action.provider == "ai-auth"` |

## 执行流程

### 1. 提取关键信息

从 40008 错误响应中提取：

```json
{
  "Code": 40008,
  "Type": "blocked_by_strategy",
  "Message": "该请求命中管控策略'<策略名>', ...",
  "RecoveryURL": "https://cloud.bytedance.net/open/explorer/ai-policy/apply?type=openapi&strategy_id=<ID>&api_id=<APIID>&account_id=<AccountID>"
}
```

必提取字段：
- `StrategyID` ← RecoveryURL query param `strategy_id`（转 int）
- `AccountID` ← RecoveryURL query param `account_id`
- `APIID` ← RecoveryURL query param `api_id`

### 2. 校验 RecoveryURL

必须使用 URL 解析器验证错误响应中的原始 `RecoveryURL`，不可用字符串拼接重建。只有同时满足以下条件才可展示为操作入口：

- scheme 必须是 `https`。
- hostname 必须精确等于 `cloud.bytedance.net`。
- path 必须精确等于 `/open/explorer/ai-policy/apply`。
- `strategy_id` 必须是正整数。
- `account_id`、`api_id` 必须存在且非空。

任一条件不满足时停止，不打开、不请求该 URL；只保留脱敏后的错误码、类型和策略名称，并提示用户联系策略管理员。

### 3. 确定管控动作

- **approval**（Message 含"审批通过后可访问"）→ 执行步骤 4-6 自动建单
- **deny**（Message 含"拒绝请求"）→ 告知用户无法逃逸，建议联系策略管理员
- **confirm**（Message 含"二次确认"）→ 引导用户在平台完成二次确认，不提交逃逸工单

### 4. 询问并确认申请参数

提交前必须向用户确认逃逸类型、时长/次数和理由。使用以下模板：

---

> **需要你确认以下逃逸申请信息：**
>
> 1. **逃逸类型**：按时长（默认）或按次数
> 2. **逃逸时长/次数**：默认 60 分钟；永久为 -1；按次数时填写正整数
> 3. **申请理由**：说明被拦截操作、策略名称和临时逃逸目的
>
> 可以回复“使用默认值”，或指出需要修改的字段。

---

- 用户说“使用默认值”“确认”“直接提交”：使用 `EscapeType=escape_duration`、`EscapeTime=60`，并从上下文生成可审计 Reason。
- 用户只指定部分字段：未指定字段使用默认值。
- Reason 必须描述实际被拦截操作，不得编造业务背景。
- 未获得用户明确确认前不得执行步骤 5。

### 5. 使用安全 helper 提交

1. 读取 [references/policy-apply.md](references/policy-apply.md) 的输入结构和执行规则。
2. 使用 Agent 的结构化文件写入能力创建权限为 `0600` 的临时 JSON 文件；不要用 shell heredoc、字符串插值或拼接 JSON。字段值必须来自步骤 2 的 RecoveryURL 和步骤 4 的用户确认。
3. 将当前 Skill 目录解析为绝对路径，先执行只校验、不联网的预检：

```bash
node "<ai-auth-skill-dir>/scripts/submit-agentgate-approval.mjs" \
  --input "<private-input-json>" \
  --validate-only
```

4. 预检输出 `status=validated` 后，再执行真实提交：

```bash
set -o pipefail
bytedcli --site cn auth get-bytecloud-jwt-token |
  node "<ai-auth-skill-dir>/scripts/submit-agentgate-approval.mjs" \
    --input "<private-input-json>"
```

helper 固定 AgentGate 端点，重新校验 RecoveryURL 和全部字段，使用 `JSON.stringify` 构造请求，并从 stdin 接收 JWT；JWT 不会出现在命令参数、日志或临时 JSON 中。`--validate-only` 会保留输入文件供下一步提交；真实提交会在联网前安全消费并删除该文件，因此后续认证、网络或业务失败也不会遗留私有输入。

### 6. 输出工单结果

helper 成功时输出稳定 JSON，其中包含 `ticket_id` 和 `ticket_url`。按以下模板回复：

---

> 逃逸工单已创建成功：
>
> - **TicketID**：`<ticket-id>`
> - **工单链接**：`<ticket-url>`
> - **逃逸类型**：按时长 `<minutes>` 分钟 / 按次数 `<count>` 次
> - **策略**：`<strategy-name>`（ID: `<strategy-id>`）
>
> 等策略管理员审批通过后，重新执行原命令即可。

---

失败时只展示 helper 的稳定错误，不展示 JWT 或原始响应体。`100012` 表示策略失效、重复提交或审批配置缺失，建议联系策略管理员；网络结果不明确时先到经过校验的 RecoveryURL 或工单页回查，不自动重放提交。

## 禁止事项

- 不调用通用 `ticket create`——AgentGate 有独立工单体系。
- 不用 `curl`、`fetch`、`httpie` 或临时脚本替代仓库内置 helper。
- 不把 JWT 写入命令参数、环境变量、临时文件、日志或输出；只允许认证命令通过管道写入 helper stdin。
- 不把错误字段或用户输入拼接进 shell、URL 或 JSON；临时输入必须由结构化文件写入能力生成。
- 不重建或改写 RecoveryURL；helper 只接受通过严格校验的原始 URL。
- 不补造 `strategy_id`、`account_id`、`api_id`——必须从实际错误响应提取。
- 不把 AI 策略管控拦截当 IAM 权限问题。
- 不将 token 过期、认证失败等非策略问题路由到此处。
