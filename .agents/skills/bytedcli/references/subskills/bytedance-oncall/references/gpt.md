# 智能问答与记录

| 用户意图 | 命令 |
|---|---|
| 执行智能问答 | `agent execute` |
| 查前置拦截、GPT/智能体问答记录 | `agent log-list` |
| 查工单或群聊总结 | `agent summary-get` |

查询记录需要工单 ID；缺少 ID 时先按 [工单查询](flow.md) 定位。执行智能问答不要求工单 ID。

## `agent execute`

```bash
bytedcli oncall agent execute \
  --tenant-id "<tenant-id>" \
  --region "<region>" \
  --question "如何处理值班计划" \
  --format markdown
```

命令自动确定服务端智能体类型，无需传 `host_type`。区域必须使用已确认的可用值；如果携带 `--flow-id`，按字符串传入。不要为了执行问答而预先创建或查询工单。

输出行为：

- `markdown` 实时输出 SSE 中新增的回答正文。
- `table/text` 等待完成后展示最终回答。
- `json` 输出解析后的 SSE 事件，适合调试。

### 实时转发规则

运行环境支持持续读取命令输出时：

1. 只启动一次 `agent execute --format markdown`，保留命令会话标识。
2. 每 1–2 秒增量读取输出，取得新的非空内容后先作为过程消息展示。
3. 按完整行、段落或约 80–300 个字符分段；不要逐字转发，也不要等待完整回答。
4. 只转发新增 Markdown，保持顺序且不重复；不要展示 SSE 原始事件，也不要用管道、命令替换或文件重定向聚合输出。
5. 命令结束后只给最终状态和简短结论，不重复回答全文。

运行环境无法在命令执行期间读取输出时，正常等待命令结束，不要宣称会话正文已经实时转发。

## `agent log-list`

```bash
bytedcli oncall agent log-list --flow-id "<flow-id>" --format table
```

`--flow-id` 必须是整数。结果对应 `gpt_chat_log`，保留记录 ID、工单 ID、问题、回答、提问人和时间。用户说“前置拦截”时使用本命令，不要查询群聊。

## `agent summary-get`

```bash
bytedcli oncall agent summary-get --flow-id "<flow-id>"
```

`--flow-id` 必须是整数。结果对应 `gpt_summary_detail`，优先使用有效的 `latest_content`，为空时回退到 `origin_content`，并输出总结正文、时间和用户等核心字段。

用户同时需要群聊原文时，再按 [群聊信息](chat.md) 查询；不要把总结结果当成群聊记录。
