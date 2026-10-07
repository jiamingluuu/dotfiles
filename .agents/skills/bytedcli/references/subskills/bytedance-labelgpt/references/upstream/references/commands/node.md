# bytedcli labelgpt node

查询 Agent 可用的 Service Node，并按 Service Node ID 同步执行已发布的业务/系统插件节点。
不要把 Agent ID、Plugin ID 或 Agent 工作流节点实例 ID/key 混用。

## node list

```bash
bytedcli labelgpt node list --agent-id <AGENT_ID> --format raw
bytedcli labelgpt node list --global --format raw
bytedcli labelgpt node list --agent-id <AGENT_ID> --category <CATEGORY> --query <TEXT> --format raw
bytedcli labelgpt node list --global --node-id 0 --node-id <NODE_ID> --plugin-id <PLUGIN_ID> --format raw
```

- `--agent-id` 与 `--global` 必须且只能选择一个。前者查询某个 Agent 可用的目录，后者查询当前用户可见的全局 Service Node 目录；本命令不接受通用 `--id`。
- `--category` 可按分类名称或 ID 过滤；`--deprecated` 包含废弃节点。
- `--query` 对节点名称和描述做大小写不敏感匹配。
- `--node-id` 可重复或使用逗号分隔，允许非负整数（内建节点可为 0）；`--plugin-id` 同样可重复或逗号分隔，但必须是正整数。
- 同类多个 ID 按 OR，不同过滤维度以及 category/deprecated 按 AND。筛选在 CLI 获取完整目录后完成。
- 按 Agent ID 查询，不强制要求 `space-id`；显式提供时仍会转发。
- `raw/json` 输出 `scope`、`agent_id`、`categories`、`nodes`、`total`、`shown`。`categories` 保留完整目录，`nodes` 是筛选后的平面结果；global 模式的 `agent_id` 为空。
- 插件节点同时含 `node_id` 和 `plugin_id`；前者用于 `node execute` 和工作流选择节点，后者是
  Plugin 资源 ID，两者不可互换。
- `-o <DIR>` 写入 `node_list_<AGENT_ID>.json`。

## node execute

```bash
bytedcli labelgpt node list --agent-id <AGENT_ID> --format raw

bytedcli labelgpt node execute --node-id <SERVICE_NODE_ID> --format raw
bytedcli labelgpt node execute --node-id <SERVICE_NODE_ID> \
  --input '{"content":"hello"}' --format raw
bytedcli labelgpt node execute --node-id <SERVICE_NODE_ID> --input ./input.json --format raw
cat input.json | bytedcli labelgpt node execute --node-id <SERVICE_NODE_ID> --input - --format raw
```

### ID 规则

- `--node-id` 必填，必须是正 int64。
- 值来自 `node list --agent-id <AGENT_ID> --format raw` 的 `nodes[].node_id`。
- 同一项的 `nodes[].plugin_id` 是 Plugin ID，不能传给 `--node-id`。
- Agent 草稿或已保存工作流中的节点实例 ID/key 也不能传给 `--node-id`。
- 命令按全局唯一 Service Node ID 定位，不强制要求 `space-id`；显式提供时仍会转发。

### 输入与执行

- `--input` 可选，省略时默认为空 JSON object `{}`。
- 输入可为内联 JSON object、JSON object 文件路径或 `-` stdin；数组、标量、`null` 和空内容
  会被拒绝。
- 命令调用 `POST /labelgpt/model/ExecuteNode`，服务端只接受已发布、未废弃的业务/系统插件
  Service Node；其他节点由服务端拒绝。
- 命令同步等待并直接返回本次执行结果。

### 输出

`raw/json` 输出一个 JSON 文档：

- `node_id`：本次请求的 Service Node ID。
- `plugin_id`：该节点关联的 Plugin ID，仅作为结果元数据。
- `execution_time_ms`：服务端执行耗时。
- `trace_id`：可选追踪 ID。
- `result`：从服务端 JSON 字符串解码后的结构化结果。

`-o <DIR>` 写入 `node_execute_<SERVICE_NODE_ID>.json`。服务端状态失败、返回 ID 不匹配、耗时
非法或 result 不是合法 JSON 时，命令返回非零。

## Schema

```bash
bytedcli labelgpt schema node execute --format raw
bytedcli labelgpt schema node list --format raw
```

`node list` 的 Schema V2 分为 `agent` 和 `global` 两个 mode。
