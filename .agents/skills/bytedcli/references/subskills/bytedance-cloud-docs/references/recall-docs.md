# Cloud Docs 文档搜索与召回

## 目标与边界

本 reference 由 `bytedance-cloud-docs` 主 Skill 路由到文档搜索与召回路径后读取，只承载该路径的执行细节：根据用户原始问题和产品或组件线索，召回少量高相关 ByteCloud 文档，返回文章链接、召回原因和 Markdown 正文。

本流程只负责召回并返回文档；对于文章的后续操作，不由本流程决定。

## 执行顺序

### 1. 理解问题

提取用户意图、关键术语、产品或组件线索，以及内容类型，例如概念、原理、接入、配置、最佳实践或排障。

### 2. 从总索引定位候选组件

```bash
bytedcli insearch get \
  'https://cloud.bytedance.net/api/v1/cloud_developer/docs/all/cn/llms.txt'
```

根据总索引中的组件名称、分类和描述选择少量候选组件。线索不足时，请用户补充一个最关键的信息点；不要遍历全部组件或自行猜测。

### 3. 从组件索引筛选候选文章

使用总索引返回的实际 `llms.txt` 链接：

```bash
COMPONENT_LLMS_URL='<component llms.txt URL from the global index>'

bytedcli insearch get "${COMPONENT_LLMS_URL}"
```

保留索引返回的域名、站点、语言和路径，不要自行改写 URL。

### 4. 读取文章正文

使用组件索引返回的实际 `.md` 链接读取候选文章：

```bash
ARTICLE_MD_URL='<article.md URL from the component index>'

bytedcli insearch get "${ARTICLE_MD_URL}"
```

只读取判断和回答所需的文章，不要为了凑数量返回弱相关文档。

## 请求规则

- `llms.txt` 和 `.md` 请求统一使用 `bytedcli insearch get <url>`。
- `insearch get` 会根据 URL 自动附带 ByteCloud JWT；不要手写、持久化或返回 token。
- 不要改用 `bytedcli cloud-docs` 请求这些 URL。

## 选文规则

召回原因必须由索引或正文支持，例如：

- 文章所属产品或组件与用户问题一致。
- 标题或目录直接覆盖用户询问的功能、配置、错误或排障场景。
- 正文包含能够支持相关性判断的章节或事实。
- 文章之间形成必要的概念、操作、限制或排障补充。

不要只使用“可能相关”或“看起来相关”作为召回原因。

## 返回约定

- 有可靠文章时，返回能够覆盖问题的最少文章集；每篇包含标题、链接、所属组件、召回原因和 Markdown 正文。
- 问题不明确时，返回需要用户补充的一个最关键信息点。
- 没有可靠文章时，返回 `not_found`，不要编造文档或链接。

```markdown
# 文档召回结果

## 查询理解

- 用户意图：...
- 候选组件：...

## 召回文章

### 1. [文章标题](文章 URL)

- 所属组件：...
- 召回原因：...

#### 正文

<Markdown 正文>
```
