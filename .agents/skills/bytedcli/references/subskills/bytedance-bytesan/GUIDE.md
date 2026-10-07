---
name: bytedance-bytesan
description: "Use for evidence-backed ByteSan defect analysis whenever the user provides a ByteCloud console URL under /byteq/bytesan, mentions a ByteSan task ID, run ID, bug ID, report ID, or build ID, wants to list ByteSan tasks or scans by repository or PSM, or asks for a ByteSan scan finding's root cause, source-code evidence, remediation, or final analysis document. Fetch ByteSan evidence through bytedcli bytesan, correlate reports with exact Git commits, and produce a structured summary, root-cause analysis, and repair proposal with Git permalinks."
---

# ByteSan 缺陷分析

使用 `bytedcli bytesan` 获取 ByteSan 扫描证据，将原始报告关联到当前仓库或依赖仓库的精确 commit，并产出带 Git 代码链接的根因与修复文档。

执行任何 ByteSan 命令前，先读 [ByteSan 命令接口说明](references/bytesan.md)。该 reference 是命令参数、输出字段、分页、站点与错误处理的单一事实来源。

## 工具

使用以下只读命令收集分析证据。主流程只负责选择工具；具体 command 用法见 `references/bytesan.md`。

| bytedcli 命令                   | 用途                                      |
| ------------------------------- | ----------------------------------------- |
| `bytesan task list`             | 根据用户提供的仓库名筛选任务              |
| `bytesan scan list`             | 根据用户提供的 PSM 或仓库名筛选扫描       |
| `bytesan task-bug list`         | 根据 Task ID 或任务 URL 获取缺陷列表      |
| `bytesan run-bug list`          | 根据 Run ID 或运行 URL 获取缺陷列表       |
| `bytesan bug-build-report list` | 根据 Bug ID 或缺陷 URL 获取 Build、Run 与 Report ID |
| `bytesan report-content get`    | 根据 Report ID 获取缺陷原始报告           |
| `bytesan build-metadata get`    | 根据 Build ID 获取主仓及依赖仓库 Git 信息 |

## 文档内容要求（Rule）

### 1. 证据约束

- 严禁在没有工具输出或代码证据时空想根因。把内容明确区分为“已观察事实”“待验证假设”和“验证后的结论”。
- 每个假设后必须紧跟验证动作与验证结果，使用固定顺序：`假设 → 验证动作 → 验证结果 → 结论`。不能把尚未执行的验证动作写成已经成立的事实。
- ByteSan 数据缺失、Git metadata 缺失、仓库不可访问或 commit 无法读取时，明确记录缺失证据及其影响；不要用经验补齐未知字段。
- 代码分析必须基于 Build metadata 指向的精确 commit。不要用默认分支当前代码替代扫描时的代码，再把差异误判为扫描根因。

### 2. 最终文档结构

最终结论必须使用以下结构：

````markdown
# ByteSan 缺陷分析：<缺陷标识或标题>

## 摘要

- 缺陷概念：<缺陷本身是什么>
- 触发原因：<当前扫描为什么命中>
- 修复摘要：<建议如何修复>
- MR 链接：<已有 MR permalink；没有则写“暂无”>

## 根因分析

### <根因或证据点>

- 已观察事实：<ByteSan 报告或代码事实>
- 假设：<需要验证的解释>
- 验证动作：<实际执行的工具、代码检索、调用链检查或测试>
- 验证结果：<动作返回的结果>
- 结论：<由证据支持的根因>

**Git 代码：** [<repo>@<commit> <path>:<lines>](<固定到 commit 和行号的 permalink>)

```<language>
<与结论直接相关的最小代码片段>
```

## 修复方案

### 修复目标与生产标准

<架构目标，以及适用的 Google 或 Meta 官方生产标准链接>

### 建议代码

<可能的修复代码；每段代码标明修改目标，并附目标现有代码或已有 MR diff 的精确 Git permalink>

### 方案理由

<为什么能消除根因，而不只是绕过扫描规则>

### 影响面

<调用方、兼容性、性能、安全性、依赖仓库和回滚风险>

### 验证计划

<定向测试、回归测试、静态检查和重新扫描方式>
````

- 根因分析中每引入一段代码，都必须先给出固定到仓库、commit、文件和行号的 Git permalink。没有可跳转链接时，不要贴无法追溯的代码片段；改为说明缺少什么访问条件。
- 建议代码尚未提交时，链接到它要修改的现有代码位置；已有 MR 时，优先链接 MR 中的对应代码行。不要伪造一个尚不存在的新代码 permalink。
- 修复目标不能只是“让检测不命中”。结合现有架构说明职责边界、生命周期、并发、所有权、错误处理或资源管理为什么更合理。
- 修复设计必须检查是否存在适用的 Google 或 Meta 官方生产标准，并给出官方一手来源链接。没有直接适用的标准时，明确写明未找到，不得伪造归因或用二手文章代替官方标准。
- 如果用户只要求分析，不要直接修改代码或创建 MR；在“建议代码”中给出最小可实施方案。只有用户明确要求实施时才改代码。

## 处理手段 / 方法（Method）

- Git 代码不属于 ByteSan 数据：使用当前 workspace 的 Git 或代码托管平台只读工具读取 Build metadata 指向的精确 commit，并获取永久链接；无法访问时停止对应代码结论。
- 默认使用 `bytedcli --json`，读取标准 envelope 的 `data` 字段。始终优先使用已经存在、距离目标证据最近的 ID，避免无意义的反向扫描。
- 仓库名和 PSM 由用户直接提供。不要额外查询、猜测或补全候选值。
- 用户提供 ByteCloud 控制台 URL 时，先确认 path 属于 `/byteq/bytesan`，再按 [控制台 URL 识别](references/bytesan.md#控制台-url-识别) 选择命令，完整链接直接传给 `--url`。资源类型由 path 与 query 决定；host 用于推断 site，不能因为域名不同而漏掉 ByteSan 路由。存在 `runId` 时优先识别为 Run，保留完整值，不截断其中的点号。
- `task-bug list`、`run-bug list`、`bug-build-report list` 对 ID 和 URL 输入都返回实际请求站点 `data.site`，作为后续 Task / Run / Bug / Report 查询的区域依据。后续 ID 查询显式传入同一个 `--site`；跨链接收集证据时以 `(site, ID)` 去重，避免不同控制面的同名 ID 混用。Build metadata 仍走共享入口。

1. 用户需要按仓库查找 Task 时调用 `bytesan task list --repo <repo>`；需要按 PSM 或仓库查找 Run ID 时调用 `bytesan scan list --psm <psm> --repo <repo>`。筛选值由用户直接输入；只遍历返回分页，不扩展搜索范围。
2. 已有 Task ID 时调用 `bytesan task-bug list`；已有 Run ID 时调用 `bytesan run-bug list`。如果两者都没有但已有 Bug ID，直接进入步骤 3。若已经有 Report ID 或 Build ID，直接进入对应步骤。
3. 对缺陷列表中的每个唯一 Bug ID，或用户直接给出的 Bug ID，调用 `bytesan bug-build-report list`，获取 Build、Run 与 Report ID。列表有下一页时继续分页，并按 ID 去重。
4. 对每个唯一 Report ID 调用 `bytesan report-content get`，保存返回的完整报告正文。报告接口对非法 JSON 转义 `\x00` 按 byteq-fe 的方式删除后重新解析；兼容范围与失败行为见命令接口说明，不要将这类输出视为逐字节原始 HTTP 响应。
5. 对每个唯一 Build ID 调用 `bytesan build-metadata get`，保存当前仓库及依赖仓库的 Git 地址和 commit。不要因为多个 Bug 关联同一个 Build 而重复请求。

这里的“轮询”表示遍历分页与唯一 ID 集合，不是无限等待异步任务。同一 ID 失败时记录命令、ID 和错误，继续收集其他证据，最终明确报告不完整项。

## 处理流程（Pipeline）

1. 建立证据台账，至少记录 `bug_id → run_id → report_id → build_id → repository → commit` 的对应关系，并保存每个 Report 的原始内容。无法获取 Build metadata 时，只基于原始报告分析，并在结论中声明无法核对扫描 commit。
2. 从原始报告提取代码路径、行号、调用栈、缺陷类型和 sanitizer 信息。用 Build metadata 判断路径属于当前仓库还是依赖仓库，然后读取对应仓库的精确 commit；不要只按同名文件猜仓库。
3. 将报告中的位置与精确 commit 代码、调用方、数据流和生命周期关联。每提出一个根因假设，立即执行代码检索、调用链检查、历史差异检查、测试或静态分析等验证动作，并记录结果。
4. 基于验证后的根因设计修复。优先改善架构与不变量，再给出可能的代码修改、影响面和验证计划；适用时引用 Google 或 Meta 官方生产标准。
5. 按“文档内容要求”输出最终结论。摘要必须能独立回答缺陷是什么、为何触发、如何修复以及是否已有 MR；根因与建议代码必须可通过 Git permalink 追溯。

## 完成前检查

- 所有 ByteSan 结论都有工具输出支撑。
- 所有假设都有紧随其后的验证动作和结果。
- 所有代码片段都有固定到扫描 commit 和行号的 Git permalink。
- Report、Build、仓库与 commit 的映射没有跨控制面或跨构建混用。
- 修复方案处理根因，并说明架构理由、生产标准、影响面与验证计划。
