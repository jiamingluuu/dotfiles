---
name: bytedance-bytedog
description: "Handles ByteDog operations through bytedcli bytedog whenever users mention ByteDog, remote GDB, flamegraphs, CPU profiling, thread overview, Python thread dumps, Python memory and GC profiling, continuous profiling, host hardware topology, memory bandwidth, jemalloc, off-CPU, pthread or lock contention, PID lookup, profile result downloads, performance diagnostics, or mapping a TCE pod/profile to its deployed SCM version and Codebase source"
---

# ByteDog (`bytedcli bytedog`) — Performance Profiling & Diagnostics

## 如何调用 bytedcli

推荐：先全局安装一次，后续所有命令直接调用 `bytedcli`。

```bash
# 推荐方式：先全局安装，后续直接调用 bytedcli
NPM_CONFIG_REGISTRY=http://bnpm.byted.org npm install -g @bytedance-dev/bytedcli@latest
bytedcli <command> [options]
```

```bash
# Fallback：仅在无法全局安装时使用 npx 临时执行
NPM_CONFIG_REGISTRY=http://bnpm.byted.org npx -y @bytedance-dev/bytedcli@latest <command> [options]
```

## 前置条件

- 使用通用调用方式：`../../invocation.md`
- ByteDog 认证与站点选择：`references/auth.md`
- `bytedcli bytedog` 命令参数: `references/bytedog-command-reference.md`

## Authentication decision

按 [认证说明](references/auth.md) 选择环境并检查 ByteCloud JWT。`data.authenticated=true` 时直接执行命令；只有 `false` 时才登录。同一诊断流程复用已选环境和认证，网络配置见认证说明。

## `--reason` 与 `--question`

- `--reason <text>` 与 `--question <text>` 均为可选，可单独或同时传入。
- `--reason` 说明为什么选择当前命令，以及期望它提供什么信息；不要只复述命令名。
- `--question` 从第一性原理描述要解决的问题或已经观察到的现象；不要把预设结论写成问题。
- 轮询或重复查询同一任务时，后续命令无需重复携带这两个字段；只有需要更新诊断上下文时再传。
- 一个诊断流程执行多条独立命令时，可按当前步骤分别填写，使选命令的目的可独立理解。

示例：

```bash
bytedcli bytedog tool process list \
  --pod demo-pod \
  --reason 'List CPU and RSS usage to select the process that should be profiled' \
  --question 'Which process is causing the observed latency regression?'
```

## When to use

- 获取或解析已有 ByteDog detail URL 或支持的 profiling diff URL，使用 `bytedcli bytedog profile get`；diff 的 base / target 结果会下载为两个独立文件并标记 `comparison_role`。同时传入多个 URL 时，相同数据类型在 `data-format.md` 中只保留一份说明，标题会列出该类型对应的全部结果文件。
- 用户要通过 ByteDog / `bytedcli bytedog` 使用 GDB 分析 coredump、native crash、core 线程或调用栈时，先读 `references/gdb-workflow.md`，再按 `references/bytedog-command-reference.md` 确认参数和输出；默认使用 coredump workflow。
- 只有用户明确要求 attach 在线进程并接受可能暂停或降低性能的影响时，才使用 attach workflow；创建 attach session 及后续每次执行命令都必须显式传 `--confirm-performance-impact`。
- 查询历史 profiling 任务并希望拿到可用结果 URL 时，默认给 `profile <type> list` 加 `--status GOOD`；只有排查运行中或失败任务时再改用 `--status RUNNING` / `--status BAD` 或省略状态过滤。
- 当 profile create 需要 PID，或需要确认主机、TCE Pod、Cloud IDE、大数据分析实例或 Kubernetes 容器里的目标进程、RSS、CPU、命令行时，先用 `bytedcli bytedog tool process list` 列出进程，并让该命令与后续 create 使用相同的目标类型和目标参数组合。不同目标返回的进程结果会有差异，create 与列出进程的目标类型需要保持一致；例如 Kubernetes create 使用 `--ip --k8s-pod --container-id` 时，`tool process list` 也要使用同一组目标参数，不能只传 `--ip`。
- `bytedcli bytedog tool process list` 输出中的 `CPU_%` / JSON `cpu` 来自目标侧 `ps`；Linux `ps` 的 `%CPU` 是进程启动以来累计 CPU time / elapsed time 的生命周期平均值，不是瞬时 CPU 采样。
- `bytedcli bytedog profile oncpu create`：用于 CPU 忙、CPU 使用率高、需要定位 C++/Go/Rust/Java/Python 热点函数或调用栈时；支持主机、TCE Pod、Cloud IDE、大数据分析实例和 Kubernetes 容器目标。如果只想采某个进程，先拿 PID 再传 `--pid`；大数据分析实例目标必须传 `--pid`。
- `bytedcli bytedog profile thread-overview create`：用于快速观察指定进程在短采样窗口内的线程运行、读写等待、阻塞和调度状态分布；所有目标都需要明确 PID，采样时长为 5 到 30 秒。返回的 `/profiling/cpuoverview/single` 详情页可交给 `profile get` 查询状态并下载线程状态时间线 JSON。
- `bytedcli bytedog profile sprofile create`：用于需要机器维度的 continuous profiling、长时间 CPU 画像、历史时间窗口或难以稳定复现的 CPU 问题；该命令只支持 `--ip` 目标。
- `bytedcli bytedog profile je-continuous status/create/list`：用于 TCE Pod 的 jemalloc 常态化内存采集。先执行 `status`；`data_available` 表示最近 7 天已有数据，可执行 `create`。`no_recent_data` 无法区分“未开启”和“已开启但尚未回传”，此时绝不能自行执行 `enable --yes`：如果当前对话或工作流已经提交过 `enable --yes`，等待数据回传后重试 `status/create`；否则先运行不带 `--yes` 的 `enable` 获取 dry-run，并向用户说明实例会重启。观测到的典型资源开销是 CPU 使用率绝对值增加低于 1 个百分点（通常为 0.x 个百分点）、时延几乎不变，内存使用率绝对值增加 10–19 个百分点；提交前必须确认内存余量。只有用户明确接受重启与资源开销后，才用 `--yes` 提交。
- `bytedcli bytedog profile offcpu create`：用于 p99/RT 飙升但 CPU 未饱和、怀疑线程卡在 IO wait、sleep、futex、调度等待或阻塞调用时；支持主机、TCE Pod、大数据分析实例和 Kubernetes 容器目标，需要明确 PID。
- `bytedcli bytedog profile pthread create`：用于怀疑 pthread mutex/rwlock 等用户态锁竞争、锁等待或临界区争用导致延迟时；支持主机、TCE Pod、大数据分析实例和 Kubernetes 容器目标，需要明确 PID。
- `bytedcli bytedog profile je-stats create`：用于快速查看 jemalloc allocator stats，判断 RSS、arena/bin/tcache、碎片或分配状态是否异常；支持主机、TCE Pod、大数据分析实例和 Kubernetes 容器目标，需要明确 PID。
- `bytedcli bytedog profile je-flamegraph create`：用于怀疑 jemalloc 内存泄漏、RSS 持续增长、分配热点不清楚，或需要按调用栈定位内存分配来源时；支持主机、TCE Pod、大数据分析实例和 Kubernetes 容器目标，需要明确 PID。默认 `--type increment` 依赖 jemalloc memory flamegraph enable 状态，TCE Pod 必要时先执行 `bytedcli bytedog profile je-flamegraph enable --pod demo-pod --pid 12345 --wait`；`--type stock` 只支持已完成 ByteDog 专用 jemalloc restart 准备的 TCE Pod，先用 `bytedcli bytedog profile je-flamegraph restart --pod demo-pod --dry-run` 确认请求，再经用户确认后执行 `bytedcli bytedog profile je-flamegraph restart --pod demo-pod --yes --wait`，重启完成后重新查询 PID。不要用普通 TCE cluster restart 代替。
- `bytedcli bytedog profile java-heapdump create`：用于分析 Java heap 使用、疑似内存泄漏、对象分布、引用链、retained size 或 GC 压力来源时；支持在线 TCE / machine / 大数据分析实例目标，需要明确 PID，不支持 Kubernetes 容器。该命令会采集完整 heap 快照，可能短时间影响目标进程，必须传 `--confirm-hang-risk`。
- `bytedcli bytedog profile java-allocation create`：用于线上低开销定位 Java 分配热点、短时间 heap 增长或分配压力来源时；采样结果不是完整分配日志，但通常足够定位热点调用栈。支持在线 TCE / machine / 大数据分析实例目标，需要明确 PID，不支持 Kubernetes 容器。
- `bytedcli bytedog profile java-gc create`：用于分析 Java GC 行为、频繁 GC、Full GC、停顿过长或内存回收效果异常时；支持在线 TCE / machine / 大数据分析实例目标，需要明确 PID，不支持 Kubernetes 容器。
- `bytedcli bytedog profile java-thread create`：用于分析 Java 线程状态、thread dump、线程阻塞、Runnable/Waiting 分布、高 CPU 线程栈或疑似死锁线索时；支持在线 TCE / machine / 大数据分析实例目标，需要明确 PID，不支持 Kubernetes 容器。
- `bytedcli bytedog profile java-lock create`：用于分析 Java 锁竞争、锁等待、锁冲突、monitor/synchronized 热点或疑似死锁时；支持在线 TCE / machine / 大数据分析实例目标，需要明确 PID，不支持 Kubernetes 容器。
- `bytedcli bytedog profile python-thread-dump create`：采集 Python 线程栈快照，用于查看各线程的执行位置和调用栈。
- `bytedcli bytedog profile python-memory create`：采集 Python 内存栈数据，用于比较各调用栈的字节权重；`--duration` 为 1 到 600 秒，默认 30。
- `bytedcli bytedog profile python-gc create`：查看 GC 管理对象按类型统计的计数或计数变化；`--diff-time` 为 0 到 600 秒，默认 30，0 获取当前计数，大于 0 获取两次快照的差分。
- 三类 Python 采集均通过 `--pid` 指定单个进程，支持主机、TCE Pod、Kubernetes 容器。使用对应 list 查询历史，可按 `--ip`、`--creator`、`--status` 筛选，再将详情 URL 交给 `bytedcli bytedog profile get` 下载结果，按同目录 `data-format.md` 解读文件。
- `profile get` 获取失败时，结合错误提示参阅 [ByteDog 排查文档](https://bytedance.larkoffice.com/wiki/WzEewPiW3i4Fi5k6ue5cjTw5nMe)。
- `bytedcli bytedog profile hw-topology create`：用于采集主机 CPU、NUMA、内存和设备拓扑；只支持 `--ip` 机器目标。使用 `hw-topology list` 查询历史任务，使用返回的详情 URL 配合 `profile get` 下载拓扑结果。
- `bytedcli bytedog profile mbw create`：用于采集主机或 TCE Pod 的内存带宽。使用 `mbw list` 查询历史任务，使用 `profile get` 把任务详情保存为 `<id>-memory_bandwidth.json`；满足指标查询条件时还会附加完整指标序列。按同目录 `data-format.md` 说明在本地处理。
- 需要确认 `bytedcli bytedog` 命令参数、输出、限制或示例时，读 `references/bytedog-command-reference.md`。

## 资料索引

执行或推荐命令前，先读命令详情；涉及多步操作时，再读对应流程文件。

| 读取时机                                              | 文件                                                                         |
| ----------------------------------------------------- | ---------------------------------------------------------------------------- |
| 选择命令，确认功能、site 支持、参数、输出、限制与示例 | [命令详情](references/bytedog-command-reference.md)                          |
| 安装或确认 bytedcli 调用方式                          | [通用调用方式](../../invocation.md)                                     |
| 按 ByteDog URL 选择环境，检查认证或网络配置           | [认证说明](references/auth.md)                                               |
| 排查 CLI 调用问题                                     | [通用排查](../../troubleshooting.md)                                    |
| 从 TCE Pod 追溯部署版本与源码                         | [部署源码追溯流程](references/tce-pod-scm-codebase-workflow.md)              |
| 从 TCE PSM、Pod 定位实例并采集 CPU 火焰图             | [TCE on-CPU 流程](references/tce-on-cpu-profile-workflow.md)                 |
| 创建 on-CPU 任务并获取结果                            | [on-CPU 创建到结果流程](references/on-cpu-profile-create-to-get-workflow.md) |
| 从历史任务查找并获取结果                              | [历史查询到结果流程](references/profile-list-to-get-workflow.md)             |
| 执行 GDB/coredump 调试或用户明确要求的在线 attach     | [GDB 流程](references/gdb-workflow.md)                                       |
