# Flink 使用与配置咨询

## 先固定上下文

没有真实任务也要尽量确认：

- Flink 完整版本与内部 fork；
- ByteDance Dorado/Godel 还是上游/其他部署；
- YARN/Kubernetes、stream/batch；
- source/sink、state backend、checkpoint mode；
- 目标：正确性、吞吐、延迟、恢复时间、成本或操作命令；
- 当前配置、正常基线、SLA 和不能接受的副作用。

信息不足时给条件式答案和验证方法，不以最新版上游默认值替代实际 fork。

## 咨询范围

覆盖：

- bytedcli 只读命令、metric、Dashboard、site/region 路由与鉴权；
- checkpoint/savepoint、restart/failover、state/backend；
- 并行度、slot、TM/JM 内存、network/off-heap；
- backpressure、watermark、event time、batch/minibatch；
- source/sink connector 与外部依赖诊断；
- Flink 版本能力、兼容性和迁移风险；
- 容量与性能优化的实验设计。

业务代码或 SQL 的逐行审查不是核心流程；可解释 Flink 语义并指出需要进入代码仓库验证的边界。

## 回答结构

1. 直接回答当前问题。
2. 写明适用版本、部署和前提。
3. 区分事实、推断与候选。
4. 给只读检查命令或配置发现方式。
5. 给风险、替代方案和验证条件。
6. 涉及生产变更时只给建议，不执行。

## 参数建议

禁止凭经验拍固定值。先收集当前值与指标，再给范围或推导方式：

- 并行度：输入 partition、当前 records rate、busy/BP、下游容量、state/recovery 成本；
- 内存：heap/direct/metaspace/network/managed/native/container 分层与峰值；
- checkpoint：实际 phase、state/in-flight size、storage 带宽、interval/timeout 与恢复目标；
- timeout/retry：远端延迟分布、幂等、重试放大、业务 SLA；
- watermark/idle：事件时间分布、空闲 partition、allowed lateness 和正确性语义。

将建议标为根因修复、缓解、实验或恢复性优化，并包含回滚。

## 版本闸门

Flink 1.11、1.17 与内部 backport 在 endpoint、metric、unaligned checkpoint、watermark alignment、反压采样和默认 restart strategy 上可能不同。先执行：

1. 查询 runtime/build/config；
2. 列出实际 REST/metric catalog；
3. 试探能力并记录返回语义；
4. 仅使用确认存在的字段和配置；
5. 将上游文档当语义参考，不当内部 fork 交付证明。
