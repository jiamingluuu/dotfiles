# Slardar CAT Agent 调用流程

通过 `slardar web chat` 命令调用 Slardar CAT Agent，一条命令完成监控数据查询、问题诊断、归因分析等任务。

## 流程

### 1. 发起对话

```bash
bytedcli --json slardar web chat send --input "<问题或任务描述>"
```

`--space-id` 可选；不传时使用当前用户的 active Space。

返回字段：

| 字段         | 说明                       |
| ------------ | -------------------------- |
| `thread_id`  | 后续轮询、继续对话使用     |
| `run_id`     | 本次运行 ID                |
| `status`     | 当前运行状态               |
| `space_id`   | 该对话所属 Space           |
| `thread_url` | 可在浏览器中打开的对话链接 |

### 2. 流式输出（推荐）

加 `--stream` 实时获取 Agent 的 NDJSON 输出流；流式模式必须同时使用 `--json`：

```bash
bytedcli --json slardar web chat send --input "<问题>" --stream
```

流式模式每行输出一个 JSON 事件，包括 `thread_created`、`user_input`、`message`（含 AI 回复 chunks）、`token_usage`、`complete`、`done`。输出只保留公开字段；`user_input` 仅包含输入长度等元数据，不回显原始问题文本，`complete` 仅包含 run 状态与最终结果。

### 3. 轮询等待结果（非流式）

非流式场景使用 `thread_id` 查询状态：

```bash
bytedcli --json slardar web chat get --thread-id <thread-id>
```

`status` 为 `pending` 或 `running` 时等待后重试；`result` 有内容时即为 Agent 最终输出。
少数情况下 run 先进入 `success`，最终消息稍后才写入 state；若 `result` 仍为 `null`，等待数秒后重试 `get`。

加 `--full` 获取完整消息列表：

```bash
bytedcli --json slardar web chat get --thread-id <thread-id> --full
```

### 4. 下载单个产物

如需下载 `chat get` 结果中的 `local_file` 产物：

```bash
bytedcli --json slardar web chat download-artifact \
  --thread-id <thread-id> \
  --path '<artifact-path>'
```

team/user 产物分别补充 `--space-id` / `--user-id`；需要指定保存位置时加 `--output`，否则保存到当前目录并使用 artifact basename。已有同名文件不会被覆盖，`--output` 的父目录需要预先存在。

### 5. 继续已有对话

多轮协作时使用同一 `thread_id`：

```bash
bytedcli --json slardar web chat send --thread-id <thread-id> --input "<补充信息或追问>"
```

### 6. 取消运行

```bash
bytedcli --json slardar web chat cancel --thread-id <thread-id>
```

### 7. 列出对话

```bash
bytedcli --json slardar web chat list
bytedcli --json slardar web chat list --space-id <space-id> --thread-source bytedcli --page-size 10
```

支持 `--thread-source`（bytedcli/cli/web/lark_group/lark_p2p/scheduled_plan/manual_plan/alarm_plan）、`--created-by`、`--page`、`--page-size` 筛选。

### 8. 检查授权

```bash
bytedcli --json slardar web chat check-auth
```

## 注意事项

1. 直接查指标、日志、看板、报警时，确定性命令更快更精确。
2. Chat 适合交给 CAT Agent 做开放式分析、诊断、复杂任务处理或多轮协作。
3. 不要在 `--input` 中粘贴 JWT、Cookie、Token 等敏感信息。

## 调用约束

- 同一上下文的一批分析合并为一次 `chat send`；只有独立上下文才新建 thread。
- 批量调用先归并同类子任务，小批量并发发起。
- 同一问题链路复用首次返回的 `thread_id`；补充信息、追问、修正参数和分阶段分析都追加到原 thread。
- 轮询 `chat get` 间隔 10-20 秒；长时间运行或失败重试时使用递增退避。
