# 统一模型节点 117

## 数据流

```text
UnifiedModelList data
  -> 只索引 GroupList[].ModelNameList[].ModelList[]
  -> name-group 继承 AbilityList / ModalityList
  -> 校验主备账号与 typed TypeKey
  -> 前端同构 normalizeModelConfig + 账号元数据
  -> GetModelConfigInfo(仅主模型, SceneKey=agent)
  -> runtime 能力与模板 I/O 归一
  -> 克隆草稿一次性写回
```

`UnifiedModelList` 的 wire data 保持 `BaseResp/GroupList/Total` 原样。兼容字段 `UnifiedModelGroup.ModelList` 会序列化输出，但绝不参与模型选择。可选标量使用指针 DTO，服务端实际返回的 `false/0/""` 不会因 `omitempty` 丢失。

### set-model 的查询约定

`set-model` 解析主备账号时按节点 117 的完整类目请求 `ModelTypes=[llm,multimodal,video_gen,image_gen]`（与前端 `MERGE_LLM_MODEL_TYPES` 一致），不发送 `ModelId/ModelIds`，也不发送 `PageRequest`：

- 必须请求全部四种类型，不能只请求当前叶子的类型：后端 `buildUnifiedModelGroup` 从**合并视图**推导每个账号的权威 `TypeKey`——当同一 name-group 里同时存在多模态兄弟时，纯文本账号会被 `convertLlmListToUnifiedMultimodal` 提升为 `multimodal`。只请求单一类型会让同一账号解析出与编辑器不同的 `TypeKey` 和能力集。
- `ModelId/ModelIds` 只被服务端透传到 DB 源，而 ByteCloud 和 ModelHub 两个 RPC 源只按 `ModelName/ModelCategory` 查询、不认这些 ID。随后聚合逻辑按 `ModelName` 分桶，并对存活账号的 `AbilityList/ModalityList` 取并集。因此带 ID 过滤时同一 name-group 会丢掉兄弟账号，导致目标账号继承到的能力集随请求形态收缩，破坏能力超集判定与 runtime 归一。
- 已发布模型链路不会回填 `PageRequest`，catalog 本就完整返回，发送分页既无效又易误导。

拉取完整 catalog 后，CLI 在本地按 `modelIdV2` 选主备账号，`TypeKey` 与 `AbilityList/ModalityList` 与前端节点 117 同构，因此 typed 叶子的类型校验和备用能力超集校验与前端结论一致。

## 主备链与切换

- `modelConfigs[0]` 是主模型，后续最多三个备用。`--model-id` 决定主模型。
- 精确相同账号按 `modelIdV2` 保留参数，主备重排不丢参数。
- 同一 name-group 换账号保留运行与动态参数；跨 name-group 清空旧候选参数，再应用新模型默认值。
- 未显式提供 `modelConfigs` 时保留备用链；如果保留后的备用不再满足同类型、授权、去重或能力超集约束，整次命令失败。
- 显式 `modelConfigs: []` 清空备用；显式列表替换完整主备链。

候选固定写入 `modelId/modelIdV2/originModelId/largeModelBase/largeModelName/modelName/chatModelId/modelCategory/accountType/accountRole/accountName/accountLabel/accountSourceType/endpoint/endpointName/userAuthId/isAuthorized/modelAffiliation/medivhAiConfig/aiConfig/abParams`。

账号映射：

| 条件 | accountType | 特殊字段 |
|---|---:|---|
| `accountRole=0` | 1 | 公共账号 |
| `endpoint + userAuthId` | 3 | ByteCloud；`largeModelBase=ModelName`，删除 `chatModelId`，写 `medivhAiConfig` |
| `PlatformChannel=GPT_OPENAPI/GPT_CHATBOT` | 5 | GPT personal |
| `PlatformChannel=MERLIN` | 6 | Merlin |

非 ByteCloud 使用 `largeModelBase=OriginModelId`、`chatModelId=ModelId`。候选级 `TypeKey`、`_capability` 等编辑态派生字段不持久化。

## 固定字段与模板

| TypeKey | 模板节点 | 固定适配 |
|---|---:|---|
| `llm` | `59` | 文本 prompt/system prompt；按能力管理推理、联网与 MCP |
| `multimodal` | `53` | 第一输入固定 `Type=1` 且必填；其余非必填，`1/2/3/4=text/image/video/audio`，由最终输入重建 `MultiModelConfig` |
| `image_gen` | `116` | `imageUrl.LimitCount` 使用模型 `LimitCount`，缺失回退 `1` |
| `video_gen` | `115` | 按 `supportPicture` 增删 `imageUrl` 参考图输入 |

首次配置、I/O 为空或 `TypeKey` 变化时，从 `GetServiceNodeList(AgentId)` 合并模板和已有绑定；相同类型换账号保留自定义 I/O。输出 alias 自动补全且工作流内唯一，`ModelInputOutputField` 归一为空数组。

节点 `117` 是工作流唯一可写的统一模型入口；表中的节点 `53` 只作为内部 I/O 模板，不能据此引导用户直接配置旧多模态节点。对 `multimodal`，`MultiModelConfig` 是从最终 `InputFields` 重建的字段类型表，不是自动附加字段列表：字段绑定只负责把值放入执行参数，文本和媒体字段都由 Prompt 占位符触发消费。文本值在占位符处替换，媒体值在占位符处展开为对应内容片段，因此 Prompt 中的顺序决定消息内容顺序；没有被引用的字段不会进入消息。

`image_gen` / `video_gen` 的 `imageUrl` 是生成执行器直接消费的专用参考图输入，与 `multimodal` 中媒体字段经 Prompt 占位符构造消息片段是两条不同路径。生成类 Prompt 仍可用占位符消费普通文本辅助字段，但参考图本身不依赖多模态类型表或媒体占位符。

每个候选都有 `aiConfig.temperature=1`、`topP=1`、`maxToken=模型 MaxToken`；MaxToken 非正数才回退 `4096`。`AbParams` 原样保留并按 `gpt_engine/graph_config` 路径反解三个运行参数；`Extra.supportIgnoreRisk` 和图片输入下的 `supportImageDetail/imageDetailOptions/imageDetailDefault` 驱动附加配置，`AdvancedConfig` 原样保留。图片/视频专属参数不硬编码，统一由动态 schema 提供。

## 动态 schema 与 runtime

仅主模型调用 `GetModelConfigInfo(ModelName, ModelCategory, SceneKey=agent)`。先处理 `prefix.agent`，再把 `ModelParamConfig.*` 重定位到 `ModelParamConfig.modelConfigs[0].*`。当前值优先；缺失使用 `defaultValue`；options 外的值重置为默认值；最终执行 required/type/range/options validator。

`onChange` rules 支持 `empty/notEmpty/eq/neq/gt/lt/gte/lte/in/notIn`，change 支持 `value/clearValue`；`props` 只影响 UI，不写草稿。`{{ expression }}` 在无宿主能力、带超时中断的 JavaScript runtime 中求值。schema 拉取、解析、默认值、规则或校验失败都会使草稿保持不变。

- 推理：顶层 `supportCot/thinking` 驱动 `reasoning_content:String` 输出。
- 联网：仅 `IsWebSearch=1` 可启用 `showWebSearch=1` 和 `web_search_result:String`；默认关闭为 `2`。
- MCP：仅 `SupportFunctionCall=true` 可用 `RuntimeMode=mcp`；验证 API Hub server/tool 与 API key，使用 `ApiId/apikeyOfApihubForAgent/mcp/apihub_tools/mcpsource/maxCallNum/toolPrompt/languageType/code`。默认 `RuntimeMode=normal`、`maxCallNum="60"`、`mcpsource=3`、`languageType=2`。

所有远端读取、解析和校验都先作用于克隆草稿，成功后才由命令执行一次文件写回。
