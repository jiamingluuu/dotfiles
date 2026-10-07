---
name: get-figma-design-description
description: 调用 getFigmaDescription 接口，按 figmaPageUrl + node-id 拉取人工沉淀的 Figma 节点语义描述（Role/Intent/Data/Implementation/Unknowns），作为额外语义上下文辅助 browser-design-to-code / lynx-design-to-code 生成代码。
allowed-tools: Bash, Read
---

# 获取 Figma 节点语义描述

按 `figmaPageUrl` + Figma 节点 `node-id`，从远端拉取人工沉淀的**语义描述**（D2C semantic description）。这些描述是对节点意图的简短文本契约（通常含 `Role / Intent / Data / Implementation / Unknowns`），也可能是结构化 JSON，用来在 **browser-design-to-code** / **lynx-design-to-code** 生成代码时补充“设计稿看不出来的语义”，比如某块是可点击卡片、某段文案绑定哪份数据、某区域的实现约束等。

本 capability 用 `bytedcli d2c figma get-description` 命令调用该服务，无需本地起服务。

这是一条 **✅ bytedcli command**，且是 **read-only** 的查询：它只读取已沉淀的描述，不创建任务、不消耗算力、不写任何远端状态。

## 何时使用

在 region-generation / full-page-generation / global-assembly 等生成流程里，拿到 Figma JSON / IR、确定要生成哪些节点后，**生成代码前**调用本 capability：

1. 用区域 / 整页里关注的节点 `node-id` 逐个查询。
2. 命中的描述作为该节点的语义补充，优先级高于纯视觉猜测、低于截图与 Figma 结构本身（见下方「如何使用结果」）。
3. 如果命中描述是 JSON，读取其中的 `rootConfig`；若存在可识别的根级配置，生成页面时必须应用到页面最根部节点。
4. 未命中的节点照常按截图 + Figma 结构生成，不要因为缺描述而中断。

## 用法

```bash
bytedcli --json d2c figma get-description \
  --figma-page-url "https://www.figma.com/design/<fileKey>/<name>" \
  --figma-node-id "364-39184"
```

命令一次查询**一个**节点。要覆盖一个区域 / 整页的多个节点时，在 shell 里循环：

```bash
for id in 364-39184 382-46559 295-21010; do
  bytedcli --json d2c figma get-description \
    --figma-page-url "https://www.figma.com/design/<fileKey>/<name>" \
    --figma-node-id "$id"
done
```

- `--figma-page-url`（必填）：Figma 页面链接。**可直接传含 `?node-id=...` 的完整链接**，命令会先归一为 baseUrl（只保留 scheme+host+path、剥掉 query/hash）再查询，所以带不带 query 都能命中。
- `--figma-node-id`（必填）：要查询的节点 id，一次一个。**短横线或冒号形式都可以**，命令会统一成 Figma 规范的冒号形式（URL 里的 `274-11320` → `274:11320`）再查询，与服务端唯一键一致。
- 所有参数都由调用方（agent）从上下文中明确给出，命令不会自动推断。

## 返回结构

每次调用返回该节点的查询结果 JSON：

```jsonc
{
  "figmaPageUrl": "https://www.figma.com/design/<fileKey>/<name>",
  "figmaNodeId": "364-39184",
  "found": true,
  "figmaDescription": "{\"rootConfig\":{\"fontSize\":14},\"role\":\"...\"}",
  "semanticJson": { "rootConfig": { "fontSize": 14 }, "role": "..." },
  "rootConfig": { "fontSize": 14 },
  "updatedAt": "..."
}
```

- `found: true` → 用 `figmaDescription` 作为该节点的语义补充。
- `semanticJson` → 当 `figmaDescription` 是 JSON 字符串或对象时由命令解析透出，便于生成流程直接读取结构化字段。
- `rootConfig` → 当 `semanticJson.rootConfig` 存在时由命令提升到结果顶层；生成页面时把其中可识别的根级配置应用到页面最根部节点，例如样式类配置应落到 `.page-root` / Lynx 根 `<view>` 对应 class 上。
- `found: false` → 该节点没有人工描述，**属正常**，照常生成。
- 循环查询多个节点时，逐个汇总各次调用的结果；某个节点查询失败不影响已命中的其他节点。

## 如何使用结果（生成代码时）

把命中的 `figmaDescription` 并入该节点的语义判断，作为 browser / lynx 生成的输入之一。若结果包含 `semanticJson` / `rootConfig`，优先读取结构化字段，不要只按纯文本处理。来源优先级：

1. 截图 / 区域裁图：视觉事实。
2. Figma JSON / IR：结构、文本、资源、重复数据。
3. **本 skill 的 `figmaDescription`：人工沉淀的语义意图与实现约束**（解释“为什么这么做”，补结构看不出的数据绑定 / 交互 / 实现要点）。
4. 平台与组件 references：实现约束。

当 `figmaDescription` 与视觉 / 结构冲突时，以截图与 Figma 结构为准，把描述里的差异作为存疑项记录到 RFC，不要盲信描述覆盖视觉事实。

当 `rootConfig` 与视觉 / 结构不冲突时，它是页面根节点配置契约。读取到可识别的根级样式、布局或运行配置时，必须转换成目标平台对应写法并写到页面最根部节点上，而不是写到某个内部节点或丢弃。未知字段不要臆造含义，可记录到 RFC / notes。

## ⚠️ 重要注意事项

1. **执行环境**：命令调用**必须**用 `Bash` 工具执行，**切勿**通过重复调用 `Skill` 工具来运行命令。
2. **缺描述不是错误**：`found: false`（404）是常见且正常的情况，照常按截图 + Figma 结构生成。
3. **错误透传**：某次调用报错时把对应 message 透传给用户；仅当全部节点都查询失败时才终止，否则继续用已命中的部分。
4. **不要泄露真实链接到产物**：把 `figmaPageUrl` 当输入用，不要把内网接口地址 / 完整链接写进最终生成的代码或文档。
