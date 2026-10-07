# Checkpoint 与状态恢复诊断

## 先执行 failover guard

checkpoint 失败文本包含 `FailoverRegion is restarting`、tasks not ready、task cancellation，或失败窗口与 restart/TM lost 重合时，先诊断 failover。CP cancellation 是恢复后果，不是独立根因。

只有排除 failover 后，才按 checkpoint phase 下钻。

## 取证顺序

1. 读取 checkpoint config：interval、timeout、mode、min pause、并发数、unaligned 能力。
2. 读取 checkpoint list：counts、latest/history、duration、size 和失败原因。
3. 选择故障窗口内的具体 checkpoint ID，读取 vertex/subtask detail。
4. 对齐 JM log、restart、GC、backpressure、records、storage/network/I/O 历史。
5. 比较异常 checkpoint 与任务自身健康基线，不套固定阈值。

## 按阶段判断

| 阶段 | 含义 | 主要候选 | 区分证据 |
|---|---|---|---|
| trigger/调度 | coordinator 发起 | JM pause、timer/contention、配置 | trigger 时间、JM GC/log、config |
| start delay | trigger 到 subtask 收到首个 barrier | barrier 传播慢、上游阻塞、task 未就绪 | subtask 分布、上游 BP/records、DAG |
| alignment | 第一个到最后一个 barrier | 多输入不均、反压、倾斜 | alignment duration/bytes、各 input/subtask |
| sync | 同步 snapshot 阻塞处理 | state snapshot、本地 flush、大对象/定时器 | sync 最大 subtask、state/operator、thread/log |
| async/upload | 异步持久化；unaligned 还含 in-flight data | storage/network、state/in-flight size | upload duration、存储错误/延迟、size/I/O |
| end-to-end | 最后 ACK 决定完成 | 最慢 subtask 或协调路径 | checkpoint subtask detail，不看平均值 |

单个 subtask 显著异常只支持“倾斜/单实例问题”候选，仍需 records/state/placement。所有 subtask 同步异常更支持共享 storage/network、全局 GC 或配置问题。

## 常见因果链

### 反压导致 checkpoint 慢

下游处理能力下降 → 反压向上游传播 → start delay/alignment 增长 → CP timeout。此时修复下游瓶颈是根因修复；单纯加 CP timeout 是缓解。

### Storage/外部 I/O

async/upload 明显增加，并有 HDFS/TOS/S3 明确 timeout、403、quota、bad node 或 write slow，才确认存储侧。只看到 CP failed count 不足以确认。

### State 过大或倾斜

联合 state size 趋势、vertex/subtask state 分布、sync/async phase、单 TM placement。总 state 大但 duration 稳定不构成根因。

### 长期 CP 失败与 MQ TTL

CP 长期失败 → restart 从旧 offset 恢复 → lag 暴涨；若超过 MQ retention，可能 offset out of range/reset 并丢失过期数据。报告实际恢复点、MQ TTL、可能丢数/重复范围和补数 owner。

## 状态恢复

区分：路径/文件缺失、权限/quota、checkpoint 损坏、operator UID/topology/schema/serializer 不兼容、单 TM state 超限和恢复资源不足。

无状态重启或更换 namespace 会放弃状态，可能导致 offset 重置、重复或丢数据。把它列为高风险恢复动作，不默认执行；给出影响评估和回滚/补数方案。

## Unaligned checkpoint 边界

仅在以下条件都成立时列为候选缓解：

- 实际 fork/version 与配置支持；
- 主要耗时在 barrier propagation/alignment；
- checkpoint storage 带宽有余量；
- state/connector 语义兼容。

Unaligned 可以绕过 alignment 等待，但会持久化 in-flight data、增加 I/O；它不能消除底层反压，也不适合掩盖 storage 瓶颈。

## 验证

跨越多个实际配置 interval 验证连续成功；确认失败 phase 恢复到任务基线、state size/最慢 subtask 不再异常、restart 不增加、lag 与业务输出恢复。不要设置跨任务通用的“连续 N 次”或固定 duration 阈值。
