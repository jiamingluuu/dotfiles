---
name: deepwiki-skill
description: 搜索基于仓库代码和业务文档生成的 DeepWiki 文档内容。当您需要从代码仓库中定位功能模块/模块组件、查找 API 文档、使用示例或技术知识时，当你需要跨仓库了解公司其它任意基础能力的接口文档或技术实现时，请必须使用此技能。支持知识搜索、带答案的综合搜索和完整文档检索。
---

# DeepWiki 知识搜索

DeepWiki 服务的直接 API 集成，用于从索引仓库中搜索文档和知识，支持跨仓库搜索和公司基建知识搜索。知识内容包括且不限于：

- 功能模块/模块组件的使用方法
- API 文档
- 技术实现示例
- 业务背景知识
- 业务最佳实践
- 公司通用基建
- 开源基础库
- 公司通用文档知识

## 基础能力

### 搜索文档片段

- **功能**：从索引仓库中搜索知识片段，返回相关文档片段。
- **耗时**：~10 秒
- **Token 消耗**：高（> 10K）
- **执行命令**：`bytedcli --json deepwiki search --format snippets --query "..." --repo-name "..." --limit 5 --collection-name "..."`
- **用法：**

```bash
bytedcli --json deepwiki search --format snippets \
  --query "表单验证使用方法" \
  --repo-name "douyinfe/semi-design" \
  --limit 5
```

**参数：**

- `--query`: 搜索查询（必需）
- `--collection-name`: 集合名称（可选，优先级高于 repo-name，如果传了，将根据 collection-name 进行搜索，否则根据 repo-name 进行搜索，一般用于跨仓库知识、基建知识搜索）
- `--repo-name`: 仓库全名（可选，如果没传切 collection-name 也没传，默认自动在 当前 git 仓库获取）
- `--package-name`: 包名（可选，多个包名用逗号分隔，优先级高于 repo-name，如果传了，将根据 package-name 进行搜索，否则根据 repo-name 进行搜索，一般用于跨仓库知识、基建知识搜索）
- `--limit`: 结果数量（可选，默认：10）

**输出：** 包含搜索结果的 JSON 数组，包含 score、rerank_score、content、file_name、doc_id

### 基于文档片段进行快速总结

- **功能**：基于文档片段进行快速总结，返回简洁的知识总和文件定位。
- **Token 消耗**：小
- **耗时**：~30 秒
- **执行命令**：`bytedcli --json deepwiki search --format summary --query "..." --repo-name "..." --limit 5 --collection-name "..."`
- **用法：**

```bash
bytedcli --json deepwiki search --format summary \
  --query "表单验证使用方法" \
  --repo-name "douyinfe/semi-design" \
  --limit 5
```

**参数：**

- `--query`: 搜索查询（必需）
- `--collection-name`: 集合名称（可选，优先级高于 repo-name，如果传了，将根据 collection-name 进行搜索，否则根据 repo-name 进行搜索，一般用于跨仓库知识、基建知识搜索）
- `--package-name`: 包名（可选，多个包名用逗号分隔，优先级高于 repo-name，如果传了，将根据 package-name 进行搜索，否则根据 repo-name 进行搜索，一般用于跨仓库知识、基建知识搜索）
- `--repo-name`: 仓库全名（可选，如果没传切 collection-name 也没传，默认自动在 当前 git 仓库获取）
- `--limit`: 结果数量（可选，默认：10）

**输出：** 包含 answer 和 file_paths 的 JSON


### 基于文档片段进行深度分析和源码定位并总结

- **功能**：基于文档片段进行深度分析和源码定位，并总结，返回详细的知识总结和文件定位。
- **耗时**：~75 秒
- **Token 消耗**：小
- **执行命令**：`bytedcli --json deepwiki analyze --query "..." --repo-name "..." --branch "main"`
- **用法：**

```bash
bytedcli --json deepwiki analyze \
  --query "表单验证架构" \
  --repo-name "ies/sdma-deepwiki"
```

**参数：**

- `--query`: 搜索查询（必需）
- `--repo-url`: Git 克隆 URL（非必需，如果不传，默认会自动在 当前 git 仓库获取）
- `--repo-name`: 仓库全名（非必需，如果不传，默认会自动在 当前 git 仓库获取）
- `--creator`: 有仓库访问权限的用户邮箱前缀（非必需，如果不传，默认会自动在 当前 git 配置获取）
- `--branch`: 分支名称（可选，默认为 main）

**输出：** 包含 answer 和 file_paths 的 JSON

### 注意事项
- [非常重要] 以上三种能力，基于对性能、准确率、成本的综合考虑，选择合适的能力进行使用。
- [非常重要] `deepwiki search`（`--format summary` 与 `--format snippets`）本身没有做源码定位，会存在实效性等问题，获取到 `file_paths` 以后**必须**在本地进行源码定位再给出结论。
- [非常重要] `deepwiki analyze` 需要提供 `--repo-url`，所以一般只能用于当前工作目录下的仓库搜索。
- [非常重要] `deepwiki analyze` 耗时较长，**必须**设置至少 3 分钟的超时时间

### 其余可用命令

### 1. `deepwiki get-collection`

获取仓库或包的集合名称，这里的包是指 package.json 中的 name 字段，例如 "@douyinfe/semi-ui"，或者用户代码中引入时的包名，例如 "react"。

**用法：**

```bash
# 通过仓库名
bytedcli --json deepwiki get-collection --repo-name "douyinfe/semi-design"

# 通过包名
bytedcli --json deepwiki get-collection --package-name "@douyinfe/semi-ui"
```

**参数：**

- `--repo-name`: 仓库全名（与 package-name 二选一）
- `--package-name`: 包名如 "@scope/package"（与 repo-name 二选一）
- `--query`: 可选查询上下文

**输出：** 集合名称字符串

### 2. `deepwiki get-content`

通过 doc_id 获取完整文档内容（必须在搜索后调用），当分片内容不完整缺少关键信息时，需要调用此命令获取完整内容。

**用法：**

```bash
bytedcli --json deepwiki get-content \
  --doc-id "_sys_auto_gen_doc_id-xxx" \
  --repo-name "douyinfe/semi-design"
```

**参数：**

- `--doc-id`: 搜索结果中的文档 ID（必需）
- `--repo-name`: 仓库全名（可选，与 collection-name 二选一）
- `--collection-name`: 集合名称（可选，与 repo-name 二选一）

**输出：** 完整文档内容文本

## 工作流策略

### 搜索本仓库知识

### 搜索跨仓库/公司基建知识

#### 仓库映射配置

插件提供了常用仓库的预配置映射（`../../common/repo-config.json`），包含 `collection-name` 和 `repo-name`：

| 项目            | collection-name      | 描述                      |
| --------------- | -------------------- | ------------------------- |
| **pia**         | pia_pia              | 渐进式即时应用框架        |
| **edenx**       | webinfra_edenx       | 基于 Modern.js 的全栈框架 |
| **gulux**       | nodejs_gulux         | 次世代 Node.js 框架       |
| **garfish**     | pgcfe_garfish        | 微前端平台                |
| **semi-design** | DouyinFE_semi_design | 现代设计系统和 UI 库      |
| **@byted/hooks** | `toutiao_fe_hooks` | @byted/hooks，基础 React Hooks 库相关知识 |
| **gulux** | `nodejs_gulux` | gulux（Node.js 服务框架） 相关知识 |
| **noah** | `ife_noah` | noah （中后台基础库）相关知识，包括 @webcast/standard-components 组件库 |
| **@safe-fe/ui** | `ies_safe_devlib` | @safe-fe/ui、@safe-fe/admin-ui 组件库相关知识 |
| **pace** | `ies_pace` | pace（PC 端 SSR 渲染框架）相关知识 |
| **emo** | `web_solutions_emo` | emo (Monorepo 管理工具)相关知识 |
| **ace** | `ife_dayu` | ace 基础库相关知识，相关关键词包括 `@byted-ace/form`、`@byted-ace/request`、`@byted-ace/hook`、`@byted-ace/utils`、`@byted-ace/flow`、`AceSemiV2Form`、`AceSemiForm` |
| **ufra** | `ies_ufra` | ufra C 端流程管理工具相关知识，相关关键词包括 `@ufra/*`、`ufra.meta.json` |
| **lynx** | `lynx` | Lynx 相关知识，Lynx 是公司内构件高性能跨平台应用的技术栈，它有独立的样式体系和原生组件，不能把它理解为常规的 web 应用，相关关键词 ReactLynx、TTML、Lepus、rspeedy、lynx-speedy、x-element ..；遇到这类知识尽量先查询，再根据查询结果进行分析 |
| **hybrid** | `hybrid` | 字节内部跨端容器（AnnieX）以及资源发布平台（Gecko/GFC）相关知识，相关关键词 AnnieX、Gecko、HybridMonitor、Forest、GFC、Bullet、HybridContainer、Native Preload、Native Prefetch、Latch、JSB、JSBridge；遇到这类知识尽量先查询，再根据查询结果进行分析 |
| **slardar hybrid 监控** | `hybrid_performance` | 字节跨端监控平台 Slardar Hybrid 相关知识，包含性能监控、稳定性监控、报警相关知识，注意只包含跨端页面（端内 H5、Lynx）的监控知识，不包含纯 Web 端的监控知识 |
| **其它开源库** | external |	任意 开源（非公司内）组件库或工具库，如 ahooks、ant-design，query 中必须包含需要搜索哪个包的知识的 NPM 包名
| **公司基础平台**  | internal |	公司内文档的搜索和知识总结，可以搜索作为公司内基建知识获取的兜底

**使用建议（重要）**：

- **创建便捷脚本**：可以创建 shell 脚本读取映射，简化常用项目的搜索
- **扩展映射**：映射可以在 `common/repo-config.json` 中扩展

```bash
# 直接使用 collection_name（推荐）
# Semi Design 搜索示例
bytedcli --json deepwiki search --format snippets \
  --query "Button 组件 API" \
  --collection-name "DouyinFE_semi_design" \
  --limit 5

# Pia 框架搜索示例
bytedcli --json deepwiki search --format snippets \
  --query "路由配置" \
  --collection-name "pia_pia" \
  --limit 5
```

#### 映射未覆盖的项目

```bash
# 步骤 1：获取集合名称（如果需要）
COLLECTION=$(bytedcli --json deepwiki get-collection --repo-name "douyinfe/semi-design")

# 步骤 2：搜索知识
bytedcli --json deepwiki search --format snippets \
  --query "Button 组件 API" \
  --collection-name "$COLLECTION" \
  --limit 5

# 步骤 3：获取完整内容（可选）
bytedcli --json deepwiki get-content \
  --doc-id "<step2的doc_id>" \
  --collection-name "$COLLECTION"
```

### 综合分析

### 内部知识搜索

```bash
# 搜索公司内部知识
bytedcli --json deepwiki search --format snippets \
  --query "React 编码规范" \
  --collection-name "internal" \
  --limit 5
```

## 最佳实践

### 查询优化

- **专注查询**（<3 个特征）： "表单验证使用方法"
- **避免宽泛查询**（>3 个特征）： "带验证和错误和提交的表单"
- **将复杂查询拆分**为多个专注搜索

### 何时使用每个工具

- **`deepwiki search --format snippets`**: 查找文档片段的主要工具
- **`deepwiki analyze`**: 用于带文件路径的综合答案
- **`deepwiki get-collection`**: 在集合名称未知时使用
- **`deepwiki get-content`**: 仅在片段搜索后需要完整文档时使用

### 性能考虑

- **`deepwiki search --format snippets`**: ~10 秒
- **`deepwiki analyze`**: ~75 秒
- **`deepwiki get-collection`**: ~120 秒
- 大多数情况使用 `deepwiki search`；仅在需要综合答案时使用 `deepwiki analyze`

## 示例

### 示例 1：查找组件文档

```bash
# 获取集合名称
COLLECTION=$(bytedcli --json deepwiki get-collection --repo-name "douyinfe/semi-design")

# 搜索 Button 文档
bytedcli --json deepwiki search --format snippets \
  --query "Button 组件属性和事件" \
  --collection-name "$COLLECTION" \
  --limit 5
```

### 示例 2：综合架构理解

```bash
# 完全理解表单验证
bytedcli --json deepwiki analyze \
  --query "表单验证架构和机制" \
  --repo-name "douyinfe/semi-design" \
  --creator "your-email"
```

### 示例 3：业务功能模块定位

```bash
# 定位话题模块
bytedcli --json deepwiki analyze \
  --query "话题模块的位置与功能" \
  --repo-url "https://code.byted.org/ife/entertainment_vs_platform.git" \
  --repo-name "ife/entertainment_vs_platform" \
  --creator "your-email-prefix"
```

### 示例 4：多方面分析

```bash
# 多次调用以完全理解
bytedcli --json deepwiki analyze --query "Monorepo 结构" --repo-url "..." --repo-name "..." --creator "..."
bytedcli --json deepwiki analyze --query "组件模块" --repo-url "..." --repo-name "..." --creator "..."
bytedcli --json deepwiki analyze --query "工具库" --repo-url "..." --repo-name "..." --creator "..."
# 合并结果
```

## 注意事项

- 所有命令在 `--json` 下输出 JSON 到 stdout 以便于解析
- 错误消息输出到 stderr
- 退出代码：0（成功），1（错误）
- 不需要外部 npm 依赖
