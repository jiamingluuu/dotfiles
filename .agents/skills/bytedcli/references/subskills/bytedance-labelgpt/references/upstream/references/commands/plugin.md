# bytedcli labelgpt plugin

Plugin 命令覆盖插件列表、业务/系统插件创建、详情、本地文件拉取、上传、同步部署、发布和调试。
分页列表、创建和写操作前先确认目标 Space；按 Plugin ID 查询详情、拉取文件或调试不强制要求
`space-id`。

## plugin list

分页列出插件，或通过 `--id` 查询单个插件详情：

```bash
bytedcli labelgpt plugin list --space-id <SPACE_ID>
bytedcli labelgpt plugin list --space-id <SPACE_ID> --page-num 1 --page-size 20 --format raw
bytedcli labelgpt plugin list --space-id <SPACE_ID> --name demo --status published \
  --owner-user-id <USER_ID> --create-type label-ide --format raw
bytedcli labelgpt plugin list --id <PLUGIN_ID> --format raw
```

- `--page-num` 默认 `1`，`--page-size` 默认 `10`。
- list 模式可组合 `--name` 模糊名称、`--status unpublished|published`、`--owner-user-id` 精确 Owner 和 `--create-type label-ide|existing-service`；不同条件同时提供时取交集。枚举只接受这些可读值，不接受裸数字。
- 不带 `--id` 的分页列表依赖目标 Space；`--id` 模式按资源 ID 查询，不强制要求 Space。
- `--id` single 模式不能与分页或上述 list-only 筛选同时使用。
- 列表结果包括 `plugins`、`total`、`page_num`、`page_size`。插件摘要新增 `status_text`、`create_type`、`create_type_text` 和 `create_time`；未知枚举显示为 `unknown`。
- 单插件摘要包括 `id`、`plugin_name`、`brief_introduction`、`plugin_type`、`status`、
  `debug_status`、`number_of_citations`、`modify_time`、`owners_open_id_list`。

## plugin init

创建业务或系统插件，并拉取默认脚手架：

```bash
bytedcli labelgpt plugin init --name <NAME> --type biz --language python3 --space-id <SPACE_ID> --format raw
bytedcli labelgpt plugin init --name <NAME> --type system --language nodejs --space-id <SPACE_ID> --format raw
```

- `--name`、`--type <biz|system>`、`--language <python3|nodejs>` 必填；`--brief` 可选。
- 创建前确认 Space，并在当前命令显式传 `--space-id`。
- 创建后生成 `./plugin-<id>/main` 和 `./plugin-<id>/.plugin.yaml`。
- 结果包括 `id`、`name`、`space_id`；`-o` 写入 `plugin_<id>.json`。

## plugin view

```bash
bytedcli labelgpt plugin view --id <PLUGIN_ID> --format raw
```

返回插件详细配置，包括 `id`、`plugin_name`、`plugin_type`、`param`、`scm_source`、
`scm_build_url` 和 `multi_file`。`-o` 写入 `plugin_<id>.json`。

## plugin pull

```bash
bytedcli labelgpt plugin pull --id <PLUGIN_ID> --format raw
```

- 下载到当前目录的 `./plugin-<id>/`；目录已存在时失败，避免覆盖。
- 保留子目录结构，并生成本地参数契约文件 `.plugin.yaml`。
- 结果包括 `id`、`name`、`dir`、`files`、`file_count`；`files` 和计数不含
  `.plugin.yaml`。

## plugin push

```bash
bytedcli labelgpt plugin push --id <PLUGIN_ID> --format raw
```

- 递归读取 `./plugin-<id>/` 并保留相对路径。
- 业务/系统插件必须保留 `main`；其内容同步到远端入口配置，不计入上传文件。
- `.plugin.yaml` 用于更新参数，不作为插件文件上传；缺失时保留现有远端参数。
- `.plugin-ignore` 按规则排除不需要上传的路径。
- `.plugin.yaml` 语法非法或字段缺少 `key` 时失败，避免写入坏参数。
- 结果中的 `files` 包含 `file_name`、`suffix`、`url`，并返回 `file_count`。

`.plugin.yaml` 格式：

```yaml
input_fields:
  - key: timeout
    key_desc: 超时时间（秒）
    required: false
output_fields:
  - key: labelGPT_error_retry
    key_desc: 如返回值时系统将尝试重试，返回空值时不重试
    type: String
```

- `input_fields`、`output_fields` 都是字段数组。
- `key` 必填；`key_desc`、输入的 `required`、输出的 `type` 可选。

## plugin deploy

```bash
bytedcli labelgpt plugin deploy --id <PLUGIN_ID> --format raw
```

业务插件和系统插件调用同步 `reDeploy`。结果包括：

- `id`
- `file_count`
- `deploy_mode=sync`
- `status_code`
- `status_message`

部署失败或超时时按失败处理。`raw/json` stdout 只输出最终结果，进度与诊断写 stderr。
推荐在本轮文件和参数 push 完成后先 deploy，再 debug 或 publish；后两者不会自行证明线上版本
就是本轮内容。

## plugin debug

```bash
bytedcli labelgpt plugin debug --id <PLUGIN_ID> --input '{"foo":"bar"}' --format raw
bytedcli labelgpt plugin debug --id <PLUGIN_ID> --input-file ./input.json --format raw
cat input.json | bytedcli labelgpt plugin debug --id <PLUGIN_ID> --input - --format raw
```

- `--input` 和 `--input-file` 互斥；输入顶层必须是 JSON object。
- 输入字段名必须和插件定义完全匹配，缺少必填字段时命令先报错。
- CLI 将输入映射为服务端 `ActualValue` 后调用同步调试路径，直接返回最终结果。
- 本地代码或参数变化后按 `push -> deploy -> debug` 执行。
- 结果包括 `plugin_id`、`debug_status`、`debug_status_text`、`finished`、`result`、`log`、
  `status_code`、`status_message`。
- 调试失败返回非零；`raw/json` stdout 和 `-o` 只包含最终快照。

## plugin publish

```bash
bytedcli labelgpt plugin publish --id <PLUGIN_ID> --format raw
```

发布已部署插件，`raw/json` 返回已发布的 `id`。推荐调试通过后发布；只需要调试态时不要 publish。

## 发布后线上执行

业务/系统插件发布后按 Service Node ID 执行，不使用 Plugin ID：

```bash
bytedcli labelgpt node list --agent-id <AGENT_ID> --format raw
bytedcli labelgpt node execute --node-id <SERVICE_NODE_ID> --input '{"foo":"bar"}' --format raw
```

`SERVICE_NODE_ID` 是 `node list` 输出中的 `nodes[].node_id`，不是同一项的
`nodes[].plugin_id`，也不是 Agent 工作流节点实例 ID/key。完整输入、输出和错误规则见
[Service Node](node.md)。

## 推荐生命周期

```text
init -> 编辑 main 和 .plugin.yaml -> push -> deploy -> debug -> publish
```

完整实现与参数映射见 `../user_case/plugin_biz_system_lifecycle.md`。

## Schema

```bash
bytedcli labelgpt schema plugin list --format raw
bytedcli labelgpt schema plugin init --format raw
bytedcli labelgpt schema plugin view --format raw
bytedcli labelgpt schema plugin pull --format raw
bytedcli labelgpt schema plugin push --format raw
bytedcli labelgpt schema plugin deploy --format raw
bytedcli labelgpt schema plugin debug --format raw
bytedcli labelgpt schema plugin publish --format raw
bytedcli labelgpt schema node execute --format raw
```
