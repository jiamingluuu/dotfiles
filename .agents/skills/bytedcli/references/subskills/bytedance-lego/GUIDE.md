---
name: bytedance-lego
description: "Operate Lego plugin compile & release via bytedcli. Use when tasks mention Lego, Lego plugin, plugin register/compile, compile version list, release pipeline/scope, release order create/list/get, release step-info, manual confirm, or Lego OpenAPI. Covers plugin register, compile and version lookup, pipeline/scope discovery, order creation and tracking, and pipeline confirm across region-aware sites."
---

# bytedcli Lego 插件编译与发布

通过 bytedcli `lego` 命令注册和编译插件、创建发布工单、跟踪发布进度，并在人工确认或审核节点暂停等待用户处理。

## Phase 0：检查调用条件

先运行 `command -v bytedcli`。如果找不到可执行文件，加载 [../../invocation.md](../../invocation.md)，给出安装或 `npx` 调用方式；不要自行改用 `curl` 或硬编码 OpenAPI。执行具体命令前确认目标 site、region 和认证状态，遇到 `LEGO_AUTH_REQUIRED` 或 `LEGO_INPUT_ERROR` 时按下表加载对应资料。

## Action → 必读资料

只加载当前 action 所需文件。端到端任务按阶段加载，不要一次读取全部 reference。

| Action / 场景                              | 必读资料                                                                                                                      |
| ------------------------------------------ | ----------------------------------------------------------------------------------------------------------------------------- |
| plugin 查询、branch、commit                | [plugin-actions.md](references/plugin-actions.md)                                                                             |
| plugin register                            | [plugin-actions.md](references/plugin-actions.md)                                                                             |
| plugin compile、version、compile-detail    | [plugin-actions.md](references/plugin-actions.md)；判断状态时加读 [statuses-and-errors.md](references/statuses-and-errors.md) |
| 发布信息收集（pipeline / scope / version） | [release-actions.md](references/release-actions.md) + [plugin-actions.md](references/plugin-actions.md)                       |
| order create                               | [release-actions.md](references/release-actions.md)；校验版本时加读 [plugin-actions.md](references/plugin-actions.md)         |
| 发布跟踪（order get / step-info）          | [release-actions.md](references/release-actions.md) + [statuses-and-errors.md](references/statuses-and-errors.md)             |
| pipeline confirm                           | [release-actions.md](references/release-actions.md) + [statuses-and-errors.md](references/statuses-and-errors.md)             |
| 认证、site 或 region 错误                  | [sites-and-auth.md](references/sites-and-auth.md) + [troubleshooting.md](../../troubleshooting.md)                       |
| 通用参数、JSON 输出、安装方式              | [invocation.md](../../invocation.md)                                                                                     |

[references/lego.md](references/lego.md) 仅作为兼容索引，不承载完整命令正文。

## Do not use

- 非 Lego 的发布或部署平台（如 TCE / Goofy）应使用对应 domain skill
- 通用 npm 包发布不属于 Lego 插件发布
- 不要在未预览 dry-run 且未取得显式确认时执行 live 写操作
- 不要循环重试 `pipeline confirm`；它是写操作

## 五条安全不变量

1. `plugin register`、`plugin compile`、`order create`、`pipeline confirm` 分别执行预览和确认。一次确认只授权当前展示的一个请求。
2. 写入前用只读命令验证 plugin、branch、commit、成功版本、pipeline 和 scope。查询不到时报告“不存在”并停止，不替换成相近值。
3. 编译任务必须轮询到所有已返回架构状态都是 `build_ok` / `success`，或任一状态为 `build_failed`；拿到创建响应不代表编译成功。
4. 工单 `PublishReady(4)` 仍需轮询，`PublishFinish(1)` 才表示发布完成；步骤类型 `5` 或 `8` 时暂停自动推进。
5. 状态未知、响应结构不符合预期、认证失败或后端拒绝写入时停止自动化，展示原始状态或结构化错误。

## 用户确认协议

优先使用运行时提供的结构化用户询问工具（例如 `AskUserQuestion`、`request_user_input` 或等价能力）。运行时没有结构化询问工具时，一次性展示候选、请求体或 confirm target、操作风险和可接受回复，提出一个简短问题并结束当前轮，等待用户明确回复。

两种方式都必须遵守：

- 默认不执行 live 写。沉默、超时、模糊回复或先前对其它写操作的确认均不构成授权。
- 普通文本 fallback 必须列出候选关键字段，明确说明“当前未执行”，且只接受针对当前请求的显式确认。
- 参数收集与写入授权分开。参数齐全后仍要先校验和 dry-run，再单独确认当前 live 写。
- 后端错误不等于用户取消；按原错误码和 hint 处理，不能自动追加 `--yes`。

### 一次性收集缺失参数

参数收集按依赖分层：同层独立字段在同一轮列全；依赖后端候选的字段先执行只读查询，再一次性展示候选。不要逐项追问。

| 写操作          | 一次性收集字段                                                                                                                                                                                                                     |
| --------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| plugin register | `--plugin-name`、`--scm-path`、`--plugin-type`、`--owners`、`--parent-id`、`--language`；按任务需要再问 `--category-list`、`--is-adaptive`、`--default-adaptive-run-mode`                                                          |
| plugin compile  | `--plugin-name`、`--version-type`、`--branch` 或 `--commit-hash`；按任务需要再问 `--multi-arch`、`--ipc-only`、`--user-env`                                                                                                        |
| order create    | `--plugin-name`、具体 `--version` 或“最新成功版本”、`--scope-name`、`--pipeline-id`（泳道可空）、`--order-type hot_upgrade`（当前仅接受 `hot_upgrade`，`cold_upgrade` 等其它值会被后端拒绝，用户提出时直接说明不支持而非追问确认） |

### 可选参数展示（写操作 dry-run 前必读）

本节适用于**每个写操作**——`plugin register`、`plugin compile`、`order create` 一视同仁，不因为请求看起来像“编译”“注册”而只当发布场景处理。必填项齐了、dry-run 之前，如果当前写操作还有可选参数没被用户表过态，先把这些可选项一次性列出来（参数名 + 作用 + 不设时的默认），问一句“要不要设，还是全用默认”。别因为必填项给全了、请求看着具体就跳过，也别闷头套默认值直接往下走。

- 只有用户明确填了某可选项的值、或明确说“其余用默认”，才算表过态；表过态的不再问，其余的继续一次性列出，直到全部给值或用户说用默认。

| 写操作          | 需展示的可选参数（缺省 = 不传，走后端默认）                                                                                                                                                                                                          |
| --------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| plugin register | `--category-list`（项目类目）、`--is-adaptive`（标记自适应插件）、`--default-adaptive-run-mode`（默认自适应运行模式 ipc/native）                                                                                                                     |
| plugin compile  | `--multi-arch`（多架构编译）、`--ipc-only`（开启 ipc_only）、`--user-env`（编译环境变量 JSON map）                                                                                                                                                   |
| order create    | `--pipeline-id`（流水线 id，泳道可空）、`--ready-sec`（ready 秒数）、`--surge-percent`（灰度百分比 1-100）、`--enable-go-version-cleanup`（开启 go version 清理）、`--cleanup-pipeline-id`（清理流水线 id）、`--publish-parameters`（发布参数 JSON） |

`pipeline confirm` 无业务可选参数，只有 `--yes`，不适用本节。

依赖候选的处理：

- `branch list` 必须先取得关键词；用户未提供时与其它独立缺参一起询问，不能执行缺少 `--keyword` 的命令。
- `--site` 有全局默认值；只有用户指定其它站点或当前上下文无法确定站点时才询问。多 region site（`cn` / `i18n-bd` / `i18n-tt`）缺少 `--region` 时，必须暂停后续操作并向用户提出实际选择问题，列出该 site 的允许值；不能只在计划中记录“稍后询问”，也不能猜测 region。单 region site（`boe` / `us-ttp` / `eu-ttp`）可省略 `--region`，不要追问用户选 region。
- 具体 branch、commit、version、pipeline、scope 或 order id 不唯一时，展示可区分候选的 id、名称、状态、版本和时间，由用户选择。
- 用户问“最近一次工单”或某工单“进行到哪一步”时，先执行只读 `order list`，再把完整 JSON 交给 `lego_workflow_state.py select --kind latest-order` 按 `create_time` 选择唯一最新工单；取其 order id 后执行 `order get` / `pipeline step-info get`。最新记录唯一时直接查询，不请用户提供 order id 或选择工单；脚本返回 `selected=null` 时展示原因和候选，让用户选择，不能按 order id 或列表顺序决定。
- 用户说“最新版本”时，先执行 `plugin version list`，再把完整 JSON 交给 `lego_workflow_state.py select --kind latest-successful-version`，过滤编译失败或未完成的版本并按 `create_time` 选择最新成功版本，在 order dry-run 中回显具体版本。没有成功版本或脚本返回 `selected=null` 时停止。
- 用户指定具体版本创建工单时，也必须先执行 `plugin version list --plugin-name <name>`，用返回结果精确匹配该版本并确认编译成功。版本不存在或未成功时停止，不执行 `order create`，也不替换为相近版本。
- `全量发布` 是内置 scope，可能不在 `scope list` 结果中；只有用户明确选择后才能使用。
- 用户给出的具体标识仍需后端验证。参数存在不代表资源存在或状态合法。

`pipeline confirm` 的 dry-run 在所有 site 都可执行；CLI live confirm 仅允许 `--site boe`。`cn`、`i18n-bd`、`i18n-tt`、`us-ttp`、`eu-ttp` 只能通过 dry-run 获取 `confirm_target` 和可选 `web_url`，随后让用户在网页处理，不能追加 `--yes` 或重试 live confirm。

## 依赖顺序与并行边界

同一 site、region 和 plugin 已确认后，没有数据依赖的只读发现可并行执行，例如 `plugin version list`、`pipeline list` 和 `scope list`。运行时不支持并行工具调用时可顺序执行，结果语义不变。等待同一候选发现阶段的查询全部结束后再决定下一步；部分查询失败时，展示已取得的成功结果和每个失败项，把候选集标记为不完整并停止写操作，不能丢弃成功结果或用部分结果继续。

以下操作保持依赖顺序：

```text
plugin get
  -> branch/commit 校验
  -> compile dry-run -> 用户确认 -> compile live
  -> compile-detail 轮询到终态
  -> version/pipeline/scope 校验
  -> order dry-run -> 用户确认 -> order live
  -> order get -> step-info
  -> 必要时 confirm 预览 -> 用户确认 -> confirm live
```

所有 live 写操作串行执行并分别确认。只有无副作用、无数据依赖的查询可以并行。

## 确定性状态判定

拿到 `--json` 输出后，优先使用 skill 自带脚本分类编译、工单和步骤状态。脚本路径按当前所在目录解析，不要假设工作目录。
脚本依赖系统 `python3`；如果 `python3` 不存在，直接报告环境缺失并停止，不要改用旧的 `ts-node`/Node 路径。

```bash
python3 <skill-dir>/scripts/lego_workflow_state.py classify --kind compile < compile-detail.json
python3 <skill-dir>/scripts/lego_workflow_state.py classify --kind order < order.json
python3 <skill-dir>/scripts/lego_workflow_state.py classify --kind step < step-info.json
```

脚本接受完整 bytedcli JSON envelope 或直接的 `data` 对象，固定输出：

```json
{
  "state": "pending",
  "terminal": false,
  "requires_human": false,
  "next_action": "poll",
  "reason": "..."
}
```

- `next_action=poll`：等待 10 秒后重新执行对应只读查询。每个编译或工单跟踪阶段最多轮询 60 次且总等待不超过 10 分钟；达到任一上限后停止，返回最后状态、已等待时长和可继续执行的查询命令，不宣称成功或失败。
- `next_action=confirm`：按用户确认协议暂停，不能自动执行 live confirm。
- `next_action=inspect_failure`：停止自动化并展示原始响应；不要根据相似状态名继续。
- `next_action=stop`：停止当前轮询。只有 `state=succeeded` 才能向用户声明成功。

脚本只读取 JSON 并分类，不执行 bytedcli、不联网，也不发起写请求。

## Quick start

```bash
# --site 是全局参数，放在 lego 前；--region 放在 lego 后、资源组前
bytedcli --site cn lego --region online plugin get --name demo_plugin
bytedcli --site cn lego --region online plugin branch list --plugin-name demo_plugin --keyword main
bytedcli --site cn lego --region online plugin compile --plugin-name demo_plugin --version-type offline --branch master
bytedcli --site cn lego --region online plugin compile --plugin-name demo_plugin --version-type offline --branch master --yes
bytedcli --site cn lego --region online plugin compile-detail get --plugin-name demo_plugin --version 1.0.0.1
bytedcli --site cn lego --region online plugin version list --plugin-name demo_plugin
bytedcli --site cn lego --region online pipeline list --plugin-name demo_plugin
bytedcli --site cn lego --region online scope list --plugin-name demo_plugin
bytedcli --site cn lego --region online order create --plugin-name demo_plugin --version 1.0.0.1 --scope-name 全量发布 --order-type hot_upgrade
bytedcli --site cn lego --region online order get --id 12345
bytedcli --site cn lego --region online pipeline step-info get --order-id 12345 --flow-index 0 --step-index 0
bytedcli --site cn lego --region online pipeline confirm --order-id 12345
```

每条写命令在示例中出现 live 形式不代表可以跳过前置校验、dry-run 和当前请求确认。

## 命令树

```text
bytedcli
`- lego  (--region <region>)
   |- plugin
   |  |- get                  (--name)
   |  |- register             (--plugin-name --scm-path --plugin-type --owners --parent-id --language ...)
   |  |- compile              (--plugin-name --version-type {offline|online|test} + branch|commit-hash)
   |  |- version list         (--plugin-name)
   |  |- compile-detail get   (--plugin-name --version)
   |  |- commit list          (--plugin-name)
   |  `- branch list          (--plugin-name --keyword)
   |- pipeline
   |  |- list                 (--plugin-name)
   |  |- confirm              (--order-id [--yes])
   |  `- step-info get        (--order-id --flow-index --step-index)
   |- order
   |  |- create               (--plugin-name --version --scope-name --order-type [--yes])
   |  |- list                 (--plugin-name)
   |  `- get                  (--id)
   `- scope
      `- list                 (--plugin-name)
```

`plugin get` 使用 `--name`；其它 plugin 相关命令使用 `--plugin-name`。完整参数和 JSON 字段按 Action → 必读资料表加载。

## 输出与错误

默认文本输出用于人工阅读；需要提取 id、索引或状态时，把全局 `--json` 放在 `lego` 之前。JSON envelope 为 `{ status, data, error, context }`。枚举含义和停止条件见 [statuses-and-errors.md](references/statuses-and-errors.md)，各 action 的 `data` 字段见对应 action reference。

## References

完整资料索引见上方「Action → 必读资料」表；按当前 action 的「必读资料」列加载，不要一次读取全部 reference。
