# bytedcli labelgpt Managed Agent

Managed Agent 由 Agent Harness 托管运行规范，在 LabelGPT 中保存为 `PlanType=2` Agent。CLI 支持发现可挂载资源、创建、更新、查看、同步运行，以及把已发布 Managed Agent 加入普通 Agent 工作流。

## 快速导航

- `agent managed list`：列出当前 Space 中的 Managed Agent。
- `agent managed skills|mcps|hooks`：查询 Agent Harness 资源目录。
- `agent managed create`：创建并发布 Managed Agent。
- `agent managed update`：保留未指定字段，更新并发布 Managed Agent。
- `agent managed view`：查看 LabelGPT 方案和 Harness 配置。
- `agent managed run`：用普通文本 prompt 运行并等待结果。
- `agent workflow add-managed-agent-node`：把 Managed Agent 加入普通工作流。

## 资源发现

```bash
bytedcli labelgpt agent managed skills --query repository --official --format raw
bytedcli labelgpt agent managed mcps --query browser --scope public --format raw
bytedcli labelgpt agent managed hooks --query review --format raw
```

三类命令均支持 `--page-num` 和 `--page-size`。Skill 还支持 `--group`、`--official`，MCP 支持 `--scope`。`raw/json` 输出固定包含 `items`、`total`、`page_num` 和 `page_size`；创建参数中的资源引用优先使用返回的 `ref`。

## 创建与更新

```bash
bytedcli labelgpt agent managed create \
  --name repo_assistant \
  --runtime codex \
  --work-dir /workspace \
  --model-id <MODEL_ID> \
  --system-instructions-file ./SYSTEM.md \
  --developer-instructions-file ./AGENTS.md \
  --reasoning-effort high \
  --skill <SKILL_REF> \
  --mcp '{"id":"<MCP_REF>","version":"<VERSION>"}' \
  --space-id <SPACE_ID> \
  --format raw

bytedcli labelgpt agent managed update --id <PLAN_ID> \
  --model-id <NEW_MODEL_ID> \
  --clear-hooks \
  --format raw
```

- 创建默认 runtime 为 `codex`、工作目录为 `/workspace`、目标语言和 i18n 为 `zh-CN`，当前用户自动成为 owner；可重复传 `--owner-user-id` 显式覆盖。
- `--system-instructions` 与 `--system-instructions-file` 互斥；developer instructions 同理。
- `--skill`、`--mcp`、`--hook` 可重复，每项可直接传 catalog `ref`，也可传包含 `id/name/version/extra` 的 JSON object。
- 更新会先读取 Managed Agent 详情和普通 Agent 方案详情，只覆盖显式字段。任一资源 flag 都替换该类完整列表；清空分别使用 `--clear-skills`、`--clear-mcps`、`--clear-hooks`。
- 并发版本冲突时先重新 `view` 再重试；只有用户明确要求覆盖当前最新版本时才使用 `--force-save`。

`raw/json` 输出为更新后的完整详情，包含 `plan_id`、Harness 侧 ID/版本/发布状态、runtime、模型、instructions、资源引用和固定 I/O。

## 查看与运行

```bash
bytedcli labelgpt agent managed view --id <PLAN_ID> --format raw

bytedcli labelgpt agent managed run --id <PLAN_ID> \
  --input "inspect the repository and summarize the failing tests" \
  --image-url https://example.com/context.png \
  --format raw
```

- `run --input` 接受普通文本，不是 JSON；也可用 `--input-file <PATH>`，或 `--input -` 从 stdin 读取。
- CLI 会把 prompt 写入 Agent debug 需要的 `managed_agent_input` 数据字段，并兼容写入执行节点内部使用的 `input`；`--image-url` 可重复并写入 `image_urls`。
- `--poll-interval` 默认 `500ms`、最小 `100ms`；`--wait-timeout` 默认 `30m`。
- `raw/json` stdout 只输出最终 `agentDebugOutput`；进度写 stderr。异常节点和超时都会先输出最后结果，再以非零状态退出。

## 加入普通工作流

```bash
bytedcli labelgpt agent workflow pull \
  --id <PARENT_AGENT_ID> --file /tmp/agent_workflow.json --format raw

bytedcli labelgpt agent workflow add-managed-agent-node \
  --file /tmp/agent_workflow.json \
  --node-key coder \
  --managed-agent-id <MANAGED_AGENT_PLAN_ID> \
  --format raw

bytedcli labelgpt agent workflow add-edge \
  --file /tmp/agent_workflow.json --from <UPSTREAM_KEY> --to coder --format raw
bytedcli labelgpt agent workflow validate --file /tmp/agent_workflow.json --format raw
bytedcli labelgpt agent workflow commit \
  --file /tmp/agent_workflow.json --space-id <SPACE_ID> --format raw
```

`add-managed-agent-node` 和 `update-managed-agent-node` 会验证目标类型，并用 Agent 调用节点 `10349` 选择已发布版本、默认同步输入输出。已发布版本通常暴露 `managed_agent_input` / `managed_agent_result`，缺失的输出 alias 会由 CLI 使用字段 key 兜底。只改版本配置而不覆盖节点 I/O 时使用 `--no-sync-io`。Managed Agent 自身方案中的 `1013` 是内部执行节点，不要直接拼入普通工作流。

## Schema 查询索引

```bash
bytedcli labelgpt schema agent managed list --format raw
bytedcli labelgpt schema agent managed create --format raw
bytedcli labelgpt schema agent managed update --format raw
bytedcli labelgpt schema agent managed view --format raw
bytedcli labelgpt schema agent managed run --format raw
bytedcli labelgpt schema agent managed skills --format raw
bytedcli labelgpt schema agent managed mcps --format raw
bytedcli labelgpt schema agent managed hooks --format raw
bytedcli labelgpt schema agent workflow add-managed-agent-node --format raw
bytedcli labelgpt schema agent workflow update-managed-agent-node --format raw
```
