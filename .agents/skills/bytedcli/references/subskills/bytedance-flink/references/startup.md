# 启动、提交与调度诊断

## 先判引擎与部署形态

先从 `dorado task get` 的实际 metadata 和 application type 确认 Flink/fork、stream/batch 与 provider。`megatron app search/get` 支持定位 Flink application，不是 Spark 专属；但 `dorado instance diagnose` 默认使用 Spark/offline 语义，不能作为 Flink 流任务的权威根因来源。目标实际是 Spark/离线批任务时停止本流程，切换到对应 Spark 诊断入口。

只有已经从平台 metadata 得到精确 `cluster`、`namespace`、workload `name/type`，且用户明确允许创建只读诊断 artifact 时，才建议使用 Godel Explainer。它不能接收 Dorado task、Primus/Forge selector 或 Flink Web URL 自动反查坐标，也不能替代 Flink exception、JM/TM 日志和 attempt 证据。

## 先判断停在哪一层

按顺序定位，不要看到“启动失败”就直接查 Flink exception：

1. **身份/提交前**：task 是否存在，region/site 是否正确，操作请求是否成功。
2. **未创建 application**：读取 Dorado operation log 的提交响应与错误。
3. **application 已创建但未运行**：读取 application state/diagnostics、queue/quota、scheduler rejection、镜像或制品错误。
4. **JM 未启动或 Web 不可达**：仅在 application 从未稳定进入 RUNNING 时按启动处理，读取 JM/container stderr、终态 attempt 和离线日志。
5. **JM 已起但 JobGraph 未 RUNNING**：读取 root exception，区分类加载/配置/序列化、state restore、source/sink 初始化和 slot/resource。
6. **部分 task 卡住**：读取 task execution state、目标 TM、slot、deployment exception、注册和网络；不要把 task state 写成 JobStatus。

## 取证顺序

1. 用 task ID 获取 task metadata、monitor URL 和 operation log。
2. 用 operation log 固定提交/重启时间、版本、操作人和 application ID。
3. 没有当前 Web URL 时，用 task name 搜索所有 Flink application；核对 task tag、attempt、state 和 `_stage`。
4. 读取 application diagnostics、queue usage/quota 和 JM/container 日志。
5. Web 可达时列出实际 job ID，再读取 job details、root exception 和 JM log。
6. 命中 restore/source/sink/connector 错误后才下钻对应 state 或外部依赖。
7. K8s provider 才关联 Pod event；YARN provider 使用 application/container 日志。

若 application 此前已稳定 RUNNING，随后出现 Lag/source 断流、平台仍保留 RUNNING、incident attempt/restart 未变化，并且绑定该 attempt 的 JM REST 或 uptime 断点，转 [failover.md 的 JM 静默强制分支](failover.md#jm-静默或宿主机不可用无-failover)，不要归为“JM 未启动”。

## 症状与证据边界

| 症状 | 可确认的直接证据 | 不足以确认 |
|---|---|---|
| 提交后无 application | operation log 中明确拒绝、参数或鉴权错误 | “平台坏了” |
| application Pending/Accepted | scheduler/queue 明确 quota、affinity、taint、resource rejection | “slot 不够”泛化文本 |
| JM 反复退出 | JM/container termination + root log | 只看到 restart |
| operator `open()`/source init 失败 | 完整 `Caused by` + connector/远端响应 | connector 名称本身 |
| restore 失败 | restore exception + CP/savepoint 元数据/存储错误 | “状态太大” |
| Pod Pending | scheduling event 或 image pull event | Pod phase 本身 |

## 常见分支

### 调度与容量

同时检查请求资源、queue quota、节点碎片、affinity/taint、preemption 和 slot 需求。`NoResourceAvailableException` 可能来自无可用 slot，也可能来自调度控制面；需要 queue/scheduler 直接证据。

### 制品、镜像与依赖

保留 artifact/image 名、版本和失败响应。区分拉取失败、文件不存在、权限、校验失败、类冲突和 connector SDK 不兼容。最近发布与首次失败时间一致时仍只是强候选，需异常栈闭环。

### 状态恢复

读取恢复路径、checkpoint/savepoint ID、operator UID、serializer/schema 与存储响应。路径缺失、权限、损坏、不兼容分别处理；不要用“无状态重启”作为默认建议，先说明状态丢失和 offset/重复消费风险。

### 外部初始化

从异常提取 endpoint、库表/topic/path、错误码和首次时间。只有远端明确 auth/quota/schema/not-found 响应或独立远端证据，才确认外部依赖根因。单独 timeout 保持候选。

## 启动诊断输出

内部必须明确以下事实，并按上层 `SKILL.md` 的“三项紧凑报告契约”只保留能改变判断的内容：

- application 是否创建、当前/最后 attempt 及状态；
- 卡住层级：提交、调度、JM/container、JobGraph、task deployment、restore 或 external init；
- 第一条有区分力的错误；
- 最近变更与错误的时间关系；
- 缺失的日志/事件与停止原因；
- 根因修复和可逆验证步骤。

不要把这些事实展开成独立章节或任务表；根因未确认时，解决方案只保留信息增益最高的一项只读验证。
