---
name: bytedance-temporal
description: "Read-only Temporal cluster queries through bytedcli and a fixed Query Gateway. Use for cluster health, workflow execution metadata/listing, normalized workflow evidence, and task queue poller/backlog inspection needed by business testing."
---

# bytedcli Temporal

## When to use

- 业务测试中确认 workflow 是否启动、完成或失败
- 查看 activity 状态、attempt 和失败摘要，作为测试证据
- 查询 Temporal visibility 列表
- 查看 task queue poller 与 backlog hint
- 检查 Temporal cluster 健康和基础元数据

所有命令都是只读查询。CLI 只访问固定 Query Gateway；Gateway 部署在已开启
Mesh 的运行环境中，并由
Gateway 内的 Temporal SDK client 访问 Temporal。CLI 不连接 Mesh 或 Temporal。

## 前置条件

- Gateway 已部署，并且默认 `master` IDL 包含 Temporal 查询方法
- 知道目标 Temporal `namespace`；`cluster` 默认使用 Gateway 支持的集群
- 使用全局 `--site i18n-tt`（或设置 `BYTEDCLI_CLOUD_SITE=i18n-tt`）
- 推荐把全局 `--json` 放在 `temporal` 前，便于 Agent 解析

## Commands

```bash
# Cluster status and health metadata
bytedcli --json --site i18n-tt temporal cluster status \
  [--temporal-cluster <cluster>]

# Workflow detail
bytedcli --json --site i18n-tt temporal workflow get \
  [--temporal-cluster <cluster>] --namespace <namespace> \
  --workflow-id <workflow-id> [--run-id <run-id>]

# Workflow visibility list
bytedcli --json --site i18n-tt temporal workflow list \
  [--temporal-cluster <cluster>] --namespace <namespace> \
  [--filter '<visibility-query>'] [--page-size 20] \
  [--next-page-token <token>]

# Normalized evidence (does not return payload contents)
bytedcli --json --site i18n-tt temporal workflow evidence get \
  [--temporal-cluster <cluster>] --namespace <namespace> \
  --workflow-id <workflow-id> [--run-id <run-id>] [--max-events 1000]

# Full history with workflow/activity inputs and outputs (explicit payload query)
bytedcli --json --site i18n-tt temporal workflow history get \
  [--temporal-cluster <cluster>] --namespace <namespace> \
  --workflow-id <workflow-id> [--run-id <run-id>] \
  [--page-size 20] [--next-page-token <token>]

# Task queue
bytedcli --json --site i18n-tt temporal task-queue get \
  [--temporal-cluster <cluster>] --namespace <namespace> \
  --task-queue <task-queue> [--task-type workflow|activity]
```

Gateway 默认使用 `env=prod`、`idc=MY2`、`zone=alisg`、`idl-version=1.0.0` 和
`gateway-cluster=c2c`。联调未合入的 Gateway IDL branch 时，增加
`--idl-version <branch> --idl-source branch`；使用 BAM version 时增加
`--idl-version <version> --idl-source bam`。

## Evidence interpretation

- `workflow.status` 是 execution 生命周期状态
- `pending_activities` 来自 workflow describe，只表示当前 pending activity
- `activities` 是限定 history 范围内归一化后的 activity 生命周期证据
- `history_truncated=true` 表示达到 `--max-events`，不能把当前列表当作完整历史
- `--max-events` 默认 1000；达到上限时命令会明确警告 history 不完整
- `result_payload_count` 只返回 payload 数量，不返回 payload 内容
- `failure` 只返回失败摘要，不返回输入/输出 payload
- `log_id` 和 `audit.precheck` 用于定位 Gateway 调用和保留接口测试预检证据

## Full history and payload diff

`workflow history get` requires a deployed Gateway and an IDL version containing
`GetTemporalWorkflowHistory`. An older Gateway/IDL must be upgraded first; the
CLI cannot enable a new Temporal cluster by itself. The Gateway allowlist supports
`scheduler` and `1_31`. `--temporal-cluster` is optional and defaults to
`scheduler`; explicitly pass `--temporal-cluster 1_31` for historical executions
in that cluster. `--temporal-cluster` selects Temporal, while
`--gateway-cluster` selects the Gateway deployment.

The result contains `history.events`, `run_id`, `event_count`, and
`next_page_token`. Keep fetching with the same cluster/namespace/workflow until
`next_page_token` is absent. A page may contain no events and still have a token.
The cursor pins the first page's resolved run; do not reuse it for another
execution. Page size defaults to 20 (1–100), is an upstream page-size hint, and
is independent of the evidence command's `--max-events` cap.

Events use protobuf JSON field names. Workflow input is in
`workflowExecutionStartedEventAttributes.input`; Activity input is in
`activityTaskScheduledEventAttributes.input`; Activity output is in
`activityTaskCompletedEventAttributes.result`. Failed-event attributes retain
failure details. Match Activity completion/failure `scheduledEventId` to the
scheduled event's `eventId`. Follow child execution IDs with separate history
queries; parent history does not inline child history.

Every payload retains `metadata` and `data` as base64 bytes. Decode metadata's
`encoding` first: `json/plain` data can be UTF-8 decoded; custom codecs,
compression, encryption and protobuf payloads require their matching decoder.
Do not interpret unsupported encoding as empty or matching output. Event int64
IDs are strings. When decoding application JSON, use an integer-safe parser
(e.g. Python `json.loads`) for TaskId values larger than JavaScript's safe range.
The CLI does not decode application JSON into potentially imprecise JS numbers.

For a complete diff, finish all pages of both executions and compare inputs,
outputs and failure details alongside normalized evidence. Running executions
can grow after the last fetched page; a finished page sequence is not a snapshot
of a still-running workflow. Keep raw payload output in the authorized test
workspace; do not attach it to public examples or MR descriptions.

## Safety

- 这些命令不提供 start/signal/cancel/terminate/reset 等写操作
- visibility `--filter` 原样交给 Temporal，复杂查询失败时先缩小为简单条件
- 不要把包含敏感信息的 workflow ID、失败摘要或 JSON 输出粘贴到非授权位置
