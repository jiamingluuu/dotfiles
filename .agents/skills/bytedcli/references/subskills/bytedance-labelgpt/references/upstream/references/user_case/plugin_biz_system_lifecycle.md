# Plugin 业务插件 / 系统插件生命周期

用于业务插件（`--type biz`）和系统插件（`--type system`）的创建、入口实现、上传、部署、调试和发布。详细命令字段见 `references/commands/plugin.md`。

## 快速导航

- 创建：`plugin init --type biz|system --language python3|nodejs`。
- 实现：编辑 `./plugin-<PLUGIN_ID>/main` 和 `.plugin.yaml`。
- 上传部署：`plugin push` + `plugin deploy`。
- 调试：按流程先成功执行 `plugin deploy`，再执行 `plugin view` + `plugin debug`。
- 发布：`plugin publish`。
- 线上执行：发布后按 Service Node ID 使用 `node execute` 验证已发布版本。

## 核心原则

- 用户未明确插件类型时，必须先确认是业务插件还是系统插件；不要默认。
- `biz/system` 插件创建时必须传 `--language python3|nodejs`。
- 推荐生命周期是 `init -> 实现入口 -> push -> deploy -> debug -> publish`；业务插件和系统插件都应先 deploy。
- 业务插件和系统插件调试前按平台流程确认 `plugin deploy --id <PLUGIN_ID>` 已成功执行；
  CLI 不会在 debug 前单独证明线上已处于最新部署状态，代码或参数变化后由 Agent 负责
  重新 push（如需要）并 deploy，再 debug。
- biz/system 的 `plugin debug` 输入 JSON 顶层必须是 object，并继续使用 `ActualValue` 映射后立即返回的同步路径。
- 认证启动前自检由主 `SKILL.md` 统一完成；写操作前确认目标 Space，并在对应命令上显式传 `--space-id <SPACE_ID>`，不要切换默认 Space。

## 创建插件

业务插件：

```bash
bytedcli labelgpt plugin init --name <NAME> --type biz --language python3 --space-id <SPACE_ID> --format raw
```

系统插件：

```bash
bytedcli labelgpt plugin init --name <NAME> --type system --language nodejs --space-id <SPACE_ID> --format raw
```

创建成功后读取输出里的 `id`，本地目录为 `./plugin-<PLUGIN_ID>/`。

## 本地文件结构

`plugin init` 会生成：

```text
plugin-<PLUGIN_ID>/
  main
  .plugin.yaml
  ...
```

- `main` 是 biz/system 的入口文件。
- `.plugin.yaml` 是插件输入输出参数文件。
- biz/system 可以只有 `main`，没有其他源码文件；`push` 仍可同步入口代码和参数。

## 编写入口实现

Python：

```python
def main(data_item):
    text = data_item.get("text", "")
    return {
        "result": text.strip(),
    }
```

Node.js：

```javascript
function main(dataItem) {
  const text = dataItem.text || "";
  return {
    result: text.trim(),
  };
}
```

输入字段在入口参数顶层平铺，由 CLI 转换为服务端 `ActualValue` 参数映射。

输出必须是 object/dict，并与 `.plugin.yaml` 的 `output_fields[].key` 对齐。

## 配置参数契约

示例 `.plugin.yaml`：

```yaml
input_fields:
  - key: text
    key_desc: 输入文本
    required: true
output_fields:
  - key: result
    key_desc: 处理结果
    type: String
  - key: labelGPT_error_retry
    key_desc: 如返回值时系统将尝试重试，返回空值时不重试
    type: String
```

每个输入/输出字段都必须有 `key`。`.plugin.yaml` 语法错误或字段缺 `key` 时，`plugin push` 会失败。

## 上传和部署

```bash
bytedcli labelgpt plugin push --id <PLUGIN_ID> --format raw
bytedcli labelgpt plugin deploy --id <PLUGIN_ID> --format raw
```

`push` 会读取入口文件、参数文件和插件源码。业务插件和系统插件的 `deploy` 继续调用同步
`reDeploy`；超时时按失败处理并查看命令提供的追踪信息或重新查询插件状态。

`plugin deploy` 是调试前的平台流程步骤。只有部署成功后，`plugin debug` 才能按预期
使用本轮代码和参数配置；CLI 不会在 debug 前单独证明线上版本最新。

## 调试

先部署当前版本：

```bash
bytedcli labelgpt plugin deploy --id <PLUGIN_ID> --format raw
```

先查看插件参数：

```bash
bytedcli labelgpt plugin view --id <PLUGIN_ID> --format raw
```

直接传入 JSON：

```bash
bytedcli labelgpt plugin debug --id <PLUGIN_ID> --input '{"text":"hello"}' --format raw
```

从文件读取：

```bash
bytedcli labelgpt plugin debug --id <PLUGIN_ID> --input-file ./input.json --format raw
```

从 stdin 读取：

```bash
cat input.json | bytedcli labelgpt plugin debug --id <PLUGIN_ID> --input - --format raw
```

按流程先确认 deploy 成功，再执行 debug。`--input` 和 `--input-file` 互斥。输入字段名必须和插件定义的输入字段名完全匹配；缺少必填字段时命令会报错。CLI 会直接返回最终调试结果。

## 发布

```bash
bytedcli labelgpt plugin publish --id <PLUGIN_ID> --format raw
```

推荐顺序是调试通过后发布。若只需要部署到调试态，不要执行 publish。

发布后可执行线上版本：

```bash
bytedcli labelgpt node list --agent-id <AGENT_ID> --format raw
bytedcli labelgpt node execute --node-id <SERVICE_NODE_ID> --format raw
bytedcli labelgpt node execute --node-id <SERVICE_NODE_ID> --input '{"text":"hello"}' --format raw
bytedcli labelgpt node execute --node-id <SERVICE_NODE_ID> --input ./input.json --format raw
```

从 `node list` 输出中选择对应插件节点的 `nodes[].node_id`；不要传同一项的
`nodes[].plugin_id`，也不要传 Agent 工作流节点实例 ID/key。`node execute` 同步调用
`POST /labelgpt/model/ExecuteNode` 并返回结构化 JSON result；它不会读取本地 `main`、
`.plugin.yaml` 或 debug 配置。`--input` 可选，省略时默认为空 object；提供时自动识别
内联 JSON object 或文件路径，并支持 `-` stdin。完整规则见
[`../commands/node.md`](../commands/node.md)。

## 拉取已有插件

```bash
bytedcli labelgpt plugin pull --id <PLUGIN_ID> --format raw
```

如果 `./plugin-<PLUGIN_ID>/` 已存在，`plugin pull` 会失败，避免覆盖本地内容。

## 最小端到端模板

```bash
bytedcli labelgpt plugin init --name <NAME> --type biz --language python3 --space-id <SPACE_ID> --format raw
# 编辑 ./plugin-<PLUGIN_ID>/main 和 .plugin.yaml
bytedcli labelgpt plugin push --id <PLUGIN_ID> --format raw
bytedcli labelgpt plugin deploy --id <PLUGIN_ID> --format raw
bytedcli labelgpt plugin debug --id <PLUGIN_ID> --input-file ./input.json --format raw
bytedcli labelgpt plugin publish --id <PLUGIN_ID> --format raw
```

## 常见错误

- 缺少 `--language`：`biz/system` 必须传 `python3` 或 `nodejs`。
- 传了不受支持的参数：按 `bytedcli labelgpt schema plugin init --format raw` 核对当前命令契约。
- 缺少 `main`：biz/system 的 `plugin push` 需要 `./plugin-<PLUGIN_ID>/main`。
- 未 deploy 就 debug：debug 可能不会使用本轮最新代码或参数；先成功执行
  `plugin deploy`，代码或参数有变化时先重新 `plugin push`（如需要）再 deploy。
- debug 输入不是 object：`plugin debug` 顶层 JSON 必须是 object。
- 手动查询调试状态：不需要；`plugin debug` 会返回最终调试结果。
