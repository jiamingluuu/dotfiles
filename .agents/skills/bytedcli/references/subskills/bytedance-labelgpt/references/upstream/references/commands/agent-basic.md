# bytedcli labelgpt agent 基础命令

Agent 基础命令覆盖列表、创建、复制、详情和在线调试。分页列表、创建和复制依赖 `space-id`；按 Agent ID 定位的详情和调试不强制要求 `space-id`。Service Node 查询见 [node.md](node.md)。

## 快速导航

- [agent list](#agent-list)：分页列出目标 Space 下的 Agent。
- [agent init](#agent-init)：创建带默认 start node 的 Agent。
- [agent copy](#agent-copy)：复制已有 Agent。
- [agent view](#agent-view)：查看 Agent 详情和工作流。
- [agent schema](#agent-schema)：查看 Agent 的输入和输出字段契约。
- [agent debug](#agent-debug)：调试已保存的在线工作流。
- 历史版本查询与图导出见 [agent-version.md](agent-version.md)。
- 运行监控与诊断见 [agent-monitor.md](agent-monitor.md)。
- 工作流草稿编辑见 [agent-workflow.md](agent-workflow.md)。
- 异步任务操作见 [agent-task.md](agent-task.md)。

## agent list

分页列出目标 Space 下的 Agent。

### 用法

```bash
bytedcli labelgpt agent list [选项]
```

### 示例

```bash
bytedcli labelgpt agent list --space-id <SPACE_ID>
bytedcli labelgpt agent list --space-id <SPACE_ID> --page-num 1 --page-size 30 --format raw
bytedcli labelgpt agent list --space-id <SPACE_ID> --all-pages --page-size 100 --format raw
bytedcli labelgpt agent list --space-id <SPACE_ID> --favorite-status 0 --type 0 --sort-type 1 --format raw
```

### 参数说明

- `--page-num <N>`：页码，从 1 开始，默认 1。
- `--page-size <N>`：每页数量，默认 30。
- `--all-pages`：自动读取全部分页；不能与显式 `--page-num` 同时使用。此时 `--page-size` 表示每次请求批量。
- `--favorite-status <N>`：收藏过滤，默认 0。
- `--type <N>`：Agent 类型过滤，默认 0。
- `--sort-type <N>`：排序类型，默认 1。

### 输出

`raw/json` 输出 `agents`、`total`、`page_num`、`page_size`、`all_pages`、`pages_fetched` 和 `fetched`。Agent 行包含 `id`、`name`、`description`、`create_time` 和 `modify_time`。全量模式按 Agent ID 去重并保留首次出现顺序；后续页失败时整体失败，不返回静默截断结果。

### 输出文件

- `-o <DIR>`：写入 `agent_list_<timestamp>.json`。

### 注意事项

- 必须在当前命令中显式传 `--space-id <SPACE_ID>`。

## agent init

创建一个带默认 start node 的 Agent。start 只标记 DAG 入口并连接首个业务节点，本身没有业务或数据语义；其输入输出保持为空，工作流真实输入直接绑定到首个业务节点。

### 用法

```bash
bytedcli labelgpt agent init [选项]
```

### 示例

```bash
bytedcli labelgpt agent init --space-id <SPACE_ID>
bytedcli labelgpt agent init --name demo_agent --space-id <SPACE_ID>
bytedcli labelgpt agent init --name demo_agent --space-id <SPACE_ID> --format raw
```

### 参数说明

- `--name <name>`：Agent 名称。未提供时使用 `Agent-<timestamp>`。

### 输出

`raw/json` 输出 `id`、`name` 和 `space_id`。

### 输出文件

- `-o <DIR>`：写入 `agent_<id>.json`；如果 ID 为空则使用当前时间戳兜底。

### 注意事项

- 创建前确认目标 Space，并在当前命令中显式传 `--space-id <SPACE_ID>`。
- 创建结果包含所属 Space 信息，便于确认资源归属。

## agent copy

复制已有 Agent 到目标 Space。普通复制直接走后端 `CopyAndGenerateAgentServicePlan`，不拉取或重建本地工作流草稿。

### 用法

```bash
bytedcli labelgpt agent copy --id <agent-id> [选项]
```

### 示例

```bash
bytedcli labelgpt agent copy --id <AGENT_ID> --space-id <SPACE_ID>
bytedcli labelgpt agent copy --id <AGENT_ID> --space-id <SPACE_ID> --format raw
bytedcli labelgpt agent copy --id <AGENT_ID> --type 1 --space-id <SPACE_ID> --format raw
```

### 参数说明

- `--id <AGENT_ID>`：源 Agent PlanId，必填。
- `--type <0|1>`：来源类型。默认不发送该字段；复制 Agent 广场资源时传 `1`。`0` 表示我的 Agent，`1` 表示 Agent 广场。

### 输出

`raw/json` 输出 `source_id`、`new_id`、`space_id`，以及显式传 `--type` 时的 `type`。

### 输出文件

- `-o <DIR>`：写入 `agent_copy_<new_id>.json`；如果后端未返回新 ID，则使用源 ID 兜底。

### 注意事项

- 复制前确认目标 Space，并在当前命令中显式传 `--space-id <SPACE_ID>`。
- 后端负责复制后的命名、权限、工作流节点行 ID 和版本初始化。
- 如果源 Agent 存在字段聚合异常、脏 `ParentNodeKey`、旧保存节点 ID 等存储问题，不要用普通复制修复；改走工作流重建/修复场景。

## agent view

查看 Agent 详情和工作流。

### 用法

```bash
bytedcli labelgpt agent view --id <agent-id> [选项]
```

### 示例

```bash
bytedcli labelgpt agent view --id <AGENT_ID>
bytedcli labelgpt agent view --id <AGENT_ID> --format raw
```

### 参数说明

- `--id <AGENT_ID>`：Agent ID，必填。

### 输出

`raw/json` 输出包括 `id`、当前详情返回的精确 `version_id`、版本历史中与其匹配的可读 `display_version`、`name`、`space_id`、可直接打开 Agent 编辑页的 `url`、`tags`、`description`、`public`、限流配置、运行时限、创建修改时间和包含 nodes/edges 的 `graph`。

### 输出文件

- `-o <DIR>`：写入 `agent_<id>.json`。

### 注意事项

- `agent view` 按 Agent ID 查询，不强制要求 `space-id`；若显式传入，仍作为请求头发送。
- `pretty` 输出同时展示可读的 `Version`、精确的 `Version ID` 和 Agent 编辑页 URL，并使用单行链路展示工作流，例如 `Start → NodeA → NodeB`。
- 为避免错误关联版本，详情中的 `version_id` 无法在版本历史中精确匹配时命令会失败。

## agent schema

查看 Agent 的输入和输出字段契约。适合在 `dataset run` 或 `agent debug` 之前确认 Agent 期望的输入字段（名称、类型、是否必填、取值来源）和产出的输出字段。

### 用法

```bash
bytedcli labelgpt agent schema --id <agent-id> [选项]
```

### 示例

```bash
bytedcli labelgpt agent schema --id <AGENT_ID> --format raw
bytedcli labelgpt agent schema --id <AGENT_ID> --version-id <VERSION_ID> --format raw
```

### 参数说明

- `--id <AGENT_ID>`：Agent ID，必填。
- `--version-id <VERSION_ID>`：查看指定已发布版本；省略时使用当前生效版本。

### 输出

`raw/json` 输出包含 `id`、`version`、`inputs` 和 `outputs`。`inputs[]` 每项含 `key`、`type`、`required`、`source`（取值来源，翻译为 `dataset`/`reference`/`custom`/`knowledge`/`file`）和 `description`。`outputs[]` 每项含 `key`、`alias`、`type`、`show_in_dataset`、`description`，并可嵌套 `fields`。

### 输出文件

- `-o <DIR>`：写入 `agent_schema_<id>.json`。

### 注意事项

- `agent schema` 按 Agent ID 查询，不强制要求 `space-id`；若显式传入，仍作为请求头发送。
- `source` 始终是人类可读的取值来源名称，不是数字。

## agent debug

调试已保存的在线 Agent 工作流。命令发起异步调试并自动等待结果完成。

### 用法

```bash
bytedcli labelgpt agent debug --id <agent-id> (--input <json> | --input-file <path>) [选项]
```

### 示例

```bash
bytedcli labelgpt agent debug --id <AGENT_ID> --input '{"prompt":"hello"}' --format raw
bytedcli labelgpt agent debug --id <AGENT_ID> --input-file ./input.json --poll-interval 1s --wait-timeout 10m --format json
cat input.json | bytedcli labelgpt agent debug --id <AGENT_ID> --input - --format raw
```

### 参数说明

- `--id <AGENT_ID>`：要调试的 Agent ID，必须是正 int64。
- `--input <JSON>`：直接传 JSON object；传 `-` 时从 stdin 读取。
- `--input-file <PATH>`：从文件读取 JSON object，和 `--input` 互斥。
- `--poll-interval <DURATION>`：结果轮询间隔，默认 `500ms`，最小 `100ms`。
- `--wait-timeout <DURATION>`：整个调试流程的最长等待时间，默认 `30m`。
- 全局 `--timeout` 只控制每一次 HTTP 请求，不替代 `--wait-timeout`。

### 执行与失败语义

- 用户只需提供 Agent ID 和调试输入，不需要额外提供工作流结构。
- CLI 发起调试后自动轮询，直到结果完成或达到 `--wait-timeout`。
- 本地草稿变更不会被直接调试；先执行 `agent workflow validate` 和 `agent workflow commit`。
- 完成结果中存在 `status_text=exception` 的异常节点时，CLI 先输出完整结果，再返回非零退出码。
- 等待超时时，CLI 输出最后一次结果快照，设置 `timed_out=true`，再返回非零退出码。
- `raw/json` stdout 始终只有一个最终 JSON 文档；发起成功和等待提示写 stderr。

### 输出

顶层输出 `agent_id`、`debug_id`、`finished`、`succeeded`、`timed_out`、`warnings` 和 `nodes`。`nodes[]` 包含节点/模型信息、状态、执行耗时、输入、结果、异常、token usage、warning、extra property 和 reasoning。

### 输出文件

- `-o <DIR>`：写入 `agent_debug_<debug-id>.json`。

## Schema 查询索引

```bash
bytedcli labelgpt schema agent list --format raw
bytedcli labelgpt schema agent init --format raw
bytedcli labelgpt schema agent copy --format raw
bytedcli labelgpt schema agent view --format raw
bytedcli labelgpt schema agent schema --format raw
bytedcli labelgpt schema agent debug --format raw
```
