---
name: bytedance-super-relay
description: "Use bytedcli to investigate Super Relay model traces and sessions, download complete payloads, find exact output/protocol corruption across every list page, inspect existing trace feedback, and preview or submit trace-linked feedback after explicit confirmation. Also list the model catalog with per-model health, fetch performance metrics and SLOs, and print quick-start connection settings for a model. Trigger on Super Relay, model bad case, repeated output, leaked tool_call/function-call markers, trace/session correlation, payload Response Body, feedback submission, model health, model SLO, model metrics, or quick-start configuration."
---

# bytedcli Super Relay Observability

## 入口

```bash
bytedcli super-relay --help
bytedcli super-relay trace --help
bytedcli super-relay feedback --help
bytedcli super-relay model --help
```

认证固定使用 CN ByteCloud credential partition，不要打印、保存或复制 JWT。非 CN 默认站点下显式传全局参数 `--site cn`：

```bash
bytedcli --site cn auth status
bytedcli --site cn auth login
```

## 调查原则

1. 用具体时间、用户和模型缩小候选 Trace。
2. 列表接口只包含元数据；异常文本必须以完整 Trace Payload 为准。
3. 优先检查 `response_body`，这是客户端 Payload 页面 **Response Body** 的对应字段。
4. `upstream_response_body` 用于判断异常是否已经存在于上游输出。
5. `request_body` / `upstream_request_body` 只用于判断异常是否被后续会话历史携带，不能证明当前响应首次产生了异常。
6. 不依赖平台 Prompt Search 判断模型输出是否存在某段文本；使用完整分页、Payload 下载和本地精确匹配。

## Trace 列表与分页 shorthand

单页查询默认使用 `--page 1 --page-size 20`：

```bash
bytedcli --json super-relay trace list \
  --since 2026-01-02T03:04:05Z \
  --user demo-user@example.com \
  --model 'sample-model-*'
```

`--all-pages` 是完整分页 shorthand。它优先沿用服务端 `next_cursor`，仅在无 cursor 时回退 offset：

```bash
bytedcli --json super-relay trace list \
  --hours 24 \
  --model 'sample-model-*' \
  --page-size 20 \
  --all-pages
```

可直接传平台原始过滤表达式，并与 shorthand 通过 `AND` 组合：

```bash
bytedcli --json super-relay trace list \
  --filter 'status_code >= 500' \
  --since 2026-01-02T03:04:05Z \
  --all-pages
```

若达到 `--max-pages`，返回结果会标记 `truncated`；缩小时间窗或调大上限后重试。重复页会以 `SUPER_RELAY_PAGINATION_STALLED` 失败，避免把不完整数据误报为完整。

## `trace search`：下载并本地精确匹配

`trace search` 是调查异常输出的主路径：自动完整分页、下载完整 Payload、原子写入本地目录，再做区分大小写的固定字符串匹配。Payload 下载默认 `--concurrency 1`，避免在桌面环境制造不必要的并发负载。省略 `--output-dir` 时，每次运行都会在系统临时目录下新建不可预测、仅当前用户可访问的目录。

```bash
bytedcli --json super-relay trace search \
  --hours 24 \
  --model 'sample-model-*' \
  --pattern 'tool_call>' \
  --output-dir ./super-relay-payloads
```

需要搜索多个异常片段时，在**同一个命令**中重复传 `--pattern`。命令只分页一次、每个 Trace 只下载一次，然后在本地同时匹配全部 pattern：

```bash
bytedcli --json super-relay trace search \
  --hours 2 \
  --model 'sample-model-*' \
  --pattern 'tool_call>' \
  --pattern 'seed:tool_call' \
  --pattern '<function name=' \
  --output-dir ./super-relay-payloads
```

禁止按 pattern、时间分片或 Session 启动多个并行 `bytedcli ... trace search` 进程。网络请求阻塞不代表进程没有本地成本：每个进程都会独立加载 CLI/Auth runtime、重复请求相同的列表页并重复下载 Payload；多个进程会叠加内存、认证和磁盘写入负载，导致整机卡顿。

已有 `trace list --all-pages` 的完整 JSON 结果时，直接用 `--list-file` 复用候选集合，不再请求列表页：

```bash
bytedcli --json super-relay trace search \
  --list-file ./complete-traces.json \
  --pattern 'toolcall_count=167' \
  --concurrency 1 \
  --output-dir ./super-relay-payloads
```

禁止编写 Python `ThreadPoolExecutor`，在每个 Worker 中运行一次 `bytedcli ... trace get`。`--workers 8` 实际会同时启动 8 个完整 Node/CLI 进程，而不是 8 个轻量网络请求；按单进程约 467 MB RSS 估算，仅这些子进程就可能占用约 3.7 GB，并重复执行 CLI 初始化和认证。

候选 Trace 数量不设上限，以支持完整的大批量扫描。桌面环境保持 `--concurrency 1`；只有用户明确需要时才提高，允许范围为 1–4。大批量扫描耗时较长是正常现象，不要通过启动多个 CLI 进程来提速。

默认只搜索 `response_body`。需要对比上游响应时：

```bash
bytedcli --json super-relay trace search \
  --filter 'status_code = 200' \
  --pattern 'sample-protocol-marker' \
  --fields response-body,upstream-response-body \
  --output-dir ./super-relay-payloads
```

仅在判断历史污染时添加请求字段：

```bash
bytedcli --json super-relay trace search \
  --hours 24 \
  --pattern 'sample-protocol-marker' \
  --include-history
```

字段名：

- `response-body`
- `upstream-response-body`
- `request-body`
- `upstream-request-body`

不要把 search miss 改成逐步模糊搜索，也不要因此断言 Trace 不存在；先检查过滤范围、分页是否完整和目标字段是否正确。需要尝试多个精确片段时，重复 `--pattern` 合并到同一进程。

## 获取单个完整 Payload

```bash
bytedcli --json super-relay trace get \
  --trace-id 00000000-0000-4000-8000-000000000000 \
  --compact

bytedcli super-relay trace get \
  --trace-id 00000000-0000-4000-8000-000000000000 \
  --output ./trace.json
```

对候选 Trace 核对：

- Trace ID、Session ID、Request ID、绝对时间。
- `requested_model`、`published_model`、`resolved_model`、`provider_model`。
- HTTP 状态、输入/输出 Token、chunk 数、TTFT、Latency。
- 同一 Session 中紧邻的前后 Trace。
- 异常最早出现于上游响应、转换后响应，还是后续请求历史。

## Model 命令

`super-relay model` 提供模型目录、健康状态、性能指标、SLO 与快速开始配置。

模型使用 canonical model id 作为唯一标识，格式为 `provider_type/name`（如 `sample-catalog/sample-model`）。所有 `--id` 传入 canonical model id，CLI 负责路径转义；不要传模型短名或列表中的内部 UUID。

```bash
bytedcli super-relay model list --all-pages
bytedcli --json super-relay model list --all-pages
```

`health_status` 枚举为 `healthy` / `unknown` / `unhealthy`。列表 `-j` 输出模型全字段，消费方按健康状态、上下文长度、错误数自行筛选。

查询单模型完整档案与健康状况：

```bash
bytedcli super-relay model get --id sample-catalog/sample-model
bytedcli --json super-relay model get --id sample-catalog/sample-model
```

查询单模型性能指标，时间窗仅支持 `1h`（分钟级）与 `3d`（小时级）：

```bash
bytedcli --json super-relay model metrics --id sample-catalog/sample-model --window 1h
bytedcli super-relay model metrics --id sample-catalog/sample-model --window 3d --points 5
```

`-j` 始终包含完整 `series` 时间序列；文本模式默认只输出 summary 聚合，`--points <n>` 展开最近 n 个时间桶。

查询单模型 SLO（可用性与达标状态）：

```bash
bytedcli super-relay model slo --id sample-catalog/sample-model --window 1h
```

可用性与错误预算来自 `objectives.availability`（target / actual / met）与 `overall_status`；未配置的 SLO 字段输出 `not configured`。

输出「快速开始」配置参数与各客户端示例（端点、headers、环境变量、curl / shell）：

```bash
bytedcli super-relay model quickstart --id sample-catalog/sample-model
bytedcli --json super-relay model quickstart --id sample-catalog/sample-model --client claude-code --client codex
```

`--client` 取值：`openai-chat` / `openai-responses` / `anthropic` / `claude-code` / `codex` / `trae` / `managed` / `hybrid`，可重复传入；不传则输出全部客户端示例。API key 一律以占位符 `<your-api-key>` 输出：到 Super Relay 平台页面「Quick Start」获取，或找平台管理员申请。

## 查询已有反馈

```bash
bytedcli --json super-relay feedback list \
  --trace-id 00000000-0000-4000-8000-000000000000
```

优先使用 Trace scoped 查询。全局反馈页面没有权限，不代表 Trace scoped 查询或创建反馈不可用。

## 快速上报 Bad Case

上报前先复核完整 Payload、实际模型和已有反馈。第一次执行不带 `--yes`，只生成规范化 Payload 预览：

```bash
bytedcli --json super-relay feedback submit \
  --trace-id 00000000-0000-4000-8000-000000000000 \
  --rating bad \
  --category model_issue \
  --comment-file ./feedback.md \
  --require-model 'sample-model-*'
```

`--require-model` 只检查 Trace 的 `requested_model` 和 `resolved_model`；不匹配时拒绝提交并返回全部模型字段。

必须完整展示预览命令返回的 Payload，然后停止并等待用户在后续消息中明确确认该 Payload。不能在第一次展示预览的同一轮自动追加 `--yes`。

用户确认后，原样重跑并添加 `--yes`：

```bash
bytedcli --json super-relay feedback submit \
  --trace-id 00000000-0000-4000-8000-000000000000 \
  --rating bad \
  --category model_issue \
  --comment-file ./feedback.md \
  --require-model 'sample-model-*' \
  --yes
```

命令会在 POST 前检查完全相同的反馈；默认返回 `already_exists` 而不重复提交。只有用户明确要求再创建一条完全相同的记录时才使用 `--allow-duplicate`。提交后命令会重新查询 Trace feedback，并输出按 feedback ID 和 Payload 的验证结果。

## 反馈证据标准

反馈正文至少包含：

- 精确 Trace ID、Session ID、Request ID、模型字段和绝对时间。
- 最早包含异常的 Trace。
- 异常位于上游响应、转换响应、请求历史或仅存在于客户端。
- 相邻正常/失败 Trace 的对比。
- 无法从持久化 Payload 证明的内容必须标为推断。

HTTP 200 不代表流式协议一定正常。对 completion/parser 异常分别记录持久化 Trace snapshot、observation 聚合、原始 terminal SSE 是否可用以及客户端错误证据。
