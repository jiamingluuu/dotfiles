# Lag、反压、吞吐、延迟与性能优化

## 目录

- Lag 先看斜率与供需
- JM 静默强制分流
- 反压沿 DAG 向下游定位
- High busy 强制 TM 下钻
- 瓶颈分类
- 无 Lag 但端到端延迟高
- 正确性
- 优化建议纪律
- 验证

## Lag 先看斜率与供需

用多个时间点估计 backlog `L(t)` 的斜率，并对齐生产率 `P`、source 消费率 `C`、作业输出率 `O`：

| 组合                            | 解释                          | 下一步                                               |
| ------------------------------- | ----------------------------- | ---------------------------------------------------- |
| `dL/dt > 0`，`P` 先升且 `P > C` | 流量上涨超过当前容量          | 判断 C 是否达到健康容量，再查 BP、busy、资源和并行度 |
| `dL/dt > 0`，P 稳定而 C 下降    | 作业或下游性能回退            | 对齐发布、restart、CP、GC、外部延迟，沿 DAG 下钻     |
| `dL/dt ≈ 0` 且 lag 高，`P ≈ C`  | 稳态积压或 offset/commit 口径 | 看 SLA、commit 和更长基线，不写“正在恶化”            |
| `dL/dt < 0`                     | 正在追赶                      | 估算回到 SLA 的时间，检查是否周期性反压              |
| lag 低但 e2e 高                 | backlog 非主路径              | 查 watermark、batch/minibatch、sink commit/CP        |

Lag 绝对值量化影响，不解释原因。扩并行度前确认 source partition 上限、当前并行度、busy/CPU、下游容量和是否存在倾斜。

## JM 静默强制分流

Lag 上升或 source 断流且平台仍保留 `RUNNING` 时，先读取 [failover.md 的 JM 静默守卫](failover.md#jm-静默或宿主机不可用无-failover)。同窗已稳定运行、incident attempt 与 restart 未变化，并且绑定该 attempt 的 JM REST 或 uptime 断点时，强制转 `JM_SILENT_OR_HOST_UNAVAILABLE`；不要因无法取得 DAG/busy 就停在普通性能分支，也不要运行依赖可用 JM REST 的 TM thread-dump 下钻。

## 反压沿 DAG 向下游定位

1. 获取实际 DAG、vertex ID、并行度和 chain。
2. 试探 backpressure endpoint；deprecated 时按 [commands.md](commands.md) 的固定指标白名单查询 busy/idle/backPressured。高并行度 vertex 不做 catalog discovery。
3. 对候选 vertex 做有界 subtask 分层采样，比较可取得的 hottest、median/control、records in/out 和 TM/Pod placement；不要为了计算全局 max/p95 枚举全部 subtask。
4. 从高反压 vertex 沿数据流向下游走；最下游仍能解释上游阻塞的阶段才是瓶颈候选。
5. 少数 subtask 异常：查热点 key/partition、单 Pod throttling、单 host、partition-specific remote call。
6. 全体同步异常：查阶段容量、GC、checkpoint pause、共享下游、网络/存储。

只有同时存在 busy、idle、backPressured 三指标且语义匹配本 fork 时，才使用近似合计 1000ms/s 的解释。旧 1.11 sampling 语义或内部 backport 必须 capability discovery。

Operator chain 场景中 vertex 汇总 records 可能为 0、busy 可能 NaN；使用固定白名单中的算子级 metric 路径补证，不要判“无流量”。白名单不覆盖实际 fork 时记录 capability 缺口，不扩大为 catalog discovery。

## High busy 强制 TM 下钻

把“同窗 high busy 且同时存在上游反压或用户报告 lag”作为强制守卫。`flink diagnose` 使用固定指标白名单自动验证守卫；触发后不得把 high busy 直接写成 CPU 饱和，也不得停在 operator/vertex 级，而是继续用原生 Flink/Kelemetry/Vela 只读 API 完成以下步骤。守卫未闭合时输出 `PERFORMANCE_HIGH_BUSY_EVIDENCE_REQUIRED`；只有 capability、权限或有界采集预算阻断时才提前结束，并把状态降为 `PARTIAL` 或 `UNKNOWN`。

### 1. 绑定 current attempt

1. 固定当前 application attempt、job ID、vertex ID 和采样时间。
2. 从当前 vertex/subtask detail 取得正在运行的 subtask attempt、TM ID 与 runtime host hint；验证 job attempt、subtask attempt 和 placement 都是当前值。TM ID 只是 Godel Pod 候选，runtime host 只是 Vela 查询候选，不把它们提前写成已验证 Pod/physical host。
3. 把用户提供的 TM 链接只作为候选。未通过 current placement 验证的 TM 不进入样本，也不用于解释当前 busy。

### 2. 选取代表样本

1. 复用已取得的有界 backpressure、top-N、partition 或固定白名单 metric 证据选择 hottest subtask；不要为找热点扫描 metric catalog。在证据记录中显式标为 `hottest:<index>`；其他已证实热点可标为 `hot:<index>`。
2. 再选择 median/control subtask，并显式标为 `control:<index>`。只能取得有界样本时写“sampled control”，不要声称它是全局中位数。缺少 hottest 或 control 角色时强制分支不算完成。
3. 把代表 subtask 集合限制在 12 个以内，再选择 2–3 台代表 TM：优先覆盖 hottest 与 median/control，并按 runtime host hint 尽量分散；多个候选落在同一 TM/hint 时换取能增加区分力的样本。任何一次诊断最多查询 3 台 TM，不能遍历全部 TM。最终物理机数量只能依据闭合后的 placement 报告，不能把 hint 去重数当真实 host 数。

### 3. 收集同窗 TM 证据

对每台代表 TM 先用已知 TM Pod 候选执行 Kelemetry exact-name lifecycle 查询，再对 runtime host hint 执行 Vela 固定机器指标查询；两者都只旁证 current placement，不能执行反查。随后取得同一时间窗的 Flink TM CPU、GC、heap/non-heap、direct/network memory、network/buffer 指标和有限日志，并获取两轮 thread dump，按重复栈签名聚合 execution thread 的状态、用户/connector 栈、锁 owner 与等待对象。两轮之间使用有界间隔；单份 dump 只是瞬时截面，不是时间线。

Kelemetry 只保留 trace ID、操作名、span 数和时间摘要，不保留 loose tags/logs/raw；0 trace 不表示 Pod 不存在。Vela 只保留固定 metric 的有界统计，空 series、空 points 或 `selectedName` 不一致不算机器证据。若 Kelemetry/Vela 无法闭合实体边，继续收集 TM metric/log/dump 以区分性能机制，但整个强制分支降为 `PARTIAL`。

只保留栈签名、计数和必要帧，不把完整 dump 写入报告。当前 thread dump 只能解释当前性能机制，不能反推历史 failover 的根因。

### 4. 区分机制

| 机制           | 支持证据                                                                                                                | 判断边界                                                                                                    |
| -------------- | ----------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------- |
| CPU 计算       | 两轮中 execution thread 持续位于用户计算/序列化栈，且 TM/container CPU 同窗升高                                         | `RUNNABLE` 只表示 JVM 线程状态；native socket read 中的 `RUNNABLE` 不等于消耗 CPU                           |
| 锁竞争         | 重复出现 `BLOCKED`、monitor/park 等待，同一锁或 owner 可关联，吞吐同步受限                                              | 单个等待线程或无 owner 的一次快照不足以确认全局锁瓶颈                                                       |
| 同步外部 I/O   | 多个 execution thread 两轮重复停在 Redis/Jedis、HTTP、DB、RPC 或 socket read/write 路径，CPU 不支持计算饱和             | 外部 client 栈只定位到调用路径，不能单独确认服务端故障；继续区分客户端 timeout、连接池、DNS、网络和远端延迟 |
| 线程池等待     | Future/queue/semaphore/connection acquisition 等待聚集，并有队列、active/max、拒绝或超时旁证                            | Future wait 可能只是同步 I/O 的上层表现，需与 worker/连接池证据关联                                         |
| Network buffer | Flink network/input gate/buffer request/output flush 栈与 buffer pool、network memory、in/out/backpressure 指标同窗一致 | 普通远端 socket 栈不自动归为 Flink network buffer 问题                                                      |

证据混合或缺少区分力时并列候选并输出 `UNKNOWN`，不要强选单一机制。

### 完成条件

只有同时满足以下条件，强制性能分支才算闭合：

1. 每个代表 subtask 都有 current job/subtask attempt → TM 候选 → Kelemetry Pod lifecycle、runtime host hint → Vela 的分段记录；未闭合的 Pod/host 边明确标为 candidate/partial，不得写成 verified physical host。
2. 已选择不超过 3 台、覆盖 hottest 与 median/control 且按 runtime host hint 尽量分散的代表 TM，并记录选择理由；不得把 hint 数量声称为物理机数量。
3. 每台代表 TM 都查询 Kelemetry、Vela，并取得 CPU/GC/内存/网络、有限日志和两轮 thread dump；取不到的项目有明确的 capability、权限或预算失败证据。
4. 已聚合两轮重复栈，并对 CPU、锁、同步外部 I/O、线程池、network buffer 分别列出支持证据、反证、缺口与置信度；仅有重复栈但缺少对应独立旁证时不得给 `MEDIUM`。
5. 所有调用满足 [commands.md](commands.md) 的单次与总预算，代表 subtask 不超过 12 个，没有 metric catalog discovery，也没有遍历全部 TM。

第 3 项因明确阻断而不完整时，以 `PARTIAL`/`UNKNOWN` 结束；其余情况下继续取证，不得以“已发现 busy/反压”作为停止理由。

## 瓶颈分类

### CPU/计算

busy 高、CPU 高且 records 受限支持计算瓶颈；再看算子/业务栈、序列化、热点 key 和 JIT/GC。CPU 高也可能是恢复追赶或 checkpoint，不自动建议扩容。

### GC/内存

对齐 heap/max、GC time/count、direct/metaspace/network memory、container RSS/limit 和 termination。Heap 未满不能排除 container/native 内存；exit 137 不能单独确认 OOM。

### 数据倾斜

要求少数 subtask 在 records、state、busy/BP 或 queue/partition lag 上显著偏离，并排除单 Pod/host。给出重分区、key 设计或并行度建议前说明数据语义和 shuffle 成本。

### 外部 sink/lookup

下游 latency/error 要早于 sink busy/BP 和上游 lag。只有 Flink timeout 时仍需排除本地 GC、thread pool、网络/DNS 和 timeout 配置。下游热点分片时，单纯加 Flink 并行度可能加剧压力。

### Source/分区

比较 MQ partition/queue、consumer allocation、source subtask records 和 watermark。分区数是并行上限线索，不是自动等于推荐并行度。

### Checkpoint/恢复干扰

性能异常与 restart/CP 同窗时先判 failover 或 CP phase。恢复从旧 offset 会制造 lag；不要把它误判为 source 性能回退。

## 无 Lag 但端到端延迟高

### Watermark

比较每个 source/input/subtask watermark、最后记录时间和 idle 状态。多输入 operator 的 watermark 受最小输入限制；确认具体阻塞 input，不只看作业汇总。

### 低 QPS batching

只有输入稀疏、延迟接近 poll/batch/minibatch 周期，并且改变/触发批次后延迟按预期变化时，才确认凑批机制。

### Sink commit

计算延迟正常但输出只在 transaction/CP commit 后可见时，把 commit 周期列为机制；再区分设计语义、CP 变慢和远端 commit latency。

## 正确性

dirty、late、dropped、writeFailed 只是线索。联合具体 record/partition、operator exception、watermark/allowed lateness、checkpoint/recovery 边界和 sink 幂等/事务语义，区分主动过滤、late data、恢复期丢弃、sink 写失败和重复提交。

正确性/SLA 破坏是独立高优先级轨道，不能被性能或 checkpoint 症状覆盖。

## 优化建议纪律

先建立任务自身健康基线，再给建议。内部区分四类：

1. **根因修复**：移除后能阻断事件链。
2. **临时缓解**：降低当前影响，但不声称消除根因。
3. **待验证实验**：写明假设、单一变量、预期指标、风险、回滚和观察窗口。
4. **恢复性优化**：缩短失败后的恢复时间或影响范围。

没有数据时不给具体并行度、TM 内存、buffer、timeout 或 checkpoint interval。参数建议至少说明：当前值、瓶颈证据、资源/状态/partition 约束、目标 SLA、预期收益、副作用和验证指标。

最终仍按上层 `SKILL.md` 的“三项紧凑报告契约”输出：只选择优先级最高且与当前置信度相符的最多三项解决方案，不把上述四类全部展开。根因未确认时只输出一项信息增益最高的只读验证。

## 验证

- lag 斜率不再为正，并在预期时间回到 SLA；
- records in/out、busy/idle/BP 和 subtask 分布恢复；
- CPU/GC/memory/throttling 回到任务基线；
- checkpoint 和 restart 不再干扰；
- watermark/e2e/commit 延迟恢复；
- 下游错误、dirty/writeFailed 不再增加。
