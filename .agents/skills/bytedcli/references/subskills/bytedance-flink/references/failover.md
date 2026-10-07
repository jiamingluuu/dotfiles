# Failover、JM 静默、进程退出与重启诊断

## 先找第一个失败事件

1. 固定 application attempt 和首次状态变化时间。
2. 读取 job exception history，保留 exception chain、timestamp、task/vertex、TM 标识和 `truncated`。
3. 在 JM log 中向前找第一次 task `to FAILED` 或 failure handling 之前的异常。
4. 涉及 TM lost 时，以 TM/pod/container 为 join key 对齐 runtime、YARN/K8s、资源和宿主机证据。
5. 涉及 JM lost 时，对齐 JM termination、leadership/application attempt 和平台事件。
6. 只有直接证据指向 connector/远端后，才进入外部依赖验证。

不要从最后的级联 cancellation、slot shortage、BLOB fetch、deployment retry 或 `TaskExecutor is shutting down` 倒推根因。

## Failover 优先守卫

出现任一条件时优先进入本分支：

- 平台 `FAILED`；
- Flink `FAILING`、`RESTARTING`、`FAILED`；
- TM/JM lost、container termination；
- restart/fullRestart 在故障窗口内上升；
- checkpoint 错误包含 `FailoverRegion is restarting`、tasks not ready 或 task cancellation。

恢复策略决定是否/何时重启，failover strategy 决定重启范围；二者不是触发根因。

## JM 静默或宿主机不可用（无 failover）

### 强制守卫

先把故障窗口记为 `W=(last_good, first_bad]`；时间精度不超过数据源采样周期。人工 restart 及其新 application/attempt 属于恢复动作，不放入 `W`，也不使用恢复后的 `latest` 身份反查故障实体。

Lag 或 source 断流且平台仍保留 `RUNNING` 时，必须先验证本守卫，不能直接转 `RUNNING_PERFORMANCE`。只有以下条件在同一 `W` 内全部成立，才进入 `JM_SILENT_OR_HOST_UNAVAILABLE`：

1. **业务影响**：Lag 正在增长；或 source 消费从健康基线降到 0/断点，并有 MQ lag、offset、生产率或其他独立消费面佐证。source metric 单独无数据不是业务断流证据。
2. **平台保留 RUNNING**：Dorado/Megatron 在 `W` 内仍保留非终态 application。状态更新时间陈旧时只能写“控制面仍保留 RUNNING”，不能解释为 JM 健康。
3. **此前已稳定运行**：该 attempt 在 `last_good` 前已有 RUNNING、单调 uptime 或成功 checkpoint；否则按启动分支处理。
4. **无 failover 的正向证据**：同一 incident application/AM attempt 覆盖 `W`，且 `numRestarts` 与 `fullRestarts` 的平坦序列实际覆盖 incident，或另有已规范化、可复核的 incident-time `restart_unchanged` 事实。只有 incident 前三个相邻采样点平坦、随后随 JM 一起断流，只能证明断点前未增长，不能单独闭合本项。查询为空、少于三个点或日志缺失不能证明“未重启”；任一 counter 明确上升/重置必须压过另一个 counter 的缺失并转 `FAILOVER`。attempt 历史中的后续 replacement 只有在其时间不早于独立 operation-log/人工恢复 artifact 给出的 `recoveryTime` 时才可视为恢复；缺少该 provenance 时视为 attempt 变化反证。
5. **JM 控制面静默**：绑定该 incident attempt 的 JM REST 经有界网络重试仍不可达，或 `flink.job.uptime` 在此前按稳定采样周期单调增长后、从 incident 附近开始连续缺失至少两个采样周期。最近采样 cadence 不能稀疏，并以 incident 后 2 分钟为当前 1 分钟指标的归因容差；断点从容差边界或更晚才开始时记为不对齐，不能归因到 earlier incident。鉴权失败、错误 site、陈旧 URL、404 或身份冲突不算 JM 静默；uptime reset 或 attempt/restart 上升转 `FAILOVER`。

先处理显式 failover 和身份冲突：发现 attempt/restart 上升、termination 或明确 JM lost 时转 `FAILOVER`；attempt、URL、时间窗或 host 映射不唯一时转 `PLATFORM_RECONCILIATION`。只有守卫闭合后才把 Lag 作为本分支的业务后果，而不是普通算子性能问题。

### 固定 incident attempt 和 JM host

闭合以下实体链，并为每条边保存来源、有效时间和抓取时间：

```text
task
  -> incident application + 精确 jobName/app_name 绑定
  -> application/AM attempt valid at W
  -> JM/AM containerId（已知 Godel JM Pod 候选）
  -> Kelemetry exact Pod lifecycle at W
  -> Kelemetry allowlisted、唯一且同窗的 node（physical host）
  -> Vela exact selectedName host metrics at W
  -> Megatron nodeHttpAddress 分域交叉验证
```

- 使用故障时刻的明确 attempt；`latest` 只有在已证明它等于 incident attempt 时才可使用。
- Megatron `app_name` 必须与查询 ByteTSD 使用的 `jobName` 精确一致，Megatron 的权威 `physical_cluster/cluster_name` 字段也必须与 ByteTSD `physicalCluster` 精确一致；字段缺失时只有已由主采集器闭合 task → application → physicalCluster 的主作业可以显式继承该 join。同机 peer 必须各自同时验证 job 与 cluster，不能把任意 application 的 host 与另一 job/cluster 的指标拼接。
- 当前原生路径只支持明确的 Godel Flink 部署契约：application AM container 即 Flink JM。`containerId` 是 Kelemetry 已知 Pod 名候选；Vela host 只能来自 Kelemetry trace 中严格 allowlist、唯一且同窗的 node，`nodeHttpAddress` 仅用于分域交叉验证。任一关键字段缺失、冲突或 provider 不明时停止对应 join。
- Kelemetry 只能查询已知 Pod lifecycle，Vela 只能查询已知 host/IP 指标；二者都不能反查 `JM → Pod → host`。旧 Flink URL、DNS 推断、同名 application、恢复后的新 app、Kelemetry 空结果或 Vela 空 points 都不能替代 placement bridge。
- 任一 join 冲突时停止 host 归因，输出 `PLATFORM_RECONCILIATION` 或 `PARTIAL/UNKNOWN`。

### 有界取证顺序

`flink diagnose` 输出 `JM_SILENT_EVIDENCE_REQUIRED` 时，必须先按 handoff 的 `argumentMap` 用原生 Kelemetry、Megatron、APM/ByteTSD 和 Vela 只读命令补证；该步骤优先于普通性能/TM 下钻。参数与预算见 [commands.md](commands.md#jm-静默历史证据)。

1. **ByteTSD/Flink 历史**：只按 incident application/job 和已知指标名查询 `flink.job.uptime`、`numRestarts/fullRestarts`、已知 source consume/records rate、checkpoint completed/failed/continuous-failure。记录 last-good、first-bad、恢复点、采样周期以及值为 0、reset、无样本的区别；不做 job/vertex metric catalog discovery。已验证 `recoveryTime` 之后的 restart counter 变化属于恢复段，不倒灌进 incident 判定；没有恢复 provenance 时不做这个截断。
2. **Megatron attempt**：读取 application state 和 `am_attempts_container_info` 等已有字段，固定 attempt、container/pod 候选、start/end、nodeHttpAddress、exit code 和是否发生 replacement。nodeHttpAddress 只作后续 Kelemetry node 的分域交叉验证，不直接驱动 Vela。当前 bytedcli 没有顶级 Godel AM health/allocation/event 叶子；不得把缺少 Godel event 解释成没有调度或节点事件。
3. **Kelemetry Pod**：只对 primary 与最多两个显式 peer 的 incident JM containerId 做 exact `pods/name/start/end` 查询，每个 Pod 最多 3 条 trace、必要时最多一次 detail。`--cluster` 是 Jaeger operation，不能传 physicalCluster。只保留脱敏 allowlist 摘要；0 trace、多个冲突 UID/namespace/node 或时窗不覆盖均为 `PARTIAL/PLATFORM_RECONCILIATION`，不是“没有 Pod/事件”。
4. **Vela host**：JM 只对 Kelemetry 唯一绑定的 node 查询 `W` 内固定指标；TM 只对 current runtime host hint 查询。Vela response `selectedName` 必须与请求一致并含有效 points。CPU/load/内存/网络高、`agent.alive` 断点或返回空数据都是旁证，不能单独证明节点不可用、驱逐或宿主机故障。
5. **已知同机 peer**：只验证调用方或现有证据已给出的最多两个其他 JM；每个 peer 独立闭合 application/job/attempt/container → Kelemetry Pod 与 host hint → Vela，再按准确 tag 查询 uptime 断点。当前 bytedcli 没有 host → applications 过滤能力，禁止为寻找 peer 扫描全 cluster 或全量 application。
6. **对齐与反证**：按事件自身时间对齐 Lag/source、JM REST/uptime、attempt/restart、checkpoint、Pod lifecycle、host 负载和 peer 断点。处理陈旧 URL/鉴权、ByteTSD 全局断流、上游无流量、真实 failover 和恢复动作落入错误时间窗等替代解释。

### 输出分类与置信度

只有强制守卫全部闭合并路由到 `JM_SILENT_OR_HOST_UNAVAILABLE` 后，才输出以下两个本分支分类。补证后若仍缺 Lag/source 独立影响、历史 RUNNING、restart/attempt 或 JM 静默证据，顶层保持 `UNKNOWN`；不得提前命名为 `JM_SILENT_CAUSE_UNKNOWN`，因为此时连“JM 已静默”也未确认。

#### `JM_HOST_UNAVAILABLE`

必须同时满足：

1. incident attempt → JM/AM containerId → Kelemetry Pod，以及 node/host hint → Vela 的分段身份链闭合且无冲突；
2. 同一 host、故障时刻前后 5 分钟内存在来自外部或其他证据面的、可复核的节点 unavailable/reboot/isolation lifecycle artifact，包含 host、时间、事件类型、原始 reason 和 artifact 引用；
3. 至少一个独立已知同机 peer 的 JM uptime 同窗断点闭合；
4. 不存在异机同样断流、故障 onset 已发生 attempt replacement 或其他强冲突；数小时后的人工 restart/换机只有具备独立恢复时间 artifact 时才属于恢复证据，不反向抹掉 incident attempt 的身份与同窗断点。

直接节点事件与 host/时间精确匹配，且跨作业独立佐证闭环时可给 `CONFIRMED`；二者均存在但事件时间粒度或独立对照不完整时最高给 `HIGH`。节点不可用是可证实机制；硬件故障、网络隔离、OS 卡死或调度动作仍按事件实际 reason 分开，不从恢复动作倒推。

当前 Vela 命令面只有 `vela one-machine query`，没有 node lifecycle/availability event 叶子。因此原生自动链最高只能输出 `JM_SILENT_CAUSE_UNKNOWN`；不能用 Vela 负载、`agent.alive` 或空数据满足第 2 项。只有调用方提供、且能精确复核 host/时间/reason 的直接节点事件 artifact，再加同机 peer uptime 断点，才能升格为 `JM_HOST_UNAVAILABLE`。每次执行仍以当前 `--help` 做 capability discovery。

#### `JM_SILENT_CAUSE_UNKNOWN`

强制守卫成立，但直接节点 lifecycle artifact、跨作业闭环或 host 身份任一缺失/冲突时输出该分类。明确写最后可证实层级，例如“JM REST 路径不可达”或“JM uptime 与消费同窗中断”；只有 REST 失败时不得升级为“JM 进程卡死”。

根因状态使用 `UNKNOWN`；关键数据源因 capability、权限或 retention 受阻时使用 `PARTIAL`。Vela 高负载或无数据不能得到 `MEDIUM` 以上的宿主机故障结论，同机 peer 正常或异机也同窗断流属于必须展示的反证。

### 完成与停止条件

本分支仅在以下条件满足后结束：

1. 守卫每个合取项都有正向证据或明确缺口，incident attempt 与故障窗口没有使用恢复后的 `latest` 替代。
2. JM/AM container → Kelemetry Pod 与 node/host hint → Vela 的实体链闭合，或已因冲突停止 host 归因。
3. 已完成有界 ByteTSD、Megatron attempt、primary/最多两个 peer 的 Kelemetry Pod、Vela host 查询；取不到的项目记录 capability、权限或 retention 原因。
4. 已按上述硬条件输出 `JM_HOST_UNAVAILABLE` 或 `JM_SILENT_CAUSE_UNKNOWN`，并处理最近的替代解释。

`JM_HOST_UNAVAILABLE` 闭环后停止，不再查询全部 TM、host 或 application。直接 node lifecycle artifact、Godel event 或 host → applications capability 缺失时，在完成其余有区分力的有界查询后以 `JM_SILENT_CAUSE_UNKNOWN` 和 `PARTIAL/UNKNOWN` 停止；不得发明命令、扩大到全量扫描或转用 high-busy 的 TM thread dump 分支。

## 不确定 TM failover：日志优先的身份取证

仅有 `TM lost`、heartbeat timeout、`Pod deleted`、`Pod Terminated`（包含常见误拼 `Termated`）或远端连接断开时，只能确认 TM 失联/生命周期结束，不能确认它为什么消失。必须进入 `FAILOVER_TM_IDENTITY_EVIDENCE_REQUIRED`，先查故障 TM 日志，日志不可得、被截断或没有决定性信号时才进入 Kelemetry/Vela 旁证。

### 固定事件与实体

1. 固定 incident application 与 `W=(last_good, first_bad]`。handoff 保留 `incidentAttemptBinding={applicationId, attemptOrdinal?, attemptBindingSource, identitySource, provenance}`。application ID 不等价于 AM attempt；attempt ordinal 只能来自显式平台元数据，或严格形如 `<application-id>-taskmanager-<numeric-attempt>-<tm>` 的 exact incident Pod。二者冲突时停止，恢复后的 current TM/application 不能回填。若只有 opaque TM ID、attempt ordinal 缺失，仍先执行有界日志采集，但输出保持 `identity-unverified/PARTIAL`。若原始 `W` 超过 2 小时，主采集器在不越出 `W` 的前提下围绕 event 裁出严格包含 event 的 `W_TM ⊆ W`，且 `W_TM ≤ 2h`。
2. 把原始文本解析为不超过 3 个去重的实体记录，每个字段保留 `value/source/observedAt`，并在可证明时保留 `attempt`：
   - `tmResourceId`：Flink TaskExecutor/TaskManager 资源 ID；
   - `exactPod`：经 runtime/platform 字段或明确生命周期文本验证的完整 Pod 名；
   - `hostHint`：TM remote address、runtime host 或 node address 候选。
3. opaque `tmResourceId` 不等于 Pod 名，remote address 不等于已验证宿主机。只有完整、严格匹配 incident application 前缀与 `taskmanager` 段的 Godel Pod 形态 `tmResourceId` 才可自动提升为 `exactPod`；其他 ID 保持 opaque。泛化文本、字段冲突、attempt 不匹配或无法绑定 `W` 时保留 `PARTIAL/UNKNOWN`，不用字符串相似度强行 join。
4. 主采集器只从已有 exception/JM log/runtime 事件中去重并保留最多 3 个显式候选；达到上限即停止扩大实体集。不遍历全部 TM、Pod 或 host。

### 强制取证顺序

`flink diagnose` 输出 `FAILOVER_TM_IDENTITY_EVIDENCE_REQUIRED` 时，按 handoff 对选中的最多 3 个结构化实体，用原生 Flink log、Kelemetry 与 Vela 只读命令逐个补齐 incident identity、event time 与 `W_TM`。有 `inputIssues` 时先补证并保持 `PARTIAL/UNKNOWN`，不能猜测参数。命令和字节预算见 [commands.md](commands.md#failover-tm-身份证据原生补证)。

1. **TM 日志优先**：只查已绑定 incident application 与事件文本中显式 TM 身份的代表实体；attempt 已由元数据或 exact Pod 绑定时继续施加该约束，只有 opaque TM ID 且 attempt 缺失时仍日志先行但不升级出 `PARTIAL`。先用结构化 `taskmanager log list` 确认文件不超过 64 MiB，再以非 JSON 模式执行 `taskmanager log get --tail 50`，每台 stdout+stderr 合计硬上限 64 KiB。size 缺失/超限、历史 TM 已不可达、输出截断或无决定性信号都要显式记录。
2. **先裁决日志**：仅当同一 TM 的日志在 event 前后 5 分钟内给出明确 OOM/OOMKilled、JVM crash、SIGSEGV 或 `hs_err` 时，才把它作为决定性信号，并可不再执行 Kelemetry/Vela。其他 root exception 保留为候选且继续 fallback。单独出现 `Full GC`/`FullGC` 字样只是 GC 症状，需要 pause/duration、CPU/heap 时序或同窗 heartbeat 证据，不得直接归因 TM lost。
3. **Kelemetry 仅查 exact Pod**：仅在日志不可得、截断或没有决定性信号，且实体含 `exactPod` 时，查该 Pod 在 `W` 内以 event 为中心、前后最多 5 分钟的 lifecycle。Kelemetry 返回与该区间同窗、allowlist 内且唯一的 node 时，该 node 才是已验证的 Vela target；0 trace、多 node、身份冲突或查询失败都是证据缺口。
4. **Vela 分级查询**：优先查 Kelemetry 唯一 node，标为 verified target。Kelemetry 未得到唯一 node 但也未发生身份冲突，且实体仍有可审计 `tmResourceId`/`exactPod` 与显式 `hostHint` 时，可对该 host/IP 做有界 Vela 查询，但输出必须标为 candidate，不能证明 Pod 当时在该机器上。verified node 与 `hostHint` 冲突时停止 host 归因并保留 `PARTIAL/PLATFORM_RECONCILIATION`。只有 `hostHint`、无 `tmResourceId` 或 `exactPod` 的输入无法执行日志优先守卫，必须 fail-closed。

### 输出与停止边界

- `RemoteTransportException: Lost connection to task manager`、`Connection reset by peer` 或 remote shuffle client 错误只证明 consumer 到 remote TM 的连接断开。无更强证据时写：“直接触发信号是 TM 间连接断开；远端 TM 丢失原因未确认。”
- `Pod deleted`/`Pod Terminated` 只确认 lifecycle 事件；没有 reason/diagnostics、进程日志或节点事件时，它不是 OOM、驱逐、人工删除或节点故障的根因。
- Kelemetry/Vela 空结果、无有效 points、查询失败或 retention 缺口不代表 Pod/host 健康。Vela 高负载也不能单独证明 TM 丢失机制。
- 日志中有决定性 E0 时，仅保留脱敏的 signal type、事件时间和 artifact 引用后停止 fallback，不保留原始日志。否则在最多 3 个实体完成日志优先及可执行的 Kelemetry/Vela 旁证后停止；冲突、泛化文本、旧 attempt 或预算阻断时输出 `PARTIAL/UNKNOWN` 和明确补证 owner，不扩大到全量 TM 扫描。

## OOM 与退出码

按层区分：

| 层              | 直接证据                                                      | 需要补充                                     |
| --------------- | ------------------------------------------------------------- | -------------------------------------------- |
| Java heap       | `OutOfMemoryError: Java heap space`                           | heap/max、GC、state/object 分布              |
| Direct/off-heap | direct buffer/metaspace/native thread/network buffer 明确错误 | pool、connector/native allocation            |
| Container       | 同一容器 `reason=OOMKilled`，最好结合 usage/limit             | JVM 子池、RSS、limit                         |
| Unknown SIGKILL | 只有 exit 137                                                 | eviction、人工 kill、node failure、OOM event |
| JVM crash       | SIGSEGV、exit 127/hs_err/crash frame                          | `hs_err`、JDK/native library、CPU            |

exit 137/239 单独出现时绝不分类为容器 OOM。即使确认 OOMKilled，也继续区分 heap、direct、metaspace、network/managed、native/thread stack 与 container limit。

## 外部依赖与业务异常

业务栈、明确 auth/quota/schema/not-found/error code 属于高区分度证据。单独 timeout 仍可能来自本地 GC、CPU throttling、线程池、网络/DNS 或 timeout 配置。

Kafka/BMQ：

- `TimeoutException`、request timed out、record expiry → 发送超时候选；
- 只有 `RecordTooLargeException`、MessageSizeTooLarge 或明确 broker/producer size limit 才判单条消息过大；
- 配置中存在 `max.request.size` 不是消息过大的证据。

## 调度、节点与平台事件

内部 exit code 只作为路由线索；必须联合 reason/diagnostics、进程日志和资源时序。区分高负载驱逐、慢节点、机器维护、fault machine、混部抢占、黑名单和通用退出。

若 checkpoint timeout、反压和 lag 在驱逐之后出现，把它们列为传播后果。扩容或提高重启容忍度通常只是缓解，不是阻止平台驱逐的根因修复。

## 多根因与异常历史

- 同一 application 出现多个独立 leaf 时，分别报告最早决定性异常和最近异常。
- 按事件/实体/leaf 分组展示时间、算子、关键 `Caused by` 和置信度。
- exception history `truncated=true` 或日志轮转时降低置信度；“最早可见”不能写成“第一次”。
- Redis `isrootcause` 和 regex score 只能辅助排序，不能替代跨层因果链。

## Redis trace fallback

原生诊断不自动读取 Redis failover 历史。只有 runtime/attempt 历史不足或需要内部 oncall signature，且用户明确给出单一 Cache PSM 时，才按只读允许列表执行 `get-cluster` 与有界 `LLEN`/`LRANGE`/`ZREVRANGE`；不要默认多源扫描。线上 PSM、路由和 key 由运行环境提供，不固化在 Skill 中。缺少已审计的 key 构造能力时记录 capability gap，不临时拼接命令。

解释规则：

- 把 trace classification 记录为候选 evidence，不自动设为最终 root cause；
- 用 Flink exception、JM/TM log、termination 和同窗 metric 覆盖更弱的平台 label；
- 多个 leaf 不强选一个 root cause；
- 空结果、权限或网络失败输出 `PARTIAL/UNKNOWN`。

## 修复与验证

把行动分为：

- 根因修复：业务代码、凭据、远端容量、平台节点/队列、实际内存层等；
- 临时缓解：切稳定资源、限流、降低并发、回滚、扩大 timeout；
- 恢复性优化：checkpoint、restart/failover strategy、region recovery；
- 待验证实验：有明确假设、指标、风险和回滚。

验证 application attempt/restart 不再增长、原始异常消失、lag/吞吐恢复、连续 checkpoint 成功，并跨越足以覆盖原故障周期的观察窗口。
