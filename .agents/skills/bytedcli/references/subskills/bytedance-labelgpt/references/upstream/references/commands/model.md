# model 命令

## `model list`

`model list` 直接调用 `UnifiedModelList`，没有按类型拆分的子命令，也不接受节点 ID、旧模型分类、客户端授权过滤或按模型 ID 过滤。

```bash
bytedcli labelgpt model list --format raw
bytedcli labelgpt model list --model-type llm,multimodal --channel MERLIN --format raw
bytedcli labelgpt model list --model-name doubao --format raw
bytedcli labelgpt model list --page-num 1 --page-size 50 --format raw
```

业务参数：

- `--model-type`：可重复或逗号分隔，值为 `llm|multimodal|image_gen|video_gen`；不传表示由服务端返回全部。
- `--model-name`、`--channel`：模型筛选，服务端对 DB / ByteCloud / ModelHub 全部源生效，是收窄结果的推荐方式。
- `--approval`：只允许 `1|2`。
- `--unpublished-auth`、`--support-offline-inference 0|1|2`、`--support-function-call`。
- `--page-num` 与 `--page-size` 必须成对提供且为正数；都不传时请求不包含 `PageRequest`。
- `CommonRequest` 与 `Base` 由客户端注入，不是公开 flag。

> 不提供按模型 ID 过滤（`ModelId/ModelIds`）：`UnifiedModelList` 只把这类 ID 透传给 DB 源，ByteCloud/ModelHub 源不过滤，并按存活账号对每个 name-group 的 `AbilityList/ModalityList` 取并集，因此 ID 过滤会丢兄弟账号、让能力字段随请求形态收缩，不适合作稳定筛选。需要收窄时用 `--model-name` / `--channel` / `--model-type`；判断某账号真实类型或能否作备用时以 `set-model` 的判定为准（见下文“配置统一模型节点”）。

`raw/json` 与 `-o` 文件直接使用接口 `data`，顶层固定为 `BaseResp`、`GroupList`、`Total`。CLI 不输出 `code/message`，不加 wrapper，不扁平化、去重、重算 `Total` 或二次过滤。模型账号位于 `GroupList[].ModelNameList[].ModelList[]`，账号 ID 是每个 `ModelList[].ModelId`；`GroupList[].ModelList` 仅作为接口兼容字段原样输出，不用于模型选择。

模型账号完整保留 IDL 的 36 个字段，包含授权审批、`modelParams`、能力与渠道字段。`modelParams` 结构为 `field/label/compType/defaultValue/options[{label,value}]`。

```bash
bytedcli labelgpt schema model list --format raw
```

## 配置统一模型节点

工作流仅支持可写统一模型节点 `117`，`set-model` 是命令组，必须选择 typed 叶子：

```bash
bytedcli labelgpt agent workflow set-model llm --file draft.json --node-key model --model-id <MODEL_ID> --format raw
bytedcli labelgpt agent workflow set-model multimodal --file draft.json --node-key model --model-id <MODEL_ID> --format raw
bytedcli labelgpt agent workflow set-model image-gen --file draft.json --node-key model --model-id <MODEL_ID> --format raw
bytedcli labelgpt agent workflow set-model video-gen --file draft.json --node-key model --model-id <MODEL_ID> --format raw
```

每个叶子必需 `--file --node-key --model-id`。可选 `--model-config-json` 或 `--model-config-file`，二者互斥；JSON 根对象就是前端 `ModelParamConfig` 的局部覆盖。

```json
{
  "prompt": "You are helpful.",
  "thinking": 1,
  "showWebSearch": 2,
  "modelConfigs": [
    {},
    {"modelIdV2": "backup-model-id"}
  ]
}
```

- `--model-id` 是主模型唯一权威 ID；`modelConfigs[0].modelIdV2` 可省略，提供时必须一致。
- 不提供 `modelConfigs` 时保留当前备用链；显式提供时替换完整主备链；`[]` 表示清空备用并重建主模型。
- 最多三个备用模型。主备账号必须唯一、已授权、同 `TypeKey`，备用的 `AbilityList/ModalityList` 必须覆盖主模型。
- **能力/类型判定的真相来源**：`set-model` 按节点 `117` 的四类合并 catalog（`ModelTypes=[llm,multimodal,video_gen,image_gen]`，与前端一致）解析每个账号的权威 `TypeKey/AbilityList/ModalityList`，并据此做类型和能力超集校验。同一账号在 `model list --model-type <单类型>` 单类型视图里可能解析成不同的 `TypeKey`（例如同 name-group 有多模态兄弟时文本账号会被提升为 `multimodal`），因此**不要用单类型 `model list` 的字段判断备用兼容性**，直接以 `set-model` 的成功/报错为准。
- API 返回的账号身份与元数据覆盖调用方同名字段；API key 等 secret 只进入草稿，不进入命令结果或错误。
- CLI 只对主模型读取 `GetModelConfigInfo(SceneKey=agent)`，应用默认值、options、validator 与 `onChange` rules；失败时草稿不变。
- `raw/json` 输出是节点摘要，包含 `selected_model_id/type_key/backup_model_ids`，不回显模型配置或 secret。

## Prompt 模板与输入字段

模型节点的输入字段只负责从 Dataset、上游节点或固定值取得数据；声明字段或设置 type 不会把它自动追加到模型内容。要让文本或媒体实际进入模型消息，必须在 `userPrompt` 或 system prompt（模型配置中的 `prompt`）里使用 `{{field}}` 引用它。占位符名称大小写敏感，必须与输入字段 `Key` 完全一致。

读取已有模型节点草稿时，输入来源以原始数字枚举为准：`Source=1` 是 `dataset`，`Source=2` 是 `reference`，`Source=3` 是 `custom`。`Source=1` 的裸 `ValueKey`（如 `response`）是数据集列名，不是按 alias 引用上游输出；迁移或重建时不要根据 `ValueKey` 是否带 `$.` 来反推来源。完整的 `1..5` 映射见 [Agent 工作流的参数与草稿规则](agent-workflow.md#参数与草稿规则)。

`userPrompt` 和 system prompt 都支持 `{{field}}` 模板。媒体通常放在 `userPrompt`，这样角色与内容顺序最直观。对 `multimodal` 节点，输入 type 决定占位符所在位置生成的内容：

| 输入 type | 占位符行为 | 值要求 |
| --- | --- | --- |
| `type=1` | 在占位符位置插入文本；对象和数组按 JSON 文本序列化 | 字符串、对象或数组 |
| `type=2` | 在占位符位置构造 `image_url` 消息片段 | HTTP(S) 图片 URL |
| `type=3` | 在占位符位置构造 `video_url` 消息片段 | HTTP(S) 视频 URL |
| `type=4` | 在占位符位置构造 `audio_url` 消息片段 | HTTP(S) 音频 URL |

媒体值支持单个 URL、JSON URL 数组或逗号分隔的 URL；每一项都必须是 `http://` 或 `https://` URL。媒体片段插入到占位符所在位置，因此多个占位符在 Prompt 中的先后顺序就是消息内容顺序。

以下四类模板分别消费文本变量、图片、视频和音频：

```text
请总结以下材料：{{article}}
请描述图片：{{imageUrl}}
请分析视频：{{videoUrl}}
请转写音频：{{audioUrl}}
```

对应的辅助字段分别使用 `article/type=1`、`imageUrl/type=2`、`videoUrl/type=3` 和 `audioUrl/type=4`。例如 `article` 的值是 `[{"title":"A"}]` 这样的数组时，会作为 JSON 文本插入；`imageUrl` 的值可以是单个图片 URL、`["https://a.example/1.png","https://a.example/2.png"]`，或以逗号分隔的两个 URL。

引用不存在的字段会得到空内容。未引用的辅助文本字段不会进入 Prompt，未引用的媒体字段不会成为多模态消息：

```text
错误：userPrompt = "请描述图片"，同时只绑定 imageUrl/type=2
正确：userPrompt = "请描述图片：{{imageUrl}}"，同时绑定 imageUrl/type=2
```

推荐按以下顺序配置；如果节点尚未初始化，可以先选择一次目标类型的模型取得模板，但最终仍要完整执行这组步骤：

1. 使用 `update-node` 绑定全部输入及其最终 type。
2. 在 `userPrompt` 中配置所需占位符；system prompt 如需变量，也在最后一次 `set-model` 的模型配置中写入占位符。
3. 最后运行 typed `set-model`，让模型配置按最终 I/O 重建。
4. 依次执行 `workflow validate`、`workflow commit` 和 `agent debug`。

图片理解示例：

```bash
bytedcli labelgpt agent workflow update-node \
  --file draft.json --node-key model \
  --input '{"field":"userPrompt","source":"custom","value":"请描述图片：{{imageUrl}}","type":"1"}' \
  --input '{"field":"imageUrl","source":"dataset","value":"image_url","type":"2"}' \
  --format raw

bytedcli labelgpt agent workflow set-model multimodal \
  --file draft.json --node-key model --model-id <MODEL_ID> --format raw
bytedcli labelgpt agent workflow validate --file draft.json --format raw
bytedcli labelgpt agent workflow commit --file draft.json --space-id <SPACE_ID> --format raw
bytedcli labelgpt agent debug --id <AGENT_ID> --input '{"image_url":"https://example.com/image.png"}' --format raw
```

若图片来自上游节点，把 `imageUrl` 的 `source` 改为 `reference`，并把 `value` 设为对应输出 alias 或 JSONPath。若在 `set-model` 后新增多模态字段，或修改了字段 key/type，必须重新运行同一个 `set-model multimodal`；否则草稿里的模型输入映射仍可能是旧值。

`image_gen` / `video_gen` 的参考图是节点的专用参考图输入，由生成执行器直接消费，不是通过 `type=2` 占位符构造的多模态消息。生成 Prompt 里的普通文本变量仍使用 `{{field}}`，但不要为了传入参考图而把专用 `imageUrl` 强行写成多模态媒体占位符。

完整物化规则与查询约定见 [统一模型节点](../domain/unified-model-node.md)。
