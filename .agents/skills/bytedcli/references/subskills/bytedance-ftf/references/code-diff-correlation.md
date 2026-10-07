# FTF 与代码 Diff 关联判断

目录：[用途](#用途) · [Canonical Analyzer 路由](#canonical-analyzer-路由) · [非 canonical 本地 / MR 分析](#非-canonical-本地--mr-分析)

## 用途

当 FTF diff 需要判断“是否本分支代码引入”，或需要解释同一 commit 在不同任务执行输入下为何
进入不同业务分支，或用户提供本地 `git diff`、Codebase MR URL、commit、branch 时，使用本流程。

本流程只判断代码相关性，不替代 FTF 平台取证。先用 `task-diff-triage.md` 或 `flow-diff-root-cause.md` 拿到具体 method、diff path、base/replay 值和日志证据，并按 `diff-denoise.md` 完成随机值和数组乱序降噪检查；最终判断依据遵循 `diff-analysis.md` 的“归因证据规范”。可剔除降噪项不要继续硬找代码根因；待核验降噪候选可以保留为低权重线索。这些名称是降噪处理状态，不是 Finding 的 `confidence`；后者只允许“高 / 低”。
任务 URL 先按 `SKILL.md` 冻结站点；下列 ID-only FTF 示例固定为 cn，zg 使用全局前缀
`--site cn --vregion China-Pay`。裸 ID 未附站点时先索取，不得猜测。

## Canonical Analyzer 路由

当当前请求上下文已提供或可权威解析出 `task_id + similar_diff_id`，且任务要求判断字段 Diff
是否由 base→target 代码变更导致时，使用独立的 `ftf-code-analyzer`，不要执行本文件后面的
手工代码分析路径。

该路由只垄断 **base→target 代码变更因果**。FTF 只向 wrapper 提供冻结任务的 `task_id` 和与其
绑定的唯一 `similar_diff_id`；不得在委派前查询、比较或组装 repository、base revision、target
revision。Code resolver 是这些代码身份的唯一解析点，FTF 只对 canonical 返回值执行后置校验。

当前流程已进入任务归因或 DIFF 根因分析、目标身份唯一，且现有降噪检查未将该 DIFF 判为
“可剔除降噪项”时，必须调用一次 wrapper。待核验降噪候选、尚未定位根因、未发现代码候选、
日志不足或已初判为配置/平台问题均不是跳过理由。同一报告先按 `similar_diff_id` 去重，再按冻结
清单的稳定顺序调用，每个目标只调用一次。
Code resolver 无法从冻结任务解析出比较版本时，停止该分支并进入可恢复交互检查点：保留任务快照与已完成取证，
请求带来源的精确版本信息或取得 Flow 读取权限，待用户补充或授权后只重跑该受阻分支并继续。不得用任务级
`base_commit_hash` / `commit_hash`、base task、`record_commit`、target parent 或默认分支替代。

若 base/replay commit 完全相同，或当前问题明确是“同一版本为什么走不同运行分支”，则不存在待分析的
提交差异，不进入 canonical Analyzer；转入下文“同 commit 运行时路径分析”，结论只能表述为“任务输入
触发既有分支”，不得表述为“本分支代码变更引入”。

### 依赖能力

- Skill 名称：`ftf-code-analyzer`。
- 推荐 AgentBuddy 分发坐标：`skills:skills.byted.org/default/public/ftf-code-analyzer`；该坐标只用于
  定位制品，不是唯一来源，也不参与兼容性判断。
- 兼容性按能力判断：提供接受 `task_id + similar_diff_id` 的 canonical `run` 入口，并返回
  身份一致、满足六态与 artifact 完整性约束的 canonical JSON。版本仅用于部署追踪，不作为
  调用门禁；Analyzer 自行校验其运行依赖。
- `bytedance-ftf` 不包含 Analyzer 的脚本或二进制，安装、挂载与升级两者相互独立。普通
  FTF 查询、diff triage、计划管理和 Smart Access 不因 Analyzer 缺失而阻断。

查询并下载部署方选定的制品：

```bash
bytedcli --json --site cn agentbuddy skill get \
  --namespace skills.byted.org/default/public \
  --name ftf-code-analyzer

bytedcli --json --site cn agentbuddy skill download \
  --namespace skills.byted.org/default/public \
  --name ftf-code-analyzer \
  --version <selected-version> \
  --out <download-path>/ftf-code-analyzer.zip
```

`agentbuddy skill download` 只下载制品，不自动注册到当前 Agent。使用当前平台的 Skill
安装机制解压并激活，随后开启新会话；不要把某个宿主的 `/root`、`/opt` 或工作目录写成
公共固定路径。调用时优先使用平台已经解析出的 `ftf-code-analyzer` Skill 绝对目录。

### Readiness

运行前先确认：

1. 当前 Agent 能发现并完整读取 `ftf-code-analyzer/SKILL.md`。
2. Skill 提供上述 canonical `run` 输入与六态 JSON 输出能力。
3. `scripts/tool.py` 可读，Python `>=3.9`、Git 可用；其他运行依赖由 Analyzer fail closed 校验。
4. 当前站点的登录态、网络、任务权限和仓库权限由本次真实 `run` fail closed 验证，不通过
   假响应或第二次试跑预判。

Universal 受控模式不得用 `tool.py --help` 或 `tool.py run --help` 探测 readiness。包级检查
只验证依赖和上述能力存在；真正的 endpoint、鉴权、任务身份和 clone 能力交给标准 `run`。

### 普通模式调用

普通/直连模式先读取当前已加载 FTF 与 Analyzer 的 `SKILL.md`，使用其绝对目录调用 FTF
wrapper。路径是编排期内部参数，不得让用户填写，也不得从当前工作目录推断：

```bash
node <bytedance-ftf-dir>/scripts/run-code-analyzer.mjs \
  --analyzer-skill-dir <ftf-code-analyzer-dir> \
  --task-id <task_id> \
  --diff-id <similar_diff_id> \
  --site <cn|i18n-tt> \
  --vregion <China-North|Singapore-Central> \
  [--network <office|prod>]
```

`task-id` 来自冻结任务，`diff-id` 是当前唯一 `similar_diff_id`；同一报告先按 diff ID 去重，再按
稳定顺序逐个调用，每个目标只调用一次。地域必须来自冻结任务上下文：仅接受
`cn/China-North` 与 `i18n-tt/Singapore-Central`，未知、不完整、错配或 China-Pay 均直接拒绝。
wrapper 固定启动一次 `python3 <ftf-code-analyzer-dir>/scripts/tool.py run`，不传 repository、
revision 或 method，不重试、不扫描历史 artifact，也不回退手工代码归因。
普通模式不得绕过 wrapper 直接执行 Python Analyzer。

### Universal 受控模式

阶段 A 的兼容窗口内，已发布 Agent 仍可执行宿主注入的固定
`python3 <ftf-code-analyzer-dir>/scripts/tool.py run` 命令；该 legacy 路径不是普通模式的失败回退，
也不代表目标架构。Agent 完成阶段 B 后必须改为调用同一 Node wrapper。受控宿主在启动 wrapper
前删除继承的同名变量，只注入由当前 run 推导的 `FTF_PREPARED_CONTEXT_DIR` 和固定
`BYTEDANCE_FTF_WRAPPER_TIMEOUT_SECONDS=450`。wrapper 校验 workspace 为绝对、非符号链接、当前用户
所有且权限受限的目录，将 artifact 固定为
`<workspace>/task-<task_id>/result-artifacts/<similar_diff_id>/result.json` 并作为 `--output` 传给
Code；Code 超时仍为 300 秒，外层 Guard 保持 480 秒，任何一层都不重试。普通模式不设置这两个
变量，继续使用 wrapper 自有安全临时 workspace 和现有总超时。

### 结果与失败边界

wrapper 退出码为 0 时只接受 `contract_version=ftf-code-analysis/v1` 的
`accepted | not_applicable | rejected` 信封；唯一机器定义位于
`assets/schemas/ftf-code-analysis.schema.json`。未知主版本、未知状态、缺失必填字段或互斥字段共存均 fail
closed，v1 新增可选字段允许忽略。`accepted.analyzer_run` 写入当前 DIFF Finding 的
`analyzer_runs[]`；`rejected.evidence_boundary` 只写入该 Finding 或根级边界中的一处。
wrapper 已绑定进程终态、canonical stdout 与 artifact，并校验：

- stdout 读取前受 FTF 自有 64 KiB 硬上限保护；`projection` 的 strategy、实际序列化字节数和
  producer 自声明上限必须一致，自声明上限不得超过 FTF 硬上限。
- 请求 `task_id + similar_diff_id` 与返回身份一致，目标 `diff_results[]` 存在且唯一。
- stdout 允许新增展示或诊断字段；FTF 仅比较任务、聚合结论和目标 DIFF 的稳定核心字段，未知字段
  不参与准入，也不得传播到最终报告。
- artifact descriptor 的路径、bytes、SHA-256 与受控目录中的实际文件严格一致；repository、
  base/target revision identity 与目标分析一致。
- 每项 `analysis_state` 只能是 `invalid_observation`、`analysis_incomplete`、
  `evidence_blocked`、`proven_code_caused`、`proven_not_code_caused`、
  `runtime_unresolved` 之一，并满足对应状态对象的互斥约束。
- 对完整 artifact 校验对应状态专属对象、兼容 evidence 投影、`self_proof` 和 warnings；
  准入后的 `analyzer_run.result_artifact` 只保留 bytes 和 SHA-256，不得带出同宿主绝对路径；
  不得提升非终态、改写状态或用自然语言摘要覆盖 canonical 结果。

只有完成上述全部校验后，base 与 target 相等、状态为 `proven_not_code_caused`、verdict 为
`not_caused`、因果值为 `false`，且 `exclusion_proof.proof_type=revision_tree_delta_empty` 时，才输出
`not_applicable/no_revision_delta`。该信封保留 task、DIFF、repository、唯一 revision 和
`result_artifact {bytes, sha256}`，不包含 `analyzer_run` 或本地路径，并转入同 commit 运行时路径
分析。base=target 但证明不完整时返回 `rejected/state_contract_invalid`；base≠target 即使 tree diff
为空也继续输出 `accepted/proven_not_code_caused`。

依赖缺失、地域不支持、runner 失败/中断、stdout/identity/revision/六态/artifact 校验失败都返回
`rejected`，不是 Analyzer 第七态。wrapper 自身非零退出时，调用方生成 `[adapter_failed]` 的
material `EvidenceBoundary`；任何失败都不得伪造六态或回退到其他代码归因路径。
当 rejected 或 wrapper 失败可通过用户补充必要信息或申请代码仓库权限解除时，按 `SKILL.md` 的
interactive recovery checkpoint 进入 `awaiting_user_input` 或 `awaiting_authorization`；用户响应后校验
冻结版本与 task `update_time`，仅重跑该 Analyzer 分支，而不是把整单归因标为终止。

当前报告首个 `accepted` 信封以 `repository + base_ref + target_ref`、首个 `not_applicable` 信封以
`repository + revision` 建立代码身份，并回填现有 metadata；`not_applicable.revision` 同时写入 base/target
commit。后续信封必须与已绑定身份完全一致。冻结 PSM
仓库非空但不一致，或后续代码身份冲突时，生成 `[report_identity_mismatch]` material
EvidenceBoundary 并停止最终报告，不得覆盖 metadata。`rejected` 不提供报告身份；全部调用均为
`rejected` 时不得用 Flow commit 冒充 Analyzer 身份。

## 同 commit 运行时路径分析

base/replay commit 相同时，按以下顺序取证：

1. 用 `ftf psm get --psm <psm>` 冻结 PSM 与 Codebase 仓库绑定。
2. 从 task detail 读取 method 级 before/after script、请求头、参数和组件选择，明确 base/replay
   实际注入值；只有具体字段和值才构成任务执行配置证据。
3. 在该固定 commit 中定位消费这些值的函数、条件分支及响应组装路径，使用不可变 commit 的
   Codebase 行号深链。
4. 用代表 flow 的 `logid_comparison` 查询任务时间窗日志 / Trace，确认实际命中的模式、分支、
   组件或返回路径。若冻结输入与固定代码已唯一决定路径且没有外部状态参与，可直接闭环；若路径
   受 TCC、实验、缓存、下游返回或其他运行时状态影响，日志不可得时只能证明设计机制，不能声称
   代表流量已命中。
5. 用一个代表 response / Flow DIFF 闭合结果证据，并明确这不是代码提交差异。

任务执行配置与固定提交源码能够唯一决定路径、且无外部状态参与时，可以形成配置驱动的机制
结论；若路径仍受 TCC、实验、缓存或下游结果影响，必须取得对应运行时证据，否则降级为未闭环。

## 非 canonical 本地 / MR 分析

以下章节只适用于用户明确提供本地 workspace、MR、commit 或 branch，且当前请求上下文无法
权威获得满足 base→target 字段因果判断所需的 `task_id + similar_diff_id`。它不限制上一节的
同 commit 运行时路径分析。

### 先确认任务绑定代码

代码关联判断前，必须确认：

- 任务形态是什么：系统级、沙箱，还是不确定/混合（判定依据见 `domain-model.md#任务形态判定`，需输出字段依据）。
- baseline 是什么：基准任务、基准 commit、master/main，还是平台默认基线。
- replay 绑定的 branch/commit 是什么。
- PSM replay 参数里的 commit、env、replay cluster、IDL version 是否与用户预期一致。
- 顶层 `code_branch` 为空时，不要直接判定未绑定分支；有些任务会把 commit 写在 PSM replay 参数里。
- 任务结果是否包含能证明回放产物、env、replay cluster 或 logid 错误的证据。任务结果没有展示的 record/ftf bin、启动条件、覆盖率脚本、环境变量，不能作为代码关联判断的已验证前提。

常用复查：

```bash
bytedcli --json --site cn ftf task get --id 1234567
```

需要从任务返回里抽取 PSM replay 参数时，优先保留原始 JSON 证据，再摘出顶层 `env`、`commit_hash`、`base_commit_hash`、`replay_env`、`base_replay_env`、`replay_cluster`、`idl_version`、`code_branch`、`inherited_branches`、`base_task_id`，并统计 `replay_method_params.*.mock_enable`。这些任务级字段用于非 canonical 任务形态与运行路径分析，不得作为 canonical Analyzer 的 base/target 版本源。

任务形态会影响代码版本证据的解释（形态判定依据见 `domain-model.md#任务形态判定`）：

- 系统级任务：base/replay 在两个真实代码环境比较 response，重点关注 `base_commit_hash`、`commit_hash`、`base_replay_env`、`replay_env` 是否完整且符合预期。
- 沙箱任务：入口回放 + mock outbound，`base_commit_hash` 可能为空，不要仅凭 base commit 缺失判定元数据异常；优先结合 `code_branch`、`inherited_branches`、`base_task_id` / `base_task_id_realtime` 和 outbound request diff 建立代码相关性。
- 不确定/混合：说明本次代码关联只覆盖已分析 method 的证据。

base commit 缺失只表示不能证明 base→target 代码变更因果。只要 target commit 可冻结，仍必须分析固定
target commit 中的入口、字段生产、默认值、提前返回和调用链；需要外部状态才能确认实际分支时，再用
replay LogID 的任务时间窗日志 / Trace 闭环。不得因为 base commit 为空而跳过 target 代码分析。

### 获取代码 diff

本地仓库场景：

```bash
git status --short
git diff --stat
git diff -- path/to/file.ts
git show <commit> --stat
git show <commit> -- path/to/file.ts
```

Codebase MR 场景：

```bash
bytedcli --json codebase mr diff 821 -R "example-org/example-repo"
bytedcli --json codebase mr diff 821 -R "example-org/example-repo" --file "path/to/file.ts"
```

如果命令不可用或参数不确定，先查 `bytedcli codebase mr --help`，不要猜测新的 codebase 命令。

### 从 FTF 证据反推代码区域

按以下线索缩小范围：

- method / RPC 名称：找 handler、service、IDL adapter、assembler、mapper。
- diff path：找字段定义、字段组装、默认值、过滤条件、排序逻辑。
- replay err_msg：找抛错位置、状态机分支、下游调用封装。
- outbound diff：沙箱任务里重点找下游请求参数构造、protocol/method 变化、调用次数变化、调用条件、fallback 逻辑。系统级任务通常不期待 outbound diff，不要因为没有 outbound 就降级为证据缺失。
- request 差异：先确认是否输入不同；输入不同通常不能直接归因到响应逻辑。
- context 相关风险：可以在代码 diff 中识别协程池、异步任务、context.Background、没有透传 request context 的调用路径；但是否真实导致本次任务 mock 缺失，需要任务日志或外部验证。
- 请求外状态风险：可以在代码 diff 中识别 TCC AddListener、localcache、全局变量、singleflight、异步预热和 BOE 特殊逻辑；是否命中本次 case 需要任务证据支持。

不要只用文件名相似或字段名相同下结论。需要看到代码变更与 FTF 证据之间有可解释的因果链。

### 相关性等级

| 等级        | 使用条件                                                                                                                               |
| ----------- | -------------------------------------------------------------------------------------------------------------------------------------- |
| strong      | 代码 diff 直接修改了对应 method、字段 path、排序/过滤/默认值或下游请求，且 FTF base/replay 差异与修改方向一致                          |
| possible    | 代码 diff 命中相关模块，或改变了 outbound 请求参数/次数/context 透传，但缺少字段级或日志级证据，需要补查 flow/logid 或补充本地单测     |
| weak        | 代码 diff 只在邻近模块，FTF 证据不足以连接到字段差异；采集源、环境、mock、配置、localcache、TCC 异步或 singleflight 等方向缺少任务证据 |
| no evidence | 已查相关代码路径，未见能解释 diff 的改动；仍需说明检查范围                                                                             |

### 结论边界

- 不能只凭 FTF value diff 说“代码问题”；必须说明代码 diff 如何改变该字段、下游请求或业务分支。
- 不能只凭代码 diff 排除环境问题；如果 mock、DB、缓存、TCC、实验或 IDL 证据不完整，要保留验证项。
- 如果 base/replay 都成功且只是数组顺序变化，先按 `diff-denoise.md` 检查元素集合、业务主键和排序后匹配结论，不要直接判回归。
- 如果 replay 失败来自环境资源缺失、mock 未命中或状态污染，代码相关性通常是 `weak` 或 `possible`，除非本分支改变了资源 key、请求参数、调用次数或 context 透传。
- 如果沙箱任务 outbound mock 失败，先按匹配规则解释：录制侧是否有同 protocol/method 的 outbound、请求参数是否 diff、候选是否已被使用、回放调用次数是否增加。只有这些变化能被代码 diff 解释时，才提高代码相关性等级（此逻辑仅适用于沙箱任务）。

### 输出要求

代码关联结论至少包含：

- FTF 证据：method、diff path、base/replay 值、logid 或 outbound 摘要。
- 任务形态证据：系统级 / 沙箱 / 不确定，顶层 `env`、`replay_env`、`mock_enable` 统计、base/replay commit 获取情况。
- 代码范围：本地 diff、MR diff、commit，检查过的文件/函数。
- 相关性等级：strong / possible / weak / no evidence。
- 因果说明：代码变更如何解释或不能解释 FTF diff。提供固定 commit 的 Codebase 文件行号深链，说明代码变更如何改变执行路径；有运行时
  证据时紧接 LogID / Trace 深链和关键词，再以回放响应 / 字段 DIFF 闭合结论。FTF 详情页只作
  现象入口，不能替代代码或日志证据。
- 后续验证：需要补充的日志、重跑、单测、配置确认或平台环境动作。
