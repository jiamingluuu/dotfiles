# 群聊信息

使用 `chat get` 按 Oncall 工单 ID 查询该工单关联的群聊消息。这里的 `--flow-id` 是工单 ID，不是飞书群 ID。

```bash
bytedcli oncall chat get --flow-id "<flow-id>" --format text
```

结果对应 `oncall_chat`。JSON 顶层包含 `flow_id`、`chat_id`、`open_chat_id`、`items` 和分页信息；表格按时间、发送人和消息正文展示，并标记工单创建人。`flow_id` 是工单 ID，`chat_id` 是 Oncall 内部群 ID，`open_chat_id` 是飞书群 ID。

- `--flow-id` 必须是整数。
- 用户只给租户或人员条件时，先用 `flow list` 定位工单；候选不唯一时请用户确认。
- 用户要查“前置拦截、GPT/智能体问答记录”时改用 `agent log-list`，不要查询群聊。
- 用户继续查询总结时，使用 `agent summary-get --flow-id "<flow-id>"`。
