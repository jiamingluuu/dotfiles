# FTF Task Diff Triage

## 用途

当用户给出 FTF task URL、task id，或要求分析一批 diff cluster 时，使用本流程。目标是从任务总览中找出最值得深挖的 method / cluster / case，并给出优先级。

查询命令参数见 `diff-query-reference.md`；降噪检查、分析编排和根因判断依据见 `diff-analysis.md`；单条根因见 `flow-diff-root-cause.md`。

## 目录

- [快速路径](#快速路径)
- [任务结果可见性边界](#任务结果可见性边界)
- [分析范围规则](#分析范围规则)
- [优先级规则](#优先级规则)
- [选择代表性 case](#选择代表性-case)
- [聚类详情链接](#聚类必须附查看-diff-明细链接硬性完成标准)
- [单条根因分析](#何时进入单条根因分析)
- [Task 级输出](#task-级输出)
- [推荐分析模板](#推荐分析模板)

## 快速路径

```bash
# 1. 解析 URL，确认 task selector。
bytedcli --json ftf target parse --url "<ftf-task-url>"

# 2. 冻结解析出的 site。以下为 cn；zg 使用 --site cn --vregion China-Pay。
bytedcli --json --site cn ftf task get --id 1234567

# 3. 获取 Tesla-X task 上下文和 PSM task id 映射。
bytedcli --json ftf task evidence get --url "<ftf-task-url>" --page 1 --page-size 20

# 4. 列出高频 diff cluster。task URL 带 diffReasons 时会自动应用页面筛选；否则默认可按需显式加 --annotation-op-type。
bytedcli --json ftf task diff-cluster list \
  --url "<ftf-task-url>" \
  --direction all \
  --sort diff-count-desc \
  --top 20

# 5. 对 top cluster 串联 value diff 和相似 case。
bytedcli --json ftf task analyze \
  --url "<ftf-task-url>" \
  --direction inbound \
  --with-values \
  --sample-values 3 \
  --with-similar-cases \
  --top-n 10
```

URL 命令自身会自动派生站点。工作流仍须将解析结果与用户明确声明的目标站点对比，如不一致，
在任何派生 ID 查询前停止；后续所有 URL→ID 查询都显式复用冻结路由。输入只有裸 ID 且未给
站点时先索取，不从 ID、默认配置或任务字段猜测。

如果用户已经指定 method，所有 task 级查询都带上 `--method <method>`，避免把无关方法混入结论。

## 任务结果可见性边界

task 级 triage 只能分析任务结果中**可见**的证据，不要要求 Agent 通过 FTF task 结果之外的渠道自行确认。任务形态判定（系统级 / 沙箱 / 混合）、系统级 vs 沙箱的 outbound 期待、`bytecopy` / `sdk` 采集源差异，以及“结果未展示即列为外部待验证项”的原则，统一见 `domain-model.md#任务形态判定` 与 `domain-model.md#采集源与证据可见性边界`。

triage 场景补充：如果整批 case 都没有 outbound mock 数据，只能说“任务结果缺少 outbound 证据”，把采集源限制、产物启动、组件支持、context 透传等列入外部待验证项，不要写成 mock 失败结论。

## 分析范围规则

先明确“待分析 diff 聚类集合”：默认按用户当前 URL 或显式参数对应的筛选范围作为报告主线；CLI 会自动应用 task URL 里的 `diffReasons`，报告中需要引用 JSON 的 `annotationOpTypeSource` 说明筛选来自 URL、显式参数还是默认未处理。用户未指定 annotation scope 且 URL 没有筛选时，先看未处理或待确认的 diff 聚类，同时保留已标注高风险项摘要。报告中可以同时列出全部聚类数、未处理聚类数、待确认流量数，但不要把这些口径混成一个数字。这里的“待分析 diff 聚类数”指筛选后的 diff 聚类数量，不是 `diffCount`、`logCount`、累计 diff 明细条数或命中流量数。

- 用户要求分析 task 时，完成标准不是“拿到 task evidence”或“输出初步分析”，而是已经进入 diff 聚类内容：每个当前轮覆盖的聚类都要有 path、代表流量、两侧值/差异形态、降噪依据或根因假设。
- 阈值按单个 method 单独计算，不要把整个 task 的聚类数跨 method 合并后决定是否分层。
- 默认口径是未处理聚类；如果 URL 或显式参数选择了已标注/全部聚类，就以该筛选后的聚类集合作为当前轮待分析集合。
- 单个 method 下当前轮待分析 diff 聚类数不超过 10 个：该 method 的所有当前轮聚类都要默认覆盖，不需要用户额外强调“全部分析”。覆盖不等于每个都同等深挖；高风险项做详细分析，明显降噪项给出降噪依据，已标注且证据充分的低风险项可摘要说明。
- 单个 method 下当前轮待分析 diff 聚类数超过 10 个：当前轮只详细分析该 method 的 Top 10 聚类；剩余聚类要按 path/direction/标注状态做摘要，明确还剩多少个未逐个分析、为什么没有展开，以及用户追问时会从下一批继续。
- 用户明确要求“全部分析”时，即使超过 10 个，也要分批覆盖；如果证据量过大，先输出已完成部分和剩余批次说明。
- 不同 method 的 diff 可以使用 subagent 并行分析，但每个 subagent 必须基于同一份 `task evidence get` 结果、同一 URL/显式参数筛选口径和相同术语规范，避免各自绕不同命令得出不可比较结论。

## 优先级规则

本节前半部分只决定调查顺序；最终任务级报告中的 P0～P3 必须按 `task-analysis.md` 的统一口径
判定，并且置信度只允许“高 / 低”：

| Finding 原因 | 高置信度 | 低置信度 |
| ------------ | -------- | -------- |
| 业务缺陷     | P0       | P1       |
| 预期变更     | P2       | P1       |
| 噪音         | P2       | P1       |
| FTF平台问题  | P3       | P2       |

命中量和影响范围只能帮助安排先查哪一项，不能改变最终报告优先级。

详细分析优先覆盖这些 diff 聚类：

- 命中流量数最高，且未标注原因。命中流量数优先于累计 diff 明细条数，更接近真实影响面。
- 累计 diff 明细条数很高，且不是纯数组元素数量放大。数组 path 的明细条数要结合元素数量解释，不能直接当成独立问题数。
- replay 成功但字段值不同，通常更可能需要业务或代码确认。
- replay 失败且错误码、err_msg、logid 指向具体业务路径。
- 沙箱任务中的 outbound diff 指向关键下游依赖、mock 缺失、请求参数变化、调用次数变化或返回体结构变化。
- 请求参数 diff 导致 outbound 匹配变化，说明回放对外请求和录制请求已经不一致；系统级任务里没有 outbound diff 时不适用这条。
- 同一 diff path 覆盖多个 case 或多个相似 case，说明不是单条流量偶发。

可以后置或单独标记这些 diff 聚类：

- 已被平台标为噪声、低风险、case-noise、big-json 等，且用户没有要求复核标注。
- 疑似随机值 diff 或数组顺序变化。先按 `diff-denoise.md` 判断降噪处理级别；只有可剔除降噪项才从主根因链路剔除。
- 仅出现在少量 case，且缺少 replay 错误、字段 path 或相似 case 支撑。
- 系统级任务的 outbound 缺失通常不是问题。沙箱任务 outbound 缺失且任务结果没有说明采集源或 mock 匹配状态时，先标记为证据不足而不是 mock 失败。

## 选择代表性 case

对每个需要深挖的 diff 聚类，内部取证至少记录：

- `similarDiffId` / `diffId` / `similarCaseId`
- method、direction、diff path、diff reason
- 代表性 record、pid、base logid、replay logid、replay status code
- `task_diff_incr_id`，用于后续 `ftf diff value`
- 用于根因合并的现象指纹：响应状态/错误码、base/replay 值形态、首个候选责任 PSM。每个原始
  聚类保留独立 source ID 和所属 Flow ID，不能把另一聚类的代表 Flow 混入。

根因合并发生在逐聚类分析之后，且只能合并因果机制、责任 PSM、修复点、预期性一致的成员。
根因已经证明时，允许同一机制跨接口产生不同但因果兼容的表现；根因尚未定位时只能合并现象指纹
同质的成员，不能以“暂未定位”作为合并键。
尚未定位根因时门槛更严格：方向/阶段、响应签名、值形态和候选责任 PSM 也必须一致；鉴权提前
返回、Mock 未匹配、配置分支、动态字段、数组变化或对象缺失不能因为都“证据不足”而合并。
同一鉴权机制可以跨接口合并，但每个成员仍保留自己的聚类和 Flow 归属供最终校验。

面向用户描述时，不要把 `similarDiffId` 放在正文主语里。优先使用：

```text
<method> 的 <diff path> 覆盖 <N> 条流量，累计记录 <M> 条 diff 明细。<M> 是平台记录的字段级差异条数，数组 path 会被元素数量放大，不代表 <M> 个独立问题。详情链接：<diff-link>。
```

详情链接优先拼代表流量 flow diff 链接，不要展示 `similarDiffId`；生成规则见 `diff-query-reference.md` 的“Flow diff 链接拼接”。每个需要用户复核的聚类（任何维度，含回放失败聚类）至少给一个代表流量链接，硬性要求见下文“聚类必须附「查看 diff 明细」链接”。`similarDiffId` 只放在命令清单或证据附录，方便复现查询。

该链接是聚类覆盖与现象复核入口，不是根因判断依据。进入单条或任务级归因后，必须按
`diff-analysis.md` 的“归因证据规范”补齐代码 / 配置 / 部署机制和日志 / Trace 执行路径；不得把这里的
聚类表或多个详情链接直接复制为“判断依据”。

优先选择：

- diff 聚类内最常见的 diff path；
- 有完整 base/replay 值的 case；
- replay logid 可查且错误更具体的 case；
- 用户关心的 method、接口字段或下游调用。

## 聚类必须附「查看 diff 明细」链接（硬性完成标准）

这条与“一行一聚类”同级，是报告的强制验收条，不是推荐做法。

- 报告里**任何维度**的每一个聚类行都必须带一个代表流量的可点击链接（表头写“查看 diff 明细”或“详情链接”）。维度无关：无论是按 `similarDiffId` 的 diff cluster，还是按 `method × failed_reason` 的回放失败聚类，都必须逐行附链接。
- 只有确实缺 `spaceId`、`protocol` 或原始 `log_id` 时，才允许把该行降级为 `task URL + method + 代表 log_id` 文本，并在该行显式标注降级原因。不要用 `similarDiffId` 或任何内部 ID 冒充可点击链接，也不要编造链接。
- 聚类行缺链接又未标注降级原因，等同于把多个聚类合并成一行，判为报告不合格。

### diff cluster（similarDiffId 维度）

优先读取 `task diff-cluster list/get` 或 `task analyze` JSON 里的 `cluster.flowDiffUrl`；缺字段时按 `diff-query-reference.md` 的“Flow diff 链接拼接”手工拼接。

### 回放失败聚类（failed_reason 维度）

回放失败聚类不能只依赖 `task evidence get`：它的 method 集可能来自 DIFF 聚类，无法保证覆盖
“发送失败但没有 DIFF”的流量。先按
`diag-replay-failure.md#第一步读任务终态与失败聚类` 建立有界清单并完成单条确认与数量对账，
其中先用 task detail / Flow 列表发现实际 PSM + method，再查 method report；
再按 `method × 单条 failed_reason` 聚类（例如 `901604` ByteMesh QPS 限流、`901501` ByteMesh
服务发现失败）。错误码语义见
`enums.md#单条流量回放失败码failed_reason`。这条路径**没有** `similarDiffId`，CLI 也不会自动
产出链接，必须手工拼，规则与 diff cluster 完全一致：

- 用**不带** `similarDiffId` 后缀的 flow-diff 链接格式（见 `diff-query-reference.md` 的“Flow diff 链接拼接”；host 跟随任务所在 Tesla-X 部署，zg 任务用 `tesla-x-zg.bytedance.net`）：

  ```text
  https://tesla-x.bytedance.net/space/<space_id>/f_app/task/new/diff/<task_id>/<psm_task_id>/<method_base64>/<protocol>/<log_id>
  ```

- 代表 `log_id` 从该聚类对应的 `log_id_classify_map` 里取一条最能说明失败的流量；`method`、`psm_task_id` 用该聚类对应值；`method` 需 UTF-8 base64 后再 URL encode。
- 每个 `method × failed_reason` 聚类至少给一个代表流量链接；缺 `spaceId` / `protocol` / 原始 `log_id` 时才按上面的降级规则处理。

## 何时进入单条根因分析

满足任一条件时，继续读 `flow-diff-root-cause.md`：

- 需要解释某个字段为什么不同。
- 需要确认 outbound diff 是 mock 缺失、下游变化还是业务代码变更。
- 需要拿 replay logid、request/response 或 record value。
- 需要把 task 级结论落到可修复的文件、配置、mock 或环境动作。

## Task 级输出

task 级 triage 不要只输出任务状态。至少包含：

- 任务状态、PSM、plan、env、branch/commit、PSM task id、Tesla-X 直达链接。
- 任务形态：系统级 / 沙箱 / 不确定；必须列出顶层 `env`、`replay_env`、`mock_enable` 统计和任何冲突字段。
- 总览计数：case/replay 成功失败、`total_diff_count`、`noise_count`、`need_confirm_count`。
- 分析范围：主线筛选口径、各 method 待分析 diff 聚类数、哪些 method 全量覆盖、哪些 method 仅覆盖 Top 10、剩余未分析聚类数量。
- 任务 / PSM / 接口汇总统计。不要在用户报告里直接写 `Aggregate`，统一写“汇总统计”。
- Top diff 聚类列表：method、direction、diff path/reason、命中流量数、累计 diff 明细条数、标注状态、代表性 case、代表流量详情链接。每个已分析 diff 聚类必须单独一行输出聚类级结论。
- 对累计 diff 明细条数按 `domain-model.md#术语与表达规范` 的口径说明；判断影响范围优先看“命中流量数”。
- 任务结果可见性：系统级任务说明“不期待 outbound diff”；沙箱任务说明是否有 outbound request diff、mock 匹配状态、logid 错误；未在结果中出现的采集/部署/context 前提列为不可验证。
- 降噪判断：是否存在随机值 diff 或数组乱序 diff；可剔除降噪项、待核验降噪候选和证据不足降噪项分开列。
- 仍需验证项：只有证据不足、需要业务确认或需要代码关联时输出。不要在分析范围表里展示“下一步”；用户追问时再继续分析剩余聚类。

## 推荐分析模板

task 级报告默认先输出以下三张表。第一张表是强制项，用来让用户先看清本次覆盖边界；第二张表展示已经详细分析的聚类；第三张表只在存在截断时输出。

报告必须同时有两层结论：

- 聚类级结论：每个已分析 diff 聚类必须单独输出一行。相似聚类可以在“当前判断”里写成同一类根因，但不能合并成一行。
- 任务级结论：在逐条聚类结论之后，再总结共同根因、主线影响和仍需验证项。任务级结论不能替代聚类级结论。

### 表 1：分析范围表

| method     | 方向                   | 筛选口径                             | 待分析 diff 聚类数 | 本次分析策略          | 本次详细分析 | 剩余未分析 | 主要 diff path / 现象    |
| ---------- | ---------------------- | ------------------------------------ | -----------------: | --------------------- | -----------: | ---------: | ------------------------ |
| `<method>` | `<inbound / outbound>` | `<未处理聚类 / URL 筛选 / 显式筛选>` |              `<N>` | `<全量分析 / Top 10>` |        `<M>` |    `<N-M>` | `<主要 path 或现象摘要>` |

填写规则：

- `待分析 diff 聚类数` 是当前筛选口径下，这个 method + 方向需要分析的 diff 聚类总数。优先读取 `task analyze` / `task diff-cluster list` JSON 里的 `clusterSelection.total`。
- `本次详细分析` 是本轮实际展开到 path、样本值、降噪判断、当前判断的聚类数。
- `剩余未分析` 等于 `待分析 diff 聚类数 - 本次详细分析`。
- `本次详细分析` 必须等于“已分析 diff 聚类表”中该 method + 方向的行数；如果没有逐行输出，就不能声称已详细分析。
- 不要增加“下一步”列；用户追问时再继续分析剩余聚类。

### 表 2：已分析 diff 聚类表

|        优先级 | method     | 方向                   | diff path / 现象        |   命中流量数 | 累计 diff 明细条数 | base / replay 样本       | 降噪判断                                          | 当前判断         | 详情链接                    |
| ------------: | ---------- | ---------------------- | ----------------------- | -----------: | -----------------: | ------------------------ | ------------------------------------------------- | ---------------- | --------------------------- |
| `P0/P1/P2/P3` | `<method>` | `<inbound / outbound>` | `<path + 用户可读现象>` | `<logCount>` |      `<diffCount>` | `<base/replay 代表样本>` | `<非随机值 / 非纯乱序 / 可剔除降噪项 / 证据不足>` | `<当前归因判断>` | `<代表流量 flow diff 链接>` |

填写规则：

- 表 2 的每一行只能对应一个 method + 方向 + 一个 diff path/reason + 一个 diff 聚类。不要把多个 diff 聚类合并成“模块结构变化”“页面字段变化”这类主题行。
- 如果一个 method + 方向本次详细分析 10 个聚类，表 2 中该 method + 方向必须有 10 行；如果只输出 3 行，就只能算详细分析 3 个，其他聚类要进入剩余未分析表或摘要覆盖说明。
- 正文用 method + 方向 + diff path / 现象描述，不要用 `similarDiffId` 当主语。
- `diff path / 现象` 优先读取 JSON 的 `cluster.displayPath`；如果没有，再用 `diffPath`、样本 path 或 schema path。
- 代表流量名称不超过 30 个 Unicode 字符，并尽可能概括差异语义和接口/方法，例如
  “审计单详情鉴权提前返回”；不要求完全准确，但禁止只写接口路径、`代表流量`、`样本 1` 或
  Flow/Log ID。
- `累计 diff 明细条数` 的口径见 `domain-model.md#术语与表达规范`；数组字段会放大它，判断影响范围优先看“命中流量数”。
- `详情链接` 优先填 JSON 的 `cluster.flowDiffUrl`；缺少必要字段时填 task URL、method、方向、diff path 和代表 log_id，不要编造链接。
- inbound 聚类的 `base / replay 样本` 优先读取 `inbound.samples`；如果样本带 `basePresent/replayPresent=false`，表达成“录制侧/回放侧未抽到或不存在该值”，不要过度断言具体业务含义。
- outbound 聚类的样本优先读取 `outbound.summary` 和 `baseOutboundPreview/replayOutboundPreview`，说明调用次数、主要外调 method/target 和请求参数变化；preview 不是全量外调列表。

### 表 3：剩余未分析聚类表

仅当任一 method 因待分析 diff 聚类数超过 10 而发生截断时输出。

| method     | 方向                   | 剩余未分析 | 剩余聚类归类                                                | 为什么本次未展开                                                    |
| ---------- | ---------------------- | ---------: | ----------------------------------------------------------- | ------------------------------------------------------------------- |
| `<method>` | `<inbound / outbound>` |      `<N>` | `<低命中 path / 与主线相似 path / 已标注低风险 / 证据不足>` | `该 method + 方向待分析聚类数为 <total>，按规则本次详细分析 Top 10` |
