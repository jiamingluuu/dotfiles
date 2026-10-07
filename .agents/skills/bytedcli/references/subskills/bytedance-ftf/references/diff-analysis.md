# FTF Diff 分析编排(总流程)

目录：[用途](#用途) · [分析原则](#分析原则) · [标准流程](#标准流程) · [归因证据规范](#归因证据规范) · [报告表达规范](#报告表达规范) · [报告结构](#报告结构) · [常见误判](#常见误判)

## 用途

当需要完成一次 FTF diff 归因时读本文件。它定义**分析顺序、证据分层、报告结构**,
是把降噪 / triage / 单条根因 / 代码关联串起来的编排层。

- 领域背景(录制回放、任务形态、术语、证据可见性)见 `domain-model.md`。
- 一次请求该先打开哪个文件,由 `SKILL.md` 的 dispatch 表决定;本文件只负责
  "一次完整归因按什么顺序跑完"。
- 降噪见 `diff-denoise.md`;单条根因见 `flow-diff-root-cause.md`;
  代码关联见 `code-diff-correlation.md`;命令参数见 `diff-query-reference.md`。判断依据的证据角色、
  因果链、深链和降级规则由本文件的“归因证据规范”统一定义。
- 需要聚合整个任务并输出缺陷、DIFF 归因分析、回放失败归因分析和其他建议项时，转入
  `task-analysis.md`；单个 DIFF 的代码证据仍使用本文件定义的 canonical
  `ftf-code-analyzer` 路由。

## 分析原则

- 先取证再下结论。至少确认任务上下文、diff 类型、base/replay 两边表现,再给根因判断。
- 默认只做只读查询。FTF plan execute、task retry、task stop 都是写操作,必须等用户
  明确确认后再执行。
- 机器可读结果默认用 `bytedcli --json ftf ...`,并把 `--json` 放在 `ftf` 前面。
- 结论分层表达:已证明事实、基于事实的推断、仍需验证项。
- 不要只凭 `need_confirm_count`、平台标注、单个错误字符串或代码 diff 直接断言根因。
- FTF Flow / DIFF 页面只证明输入输出和差异现象，不能单独证明根因机制。根因结论应由业务代码
  行为、日志 / Trace、配置 / 部署或可复验的请求响应机制支撑；缺失时明确证据缺口并降为低置信。
- 不要把 outbound 缺失一律当成业务回归。形态与证据可见性判断见
  `domain-model.md#任务形态判定`、`domain-model.md#采集源与证据可见性边界`。
- 下列 ID-only 示例固定为 cn；若 ID 来自 URL，先按 `SKILL.md` 冻结站点并替换前缀：zg 使用
  `bytedcli --json --site cn --vregion China-Pay ftf`。裸 ID 未附站点时先索取，不得猜测。

## 标准流程

先判断任务形态(依据见 `domain-model.md#任务形态判定`),再按下列顺序推进。
四个子分析各引对应 L1,**顺序固定:triage → 降噪 → 单条根因 → 代码关联**。

1. **[准备] 收集上下文**:用 `bytedcli --json --site cn ftf task get --id <task_id>` 读顶层
   `env`、`psm_replay_param(_detail)` 里的 `replay_env`、`base_replay_env`、
   `commit_hash`/`base_commit_hash`、`code_branch`、`inherited_branches`、`base_task_id`,
   并统计 `replay_method_params.*.mock_enable`;据此判断系统级/沙箱/混合形态并记录依据。
   对每个目标 PSM 再执行 `bytedcli --json --site cn ftf psm get --psm <psm>`，用 PSM 元数据
   解析 Codebase 仓库。保留 method 的冻结 before/after script 和实际执行参数；能明确解析出的
   base/replay header、参数和组件选择属于任务执行配置证据。
2. **[准备] 跑统一证据包**:`bytedcli --json ftf task evidence get --url "<ftf-task-url>"
--top-n 10 --sample-size 3`,作为 task meta、汇总统计、top method、top diff 聚类和
   代表样本的共同事实来源。URL 带 `diffReasons` 时 CLI 自动应用筛选,不要再传
   `--annotation-op-type unannotated` 覆盖。
3. **[triage] task 级 triage**(详见 `task-diff-triage.md`):不能只输出任务状态或
   "初步分析";必须进入 diff 聚类内容,覆盖当前轮应分析的聚类 path、代表流量、
   两侧值/差异形态、降噪依据或根因假设。
4. **[triage] 确定分析范围**:按当前 URL / 显式参数圈定主线集合,引用 JSON 的
   `annotationOpTypeSource` 说明筛选来源,再按 method、direction、标注状态拆分。
   默认口径未处理聚类;阈值在单个 method 内计算——待分析聚类 ≤10 全覆盖,>10 当前轮
   详析 Top 10 并摘要剩余。不同 method 可用 subagent 并行,但共用同一份证据包和筛选口径。
5. **[回放有效性] 检查单条失败状态**:对代表 Flow 用 `task flow get` 读取
   `data.diff.failed_reason`。非零时按下方“分支切换和退出边界”转入 replay-failure 成员归因；
   零或字段缺失时继续当前 DIFF 链路，字段缺失须记录证据边界，不得猜测为零。
6. **[降噪] 降噪检查**(详见 `diff-denoise.md`):对已圈定的 cluster,进入
   根因归类**前的强制前置步骤**。随机值候选用 `ftf diff path-profile get` 看跨流量
   base/replay 分布;数组乱序候选用 `ftf diff array-check get`。可剔除降噪项可从主根因
   链路剔除;待核验降噪候选只降权,仍参与后续分析。这些是降噪处理状态，不得写入
   Finding 的 `confidence`;该字段只允许“高 / 低”。
7. **[根因] 单条 flow 根因分析**(详见 `flow-diff-root-cause.md`):对代表性 case 拉
   base/replay value、request/response、outbound、similar case、replay logid。按该 Reference 的
   [错误症状前置分流](flow-diff-root-cause.md#错误症状前置分流)识别候选，只调整取证优先级，
   不用错误文案直接判断环境、Mock、依赖或代码根因。
8. **[代码关联] 执行代码关联**(详见 `code-diff-correlation.md`):当前流程已进入 DIFF 根因分析、
   已取得与任务绑定的唯一 `task_id + similar_diff_id`，且降噪结论不是“可剔除降噪项”时，调用
   一次 FTF wrapper；待核验降噪候选、尚未定位根因、未发现代码候选或日志不足均不是跳过理由。
   wrapper 不接收 FTF 组装的仓库或 revision，由 Code resolver 唯一解析。只消费
   `ftf-code-analysis/v1` 三信封：`accepted` 保留六态，`rejected` 保留证据边界，
   `not_applicable/no_revision_delta` 转入固定版本源码与 replay 日志的运行时路径分析，不得据此
   声称既有代码或运行时状态与 DIFF 无关。
9. **[跨服务追踪] 定位字段生产者和首个代码分歧点**:入口仓库未命中字段名、只命中通用
   透传或只看到最终响应组装时，不能停止归因。必须从代表流量的 replay LogID 沿 Trace 逐跳检查
   下游 PSM，找到字段首次出现、首次改变或首次丢失的 span；再冻结该 PSM 在任务时间窗内的运行
   版本及对应不可变 commit，定位字段生产、转换和传输代码。随后沿返回链检查入口服务的消费代码，
   比较旧、新路径对同一中间值的读取方式，确定第一个能够预测最终 DIFF 的代码分歧点。
10. **[输出] 输出分层报告**，把证据组织为“代码或配置机制 → 日志 / Trace 运行时印证 →
   回放响应 / DIFF 结果”的因果链。代码链接直达不可变 commit 的文件行号，日志链接直达对应
   LogID / Trace 和时间窗；FTF 详情链接只作为代表性现象证据，不得替代前两类链接。

分支切换和退出边界：

- 单条 `task flow get` 的 `data.diff.failed_reason != 0` 时，退出依赖
  `task_id + similar_diff_id` 的 canonical Analyzer，切换到 `diag-replay-failure.md` 的成员归因。
  这不是停止根因分析；仍须核实脱敏错误摘要、回放状态码、任务时间窗日志，以及能取得的
  request/response、outbound、配置、部署和固定版本代码证据。任务级计数或 method 聚类键不能替代
  单条 `data.diff.failed_reason`。
- 只有已按 `diff-denoise.md` 证明可剔除的降噪项可以退出当前 DIFF 主根因链路。待核验候选仍须
  继续分析；不能因“像环境问题”“像 Mock 问题”或症状候选而跳过现有代码关联边界。

## 归因证据规范

任务级归因、单条 DIFF 根因和回放失败分析共用本节。判断依据的目标是用最少文字解释
“什么机制改变了执行路径、运行时如何印证、最终产生了什么响应或 DIFF”，而不是罗列查询链接。

证据按其实际证明力使用：

- **代码**：定位业务服务、不可变 commit、文件行号、函数或分支，并说明该逻辑如何改变执行路径。
- **日志 / Trace**：定位服务、任务时间窗、LogID / TraceID 和决定性关键词，证明实际进入了哪条路径。
- **请求 / 响应 / Flow**：证明相同输入下的状态码、返回值或字段 DIFF，只承担现象和传播结果证据。
- **配置 / 部署**：证明任务时间窗内生效的配置值、环境身份或部署版本，承担非代码机制证据。
- **任务执行配置**：冻结任务中的脚本、请求头、参数或组件选择，证明 base/replay 被注入的实际
  输入；必须列出具体字段和值，并与固定 commit 的消费代码对应，不能用任务描述代替。
- **证据边界**：记录应有证据为何不可得、它限制了什么结论，以及唯一可执行的补证动作。

根据实际证据，自然串联“代码或配置机制 → 日志 / Trace 运行时印证 → 回放响应或字段差异 →
根因结论”。不适用的环节直接省略，不要求固定句式、固定段数或机械罗列“事实 / 推断 / 待确认”。
代码证据应尽可能直达 Codebase 不可变 commit 的文件行号；日志和 Trace 应尽可能直达对应查询结果，
并在链接旁写明服务、时间窗、标识和决定性关键词。平台明确没有可分享链接时保留标识、时间窗与
决定性内容，并将 URL 置空；不得猜测链接，也不得把 FTF 任务页、DIFF 页或 Flow 页登记为日志 /
Trace 链接。只有至少存在一项代码、日志 / Trace、历史配置或部署机制证据时，才允许
在判断依据的链路末端保留一个代表 Flow 作为结果印证；其余 Flow 只放“流量样本”。

“判断依据”是支持根因结论的论证，不是现象复述或取证过程说明。Flow / DIFF 现象、聚类统计、
平台标注、证据缺口和补证动作均不能单独进入“判断依据”。没有根因机制证据、无法形成证据链时，
该字段写“当前没有能证明根因的直接证据。”。具体排查结果只保留在私有结构化数据中；受阻原因和
补证动作放在“处理建议”中。证据缺口继续用于降低置信度、约束缺陷准入和生成具体建议。最终报告
不得展示“定位过程”字段。

FTF Flow / DIFF 页面只证明请求、响应、字段差异或失败现象，不能单独证明业务代码、运行时或
配置根因。只有 Flow 证据时，必须在私有结构化数据中将调查状态置为 `evidence_blocked`，增加
`material=true` 的 `evidence_boundary`，并逐成员记录获取尝试、阻塞原因和唯一补证动作；不能用更多
FTF 链接填补证据缺口。无法取得可靠深链时不得伪造，也不得用任务首页替代。该状态不得渲染为最终
报告，必须直接向用户提出具体权限或信息请求。
配置或部署只有在证据包含具体服务、配置项或部署对象、任务时间窗内实际生效值、机制说明和
对应平台深链时，才能进入判断依据；任务场景名、任务描述、当前快照或任务首页不能作为机制证据。

入口服务源码搜索无命中不是证据边界，而是跨服务追踪的起点。字段可能由下游 RPC、组件服务、
缓存或标准化层生产，也可能以 map key、序列化字符串或别名传递。此时按以下顺序闭环：

1. 用 replay LogID 打开任务时间窗 Trace，列出实际经过的下游 PSM，并检查各 span 的请求、响应或
   结构化日志，定位字段值首次出现、改变或消失的位置。
2. 将该 PSM 映射到代码仓库，取得任务时点运行版本及对应不可变 commit；当前 master、当前部署或
   入口仓库的同名搜索结果均不能替代任务时点身份。
3. 在固定 commit 中分别定位生产、传输和消费代码。对 map / LogExtra / JSON 字符串必须核对原始 key
   的每个字符、类型后缀和编码，不得只做近似关键词搜索。
4. 比较 base/replay 或旧/新组件如何消费同一个中间值，找出首个会导致两侧结果不同的代码分歧点；
   双跑或对比框架只解释“为何能看到差异”，不自动等于字段根因。
5. 用 Trace 中间值验证代码预测，再用一个代表 Flow 验证最终结果。代码预测、中间值和最终 DIFF
   三者不一致时，结论仍为“现有证据不足，尚不能确认根因。”，不得选择其中两项拼成根因。

同一 commit 下允许形成 `strong` 运行时代码归因，但门槛不低于跨提交归因：任务目标身份必须固定，
至少有一条任务时间窗日志 / Trace 证明真实路径，生产与传递、消费与影响均有证据，且已定位能预测
最终结果的首个代码分歧点。此路径不需要、也不得伪造 `proven_code_caused` Analyzer 结果；base 和
replay commit 不同时，仍严格使用 canonical Analyzer 证明代码变更因果。

聚类清单中的“详情链接”只证明分析覆盖和提供现象复核入口，不属于根因机制证据。最终判断依据
不能直接复制聚类清单，必须把聚类的代码、配置、部署、日志 / Trace 和响应证据重新组织成可复核的
因果链；无法组织时写“当前没有能证明根因的直接证据。”。完成前检查：读者能直接定位服务、代码行或运行时查询；
各类证据没有越权证明；同类证据已去重；证据缺失会降低结论强度，而不会被现象复述、链接数量、
平台标注、错误码目录或补证说明掩盖。

“现有证据不足，尚不能确认根因”只能是关键证据入口已实际检查后的结果，不能是提前停止的理由。
对代码、日志、Trace、响应、历史配置和部署六类入口逐项记录 `available`、`checked`、
`evidence_ids`、`acquisition_attempt`、`blocker`、`recovery_action` 与 `outcome`：可访问或已有 selector 的入口视为
available；只有实际查询并检查了与本聚类相关的结果才是 checked；不可用入口必须记录真实获取尝试、
具体阻塞和唯一恢复动作。调查成员以 `source_type + source_id` 作为唯一身份；`checked=true` 必须引用类型匹配的成员级证据；代码、日志和 Trace 证据的 `member_refs` 必须反向包含同一成员，日志 / Trace 还必须绑定该成员的真实 Flow ID，共享证据必须逐项声明覆盖成员；代码引用必须匹配任务 target
PSM、仓库和 commit，响应引用必须匹配成员及其 Flow。任何 `available=true, checked=false` 都表示分析未完成。任一成员没有实际
检查目标提交代码，或没有检查任务时间窗日志 / Trace 至少一项时，状态必须为 `evidence_blocked`，
禁止进入报告并直接请求权限或信息。入口服务未命中、平台智能归因为空、Analyzer 无代码变更或第一条
日志无关键词，都只会改变下一步搜索位置，不会完成归因。只有上述关键证据已实际检查、其余适用入口
也已查尽但仍无机制证据时，才允许使用 `exhausted_unresolved`、低置信度以及
“现有证据不足，尚不能确认根因。”。

## 报告表达规范

术语的用户可读译法见 `domain-model.md#术语与表达规范`;本层只规定报告怎么写:
正文面向业务研发 / 业务测试同学,优先用可读说法,内部字段名只放命令清单、证据附录
或括号说明。

单 DIFF / Flow 的用户回复必须让以下六类语义可定位：当前结论、已确认现象、已验证证据、证据边界、
下一步动作、状态说明。它们是内容契约，不是六个固定标题、固定段数、JSON 中间协议或任务级 renderer
模板；可按上下文合并为表格或自然段。状态说明须分别表达本次执行进度与当前结论是否可消费，
不得把“可消费”改写为证据已闭环。已检查且确实不存在的对象写明检查范围；尚未取得的证据写明
缺失原因、判断影响和唯一恢复动作，不能使用裸“无”“暂无”或“未知”占位。material evidence boundary
按 `SKILL.md` 的可恢复交互检查点暂停最终报告，不把编排层的 `awaiting_user_input` 或
`awaiting_authorization` 写入报告状态。任务级 canonical 报告继续使用 `task-analysis.md` 的现有契约。

推荐表达:

```text
`/demo/method` 的 `data->items->[*]` 覆盖 75 条流量,累计记录 3348 条 diff 明细。这个明细条数会受数组元素数量影响,只用于说明规模,不代表 3348 个独立问题。可通过具体 diff 链接确认:<diff-link>。
```

避免表达:

```text
similarDiffId=xxx,diffCount=3348、logCount=75。
```

如果查询结果或用户输入中有可打开的 diff / flow 直达链接，只为代表性响应或字段差异附一个
“详情链接”；没有可靠链接不要编造，只提供 task URL、接口、path 和代表 log_id。task 级报告里，
其余 Flow 链接放入“流量样本”，不在“判断依据”堆叠。代码和日志应优先使用各自平台的精确
深链，生成规则见 `diff-query-reference.md` 的“Flow diff 链接拼接”。

## 报告结构

默认使用以下结构,按证据多少压缩或展开:

```text
结论摘要
- 当前判断:<系统问题 | 环境/平台问题 | 业务变更 | 疑似代码引入 | 证据不足>
- 影响范围:<task/method/cluster/case 数>
- 分析范围:<主线筛选口径、各 method + 方向待分析 diff 聚类数、全量覆盖或 Top 10 截断、剩余未分析数量>
- 优先级:<先看哪些 cluster 或 case>

任务与输入
- task / flow / record / MR / commit
- PSM / method / env / branch / commit / psm_task_id
- 任务形态:<系统级 | 沙箱 | 不确定/混合>,以及顶层 env、replay_env、mock_enable 统计、base/replay commit 获取情况

关键证据
- 任务 / PSM / 接口汇总统计
- 聚类级结论:每个已分析 diff 聚类单独一行,包含接口、方向、path、命中流量数、累计 diff 明细条数、标注状态、代表流量详情链接、降噪判断和当前判断
- FTF diff path、base/replay 值、状态码、错误信息
- request/response、outbound、similar case、logid 日志
- 代码 diff 命中的文件、函数、字段或分支

降噪判断
- 可剔除降噪项:
- 待核验降噪候选:
- 不应降噪:
- 证据不足/待补充:

根因分析
- 逐条聚类结论之后,再输出任务级归纳;任务级结论不能替代聚类级结论
- 已证明事实
- 基于事实的推断
- 仍需验证项

建议动作
- 是否需要继续查某条 flow
- 是否需要代码确认或修复
- 是否需要平台清理、mock 补齐、重跑、降噪或外部确认
```

## 常见误判

- 把平台已标注噪声当成当前待处理 diff。筛待确认时要排除 `not_mark=true` 或已标注原因的记录。
- 把随机值或 order-only diff 当成业务回归。随机值要同时看跨流量分散和字段语义;数组乱序要基于两侧明细、稳定业务主键和排序语义判断。
- 把 replay 日志中的业务错误直接判为代码问题。需要结合任务结果里的 request/response、mock、下游和本分支代码改动;任务结果没有覆盖的环境前提只能列为待验证。
- 把 task 顶层 `code_branch` 为空当成没有绑定分支。有些任务只在 PSM replay 参数里记录 commit。
- 忽略 FTF 回放流量标识。回放 HTTP header / RPC extra 会带 FTF tag 和 task id,业务代码可能基于这些标识走不同逻辑。
