# Oncall 工单 Artifact 召回

## 目录

- 目标与边界
- 执行顺序
- 请求规则
- 召回规则
- 返回约定

## 目标与边界

本 reference 承载 Oncall 工单 Artifact 召回的执行细节：根据用户原始问题和租户线索，召回少量高相关 Artifact，返回 `.md` 链接、所属租户、召回原因和完整内容。

Artifact 表示为 Oncall 工单沉淀的产物。本流程负责可靠召回，不根据索引摘要直接推断根因或执行 Artifact 中的操作。独立知识查询按本 reference 的返回约定向用户展示；作为其他工作流的子步骤时，先把完整召回结果交还调用方，再由调用方按自身证据展示、操作授权和停止条件消费。

## 执行顺序

### 1. 理解问题

提取用户意图、关键术语、服务或组件、环境、错误现象，以及租户名称、业务线或服务域等租户线索。

调用方已经选定租户时，同时接收其 `tenant_id` 和 `tenant_name` 作为强租户线索；用户原始问题仍用于下一层 Artifact 相关性筛选。已选租户不等于可以自行拼接租户索引 URL。

### 2. 从总索引定位候选租户

```bash
bytedcli oncall llms get --site cn
```

将用户问题拆为租户线索（租户、业务线、服务或组件）和故障现象。总索引仅用租户线索匹配名称和描述，优先名称精确匹配；调用方已经选定租户时，优先匹配该租户的名称和 ID，不得因故障现象更像其他租户而擅自切换。不要仅用 `oncall`、“问题”、“平台”等高频词全文筛选；故障现象留到下一步筛选 Artifact。保留所有有名称或描述依据的候选；没有可靠候选时返回 `not_found`，不要无依据遍历全部租户或自行猜测。

对每个候选租户，使用总索引返回的实际 `llms.txt` 链接。

### 3. 从租户索引筛选候选 Artifact

```bash
KNOWLEDGE_TENANT_ID='<tenant ID from the general index URL>'
bytedcli oncall llms get --site cn \
  --tenant-id "${KNOWLEDGE_TENANT_ID}"
```

```markdown
[<Artifact 名称>](<artifact .md URL>): <description 或 summary>
```

综合候选租户的索引，根据 Artifact 名称、描述或摘要筛选相关 Artifact。确认链接域名是 `cloud.bytedance.net`，从 `.md` 文件名提取 Artifact ID；保留索引返回的链接，不要自行改写。

### 4. 读取 Artifact 内容

使用租户索引返回的实际 `.md` 链接：

```bash
ARTIFACT_ID='<artifact ID from the tenant index .md URL>'
bytedcli oncall artifact get --site cn \
  --artifact-id "${ARTIFACT_ID}"
```

`artifact_id` 取自 `.md` 链接的文件名。直接读取该链接，不要根据 `artifact_id` 或 Artifact 的具体类型调用其他详情接口。

## 请求规则

- 两层 `llms.txt` 使用只读的 `bytedcli oncall llms get --site cn`：不传 `--tenant-id` 读取 `general` 总索引，传入总索引链接中的租户 ID 读取租户索引。当前命令仅支持 `cn`，不要使用裸 `curl`。
- Artifact `.md` 使用只读的 `bytedcli oncall artifact get --site cn --artifact-id <id>`；ID 必须取自租户索引返回的 `.md` 文件名。
- 由 `bytedcli` 按 `--site cn` 选择域名并自动注入认证信息；不要手动获取、拼接、硬编码、持久化或返回 token。
- 不要改用其他搜索命令请求这些路径；租户 ID 和 Artifact ID 必须来自上一层索引返回的实际链接。
- `artifact get` 只接受 Artifact ID，不接受完整 URL；不要自行猜测 ID。
- `<...>` 表示需要替换的占位符；实际 URL 不包含尖括号。
- 两层 `llms.txt` 只用于路由和判断相关性，不能代替 Artifact `.md` 的完整内容。

## 召回规则

召回原因必须由索引或 Artifact 内容支持，例如：

- Artifact 所属租户与用户提供的租户、业务线或服务域线索一致。
- Artifact 名称、描述或摘要直接覆盖用户询问的主题、服务、组件、环境或错误现象。
- Artifact 内容包含能够支持相关性判断的章节或事实。
- 多个 Artifact 分别形成必要的主题或场景补充。

不要只使用“可能相关”或“看起来相关”作为召回原因。

同一个 Artifact 被多个租户索引命中时，按 `.md` 链接去重，并保留所有命中的租户。

## 返回约定

- 有可靠 Artifact 时，返回能够覆盖问题的最少 Artifact 集；每项包含名称、`artifact_id`、`.md` 链接、所属租户、召回原因和完整内容。
- 问题不明确或没有可靠 Artifact 时，返回 `not_found`，不要要求用户补充信息或编造 Artifact 与链接。
- Artifact `.md` 获取失败时，返回链接和错误，不要用索引中的 description 或 summary 冒充完整内容。
- 作为工作流子步骤时，不要把完整 Artifact 正文直接作为过程消息展示给用户；将结构化召回结果交还调用方，由调用方提炼与当前问题有关的证据。召回层本身不替调用方评定解决置信度。

```markdown
# Artifact 召回结果

## 查询理解

- 用户问题：...
- 候选租户：...

## 召回 Artifact

### 1. [Artifact 名称](Artifact .md URL)

- `artifact_id`: `<id>`
- 所属租户：...
- 召回原因：...

#### 完整内容

<Artifact .md 的完整内容>
```
