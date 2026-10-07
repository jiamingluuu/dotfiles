# Oncall 常用概念

本文件用于把用户的自然语言说法映射到 oncall 命令使用的标准概念、参数名和命令。

| 标准概念 | 含义 | 用户可能的说法 | 如何获取 | 关联命令 |
|----------|------|----------------|----------|----------|
| `oncall_flow_id` | oncall 工单 ID | 工单 ID、oncall 工单 ID、flow ID、oncall flow ID | 用户直接提供，或通过 `flow list` 查询结果获取 | `flow get`, `flow timeline`, `chat get`, `agent log-list`, `agent summary-get` |
| `oncall_flow` | oncall 工单 | 工单、oncall 单、flow、oncall flow | 通过 `flow list` 列表查询，或通过 `flow get` 精确查询 | `flow list`, `flow get`, `flow timeline` |
| `tenant_id` | 租户 ID，oncall 租户 ID | 租户 ID、oncall 租户 ID、tenant ID | 用户直接提供，或通过 `tenant search` / `tenant get` 辅助定位 | `flow list`, `duty-user get` |
| `tenant` | oncall 租户 | 租户、oncall 租户、tenant | 通过 `tenant get` 精确查询，或通过 `tenant search` 列表/模糊查询 | `tenant get`, `tenant search` |
| `oncall_chat` | oncall 群聊 | 群聊、工单群、oncall 群、oncall 群聊、chat | 通过 `chat get --flow-id <id>` 获取 | `chat get` |
| `gpt_chat_log` | GPT 问答记录、智能体问答记录、前置拦截记录 | 问答记录、智能体记录、前置拦截、GPT 对话、GPT 问答、聊天记录 | 通过 `agent log-list --flow-id <id>` 获取 | `agent log-list` |
| `gpt_summary_detail` | oncall 群聊总结、工单总结记录、GPT 总结记录 | 总结、群聊总结、工单总结、GPT 总结、summary detail | 通过 `agent summary-get --flow-id <id>` 获取 | `agent summary-get` |

## 使用建议

- 用户提到“工单 ID”时，优先理解为 `oncall_flow_id`。
- 用户提到“工单”或“oncall 单”时，优先理解为 `oncall_flow`。
- 用户提到“租户 ID”时，优先理解为 `tenant_id`。
- 用户提到“群聊”或“工单群”时，优先理解为 `oncall_chat`，通常需要 `oncall_flow_id`。
- 用户提到“前置拦截”“智能体问答”或“GPT 问答”时，优先使用 `gpt_chat_log` 相关命令。
- 用户提到“总结”“群聊总结”或“工单总结”时，优先使用 `gpt_summary_detail` 相关命令。
- 缺少 `oncall_flow_id` 且用户提供了人员、租户、区域、分类、状态、关键词或时间范围时，优先用 `flow list` 找候选工单；否则先追问。
