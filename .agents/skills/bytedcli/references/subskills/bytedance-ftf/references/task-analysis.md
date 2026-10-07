# FTF 任务级归因 Workflow

## 目录

- [用途](#用途)
- [强制边界](#强制边界)
- [三层结论](#三层结论)
- [执行模型：有界并发](#执行模型有界并发)
- [阻断交互与恢复检查点](#阻断交互与恢复检查点)
- [证据来源与身份门禁](#证据来源与身份门禁)
- [缺陷准入门禁](#缺陷准入门禁)
- [缺陷等级](#缺陷等级)
- [DIFF 根因类型](#diff-根因类型)
- [标准流程](#标准流程)
- [呈现格式](#呈现格式)
- [输出契约](#输出契约)
- [压力场景](#压力场景)
- [完成检查](#完成检查)

## 用途

当用户提供 FTF task URL / task id，并要求任务报告级归因、缺陷列表、DIFF 归因分析或回放失败归因时，使用本流程。它只负责编排既有 FTF 能力和约束，不重复定义底层命令或单条 DIFF 判断逻辑：

- 任务形态与证据边界：`domain-model.md`
- 完整 DIFF 分析顺序：`diff-analysis.md`
- task 聚类覆盖与详情链接：`task-diff-triage.md`
- 随机值和数组乱序降噪：`diff-denoise.md`
- 单条 flow 根因：`flow-diff-root-cause.md`
- 业务代码关联与 canonical Analyzer：`code-diff-correlation.md`
- 查询参数与字段：`diff-query-reference.md`
- 回放失败清单、错误码与下钻：`diag-replay-failure.md`、`enums.md`

本流程使用一个私有结构化报告对象和两个 canonical 展示模板：

- 私有 Schema：[`../assets/schemas/task-analysis.schema.json`](../assets/schemas/task-analysis.schema.json)
- 校验与渲染脚本：[`../scripts/render-task-analysis.mjs`](../scripts/render-task-analysis.mjs)
- Markdown：[`../assets/templates/task-analysis.md`](../assets/templates/task-analysis.md)
- HTML：[`../assets/templates/task-analysis.html`](../assets/templates/task-analysis.html)

取证、聚类、数量对账和缺陷准入完成后，必须先生成符合 Schema 的私有 `TaskAnalysisReport` JSON，再调用 renderer 同时生成 Markdown 和 HTML。JSON 只作为临时中间产物；两个报告必须来自同一份已校验 JSON，不得重复远程取证、Analyzer、根因聚类或手工填充模板。

两个模板共享同一份分析结果和以下语义：

1. **顶部关键指标**：标题下、“总体结论”上方依次展示有效流量、DIFF 流量、缺陷、接口覆盖率和代码覆盖率；有效流量等于总流量减回放失败流量，缺陷数量取已通过准入门禁的缺陷列表长度。
2. **总体结论**：只回答是否发现明确的业务代码缺陷。
3. **问题汇总**：仅在存在通过全部准入门禁的业务代码缺陷时，在“总体结论”后作为独立板块展示。
4. **DIFF 归因分析**：覆盖分析范围内的全部 DIFF。
5. **回放失败归因分析**：覆盖所有 `failed_reason != 0` 的流量。
6. **其他建议项**：按阻断程度输出不超过 3 个具体、可执行且可验收的建议。

业务配置错误只进入 DIFF 归因分析，不进入缺陷列表。FTF 平台自身问题必须在归因结果中如实展示，但严禁写入缺陷列表。

## 强制边界

- 全程默认只读。不得自动重试、停止、废弃、重新解析、标注或修改任务。
- 不把任务状态、平台标注、错误码、单条日志、单个字段差异或代码 diff 单独当成根因。
- 不把 FTF Recorder、Executor、Replayer、Mocker、Assertion、SDK 插桩、回放协议注入、
  报告解析或 FTF 配置问题归入业务缺陷。
- 不把业务 TCC、ACL、白名单、环境数据、部署状态等配置或环境问题归入业务代码缺陷。
- 缺少业务代码因果链时，缺陷列表必须留空；不能为了产出缺陷而升级推断。
- 当前聚类能权威取得 `task_id + similar_diff_id`，且要判断 base→target 代码变更是否导致字段 DIFF 时，代码变更归因必须使用 `code-diff-correlation.md` 的 canonical `ftf-code-analyzer` 路由。Analyzer 未安装、被阻断、结果非法或未返回终态时，不得回退到手工 Codebase/Git 检索并伪造代码变更因果结论。该门禁不阻止同一 commit 下基于任务执行配置、固定版本源码和日志分析实际运行分支，但此类结论必须明确为运行时路径因果。
- 报告中的真实 token、cookie、JWT、authorization、用户信息必须脱敏。
- 任务报告级归因要求完整分类。允许按 method 分批下钻，但不能在仍有未分类 DIFF 时声称
  已完成全量归因。
- “总体结论”板块的“未发现缺陷。”不等于“任务通过”。任务有效性、缺陷结论和发布建议必须分开判断。
- 只有明确归因为业务代码缺陷且通过全部缺陷准入门禁时，“总体结论”板块才写“发现 `<N>` 个缺陷。”，
  并在其后展示独立“问题汇总”板块。否则“总体结论”板块必须只写“未发现缺陷。”，且不得输出“问题汇总”。
- 不得在“总体结论”板块中突出 FTF 平台问题、业务配置问题、稳定性问题或其他警告类问题；这些信息
  只能通过顶部关键指标、DIFF 归因分析、回放失败归因分析和其他建议项表达。

## 三层结论

### 任务有效性

任务有效性只描述本次任务能否支撑质量判断，不描述业务代码是否正确：

| 状态     | 判定                                                                                                       |
| -------- | ---------------------------------------------------------------------------------------------------------- |
| 有效     | 任务已到可消费终态，快照稳定，目标版本身份一致，关键范围已执行，失败与未断言未超过用户或测试计划认可的门槛 |
| 部分有效 | 部分 method / 场景证据可用，但存在明确覆盖损失；只能对已验证范围下结论                                     |
| 无效     | 任务未完成、报告不完整、目标版本错误，或失败/未断言已破坏主要验证范围                                      |
| 无法确认 | 权限、限流、数据缺失或外部系统不可用，无法取得判定任务有效性所需证据                                       |

不得自创统一失败率阈值。优先使用测试计划、流水线或业务明确给出的门槛；没有门槛且覆盖损失
可能影响核心范围时，不得输出“有效”。

### 归因状态

- **完整**：分析范围内全部原始 DIFF 聚类均已归类，关键证据源可用，数量对账通过。
- **部分**：已归类部分聚类或部分证据源失败；必须列出已覆盖范围和未解决证据。
- **失败**：无法建立可靠聚类清单、任务身份或基本 base/replay 证据。

### 发布建议

发布建议使用 `通过 / 有条件通过 / 不通过 / 不可据此判断`：

- **通过**：任务有效、归因完整、无业务代码缺陷，且约定的核心 method / 场景 / 代码覆盖门槛
  已满足。
- **有条件通过**：无业务代码缺陷，剩余项已确认不阻断，并有责任方、验收标准和截止条件。
- **不通过**：存在已通过准入门禁的业务代码缺陷，或明确违反发布门禁。
- **不可据此判断**：任务无效、无法确认、归因失败，或覆盖/预期性证据不足。

## 执行模型：有界并发

并发只优化互不依赖的只读归因，不改变 `快照与身份 → 任务有效性 → 范围确认 → triage → 降噪 → 单条根因 → 代码关联 → 根因合并 → 缺陷准入 → 发布建议` 的依赖顺序。协调者最多启动 20 个后台归因 worker，并把子 Agent 与远程 API 并发分开控制；不得减少样本、跳过聚类或放宽证据门禁。

```text
串行：解析 URL / task id
  └─ 串行：task get 一次，冻结任务快照、身份、统计口径和筛选范围
       └─ 串行：获取完整 cluster inventory，建立不可变 work unit
            └─ 调度：最多 20 个后台归因 worker，每个聚类只有一个 owner
                 ├─ worker：串行消费自己的互斥聚类队列并输出结构化证据包
                 ├─ 协调者：去重 worker 的新增证据请求并按端点限流
                 └─ worker：仅对未被直接证据解释的候选补日志、配置或代码证据
                      └─ 屏障：协调者串行复核证据、合并根因、对账、执行缺陷准入和发布判断
                           └─ 串行：重新读取 task update_time，校验快照未变化
```

并发阶段必须遵守：

- 同一分析快照的任务详情只允许远程查询一次。优先从该响应本地读取 `diff_reason_failed_count` 和 `failed_reason_count`；字段缺失时才调用对应 `reason list`。结束前比较 `update_time` 的轻量一致性复查是唯一例外。
- 不得把 `task evidence get` 与 `task get` 或两次 `reason list` 并发执行。前者会继续查询 task/PSM/method 汇总和聚类样本，只适合小范围快速分析；全量任务先列 cluster inventory，再按缺口下钻。
- 所有 worker 共用协调者冻结的任务上下文、完整聚类清单、筛选口径和只读证据缓存，不得重新查询任务详情或推断任务形态。
- work unit 按 `method + direction + 规范化字段路径 + 差异指纹` 建立。聚类不超过 20 个时一项一 worker；超过时最多 20 个 worker 按证据成本均衡分配互斥队列，并串行处理各自队列。
- 每个聚类必须且只能有一个 owner worker。worker 返回原始聚类数、逐聚类证据、根因候选和未闭环项，不合并跨聚类根因或生成最终报告。
- 每个 owner 必须对自己负责的每个原始 DIFF 逐项完成定位。共享的代码、日志、Trace、配置或部署查询可以复用，但必须明确覆盖到每个成员；未被共享证据覆盖的成员要单独补查，不能因为现象相似就沿用其他成员的调查结果。
- worker 优先消费共享缓存。确需新增远程证据时只提交 selector 和用途，由协调者去重后统一查询；依赖前一步输出的日志查询保持串行。
- 对完全相同的 task、method、cluster、flow 或 log selector 只查询一次，结果缓存并供 worker
  共享；缓存键必须包含 site、task id、筛选条件和任务 `update_time`。
- 子 Agent 最多并发 20 个，但远程请求总并发仍不超过 4，method report 等易限流端点默认不超过 2。收到 429 时按服务端提示退避并降低该端点并发，不影响其他只读证据源。
- 相同错误签名可用于候选预分组和复用日志，但合并前仍须确认每个成员的责任组件、触发条件、失败机制和解决方案相同。
- 并发请求出现 429、超时或部分失败时，只重试失败的只读分支并降低并发；不得重跑成功分支，
  不得把查询失败解释成业务异常。
- 每个候选根因先取代表样本和反例样本，再根据样本是否同质自适应扩大；不能把固定 3 条样本
  当作充分性标准，也不要求同根因的每个聚类重复查询完整日志。
- 子 Agent 或 worker 输出只是线索。协调者必须复核关键原始字段、代表链接和代码证据后，
  才能确定根因类型、缺陷等级和最终结论。

最终串行对账必须同时满足：

```text
已归类原始 DIFF 聚类数 + 未闭环原始 DIFF 聚类数 = 分析范围内原始 DIFF 聚类总数
每个原始 DIFF 聚类只出现一次
已归类回放失败流量数 + 未闭环回放失败流量数 = failed_reason != 0 的流量总数
每条回放失败流量只出现一次
每个缺陷至少关联一个根因聚类
每个缺陷的代码相关性 = strong
任务结束时的 update_time = 分析快照中的 update_time
```

DIFF 与回放失败必须分别完成数量对账，不能把回放失败数计入 DIFF 流量或原始 DIFF 聚类数。

不能安全并发的环节：

- URL 解析与任务形态判定：后续查询依赖其 selector 和语义。
- 同一聚类内依赖 selector / replay logid 的链式查询。
- 跨 method 根因合并：需要识别同根因和重复证据。
- 数量对账、类型裁决、缺陷准入和等级判定：必须由主分析者统一执行。

## 阻断交互与恢复检查点

缺少必要信息或权限只暂停依赖该证据的分支，不代表整单归因失败或结束。证据未补齐时仍须保持
`evidence_blocked`，暂停最终报告渲染；暂停最终报告渲染不等于终止整个归因流程。

1. 保留已完成的只读取证结果和冻结检查点：`task_id`、站点、task `update_time`、筛选范围、已完成分支、
   受阻分支、真实获取尝试、脱敏后的具体阻塞及唯一恢复动作。不得要求用户重复提供已经冻结的任务 URL
   或信息。
2. 优先使用运行时提供的结构化用户交互能力（如 `AskUserQuestion`、`request_user_input` 或等价能力）；
   没有时提出一个简短、可执行的问题并等待用户回复。缺少代码比较版本或其他数据时，要求提供可验证来源中的精确值或产物；无代码、日志等权限时，展示工具
   实际返回的申请链接或联系人和所需权限。不得编造申请链接，不得让用户粘贴凭证、Cookie、Token 或
   Authorization Header。
3. 将编排层等待状态记为 `awaiting_user_input` 或 `awaiting_authorization`，不得把这两个值写入
   `TaskAnalysisReport`。明确说明用户补充信息或完成授权后可继续同一归因。此时只结束当前交互轮次，
   不得把整单标为失败、完成或交付半成品报告。
4. 用户回复后先校验补充信息的来源与冻结身份，并重新读取 task `update_time`。快照未变时只重跑受阻的
   只读分支并继续剩余步骤；快照变化时重建快照和受影响清单后继续。授权后仍被拒绝时更新同一个交互
   请求并继续等待，不循环重试，也不降级为 UI、猜测版本或弱证据。

## 证据来源与身份门禁

不同问题使用不同权威来源，不能用单一来源替代完整判断：

| 要证明的事实       | 首选来源                                                                          | 补充来源                      | 使用边界                                                                 |
| ------------------ | --------------------------------------------------------------------------------- | ----------------------------- | ------------------------------------------------------------------------ |
| 实际执行结果       | task / method 汇总、flow diff、base/replay request/response/outbound、replay log  | 错误目录、监控                | 任务完成只表示流程结束，不表示结果有效                                   |
| 代码变更归因       | canonical Analyzer 返回的 repository、base/target revision 与 artifact            | 代表 Flow commit 仅作任务取证 | FTF 只传 `task_id + similar_diff_id`，Code resolver 是代码身份唯一解析点 |
| 变更是否预期       | 已确认需求或技术方案、MR 描述、测试计划、任务 `demand_items`                      | 业务 Owner 明确确认、主干对比 | 代码存在变化只能证明“变了”，不能证明“符合预期”                           |
| 环境与配置         | 回放时间窗内的 TCE、TCC、Neptune、日志、Trace、Metrics                            | 当前配置快照                  | 当前状态不能倒推历史状态；必须匹配 region、env、cluster 和时间窗         |
| 测试完备性         | Nario `scene_coverage`、`code_coverage`、`core_method_coverage`、计划 method 范围 | 历史同计划任务                | FTF DIFF 只覆盖已执行流量；覆盖缺失时不能推导“无回归”                    |
| 自动归因与历史标注 | attribution status、possible/excluded/unknown、confidence、历史 `opType`          | 人工标注                      | 只作候选证据；部分完成、失败或历史继承不能替代当前任务复核               |

代码关联前必须完成业务触发门禁：

1. 当前调用已进入任务归因或 DIFF 根因分析路由；
2. 目标 `similar_diff_id` 唯一、与冻结 `task_id` 绑定，任务报告目标属于冻结清单；
3. 已完成现有降噪检查，且结论不是“可剔除降噪项”。

门禁通过后即调用一次 wrapper；待核验降噪候选、尚未定位根因、未发现代码候选、日志不足或已
初判为配置/平台问题均不得作为跳过理由。repository 与 revision 由 Code resolver 唯一解析，FTF
不读取 Flow commit 作为 Analyzer 入参。

当 canonical Analyzer 适用时，只有身份一致、artifact 完整且
`analysis_state=proven_code_caused` 的结果才可能映射为 `strong`；仍须结合当前任务的生产、
传递、消费和影响证据完成因果链。`invalid_observation`、`analysis_incomplete`、
`evidence_blocked`、`proven_not_code_caused`、`runtime_unresolved` 以及依赖级 blocked 结果
均不得映射为 `strong`。

## 缺陷准入门禁

某项只有同时满足以下条件，才能进入缺陷列表：

1. **行为异常**：有明确预期，且 base / replay 差异不是已确认的预期业务变更。
2. **业务归属**：问题发生在被测业务仓库的业务代码，不属于 FTF、公共基础设施、下游平台、
   业务配置或环境状态。
3. **真实触发**：当前任务 request、状态或依赖条件可以真实进入该代码路径。
4. **生产与传递证据**：异常值或状态由明确生产方产生，并经过 HTTP / RPC / MQ / DB /
   Cache 等链路传递到消费方，语义未在中途改变。
5. **消费与影响证据**：消费方按有问题的方式解释该值或状态，并造成可观察的错误响应、
   错误数据、权限问题、稳定性影响或兼容性破坏。
6. **代码因果归因**：`code-diff-correlation.md` 的相关性为 `strong`。base/replay commit 不同时，
   必须满足 canonical Analyzer 身份一致、artifact 完整且 `analysis_state=proven_code_caused`；
   commit 相同时，必须以固定版本源码和任务时间窗日志 / Trace 定位真实运行路径、跨服务字段生产
   与传递链、消费代码及首个代码分歧点。两条路径都必须能预测最终 FTF 结果。
7. **反例排除**：已排除随机值、数组乱序、输入不一致、回放失败、mock 异常、FTF 平台问题、
   配置差异和环境污染等更直接解释。
8. **结论置信度**：在私有结构中标注高或低置信度；部分归因时只允许对证据完整的独立范围生成
   缺陷，并明确整单仍未完成。置信度决定优先级，但不替代前七项因果与业务证据。

任一条件缺失时，不得进入缺陷列表。该项仍应保留在 DIFF 归因分析，并标明已证明事实、
推断和待验证证据。

## 优先级

优先级只由 Finding 原因和置信度决定，不使用 `diffCount`、聚类数量、错误日志数量、影响范围或
是否由本次变更引入来上调：

| 原因        | 高置信度 | 低置信度 |
| ----------- | -------- | -------- |
| 业务缺陷    | P0       | P1       |
| 预期变更    | P2       | P1       |
| 噪音        | P2       | P1       |
| FTF平台问题 | P3       | P2       |

没有符合缺陷准入门禁的项时，
“总体结论”板块只写“未发现缺陷。”并省略缺陷列表，不要用 FTF 平台问题或业务配置问题填充缺陷。

## DIFF 根因类型

每个根因聚类必须且只能选择以下一个类型：

| 类型        | 使用条件                                                           | 是否可进入缺陷列表                       |
| ----------- | ------------------------------------------------------------------ | ---------------------------------------- |
| 业务变更    | 业务代码、接口契约或产品行为发生变化；需要区分预期变更与非预期回归 | 仅非预期业务代码回归且通过缺陷准入门禁时 |
| 系统噪音    | 随机值、时间戳、trace/token、无业务语义的数组乱序等高置信噪音      | 否                                       |
| 稳定性问题  | 超时、连接拒绝、实例抖动、依赖瞬时失败、资源不足等                 | 仅能证明由业务代码缺陷直接导致时         |
| FTF平台问题 | 录制、回放、mock、断言、插桩、协议注入、报告解析或 FTF 配置导致    | 否                                       |
| 其他        | 业务配置、权限、白名单、环境数据、证据不足或无法归入前四类         | 否                                       |

业务配置发生预期调整时可以归为“业务变更”；配置缺失、配置错误或环境配置不一致统一归为
“其他”。无证据时使用“其他”，不要猜测成“业务变更”或“FTF平台问题”。

五类枚举保持稳定，同时增加两个解释维度：

- **子类型**：例如业务代码、契约变更、随机值、数组乱序、连接失败、FTF Mocker、业务配置、
  权限、环境数据、证据不足。它用于解释“具体是什么”，不新增根因类型。
- **预期性**：`预期内 / 非预期 / 待确认`。业务变更必须填写；其他类型按当前证据选择
  “预期内”或“待确认”，不得自创额外枚举。

根因置信度统一为：

- **高**：当前任务内存在直接证据，因果链闭合，关键反例已排除。
- **低**：证据不足以达到高置信度，包括链路仍缺一环、仅有聚合现象、历史标注、自动归因建议或单条样本。

高低置信度都可以进入根因聚类；进入缺陷列表仍必须通过上述八项准入门禁。

## 标准流程

### 1. 固定分析快照、身份与范围

```bash
bytedcli --json ftf target parse --url "<ftf-task-url>"
```

冻结解析结果中的 `site` 和 selector。后续 URL→ID 命令必须显式复用全局路由：cn 使用
`--site cn`，zg 使用 `--site cn --vregion China-Pay`；与用户显式配置冲突时停止。只有裸 ID 且
站点未知时先索取，不从 ID 或默认配置猜测。下文 ID-only 示例以 cn 为例。

解析后只选择一种首轮证据入口：

- 全量任务默认执行一次 `bytedcli --json --site cn ftf task get --id <task_id>`，再按需查询聚类。
- 小范围快速分析可用一次 `task evidence get` 替代 `task get`，并复用其 `context`、
  `aggregates`、`topClusters` 和 `sources`。

记录分析快照时间、task `update_time`、space、PSM、plan、env、branch、PSM task id、任务
形态、任务状态和当前 URL 筛选。对任务中的每个 PSM 执行一次
`bytedcli --json --site cn ftf psm get --psm <psm>`，冻结 PSM 元数据中的 Codebase 仓库标识；
不能因为 task 顶层没有 repository 字段就放弃源码取证。代表 Flow 的 `base_commit`、
`replay_commit` 和 `record_commit` 可作为任务与运行时路径证据冻结，但不得成为 Analyzer 请求
参数或覆盖 Code canonical 结果中的 repository、base/target revision。

同时保留冻结任务详情中每个 method 的 inbound before/after script 及其他实际执行参数。脚本只有在能解析出具体 header、参数或组件选择及其 base/replay 实际值时，才作为任务执行配置证据；脚本文本、任务描述或场景名称本身不是根因证据。

用户要求“任务报告级归因”且未明确限制筛选时，分析范围是任务报告中的全部 DIFF，不能只看
默认未处理或 Top N。任务不是可消费终态时停止深挖，输出任务有效性和等待条件。

### 2. 建立任务质量漏斗与覆盖边界

先按下面的关系解释任务统计：

```text
总流量 → 发送失败 / 发送成功 → 响应异常 / 已断言 → DIFF / 无 DIFF
```

关键字段必须按当前契约解释：

- `case_count`：总流量数。
- `success_case_count`：发送成功数，不等于业务响应成功数。
- `failed_reason_count`：发送失败原因分布，其数量合计是发送失败数。
- `fail_case_count`：响应异常数；它与发送失败数互斥，但不是 `success_case_count` 的反义字段。
- `diff_case_count`：产生 DIFF 的流量数。
- `need_confirm_case_count`：仍需人工确认的 DIFF 流量数。

发送失败与响应异常语义不同，必须分别统计和归因，不得互相替代。

本流程把单条流量的 `failed_reason != 0` 定义为回放失败。错误码名称、含义、定位组件和通用
方案读取 `enums.md#单条流量回放失败码failed_reason`；它镜像自 FTF 后端回放错误码定义。目录
只作预分类，若代码、日志、请求/响应等直接证据与目录冲突，以直接证据为准；任务版本可能
晚于目录且无法核实时，明确标记版本证据边界。

`diffCount`、`logCount` 和上述任务级数量仍按 `domain-model.md` 区分。回放失败没有进入 DIFF
集合时，必须进入任务质量漏斗和“回放失败归因分析”，不能冒充 DIFF 流量或 DIFF 归因分析。

同时读取 `scene_coverage`、`code_coverage`、`core_method_coverage` 及其详情。代码覆盖率展示目标 PSM
在 `code_coverage_detail` 中的全量 `coverage_rate`：只有对应 `coverage_err` 为空且数值位于 `[0, 100]`
时才换算为比例写入报告；增量 `incr_coverage_rate` 不替代该指标。空详情、错误字段非空或任务未创建
对应度量时统一按未取得处理，报告显示“暂无”，不得直接解释为 0% 覆盖。若开启主干对比，
读取 `base_task_id` / `base_task_id_realtime` 对应结果，区分新增 DIFF、共同 DIFF 和主干 DIFF；
未开启时明确写“无主干对比证据”，不得自动触发。

预期回放接口数只从冻结任务详情中的 `psm_replay_param_detail.{psm}.replay_method_params` 计算，其中 `{psm}` 为报告目标 PSM：

```text
expected_method_keys = Object.keys(task.psm_replay_param_detail[psm].replay_method_params)
expected_methods = expected_method_keys.length
interface_coverage = effective_covered_methods / expected_methods  # expected_methods > 0 时
```

`replay_method_params` 必须是 map；不得使用数组长度、method report 条目数、DIFF method 数或
其他字段代替。字段缺失、为 `null`、数组或其他非 map 类型时，`expected_method_keys`、
`expected_methods` 和 `interface_coverage` 均写 `null`，表示未取得口径，不能写成 0。

实际回放接口与逐接口流量必须读取目标 PSM 的聚合响应：

```bash
bytedcli --json --site cn ftf task report get \
  --dimension psm --id <task_id> --psm <psm>
```

PSM 聚合中的每个 method 条目代表一个实际接口；逐接口总流量取该条目的 `total`，回放失败
流量取该条目 `failed_reason` map 下全部枚举计数之和，有效流量为两者之差。只有总流量大于
0 的预期接口计入 `actual_methods`，只有有效流量大于 0 的预期接口计入接口覆盖率。
`failed_reason` 缺失或不是 map 时，该接口的总流量与失败流量均标记为 `null`，不得猜测为 0；
PSM 聚合中未出现的预期接口按总流量 0、失败流量 0 记录。

据此先判定任务有效性。任务完成但大量流量发送失败或响应异常时，即使缺陷列表为空，也不能
输出“通过”。

### 3. 获取完整 DIFF 与回放失败清单

先用 `task diff-cluster list` 分页获取全部 inbound / outbound 聚类，按
`clusterSelection.total` 对账。小范围快速分析可以单独执行一次：

```bash
bytedcli --json ftf task evidence get \
  --url "<ftf-task-url>" \
  --annotation-op-type all \
  --page 1 \
  --page-size 20 \
  --top-n 10 \
  --sample-size 3
```

如果选择 `task evidence get` 作为首轮入口，必须复用其中的 task、PSM、method 汇总和样本，
不再重复执行 `task get` 或 `reason list`。全量任务优先先列清单，再按证据缺口读取 method
report 和 cluster 详情，避免统一证据包内部 fan-out 触发限流。

若 CLI 截断且无法证明清单完整，归因状态必须为“部分”，不能声称完成全量分类。
按 `method + direction + diff path/reason + 内部聚类标识` 建立原始清单：

- 单个 method 的聚类不超过 10 个时全部下钻。
- 超过 10 个时按 `task-diff-triage.md` 分组下钻，直到清单内全部聚类完成类型和根因归类。
- 每个根因候选先选最典型样本、边界样本和反例样本；样本结论不一致时继续扩大样本，直到拆分
  根因或明确证据不足。
- 每个原始 DIFF 聚类至少保留一个代表 flow diff 链接；无法构造时记录 task URL、method、
  direction、path、log id 和缺链接原因。
- 每个聚类同时冻结 source ID、所属 Flow ID，以及方向、响应状态/错误码、base/replay 值形态和候选责任 PSM 组成的现象指纹；后续样本必须反向绑定到这里，不能跨根因混入。
- 不在最终报告展示 `similarDiffId`；仅在分析过程的证据缓存或复现命令中保留。

同时从 task 的 `failed_reason_count` 和 method report 的 `log_id_classify_map` 建立完整回放
失败清单：

- 先从 task detail 的 PSM 范围和 Flow 列表发现实际 PSM/method，再查询这些 method 的 report；
  不得根据用户文本或 DIFF method 集猜测并扇出 method report；
- 只纳入 `failed_reason != 0` 的流量，并按 `diag-replay-failure.md#第一步读任务终态与失败聚类` 建立有界清单；聚合字段只用于发现和对账，单条权威值来自 `data.diff.failed_reason`，达到请求预算时转为“部分”并记录证据缺口；
- `replay_failed_reason=null` 只表示该 method 聚合字段无失败证据，不能据此排除回放失败；
- 初始清单按 `method + failed_reason` 组织，保留每条流量的 log id、pid、replay time、
  `err_msg` 的脱敏摘要和 flow diff 链接；聚合值与单条值冲突时以单条值归类；
- 对每个错误码读取 `enums.md` 的名称、描述、位置和通用方案；兜底未知码按其有界取证规则下钻；
- 相同错误码只能作为候选预分组。若 `err_msg`、责任组件、触发条件或失败机制不同，必须拆分
  为不同回放失败根因；
- 每条失败 Flow 也冻结为独立成员，保留 method、失败阶段、错误码/响应签名、错误正文形态和候选责任 PSM，后续按与 DIFF 相同的样本归属规则校验；
- 每个回放失败根因至少保留一个代表 flow diff 链接；同一根因包含多种直接错误签名时，每种
  签名至少保留一个链接。

### 4. 降噪与单条根因

先按 `diff-denoise.md` 完成随机值和数组乱序检查，再按
`flow-diff-root-cause.md` 读取代表 flow：

```bash
bytedcli --json ftf task diff-cluster get \
  --url "<ftf-task-url>" \
  --similar-diff-id <similar_diff_id> \
  --with-values \
  --sample-values 3 \
  --with-similar-cases \
  --with-outbound

bytedcli --json --site cn ftf task flow get --task-id <task_id> --pid "<pid>"
bytedcli --json ftf flow diff get --url "<ftf-flow-diff-url>" --with-values --with-outbound
```

`task flow get` 返回的 commit 字段只记录为 Flow 证据。canonical Analyzer 调用只使用冻结任务的
`task_id` 和当前唯一 `similar_diff_id`，不得用 Flow 或任务级 commit 组装、补齐或覆盖 Code
resolver 的版本结果。若 resolver 无法解析比较版本，将该成员标为 `evidence_blocked`，记录 PID、
缺失字段和获取动作，按“阻断交互与恢复检查点”请求带来源的精确版本信息或相应访问权限；该阻断
未解除前不得生成最终 `ftf-report.md` / `ftf-report.html`，解除后只重跑该受阻分支并继续。

对每个原始聚类记录：现象、base/replay 输入与输出、状态码、关键字段值、outbound、
replay logid、相似 case、降噪结论和当前根因假设。

合并后的每个 DIFF 根因必须在“现象”和“问题根因”之间输出“流量样本”。每个样本必须填写不超过 30 个 Unicode 字符的 `display_name`；名称尽可能概括差异语义和接口/方法，但不要求完全准确，例如“审计单详情鉴权提前返回”；
优先覆盖不同可观察结果，但每个根因最多展示 10 条可点击 flow diff 链接。超过 10 条时只保留
最具代表性、边界性和反例价值的 10 条；展示截断不得改变 `impact_counts.flows`、私有 Flow 清单
或数量对账。不能只给接口路径、`代表流量`、`样本 N`、task 链接、log id 或内部 `similarDiffId`。

逐聚类取证完成后才允许合并根因。因果机制、责任 PSM、修复点和预期性必须一致；未定位项还必须具有相同方向/阶段、响应签名、值形态和候选责任 PSM。“未定位”不是根因签名，不能把鉴权、Mock、配置、动态字段、数组或对象缺失等异质表现合并为一项。同一鉴权机制可以跨接口合并，但每个成员仍保留自己的聚类、Flow 归属和实际检查记录。

### 5. 补日志、配置、意图与代码证据

- 日志时间窗围绕 `replay_time`，不使用当前时间。
- 对聚类样本先用 `diff attribute replay-logids` 将录制 LogID 映射到 `logid_comparison`；Flow
  列表必须使用严格个人身份按游标完整翻页，不能让环境中的共享服务账号 JWT 覆盖用户身份；
  单页不超过 20。映射成功后用 replay LogID 查询业务日志 / Trace，
  不得拿录制 LogID 或 FTF Flow 链接替代回放运行时证据。
- 业务错误、FTF 错误和下游错误分别查对应 PSM，不能只查入口服务。
- 入口 PSM 的固定 commit 中没有字段名、只存在通用 map / JSON 透传，或只能定位到最终响应组装时，
  不得停止并写“源码未命中”。必须沿代表流量 Trace 检查实际下游 PSM，定位字段值首次出现、改变
  或丢失的 span，再冻结该下游服务在任务时间窗内的运行版本、仓库和 commit。
- 对跨服务字段依次建立“下游生产代码 → Trace 中间值 → RPC / map / JSON 传递 → 入口消费代码 →
  最终响应”链路。若旧、新组件读取同一个中间值，必须比较二者的 key、类型转换、默认值和过滤
  条件，首个能解释两侧结果差异的代码位置才是根因；公共双跑或 DIFF 采集入口不是字段根因。
- 业务变更候选必须通过需求、MR、测试计划、任务 `demand_items`、业务确认或主干对比判断
  预期性；来源缺失时填“待确认”。
- 当前聚类已取得唯一 `task_id + similar_diff_id` 且不是“可剔除降噪项”时，通过 FTF wrapper 调用一次当前已加载 Code Skill；同一报告先按 `similar_diff_id` 去重并按冻结清单稳定顺序执行。
- 只消费 `ftf-code-analysis/v1` 三信封。`accepted` 必须保留请求身份、聚合结论、六态 `analysis_state`、状态专属对象、兼容 evidence 投影、`self_proof`、warnings 和 `result_artifact {bytes, sha256}`；`not_applicable/no_revision_delta` 不写入 `analyzer_runs[]`，转固定版本运行路径；`rejected` 只保留 EvidenceBoundary。不得用自然语言摘要覆盖 canonical 结果。
- Analyzer 缺失、能力不满足、执行中断或输出非法时，把该代码证据标为 blocked 并记录唯一恢复动作；不得伪造六态、提升置信度或回退到 `bytedcli codebase`、Git clone/search 猜测代码归因。
- 代码相关性不是 `strong` 时，禁止加入缺陷列表。不同 commit 的 `strong` 必须有逐聚类
  `proven_code_caused` Analyzer 结果；相同 commit 的 `strong` 必须没有伪造的 Analyzer 结果，并且
  同时具有任务目标固定 commit 代码、任务时间窗日志 / Trace、生产传递证据、消费影响证据和首个
  代码分歧点。
- FTF 平台问题只需定位到平台组件、触发条件和直接证据；无需为了填充业务缺陷继续硬找
  业务代码。
- 智能归因只作补充。必须读取其归因状态、完成/失败 Agent、possible / excluded / unknown、
  confidence 和 suggested action；部分或失败结果不得覆盖当前任务的直接证据。

每个根因的说明深度必须满足：

- **现象**：最多 200 字，只保留用户可观察的异常、关键差异和必要上下文。
- **问题根因**：最多 200 字，至少定位到具体组件、配置项、函数或外部依赖，并说明故障机制
  和最终表现。禁止只写“地址问题”“权限问题”“连接失败”等一句概括。
- **代码证据**：涉及代码时，必须使用可点击的 Codebase 链接，固定到仓库、实际 commit /
  ref、文件和行号范围，例如
  `[replay.go:L289-L297](https://code.byted.org/example/repo/blob/<commit>/biz/service/replay.go#L289-L297)`。
  只有本地路径、函数名或当前 master 行号不能作为最终报告链接。
- **日志 / Trace 证据**：涉及运行时日志或调用链时，必须记录日志工具返回的 LogID / TraceID、
  时间窗和决定性关键词。日志平台实际返回可分享链接时必须使用该链接；平台明确没有可分享链接时，
  `url` 写 `null` 并以不可点击标识呈现，禁止猜测或拼接 URL。不得只粘贴无标识、无时间窗的日志文本。
- **配置 / 部署证据**：涉及 TCC、ACL、TCE 或其他平台状态时，优先附时间窗一致的配置、
  工单或部署详情链接；当前快照不能替代历史状态。
- **任务执行配置证据**：冻结任务详情里的 before/after script、请求头和组件选择可证明本次任务向 base/replay 注入了哪些不同输入。报告需列出具体字段和值，并用固定 commit 源码解释这些值如何选择分支。若输入和代码足以唯一决定分支、且没有 TCC、实验、缓存、下游结果等外部状态参与，任务配置与固定代码可直接闭环；否则必须取得日志 / Trace 或相应历史状态，才能证明代表流量实际命中了该路径。
- **反例证据**：明确列出已排除的更直接解释，不能只写“已排除其他问题”。
- **判断依据**：只展示能支持根因机制的代码、日志 / Trace、历史配置或部署证据链。按信息价值
  排序，优先把服务、仓库、文件、行号、函数和故障逻辑压缩在相邻语句中；有日志时紧接命中
  关键词、时间窗和 LogID / TraceID；平台返回分享链接时把标识渲染为链接，否则渲染为不可点击文本。
  至少存在一项机制证据时，才允许在链路末端附一个代表
  Flow 作为结果印证。只有 Flow / DIFF 现象、聚类统计、平台标注或证据边界时，输出
  “当前没有能证明根因的直接证据。”。调查结果只保留在私有结构化数据中；影响结论的受阻原因和补证动作写入“处理建议”。判断依据可用一段或数段，原则上不超过 800 字。
- 没有上述机制证据时，“问题根因”写为“现有证据不足，尚不能确认根因。”，不得罗列代码、配置、输入或依赖等
  猜测方向换一种方式凑数。配置或部署证据必须包含具体对象、任务时间窗内实际值和改变执行
  路径的机制；任务场景名、任务描述、当前快照或任务首页不满足该门槛。

无法取得适用的代码或日志 / Trace 时，必须把调查状态置为 `evidence_blocked`，在私有调查矩阵中逐成员
写明真实获取尝试、阻塞原因和唯一恢复动作，然后暂停最终报告渲染并进入“阻断交互与恢复检查点”；
等待用户补充对应信息或完成权限申请，随后从冻结检查点继续，不得结束整个归因流程；
不得把该状态包装成“部分归因”或用“现有证据不足”收口。只有目标提交代码已实际检查，且同一成员的
任务时间窗日志或 Trace 至少一项已实际检查后，才允许使用 `exhausted_unresolved` 表示关键证据已穷尽但
尚未闭环。仅缺少平台分享链接但已有可核验标识、时间窗和决定性内容时，不视为证据缺失，也不得猜测
URL。base commit 缺失只阻断 base→target 变更因果，不得阻断固定 target commit 的代码路径分析。

处理建议必须同时包含：

1. **责任方**：负责修复或配置调整的团队 / 模块；
2. **修改对象**：具体仓库文件、函数、配置 key、服务或部署单元；
3. **最小改动**：针对已证明根因的具体修改，不写泛化治理建议；
4. **验证方式**：复用哪些样本、执行什么检查、以什么结果作为关闭标准。
   处理建议原则上不超过 800 字；确有必要描述分阶段修复或回滚条件时可超过，但不得重复判断
   依据。

### 6. 分别生成 DIFF 与回放失败根因

DIFF 和回放失败使用同一套根因合并规则，但分别聚类、分别对账。只有以下四项都相同，才允许
合并：

1. 责任组件相同；
2. 触发条件相同；
3. 失败机制相同；
4. 解决方案或处理责任人相同。
   状态码相同、`failed_reason` 相同、错误文案相似或最终字段都为空，不足以合并。一个原始
   DIFF 聚类只能归入一个 DIFF 根因；一条回放失败流量只能归入一个回放失败根因。每个根因可以
   覆盖多个 method/path，但“流量样本”和“判断依据”必须保持可追溯。

DIFF 归因分析和回放失败归因分析都使用固定五类根因类型、置信度、预期性、子类型、责任方、处理建议
和验收标准。回放错误目录中的 `location=biz` 只表示失败发生在被测服务调用阶段，不等于业务
代码缺陷；是否进入缺陷列表仍须通过完整缺陷准入门禁。

### 7. 生成缺陷列表

逐个 DIFF 和回放失败根因执行缺陷准入门禁：

- 通过：生成一条业务代码缺陷，填写等级、标题、问题根因与判断依据、解决方案。
- 未通过：只保留在 DIFF 归因分析或回放失败归因分析。
- 多个根因聚类指向同一处业务代码和同一修复时，可合并成一个缺陷；覆盖的根因聚类 ID 只
  写入私有 JSON 用于对账，最终报告仅展示聚合数量。
- 同一现象由不同代码根因引起时必须拆分，不能按接口名或错误码合并。

### 8. 生成发布建议并校验快照

先按任务有效性和归因状态确定报告能支持什么结论，再结合缺陷列表、覆盖证据和用户门槛生成
发布建议。缺陷列表为空但任务无效或覆盖不足时，发布建议必须是“不可据此判断”。

结束前重新读取 task 的 `update_time` 和关键计数。若与分析快照不一致：

- 使受影响缓存失效；
- 能快速补齐时重新对账；
- 否则把归因状态降为“部分”，明确报告基于哪个快照，不能混用前后两版数据。

## 呈现格式

### 私有结构化中间产物

分析完成后，只创建一份 `schema_version=12` 且符合 [`task-analysis.schema.json`](../assets/schemas/task-analysis.schema.json) 的临时 JSON。
它只保存结论、范围、计数、归因项、证据身份和其他建议项，不保存模型推理过程、原始 Header、凭据或完整业务 payload。

每个 `Finding` 必须提供：

```text
id, severity, title, root_cause_type, subtype, confidence, finding_reason, expectedness,
responsible_party, code_correlation, phenomenon, cause_signature, attribution_members[],
investigation, samples[], root_cause, evidence[], impact_counts, recommendation, admission,
analyzer_runs[], covered_cluster_ids[], covered_flow_ids[]
```

`impact_counts` 固定包含 `methods`、`flows`、`field_clusters` 三个非负整数，分别表示 Finding 影响的去重接口/方法数、去重流量数和字段聚类数。
`field_clusters` 必须等于内部 `covered_cluster_ids[]` 的数量；`covered_cluster_ids[]` 和 `covered_flow_ids[]` 只用于私有校验、Analyzer 身份绑定和数量对账，最终报告不得输出这些 ID。

- `id` 是稳定内部标识，不承载优先级；三类 Finding 的 `severity` 均为 `P0/P1/P2/P3`，严格按 `finding_reason + confidence` 矩阵计算；列表再按优先级、置信度和流量数降序稳定排序。
- 每条 Finding 都必须填写 `finding_reason`，且只能是 `业务缺陷 / 预期变更 / 噪音 / FTF平台问题`。该字段表达报告中的归因标注原因，不替代私有 `expectedness`，也不改变缺陷列表的准入结果：通过缺陷准入门禁的非预期业务侧问题标为“业务缺陷”，符合需求的变化标为“预期变更”，随机值、顺序、稳定性或过滤类非功能差异标为“噪音”，由录制、回放、Mock、断言、插桩、协议注入、报告解析或 FTF 配置导致的问题标为“FTF平台问题”。`defects[]` 只能使用“业务缺陷”；DIFF 与回放失败可使用全部四值。
- `cause_signature` 固定根因机制、责任 PSM、修复点和预期性；`attribution_members[]` 保存 source 类型/ID、Flow IDs、method、方向/阶段、path/reason、响应签名、值形态和候选责任 PSM。成员的 cause signature 必须一致；未定位成员还必须具有同质现象指纹。
- `investigation.sources[]` 完整列出代码、日志、Trace、响应、配置、部署；每类 `members[]` 以 `source_type + source_id` 逐项覆盖当前 Finding 的原始 DIFF / 回放失败成员，并记录 `available/checked/evidence_ids/acquisition_attempt/blocker/recovery_action/outcome`。`checked=true` 时 `evidence_ids[]` 必须引用当前 Finding 中类型匹配的真实证据，`checked=false` 时必须为空；代码、日志和 Trace 证据还必须通过 `member_refs[]` 反向声明覆盖同一成员，日志 / Trace 的 `flow_ids[]` 必须与该成员的真实 Flow 相交，共享证据必须逐项列出实际覆盖成员；代码证据必须匹配任务 target PSM、仓库和 commit，响应证据必须匹配该成员的 `source_id` 与 Flow。入口不可用时必须填写真实获取尝试、阻塞原因和唯一恢复动作；入口可用时这三项必须为 `null`。可用入口未检查、证据类型漏成员、单向引用、运行时证据没有匹配 Flow，或任一成员未实际检查目标提交代码以及日志 / Trace 至少一项时校验失败；`outcome` 用普通中文说明实际检查结果，禁止仅填写“暂无”“暂未定位”“未知”“未检查”“待检查”或“无”（包括尾部附加标点）。`introduced_by_current_change` 与 `broad_impact` 仅为归因事实，不参与优先级判定。
- `samples[].display_name` 是报告展示名，须为 1～30 个 Unicode 字符，并尽可能概括差异语义和接口/方法；禁止“代表流量”“样本 N”等空泛名称。`difference` 与 `subject` 保留为私有语义数据。每个样本以 `source_id + flow_id + evidence_id` 绑定当前 Finding 的成员、覆盖清单和 Flow evidence；同一 source/Flow 跨组复用时校验失败。同一 Flow 可承载多个独立 DIFF 聚类，回放失败成员则须保持 Flow 互斥。缺陷汇总只能精确复用基础归因已准入的成员，不得改写事实或重复归属。
- `admission` 仅用于缺陷，分别引用行为异常、业务归属、真实触发、生产与传递、消费与影响、
  代码因果和反例排除七类证据 ID；每类至少一个且必须解析到当前 Finding 的 `evidence[]`。
  置信度继续由 `confidence` 在私有结构中表达，并与 `finding_reason` 共同决定优先级；非缺陷 Finding 的 `admission` 必须为 `null`。
- `analyzer_runs[]` 保存 wrapper 准入后的 `task_id + similar_diff_id`、仓库和 base/target commit、
  顶层聚合、diff path/op、六态判别与专属对象、兼容 evidence 投影、可选摘要、warnings 和
  `result_artifact {bytes, sha256}`。Analyzer 原始输出中的 artifact 绝对路径只允许在同宿主
  wrapper 内用于目录边界、文件状态和摘要校验，不得写入临时 TaskAnalysisReport 或最终报告。
  不同 commit 的代码相关性为 `strong` 且覆盖 DIFF 聚类时，每个聚类
  必须有一条身份一致、artifact 完整且状态为 `proven_code_caused` 的记录；相同 commit 的运行态
  `strong` 归因必须保持数组为空，并以任务时间窗日志 / Trace 和固定版本代码完成准入。

实际调用 Code 的报告由首个 `accepted.analyzer_run` 的 `repository + base_ref + target_ref`，或
`not_applicable/no_revision_delta` 的 `repository + revision` 建立唯一代码身份；后者把同一 `revision`
分别回填现有 `metadata.base_identity.commit` 与 `metadata.target_identity.commit`。PSM、branch、
environment 沿用冻结任务值。冻结 PSM 仓库非空但与返回
repository 不一致，或后续任一身份字段冲突时，生成 `[report_identity_mismatch]` material
EvidenceBoundary，恢复动作固定为“修复任务内 DIFF 的代码身份一致性后重新生成报告”，并停止最终
报告。全部结果均为 `rejected` 时同样停止，不得使用旧的 Flow revision 冒充报告身份。

`test_sufficiency.expected_method_keys` 保存任务详情 map 的完整 key 清单，其长度必须等于 `expected_methods`。
`method_coverage_details[]` 必须逐一覆盖这些接口，记录 `method`、`total_flows` 和 `failed_flows`。`actual_methods` 是 `total_flows > 0` 的接口数；只有 `total_flows - failed_flows > 0` 才算有效覆盖，`interface_coverage` 等于有效覆盖接口数除以预期接口数。
任一接口的两个流量计数无法取得时必须同时为 `null`，此时 `actual_methods` 和 `interface_coverage` 也必须为 `null`，不得把未知当作 0。逐接口明细只在 HTML 的接口覆盖率悬浮层展示，不在 Markdown 展开。

每条 `Recommendation` 必须提供责任方、修改对象、最小改动、验证方式和引用的证据 ID。
“判断依据”和“处理建议”没有固定展示语法；不得要求分析者在 JSON 中编写 Markdown 列表或
HTML 片段。

代码、日志 / Trace、请求响应、Flow 与证据边界的角色和呈现方式统一遵循 [`diff-analysis.md`](diff-analysis.md) 的“归因证据规范”。代码摘录仅在能显著提高理解时填写，最多 20 行；缺陷代码证据的身份仍须与冻结目标一致。
Flow-only Finding 只能作为 `evidence_blocked` 的私有中间状态，必须包含 material evidence boundary、使用低置信度并将根因写为“现有证据不足，尚不能确认根因。”；renderer 必须拒绝将其生成 Markdown / HTML。阻塞时进入可恢复交互检查点，等待用户补充信息或完成授权后继续，不能交付最终归因报告。

应有但无法取得的证据使用 `evidence_boundary`，填写失败原因、唯一补证动作和 `material`。material boundary 无论位于根级还是 Finding 内，都必须将整单归因完整性降为“部分”或“失败”，
发布建议不得为“通过”或“有条件通过”；如果缺口影响缺陷准入门禁，则禁止写入缺陷列表。
任务链接和远程证据链接只允许 HTTPS；只有脱敏的本地辅助证据可使用无远程 host、query 或
fragment 的本地 `file://` 绝对路径。

### 校验和渲染

先只校验 JSON：

```bash
node scripts/render-task-analysis.mjs \
  --input /tmp/task-analysis.json \
  --validate-only
```

校验通过后，指定交付目录并同时生成固定文件名 `ftf-report.md` 和 `ftf-report.html`：

```bash
node scripts/render-task-analysis.mjs \
  --input /tmp/task-analysis.json \
  --output-dir /path/to/report-directory
```

`--output-base`、`--format` 和 `--output` 只保留给本地调试或兼容调用，不得用于正式任务级归因交付：

```bash
node scripts/render-task-analysis.mjs \
  --input /tmp/task-analysis.json \
  --format markdown \
  --output /tmp/task-analysis-preview.md
```

校验失败时只修正私有 JSON 并重试，不得重新查询远程证据或重复执行 canonical Analyzer。
renderer 不查询任务、日志、配置或代码，不执行归因，也不能改变缺陷准入结果。双格式模式先
完成两种格式的渲染和安全校验，再发布两个文件；任一格式失败时不得留下半套报告。

### Markdown 输出

renderer 使用 `assets/templates/task-analysis.md` 输出纯 GitHub-flavored Markdown：

- 标题后先展示有效流量、DIFF 流量、缺陷、接口覆盖率和代码覆盖率，再进入“总体结论”；有效流量等于总流量减回放失败流量，缺陷始终使用红色并取已通过准入门禁的缺陷列表长度；不展示任务、PSM、环境、快照或版本元信息表；
- “总体结论”不展示任务有效性、归因完整性、发布建议或证据边界表；无缺陷时只输出“未发现缺陷。”且省略“问题汇总”，有缺陷时在结论后用独立“问题汇总”板块列出缺陷；
- 空 DIFF 归因分析只输出“无 DIFF 流量”，空回放失败归因分析只输出“无回放失败流量”；
- 顶部只展示五项指标，不再生成“报告概览”和“测试充分度”章节；Markdown 不展开逐接口覆盖明细；
- renderer 按共享证据链组织高密度段落，最多渲染一条代表性 Flow；调查矩阵仅作私有完成门禁；重要受阻原因和唯一补证动作合并进“处理建议”；分析者不负责展示语法；
- Flow、代码、日志 / Trace、配置和部署链接由结构化证据生成并放在对应字段内。

### HTML 输出

renderer 同时使用 `assets/templates/task-analysis.html` 输出完整单文件 HTML：

- 保留 Markdown 相同的结论、计数、归因项、其他建议项和证据身份；标题区域不展示任务元信息；
- 标题最右侧展示蓝色“回放报告”链接。renderer 仅根据已校验 `task_url` 的 host 选择 CN China-North、CN China-Pay、I18N-TT、I18N-BD 或 BOE 的 canonical host，再以冻结的 `space_id` 和 `task_id` 重建任务路径；不透传原始 URL 的查询参数或 fragment，也不根据 ID 或默认站点猜测地域；
- 视觉遵循 Arco Design 亮色规范：主色 `#165DFF`，采用 neutral 分级、`2/4/8px` 圆角和 `4/8/16/24px` 间距节奏；
- 动态文本统一转义，链接只从已校验证据生成；
- 所有 CSS 内联，不加载外部资源、脚本或遥测；
- 报告不提供页面内打印按钮；浏览器原生打印仍由 `@media print` 样式支持，并设置 `referrer=no-referrer`；
- 所有板块只展示中文标题，不显示英文副标题；无缺陷时“总体结论”只展示“未发现缺陷。”且不渲染“问题汇总”，有缺陷时在独立“问题汇总”中列出缺陷；空 DIFF / 回放失败章节分别展示“无 DIFF 流量”和“无回放失败流量”；
- 标题下、“总体结论”上方用紧凑响应式卡片展示五项指标，数值和文案居中，最窄视口保持三列。有效流量使用绿色；DIFF 流量固定黄色；缺陷无条件使用红色；接口和代码覆盖率 `<50%`、`[50%,80%)`、`>=80%` 时分别用红、黄、蓝，未知项显示“暂无”并用黄色。其他计数只保留在私有 JSON 中；
- 接口覆盖率卡片支持悬浮和键盘聚焦，先显示预期/实际回放接口数，再用四列表格展示接口、总流量、失败流量和有效覆盖；成功流量大于 0 时显示“是”，未知计数显示“未知”；
- 归因明细的字段名和值统一使用白底，不对问题根因、判断依据、处理建议或其他单元格设置专属粗体或背景高亮；
- 所有 Finding 卡片标题右侧只展示原因标签，不展示预期性或置信度；业务缺陷、预期变更、噪音、FTF平台问题分别使用红、蓝、灰、黄标签；
- 输出不得包含模板占位符、凭据、原始 Header、临时签名 URL 或未脱敏 payload。

## 输出契约

最终报告必须由同一份已校验 JSON 生成，并遵守：

- 标题、章节名称和章节顺序不得调整，也不得添加模板外的一级或二级章节。
- 报告标题后直接展示五项关键指标，再进入“总体结论”；不得输出任务元信息表、“结论适用范围”或结论维度表。
- 只有明确归因为业务代码缺陷且通过全部缺陷准入门禁时，才在“总体结论”写“发现 `<N>` 个缺陷。”并在其后输出独立“问题汇总”。
- 没有明确业务缺陷时，“总体结论”必须只写“未发现缺陷。”，不得使用近义文案。
- 缺陷、DIFF 归因分析和回放失败归因分析必须使用模板中相同的六个字段及顺序：`现象 → 流量样本 → 问题根因 → 判断依据 → 影响范围 → 处理建议`。不得展示“定位过程”或其他调查步骤字段。
- 三类列表的标题前缀只显示 P0/P1/P2/P3，不显示 E1/D1/F1 等内部编号；统一按优先级、置信度、影响流量数排序，高优先级和高置信度在前。
- 不得生成“报告概览”或“测试充分度”章节。顶部只保留五项指标；需要表达的限制和动作只能进入既有归因条目或“其他建议项”。
- 未使用的 DIFF 归因分析只保留标题和“无 DIFF 流量”；未使用的回放失败归因分析只保留标题和“无回放失败流量”，不得追加失败口径、统计解释或其他说明。
- “现象”和“问题根因”各不超过 200 字；“问题根因”说明故障组件、失败机制和最终表现。
- “影响范围”只输出“影响 `<接口/方法数>` 个接口/方法、`<流量数>` 条流量、
  `<字段聚类数>` 个字段聚类。”，不得输出单个或完整聚类 ID、Flow ID，也不得附加自由文本。
- 代码、日志、调用链、请求与响应、配置、部署的检查结果只保留在私有调查矩阵；任一可用入口未检查时不得生成报告。任一成员缺少已检查的目标提交代码，或缺少已检查的任务时间窗日志 / Trace 时，必须记录获取尝试、具体阻塞和可执行恢复动作并暂停渲染，通过可恢复交互请求权限或信息，补齐后从检查点继续。
- “判断依据”遵循共享证据链规则，不限定固定句式或段数；存在证据链时必须包含适用 PSM，
  原则上不超过 800 字，确有必要保留完整因果链时可超过。没有根因机制证据时输出“当前没有能证明根因的直接证据。”。
- “处理建议”必须明确责任方或 PSM、修改对象、最小改动和验证标准；涉及代码时附文件行号
  深链，涉及日志时优先附平台实际返回的复验日志超链；平台无分享链接时附 LogID / TraceID 和
  时间窗。展示可以是段落或简单列表，不得只写“检查配置”“联系 OnCall”或“建议重跑”。原则上
  不超过 800 字，确有必要描述分阶段修复或回滚条件时可超过。
- 每个根因最多展示 10 条流量样本；超过时按代表性、边界性和反例价值选取，完整流量数量仍由
  私有清单和 `impact_counts.flows` 对账。
- 流量样本名称不得超过 30 个 Unicode 字符，应尽可能语义化并优先包含差异语义和接口/方法，但不要求完全准确；不得使用“代表流量”“样本 N”等空泛名称。
- 不适用的证据项可以省略。应有但无法取得的代码、日志、配置或部署证据必须写入“证据边界”
  并降低置信度；仅缺分享 URL 时保留证据并将 URL 置空，不得伪造链接。
- 任务有效性、归因状态、发布建议、数量对账和未闭环证据仍按本 Workflow 计算并用于约束
  结论，但不在“总体结论”中展示；需要用户处理的证据缺口只进入对应归因项或“其他建议项”。
- “其他建议项”只保留与当前证据直接相关、能明确责任方、修改对象、具体动作和验收结果的
  建议；没有此类建议时输出“无。”，不得用泛化治理话术凑数。
- 最终报告必须成对生成，文件名固定为 `ftf-report.md` 和 `ftf-report.html`；
  最终回复必须同时提供两个文件链接。
- renderer 成功后删除私有 JSON 和敏感临时证据；renderer 失败时保留脱敏 JSON 供修正，但
  不得生成半成品报告。

## 压力场景

| 场景                                       | 必须输出                                                                     |
| ------------------------------------------ | ---------------------------------------------------------------------------- |
| 任务完成但大量流量发送失败或响应异常       | “总体结论”按缺陷准入结果输出；问题进入对应归因和其他建议项，不得冒充业务缺陷 |
| 没有 DIFF 但接口或代码覆盖证据缺失         | “总体结论”写“未发现缺陷。”；可取得的覆盖数据在顶部指标中体现                 |
| 代码改动能解释 DIFF，但预期性证据缺失      | 根因可为业务变更，预期性为待确认，不得直接生成业务代码缺陷                   |
| 关键代码或运行时证据源失败                 | 状态置为 `evidence_blocked`，暂停报告渲染并进入可恢复的权限 / 信息交互，补齐后继续 |
| 历史标注为噪音，但当前样本不再满足降噪条件 | 以当前任务证据为准重新归因，不继承历史噪音结论                               |

## 完成检查

- [ ] 分析范围内每个原始 DIFF 聚类恰好归入一个根因聚类。
- [ ] 每条 `failed_reason != 0` 的流量恰好归入一个回放失败根因或未闭环项。
- [ ] DIFF 与回放失败已分别完成数量对账，没有混用流量数和聚类数。
- [ ] 每条归因的影响范围只展示接口/方法数、流量数和字段聚类数，未输出聚类 ID 或 Flow ID。
- [ ] 每个根因最多展示 10 条流量样本，每个名称不超过 30 个 Unicode 字符且尽可能语义化；展示截断未改变完整流量数量或数量对账。
- [ ] 每个样本均绑定当前 Finding 的成员、Flow 和 Flow evidence，没有跨根因混样；聚类只在根因签名一致时合并，未定位项还具有同质现象指纹。
- [ ] 六类证据入口均标记可用性、检查状态和易懂的检查结果；不可用入口记录真实获取尝试、具体阻塞和唯一恢复动作，并已进入可恢复交互；每个成员均已检查目标提交代码以及日志 / Trace 至少一项；`evidence_blocked` Finding 未进入最终报告。
- [ ] 三类 Finding 均使用 P0/P1/P2/P3，并严格按“原因 + 置信度”判级，再按优先级、置信度和影响流量排序。
- [ ] 每条 Finding 均填写四选一的 `finding_reason`，HTML 标题右侧只显示对应红、蓝、灰、黄原因标签，不显示预期性或置信度标签。
- [ ] 每条现象和问题根因均不超过 200 字，并明确故障组件、失败机制和最终表现。
- [ ] 非可剔除降噪项均按冻结 `similar_diff_id` 去重调用一次 wrapper；没有用 Flow commit、代码候选或初步根因作为前置门禁。
- [ ] 已按 `ftf-code-analysis/v1` 消费三信封；accepted 六态和 artifact 信息完整，rejected 未被提升为代码因果，not_applicable 已转固定版本运行时路径。
- [ ] 判断依据按信息价值排序、没有固定空洞套话，原则上不超过 800 字且可一眼定位服务和证据。
- [ ] 判断依据遵循共享证据链规则；Flow-only 仅作为 `evidence_blocked` 私有状态，并已停止渲染、转为具体权限 / 信息请求。
- [ ] “总体结论”只回答是否发现缺陷；无明确业务缺陷时只写“未发现缺陷。”且未输出缺陷列表。
- [ ] 报告开头没有任务元信息表，“总体结论”没有结论维度表；无明确业务缺陷时未输出“问题汇总”。
- [ ] 有明确业务缺陷时才在“总体结论”后输出独立“问题汇总”，且每项通过八项准入门禁。
- [ ] 报告标题下、“总体结论”上方只展示有效流量、DIFF 流量、缺陷、接口覆盖率和代码覆盖率；有效流量与缺陷数口径正确，缺陷卡始终为红色；不存在“报告概览”或“测试充分度”章节；两个空归因章节使用各自的明确空态文案。
- [ ] HTML 五项指标采用响应式卡片；接口覆盖率支持悬浮和键盘聚焦，摘要及逐接口四列表格口径正确；Markdown 不展开逐接口明细。
- [ ] 所有板块没有英文副标题，归因明细的全部字段名和值统一白底且没有专属高亮背景。
- [ ] 最终报告严格使用 canonical template 的章节名称、顺序和条目字段，未增加模板外章节。
- [ ] 私有 JSON 已通过 Schema shape、缺陷门禁、证据引用、数量对账、URL 和敏感信息校验。
- [ ] 最终文件由 `render-task-analysis.mjs` 生成；HTML 动态文本已转义，所有格式均无残留
      占位符，链接 scheme 与 `noopener noreferrer` 已校验。
- [ ] HTML 标题最右侧已展示蓝色“回放报告”链接，host 与任务地域一致，路径使用冻结的 `space_id` / `task_id`，且不包含原始查询参数或 fragment。
- [ ] 最终用户同时收到 `ftf-report.md` 和 `ftf-report.html`；私有 JSON 和敏感临时证据已清理。
- [ ] 首个 accepted/not_applicable 已绑定报告 metadata，后续 Analyzer 代码身份完全一致；已检查任务、PSM、仓库及代表 Flow 的 `base_commit` / `replay_commit` 身份一致性；`record_commit` 只作录制来源，Flow commit 未参与 Analyzer 版本解析。
- [ ] “问题汇总”中的每个缺陷都通过八项准入门禁，代码相关性为 `strong`，高低置信度均与证据完整性一致。
- [ ] 每个根因都有责任方、可执行动作和验收标准；证据边界说明了未闭环事实及其结论限制。
- [ ] 其他建议项均与当前证据直接相关，包含责任方、修改对象、具体动作和验收结果，无泛化凑数。
- [ ] 预期回放接口数等于目标 PSM 的 `replay_method_params` map key 数，非法或缺失类型未按 0 处理。
- [ ] 聚类已唯一分配给最多 20 个后台归因 worker；远程 API 并发单独限流，协调者已串行复核。
- [ ] 结束前已重新读取 `update_time`，确认分析快照未变化或已降级为部分归因。
- [ ] 所有敏感头和凭据已脱敏。
