# BytedTrace AI 应用观测 Tool

`bytedtrace.*` 命名空间下的 AI 观测 tool，覆盖 AI trace、span 列表检索和 session 轨迹三类场景。与通用的 `bytedtrace.get_trace` 不同，这些 tool 专门面向 GenAI 语义（Agent、Model、Tool、Prompt 等 OpenTelemetry GenAI semantic conventions）。

| Tool                                | 说明                                                     | 必填参数                                  |
| ----------------------------------- | -------------------------------------------------------- | ----------------------------------------- |
| `bytedtrace.get_ai_trace`          | 按 traceID/logID 获取 GenAI trace（仅 AI 相关 span）    | `query_id`                                |
| `bytedtrace.get_span_list`          | 按 PSM 检索 span 列表（server/client/gen_ai 等）        | `psm`                                     |
| `bytedtrace.get_ai_span_list`      | 按 PSM 检索 AI span 列表（agent/model/tool 等 GenAI span）| `psm`                                   |
| `bytedtrace.query_session_index`    | 查询 AI trace session 的 turn 索引列表                   | `psm`、`session_id`                       |
| `bytedtrace.query_session_detail`   | 查询 AI trace session 某个 turn 的详情                   | `psm`、`session_id`、`user_message_id`    |

**与 `bytedtrace.get_trace` 的关系：**

`bytedtrace.get_trace` 是通用 trace 查询（返回全量 span，包含所有 RPC/HTTP/内部 span），不限于 AI 场景。`bytedtrace.get_ai_trace` 与之入参相同（`query_id` 必填），但自动追加 `only_keep_gen_ai` 过滤，只返回 GenAI 语义 span，数据量显著更小。

**`get_span_list` vs `get_ai_span_list`：**

- `get_span_list` 需要显式指定 `category`（span/event/metric）和 `type`（server/client 等），按 PSM 检索对应类型的 span 列表
- `get_ai_span_list` 不需要 category/type，自动限定 GenAI scope，只返回 AI 相关 span
- 两者都支持 `filter_tags` 过滤、时间窗（`start_at`/`end_at`）和 cursor 分页（`context`）

**`query_session_index` / `query_session_detail`：**

通过 MCP tool 接口查询 AI trace session 的 turn 索引和 turn 详情。与 `argos ai-agent-session get` CLI 命令的区别是：CLI 命令在这两个 tool 之上做了多 turn 并发编排和结果聚合，直接 tool 命令则是单次调用。

```bash
# 已知 traceID，只看 AI 相关 span
bytedcli argos tool bytedtrace.get_ai_trace \
  --query-id 5a25e2f7-3063-326c-b0da-6584cc4b7c6e \
  --start-at 1722848400 --end-at 1722852000

# 按 PSM 检索 server span 列表
bytedcli argos tool bytedtrace.get_span_list \
  --psm example.service \
  --category span \
  --type server \
  --duration 1h \
  --limit 50

# 带 tag 过滤
bytedcli argos tool bytedtrace.get_span_list \
  --psm example.service \
  --category span \
  --type server \
  --filter-tags '[{"tag_key":"_status_code","operator":"=","values":["500"]}]' \
  --duration 1h

# 按 PSM 检索 AI span 列表
bytedcli argos tool bytedtrace.get_ai_span_list \
  --psm example.ai.service \
  --duration 1h \
  --limit 50

# 查询 AI session 的 turn 索引
bytedcli argos tool bytedtrace.query_session_index \
  --psm example.ai.service \
  --session-id sample-session-id \
  --access-mode personal

# 查询某个 turn 的详情
bytedcli argos tool bytedtrace.query_session_detail \
  --psm example.ai.service \
  --session-id sample-session-id \
  --user-message-id sample-message-id \
  --access-mode personal
```

**Agent 使用建议：**

- 已知 traceID/logID，只关注 AI span → `get_ai_trace`；需要全量 span → `bytedtrace.get_trace`
- 按 PSM 浏览 span 列表（不知道具体 traceID）→ `get_span_list`（通用）或 `get_ai_span_list`（仅 AI span）
- AI session 轨迹：完整编排用 `argos ai-agent-session get` CLI 命令（多 turn 并发 + 聚合）；单次查索引或某个 turn 详情用 `query_session_index` / `query_session_detail`
- `trace.inspect` 是更高层的工具：先查 trace，再做服务端后处理（识别错误 span、耗时排序、收集 logID），输出结构化诊断 artifact
- `argos ai-agent-session get` 的 `--access-mode` 限定为 `personal|viewer`，默认 `personal`；直接调用 `query_session_index` / `query_session_detail` 时，`access_mode` 仍是后端原始字符串字段，示例显式使用 `personal`
