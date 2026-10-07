# bytedcli labelgpt agent workflow

通过显式本地 JSON 草稿批量编辑已有 Agent 工作流。先 `pull` 线上方案到本地文件，再用 CLI 命令增删节点和边，`validate` 做本地校验，最后 `commit` 一次性保存线上。

## 快速导航

- [推荐流程](#推荐流程)
- [通用子命令](#通用子命令)
- [参数与草稿规则](#参数与草稿规则)
- [统一模型节点 117](#统一模型节点-117)
- [类型化节点](#类型化节点)
- [Loop Body](#loop-body)
- [输出与注意事项](#输出与注意事项)
- Agent 列表、节点查询与在线调试见 [agent-basic.md](agent-basic.md)。
- 异步任务操作见 [agent-task.md](agent-task.md)。

## 推荐流程

```bash
bytedcli labelgpt agent workflow pull --id <AGENT_ID> --space-id <SPACE_ID> --file /tmp/agent_workflow.json --format raw
bytedcli labelgpt agent workflow add-node --file /tmp/agent_workflow.json --node-id <NODE_ID> --node-key classify --name classify --format raw
bytedcli labelgpt agent workflow update-node --file /tmp/agent_workflow.json --node-key classify --input '{"field":"<NODE_INPUT_FIELD>","source":"dataset","value":"<DATASET_COLUMN>"}' --format raw
bytedcli labelgpt agent workflow add-edge --file /tmp/agent_workflow.json --from <START_NODE_KEY> --to classify --format raw
bytedcli labelgpt agent workflow validate --file /tmp/agent_workflow.json --format raw
bytedcli labelgpt agent workflow commit --file /tmp/agent_workflow.json --space-id <SPACE_ID> --format raw
bytedcli labelgpt agent workflow save --agent-id <AGENT_ID> --space-id <SPACE_ID> --graph-file /tmp/backend_workflow.json --format raw
```

## 通用子命令

```bash
bytedcli labelgpt agent workflow pull --id <AGENT_ID> --space-id <SPACE_ID> --file <draft.json>
bytedcli labelgpt agent workflow add-node --file <draft.json> --node-id <NODE_ID> [--node-key <KEY>] [--name <NAME>] [--x <N>] [--y <N>]
bytedcli labelgpt agent workflow update-node --file <draft.json> --node-key <KEY> [--node-id <NODE_ID>] [--name <NAME>] [--input <JSON>...] [--output <JSON>...] [--clear-inputs] [--clear-outputs]
bytedcli labelgpt agent workflow set-model llm --file <draft.json> --node-key <KEY> --model-id <MODEL_ID> [--model-config-json <JSON>|--model-config-file <PATH>]
bytedcli labelgpt agent workflow set-model multimodal --file <draft.json> --node-key <KEY> --model-id <MODEL_ID> [--model-config-json <JSON>|--model-config-file <PATH>]
bytedcli labelgpt agent workflow set-model image-gen --file <draft.json> --node-key <KEY> --model-id <MODEL_ID> [--model-config-json <JSON>|--model-config-file <PATH>]
bytedcli labelgpt agent workflow set-model video-gen --file <draft.json> --node-key <KEY> --model-id <MODEL_ID> [--model-config-json <JSON>|--model-config-file <PATH>]
bytedcli labelgpt agent workflow set-sub-agent --file <draft.json> --node-key <KEY> --sub-agent-id <AGENT_ID> [--version-id <VERSION_ID>] [--version-number <N>] [--no-sync-io]
bytedcli labelgpt agent workflow add-sub-agent-node --file <draft.json> --node-key <KEY> --sub-agent-id <AGENT_ID> [--version-id <VERSION_ID>] [--version-number <N>] [--no-sync-io] [--input <JSON>...] [--output <JSON>...]
bytedcli labelgpt agent workflow update-sub-agent-node --file <draft.json> --node-key <KEY> --sub-agent-id <AGENT_ID> [--version-id <VERSION_ID>] [--version-number <N>] [--no-sync-io] [--input <JSON>...] [--output <JSON>...]
bytedcli labelgpt agent workflow add-managed-agent-node --file <draft.json> --node-key <KEY> --managed-agent-id <MANAGED_AGENT_ID> [--version-id <VERSION_ID>] [--version-number <N>] [--no-sync-io] [--input <JSON>...] [--output <JSON>...]
bytedcli labelgpt agent workflow update-managed-agent-node --file <draft.json> --node-key <KEY> --managed-agent-id <MANAGED_AGENT_ID> [--version-id <VERSION_ID>] [--version-number <N>] [--no-sync-io] [--input <JSON>...] [--output <JSON>...]
bytedcli labelgpt agent workflow remove-node --file <draft.json> --node-key <KEY>
bytedcli labelgpt agent workflow add-edge --file <draft.json> --from <SOURCE_KEY> --to <TARGET_KEY> [--source-handle <HANDLE>] [--target-handle <HANDLE>]
bytedcli labelgpt agent workflow remove-edge --file <draft.json> --from <SOURCE_KEY> --to <TARGET_KEY> [--source-handle <HANDLE>] [--target-handle <HANDLE>]
bytedcli labelgpt agent workflow validate --file <draft.json>
bytedcli labelgpt agent workflow commit --file <draft.json> --space-id <SPACE_ID> [--force-save]
bytedcli labelgpt agent workflow save --agent-id <AGENT_ID> --space-id <SPACE_ID> --graph-file <workflow.json>
```

`save` 与 `commit` 是两条互斥的保存路径：

- CLI 搭建工作流：`pull` → 原子编辑命令 → `validate` → `commit`。完成后不要再执行 `save`。`commit` 只接受 CLI 管理的 draft。
- 外部工作流 JSON：直接执行 `save`。不要把外部后端 JSON 交给 `commit`，也不需要经过 `pull`、原子编辑或 `validate`。

`commit` 执行本地工作流校验和线上版本指纹检查，并保存完整 Agent 更新请求；`save` 先确认 `--agent-id` 对应的 Agent 存在，再只改动 `Nodes` 和 `NodeGraph`，并原样保留该 Agent 现有的其它元数据（名称、描述、Owner、公开状态、限流、可见/可调用用户、Tag 等）。

`save --graph-file` 只接受顶层直接包含 `nodes` 和 `edges` 数组的图对象，不接受 `NodeGraph` 包装格式。`Nodes` 由 CLI 依据图计算（与前端一致：剥离迭代开始节点 `86001`、清理端点缺失的悬空边）。文件不能携带 `Nodes`、`PlanId`、`PlanName`、Owner、权限、公开状态或限流字段；Agent ID 始终由 `--agent-id` 提供。成功后的 `raw/json` 输出包含 `agent_id`、`version_id`、`saved`、`nodes_count` 和 `edges_count`。

## 参数与草稿规则

- `pull --id <AGENT_ID>` 和 `pull --file <draft.json>`：要拉取的 Agent 与目标草稿文件，必填。
- `add-node --node-id <NODE_ID>`：要加入工作流的服务节点 NodeId，必填；`--node-key` 不传时自动生成 8 位 key。
- `update-node --node-key <KEY>`：要更新的工作流节点实例 key，必填。
- `update-node --clear-inputs/--clear-outputs`：显式清空节点的全部输入/输出。已有草稿若 start 节点携带非法 I/O，使用这两个参数修复；不要通过删除并重建 start 处理。
- `set-model` 是命令组，不能直接执行；只支持 `llm|multimodal|image-gen|video-gen` 四个 typed 叶子，且只配置统一模型节点 `117`。
- 每个叶子固定顶层 `TypeKey`，要求 `--file --node-key --model-id`；可选 `--model-config-json` 或 `--model-config-file`，二者互斥。
- 配置 JSON 根对象直接表示前端 `ModelParamConfig` 的局部覆盖。`--model-id` 是主模型唯一 ID；`modelConfigs[0].modelIdV2` 可省略，提供时必须一致。
- 未提供 `modelConfigs` 时保留当前备用链；显式提供时替换完整主备链；空数组清空备用。最多三个备用，所有账号必须授权、去重、同类型，备用能力与模态必须覆盖主模型。
- 类型与能力判定以节点 `117` 四类合并 catalog（`ModelTypes=[llm,multimodal,video_gen,image_gen]`）为准，与前端一致；不要用 `model list --model-type <单类型>` 的字段判断备用兼容性。完整规则见 [model.md](model.md) 与 [统一模型节点](../domain/unified-model-node.md)。
- 精确账号按 `modelIdV2` 保参，主备重排不丢参数；同一模型 name-group 换账号保参，跨模型名重置候选参数。API 身份字段始终覆盖调用方同名字段。
- 只对主模型调用 `/labelgpt/medivh/GetModelConfigInfo`（`SceneKey=agent`），应用默认值、options、validator、rules 与模板表达式。任何远端查询、解析或校验失败都不会写草稿。
- 新节点、I/O 为空或 `TypeKey` 变化时按 `59/53/116/115` 模板合并绑定；同类型换账号保留自定义 I/O。推理、联网与 MCP 能力会同步顶层 runtime 和输出字段。
- MCP 使用前端字段 `ApiId/apikeyOfApihubForAgent/mcp/apihub_tools/...`；API key 只进入草稿，不进入结果或诊断。
- `set-sub-agent`：配置服务节点 `10349`。默认选择线上/Used 版本并同步版本 I/O；显式传 `--version-id` 可固定版本，只改配置不覆盖 I/O 时加 `--no-sync-io`。
- `add-sub-agent-node` / `update-sub-agent-node`：封装 Agent 调用节点，随后使用与 `set-sub-agent` 相同的配置逻辑。
- `add-managed-agent-node` / `update-managed-agent-node`：先验证目标是 Managed Agent，再复用服务节点 `10349` 和已发布版本 I/O。不要把 Managed Agent 自身方案中的内部节点 `1013` 手工加入普通工作流。
- `add-node/update-node --input <JSON>`：可重复传。命令中推荐使用字符串 source，也接受草稿中的对应数字枚举；核心对应关系是 `Source=1 -> dataset`、`Source=2 -> reference`、`Source=3 -> custom`：

  | 草稿 `Source` | `--input source` | 含义 | 值的形态 |
  | ---: | --- | --- | --- |
  | `1` | `dataset` | 数据集列或工作流入口字段 | 裸列名，如 `response` |
  | `2` | `reference` | 上游节点输出 | alias 或 JSONPath；写回时规范为 `$.alias` |
  | `3` | `custom` | 固定字面量 | 直接文本，同时写入 `ValueKey` / `ActualValue` |
  | `4` | `knowledge` | 知识库输入 | 按节点契约提供知识库值 |
  | `5` | `file` | 文件输入 | 按节点契约提供文件值 |

  迁移或重建节点时必须以原始 `InputFields[].Source` 为准，不要靠 `ValueKey` 的形态猜 source。特别是 `Source=1, ValueKey="response"` 表示数据集列 `response`，不是“按 alias 引用上游输出”；只有 `Source=2` 才是节点间引用。裸列名即使恰好与某个上游 alias 同名，也仍应保留为 `dataset`。
- `add-node/update-node --output <JSON>`：可重复传并替换该节点全部输出。JSON 支持 `key`、`alias`/`key_alias`、`type`、`key_desc`、`show_in_dataset`。每个输出 alias 必须非空；普通产出节点之间必须全工作流唯一。`ModelId=57` 结束节点用于把上游 alias 暴露为 final field，可以复用上游 alias，不算冲突。普通节点 alias 为空或重复，或切换节点类型后引用失配时，`validate` / `commit` 会返回 alias 或引用相关校验失败。
- loop 节点聚合输出的 key 按 `<loop子节点key>_<子节点输出alias>_array` 命名，例如 `loopllm_result_array`；下游引用 `$.loopllm_result_array`。参与聚合的 loop 子节点 key 不要包含 `_`。
- `add-edge/remove-edge` 的 `--from` 和 `--to` 必填；分支或多端口节点可补 `--source-handle`、`--target-handle`。
- `commit --force-save` 显式覆盖线上版本，默认不覆盖，使用前需用户确认。

草稿由 CLI 管理：

- 所有修改都使用 `agent workflow` 命令；可以读取草稿查找 ID、key 和 alias，但不要手工改写后提交。
- 所有草稿命令都必须显式传 `--file`，CLI 不维护隐式会话状态。
- start 节点只用于标记 DAG 入口和连接首个业务节点，本身没有业务或数据语义。保留其空 `InputFields` / `OutputFields`，不要为它配置、复制或推导输入输出，也不要让业务节点引用 start 输出；节点编辑命令会拒绝为 start 写入输入输出，`validate` 和 `commit` 也会拒绝已有草稿中的非法 start I/O。工作流真实输入直接绑定到首个业务节点。
- 如果旧草稿的 start 已带 I/O，执行 `update-node --node-key <START_NODE_KEY> --clear-inputs --clear-outputs` 后重新 `validate`。清空操作是纯本地原子修改，会保留原 start 的 key、位置和连边，也不需要认证。不要尝试删除旧 start 再新增：`remove-node` 会保护 start，草稿也只允许一个顶层 start；重新解析节点元数据还会额外依赖认证和服务端查询。
- 普通节点连接使用 `add-edge/remove-edge`；loop 子流程使用 `agent workflow loop ...`。
- 修改后先 `validate`，通过后再 `commit`。
- 如果 `commit` 提示线上 Agent 已变化，重新 `pull` 后再执行修改。
- `remove-node` 拒绝删除 start node；删除普通节点时删除相关边，不自动重连。

## 统一模型节点 117

`agent workflow set-model <type>` 只适用于统一模型节点 `117`。JSON 是直接的局部 `ModelParamConfig`：

```json
{
  "prompt": "You are helpful.",
  "thinking": 1,
  "modelConfigs": [
    {},
    {"modelIdV2": "backup-model", "aiConfig": {"temperature": 0.2}}
  ]
}
```

```bash
bytedcli labelgpt agent workflow set-model llm \
  --file /tmp/agent_workflow.json \
  --node-key llm \
  --model-id primary-model \
  --model-config-file ./model.json \
  --format raw
```

`--model-id` 是主模型唯一 ID。CLI 注入账号元数据与 typed `TypeKey`，保留顶层 prompt、MCP、异常策略等配置，并按前端规则同步主备、动态参数、runtime 和 I/O。类型与能力判定以节点 `117` 四类合并 catalog 为准，与前端一致（见 [model.md](model.md)）。

### 多模态 Prompt 输入

多模态输入必须先绑定最终字段和 type，并在 Prompt 中显式引用；输入字段不会因为绑定或声明 type 就自动进入模型消息。下面先用 `update-node` 配置 `userPrompt="请描述图片：{{imageUrl}}"` 和图片字段，再运行 `set-model multimodal` 重建最终输入映射：

```bash
bytedcli labelgpt agent workflow update-node \
  --file /tmp/agent_workflow.json --node-key model \
  --input '{"field":"userPrompt","source":"custom","value":"请描述图片：{{imageUrl}}","type":"1"}' \
  --input '{"field":"imageUrl","source":"dataset","value":"image_url","type":"2"}' \
  --format raw

bytedcli labelgpt agent workflow set-model multimodal \
  --file /tmp/agent_workflow.json --node-key model --model-id <MODEL_ID> --format raw
```

图片来自上游节点时可改用 `"source":"reference"`，并将 `value` 设为输出 alias 或 JSONPath。文本、图片、视频、音频的完整类型矩阵、模板语义、生成类参考图区别和后续 `validate/commit/debug` 顺序见 [Model 的 Prompt 模板与输入字段](model.md#prompt-模板与输入字段)。

## 类型化节点

类型化命令只修改显式草稿，不会在编辑时执行脚本、发起 HTTP 请求或保存线上 Agent。完成后继续执行 `validate` 和 `commit`。

完整子命令形态：

```bash
bytedcli labelgpt agent workflow add-loop-node --file <draft.json> --node-key <KEY> --mode array|count [--count-source <SOURCE>] [--count-value <VALUE>] [--input <JSON>...]
bytedcli labelgpt agent workflow update-loop-node --file <draft.json> --node-key <KEY> --mode array|count [--count-source <SOURCE>] [--count-value <VALUE>] [--input <JSON>...]
bytedcli labelgpt agent workflow add-text-process-node --file <draft.json> --node-key <KEY> --mode join|split --symbol <SYMBOL> [--input <JSON>...]
bytedcli labelgpt agent workflow update-text-process-node --file <draft.json> --node-key <KEY> --mode join|split --symbol <SYMBOL> [--input <JSON>...]
bytedcli labelgpt agent workflow add-http-node --file <draft.json> --node-key <KEY> --url <URL> --method GET|POST [--header <JSON>...] [--input <JSON>...]
bytedcli labelgpt agent workflow update-http-node --file <draft.json> --node-key <KEY> --url <URL> --method GET|POST [--header <JSON>...] [--input <JSON>...]
bytedcli labelgpt agent workflow add-selector-node --file <draft.json> --node-key <KEY> --branch <JSON>...
bytedcli labelgpt agent workflow update-selector-node --file <draft.json> --node-key <KEY> --branch <JSON>...
bytedcli labelgpt agent workflow add-code-node --file <draft.json> --node-key <KEY> --language python|javascript (--code <SCRIPT>|--code-file <PATH>) [--input <JSON>...] [--output <JSON>...]
bytedcli labelgpt agent workflow update-code-node --file <draft.json> --node-key <KEY> --language python|javascript (--code <SCRIPT>|--code-file <PATH>) [--input <JSON>...] [--output <JSON>...]
bytedcli labelgpt agent workflow add-output-node --file <draft.json> --node-key <KEY> (--fixed-reply <TEXT>|--fixed-reply-file <PATH>) [--input <JSON>...]
bytedcli labelgpt agent workflow update-output-node --file <draft.json> --node-key <KEY> (--fixed-reply <TEXT>|--fixed-reply-file <PATH>) [--input <JSON>...]
```

### Loop

```bash
bytedcli labelgpt agent workflow add-loop-node \
  --file <DRAFT_FILE> --node-key <LOOP_KEY> --mode array \
  --input '{"field":"items","source":"reference","value":"result","type":"array"}' \
  --format raw

bytedcli labelgpt agent workflow update-loop-node \
  --file <DRAFT_FILE> --node-key <LOOP_KEY> --mode count \
  --count-source custom --count-value 3 --format raw
```

- `--mode` 只能是 `array` 或 `count`。
- `array` 必须恰好一个 `type=array` 的 `--input`。
- `count` 必须同时传 `--count-source dataset|reference|custom` 和 `--count-value`，计数范围为 1 到 100。

### Text Process

```bash
bytedcli labelgpt agent workflow add-text-process-node \
  --file <DRAFT_FILE> --node-key <TEXT_KEY> --mode join --symbol "|" \
  --input '{"field":"left","source":"reference","value":"first"}' \
  --input '{"field":"right","source":"reference","value":"second"}' \
  --format raw
```

- `--mode` 只能是 `join` 或 `split`，`--symbol` 必填。
- `join` 至少一个输入；`split` 恰好一个输入且输入类型必须为 `string`。
- add/update 命令参数约束相同。

### HTTP

```bash
bytedcli labelgpt agent workflow add-http-node \
  --file <DRAFT_FILE> --node-key <HTTP_KEY> \
  --url https://example.com/api --method POST \
  --header '{"header":"Content-Type","value":"application/json"}' \
  --input '{"field":"body","source":"reference","value":"result"}' \
  --format raw
```

- `--url` 必须使用 `http://` 或 `https://`，`--method` 只能是 `GET` 或 `POST`。
- `--header` 可重复，单个 JSON 必须包含 `header`；`--input` 也可重复。
- add/update 命令参数约束相同。

### Selector

```bash
bytedcli labelgpt agent workflow add-selector-node \
  --file <DRAFT_FILE> --node-key <SELECTOR_KEY> \
  --branch '{"id":"if_main","type":"if","logical":"and","conditions":[]}' \
  --format raw
```

- 至少一个 `--branch`；每个 branch 的 `id` 唯一且非空。
- branch JSON 支持 `type=if|else_if|else`、`logical=and|or` 和 `conditions`。
- 缺少 else 时 CLI 自动补 `branchId=else`；连边时将 branch ID 作为 `--source-handle`。

### Code

```bash
bytedcli labelgpt agent workflow add-code-node \
  --file <DRAFT_FILE> --node-key <CODE_KEY> \
  --language python --code $'def main(data_item):\n    return {"a": 1, "b": 2}\n' \
  --output '{"key":"a","alias":"a","type":"String"}' \
  --output '{"key":"b","alias":"b","type":"String"}' \
  --format raw

bytedcli labelgpt agent workflow update-code-node \
  --file <DRAFT_FILE> --node-key <CODE_KEY> \
  --language javascript --code-file ./transform.js \
  --format raw
```

- `--language` 只能是 `python` 或 `javascript`。
- `--code` 与 `--code-file` 互斥且必须提供一个；`--input` 可重复。
- `--output` 可重复；传入后会完整替换代码节点输出字段列表，每项至少包含 `key`，可用 `alias`/`type` 声明下游引用名和字段类型；未传时默认输出 `result`。
- Python 必须定义 `main(data_item)` 并返回 dict；JavaScript 必须定义或导出 `main(data)` 并返回 object。
- 命令只把脚本写入草稿配置，不在本地执行。

### 指定输出

指定输出是可选固定回复节点，不是通用 DAG 终结符。任何有输出字段的末端节点都可直接返回；仅在需要固定回复、模板包装或显式输出转换时使用。
`bytedcli labelgpt agent workflow update-output-node` 与 add 变体使用相同的固定回复、输入和互斥约束。

```bash
bytedcli labelgpt agent workflow add-output-node \
  --file <DRAFT_FILE> --node-key <OUTPUT_KEY> \
  --fixed-reply '处理完成：{{result}}' \
  --input '{"field":"result","source":"reference","value":"result"}' \
  --format raw
```

- `--fixed-reply` 与 `--fixed-reply-file` 互斥且必须提供一个，内容最多 100000 个 Unicode 字符。
- 按普通业务节点配置输入并连接前驱，避免孤立节点。

## Loop Body

完整子命令形态：

```bash
bytedcli labelgpt agent workflow loop add-node --file <draft.json> --loop-key <LOOP_KEY> --node-id <NODE_ID> --node-key <CHILD_KEY> [--entry]
bytedcli labelgpt agent workflow loop remove-node --file <draft.json> --loop-key <LOOP_KEY> --node-key <CHILD_KEY>
bytedcli labelgpt agent workflow loop add-edge --file <draft.json> --loop-key <LOOP_KEY> --from <SOURCE_KEY> --to <TARGET_KEY> [--source-handle <HANDLE>] [--target-handle <HANDLE>]
bytedcli labelgpt agent workflow loop remove-edge --file <draft.json> --loop-key <LOOP_KEY> --from <SOURCE_KEY> --to <TARGET_KEY> [--source-handle <HANDLE>] [--target-handle <HANDLE>]
bytedcli labelgpt agent workflow loop add-control --file <draft.json> --loop-key <LOOP_KEY> --control continue|break --node-key <KEY>
bytedcli labelgpt agent workflow loop set-config --file <draft.json> --loop-key <LOOP_KEY> --config '<JSON>'
```

```bash
bytedcli labelgpt agent workflow loop add-node \
  --file <DRAFT_FILE> --loop-key <LOOP_KEY> \
  --node-id <NODE_ID> --node-key <CHILD_KEY> --entry --format raw
bytedcli labelgpt agent workflow loop add-edge \
  --file <DRAFT_FILE> --loop-key <LOOP_KEY> \
  --from <CHILD_A> --to <CHILD_B> --format raw
bytedcli labelgpt agent workflow loop add-control \
  --file <DRAFT_FILE> --loop-key <LOOP_KEY> \
  --control continue --node-key <CONTROL_KEY> --format raw
bytedcli labelgpt agent workflow loop set-config \
  --file <DRAFT_FILE> --loop-key <LOOP_KEY> \
  --config '{"maxIterations":10}' --format raw
```

- `loop add-node` 必须有 `--node-id` 和 `--node-key`；`--entry` 创建 `<LOOP_KEY>start` 入口并连接子节点。
- `loop remove-node` 只删除该 loop 的子节点和相关边，不自动重连。
- loop edge 端点必须属于该 loop；可选 `--source-handle` 和 `--target-handle`。
- `loop add-control --control` 只能是 `continue` 或 `break`。
- `loop set-config --config` 必须是 JSON object，并与当前配置浅层合并。

## 输出与注意事项

所有命令的 `raw/json` 输出包含 `file`、`plan_id`、`changed`、`nodes_count`、`edges_count`。节点命令额外输出 `node_key`、`node_id`、`node_name`、`plugin_id`；边命令输出 `from`、`to`；`validate` 输出 `valid`、`errors`、`warnings`；`commit` 输出 `new_plan_id` 和 `committed`。

传 `-o <DIR>` 时按动作生成 JSON 文件；文件已存在时追加时间戳避免覆盖。

## Schema 查询索引

```bash
bytedcli labelgpt schema agent workflow pull --format raw
bytedcli labelgpt schema agent workflow add-node --format raw
bytedcli labelgpt schema agent workflow update-node --format raw
bytedcli labelgpt schema agent workflow remove-node --format raw
bytedcli labelgpt schema agent workflow add-edge --format raw
bytedcli labelgpt schema agent workflow remove-edge --format raw
bytedcli labelgpt schema agent workflow set-model llm --format raw
bytedcli labelgpt schema agent workflow set-model multimodal --format raw
bytedcli labelgpt schema agent workflow set-model image-gen --format raw
bytedcli labelgpt schema agent workflow set-model video-gen --format raw
bytedcli labelgpt schema agent workflow set-sub-agent --format raw
bytedcli labelgpt schema agent workflow add-managed-agent-node --format raw
bytedcli labelgpt schema agent workflow update-managed-agent-node --format raw
bytedcli labelgpt schema agent workflow validate --format raw
bytedcli labelgpt schema agent workflow commit --format raw
bytedcli labelgpt schema agent workflow save --format raw
```
