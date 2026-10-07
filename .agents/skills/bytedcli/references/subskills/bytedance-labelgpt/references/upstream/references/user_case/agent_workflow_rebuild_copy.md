# Agent 工作流重建与修复

用于重建或修复已有 Agent 工作流。典型场景包括：

- 用户明确要求 clean rebuild / 重建一个 Agent，而不是普通复制。
- 已有 Agent 的 `GetNodeOutPutFieldsByPlanId` 返回 `fields=[]`，但详情接口或 `agent workflow pull` 能看到 `Nodes[].OutputFields`。
- 旧工作流携带错误的 `ParentNodeKey`、旧 `NodeKey` 或旧保存节点 `NodeId`，导致字段聚合、调试或任务执行异常。

## 快速导航

- [硬性规则](#硬性规则)
- [任务类型与默认策略](#任务类型与默认策略)
- [命令面与无损重建预检](#先确认命令面)
- [拉取 Source 并创建 Target](#拉取-source-并创建-target)
- [字段聚合修复诊断](#诊断是否属于字段聚合修复)
- [用 CLI 原子命令重建](#用-cli-原子命令重建)
- [Loop 特殊处理](#loop-特殊处理)
- [Validate、Commit、Debug](#validatecommitdebug)
- [结束节点 final 字段](#结束节点-final-字段)

普通复制已有 Agent 不进入本场景，直接使用：

```bash
bytedcli labelgpt agent copy --id <SOURCE_PLAN_ID> --space-id <SPACE_ID> --format raw
```

复制 Agent 广场资源时加：

```bash
bytedcli labelgpt agent copy --id <SOURCE_PLAN_ID> --type 1 --space-id <SPACE_ID> --format raw
```

本场景的核心原则是：**重建/修复必须通过 `bytedcli labelgpt agent workflow` 原子命令构造目标工作流，不直接复制草稿 JSON**。

## 硬性规则

- 认证与 Space 启动前自检由主 `SKILL.md` 统一完成；这里先用 live schema 确认命令面。
- 不要直接把 source draft JSON 复制成 target draft 后提交。
- 不要用 `jq`、Python 或编辑器修改将要 `commit` 的工作流草稿。
- 不要保留 source 的保存节点行 ID；在 pull 出来的草稿里通常是 `nodes[].node_id`，例如 `153xxxx`。
- 修复类重建默认生成新的 top-level `NodeKey`，不要沿用旧 key。
- target 由 `agent init` 创建的 start 节点只保留为空 I/O 的图结构占位；不要复制 source start 的输入、输出、配置或保存节点行 ID，也不要把它加入业务节点映射表。首个业务节点的真实输入直接按 source 语义重建。
- 普通线性 DAG 节点不要带 `parent_key` / `ParentNodeKey`；只有 loop body 节点应保留 loop parent / iteration 元数据。
- 多条会修改同一个 `--file` 的 `agent workflow` 命令必须串行执行，不能并发。
- 每次 `commit` 成功后，如果还要继续编辑，先重新 `pull`，再做下一批命令。
- 工作流重建完成后必须执行 `agent debug`，不能只以 `commit` 成功作为完成标准。

## 任务类型与默认策略

先确认用户目标是否真的是重建/修复；如果只是“复制一个 Agent”，回到 `agent copy`。进入本场景后，再决定命名和 key 策略：

- `rebuild`：用户要行为保持一致，但目标工作流必须清理历史存储状态。默认目标名是 `<SOURCE_NAME>-重建`。
- `repair`：用户要修复字段聚合、脏 `ParentNodeKey`、错误 `NodeKey`、旧保存节点 ID 等问题。默认目标名是 `<SOURCE_NAME>-重建`。

所有重建/修复场景都必须建立一张 `old_key -> new_key` 映射表。repair/rebuild 默认生成新的 top-level `NodeKey`；只有用户明确要求稳定 key、source 已知健康且没有存储污染证据时，才可以沿用 top-level `NodeKey`。所有场景都不能沿用 source 的保存节点行 ID。

## 先确认命令面

```bash
bytedcli labelgpt commands --format raw
bytedcli labelgpt schema agent copy --format json
bytedcli labelgpt schema agent workflow pull --format json
bytedcli labelgpt schema agent workflow add-node --format json
bytedcli labelgpt schema agent workflow update-node --format json
bytedcli labelgpt schema agent workflow add-edge --format json
bytedcli labelgpt schema agent workflow validate --format json
bytedcli labelgpt schema agent workflow commit --format json
bytedcli labelgpt schema agent debug --format json
```

如果涉及模型节点，再确认：

```bash
bytedcli labelgpt schema model list --format json
bytedcli labelgpt schema agent workflow set-model llm --format json
```

## 无损重建能力预检

创建 target 前，先从 source 草稿和 live schema 判断当前 CLI 是否能无损表达 source 的关键配置。

必须列出一张重建计划表：

```text
old_key | new_key | node_type | service_node_id | typed_command | rebuild_status | notes
```

检查项：

- 每个 source 节点能映射到 `node list --agent-id` 返回的服务节点 `node_id`，或能映射到当前 CLI 支持的 typed 命令。
- code/http/text-process/selector/output/loop 节点的配置能用对应 `add-*` / `update-*` / `loop *` 命令表达。
- 模型节点先用 `add-node --node-id 117` 创建，再用 `model list` + typed `set-model` 选择模型账号；复杂 `ModelParamConfig` 通过 `--model-config-json` 或 `--model-config-file` 作为局部覆盖表达。当前命令面不承诺旧模型节点协议迁移。
- 子 Agent 节点（`ModelId=10349`）能用 `set-sub-agent` / `add-sub-agent-node` / `update-sub-agent-node` 表达；默认同步指定版本的输入输出字段。
- 如果模型节点或子 Agent 节点还依赖当前 schema 没有 flag 的配置，先标记为 `blocked`，不要创建半成品 target。
- loop 子节点 key 改名后，loop 输出字段和下游引用是否都能同步重写。
- selector branch id 是否保留；若 branch id 也改变，所有分支边的 `--source-handle` 必须同步重写。

如果存在 `blocked` 项，先向用户报告不能通过当前原子命令 100% 重建的字段和影响面。默认不要手工改 target draft，也不要直调后端保存；只有用户明确批准一次性低层保存例外时，才进入例外流程。

## 拉取 source 并创建 target

优先使用 source Agent 的 `space_id` 作为目标 Space；除非用户明确要求复制到另一个 Space。

```bash
mkdir -p .labelgpt-cli/rebuild-<SOURCE_PLAN_ID>

bytedcli labelgpt agent view \
  --id <SOURCE_PLAN_ID> \
  --space-id <SPACE_ID> \
  --format raw

bytedcli labelgpt agent workflow pull \
  --id <SOURCE_PLAN_ID> \
  --space-id <SPACE_ID> \
  --file .labelgpt-cli/rebuild-<SOURCE_PLAN_ID>/source.json \
  --format raw

bytedcli labelgpt node list \
  --agent-id <SOURCE_PLAN_ID> \
  --space-id <SPACE_ID> \
  --format raw

bytedcli labelgpt agent init \
  --name '<TARGET_NAME>' \
  --space-id <SPACE_ID> \
  --format raw

bytedcli labelgpt agent workflow pull \
  --id <TARGET_PLAN_ID> \
  --space-id <SPACE_ID> \
  --file .labelgpt-cli/rebuild-<SOURCE_PLAN_ID>/target.json \
  --format raw
```

## 诊断是否属于字段聚合修复

当用户提到 `GetNodeOutPutFieldsByPlanId`、`fields` 为空、结束节点、`ParentNodeKey` 或“详情接口能看到输出字段”时，按下面口径检查。

症状：

- `GetAgentServicePlanDetail` / `agent workflow pull` 能看到中间节点 `OutputFields`。
- `GetNodeOutPutFieldsByPlanId` 的 `fields` 为空。
- 如果 workflow 有 `ModelId=57` 结束节点，`finalFields` / `leafNodeFields` 可能不为空。

常见原因：

- 真正有输出的中间节点存储了非空 `ParentNodeKey`。
- 字段聚合口径只读取 `parent_node_key is null` 的节点。
- 结束节点 `ModelId=57` 的字段会分流到 `finalFields`，不是普通 `fields`。

修复后目标状态：

- 普通 top-level 节点 `ParentNodeKey` 为空。
- loop body 节点保留 loop parent / iteration 元数据。
- target 节点拥有后端新生成的 `node_id`。
- target 的 `fields` 包含预期的非结束节点输出；如 source 使用结束节点，target 仍保留对应 `finalFields`。

当前 `bytedcli labelgpt` 没有一等只读命令直接输出 `GetNodeOutPutFieldsByPlanId` 的 `fields`、`finalFields`、`leafNodeFields`。修复类任务需要这组证据时，可以使用项目内已存在的只读 helper 或临时只读 API wrapper 查询该接口，但不能用会提交任务的 `dataset run` 代替字段查询。若 helper 复用当前 repo 里的 `GetNodeOutPutFieldsByPlanIdData` 类型，只会保留 `fields` 和 `leafNodeFields`；要验证 `finalFields` 时必须保留原始响应或补只读解析。若没有可用只读入口，应在结果里明确报告这个验收缺口。

## 用 CLI 原子命令重建

根据 source 草稿整理节点拓扑，但实际写 target 时只使用 `bytedcli labelgpt agent workflow` 命令。

### 普通服务节点 / 插件节点

`--node-id` 使用服务节点 ID，不使用 source 保存节点 `node_id`。服务节点 ID 以 `node list --agent-id <SOURCE_PLAN_ID>` 的返回为准；source 草稿里的 `model_id` 只能作为匹配线索，不能把历史示例 ID 当成默认值。

```bash
bytedcli labelgpt agent workflow add-node \
  --file <target.json> \
  --node-id <SERVICE_NODE_ID> \
  --node-key <NEW_NODE_KEY> \
  --name '<DISPLAY_NAME>' \
  --format raw
```

### Code 节点

先把 source 的代码内容落到临时文件，再通过 typed 命令加入。不要手工修改 target draft。

```bash
bytedcli labelgpt agent workflow add-code-node \
  --file <target.json> \
  --node-key <NEW_NODE_KEY> \
  --language python \
  --code-file <code.py> \
  --format raw

bytedcli labelgpt agent workflow update-node \
  --file <target.json> \
  --node-key <NEW_NODE_KEY> \
  --name '<DISPLAY_NAME>' \
  --format raw
```

### 模型节点

优先通过 `model list` + `set-model` 选择模型账号，让 CLI 展开 `modelIdV2`、账号和 endpoint 等模型选择字段。source 的 `ModelParamConfig` 额外字段整理为 JSON object，通过 `--model-config-file` 或 `--model-config-json` 合并。

重建时的服务节点映射规则：

- target 模型节点统一使用 `--node-id 117`。若 source 模型 ID 不在当前 `UnifiedModelList` 中，先选择同等可用模型；不要回退到旧节点协议。
- 备用链的类型与能力判定以节点 `117` 四类合并 catalog 为准，不要用 `model list --model-type <单类型>` 的字段判断备用兼容性；直接以 `set-model` 的成功/报错为准。
- MCP 能力要求模型 `SupportFunctionCall=true`，并通过 typed `set-model` 验证 API Hub server/tool。

```bash
bytedcli labelgpt model list \
  --model-type llm \
  --format raw

bytedcli labelgpt agent workflow set-model llm \
  --file <target.json> \
  --node-key <MODEL_NODE_KEY> \
  --model-id <MODEL_ID> \
  --model-config-file <model-config.json> \
  --format raw
```

创建模型节点仍然使用通用 `add-node`，然后执行 `set-model`：

```bash
bytedcli labelgpt agent workflow add-node \
  --file <target.json> \
  --node-id 117 \
  --node-key <MODEL_NODE_KEY> \
  --format raw

bytedcli labelgpt agent workflow set-model llm \
  --file <target.json> \
  --node-key <MODEL_NODE_KEY> \
  --model-id <MODEL_ID> \
  --model-config-file <model-config.json> \
  --format raw
```

typed `set-model` 会保留顶层 prompt、MCP 和异常策略，并按账号切换语义处理候选参数；`TypeKey` 变化时自动从对应模板合并 I/O。若 alias 变化会破坏下游引用，命令原子失败，需先调整引用或节点设计。

### 子 Agent 节点

`Agent调用` 节点使用服务节点 `10349`。优先用 `add-sub-agent-node` 创建，或用 `set-sub-agent` 更新已有节点：

```bash
bytedcli labelgpt agent workflow add-sub-agent-node \
  --file <target.json> \
  --node-key <CALL_AGENT_KEY> \
  --sub-agent-id <SUB_AGENT_ID> \
  --format raw
```

默认会查询该线上 Agent 的版本列表，优先选择 Used/线上版本，否则选择返回的第一个版本，并通过子 Agent 版本接口同步 `InputFields` / `OutputFields`。如果源工作流明确绑定了某个版本，也可以传 `--version-id <VERSION_ID>`。如果只想修改 `ModelParamConfig.subAgentPlanId`、`subAgentVersionId`、`subAgentVersionNumber` 而保留当前 I/O，加 `--no-sync-io`。若还需要在同步后覆盖输入绑定或输出 alias，可以继续传 `--input` / `--output`。

### 输入和输出

输入输出统一通过 `add-node` / `update-node` 的 `--input` 和 `--output` 写入。

```bash
bytedcli labelgpt agent workflow update-node \
  --file <target.json> \
  --node-key <NEW_NODE_KEY> \
  --input '{"field":"AIGC_text","source":"dataset","value":"AIGC文案","type":"1"}' \
  --output '{"key":"result","alias":"result","type":"String"}' \
  --format raw
```

不要新增单独的 set-output 命令假设；当前输出编辑和输入一样走节点 add/update。

引用重写规则：

- start 节点没有可复制或引用的输入输出；保留 target start 的空 `InputFields` / `OutputFields`，只从它连接到首个业务节点。
- 先按 source 草稿的原始数字枚举恢复每个输入：`Source=1 -> source=dataset`、`Source=2 -> source=reference`、`Source=3 -> source=custom`、`Source=4 -> source=knowledge`、`Source=5 -> source=file`。原始 `Source` 是权威信息，不能根据 `ValueKey` 形态重新分类。
- `Source=1` 常见 `ValueKey` 是 `response`、`prompt` 等裸列名，表示数据集/工作流输入列；即使该名字也出现在某个上游输出 alias 中，也不能改成 `reference`。只有原始 `Source=2` 才按上游引用处理并规范为 `$.alias` / JSONPath。
- `source=dataset` 和 `source=custom` 的 input 按原值复制。
- `source=reference` 通常引用输出 alias 或 JSONPath；如果 value 里包含旧 node key、loop 派生字段或旧 child key，必须按 `old_key -> new_key` 映射重写。
- 每个输出字段都必须有非空 alias；alias 可以和字段 key 同名，但同一工作流内不同输出字段的 alias 不能重复。
- 保持输出 alias 稳定，除非用户要求改名或原 alias 为空/重复；如果输出 alias 改名，所有下游 `source=reference` 输入必须同步改。
- loop 输出字段按 `<childKey>_<alias>_array` 生成；如果 loop child key 改名，loop 节点的 `--output` 和所有下游引用都必须同步重写。

### 边

按拓扑顺序添加边。`--from` 和 `--to` 都必须使用重写后的 `new_key`。选择器等分支节点需要带 `--source-handle`；默认保留 source 的 branch id，若 branch id 改名则同步重写 handle。

```bash
bytedcli labelgpt agent workflow add-edge \
  --file <target.json> \
  --from <SOURCE_NEW_KEY> \
  --to <TARGET_NEW_KEY> \
  --format raw
```

## Loop 特殊处理

loop body 不是 top-level 节点，必须使用 loop 子命令。

```bash
bytedcli labelgpt agent workflow add-loop-node \
  --file <target.json> \
  --node-key <LOOP_KEY> \
  --mode array \
  --input '{"field":"items","source":"reference","value":"result","type":"array"}' \
  --format raw

bytedcli labelgpt agent workflow loop add-node \
  --file <target.json> \
  --loop-key <LOOP_KEY> \
  --node-id <NODE_ID> \
  --node-key <CHILD_KEY> \
  --entry \
  --format raw
```

loop 子节点 key 不要包含 `_`，因为循环输出聚合按 `<childKey>_<alias>_array` 命名。若 source child key 已包含 `_`，重建时优先生成无 `_` 的新 child key，并同步重写 loop 输出字段和下游引用。

## Validate、Commit、Debug

```bash
bytedcli labelgpt agent workflow validate \
  --file <target.json> \
  --format raw

bytedcli labelgpt agent workflow commit \
  --file <target.json> \
  --space-id <SPACE_ID> \
  --format raw

bytedcli labelgpt agent workflow pull \
  --id <TARGET_PLAN_ID> \
  --space-id <SPACE_ID> \
  --file <after.json> \
  --format raw
```

验证拉回结果：

- 节点数和边数符合预期。
- `node_id` 是 target commit 后新生成的 ID，不是 source 的保存节点 ID。
- 普通 top-level 节点没有意外 `parent_key`。
- `old_key -> new_key` 映射中的每条边、selector handle、loop body 入口和 loop 内边都已落到 target。
- 输出 alias 符合预期。
- 修复字段聚合时，对比 source/target 的 `fields`、`finalFields`、`leafNodeFields`。

最后执行调试：

```bash
bytedcli labelgpt agent debug \
  --id <TARGET_PLAN_ID> \
  --space-id <SPACE_ID> \
  --input-file <debug.json> \
  --poll-interval 1s \
  --wait-timeout 30m \
  --format raw
```

只有 `finished=true`、`succeeded=true`、`timed_out=false` 才能确认工作流运行正常。

## 结束节点 final 字段

部分工作流使用 `ModelId=57` 结束节点，把上游输出重新暴露为最终字段。结束节点的 `OutputFields` 属于 final-field 投影，可以复用上游普通节点的 alias；`workflow validate` 和 `workflow commit` 不会把这种转发误判为 duplicate output alias。普通产出节点之间仍必须保持 alias 唯一。

重建或修复这类工作流时，保留 source 的结束节点字段映射；如果上游 alias 改名，同时更新结束节点投影。完成后仍按标准流程执行 `validate`、`commit`、拉回验证和 debug，不需要绕过 CLI 直调保存接口。
