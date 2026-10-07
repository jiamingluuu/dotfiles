# Agent 工作流创建并上传

用于创建 Agent、查询可用节点、编辑显式本地草稿、上传为线上工作流，并通过调试验证工作流可正常运行。详细命令字段见
[Agent 基础命令](../commands/agent-basic.md)、[Agent 工作流](../commands/agent-workflow.md)
和 [Model](../commands/model.md)。

## 快速导航

- 创建并拉取草稿：`agent init`、`node list`、`agent workflow pull`。
- 普通/插件节点：`agent workflow add-node/update-node/add-edge`。
- 模型节点：`model list` + `agent workflow set-model`。
- typed 节点：`add-loop-node`、`add-text-process-node`、`add-http-node`、`add-selector-node`、`add-code-node`；`add-output-node` 是可选固定回复节点。
- loop body：`agent workflow loop add-node/add-edge/add-control/set-config`。
- 上传线上：`agent workflow validate` + `agent workflow commit`。
- 运行验证：`agent debug`；工作流编排完成后必须执行，不能只以 `commit` 成功作为完成标准。

## 核心原则

- 工作流编辑统一使用 `agent workflow` 下的显式草稿命令，不在 `agent` 顶层直接编辑节点。
- 本地草稿必须显式传 `--file <DRAFT_FILE>`；CLI 不维护隐式会话状态。
- 线上保存必须先 `validate`，再 `commit`；`commit` 默认做 stale check，线上已变化时重新 `pull`。
- `commit` 后必须用符合工作流输入约定的 JSON object 执行 `agent debug`。只有命令成功退出，且结果为 `finished=true`、`succeeded=true`、`timed_out=false`，才能确认工作流运行正常。
- 调试失败或超时时，不得宣称编排完成；根据 `nodes` 中的异常信息重新 `pull`，使用原子命令修复后再次执行 `validate -> commit -> debug`。
- `add-node` 用 `node list --agent-id` 返回的服务节点 `node_id`；模型节点选择账号时用 `model list` 返回的 `GroupList[].ModelNameList[].ModelList[].ModelId`。
- 普通插件节点也通过 `node list` 选择后使用 `add-node` 加入工作流。草稿由 CLI 管理，任何修改都走 `agent workflow` 命令；可以读取草稿查值，但不要用 `jq` 或编辑器直接修改后再提交。
- 新建或重配模型节点时，只使用统一模型节点 `117` 和 typed `set-model` 流程。
- start 节点只用于标记 DAG 入口和连接首个业务节点，本身没有业务或数据语义。不要为它配置输入输出，保留空 `InputFields` / `OutputFields`，也不要让首个业务节点引用 start 输出；工作流真实输入直接绑定到首个业务节点。
- 工作流不要求添加“指定输出”节点；有输出字段的末端/叶子节点可直接作为最终输出。不要只为结束 DAG 添加 output node。
- `add-output-node` 仅在需要固定回复、模板包装或显式输出转换时使用，并像普通业务节点一样绑定输入、连接前驱 edge。
- 每个输出字段都必须有非空 alias；alias 可以与字段 key 同名，普通产出节点之间的 alias 必须全工作流唯一。`ModelId=57` 结束节点的输出是 final-field 投影，可以复用上游 alias。添加、同步或替换普通节点后，应检查该节点 `OutputFields`；若 alias 为空或与其他普通节点重复，先读取现有 `OutputFields`，再用多个 `--output` 重新声明该节点完整输出字段列表。`--output` 会替换整个输出列表，不是局部 patch；不要只传要修复的单个字段，否则会删除该节点其它输出。若普通产出 alias 改名，还要同步更新下游 `source=reference` 输入和结束节点投影；alias 或引用未修复时，`validate` / `commit` 会直接失败。

## 创建 Agent 并拉取草稿

```bash
bytedcli labelgpt agent init --name <AGENT_NAME> --space-id <SPACE_ID> --format raw
bytedcli labelgpt node list --agent-id <AGENT_ID> --space-id <SPACE_ID> --format raw
bytedcli labelgpt agent workflow pull --id <AGENT_ID> --space-id <SPACE_ID> --file <DRAFT_FILE> --format raw
```

`node list` 可用分类过滤：

```bash
bytedcli labelgpt node list --agent-id <AGENT_ID> --category <CATEGORY> --format raw
bytedcli labelgpt node list --agent-id <AGENT_ID> --deprecated --format raw
```

## 添加普通服务节点和插件节点

普通服务节点和插件节点都用 `add-node`。如后续要连边，显式指定稳定 `--node-key`。

```bash
bytedcli labelgpt agent workflow add-node \
  --file <DRAFT_FILE> \
  --node-id <NODE_ID> \
  --node-key classify \
  --name classify \
  --format raw

bytedcli labelgpt agent workflow add-edge \
  --file <DRAFT_FILE> \
  --from <START_NODE_KEY> \
  --to classify \
  --format raw
```

配置输入绑定：

```bash
# 数据集列名
bytedcli labelgpt agent workflow update-node \
  --file <DRAFT_FILE> \
  --node-key classify \
  --input '{"field":"text","source":"dataset","value":"prompt"}' \
  --format raw

# 前驱节点输出引用；result 会规范为 $.result
bytedcli labelgpt agent workflow update-node \
  --file <DRAFT_FILE> \
  --node-key classify \
  --input '{"field":"context","source":"reference","value":"result"}' \
  --format raw

# 固定值
bytedcli labelgpt agent workflow update-node \
  --file <DRAFT_FILE> \
  --node-key classify \
  --input '{"field":"temperature","source":"custom","value":"0.1"}' \
  --format raw
```

替换服务节点类型或改展示名：

```bash
bytedcli labelgpt agent workflow update-node \
  --file <DRAFT_FILE> \
  --node-key classify \
  --node-id <NEW_NODE_ID> \
  --name <DISPLAY_NAME> \
  --format raw
```

## 配置模型节点

先查询节点可选模型（`model list --model-type` 只用于查看候选账号，能力/类型判定以 `set-model` 为准）：

```bash
bytedcli labelgpt model list --model-type llm --format raw
```

把 `GroupList[].ModelNameList[].ModelList[].ModelId` 写入草稿：

```bash
bytedcli labelgpt agent workflow set-model llm \
  --file <DRAFT_FILE> \
  --node-key <MODEL_NODE_KEY> \
  --model-id <MODEL_ID> \
  --model-config-file model-config.json \
  --format raw
```

typed `set-model` 会通过 `UnifiedModelList` 校验模型账号，并把可选 JSON 作为局部
`ModelParamConfig` 覆盖。CLI 会按模型类型和能力同步 runtime 与 I/O，失败时草稿不变。

## 添加 typed 节点

typed 节点命令只修改本地草稿，不执行脚本、HTTP 请求或线上保存。

### Loop

```bash
# array 模式：必须恰好一个 type=array 的 input
bytedcli labelgpt agent workflow add-loop-node \
  --file <DRAFT_FILE> \
  --node-key loop_items \
  --mode array \
  --input '{"field":"items","source":"reference","value":"result","type":"array"}' \
  --format raw

# count 模式：count-source 和 count-value 必须同时提供，count-value 范围 1..100
bytedcli labelgpt agent workflow update-loop-node \
  --file <DRAFT_FILE> \
  --node-key loop_items \
  --mode count \
  --count-source custom \
  --count-value 3 \
  --format raw
```

### Text Process

```bash
bytedcli labelgpt agent workflow add-text-process-node \
  --file <DRAFT_FILE> \
  --node-key join_text \
  --mode join \
  --symbol "|" \
  --input '{"field":"left","source":"reference","value":"first"}' \
  --input '{"field":"right","source":"reference","value":"second"}' \
  --format raw
```

`join` 至少一个输入；`split` 恰好一个 `type=string` 的输入；两种模式都必须传 `--symbol`。

### HTTP

```bash
bytedcli labelgpt agent workflow add-http-node \
  --file <DRAFT_FILE> \
  --node-key call_api \
  --url https://example.com/api \
  --method POST \
  --header '{"header":"Content-Type","value":"application/json"}' \
  --input '{"field":"body","source":"reference","value":"result"}' \
  --format raw
```

`--url` 必须是 `http://` 或 `https://`；`--method` 只能是 `GET` 或 `POST`。

### Selector

```bash
bytedcli labelgpt agent workflow add-selector-node \
  --file <DRAFT_FILE> \
  --node-key route \
  --branch '{"id":"if_main","type":"if","logical":"and","conditions":[]}' \
  --format raw

bytedcli labelgpt agent workflow add-edge \
  --file <DRAFT_FILE> \
  --from route \
  --to <IF_TARGET_KEY> \
  --source-handle if_main \
  --format raw

bytedcli labelgpt agent workflow add-edge \
  --file <DRAFT_FILE> \
  --from route \
  --to <ELSE_TARGET_KEY> \
  --source-handle else \
  --format raw
```

`--branch` 可重复传入；缺少 `else` 时 CLI 自动补齐。

### Code

```bash
bytedcli labelgpt agent workflow add-code-node \
  --file <DRAFT_FILE> \
  --node-key transform \
  --language python \
  --code $'def main(data_item):\n    return {\"a\": data_item, \"b\": data_item}\n' \
  --output '{"key":"a","alias":"a","type":"String"}' \
  --output '{"key":"b","alias":"b","type":"String"}' \
  --format raw

bytedcli labelgpt agent workflow update-code-node \
  --file <DRAFT_FILE> \
  --node-key transform \
  --language javascript \
  --code-file ./transform.js \
  --format raw
```

Python 必须定义 `def main(data_item): ... return dict`；JavaScript 必须定义 `main(data)` 并返回 object。不要生成顶层 `return ...`。`--output` 可重复传入并完整声明代码节点的输出字段；未传时默认声明 `result`。

代码节点声明的输出字段可直接作为下游引用；当 `transform` 是末端节点时，声明的字段可直接返回。例如补一条 `开始 -> transform` 的边后即可 `validate`、`commit`，无需再添加 output node：

```bash
bytedcli labelgpt agent workflow add-edge \
  --file <DRAFT_FILE> \
  --from <START_NODE_KEY> \
  --to transform \
  --format raw
bytedcli labelgpt agent workflow validate --file <DRAFT_FILE> --format raw
bytedcli labelgpt agent workflow commit --file <DRAFT_FILE> --space-id <SPACE_ID> --format raw
```

### 指定输出（可选）

仅在需要固定回复、模板包装或显式输出转换时使用；不要把它当成通用 DAG 终结符。节点应绑定前驱结果，并通过普通 edge 连入工作流：

```bash
bytedcli labelgpt agent workflow add-output-node \
  --file <DRAFT_FILE> \
  --node-key final_reply \
  --fixed-reply '处理完成：{{result}}' \
  --input '{"field":"result","source":"reference","value":"result"}' \
  --format raw

bytedcli labelgpt agent workflow add-edge \
  --file <DRAFT_FILE> \
  --from transform \
  --to final_reply \
  --format raw

bytedcli labelgpt agent workflow update-output-node \
  --file <DRAFT_FILE> \
  --node-key final_reply \
  --fixed-reply-file ./reply.txt \
  --format raw
```

`--fixed-reply` 与 `--fixed-reply-file` 互斥，内容最多 100000 个 Unicode 字符。

## 编辑 loop body

loop body 只能通过 `agent workflow loop ...` 编辑：

```bash
bytedcli labelgpt agent workflow loop add-node \
  --file <DRAFT_FILE> \
  --loop-key loop_items \
  --node-id <NODE_ID> \
  --node-key loop_worker \
  --entry \
  --format raw

bytedcli labelgpt agent workflow loop add-edge \
  --file <DRAFT_FILE> \
  --loop-key loop_items \
  --from loop_worker \
  --to <NEXT_CHILD_KEY> \
  --format raw

bytedcli labelgpt agent workflow loop add-control \
  --file <DRAFT_FILE> \
  --loop-key loop_items \
  --control continue \
  --node-key continue_loop \
  --format raw

bytedcli labelgpt agent workflow loop set-config \
  --file <DRAFT_FILE> \
  --loop-key loop_items \
  --config '{"maxIterations":10}' \
  --format raw
```

`loop add-control` 的 `--control` 只能是 `continue` 或 `break`。`loop set-config` 要求 `--config` 是 JSON object，并与当前配置浅层合并。

## 删除节点或边

```bash
bytedcli labelgpt agent workflow remove-edge \
  --file <DRAFT_FILE> \
  --from <SOURCE_KEY> \
  --to <TARGET_KEY> \
  --format raw

bytedcli labelgpt agent workflow remove-node \
  --file <DRAFT_FILE> \
  --node-key <NODE_KEY> \
  --format raw
```

`remove-node` 拒绝删除 start node；删除普通节点时删除相关边，不自动重连。

## 校验、上传并调试

```bash
bytedcli labelgpt agent workflow validate --file <DRAFT_FILE> --format raw
bytedcli labelgpt agent workflow commit --file <DRAFT_FILE> --space-id <SPACE_ID> --format raw
bytedcli labelgpt agent debug --id <AGENT_ID> --space-id <SPACE_ID> --input '<DEBUG_INPUT_JSON>' --format raw
bytedcli labelgpt agent view --id <AGENT_ID> --space-id <SPACE_ID> --format raw
```

如果 `commit` 提示线上已变化，重新执行 `pull` 生成新草稿，再重做本地编辑。只有明确要覆盖线上版本时才使用 `--force-save`。

`agent debug` 调试的是已 `commit` 的在线工作流，并自动轮询到完成或达到 `--wait-timeout`。调试输入必须是符合工作流入口约定的 JSON object；无业务输入时可使用 `{}`。输入较长时改用 `--input-file <PATH>`。

检查调试结果时必须同时满足：

- 命令退出码为 0。
- `finished=true`。
- `succeeded=true`。
- `timed_out=false`。
- `nodes` 中没有 `status_text=exception` 的节点。

任一条件不满足都表示工作流尚未通过运行验证。根据 `nodes[].exception_desc`、`nodes[].warning` 和节点结果定位问题，然后重新执行 `pull -> 原子命令修复 -> validate -> commit -> debug`，直到调试成功。

## 最小端到端模板

```bash
bytedcli labelgpt agent init --name <AGENT_NAME> --space-id <SPACE_ID> --format raw
bytedcli labelgpt node list --agent-id <AGENT_ID> --space-id <SPACE_ID> --format raw
bytedcli labelgpt agent workflow pull --id <AGENT_ID> --space-id <SPACE_ID> --file <DRAFT_FILE> --format raw
bytedcli labelgpt agent workflow add-node --file <DRAFT_FILE> --node-id <NODE_ID> --node-key classify --format raw
bytedcli labelgpt agent workflow update-node --file <DRAFT_FILE> --node-key classify --input '{"field":"<NODE_INPUT_FIELD>","source":"dataset","value":"<DATASET_COLUMN>"}' --format raw
bytedcli labelgpt agent workflow add-edge --file <DRAFT_FILE> --from <START_NODE_KEY> --to classify --format raw
bytedcli labelgpt agent workflow validate --file <DRAFT_FILE> --format raw
bytedcli labelgpt agent workflow commit --file <DRAFT_FILE> --space-id <SPACE_ID> --format raw
bytedcli labelgpt agent debug --id <AGENT_ID> --space-id <SPACE_ID> --input '{"<DATASET_COLUMN>":"<DEBUG_VALUE>"}' --format raw
```

## 常见错误

- 缺少节点 ID：先用 `node list --agent-id <AGENT_ID> --format raw` 查询。
- 缺少模型 ID：先用 `model list --model-type <TYPE_KEY> --format raw` 查询，并选择 `isAuthorized=true` 的账号。
- 创建或保存线上 Agent 的命令要求 `space-id`；按 ID 查询、调试、模型查询以及纯本地草稿编辑/校验不强制要求 `space-id`。
- 分支连边不生效：selector 边要把 branch id 传给 `--source-handle`。
- 调试输入无效：`--input` 或 `--input-file` 必须提供合法 JSON object，并与工作流入口字段匹配。
- start 节点残留输入输出：使用 `agent workflow update-node --file <DRAFT_FILE> --node-key <START_NODE_KEY> --clear-inputs --clear-outputs` 修复，不要删除并重建 start。
- 调试节点异常或超时：检查调试输出中的 `nodes`、`exception_desc`、`warning` 和 `timed_out`，修复并重新提交后再次执行 `agent debug`。
