# MindAI 图表事件契约

客户端把 MindAI CreateTask、ResumeTask 和 Events SSE 帧归一化为紧凑的本地 Agent 事件。本契约只覆盖 MindAI 任务和 SVG，不覆盖飞书文档、画板或 Canvas。

## 远端接口

- 创建任务：`POST /mindai/deep_research/api/tasks`
- 继续任务：`POST /mindai/deep_research/api/tasks/resume`
- 监听事件：`POST /mindai/deep_research/api/tasks/events`
- 模板执行：`POST /mindai/wiki/apiai/executeSopTemplate`

CreateTask 和模板执行返回的任务 ID 是 Resume、Events 和 MindAI 会话链接共用的唯一标识，客户端统一称为 `task_id`。

## 监听语义

`execute`、`watch`、`svg download` 和 `template execute` 默认使用 `--until svg`：

- `svg_ready`：成功停止。
- `error`：失败停止。
- `needs_input`：向调用方暴露补充输入需求，但不会自动 Resume。
- 心跳或 SSE 静默：继续等待，并按 `--waiting-interval-ms` 输出本地进度。

`--until never` 只用于明确需要持续监听的调用方。客户端不支持 `board` 或 `done` 交付条件，也不会自动提交飞书导出指令。

## 归一化事件

### `progress`

表示任务启动、用户输入、图表生成进度或本地等待状态。常用字段：

- `task_id`
- `event_id`
- `stage`
- `message`
- `raw_event_type`

### `needs_input`

表示服务端等待用户补充要求。常用字段：

- `task_id`
- `event_id`
- `message`
- `can_continue`

调用方只有在用户提供了明确补充内容时，才使用 `update --task-id <id> --prompt <text>`。

### `svg_ready`

表示最终 SVG 已生成：

- 客户端把 SVG 保存到 `~/.local/share/bytedcli/data/mindai/chart/tasks/<task_id>.svg`。
- JSONL 默认只输出 `svg_path` 和 `svg_chars`，不输出完整 SVG。
- 只有显式 `--include-svg` 才在 JSONL 中包含 `svg`。

### `error`

表示远端不可恢复错误。错误消息在输出前会经过脱敏和长度限制。

### `summary`

命令结束时的汇总，只包含：

- `task_id`
- `svg_path`（已生成时）
- `mindai_chat_url`

summary 不包含飞书文档、画板或 Canvas 字段。

## 本地状态

任务状态保存在：

```text
~/.local/share/bytedcli/data/mindai/chart/tasks/<safe_task_id>.json
```

只持久化恢复监听和缓存命中所需字段：

- `task_id`
- `last_event_id`
- `svg_path`
- `updated_at`

不持久化 query、标题、内联 SVG、授权信息、附件正文或跨域交付状态。

## SSE 信封

`mindai_wiki` 业务事件位于外层 SSE `data:` JSON 的 `event` 字段中：

```json
{
  "event": {
    "id": "message-id",
    "event": "type_svg",
    "data": "{\"event_type\":\"type_svg\",\"response_type\":\"svg_final\",\"content\":\"...\"}"
  }
}
```

`Last-Event-ID` 优先使用本地状态里的最后业务事件 ID；没有记录时从 `0` 开始。不要把业务 payload 的 sequence 字段当作 SSE 游标。

客户端识别的远端事件映射：

- `task_start`、`graph_progress`、`user_input` → `progress`
- `graph_clarification_text`、`user_interaction_required` → `needs_input`
- `type_svg response_type=svg_final` → `svg_ready`
- `task_error` 或 `*_error` → `error`

其他事件，包括历史飞书交付事件，不进入本技能的稳定输出契约。
