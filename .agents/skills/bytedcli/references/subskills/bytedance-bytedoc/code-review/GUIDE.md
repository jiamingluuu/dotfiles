# ByteDoc 业务代码 Review 指南

当用户要求审查提交前改动、MR/PR diff、指定文件或代码片段中的 ByteDoc / MongoDB 用法时，使用本指南。coding agent 负责理解代码和通用缺陷判断；本 Skill 的重点是发现业务查询后，主动确认目标并通过 bytedcli 获取真实线上元数据，将代码中的查询与当前库状态结合审查。

开始前加载 [`RULES.md`](RULES.md)。规则 ID、语言适配、误报边界和 timeout 分层均以该文件为准。

## 与宿主 Review 的关系

- 如果仓库或会话已有宿主 review skill，例如仓库自己的 review 流程或 `bits-code-guard`，由宿主负责 diff 获取、通用代码审查、严重度和最终输出。本指南只补充 ByteDoc 专项 findings。
- 保留宿主的输出格式、文件行号约定和严重度口径；把 `BDCR-*` 规则 ID 放入对应 finding，不另起一份互相冲突的报告。
- ByteDoc 专项不得压掉、降级或遗漏宿主已经发现的通用 findings。连接泄漏、并发、错误处理等问题可以同时属于通用规则和 ByteDoc 规则，合并说明但保留完整风险。
- 没有宿主 review skill 时，本指南可以独立完成 review，并使用下文的兜底输出格式。

## Review 范围

- 覆盖 ByteDoc SDK/driver 依赖、client/连接池/session/cursor 的 owner 与释放、timeout/maxTime、查询 shape、cursor 结果完整性、索引匹配、业务 DML、索引/DDL、凭证和日志。
- Go、Python、Node.js、Java、C++ 同等严格。语言差异只影响依赖识别和 API 形态，不降低检查能力。
- 默认审查用户指定范围；若用户说“提交前改动”但未提供 diff，由 Agent 按下面的协议组成完整增量。
- 只输出可能导致慢查、连接风暴、权限/凭证问题、误写、结构变更事故或明确稳定性风险的 findings。默认不输出格式和命名偏好。
- 不自动修改业务代码，不自动创建索引、提交工单或写线上数据。用户要求治理或执行时再切换到对应 ByteDoc guide。

## 增量组成协议

宿主已经提供完整 diff 时直接使用宿主范围，不重复收集。独立 review 本地工作区时：

1. 用 `git status --porcelain=v1 --untracked-files=all` 识别 staged、unstaged、rename/delete 和 untracked 文件。
2. 用 `git diff --cached --no-ext-diff --unified=80` 读取 staged diff。
3. 用 `git diff --no-ext-diff --unified=80` 读取 unstaged diff。
4. 对 untracked 文件按状态列表直接读取文件内容。不要执行 `git add -N`、`git add` 或其它会改变用户 index/worktree 的命令。
5. 审查分支或 MR 时，先从用户、MR 元数据或仓库配置确认目标分支，再用 `git merge-base HEAD <target>` 计算 committed diff；不要默认目标一定是 `master`。仍需把本地 staged、unstaged、untracked 改动纳入并去重。
6. 依赖清单和锁文件是识别 ByteDoc 官方 SDK 的证据，不能因为它们不是业务源码就跳过。对生成文件、vendor 和大锁文件只读取与本次依赖变化相关的最小片段。

读取 `git status --porcelain=v1` 时按 XY 两列解释：第一列是 index/staged，第二列是 worktree/unstaged。` M` 表示仅 unstaged，`M ` 表示仅 staged，`MM` 才表示两者都有；`??` 只表示 untracked，不属于 unstaged。untracked 文件不进入 `git diff`，因此即使 status 中存在 `??`，只要 `git diff` 为空就必须记录 `unstaged=false`。若 `git diff --cached` 为空，也不能仅凭被裁掉前导空格的状态文本声称存在 staged 改动。

删除文件也要审查，因为删除共享 client 或 timeout 配置可能引入回归。需要跨文件判断时读取构造入口、依赖清单、DAO 调用方和目标配置的最小必要上下文。不要为确认现有索引搜索 migration、索引声明或全仓文件；diff 自身包含 DDL 时仍按 DDL 规则审查其执行方式。

## Review 流程

1. **确定输入和覆盖范围。** 记录 committed/staged/unstaged/untracked 哪些部分已审查，哪些因权限、体积或缺文件未覆盖。
2. **识别 ByteDoc 代码。** 同时检查 import/header、依赖清单、client/session/cursor 构造、URI/PSM、collection、find/aggregate/update/bulk、Close/Disconnect/EndSession、cursor 遍历与错误传播、index/DDL、timeout 和 retry。
3. **遇到业务查询就确认目标并请求查库。** 从当前代码和必要配置提取 service PSM/dbName、collection 及 site/backend/vregion 线索，列出候选目标和来源，让用户确认或补充缺失信息，同时请求只读元数据授权。不要先搜索仓库索引声明，也不要用声明代替线上状态。简单点查、已有 limit 或仓库有索引文件都不跳过此步骤。
4. **授权后一次取证，按集合复用。** 解析用户确认的目标，获取现有索引、可用的 collection/schema 和版本元数据；同一目标下多个查询合并取证，不逐条重复询问或读取。已有本次 review 中已授权取得、目标一致且完整的线上元数据可直接复用。用户明确要求只做静态 review、拒绝或接口不可用时，完成静态部分并说明线上风险未验证。
5. **结合代码和线上信息判断风险。** 将 filter/sort/range/projection 与真实索引、字段约束和版本一起分析；索引缺失/不匹配必须有线上证据。对资源 owner、错误传播、超时、DML 等代码可证明的问题直接应用 `RULES.md`，无需等待取证才开始分析。
6. **输出结论及后续动作。** 区分已确认问题、依赖数据规模/分布的风险和证据缺口；说明哪些目标已查、哪些未查。确认索引问题后给出候选索引及治理邀请。

`limit` 只限制返回条数，不能证明扫描和排序已有可用索引。线上索引匹配也不等于已证明无慢查：数据分布、扫描量和实际执行计划未知时要说明限制，不把元数据分析包装成已经测得的耗时结论。

## 线上证据授权

默认 review 不访问线上，发现业务查询后立即请求目标确认和只读元数据授权。用户确认同一目标和授权范围后不重复询问。只读不等于低风险：元数据授权不包含样本文档，后者需要单独同意。

### A. 元数据证据授权

用于确认目标库、collection/schema、索引元数据或 ByteDoc 版本/构建元数据，不读取业务文档。出现业务查询即主动询问，无须先证明静态证据不足。schema 仅指接口已有的字段/validator 元数据，不通过抽样业务文档推断。

发现短 MaxTime 时，先核对目标 mongos 构建是否严格早于 `4.0.13-286-4`。该版本及之后已修复，不输出 `BDCR-MAXTIME-001`。版本未知或只知道 `4.0` / `4.0.13` 时，合并请求元数据授权并记录待验证项，不先输出 conditional finding；本次已有完整 mongos 版本证据时直接复用。使用以下边界：

```text
这处查询设置了较短的 MaxTime。相关 mongos 连接池问题仅影响早于 4.0.13-286-4 的构建；当前还没有完整版本证据。是否允许我使用 bytedcli 读取目标 mongos 版本元数据？范围仅限目标服务解析和当前只读接口能返回的版本/构建字段，不读取样本文档、不查慢日志、不做任何写入。版本无法确认时，我会说明未验证，不将它判为该缺陷。
```

发现业务查询后，将目标确认与授权放在同一次询问中：

| 查询位置                           | site       | service PSM / dbName                          | collection | backend / vregion | 来源与待确认项                         |
| ---------------------------------- | ---------- | --------------------------------------------- | ---------- | ----------------- | -------------------------------------- |
| `internal/orders/repository.go:42` | 待用户确认 | `example.bytedoc.demo_orders` / `demo_orders` | `orders`   | 待 resolver 解析  | 来自当前配置，需确认是否为本次部署目标 |

未知值写“待提供”，不要填默认生产库，不显示含凭证的 URI。多个查询按目标合并成一张表。用户已明确给出的目标和授权直接沿用；代码配置中的目标只作为候选。

```text
发现这些 ByteDoc 业务查询。请确认上表是否为本次部署使用的库和集合，并补充缺失的 site、service/dbName 或 collection；是否允许读取这些目标的现有索引、collection/schema 和可用版本元数据，用于判断慢查风险？不会读取业务文档、慢日志或执行写入。backend/vregion 可由 CLI 解析，不需要你重复填写。
```

获得同意后：

1. 先确认 `site`；site 不能从代码猜测。
2. 已有 service PSM 或 dbName 时，使用 `bytedcli --json --site <site> bytedoc get --service "<service>" --no-include-usage` 或 `bytedcli --json --site <site> bytedoc get --db-name "<dbName>" --no-include-usage` 让 resolver 解析 backend/vregion。`--no-include-usage` 避免元数据授权被默认的 usage 查询扩大；`--json`、`--site`、`--vregion` 是全局参数，必须放在 `bytedoc` 前；不要把全局参数追加到 `get` 子命令后。不要要求用户手工补齐 CLI 能唯一解析的字段。
3. 只有 CLI 返回 `BYTEDOC_AMBIGUOUS`、多候选或 `agent_protocol.next_state=ASK_USER` 时，才展示候选让用户选择。
4. 后续命令必须保留已确认的 site/backend/vregion/service/collection；发生 STOP 类错误时遵循父 skill，不切换 backend 试探。
5. 只使用当前已验证只读接口实际返回的版本/构建字段。接口未返回、字段语义不明确或无法映射到受影响版本时，记录 evidence unavailable；不要为补版本证据调用 usage、slow-query、样本文档或任意写接口。

经典版可使用控制面索引命令：

```bash
bytedcli --json --site cn bytedoc get --service "example.bytedoc.demo_orders" --no-include-usage
bytedcli --json --site cn --vregion China-North bytedoc collections --service "example.bytedoc.demo_orders" --backend classic
bytedcli --json --site cn --vregion China-North bytedoc index list --service "example.bytedoc.demo_orders" --backend classic --db-name "demo_orders" --collection "demo_items"
```

Backend 证据边界：

| backend      | 索引证据处理                                                                                                              |
| ------------ | ------------------------------------------------------------------------------------------------------------------------- |
| classic      | 使用 `bytedoc index list`。它是经典版控制面能力；不要用 DMS shell `getIndexes()` 作为 fallback 绕过。                     |
| cloud-native | 不得套用 classic 的 `index list`。只有父 ByteDoc guide、当前 CLI help 或已验证实现明确给出该 backend 的只读路由时才执行。 |
| Volc         | 不得套用 classic 路由。只有父 ByteDoc guide、当前 CLI help 或已验证实现明确给出 DBW 的只读路由时才执行。                  |

cloud-native 和 Volc 都必须使用各自已验证的只读路由；当前上下文无法证明路由时，索引证据不可用，记录 evidence gap。不要切换 backend、site 或 vregion 猜测，也不要把“未查到”写成“不存在索引”。

索引未知只产生 metadata consent 动作或 evidence gap，不产生 finding；不得输出 conditional `BDCR-INDEX-001`。只有经授权取得的线上元数据（包括用户为本次 review 提供的、目标明确且完整的线上快照）证明缺失/不匹配时，才输出 confirmed `BDCR-INDEX-001`。

### 索引治理续接

当经授权的线上证据产生 confirmed `BDCR-INDEX-001` 时，review 不能只停在“建议加索引”：必须给出候选索引及其与 query shape 的匹配理由，并主动询问用户是否进入索引治理。

1. finding 中列出 filter/sort/range 形状、现有索引不匹配的证据、候选 key pattern，以及写放大、重复索引等评估前提。
2. 动作中输出 `offer_index_governance`，并在 `indexProposals` 中给出 `locations`、`collection`、`keyPattern`、`reason` 和 `consentScope: dry-run-only`。
3. 主动询问时要明确：用户同意只授权生成 dry-run 预览，不授权提交工单、执行 DBW 写入或线上创建索引。
4. 用户同意后，先确认 site 和可唯一解析的 selector/backend。classic 加载 `../index-governance/GUIDE.md`；Volc 加载 `../mongo-ops/GUIDE.md`；cloud-native 只在当前 CLI 和父 guide 已验证有对应写入路由时续接，否则说明暂不可执行。
5. 只执行不带 live flag 的 dry-run，向用户展示目标、keys、现有索引冲突、payload/workflow 和影响。然后停止，等待第二次明确确认后才能线上创建。

可以使用下面的询问：

```text
已确认该查询没有可用的匹配索引，候选索引为 <key pattern>，理由是 <reason>。是否允许我进入索引治理流程并先生成 dry-run 预览？此次同意不会提交工单或线上创建索引，预览后仍需你再次确认。
```

只有 `BDCR-QUERY-001`、`BDCR-MAXTIME-001` 或索引仍未知时，不得输出 `offer_index_governance`；先修复查询本身或请求 metadata consent，不把每个慢查风险机械转成建索引。

### B. 样本文档证据授权

只有字段类型/可选性无法从 schema、model、测试和元数据判断，且该证据确实会改变 finding 时才考虑样本文档。即使用户已同意元数据读取，也必须再次单独获得用户同意：

```text
元数据不足以确认字段实际形态。是否允许我额外读取最多 1 条、使用精确 filter 和最小 projection 的样本文档？结果只用于判断字段类型；我会在 review 中隐藏字段值，不扩大查询范围。
```

执行时必须同时满足：

- 使用目标 collection、最小 `--limit`、尽可能精确的 `--filter-json` 和只包含必要字段的 `--projection-json`。除非 `_id` 本身就是必要证据，projection 必须显式包含 `"_id": 0`，因为 MongoDB 默认返回 `_id`。
- 不为了“方便观察”运行无条件全集合查询，不读取 payload、token、个人信息或大字段。
- finding 中只保留字段名、类型、是否缺失等结论；字段值和样本文档内容必须脱敏，不粘贴原始返回。
- 用户拒绝、权限不足或命令失败时继续静态 review，并在证据缺口中说明，不换路径绕过。

### Slow Query 边界

`slow-query` 只在用户明确要求结合慢查、线上慢日志或历史慢查询，或者任务本身就是慢查询治理时使用。不要在普通 code review 中默认查询 slow-query；需要时先加载 `../slow-query/GUIDE.md`，再按其 backend、时间窗和完整性规则执行。

## 关键执行边界

### 业务 DML 与 Agent 写入

- 业务代码中的常规 DML 不要求经过 bytedcli dry-run。review 的对象是 filter、租户/分片边界、影响范围、幂等性、upsert 唯一性、重试、事务、结果检查和错误处理。
- 不要因为业务代码直接调用 `insertOne`、`updateOne` 或 `deleteOne` 就判定“绕过平台确认”，也不要建议线上请求逐次等待人工确认或调用 bytedcli。
- 如果 review 完成后，Agent 要通过 bytedcli 执行真实线上写入，必须停止 code-review 流程，加载 `../mongo-ops/GUIDE.md`，先运行 CLI dry-run、展示 confirmation，再等待用户明确确认。

### 索引与 DDL

- 请求路径、消费者消息处理、循环或高频定时任务内的 `createIndex/createIndexes/ensureIndex/dropIndex/createCollection` 默认作为阻塞风险审查。
- 初始化、迁移和运维脚本中的索引/DDL 不是一律禁止；必须结合一次性执行边界、幂等、并发串行化、审批、回滚和 backend 治理路径判断。
- classic 创建索引转到 `../index-governance/GUIDE.md` 的 BPM dry-run；Volc 创建索引转到 `../mongo-ops/GUIDE.md` 的 DBW 写入确认流程。review 阶段可以询问用户是否续接 dry-run，但不自动执行或把第一次同意视为 live 确认。

## Finding 与输出

严重度遵循宿主 review。独立运行时使用：

- **Blocker**：代码直接证明会造成不可控批量写入、热路径 DDL、凭证泄漏或高概率连接风暴，合入前必须修复。
- **High**：存在明确稳定性、性能或数据完整性风险，或在已确认线上版本、索引、流量证据下会触发事故。
- **Medium**：风险成立但依赖尚未确认的版本、流量或数据分布；应补证据或约束。
- 不输出 Low 风格建议。没有足够证据时请求证据或记录缺口，不制造 finding。

独立输出格式：

```text
Findings:
- [High][BDCR-CONN-001] <文件:行> <一句话问题>
  Evidence: <代码或经授权的元数据证据>
  Risk: <线上影响与触发条件>
  Fix: <具体修复方向>
  Confidence: confirmed/conditional

Index proposals:
- Location: <文件:行>
  Collection: <collection>
  Key pattern: <candidate key pattern>
  Reason: <与 query shape 和现有索引证据的关系>
  Consent scope: dry-run-only

Live evidence:
- Metadata: used/not-used/denied/unavailable
- Sample document: used/not-used/denied/unavailable
- Scope: <site/backend/vregion/service/collection 或 none>
- Missing: <证据缺口或 none>

Coverage:
- Reviewed: <committed/staged/unstaged/untracked/explicit files>
- Not reviewed: <缺失范围或 none>
```

没有问题时说明：

```text
未发现 ByteDoc 相关阻塞项。<说明已覆盖的增量范围>。<说明未做或无法完成的线上证据验证，不把证据缺口写成“已有索引”。>
```

## DO / DON'T

| 场景                      | DO                                                     | DON'T                                                         |
| ------------------------- | ------------------------------------------------------ | ------------------------------------------------------------- |
| 已有宿主 review           | 在同一报告中补充 `BDCR-*` finding                      | 另起报告或遗漏通用 finding                                    |
| 本地提交前 review         | 覆盖 staged、unstaged、untracked 和必要的 branch diff  | 只看 `git diff` 后声称覆盖全部改动                            |
| SDK import 看起来像上游包 | 同时检查依赖清单/lock/BUILD                            | 只凭 import 名下结论                                          |
| client 初始化或共享复用   | 明确 App owner；初始化失败清理，graceful shutdown 关闭 | 初始化失败遗留 client，或在单个请求中关闭共享 client          |
| session/transaction       | 获取后立即建立 EndSession/abort 责任                   | 只处理成功路径，失败或取消后遗留 session                      |
| 手动遍历 cursor           | 立即建立 Close 责任，循环后检查终止错误                | 只 Close 不查 Err，或只查 Err 不 Close                        |
| 返回 cursor/stream        | 用类型/API 明确把 owner、Err 和 Close 一起转交上层     | 仅因创建函数没有 Close 就机械报告泄露                         |
| change stream             | 提供取消信号、Close 和 graceful shutdown               | 因为生命周期长就直接判定泄露                                  |
| 发现业务查询              | 列出目标并请求元数据授权；未取证记录 evidence gap      | 输出 conditional `BDCR-INDEX-001`、直接断言缺索引或自动建索引 |
| 已确认索引缺失或不匹配    | 给出候选索引并询问是否生成 dry-run                     | 只报“可能需要索引”，或根据第一次同意直接 live                 |
| 只有查询边界或超时问题    | 修复 query shape，必要时请求元数据授权                 | 机械生成索引或输出 `offer_index_governance`                   |
| 需要字段样本              | 与元数据分开授权，最小 filter/projection/limit         | 用元数据授权读取任意文档                                      |
| selector 不完整           | 先问 site，再让 resolver 消歧                          | 让用户预先填写可自动解析的 backend/vregion                    |
| 普通 code review          | 业务查询主动请求查库，结合 live 元数据判断             | 默认调用 slow-query                                           |
| 正常业务 UpdateOne        | 检查范围、幂等、重试和结果                             | 要求每次业务请求做 CLI dry-run                                |
| 迁移脚本 DDL              | 结合执行边界和治理流程判断                             | 简化成“业务代码一律禁止 DDL”                                  |
