---
name: labelgpt-cli
description: LabelGPT CLI 助手：处理认证、配置、Space、命令发现与 schema 查询，并将业务/系统 Plugin、Agent、Agent Harness Managed Agent、Dataset、Model 与 ByteCloud Metrics 的创建、查询、编辑、调试、运行、导入导出、发布和监控分析需求转换为可执行命令。用户提到 bytedcli labelgpt、LabelGPT CLI、Space、空间申请、业务或系统插件、Agent 工作流、Agent 任务、Managed Agent、Agent Harness、Dataset、Model、Metrics、监控指标、登录配置、命令参数、输出字段、schema 或 AI Agent 结构化调用时使用。LabelGPT 团队出品。
---

# LabelGPT CLI

把用户的 LabelGPT CLI 操作目标转换成可直接执行的 `bytedcli labelgpt` 命令，或解释命令、参数、输出字段与约束。覆盖安装、认证、配置、Space、命令发现、schema、业务/系统 Plugin、Agent、Agent Harness Managed Agent、Dataset、Model 和 ByteCloud Metrics。

## 启动前自检

当用户需要你执行、验证或生成以本机执行为目标的 `bytedcli labelgpt` 命令时，先完成本节流程。用户只问概念或只要命令示例时，把本节作为前置建议简短给出。

> 本自检**每个会话只做一次**。完成后视为已登录且已了解是否需要目标 Space；后续无论进入哪个子场景（plugin / agent / dataset 等）都不要再重复执行 `bytedcli labelgpt config show`，也不要重复引导登录。只有在实际命令返回 `auth` 类错误时，才重新执行 `bytedcli labelgpt auth login`。目标命令/mode 的 schema 标记 `space-id` 为必填、或用户指定目标 Space 时，在业务命令上显式追加 `--space-id <SPACE_ID>`，不要切换默认 Space。子场景文档不再各自内置这些预检步骤。

1. 运行时由 bytedcli 自动管理：直接执行 `bytedcli labelgpt version` 验证；首次运行时 bytedcli 会自动安装兼容运行时，无需手动下载或安装，也不要引导用户执行任何独立安装脚本。

2. 检查当前配置：

```bash
bytedcli labelgpt config show
```

3. 如本会话尚未完成登录，先检查登录状态；`logged_in=true` 时复用现有登录态，不要重复
   执行登录。只有未登录、登录态无效或业务命令实际返回 auth 类错误时，才登录：

```bash
bytedcli labelgpt auth status --format raw
bytedcli labelgpt auth login
```

未设置 `LABELGPT_SERVER_TOKEN` 且进入交互流程时，`auth login` 是同步阻塞命令：输出登录
挑战后会继续等待用户授权，登录成功前不会返回。Agent 执行时，必须在命令仍运行、首次拿到
挑战信息后，立即把终端二维码（或 `qr_image_path`）和完整登录链接展示给用户，再继续等待原
命令完成；不能等命令退出后才汇总，也不能只提示“扫码登录”或只展示其中一个。
如果 `LABELGPT_SERVER_TOKEN` trim 后非空，`auth login` 是非交互命令，会跳过 JWT/SSO 并
强制换票一次；此时没有二维码或登录链接。

Agent/脚本场景建议所有业务命令显式加 `--format raw`，以便稳定解析 JSON。

## Skill 同步

- 运行时由 bytedcli 在首次运行时自动准备，无需手动安装或下载任何二进制。
- 同步 Skill 基础包使用 `bytedcli self skill update -s bytedance-labelgpt`；需要强制刷新时加 `--force`。
- skill 同步失败时，按 bytedcli 命令输出的恢复提示处理。

## 通用规则

### 大前提

如果执行过程中出现本 Skill 没有定义的步骤、方向、参数语义或分支选择，先停止并向用户询问；不要自行补流程、猜测方向或选择替代方案。

### 先补齐最少信息

只询问当前缺失且无法从上下文确定的信息：

- 通用：只有目标命令或 mode 的 `schema` 标记 `space-id` 为必填、或用户明确指定目标 Space 时，才询问/配置目标 Space。按 ID、UUID、process ID、task ID 定位的读类或执行类命令不要额外要求 Space。
- `space list`：无需目标 Space；用于发现已加入和可申请空间。
- `space get`：目标 Space ID；使用命令级 `--id`，不要求全局 `--space-id`。
- `space apply`：目标 Space ID、`member|admin` 角色和至少一个审批人邮箱；目标使用命令级 `--id`，不使用全局 `--space-id`。申请提交成功后，提示用户前往飞书“审批中心”查看自己发起的空间申请。
- `plugin init`：插件名称、插件类型（业务 / 系统）、运行语言。
- `plugin view/pull/push/deploy/publish`：Plugin ID。
- `plugin debug`：Plugin ID、调试输入内容或输入文件。按平台流程，debug 前先确认本轮
  代码和参数配置已成功执行 `plugin deploy --id <PLUGIN_ID>`；CLI 不会在 debug 前单独
  证明线上已处于最新部署状态，代码或参数配置变化后由 Agent 负责重新 push/deploy。
- `node list`：在 Agent ID（`--agent-id`）与全局目录（`--global`）中二选一，不使用通用 `--id`；可按文本、Node ID、Plugin ID 和分类组合过滤。
- `node execute`：从 `node list --agent-id` 取得的 Service Node ID，以及可选输入；不要使用 Plugin ID
  或 Agent 工作流节点实例 ID/key。
- `agent view`：Agent ID。
- `agent version list`：Agent ID；按 newest-first 查看历史版本。
- `agent version view`：Agent ID、由版本列表返回的精确 Version ID；仅在需要完整工作流图时补 `--file`。
- `agent schema`：Agent ID；只想看某个已发布版本时再补 `--version-id`。查看 Agent 的输入与输出字段契约。
- `agent managed create`：名称；按需补 runtime、模型、instructions 和 Skill/MCP/Hook 引用。目标 Space 由当前命令的 `--space-id` 指定。
- `agent managed update/view/run`：Managed Agent PlanId；运行时还需普通文本 prompt 或 prompt 文件。更新资源列表时明确是完整替换，清空使用对应 `--clear-*`。
- `agent managed skills/mcps/hooks`：无需资源 ID；按需补关键词、分组或 scope 过滤。
- `agent copy`：源 Agent ID；复制 Agent 广场 Agent 时补 `--type 1`。
- `agent debug`：Agent ID、调试输入内容或输入文件。
- `agent workflow pull`：Agent ID、草稿文件路径。
- `agent workflow add-node`：草稿文件路径、服务节点 ID；如需固定节点标识，再补节点 key。
- `agent workflow update-node/remove-node`：草稿文件路径、节点 key；更新时再补要修改的字段。
- `agent workflow add-edge/remove-edge`：草稿文件路径、起点节点 key、终点节点 key；分支连线再补 source/target handle。
- `agent workflow set-model`：草稿文件路径、节点 key、模型 ID。命令组不能直接执行，只使用统一模型节点 `117` 的四个 typed 叶子：`set-model llm|multimodal|image-gen|video-gen`。
  每个叶子必需 `--file --node-key --model-id`；可选且互斥 `--model-config-json` / `--model-config-file`。JSON 根对象直接表示前端 `ModelParamConfig` 局部覆盖；`--model-id` 是主模型唯一 ID，`modelConfigs` 省略时保留备用链、显式提供时替换完整主备链、空数组清空备用。动态 schema 只为主模型从 `/labelgpt/medivh/GetModelConfigInfo` 获取，secret 不得写入可见输出。
- `agent workflow set-sub-agent`：草稿文件路径、节点 key、线上子 Agent ID；不传版本时自动选择该 Agent 的线上/Used 版本并同步输入输出字段，只有只想改配置时才加 `--no-sync-io`。
- typed 节点：草稿文件路径、节点 key，以及该类型所需配置（loop 模式、文本处理模式、HTTP 地址与方法、selector 分支、代码语言与代码内容、固定回复等）。
- loop 子流程编辑：草稿文件路径、loop 节点 key，以及要添加、删除或连接的子节点信息。
- `agent workflow validate/commit`：CLI 草稿文件路径。CLI 搭建工作流时使用 `pull` → 原子编辑 → `validate` → `commit`，完成后不要再执行 `save`。
- `agent workflow save`：外部已有的工作流图 JSON 和 Agent ID；这是与 CLI draft `commit` 互斥的独立保存入口。`--agent-id` 与 `--graph-file` 必填；图文件必须在顶层直接包含 `nodes` / `edges`，不接受 `NodeGraph` 包装格式。`Nodes` 由 CLI 依据图计算，不应把 CLI draft 传给该命令。命令只改动 `Nodes` 和 `NodeGraph`，原样保留该 Agent 现有的其它元数据（名称、描述、Owner、公开状态、限流等）。
- `agent task --send`：Agent ID、请求参数；指定 UUID 时再补 UUID。
- `agent task --status`：一个或多个 UUID。
- `agent task --stop`：一个 UUID；停止该排队中或运行中的任务。
- `agent task --detail`：一个 UUID，或 Dataset ID + Dataset Data ID；Agent ID 和任务状态可选用于收窄。
- `agent monitor overview/tasks/health/runs/summary`：正整数 Agent ID；`health/summary` 的时间范围必须成对提供。
- `agent monitor item`：正整数 Agent ID 和 Data Item ID；Process ID 可选，默认为 0。
- `agent monitor` 不支持按 Agent 名称定位。只有名称时，先在目标 Space 用 `agent list --all-pages` 获取完整列表并按完整名称匹配精确 Agent ID；如果重名，先请用户确认。
- `agent task --detail` 与 `agent monitor item` 不等价：前者查看 AgentData 状态、重试次数和 LogID，不返回节点输入输出；后者查看指定 Data Item 的全部节点记录。按 UUID 查看节点输入输出时使用 `agent monitor runs --id <AGENT_ID> --uuid <UUID> --node-detail full`。
- `dataset init`：数据集名称和敏感级别 `1|2|3|4`；所有站点必填且无默认值。
- `dataset update`：Dataset ID，以及至少一个名称、标签、备注、保留周期或敏感级别修改项；不支持修改 Owner。
- `dataset items`：Dataset ID；需要筛选或指定返回字段时再补对应值。
- `dataset import`：Dataset ID、导入来源；文件导入补本地文件，HDFS 补路径和文件类型，Hive 补表名和 SQL，Aeolus 补 Dataset/Client/Secret/SQL，飞书补表格链接。
- `dataset export`：Dataset ID、导出目标；HDFS 补路径和文件类型，Hive 补表名，导出到其他数据集补目标 Dataset ID；需要行筛选时补统一 filter flags 或 version 1 `--filter-file`。
- `dataset status`：一个或多个 Process ID，或一个或多个 Task ID。
- `dataset stop`：一个 `dataset run` 返回的 Task ID；终止整个 Dataset Agent 批量任务。
- `dataset run`：Dataset ID、Agent ID；只想校验数据集列名与 Agent 输入绑定而不提交任务时补 `--dry-run`。
- `metrics search`：指标名前缀；不知道完整指标名时先搜索。
- `metrics field-list/tagk-list`：完整指标名。
- `metrics tagv-list`：完整指标名和至少一个 tag key；需要缩小候选值时再加 `--filter key=value`。
- `metrics query`：Metrics 面板 DSL，以及 Unix 秒 `--start-time/--end-time`；陌生指标先按 search、field、tag key/value 顺序探索。
- 查询 LabelGPT 核心服务指标时，读取
  [LabelGPT 服务指标分析模板](references/metrics/labelgpt-core.md)，先查通用服务健康，再按服务补业务指标。
  文档中的 PSM 与指标名均为占位符，必须先执行 `metrics search` 并替换为当前环境确认后的值，
  不得猜造业务指标名。
- `config set`：配置项名称、配置值。

### 工作流最终输出

- start 节点只用于标记 DAG 入口和连接首个业务节点，本身没有业务或数据语义；不要为它配置、复制或推导输入输出，`InputFields` 和 `OutputFields` 必须为空，`workflow validate` 和 `workflow commit` 都会拒绝携带输入或输出的 start 节点。不要把 start 当作工作流输入来源或最终输出；工作流真实输入直接绑定到首个业务节点。
- 工作流不要求添加“指定输出”节点；有输出字段的末端/叶子节点可直接作为最终输出。
- 不要只为结束 DAG 添加 `output` node。代码节点位于末端时，其 `result` 可直接返回。
- `add-output-node` 是可选的固定回复节点，仅在需要固定回复、模板包装或显式输出转换时使用，并像普通业务节点一样绑定输入、连接前驱 edge。
- 从 `pull` 草稿或详情 JSON 读取输入时，以原始 `InputFields[].Source` 数字枚举为准：`Source=1 -> dataset`、`Source=2 -> reference`、`Source=3 -> custom`、`Source=4 -> knowledge`、`Source=5 -> file`。尤其是 `Source=1` 配合裸 `ValueKey`（如 `response`）表示数据集/工作流输入列，不是按 alias 引用上游节点；只有 `Source=2` 才是上游输出引用，CLI 会将 alias 规范为 `$.alias`。迁移或重建节点时不得根据 `ValueKey` 是否带 `$.`、是否与某个输出 alias 同名来猜测 source。
- 每个输出字段都必须有非空 alias；alias 可以和字段 key 同名。普通产出节点之间的 alias 必须全工作流唯一；`ModelId=57` 结束节点的 `OutputFields` 是 final-field 投影，可以复用上游 alias，不视为重复产出。新增或同步普通节点后，如发现输出 alias 为空或与其它普通节点重复，必须重新声明该节点的完整输出字段列表：先读取现有 `OutputFields`，再用多个 `add-node/update-node --output '{"key":"<KEY>","alias":"<ALIAS>"}'` 把所有需要保留的输出逐个传入；`--output` 会替换整个输出列表，不是局部 patch。若普通产出 alias 改名，还要同步更新下游 `source=reference` 和结束节点 final-field 投影。
- 模型节点只按统一节点 `117` 的当前契约操作；不要推导、配置或迁移未在当前 `commands/schema` 中暴露的旧模型节点协议。
- typed `set-model` 的类型与能力判定以节点 `117` 四类合并 catalog 为准，不要用 `model list --model-type <单类型>` 的字段判断备用兼容性。`AbilityList` 含 `mcp` 且账号 `SupportFunctionCall=true` 时才允许 `RuntimeMode=mcp`。详见 [Model](references/commands/model.md) 与 [统一模型节点](references/domain/unified-model-node.md)。
- 模型节点存在 `userPrompt` 之外的辅助输入时，必须明确说明它如何进入 Prompt。`InputFields` 只完成取值绑定，输入字段不会自动进入 Prompt；未被 Prompt 引用的字段不会自动进入模型消息。
- 文本与多模态输入通过 Prompt 模板消费；占位符必须写成与输入字段 `Key` 大小写完全一致的 `{{field}}`。多模态输入的 key 或 type 修改完成后，最后再执行一次 `set-model multimodal`，使模型输入映射按最终 I/O 重建。生成类参考图不套用这条媒体消息规则。完整类型、模板与操作顺序见 [Model 的 Prompt 模板与输入字段](references/commands/model.md#prompt-模板与输入字段)。

### 草稿是 CLI 托管状态

`agent workflow` 草稿由 CLI 管理，不要手工修改后再提交。

- 修改草稿使用 `agent workflow` 的 `add-*`、`update-*`、`remove-*`、`add-edge`、`remove-edge` 和 `loop ...` 命令。
- 可以读取草稿以查找 Agent ID、节点 key 等信息，但不要用 `jq` 或编辑器直接改写草稿。
- 推荐流程：`pull` → CLI 命令编辑 → `validate` → `commit`。
- 如果 `commit` 提示线上工作流已变化，重新 `pull` 后再执行本次编辑。

### 输出规则

- 不带 `-o/--output`：结果写到 stdout。
- 带 `-o/--output <DIR>`：写入 JSON 文件到目录，文件名由命令自动生成。
- 用户显式传 `--format`：严格按用户指定。
- 用户未传 `--format`：有 `-o` 时默认 `raw`，无 `-o` 时默认 `pretty`；也就是 `-o` 默认 raw。
- `raw` 是紧凑 JSON，`json` 是缩进 JSON，`pretty` 是人类可读表格或成功提示。
- 机器调用优先使用 `--format raw`。
- `raw/json` 下 stdout 只输出结构化 JSON；进度、日志、调试信息和错误信息输出到 stderr。

### 契约发现

先用 `commands` 发现真实命令面，再用目标叶子命令的 `schema` 确认输入、输出和约束；不要依赖 Skill 中的静态命令清单猜测当前 CLI：

```bash
bytedcli labelgpt commands --format raw
bytedcli labelgpt schema <command-path> --format raw
```

多模式命令会在 `modes[]` 中分别说明输入、输出和约束。

### 配置与鉴权

本 skill 内所有登录统一使用 `auth login`。

执行交互登录前先查看登录态：

```bash
bytedcli labelgpt auth status --format raw
```

如果 `logged_in=true`，复用当前登录态，不要重复执行 `auth login`；如果 `logged_in=false`
或业务命令实际返回 auth 类错误，再执行登录：

```bash
bytedcli labelgpt auth login
```

未设置 Server Token 时，`auth login` 会同步阻塞等待用户完成授权，不会在输出登录挑战后
立即退出。Agent 必须持续读取该命令的输出，并在命令仍运行时立即转述二维码和登录链接：
终端二维码无法完整转述时，至少展示 `qr_image_path` 或说明二维码已在终端输出；登录链接
必须完整展示，方便用户复制到浏览器完成授权。展示后继续等待同一个命令返回登录结果，
不要等到命令退出后才一次性告知用户。

自动化环境可设置：

```bash
LABELGPT_SERVER_TOKEN=<SERVER_TOKEN> bytedcli labelgpt auth login --format raw
```

`LABELGPT_SERVER_TOKEN` 只从环境变量读取，读取时去除首尾空白，空白值等同未设置。它不会
写入配置文件或输出。该变量存在时，`auth login` 以它为最高优先级，跳过所有 JWT/SSO
来源并强制换票一次；换票失败直接失败，不回退。Server Token 只用于换取个人 token；换票
请求中的 `TenantId` 固定为协议占位字符串 `"1"`，不表示业务 Space；Server Token 换票不发送
业务 `x-space-id`。登录态、个人 sync-token cache 和 session Cookie 均不与业务 Space 绑定；后续业务
命令独立解析目标 Space 并发送 `x-space-id`。默认写入 global store，`--local` 写入 workspace-local。

查看默认凭据仓中的登录态：

```bash
bytedcli labelgpt auth status
```

`auth login` 默认写入全局 auth store，适合多个工作区共享登录态；需要隔离当前工作区时使用：

```bash
bytedcli labelgpt auth login --local
```

在 IDE / Agent 沙箱环境中，如果默认 `auth login` 写全局 auth store 时遇到文件系统拦截、权限不足或无法写入 `~/.labelgpt-cli/`，降级使用 `auth login --local`，把 ByteCloud SDK 的 credential 缓存写入当前工作目录的 `./.labelgpt-cli/`。

业务命令读取认证状态时按 workspace-local -> global 顺序解析。`auth status --format raw/json` 登录成功时会返回 `store`，表示实际命中的 `local` 或 `global`。`auth logout` 默认同时清理 local/global 两处认证状态；只清理当前工作区时使用 `bytedcli labelgpt auth logout --local`。

普通 LabelGPT 命令先复用当前 site 的新鲜 sync-token cache；cache 命中时
不会读取或交换 Server Token/JWT。cache stale 或 miss 时，若 Server Token
存在则用它换票，否则才使用显式 JWT 或 ByteCloud SDK 登录态；Server Token 换票失败不回退。

`auth status` 只观察状态，不换票：先按当前 site 查 fresh cache，miss 后再检查
ByteCloud SDK 登录态。顶层保持 `logged_in/site/store/user_info`；cache 命中时 `user_info` 只含
`email/user_id/open_id`，SDK fallback 保持原有用户信息结构。未登录时省略可选字段。临时 JWT
本身不会显示为 `logged_in=true`。

`auth logout` 只清理选定范围的 CLI cache 与 SDK 状态，不会 unset 或修改调用进程中的
`LABELGPT_SERVER_TOKEN`、JWT 等环境变量。若 Server Token 仍存在，后续普通命令可重新换票。

未设置 `LABELGPT_SERVER_TOKEN` 时，如果执行 `auth login` 的环境中
`AIME_USER_CLOUD_JWT` trim 后非空，所有 resolved site 都先尝试
用它跳过二维码/浏览器交互，直接换取个人凭据并写入对应 auth store；如果换票失败，
继续原有的 site-aware 登录。resolved site 为 `cn`（包括 CN、BOE 和 unknown region 的现有归一结果）时只读取
`MIRA_TOKEN_BYTED_JWT_CN`；resolved site 为 `tt`、`nontt` 或其他非 `cn` 值时只读取
`MIRA_TOKEN_BYTED_JWT`。两个 MIRA 变量之间不做跨 site fallback；本 site 对应变量为空白
时进入交互登录；对应 MIRA JWT 换票失败则直接报错。非交互路径不会输出 `qr_image_ready` 事件。

非交互或脚本场景也可通过 JWT 环境变量直接为业务命令提供认证材料：

```bash
LABELGPT_CLI_BYTED_JWT_TOKEN=<JWT> bytedcli labelgpt plugin list --space-id <SPACE_ID> --format raw
```

配置优先级从高到低：

```text
命令行 flag > 环境变量 > 本地配置 ./.labelgpt-cli/config.yaml > 全局配置 ~/.labelgpt-cli/config.yaml > 默认值
```

常用全局参数：

- `--custom-region`：站点区域，默认 `CN`。
- `--endpoint`：服务地址。
- `--space-id`：目标 Space。
- `--byted-jwt-token`：直接指定 JWT。
- `--ppe-env`：PPE 环境。
- `--format`：`pretty`、`raw`、`json`。
- `-o, --output`：JSON 输出目录。
- `--timeout`：HTTP 请求超时，默认 `30s`。
- `--debug`：开启调试日志。
- `--trace`：打印请求追踪 ID。

环境变量：

- `LABELGPT_SERVER_TOKEN`
- `LABELGPT_CLI_ENDPOINT`
- `LABELGPT_CLI_CUSTOM_REGION`
- `LABELGPT_CLI_SPACE_ID`
- `LABELGPT_CLI_BYTED_JWT_TOKEN`
- `LABELGPT_CLI_PPE_ENV`
- `LABELGPT_CLI_AUTH_SOURCE`

## 命令参考

- [核心命令](references/commands/core.md)：版本、命令发现和 schema。
- [更新](references/commands/update.md)：CLI 与基础 skill 更新。
- [认证](references/commands/auth.md)：登录、状态和登出。
- [配置](references/commands/config.md)：配置写入与查看。
- [Space](references/commands/space.md)：查询已加入/可申请空间与空间详情，并提交成员或管理员权限申请。
- [业务/系统 Plugin](references/commands/plugin.md)：列表、创建、详情、本地文件、部署、调试与发布。
- [Service Node](references/commands/node.md)：按 Agent 或全局目录发现 Service Node，并按 Service Node ID 同步执行业务/系统插件节点。
- [Agent 基础命令](references/commands/agent-basic.md)：列表、创建、复制、详情与调试。
- [Agent 历史版本](references/commands/agent-version.md)：只读列出版本、查看安全摘要与导出完整工作流图。
- [Agent 运行监控](references/commands/agent-monitor.md)：总体指标、任务、节点健康度、运行记录、单数据项与聚合摘要。
- [Managed Agent](references/commands/agent-managed.md)：Agent Harness 资源发现、创建、更新、查看、运行，以及加入普通工作流。
- [Agent 工作流](references/commands/agent-workflow.md)：显式草稿编辑、校验与提交。
- [Agent 任务](references/commands/agent-task.md)：任务提交、UUID 状态与 AgentData 详情。
- [Model](references/commands/model.md)：模型查询和模型节点配置。
- [Metrics](references/commands/metrics.md)：ByteCloud 指标、field、tag 探索与面板 DSL 时序查询。
- [LabelGPT 服务指标分析模板](references/metrics/labelgpt-core.md)：核心服务的健康指标、
  业务指标发现与分析范式；PSM 和指标名使用占位符，执行前必须替换为当前环境确认后的值。
- [Dataset 查询](references/commands/dataset-query.md)：创建、列表和数据条目查询。
- [Dataset 传输](references/commands/dataset-transfer.md)：导入和导出任务提交。
- [Dataset 运行与状态](references/commands/dataset-run-status.md)：运行 Agent、查询 Process/Task 进度。

只读取当前目标对应的参考文件。当前可用叶子命令始终以 `bytedcli labelgpt commands --format raw` 和目标 `schema` 为准。

## 典型场景

按用户目标只读取对应场景文件，不要一次性加载全部参考：

- [Dataset 导入导出与 Agent 运行](references/user_case/dataset_import_export_agent_run.md)：数据集导入、导出、进度轮询，以及关联 Agent 执行 `dataset run`。
- [Agent 工作流创建与上传](references/user_case/agent_workflow_create_upload.md)：创建 Agent，查询节点，构建包含普通/插件/typed/loop 节点的工作流草稿，`commit` 上传并用 `agent debug` 验证运行正常。
- 普通复制 Agent：使用 `bytedcli labelgpt agent copy --id <PLAN_ID> --space-id <SPACE_ID> --format raw`；复制 Agent 广场资源时加 `--type 1`。
- [Agent 工作流重建与修复](references/user_case/agent_workflow_rebuild_copy.md)：仅在用户明确要求 clean rebuild，或存在字段聚合、脏 `ParentNodeKey`、旧保存节点 ID 等异常时，通过原子命令重建。
- [Agent 任务结果与明细](references/user_case/agent_task_result_inspect.md)：提交 UUID 任务、批量获取结果、查看 AgentData 状态，并通过独立 monitor 入口诊断运行。
- [业务/系统 Plugin 生命周期](references/user_case/plugin_biz_system_lifecycle.md)：创建、入口实现、上传、部署、调试和发布。

## 安全边界

- 写操作前确认目标 Space、资源 ID 和目标目录；`space apply` 明确确认命令级 `--id`、角色与审批人。
- `dataset init` 创建空数据集；当前登录用户自动成为 owner，且必须显式传 `--sensitivity-level 1|2|3|4`。
- `dataset update` 只发送显式设置的元信息字段；空 `--tag`/`--remark` 表示清空，`--retention-seconds 0` 表示永久保留，不开放 Owner 修改。
- `metrics` 全部为只读命令，不要求 Space；它只使用 ByteCloud JWT 直连固定的 Metrics
  OpenAPI 端点。不要尝试通过 `--endpoint` 或自定义 URL 改写 Metrics 目标，也不要给
  `Authorization` 手工添加 `Bearer`。设置 `LABELGPT_SERVER_TOKEN` 时必须显式提供
  `--byted-jwt-token` 或 `LABELGPT_CLI_BYTED_JWT_TOKEN`；不得读取 SDK 登录态，缺失时必须在
  联网前停止。
- `dataset items` 是只读分页查询；用 `--field` 控制需要返回的字段。
- `plugin pull` 会创建 `./plugin-<id>/`，目录已存在会失败。
- `plugin init` 和 `plugin pull` 会在插件目录生成本地元数据文件；修改参数时保留该文件。
- `plugin push` 按 `.plugin-ignore` 排除不需要上传的路径。
- `.plugin.yaml` 中的插件输入/输出参数必须向用户确认后再 push。
- 业务插件和系统插件的推荐上线链路是先 deploy，再 debug 或 publish；
  `plugin debug` / `plugin publish` 命令本身不做本地 deployed 状态 gate。
- Agent 执行任何 `plugin debug` 前都要在流程中确认本轮代码和参数配置已成功 deploy。
  若本地文件或参数有变化，先 `plugin push`，再 `plugin deploy`，最后 `plugin debug`。
- `dataset import`、`dataset export` 和 `dataset run` 提交后立即返回任务标识，不等待完成。
- `dataset stop` 和 `agent task --stop` 是不可逆写操作，只用于仍在排队、执行或暂停中的目标。`dataset stop` 只接受 `dataset run` 返回的 Task ID，不停止导入/导出 Process。
- 导入/导出进度使用 `dataset status --process-id`；Dataset Agent 任务进度使用 `dataset status --task-id`。
- 需要等待终态时，由 Agent 循环调用对应的 `dataset status`，直到结果显示完成或失败。
- `dataset export` 的 `--data-item-id`、`--executor-status`、`--process-id`、`--source-type`、
  `--data-tag`、`--data-remark`、`--create-user-id`、`--create-time-start`、
  `--create-time-end` 支持行筛选；列表参数可重复或逗号分隔，`--executor-status` 和
  `--process-id` 为单值字符串，时间为 Unix 毫秒。`--executor-status` 仅接受 `正常` 或 `异常`，
  其他值直接报错并非零退出；尚未运行的数据不写入状态，无法按「未执行」过滤。
- `--filter-file` 只接受严格 version 1 的 `.json`/`.yaml`/`.yml`，支持 `feature_filter`
  的 and/or 条件组、全部 1-23 个完整 operator 名称和
  `sampling: {type: quantity|ratio, value: ...}`；quantity 为正整数，ratio 为 1–100
  的整数，relation 缺省为 `and`。flags 与文件按 AND 组合，`--fields` 只表示导出字段。
  旧 sampling 结构和旧缩写 operator 会被拒绝。Magnus HDFS/Hive 直导可能绕过服务端顶层
  筛选，CLI 发送但不承诺效果。
- `dataset run` 不传数据项 ID 时作用于整个数据集；传入一个或多个数据项 ID 时只处理指定数据。
- `--aeolus-secret` 不会在命令输出中回显；避免在不必要时开启 `--debug`。
- `auth logout` 会清理当前登录状态。
