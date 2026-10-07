# `bytedcli bytedog` 命令接口说明

本文说明当前 `bytedcli bytedog` 下可执行命令的调用方式、参数、输出、限制与示例。示例中的参数均为占位值。

## Table of Contents

- [特殊site 支持](#特殊site-支持)
- [通用参数与用法](#通用参数与用法)
- [Agent 快速选择](#agent-快速选择)
- [执行约定](#执行约定)
- [`bytedcli bytedog tool coredump list`](#bytedcli-bytedog-tool-coredump-list)
- [`bytedcli bytedog tool elf list`](#bytedcli-bytedog-tool-elf-list)
- [`bytedcli bytedog gdb coredump create`](#bytedcli-bytedog-gdb-coredump-create)
- [`bytedcli bytedog gdb attach create`](#bytedcli-bytedog-gdb-attach-create)
- [`bytedcli bytedog gdb session list`](#bytedcli-bytedog-gdb-session-list)
- [`bytedcli bytedog gdb session get`](#bytedcli-bytedog-gdb-session-get)
- [`bytedcli bytedog gdb command execute`](#bytedcli-bytedog-gdb-command-execute)
- [`bytedcli bytedog gdb command get`](#bytedcli-bytedog-gdb-command-get)
- [`bytedcli bytedog profile get`](#bytedcli-bytedog-profile-get)
- [`bytedcli bytedog profile oncpu create`](#bytedcli-bytedog-profile-oncpu-create)
- [`bytedcli bytedog profile thread-overview create`](#bytedcli-bytedog-profile-thread-overview-create)
- [`bytedcli bytedog profile sprofile create`](#bytedcli-bytedog-profile-sprofile-create)
- [`bytedcli bytedog profile je-continuous status`](#bytedcli-bytedog-profile-je-continuous-status)
- [`bytedcli bytedog profile je-continuous enable`](#bytedcli-bytedog-profile-je-continuous-enable)
- [`bytedcli bytedog profile je-continuous create`](#bytedcli-bytedog-profile-je-continuous-create)
- [`bytedcli bytedog profile offcpu create`](#bytedcli-bytedog-profile-offcpu-create)
- [`bytedcli bytedog profile pthread create`](#bytedcli-bytedog-profile-pthread-create)
- [`bytedcli bytedog profile je-stats create`](#bytedcli-bytedog-profile-je-stats-create)
- [`bytedcli bytedog profile je-flamegraph restart`](#bytedcli-bytedog-profile-je-flamegraph-restart)
- [`bytedcli bytedog profile je-flamegraph enable`](#bytedcli-bytedog-profile-je-flamegraph-enable)
- [`bytedcli bytedog profile je-flamegraph create`](#bytedcli-bytedog-profile-je-flamegraph-create)
- [`bytedcli bytedog profile java-heapdump create`](#bytedcli-bytedog-profile-java-heapdump-create)
- [`bytedcli bytedog profile java-allocation create`](#bytedcli-bytedog-profile-java-allocation-create)
- [`bytedcli bytedog profile java-gc create`](#bytedcli-bytedog-profile-java-gc-create)
- [`bytedcli bytedog profile java-thread create`](#bytedcli-bytedog-profile-java-thread-create)
- [`bytedcli bytedog profile java-lock create`](#bytedcli-bytedog-profile-java-lock-create)
- [`bytedcli bytedog profile python-thread-dump create`](#bytedcli-bytedog-profile-python-thread-dump-create)
- [`bytedcli bytedog profile python-memory create`](#bytedcli-bytedog-profile-python-memory-create)
- [`bytedcli bytedog profile python-gc create`](#bytedcli-bytedog-profile-python-gc-create)
- [`bytedcli bytedog profile hw-topology create`](#bytedcli-bytedog-profile-hw-topology-create)
- [`bytedcli bytedog profile hw-topology list`](#bytedcli-bytedog-profile-hw-topology-list)
- [`bytedcli bytedog profile mbw create`](#bytedcli-bytedog-profile-mbw-create)
- [`bytedcli bytedog profile oncpu list`](#bytedcli-bytedog-profile-oncpu-list)
- [`bytedcli bytedog profile thread-overview list`](#bytedcli-bytedog-profile-thread-overview-list)
- [`bytedcli bytedog profile sprofile list`](#bytedcli-bytedog-profile-sprofile-list)
- [`bytedcli bytedog profile je-continuous list`](#bytedcli-bytedog-profile-je-continuous-list)
- [`bytedcli bytedog profile offcpu list`](#bytedcli-bytedog-profile-offcpu-list)
- [`bytedcli bytedog profile pthread list`](#bytedcli-bytedog-profile-pthread-list)
- [`bytedcli bytedog profile je-stats list`](#bytedcli-bytedog-profile-je-stats-list)
- [`bytedcli bytedog profile je-flamegraph list`](#bytedcli-bytedog-profile-je-flamegraph-list)
- [`bytedcli bytedog profile java-heapdump list`](#bytedcli-bytedog-profile-java-heapdump-list)
- [`bytedcli bytedog profile java-allocation list`](#bytedcli-bytedog-profile-java-allocation-list)
- [`bytedcli bytedog profile java-gc list`](#bytedcli-bytedog-profile-java-gc-list)
- [`bytedcli bytedog profile java-thread list`](#bytedcli-bytedog-profile-java-thread-list)
- [`bytedcli bytedog profile java-lock list`](#bytedcli-bytedog-profile-java-lock-list)
- [`bytedcli bytedog profile python-thread-dump list`](#bytedcli-bytedog-profile-python-thread-dump-list)
- [`bytedcli bytedog profile python-memory list`](#bytedcli-bytedog-profile-python-memory-list)
- [`bytedcli bytedog profile python-gc list`](#bytedcli-bytedog-profile-python-gc-list)
- [`bytedcli bytedog profile mbw list`](#bytedcli-bytedog-profile-mbw-list)
- [`bytedcli bytedog tool process list`](#bytedcli-bytedog-tool-process-list)

## 特殊site 支持

下表列出三个特殊环境的命令可用性。命令均接在 `bytedcli bytedog` 后；目标类型和参数限制见各命令的参数表。

| 命令                                                                                           | `sinf-cn` | `us-ttp` | `eu-ttp` |
| ---------------------------------------------------------------------------------------------- | --------- | -------- | -------- |
| `profile get`                                                                                  | 支持      | 支持     | 支持     |
| `profile oncpu create/list`                                                                    | 支持      | 支持     | 支持     |
| `profile thread-overview create/list`                                                          | 支持      | 支持     | 支持     |
| `profile offcpu create/list`                                                                   | 支持      | 支持     | 支持     |
| `profile pthread create/list`                                                                  | 支持      | 支持     | 支持     |
| `profile java-* create/list`                                                                   | 支持      | 支持     | 支持     |
| `profile je-flamegraph create/list/enable/restart`                                             | 支持      | 支持     | 支持     |
| `profile je-stats create/list`                                                                 | 支持      | 支持     | 支持     |
| `profile sprofile create/list`                                                                 | 不支持    | 支持     | 支持     |
| `profile je-continuous create/list/status/enable`                                              | 不支持    | 支持     | 支持     |
| `profile python-thread-dump create/list`、`python-memory create/list`、`python-gc create/list` | 不支持    | 支持     | 支持     |
| `profile hw-topology create/list`、`mbw create/list`                                           | 不支持    | 支持     | 支持     |
| `tool process list`                                                                            | 支持      | 支持     | 支持     |
| `gdb ...`、`tool coredump list`、`tool elf list`                                               | 不支持    | 不支持   | 不支持   |

| 适用范围                                     | 约定                                                                        |
| -------------------------------------------- | --------------------------------------------------------------------------- |
| `sinf-cn` | 采集目标仅支持 TCE Pod。 |
| TTP：`us-ttp`、`eu-ttp`                      | 各命令的 TTP 目标和参数限制见下文参数表。                                   |
| GDB、coredump/ELF 文件查询                   | 仅支持 `cn`、`i18n-bd`、`i18n-tt`。          |
| URL 与认证环境                               | 按 [认证说明](auth.md) 选择对应 site，并复用该环境的认证。                  |

## 通用参数与用法

下方参数适用于 `bytedcli bytedog` 末级命令。后续每个命令的参数表只列业务参数，不再重复列出这些通用参数。

### bytedcli 全局参数

通用调用方式见入口文档的资料索引，认证与网络配置见 [auth.md](auth.md)。

| 参数            | 默认值                        | 取值                                                             | 用法                                                                                                |
| --------------- | ----------------------------- | ---------------------------------------------------------------- | --------------------------------------------------------------------------------------------------- |
| `--site <site>` | `BYTEDCLI_CLOUD_SITE` 或 `cn` | `cn`、`sinf-cn`、`boe`、`i18n-bd`、`i18n-tt`、`us-ttp`、`eu-ttp` | 需要覆盖默认站点时使用，写在 `bytedcli` 后、`bytedog` 前。                                          |
| `--json`        | `false`                       | 布尔开关                                                         | 输出 bytedcli 标准 JSON envelope；业务对象放在 `data` 字段里，并附 `status` / `error` / `context`。 |

所有命令默认输出文本。需要机器可读输出时，在根命令使用全局 `--json`，例如：

```bash
bytedcli --json bytedog profile get \
  --url 'https://example.bytedog/profiling/on-cpu-profiling/detail?id=1001&from=tce' \
  --output-dir ./bytedog-output
```

### `--reason` 与 `--question`

所有公开 `bytedcli bytedog` 末级命令都支持以下可选参数；两者可单独或同时填写：

| 参数                | 必填 | 默认值 | 说明                                                                     |
| ------------------- | ---- | ------ | ------------------------------------------------------------------------ |
| `--reason <text>`   | 否   | 无     | 为什么选择当前命令，以及期望它提供什么信息。                             |
| `--question <text>` | 否   | 无     | 从第一性原理描述要解决的问题或已经观察到的现象，避免把预设结论写成问题。 |

非 US/EU TTP 请求按 CLI 收到的原始字符串透传；US/EU TTP 请求不会携带这两个字段。轮询或重复查询同一任务时，后续命令无需重复携带；只有需要更新诊断上下文时再传。一个流程中的多条独立 CLI 命令可分别描述当前步骤的选择原因和待解决问题。

```bash
bytedcli bytedog profile oncpu create \
  --pod demo-pod \
  --pid 12345 \
  --reason 'Collect CPU stacks to identify the functions consuming the selected process CPU time' \
  --question 'Which call paths are causing the observed CPU saturation?'
```

## Agent 快速选择

下表命令均接在 `bytedcli bytedog` 后。采集命令异步返回详情页 URL，使用 `profile get` 查询状态并获取结果；每类 profile 的 `list` 用于查询历史任务。

### Profiling 功能

| 命令                                | 适用问题                                  | 采集内容                                       |
| ----------------------------------- | ----------------------------------------- | ---------------------------------------------- |
| `profile oncpu create`              | CPU 忙、使用率高、热点函数定位            | C++/Go/Rust/Java/Python 的 CPU 调用栈。        |
| `profile thread-overview create`    | 短时间内线程为何运行、等待或阻塞          | 线程运行、读写等待、阻塞和调度状态时间线。     |
| `profile sprofile create`           | 长时间 CPU 画像、历史窗口、难以复现的问题 | 机器维度的 continuous profiling。              |
| `profile je-continuous create`      | TCE Pod 常态化内存分析                    | jemalloc 连续内存采集结果。                    |
| `profile offcpu create`             | p99/RT 升高但 CPU 未饱和                  | IO wait、sleep、futex、调度等待或阻塞调用栈。  |
| `profile pthread create`            | 用户态锁竞争、锁等待、临界区争用          | pthread mutex/rwlock 等锁的等待信息。          |
| `profile je-stats create`           | RSS、碎片或分配状态异常                   | jemalloc arena/bin/tcache 等 allocator stats。 |
| `profile je-flamegraph create`      | 内存泄漏、RSS 增长、分配来源不明          | 按调用栈展示 jemalloc 增量或全量内存分配。     |
| `profile java-heapdump create`      | heap 泄漏、对象分布、引用链、GC 压力      | 完整 Java heap 快照与 retained size 分析材料。 |
| `profile java-allocation create`    | 分配热点、短时间 heap 增长                | 低开销分配采样；不是完整分配日志。             |
| `profile java-gc create`            | 频繁 GC、Full GC、停顿或回收效果异常      | Java GC 行为。                                 |
| `profile java-thread create`        | 线程阻塞、高 CPU 线程栈、疑似死锁         | Java thread dump 与线程状态。                  |
| `profile java-lock create`          | monitor/synchronized 竞争或锁等待         | Java 锁竞争与锁等待信息。                      |
| `profile python-thread-dump create` | 查看 Python 各线程的执行位置              | 瞬时线程栈快照。                               |
| `profile python-memory create`      | 比较 Python 各调用栈的内存权重            | 带字节权重的内存栈数据。                       |
| `profile python-gc create`          | 查看 GC 管理对象的数量或变化              | 按类型统计的当前计数或两次快照差分。           |
| `profile hw-topology create`        | 主机硬件布局分析                          | CPU、NUMA、内存和设备拓扑。                    |
| `profile mbw create`                | 主机或 TCE Pod 内存带宽分析               | 任务详情及满足查询条件时的完整指标序列。       |

### 查询与调试

| 命令                                  | 功能                                   | 结果与后续动作                                                                   |
| ------------------------------------- | -------------------------------------- | -------------------------------------------------------------------------------- |
| `profile get`                         | 获取已有详情页或 profiling diff 的结果 | 返回状态和文件位置；diff 的 base/target 分别落盘，有 `data-format.md` 时先读它。 |
| `profile <type> list`                 | 查询历史 profiling 任务                | 返回 `detail_url`；寻找可用结果时优先筛选 `GOOD`。                               |
| `tool process list`                   | 查询 PID、RSS、CPU 和进程命令          | 后续采集使用相同目标类型和参数组合，避免混用宿主机与容器 PID。                   |
| `profile je-continuous status`        | 检查近期是否有常态化内存数据           | 有数据时创建结果；无数据不能判定未开启，已提交 enable 时等待回传。               |
| `profile je-continuous enable`        | 重启 TCE Pod 并开启常态化内存采集      | 默认预览，用户明确接受重启和资源开销后提交；不得因无数据而重复重启。             |
| `profile je-flamegraph enable`        | 启用 TCE Pod 的 jemalloc 增量采集      | 查询到 `GOOD` 后等待采集窗口，再创建增量任务。                                   |
| `profile je-flamegraph restart`       | 准备 TCE Pod 的 jemalloc 全量采集      | 预览并确认服务影响后提交；重启后重新查询 PID，不用普通 TCE restart 代替。        |
| `tool coredump list`、`tool elf list` | 查找远端 coredump/ELF 路径候选         | 路径尚未验证，供 coredump session 使用。                                         |
| `gdb coredump create`                 | 创建 coredump 分析 session             | GDB 默认路径；按 `session_id` 查询到 `GOOD` 后执行命令。                         |
| `gdb attach create`                   | 创建在线进程 attach session            | 仅在用户明确要求并接受性能影响时使用；按 `session_id` 查询状态。                 |
| `gdb session list/get`                | 查找历史 session 或获取 session 详情   | create 结果不确定时先查询，禁止直接重试创建。                                    |
| `gdb command execute`                 | 在 session 中异步执行一条 GDB 命令     | 返回 `ticket_id`；attach 每次执行都要确认性能影响。                              |
| `gdb command get`                     | 按 ticket ID 读取既有命令结果          | 原始输出或错误保存为权限 `0600` 的文件；未完成时用同一 ID 重查，不重新 execute。 |

## 执行约定

- `bytedcli bytedog profile oncpu create` 的目标形态为：`--ip`、`--pod`、`--workspace-id`、`--ip --app-id`、`--ip --k8s-pod --container-id`。其中 `--app-id` 表示大数据分析实例，必须同时传 `--pid`，且只支持 `cpp/java/python`；Kubernetes 容器目标仅非 TTP 站点支持。
- `bytedcli bytedog profile thread-overview create` 通常支持 `--ip`、`--pod`、`--ip --app-id`、`--ip --k8s-pod --container-id`；所有目标都必须传 `--pid`，不支持 Cloud IDE，采样时长为 5 到 30 秒。
- `bytedcli bytedog profile sprofile create` 只支持 `--ip`。
- `bytedcli bytedog profile je-continuous status/create/enable` 只支持 TCE Pod。`status` 的 `no_recent_data` 只能说明最近 7 天无数据，不能判定采集未开启；如果当前工作流已提交过 `enable --yes`，等待数据回传后重试，不要再次重启。若当前工作流没有提交过 `enable --yes`，先运行默认 dry-run；只有用户明确接受实例重启和性能影响后才能用 `--yes` 提交。Agent 不得自行补 `--yes`。
- `bytedcli bytedog profile offcpu create` / `bytedcli bytedog profile pthread create` / `bytedcli bytedog profile je-stats create` / `bytedcli bytedog profile je-flamegraph create` 的目标形态为：`--ip`、`--pod`、`--ip --app-id`、`--ip --k8s-pod --container-id`；都需要 `--pid`。offcpu / pthread / je-flamegraph 的大数据分析实例和 Kubernetes 容器目标仅非 TTP 站点支持。
- `bytedcli bytedog profile je-flamegraph enable` 只支持 `--pod` 和 `--pid`，用于在增量采集前启用 TCE Pod 目标的 jemalloc memory flamegraph 能力。
- `bytedcli bytedog profile je-flamegraph restart` 只支持 `--pod`，不接收 PID。该命令默认 dry-run，只执行状态和权限检查并展示完整请求；必须显式传 `--yes` 才提交可能中断服务进程的 ByteDog jemalloc 准备重启。不要用普通 TCE cluster restart 代替。
- `bytedcli bytedog tool process list` 的目标形态为：`--ip`、`--pod`、`--workspace-id`、`--ip --app-id`、`--ip --k8s-pod --container-id`。
- 除 Python profiles、`hw-topology list`、`mbw list`、`je-continuous list` 外，各 profile list 历史命令至少提供一个过滤条件：`--ip`、`--pod`、`--psm`。这些命令无需目标过滤即可查询；Python profiles 的目标过滤仅支持 `--ip`；`sprofile list` 只接受 `--ip`，不接受 `--pod` / `--psm`；`je-continuous list` 可选 `--ip` 或 `--pod`。
- 查询状态可用的历史记录时，各 profile list 命令默认推荐加 `--status GOOD`，并把选中的 detail URL 交给 `profile get`。只有需要排查运行中或失败任务时，再改用 `--status RUNNING` / `--status BAD` 或省略状态过滤。
- 除 `hw-topology create`、`mbw create` 外，各 profile create 命令和 `bytedcli bytedog tool process list` 会尝试把 `--ip` 输入归一化为 ByteDog 可识别的目标 IP；这两个 GPU profiling 命令直接提交输入值。各 profile list 命令不做 IP 归一化，按传入文本过滤历史记录。
- `--tob` 用于非 TTP 站点的 machine `--ip` 或 Kubernetes `--ip --k8s-pod --container-id` 目标；适用命令包括 `bytedcli bytedog profile oncpu/thread-overview/offcpu/pthread/je-stats/je-flamegraph create` 和 `bytedcli bytedog tool process list`。TTP 站点会忽略该开关。
- `bytedcli bytedog profile java-heapdump create`、`bytedcli bytedog profile java-allocation create`、`bytedcli bytedog profile java-gc create`、`bytedcli bytedog profile java-thread create`、`bytedcli bytedog profile java-lock create` 只支持在线采集目标：`--ip`、`--pod` 或 `--ip --app-id`。本期不支持 Kubernetes、Cloud IDE、本地文件上传、远端 URL 上传。
- `bytedcli bytedog profile java-heapdump create` 会采集完整 Java heap 快照，适合看对象分布、引用链和 retained size；快照文件可能很大，采集过程可能短时间影响目标进程，必须显式传 `--confirm-hang-risk`。JOL heapdump estimates 默认开启，需要关闭时传 `--no-jol`。
- `bytedcli bytedog profile java-allocation create` 是低开销分配采样，适合线上定位分配热点或短时间 heap 增长来源；采样结果不是完整分配日志，但通常足够定位热点调用栈。
- `bytedcli bytedog profile je-flamegraph create` 默认 `--type increment`，要求目标已处于 jemalloc memory flamegraph enable 状态；TCE Pod 目标未 enable 时，先执行 `bytedcli bytedog profile je-flamegraph enable --pod demo-pod --pid 12345 --wait`。`--type stock` 只接受 `valid=true` 且 `type=JEMALLOC_RESTART_TYPE_FLAMEGRAPH` 的 TCE Pod；先 dry-run/确认/提交 `je-flamegraph restart`，重启后重新查询 PID，再创建全量任务。
- 各 profile create 命令只提交异步任务并返回详情页 URL，不等待结果生成。完整结果统一用 `bytedcli bytedog profile get --url <detail-url> --output-dir <dir>` 获取。
- `profile get` 只在详情页任务状态为 `GOOD` 时获取结果。任务仍在运行时会提示稍后重试；任务失败时会输出错误信息和可用提示。若 `GOOD` 详情既没有结果 URL，也不属于可由 CLI 组合生成结果文件的类型，命令会成功返回 `status`、`result_urls` 和空 `files`，不会生成 `data-format.md`。
- `profile get` 支持 on-cpu、off-cpu、jemalloc、continuous profiling 和 jemalloc continuous profiling 的 diff URL。每个 diff 固定解析 base / target 两侧并保存为两个独立文件；Volc 区域路由需要额外的区域账号认证，当前不支持。`/io/playback/diff` 是多任务指标对比而非两个结果文件，不属于 `profile get` 的 diff 下载能力。

## `bytedcli bytedog profile get`

获取一个或多个 ByteDog 详情页或 profiling diff URL 对应的结果。该命令不创建任务。详情页模式返回任务状态、结果 URL 与本地结果文件；支持 `/profiling/cpuoverview/single` 线程状态概览和 `/profiling/jemalloc-profiling/continuous/detail?time=long` jemalloc 常态化内存详情页。diff 模式支持 on-cpu、off-cpu、jemalloc、continuous profiling 和 jemalloc continuous profiling 五类 `/diff` 路径，并把 `base_id` 与 `target_id` 对应的结果分别下载为 `base-<id>-*` 和 `target-<id>-*` 文件。线程状态 gzip 会解压、格式化为 `<id>-thread_state_timeline.json`；jemalloc 常态化结果会解码为 `<id>-bytekd.json`，其中 `mem_records` 是以秒级时间戳为 key 的 map。Memory bandwidth 详情会保存为 `<id>-memory_bandwidth.json`；满足指标查询条件时还会附加完整指标序列。只要产出本地或远端结果文件，就会在输出目录生成 `data-format.md`。可自动下载的小文件会保存到本地；Java heap dump `.hprof` 通常很大，`profile get` 不会自动下载，只会输出远端 TOS URL 和提示。

### 参数

| 参数                 | 必填 | 默认值 | 取值                                                               | 说明                                                                                                                                                                                                                                                                                                                                        |
| -------------------- | ---- | ------ | ------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `--url <url>`        | 是   | 无     | 单个 ByteDog detail / profiling diff URL，或英文逗号分隔的多个 URL | 详情页支持 on-cpu、Thread-state timeline、off-cpu flamegraph、pthread lock、jemalloc stats、jemalloc memory flamegraph、continuous profiling、Java allocation、Java heap dump、Java GC、Java thread、Java lock、host topology、memory bandwidth；diff 支持 on-cpu、off-cpu、jemalloc、continuous profiling、jemalloc continuous profiling。 |
| `--output-dir <dir>` | 否   | `.`    | 本地目录路径                                                       | 保存 `data-format.md` 与本地结果文件的目录。目录不存在时会创建。                                                                                                                                                                                                                                                                            |

### 输出

文本模式输出获取提示、任务目标、结果 URL 和文件列表。若结果里包含不会自动下载的大文件，还会额外输出远端文件 URL 与下载提示；若该类型没有产出本地或远端结果文件，则只输出状态和空 URL 字段提示，不会输出数据列表：

```text
- HINT
成功获取数据，请优先阅读 ./bytedog-output/data-format.md 获取**采集结果数据介绍和使用须知**
- 任务目标
1001: status=GOOD psm=demo.service ip=- podname=demo-pod
- 结果 URL
1001 perf_stack_url: https://example.com/perf.gz
- 数据列表
./bytedog-output/data-format.md
./bytedog-output/1001-perf_stack_url.collapse
```

JSON 模式输出 bytedcli 标准 envelope，业务字段在 `data` 内：

```json
{
  "status": "success",
  "data": {
    "hint": "成功获取数据，请优先阅读 ./bytedog-output/data-format.md 获取采集结果数据介绍和使用须知",
    "status": "GOOD",
    "data_format_path": "./bytedog-output/data-format.md",
    "targets": [
      {
        "id": 1001,
        "comparison_role": null,
        "status": "GOOD",
        "psm": "demo.service",
        "ip": null,
        "podname": "demo-pod"
      }
    ],
    "result_urls": [
      {
        "id": 1001,
        "comparison_role": null,
        "field": "perf_stack_url",
        "url": "https://example.com/perf.gz",
        "description": "on-cpu profiling result"
      }
    ],
    "files": ["./bytedog-output/data-format.md", "./bytedog-output/1001-perf_stack_url.collapse"],
    "remote_files": []
  },
  "error": null,
  "context": {
    "execution_time_ms": 123,
    "timestamp": "2026-06-08T10:00:00+08:00",
    "api_endpoint": "ByteDog Profile Get"
  }
}
```

`profile get` 使用 Python 线程、内存或 GC 任务的详情 URL 下载结果。线程栈和 GC 类型计数保存为 `.json`，内存栈保存为含字节权重的 `.collapsed` 文本，文本结果保存为 `.txt`；同目录 `data-format.md` 说明文件格式、字段、单位和读取方法。获取失败时，结合错误提示参阅 [ByteDog 排查文档](https://bytedance.larkoffice.com/wiki/WzEewPiW3i4Fi5k6ue5cjTw5nMe)。

Python 结果的 `targets[].arguments` 保留实际采集参数，文本模式也展示该参数；其中 `taskArguments` 是 JSON 字符串，解析后读取 `pid`、`duration` 或 `diff_time`。分析历史产物时应核对这些值，尤其用 `diff_time` 区分 GC 快照与差分。

`data-format.md` 会解释每种结果文件的格式和使用注意事项；相同数据类型只输出一份说明，并在对应标题中列出该类型的全部本地文件路径或远端 URL。只有 `data.data_format_path` 非空且 `data.files` 里实际包含 `data-format.md` 时才读取它。结果文件可能包括 `.collapse`、`.json`、`.txt`、`.log` 等格式，具体取决于详情页的 profile 类型和任务结果。Java heap dump 的 `.hprof` 原始文件只会作为远端 URL 输出，不会自动下载；需要复制 `data.remote_files[].url` 或文本模式的远端文件 URL 手动下载。

diff URL 使用 `base_id` / `target_id`（也兼容 `baseId` / `targetId`）标识两侧。JSON 输出的 `targets[]` 与 `result_urls[]` 始终包含 `comparison_role`：普通详情结果为 `null`，diff 两侧分别为 `"base"` 和 `"target"`。Volc 区域路由和 `/io/playback/diff` 当前不支持，命令会返回明确错误。

多个 URL 用英文逗号分隔时，命令会把所有本地结果写入同一个输出目录；只要至少一个 URL 产出本地或远端结果文件，就会生成一份合并后的 `data-format.md` 并写入 `data.data_format_path`。`data.targets`、`data.result_urls` 与 `data.files` 会包含所有任务和本地/远端结果位置；`data.remote_files` 只包含不会自动下载的远端文件。

当详情页任务状态不是 `GOOD` 时，命令不会获取结果文件。任务仍在运行时会提示稍后重试；任务失败时会输出任务错误信息和可用提示。若状态是 `GOOD`，但该类型既没有任何结果 URL，也不能由 CLI 组合生成结果文件，命令会成功返回 `status`、`result_urls`、`data_format_path: null` 和空 `files`，并提示未返回可用结果。

Host topology 详情会通过 ByteDog 的 `fetch_file_by_url` 接口读取 `topoUrl`，按站点响应格式解析 JSON，并保存为 `<id>-host_topology.json`。Memory bandwidth 后端没有提供独立下载 URL；`profile get` 会使用任务详情接口的 camelCase 字段，并在状态为 `GOOD`、没有 `errMsg` 且任务声明了 metrics 时追加指标接口返回的原始 `metricData`，保存为 `<id>-memory_bandwidth.json`。指标请求失败时命令直接失败，不会保存部分结果。具体单位、页面显示换算与本地处理注意事项见同目录 `data-format.md`。

### Example

```bash
bytedcli bytedog profile get \
  --url 'https://example.bytedog/profiling/on-cpu-profiling/detail?id=1001&from=tce' \
  --output-dir ./bytedog-output

bytedcli bytedog profile get \
  --url 'https://example.bytedog/profiling/cpuoverview/single?id=1008&from=machine' \
  --output-dir ./bytedog-output

bytedcli --json bytedog profile get \
  --url 'https://example.bytedog/profiling/on-cpu-profiling/diff?base_id=1001&target_id=1002' \
  --output-dir ./bytedog-output
```

```bash
bytedcli bytedog profile get \
  --url 'https://example.bytedog/profiling/java-profiling/heap/detail?id=1002&from=memory' \
  --output-dir ./bytedog-output
```

```bash
bytedcli bytedog profile get \
  --url 'https://example.bytedog/profiling/java-profiling/heap/detail?id=1007&from=heap' \
  --output-dir ./bytedog-output
```

```bash
bytedcli bytedog profile get \
  --url 'https://example.bytedog/profiling/java-profiling/gc/detail?id=1003&from=gc' \
  --output-dir ./bytedog-output
```

```bash
bytedcli bytedog profile get \
  --url 'https://example.bytedog/profiling/java-profiling/thread/detail?id=1004&from=thread' \
  --output-dir ./bytedog-output
```

```bash
bytedcli bytedog profile get \
  --url 'https://example.bytedog/profiling/java-profiling/lock/detail?id=1005&from=lock' \
  --output-dir ./bytedog-output
```

```bash
bytedcli bytedog profile get \
  --url 'https://example.bytedog/profiling/on-cpu-profiling/detail?id=1001&from=tce,https://example.bytedog/profiling/jemalloc-profiling/stats?id=1006&from=machine' \
  --output-dir ./bytedog-output
```

```bash
bytedcli --json bytedog profile get \
  --url 'https://example.bytedog/profiling/continuous-profiling/detail?id=1006&time=long' \
  --output-dir ./bytedog-output

bytedcli bytedog profile get \
  --url 'https://example.bytedog/profiling/jemalloc-profiling/continuous/detail?id=1006&time=long' \
  --output-dir ./bytedog-output

bytedcli bytedog profile get \
  --url 'https://example.bytedog/gpu-profiling/hw-topology/detail?id=1009' \
  --output-dir ./bytedog-output

bytedcli --json bytedog profile get \
  --url 'https://example.bytedog/gpu-profiling/mbw/detail?id=1010'
```

## `bytedcli bytedog profile hw-topology create`

创建主机硬件拓扑采集任务。只支持机器目标。

| 参数        | 必填 | 默认值 | 取值                | 说明                   |
| ----------- | ---- | ------ | ------------------- | ---------------------- |
| `--ip <ip>` | 是   | 无     | 主机 IP 或 hostname | 要采集拓扑的目标主机。 |

```bash
bytedcli bytedog profile hw-topology create --ip example-host
```

### 输出

文本模式输出任务详情页 URL 和后续 `profile get` 提示。JSON 模式的 `data` 包含 `url` 与 `hint`；把 `url` 中的 `/gpu-profiling/hw-topology/detail?id=<id>` 地址传给 `profile get` 下载拓扑 JSON。create 只提交异步任务，不等待采集完成。

## `bytedcli bytedog profile hw-topology list`

通过 `/api/v2/history/list` 查询主机硬件拓扑采集历史，固定使用 `HOST_TOPOLOGY` 类型。无需目标过滤即可列出历史，也可按 host IP、状态或创建人缩小范围。默认每页返回 20 条，可用 `--page-size` 调整。

| 参数                  | 必填 | 默认值 | 说明                                                     |
| --------------------- | ---- | ------ | -------------------------------------------------------- |
| `--ip <ip>`           | 否   | 无     | 按 `target_ip` 过滤。 |
| `--status <statuses>` | 否   | 无     | 按 `INIT/RUNNING/GOOD/BAD` 状态过滤，可逗号分隔。        |
| `--creator <users>`   | 否   | 无     | 按创建人过滤，可逗号分隔。                               |
| `--page <page>`       | 否   | `1`    | 页码。                                                   |
| `--page-size <size>`  | 否   | `20`   | 每页返回条数。                                           |
| `--url-only`          | 否   | false  | 文本模式只输出 `/gpu-profiling/hw-topology/detail` URL。 |

### 输出

JSON 模式的 `data` 包含 `items`、`page`、`page_size`、`current_count` 与 `has_more`。每个 item 包含 `id`、`profile_type`、`raw_type`、`status`、`target`、`creator`、`description`、`start_at`、`end_at` 和可传给 `profile get` 的 `detail_url`。`current_count` 是当前页条数，不是总数；`has_more=true` 表示可能还有下一页。文本模式默认输出历史任务表格；传 `--url-only` 时每行只输出一个详情 URL。

```bash
bytedcli bytedog profile hw-topology list --status GOOD
bytedcli --json bytedog profile hw-topology list --ip example-host --status GOOD
```

## `bytedcli bytedog profile mbw create`

创建内存带宽采集任务。目标必须是一个主机或一个 TCE Pod。

| 参数                   | 必填     | 默认值 | 取值                | 说明                             |
| ---------------------- | -------- | ------ | ------------------- | -------------------------------- |
| `--ip <ip>`            | 条件必填 | 无     | 主机 IP 或 hostname | 主机目标；与 `--pod` 二选一。 |
| `--pod <podname>`      | 条件必填 | 无     | TCE Pod 名称        | TCE Pod 目标；与 `--ip` 二选一。 |
| `--duration <seconds>` | 否       | `120`  | 数字（秒）          | 采集时长。                       |

```bash
bytedcli bytedog profile mbw create --ip example-host
bytedcli bytedog profile mbw create --pod demo-pod
```

### 输出

文本模式输出任务详情页 URL 和后续 `profile get` 提示。JSON 模式的 `data` 包含 `url` 与 `hint`；把 `url` 中的 `/gpu-profiling/mbw/detail?id=<id>` 地址传给 `profile get` 获取任务详情和指标序列。create 只提交异步任务，不等待采集完成。

## `bytedcli bytedog profile mbw list`

查询内存带宽任务历史。该接口支持按单个 host IP、PSM、状态或创建人过滤。默认每页返回 20 条，可用 `--page-size` 调整。

| 参数                  | 必填 | 默认值 | 说明                                |
| --------------------- | ---- | ------ | ----------------------------------- |
| `--ip <ip>`           | 否   | 无     | 按 host IP 过滤。 |
| `--psm <psm>`         | 否   | 无     | 按 PSM 过滤。 |
| `--status <status>`   | 否   | 无     | 单个 `INIT/RUNNING/GOOD/BAD` 状态。 |
| `--creator <creator>` | 否   | 无     | 按单个创建人过滤。                  |
| `--page <page>`       | 否   | `1`    | 页码。                              |
| `--page-size <size>`  | 否   | `20`   | 每页返回条数。                      |
| `--url-only`          | 否   | false  | 文本模式只输出详情 URL。            |

### 输出

JSON 模式的 `data` 包含 `items`、`page`、`page_size`、`current_count` 与 `has_more`。每个 item 包含 `id`、`profile_type`、`raw_type`、`status`、`target`、`creator`、`description`、`duration`、`err_msg`、`start_at`、`end_at` 和可传给 `profile get` 的 `detail_url`；`target.pid` 保留后端返回的目标 PID。MBW 接口不返回任务类型，因此 `raw_type` 为 `null`。`current_count` 是当前页条数，不是总数；`has_more=true` 表示可能还有下一页。文本模式的历史任务表格包含目标 PID、采集时长和错误信息；传 `--url-only` 时每行只输出一个详情 URL。

```bash
bytedcli bytedog profile mbw list --ip example-host --status GOOD
bytedcli --json bytedog profile mbw list --psm demo.service --status GOOD
```

## `bytedcli bytedog profile oncpu create`

创建 on-cpu flamegraph 异步任务。

### 参数

| 参数                                  | 必填     | 默认值       | 取值                                                                                                                                                                         | 说明                                                                                                                                    |
| ------------------------------------- | -------- | ------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------- |
| `--ip <ip>`                           | 条件必填 | 无           | 主机 IP 或 hostname                                                                                                                                                          | 单独使用时表示机器目标；与 `--app-id` 组合表示大数据分析实例；与 `--k8s-pod --container-id` 组合表示 Kubernetes 容器目标。 |
| `--pod <podname>`                     | 条件必填 | 无           | TCE Pod 名称                                                                                                                                                                 | 用于对 TCE Pod 发起采样。 |
| `--workspace-id <id>`                 | 条件必填 | 无           | Cloud IDE workspace ID                                                                                                                                                       | 用于对 Cloud IDE workspace 发起采样。 |
| `--app-id <application_id>`           | 条件必填 | 无           | 大数据分析实例 Application ID                                                                                                                                                | 与 `--ip` 组合使用，表示大数据分析实例目标；必须同时传 `--pid`，且只支持 `--type cpp/java/python`。 |
| `--k8s-pod <podname>`                 | 条件必填 | 无           | Kubernetes Pod 名称                                                                                                                                                          | 与 `--ip --container-id` 组合使用，表示 Kubernetes 容器目标；仅非 TTP 站点支持。 |
| `--container-id <container_id>`       | 条件必填 | 无           | Kubernetes container ID                                                                                                                                                      | 与 `--ip --k8s-pod` 组合使用，表示 Kubernetes 容器目标；仅非 TTP 站点支持。 |
| `--idc <idc>`                         | 否       | 无           | IDC 标识                                                                                                                                                                     | 只在 `--pod` 目标下可选使用，用于 Pod 歧义消解；默认不需要传。                                                                          |
| `--container-type <primary\|sidecar>` | 否       | `primary`    | `primary`、`sidecar`                                                                                                                                                         | 只在 `--pod` 目标下可选使用，用于容器歧义消解。                                                                                         |
| `--pid <pid>`                         | 否       | 无           | 单个正整数 PID                                                                                                                                                               | 限定单进程采样。只允许一个 PID，不支持逗号或空格分隔。                                                                                  |
| `--duration <seconds>`                | 否       | `30`         | `1` 到 `300` 的整数秒；`python --tools-type ebpf_profiler` 最少 `10` 秒                                                                                                      | 采样时长。超过 `300` 秒会自动按 `300` 秒提交；启用 `--inline` 且 `--pid` 存在、工具为 `perf` 或 `bytekd` 时，实际采样时长最多 `5` 秒。  |
| `--type <type>`                       | 否       | `cpp`        | `cpp`、`java`、`python`、`go`、`rust`                                                                                                                                        | 采样语言类型。                                                                                                                          |
| `--tools-type <type>`                 | 否       | 按语言决定   | `perf`、`bcc`、`bytekd`、`ebpf_profiler`、`pyspy`                                                                                                                            | `cpp/go/rust` 默认 `bytekd`，允许 `perf/bcc/bytekd`；`python` 默认 `ebpf_profiler`，TTP 站点只允许并默认 `pyspy`；`java` 不支持，传入会报错。 |
| `--callgraph-type <type>`             | 否       | `fp`         | `fp`、`lbr`、`dwarf`                                                                                                                                                         | 仅在 `--tools-type perf` 时生效。                                                                                                       |
| `--interval <ns>`                     | 否       | `10000000`   | 正整数纳秒                                                                                                                                                                   | 仅在 `--type java` 时生效，表示 Java 采样间隔。                                                                                         |
| `--perf-event <event[,event...]>`     | 否       | `cpu-cycles` | `cpu-cycles`、`cpu-clock`、`branch-misses`、`L1-icache-load-misses`、`L1-dcache-load-misses`、`LLC-load-misses`、`iTLB-load-misses`、`dTLB-load-misses`、`dTLB-store-misses` | 仅在 `--tools-type perf` 时生效。多个值用英文逗号分隔。                                                                                 |
| `--inline`                            | 否       | `false`      | 布尔开关                                                                                                                                                                     | 在 `--pid` 存在且工具为 `perf` 或 `bytekd` 时解析 inline frame，并把实际采样时长限制在最多 `5` 秒。                                     |
| `--line-info`                         | 否       | `false`      | 布尔开关                                                                                                                                                                     | 在 `--inline`、`--pid`、`--tools-type perf` 同时满足时解析源码行信息。                                                                  |
| `--python-subprocess`                 | 否       | `false`      | 布尔开关                                                                                                                                                                     | 仅在 `--type python` 时包含 Python 子进程。                                                                                             |
| `--include-idle`                      | 否       | `false`      | 布尔开关                                                                                                                                                                     | 仅在 `--type python --tools-type pyspy` 时包含 idle 样本；与其他 Python 工具组合会报错。                                                |
| `--include-native`                    | 否       | `true`       | 布尔开关                                                                                                                                                                     | 仅在 `--type python` 时包含 native Python stacks；当前 CLI 不提供关闭开关。                                                             |
| `--tob`                               | 否       | `false`      | 布尔开关                                                                                                                                                                     | 非 TTP 站点支持机器 `--ip` 目标和 Kubernetes 容器目标。用于 ToB 或 mysql 机器模式；TTP 站点会忽略该参数。 |

目标形态必须恰好匹配一种：`--ip`、`--pod`、`--workspace-id`、`--ip --app-id`、`--ip --k8s-pod --container-id`。多传、少传或混用都会报输入错误。大数据分析实例目标必须传 `--pid`，并且不支持 `--type go` / `--type rust`。

### 输出

创建成功后输出详情页 URL 和后续获取命令提示。命令只提交异步任务，不等待结果文件生成。

```json
{
  "status": "success",
  "data": {
    "url": "https://example.bytedog/profiling/on-cpu-profiling/detail?id=1001&from=machine",
    "hint": "任务创建成功，执行 `bytedcli bytedog profile get --url 'https://example.bytedog/profiling/on-cpu-profiling/detail?id=1001&from=machine' --output-dir ./bytedog-output` 查看任务状态以及获取结果数据。"
  },
  "error": null,
  "context": {
    "execution_time_ms": 123,
    "timestamp": "2026-06-08T10:00:00+08:00",
    "api_endpoint": "ByteDog Profile Create"
  }
}
```

### Example

```bash
bytedcli bytedog profile oncpu create \
  --ip example-host
```

```bash
bytedcli bytedog profile oncpu create \
  --pod demo-pod \
  --pid 12345 \
  --type go \
  --tools-type perf \
  --perf-event cpu-clock,branch-misses \
  --inline
```

```bash
bytedcli --json bytedog profile oncpu create \
  --workspace-id sample-workspace \
  --type python \
  --tools-type pyspy \
  --include-idle
```

```bash
bytedcli bytedog profile oncpu create \
  --ip example-host \
  --app-id sample-application \
  --pid 12345
```

```bash
bytedcli bytedog profile oncpu create \
  --ip example-host \
  --k8s-pod demo-pod \
  --container-id sample-container
```

## `bytedcli bytedog profile thread-overview create`

创建线程状态概览异步任务。该命令采集单个进程 5 到 30 秒的线程运行、读写等待、阻塞和调度状态分布，返回 `/profiling/cpuoverview/single` 详情页 URL，不等待结果生成。把详情页 URL 交给 `bytedcli bytedog profile get` 可查询状态并下载线程状态时间线 JSON。

### 参数

| 参数                                  | 必填     | 默认值    | 取值                    | 说明                                                                                                         |
| ------------------------------------- | -------- | --------- | ----------------------- | ------------------------------------------------------------------------------------------------------------ |
| `--ip <ip>`                           | 条件必填 | 无        | 主机 IP 或 hostname     | 单独使用表示 machine；与 `--app-id` 表示大数据分析实例；与 `--k8s-pod --container-id` 表示 Kubernetes 容器。 |
| `--pod <podname>`                     | 条件必填 | 无        | TCE Pod 名称            | TCE Pod 目标。 |
| `--app-id <application_id>`           | 条件必填 | 无        | Application ID          | 与 `--ip --pid` 一起表示大数据分析实例。 |
| `--k8s-pod <podname>`                 | 条件必填 | 无        | Kubernetes Pod 名称     | 与 `--ip --container-id --pid` 一起表示 Kubernetes 容器。 |
| `--container-id <container_id>`       | 条件必填 | 无        | Kubernetes container ID | 与 `--ip --k8s-pod --pid` 一起表示 Kubernetes 容器。 |
| `--idc <idc>`                         | 否       | 无        | IDC 标识                | 仅用于 TCE Pod 歧义消解。                                                                                    |
| `--container-type <primary\|sidecar>` | 否       | `primary` | `primary`、`sidecar`    | 仅用于 TCE 容器歧义消解。                                                                                    |
| `--pid <pid>`                         | 是       | 无        | 单个正整数 PID          | 采集进程；不支持逗号或空格分隔。                                                                             |
| `--duration <seconds>`                | 否       | `30`      | `5` 到 `30` 的整数秒    | 线程状态概览采样时长，超出范围直接报输入错误。                                                               |
| `--tob`                               | 否       | `false`   | 布尔开关                | 非 TTP 的 machine/Kubernetes 使用 ToB executor；TTP 忽略。 |

目标形态必须恰好匹配 `--ip`、`--pod`、`--ip --app-id`、`--ip --k8s-pod --container-id` 之一，且必须传 `--pid`。Cloud IDE 不受支持。

### 输出

文本模式输出提示和详情页 URL。JSON 模式输出：

```json
{
  "status": "success",
  "data": {
    "url": "https://example.bytedog/profiling/cpuoverview/single?id=1301&from=tce",
    "hint": "任务创建成功，执行 `bytedcli bytedog profile get --url 'https://example.bytedog/profiling/cpuoverview/single?id=1301&from=tce' --output-dir ./bytedog-output` 查看任务状态以及获取结果数据。"
  },
  "error": null,
  "context": {
    "execution_time_ms": 123,
    "timestamp": "2026-07-10T10:00:00+08:00",
    "api_endpoint": "ByteDog Profile Create"
  }
}
```

### Example

```bash
bytedcli bytedog profile thread-overview create \
  --pod demo-pod \
  --pid 12345

bytedcli bytedog profile thread-overview create \
  --ip example-host \
  --app-id sample-application \
  --pid 12345

bytedcli --json bytedog profile thread-overview create \
  --ip example-host \
  --k8s-pod demo-pod \
  --container-id sample-container \
  --pid 12345
```

## `bytedcli bytedog profile sprofile create`

创建 continuous flamegraph 异步任务。

### 参数

| 参数                     | 必填 | 默认值                  | 取值                   | 说明                                                                                        |
| ------------------------ | ---- | ----------------------- | ---------------------- | ------------------------------------------------------------------------------------------- |
| `--ip <ip>`              | 是   | 无                      | 主机 IP 或 hostname    | 只支持机器目标。 |
| `--duration <seconds>`   | 否   | `1800`                  | `1` 到 `3600` 的整数秒 | 采集时长。超过 `3600` 秒会自动按 `3600` 秒提交。                                            |
| `--start <unix_seconds>` | 否   | 当前时间减去 `duration` | Unix 秒级时间戳        | 采集开始时间。                                                                              |
| `--tob`                  | 否   | `false`                 | 布尔开关               | 非 TTP 站点仅支持 `--ip` 目标。显式传入时使用 ToB 或 mysql 机器模式；TTP 站点会忽略该参数。 |

该命令不支持 `--pod` 和 `--workspace-id`。默认使用内场机器模式；非 TTP 站点显式传入 `--tob` 时使用 ToB 或 mysql 机器模式。

### 输出

创建成功后输出详情页 URL 和后续获取命令提示。命令只提交异步任务，不等待结果文件生成。

```json
{
  "status": "success",
  "data": {
    "url": "https://example.bytedog/profiling/continuous-profiling/detail?id=1003&time=long",
    "hint": "任务创建成功，执行 `bytedcli bytedog profile get --url 'https://example.bytedog/profiling/continuous-profiling/detail?id=1003&time=long' --output-dir ./bytedog-output` 查看任务状态以及获取结果数据。"
  },
  "error": null,
  "context": {
    "execution_time_ms": 123,
    "timestamp": "2026-06-08T10:00:00+08:00",
    "api_endpoint": "ByteDog Profile Create"
  }
}
```

### Example

```bash
bytedcli bytedog profile sprofile create \
  --ip example-host
```

```bash
bytedcli bytedog profile sprofile create \
  --ip example-host \
  --duration 900 \
  --start 1700000000
```

```bash
bytedcli --json bytedog profile sprofile create \
  --ip example-host
```

## `bytedcli bytedog profile je-continuous status`

只读检查 TCE Pod 最近 7 天是否有 jemalloc 常态化内存数据回传。请求会显式传入当前 Unix 秒级时间戳及其 7 天前的时间戳；“无数据”不等于“未开启”，也可能表示开启后尚未回传。

### 参数

| 参数              | 必填 | 默认值 | 取值         | 说明               |
| ----------------- | ---- | ------ | ------------ | ------------------ |
| `--pod <podname>` | 是   | 无     | TCE Pod 名称 | 要检查的实例名称。 |

### 输出与安全决策

- `availability=data_available`、`enabled_state=confirmed_by_recent_data`：已有数据证据，可以执行 `je-continuous create`。
- `availability=no_recent_data`、`enabled_state=unknown`：只能确定最近 7 天无数据，可能是 `not_enabled`，也可能是 `enabled_but_data_not_ready`。
- 无数据时固定返回 `auto_enable_allowed=false` 和 `recommended_action=wait_if_enable_was_submitted_otherwise_preview_then_ask_user_before_enable`。
- 如果当前对话或工作流已经执行过 `je-continuous enable --yes`，实例已经进入重启/开启流程；等待数据回传后重试 `status/create`，不要再次提交 `enable`。
- 如果当前工作流没有执行过 `enable --yes`，先运行默认 dry-run，把“实例会重启、常态化采集可能影响性能”以及待提交的 endpoint/payload 告知用户并询问是否需要开启。只有用户明确接受两项风险后才能补 `--yes`；Agent 不得自行提交。

### Example

```bash
bytedcli bytedog profile je-continuous status \
  --pod demo-pod

bytedcli --json bytedog profile je-continuous status \
  --pod demo-pod
```

## `bytedcli bytedog profile je-continuous enable`

重启目标 TCE Pod 并开启 jemalloc 常态化内存采集。观测到的典型资源开销是 CPU 使用率绝对值增加低于 1 个百分点（通常为 0.x 个百分点）、时延几乎不变，内存使用率绝对值增加 10–19 个百分点；提交前必须确认实例有足够的内存余量。该操作属于需要用户明确确认的高风险写操作。

### 参数

| 参数                                  | 必填 | 默认值    | 取值                  | 说明                                                                      |
| ------------------------------------- | ---- | --------- | --------------------- | ------------------------------------------------------------------------- |
| `--pod <podname>`                     | 是   | 无        | TCE Pod 名称          | 要重启并开启采集的实例。 |
| `--container-type <primary\|sidecar>` | 否   | `primary` | `primary`、`sidecar`  | 容器类型。                                                                |
| `--dry-run`                           | 否   | 默认行为  | 布尔开关              | 只输出完整 endpoint/payload 与风险，不提交重启；不能和 `--yes` 同时使用。 |
| `--yes`                               | 否   | `false`   | 布尔开关              | 用户明确接受实例重启和资源开销后才可传入；只有该开关会真正提交。          |
| `--wait`                              | 否   | `false`   | 布尔开关              | 等待开启任务达到终态；`GOOD` 成功，`BAD` 失败。                            |
| `--wait-timeout <seconds>`            | 否   | `600`     | `1` 到 `86400` 的整数 | `--wait` 的最长等待秒数。                                                 |
| `--wait-interval <seconds>`           | 否   | `5`       | `1` 到 `3600` 的整数  | `--wait` 的轮询间隔秒数。                                                 |

命令默认 dry-run；不传 `--yes` 时不会改变目标。Agent 必须先展示预览并获得用户明确表态，不能因为 `status` 返回 `no_recent_data` 就自行补 `--yes`。如果本工作流已经提交过本命令，后续无数据表示需要等待回传，不得重复重启。

### 输出

dry-run 的 JSON 输出包含 `dry_run=true`、`submitted=false`、`endpoint`、`payload`、`pod`、`container_type` 与后续确认提示。用 `--yes` 提交后包含任务 `id`、`status`、`waited`；轮询中只有 `GOOD`/`BAD` 表示任务结束。`BAD` 始终以结构化错误失败退出，即使后端没有返回 `errMsg`；非空 `errMsg` 或 API 错误同样表示失败，其余响应继续等待。`GOOD` 仅表示重启/开启任务完成，数据回传仍可能延迟。

### Example

```bash
bytedcli bytedog profile je-continuous enable \
  --pod demo-pod

# 仅在用户已经明确接受实例重启和性能影响后执行
bytedcli bytedog profile je-continuous enable \
  --pod demo-pod \
  --yes \
  --wait
```

## `bytedcli bytedog profile je-continuous create`

从已有 jemalloc 常态化内存数据创建采集结果。命令只支持 TCE Pod，会先检查最近 7 天是否已有数据回传，用于判断重启后的采集是否已经运行；该前置检查不校验 `--start` / `--duration` 请求窗口。create 接口只能拉取时间戳位于过去 7 天内的留存数据，单次请求窗口仍最长 12 小时；实际结束时间及留存边界由后端校验。无数据时拒绝创建，但不会自动开启采集或重启实例。

### 参数

| 参数                     | 必填 | 默认值                  | 取值                             | 说明                             |
| ------------------------ | ---- | ----------------------- | -------------------------------- | -------------------------------- |
| `--pod <podname>`        | 是   | 无                      | TCE Pod 名称                     | 要生成采集结果的实例。 |
| `--duration <seconds>`   | 否   | `300`                   | `60` 到 `43200` 的整数秒         | 结果时间窗口长度，最长 12 小时。 |
| `--start <unix_seconds>` | 否   | 当前时间减去 `duration` | 不晚于当前时间的 Unix 秒级时间戳 | 结果时间窗口开始时间；只能拉取时间戳位于过去 7 天内的留存数据。 |
| `--question <text>`      | 否   | 无                      | 文本                             | 非 TTP 站点随 create 请求上传。  |
| `--reason <text>`        | 否   | 无                      | 文本                             | 非 TTP 站点随 create 请求上传。  |

如果状态结果为 `no_recent_data`：当前流程已提交过 `enable --yes` 时等待并重试；否则先 dry-run，再询问用户是否接受重启和性能影响。任何情况下都不能由 Agent 自动补 `--yes`。

### 输出

创建成功后输出 jemalloc continuous 详情页 URL。命令只提交异步结果任务，不等待结果生成；后续可将 URL 交给 `profile get`。

### Example

```bash
bytedcli bytedog profile je-continuous create \
  --pod demo-pod

bytedcli --json bytedog profile je-continuous create \
  --pod demo-pod \
  --duration 600 \
  --start 1700000000
```

## `bytedcli bytedog profile offcpu create`

创建 off-cpu flamegraph 异步任务。

### 参数

| 参数                                  | 必填     | 默认值    | 取值                          | 说明                                                                                                                       |
| ------------------------------------- | -------- | --------- | ----------------------------- | -------------------------------------------------------------------------------------------------------------------------- |
| `--ip <ip>`                           | 条件必填 | 无        | 主机 IP 或 hostname           | 单独使用时表示机器目标；与 `--app-id` 组合表示大数据分析实例；与 `--k8s-pod --container-id` 组合表示 Kubernetes 容器目标。 |
| `--pod <podname>`                     | 条件必填 | 无        | TCE Pod 名称                  | 用于对 TCE Pod 发起采样。 |
| `--app-id <application_id>`           | 条件必填 | 无        | 大数据分析实例 Application ID | 与 `--ip` 组合使用，表示大数据分析实例目标；仅非 TTP 站点支持。 |
| `--k8s-pod <podname>`                 | 条件必填 | 无        | Kubernetes Pod 名称           | 与 `--ip --container-id` 组合使用，表示 Kubernetes 容器目标；仅非 TTP 站点支持。 |
| `--container-id <container_id>`       | 条件必填 | 无        | Kubernetes container ID       | 与 `--ip --k8s-pod` 组合使用，表示 Kubernetes 容器目标；仅非 TTP 站点支持。 |
| `--idc <idc>`                         | 否       | 无        | IDC 标识                      | 只在 `--pod` 目标下可选使用，用于 Pod 歧义消解；默认不需要传。                                                             |
| `--container-type <primary\|sidecar>` | 否       | `primary` | `primary`、`sidecar`          | 只在 `--pod` 目标下可选使用，用于容器歧义消解。                                                                            |
| `--pid <pid>`                         | 是       | 无        | 单个正整数 PID                | 采集进程。只允许一个 PID，不支持逗号或空格分隔。                                                                           |
| `--duration <seconds>`                | 否       | `30`      | `1` 到 `300` 的整数秒         | 采样时长。超过 `300` 秒会自动按 `300` 秒提交。                                                                             |
| `--tools-type <type>`                 | 否       | `bytekd`  | `bcc`、`bytekd`               | off-cpu 采样工具类型。                                                                                                     |
| `--enhance`                           | 否       | `true`    | 布尔开关                      | 启用增强栈解析。                                                                                                           |
| `--tob`                               | 否       | `false`   | 布尔开关                      | 非 TTP 站点支持机器 `--ip` 目标和 Kubernetes 容器目标。用于 ToB 或 mysql 机器模式；TTP 站点会忽略该参数。 |

目标形态必须恰好匹配一种：`--ip`、`--pod`、`--ip --app-id`、`--ip --k8s-pod --container-id`。多传、少传或混用都会报输入错误。

### 输出

创建成功后输出详情页 URL 和后续获取命令提示。命令只提交异步任务，不等待结果文件生成。

### Example

```bash
bytedcli bytedog profile offcpu create \
  --pod demo-pod \
  --pid 12345
```

```bash
bytedcli bytedog profile offcpu create \
  --ip example-host \
  --pid 12345 \
  --tools-type bcc
```

```bash
bytedcli --json bytedog profile offcpu create \
  --ip example-host \
  --pid 12345
```

```bash
bytedcli bytedog profile offcpu create \
  --ip example-host \
  --app-id sample-application \
  --pid 12345

bytedcli bytedog profile offcpu create \
  --ip example-host \
  --k8s-pod demo-pod \
  --container-id sample-container \
  --pid 12345
```

## `bytedcli bytedog profile pthread create`

创建 pthread lock profiling 异步任务。

### 参数

| 参数                                  | 必填     | 默认值                       | 取值                          | 说明                                                                                                                       |
| ------------------------------------- | -------- | ---------------------------- | ----------------------------- | -------------------------------------------------------------------------------------------------------------------------- |
| `--ip <ip>`                           | 条件必填 | 无                           | 主机 IP 或 hostname           | 单独使用时表示机器目标；与 `--app-id` 组合表示大数据分析实例；与 `--k8s-pod --container-id` 组合表示 Kubernetes 容器目标。 |
| `--pod <podname>`                     | 条件必填 | 无                           | TCE Pod 名称                  | 用于对 TCE Pod 发起采样。 |
| `--app-id <application_id>`           | 条件必填 | 无                           | 大数据分析实例 Application ID | 与 `--ip` 组合使用，表示大数据分析实例目标；仅非 TTP 站点支持。 |
| `--k8s-pod <podname>`                 | 条件必填 | 无                           | Kubernetes Pod 名称           | 与 `--ip --container-id` 组合使用，表示 Kubernetes 容器目标；仅非 TTP 站点支持。 |
| `--container-id <container_id>`       | 条件必填 | 无                           | Kubernetes container ID       | 与 `--ip --k8s-pod` 组合使用，表示 Kubernetes 容器目标；仅非 TTP 站点支持。 |
| `--idc <idc>`                         | 否       | 无                           | IDC 标识                      | 只在 `--pod` 目标下可选使用，用于 Pod 歧义消解；默认不需要传。                                                             |
| `--container-type <primary\|sidecar>` | 否       | `primary`                    | `primary`、`sidecar`          | 只在 `--pod` 目标下可选使用，用于容器歧义消解。                                                                            |
| `--pid <pid>`                         | 是       | 无                           | 单个正整数 PID                | 采集进程。只允许一个 PID，不支持逗号或空格分隔。                                                                           |
| `--duration <seconds>`                | 否       | `30`                         | `1` 到 `300` 的整数秒         | 采样时长。超过 `300` 秒会自动按 `300` 秒提交。                                                                             |
| `--enhance`                           | 否       | 非 TTP: `true`；TTP: `false` | 布尔开关                      | 启用增强栈解析。                                                                                                           |
| `--tob`                               | 否       | `false`                      | 布尔开关                      | 非 TTP 站点支持机器 `--ip` 目标和 Kubernetes 容器目标。用于 ToB 或 mysql 机器模式；TTP 站点会忽略该参数。 |

目标形态必须恰好匹配一种：`--ip`、`--pod`、`--ip --app-id`、`--ip --k8s-pod --container-id`。多传、少传或混用都会报输入错误。

### 输出

创建成功后输出详情页 URL 和后续获取命令提示。命令只提交异步任务，不等待结果文件生成。

### Example

```bash
bytedcli bytedog profile pthread create \
  --pod demo-pod \
  --pid 12345 \
  --duration 120
```

```bash
bytedcli --json bytedog profile pthread create \
  --ip example-host \
  --pid 12345
```

```bash
bytedcli bytedog profile pthread create \
  --ip example-host \
  --app-id sample-application \
  --pid 12345

bytedcli bytedog profile pthread create \
  --ip example-host \
  --k8s-pod demo-pod \
  --container-id sample-container \
  --pid 12345
```

## `bytedcli bytedog profile je-stats create`

创建 jemalloc stats 异步任务。

### 参数

| 参数                                  | 必填     | 默认值    | 取值                          | 说明                                                                                                                       |
| ------------------------------------- | -------- | --------- | ----------------------------- | -------------------------------------------------------------------------------------------------------------------------- |
| `--ip <ip>`                           | 条件必填 | 无        | 主机 IP 或 hostname           | 单独使用时表示机器目标；与 `--app-id` 组合表示大数据分析实例；与 `--k8s-pod --container-id` 组合表示 Kubernetes 容器目标。 |
| `--pod <podname>`                     | 条件必填 | 无        | TCE Pod 名称                  | 用于对 TCE Pod 发起采样。 |
| `--app-id <application_id>`           | 条件必填 | 无        | 大数据分析实例 Application ID | 与 `--ip` 组合使用，表示大数据分析实例目标。 |
| `--k8s-pod <podname>`                 | 条件必填 | 无        | Kubernetes Pod 名称           | 与 `--ip --container-id` 组合使用，表示 Kubernetes 容器目标。 |
| `--container-id <container_id>`       | 条件必填 | 无        | Kubernetes container ID       | 与 `--ip --k8s-pod` 组合使用，表示 Kubernetes 容器目标。 |
| `--idc <idc>`                         | 否       | 无        | IDC 标识                      | 只在 `--pod` 目标下可选使用，用于 Pod 歧义消解；默认不需要传。                                                             |
| `--container-type <primary\|sidecar>` | 否       | `primary` | `primary`、`sidecar`          | 只在 `--pod` 目标下可选使用，用于容器歧义消解。                                                                            |
| `--pid <pid>`                         | 是       | 无        | 单个正整数 PID                | 采集进程。只允许一个 PID，不支持逗号或空格分隔。                                                                           |
| `--tob`                               | 否       | `false`   | 布尔开关                      | 非 TTP 站点支持机器 `--ip` 目标和 Kubernetes 容器目标。用于 ToB 或 mysql 机器模式；TTP 站点会忽略该参数。 |

目标形态必须恰好匹配一种：`--ip`、`--pod`、`--ip --app-id`、`--ip --k8s-pod --container-id`。多传、少传或混用都会报输入错误。

### 输出

创建成功后输出详情页 URL 和后续获取命令提示。命令只提交异步任务，不等待结果文件生成。

### Example

```bash
bytedcli bytedog profile je-stats create \
  --ip example-host \
  --pid 12345
```

```bash
bytedcli --json bytedog profile je-stats create \
  --pod demo-pod \
  --pid 12345
```

```bash
bytedcli bytedog profile je-stats create \
  --ip example-host \
  --app-id sample-application \
  --pid 12345

bytedcli bytedog profile je-stats create \
  --ip example-host \
  --k8s-pod demo-pod \
  --container-id sample-container \
  --pid 12345
```

## `bytedcli bytedog profile je-flamegraph restart`

为 TCE Pod 全量 jemalloc memory flamegraph 准备采集环境。该命令复现 ByteDog Jemalloc Profiling 页面的专用流程：先查询目标 jemalloc 状态，再检查当前身份是否有重启权限，最后由 ByteDog 注入所选 jemalloc profiling 配置并重启服务程序。普通 TCE cluster restart 不会完成这项准备，不能替代本命令。

该动作可能中断服务进程，因此命令默认 dry-run：不传 `--yes` 时只执行只读状态/权限检查，并输出即将提交的完整 endpoint 与 payload；显式 `--dry-run` 可用于在脚本或操作记录中标明预览意图。只有传 `--yes` 才提交 restart，`--dry-run` 与 `--yes` 不能同时使用。

### 参数

| 参数                                  | 必填         | 默认值                             | 取值                                              | 说明                                                  |
| ------------------------------------- | ------------ | ---------------------------------- | ------------------------------------------------- | ----------------------------------------------------- |
| `--pod <podname>`                     | 是           | 无                                 | TCE Pod 名称                                      | ByteDog jemalloc restart 只支持 TCE Pod，不接收 PID。 |
| `--idc <idc>`                         | 否           | 无                                 | IDC 标识                                          | 用于 Pod 歧义消解。                                   |
| `--container-type <primary\|sidecar>` | 否           | `primary`                          | `primary`、`sidecar`                              | 选择要准备的 TCE 容器。                               |
| `--je-version <version>`              | 否           | `5.2.1.flame_graph.bytedog`        | `5.2.1.flame_graph.bytedog`、`5.2.1.bm.2.bytedog` | ByteDog 注入的 jemalloc profiling 版本。              |
| `--static-linked`                     | 否           | `false`                            | 布尔开关                                          | 目标二进制静态链接 jemalloc 时启用。                  |
| `--dry-run`                           | 否           | 未传 `--yes` 时自动按 dry-run 执行 | 布尔开关                                          | 展示请求但不提交 restart。                            |
| `--yes`                               | 正式提交必需 | `false`                            | 布尔开关                                          | 确认已审阅 dry-run 和服务影响，并提交 restart。       |
| `--wait`                              | 否           | `false`                            | 布尔开关                                          | 提交后等待任务状态变为 `GOOD`。                       |
| `--wait-timeout <seconds>`            | 否           | `600`                              | `1` 到 `86400` 的整数秒                           | 配合 `--wait` 使用的最长等待时间。                    |
| `--wait-interval <seconds>`           | 否           | `5`                                | `1` 到 `3600` 的整数秒                            | 配合 `--wait` 使用的轮询间隔。                        |

### 输出

Dry-run 文本和 JSON 都包含当前 jemalloc 状态、权限结果、完整 endpoint 与实际 payload，但不会输出认证 header。JSON 业务对象的关键字段为：

```json
{
  "action": "restart",
  "dry_run": true,
  "submitted": false,
  "endpoint": "https://example.bytedog-api/api/v2/memory/flamegraph/tce/create",
  "payload": {
    "action": "restart",
    "async": true,
    "podname": "demo-pod",
    "container_type": "primary",
    "jeversion": "5.2.1.flame_graph.bytedog",
    "static_linked": false
  },
  "current_state": {
    "valid": false,
    "type": null,
    "jeversion": null
  },
  "permission": {
    "has_priv": true,
    "url": null
  },
  "id": null,
  "url": null,
  "waited": false,
  "status": null,
  "would_wait": false
}
```

正式提交后，文本模式输出后续提示、详情页 URL 与状态；JSON 模式额外提供 restart 任务 `id`、`waited`、`status`、endpoint 和 payload。任务达到 `GOOD` 后，原进程 PID 可能已经变化；必须重新执行 `bytedcli bytedog tool process list --pod demo-pod`，把新 PID 传给 `je-flamegraph create --type stock`。若查询已经返回 `JEMALLOC_RESTART_TYPE_FLAMEGRAPH`，命令会阻止重复重启并提示直接获取当前 PID。

### Example

```bash
# 默认 dry-run：只读检查并预览完整请求
bytedcli bytedog profile je-flamegraph restart \
  --pod demo-pod

# 显式 dry-run，适合自动化和操作记录
bytedcli --json bytedog profile je-flamegraph restart \
  --pod demo-pod \
  --dry-run

# 审阅预览并确认服务影响后，提交并等待 GOOD
bytedcli bytedog profile je-flamegraph restart \
  --pod demo-pod \
  --yes \
  --wait

# 重启后重新获取 PID，再创建全量火焰图
bytedcli bytedog tool process list \
  --pod demo-pod

bytedcli bytedog profile je-flamegraph create \
  --pod demo-pod \
  --pid 12345 \
  --type stock
```

## `bytedcli bytedog profile je-flamegraph enable`

为 TCE Pod 目标提交 jemalloc memory flamegraph enable 异步任务。该命令只执行 enable，不生成增量或全量采集结果；enable 任务达到 `GOOD` 后，再等待需要的采集窗口并执行 `bytedcli bytedog profile je-flamegraph create --type increment` 创建增量火焰图任务。自动化场景推荐加 `--wait`，让命令阻塞到 enable 任务完成。

### 参数

| 参数                                  | 必填 | 默认值    | 取值                    | 说明                                                           |
| ------------------------------------- | ---- | --------- | ----------------------- | -------------------------------------------------------------- |
| `--pod <podname>`                     | 是   | 无        | TCE Pod 名称            | enable 只支持 TCE Pod 目标。                                   |
| `--idc <idc>`                         | 否   | 无        | IDC 标识                | 只在 `--pod` 目标下可选使用，用于 Pod 歧义消解；默认不需要传。 |
| `--container-type <primary\|sidecar>` | 否   | `primary` | `primary`、`sidecar`    | 只在 `--pod` 目标下可选使用，用于容器歧义消解。                |
| `--pid <pid>`                         | 是   | 无        | 单个正整数 PID          | 需要启用 jemalloc flamegraph 的进程。只允许一个 PID。          |
| `--wait`                              | 否   | `false`   | 布尔开关                | 等待 enable 任务状态变为 `GOOD` 后再返回。                     |
| `--wait-timeout <seconds>`            | 否   | `600`     | `1` 到 `86400` 的整数秒 | 配合 `--wait` 使用的最长等待时间。                             |
| `--wait-interval <seconds>`           | 否   | `5`       | `1` 到 `3600` 的整数秒  | 配合 `--wait` 使用的轮询间隔。                                 |

### 输出

创建成功后输出 enable 详情页 URL 和后续增量采集提示。未加 `--wait` 时不等待任务完成，应执行 `bytedcli bytedog profile get --url <enable-detail-url>` 查看 enable 任务状态；加 `--wait` 时会在 `status=GOOD` 后返回。

### Example

```bash
bytedcli bytedog profile je-flamegraph enable \
  --pod demo-pod \
  --pid 12345
```

```bash
bytedcli bytedog profile je-flamegraph enable \
  --pod demo-pod \
  --pid 12345 \
  --wait
```

## `bytedcli bytedog profile je-flamegraph create`

创建 jemalloc memory flamegraph 异步任务。

### 参数

| 参数                                  | 必填     | 默认值      | 取值                          | 说明                                                                                                                       |
| ------------------------------------- | -------- | ----------- | ----------------------------- | -------------------------------------------------------------------------------------------------------------------------- |
| `--ip <ip>`                           | 条件必填 | 无          | 主机 IP 或 hostname           | 单独使用时表示机器目标；与 `--app-id` 组合表示大数据分析实例；与 `--k8s-pod --container-id` 组合表示 Kubernetes 容器目标。 |
| `--pod <podname>`                     | 条件必填 | 无          | TCE Pod 名称                  | 用于对 TCE Pod 发起采样。 |
| `--app-id <application_id>`           | 条件必填 | 无          | 大数据分析实例 Application ID | 与 `--ip` 组合使用，表示大数据分析实例目标；仅非 TTP 站点支持。 |
| `--k8s-pod <podname>`                 | 条件必填 | 无          | Kubernetes Pod 名称           | 与 `--ip --container-id` 组合使用，表示 Kubernetes 容器目标；仅非 TTP 站点支持。 |
| `--container-id <container_id>`       | 条件必填 | 无          | Kubernetes container ID       | 与 `--ip --k8s-pod` 组合使用，表示 Kubernetes 容器目标；仅非 TTP 站点支持。 |
| `--idc <idc>`                         | 否       | 无          | IDC 标识                      | 只在 `--pod` 目标下可选使用，用于 Pod 歧义消解；默认不需要传。                                                             |
| `--container-type <primary\|sidecar>` | 否       | `primary`   | `primary`、`sidecar`          | 只在 `--pod` 目标下可选使用，用于容器歧义消解。                                                                            |
| `--pid <pid>`                         | 是       | 无          | 单个正整数 PID                | 采集进程。只允许一个 PID，不支持逗号或空格分隔。                                                                           |
| `--type <stock\|increment>`           | 否       | `increment` | `increment`、`stock`          | `increment` 表示增量采集；`stock` 表示全量采集。主机、大数据分析实例和 Kubernetes 目标仅支持 `increment`。                 |
| `--process-name <cmd>`                | 否       | 无          | 进程命令字符串                | 指定 TCE Pod、大数据分析实例或 Kubernetes 容器进程命令；机器目标不支持。建议先用 `bytedog tool process list` 确认。         |
| `--je-version <version>`              | 否       | 自动选择    | jemalloc 版本字符串           | 仅在 `--type stock` 时使用。显式传入时优先级最高。                                                                         |
| `--tob`                               | 否       | `false`     | 布尔开关                      | 非 TTP 站点支持机器 `--ip` 目标和 Kubernetes 容器目标。用于 ToB 或 mysql 机器模式；TTP 站点会忽略该参数。 |

目标形态必须恰好匹配一种：`--ip`、`--pod`、`--ip --app-id`、`--ip --k8s-pod --container-id`。多传、少传或混用都会报输入错误。创建前会校验 jemalloc 环境状态；环境不可采集时不会创建任务。主机、大数据分析实例和 Kubernetes 目标只支持 `--type increment`；TCE Pod 目标可使用 `--type stock`。默认 `--type increment` 要求目标查询状态为 jemalloc memory flamegraph enable 状态；TCE Pod 目标未 enable 时，先执行 `bytedcli bytedog profile je-flamegraph enable --pod demo-pod --pid 12345 --wait`。全量采集要求 TCE Pod 返回 `valid=true` 且 `type=JEMALLOC_RESTART_TYPE_FLAMEGRAPH`；未准备时先执行 `je-flamegraph restart --pod demo-pod --dry-run`，确认影响后改用 `--yes --wait`，完成后重新获取 PID。若 TCE Pod 目标已做过全量采集准备，增量命令会提示改用全量采集；若大数据分析实例或 Kubernetes 容器目标不支持增量采集，命令会提示更换实例或改用对应 TCE Pod 目标。

### 输出

创建成功后输出详情页 URL 和后续获取命令提示。命令只提交异步任务，不等待结果文件生成。

### Example

```bash
bytedcli bytedog profile je-flamegraph create \
  --pod demo-pod \
  --pid 12345 \
  --process-name /opt/demo/bin/server
```

```bash
bytedcli bytedog profile je-flamegraph create \
  --pod demo-pod \
  --pid 12345 \
  --type stock \
  --je-version 5.2.1.sample
```

```bash
bytedcli --json bytedog profile je-flamegraph create \
  --ip example-host \
  --pid 12345
```

```bash
bytedcli bytedog profile je-flamegraph create \
  --ip example-host \
  --app-id sample-application \
  --pid 12345

bytedcli bytedog profile je-flamegraph create \
  --ip example-host \
  --k8s-pod demo-pod \
  --container-id sample-container \
  --pid 12345
```

## `bytedcli bytedog profile java-heapdump create`

创建 Java heap dump 异步任务并返回详情页 URL，不等待结果生成。适合分析 Java heap 使用、疑似内存泄漏、对象分布、引用链、retained size 或 GC 压力来源。支持在线 TCE / machine / 大数据分析实例目标，不支持 Kubernetes、Cloud IDE、本地文件上传、远端 URL 上传。

该命令会采集完整 heap 快照，快照文件可能很大，采集过程可能短时间影响目标进程。必须显式传 `--confirm-hang-risk` 才会提交任务。JOL heapdump estimates 默认开启，关闭时传 `--no-jol`。

### 参数

| 参数                                  | 必填     | 默认值    | 取值                          | 说明                                                                    |
| ------------------------------------- | -------- | --------- | ----------------------------- | ----------------------------------------------------------------------- |
| `--ip <ip>`                           | 条件必填 | 无        | 主机 IP 或 hostname           | 单独使用时表示 machine 目标；与 `--app-id` 组合表示大数据分析实例目标。 |
| `--pod <podname>`                     | 条件必填 | 无        | TCE Pod 名称                  | 用于 TCE 在线采集。 |
| `--app-id <application_id>`           | 条件必填 | 无        | 大数据分析实例 Application ID | 与 `--ip` 组合使用，表示大数据分析实例目标。 |
| `--pid <pid>`                         | 是       | 无        | 单个正整数 PID                | Java 进程 PID。只允许一个 PID。                                         |
| `--confirm-hang-risk`                 | 是       | `false`   | 布尔开关                      | 确认 heap dump 可能导致目标进程 hang 住。                               |
| `--no-jol`                            | 否       | JOL 开启  | 布尔开关                      | 关闭 JOL heapdump estimates 输出。                                      |
| `--idc <idc>`                         | 否       | 无        | IDC 标识                      | 只在 `--pod` 目标下用于 Pod 歧义消解。                                  |
| `--container-type <primary\|sidecar>` | 否       | `primary` | `primary`、`sidecar`          | 只在 `--pod` 目标下用于容器歧义消解。                                   |

### Example

```bash
bytedcli bytedog profile java-heapdump create \
  --ip example-host \
  --pid 12345 \
  --confirm-hang-risk

bytedcli bytedog profile java-heapdump create \
  --pod demo-pod \
  --pid 12345 \
  --confirm-hang-risk

bytedcli bytedog profile java-heapdump create \
  --ip example-host \
  --app-id sample-application \
  --pid 12345 \
  --confirm-hang-risk
```

## `bytedcli bytedog profile java-allocation create`

创建 Java lightweight allocation sampling 异步任务并返回详情页 URL，不等待结果生成。适合线上低开销定位 Java 分配热点、短时间 heap 增长或分配压力来源；采样结果不是完整分配日志。支持在线 TCE / machine / 大数据分析实例目标，不支持 Kubernetes、Cloud IDE、本地文件上传、远端 URL 上传。

### 参数

| 参数                                  | 必填     | 默认值     | 取值                              | 说明                                                                    |
| ------------------------------------- | -------- | ---------- | --------------------------------- | ----------------------------------------------------------------------- |
| `--ip <ip>`                           | 条件必填 | 无         | 主机 IP 或 hostname               | 单独使用时表示 machine 目标；与 `--app-id` 组合表示大数据分析实例目标。 |
| `--pod <podname>`                     | 条件必填 | 无         | TCE Pod 名称                      | 用于 TCE 在线采集。 |
| `--app-id <application_id>`           | 条件必填 | 无         | 大数据分析实例 Application ID     | 与 `--ip` 组合使用，表示大数据分析实例目标。 |
| `--pid <pid>`                         | 是       | 无         | 单个正整数 PID                    | Java 进程 PID。只允许一个 PID。                                         |
| `--duration <seconds>`                | 否       | `30`       | `1` 到 `300` 的整数秒             | 采样时长。                                                              |
| `--interval <interval>`               | 否       | `10000000` | `10000000`、`100ms`、`100us` 等值 | 轻量分配采样间隔。                                                      |
| `--idc <idc>`                         | 否       | 无         | IDC 标识                          | 只在 `--pod` 目标下用于 Pod 歧义消解。                                  |
| `--container-type <primary\|sidecar>` | 否       | `primary`  | `primary`、`sidecar`              | 只在 `--pod` 目标下用于容器歧义消解。                                   |

### Example

```bash
bytedcli bytedog profile java-allocation create \
  --ip example-host \
  --pid 12345

bytedcli bytedog profile java-allocation create \
  --pod demo-pod \
  --pid 12345

bytedcli bytedog profile java-allocation create \
  --ip example-host \
  --app-id sample-application \
  --pid 12345
```

## `bytedcli bytedog profile java-gc create`

创建 Java GC log profiling 异步任务并返回详情页 URL，不等待结果生成。适合分析频繁 GC、Full GC、停顿过长、回收效果异常或 GC 配置调优问题。支持在线 TCE / machine / 大数据分析实例目标，不支持 Kubernetes、Cloud IDE、本地文件上传、远端 URL 上传。

### 参数

| 参数                                  | 必填     | 默认值    | 取值                          | 说明                                                                    |
| ------------------------------------- | -------- | --------- | ----------------------------- | ----------------------------------------------------------------------- |
| `--ip <ip>`                           | 条件必填 | 无        | 主机 IP 或 hostname           | 单独使用时表示 machine 目标；与 `--app-id` 组合表示大数据分析实例目标。 |
| `--pod <podname>`                     | 条件必填 | 无        | TCE Pod 名称                  | 用于 TCE 在线采集。 |
| `--app-id <application_id>`           | 条件必填 | 无        | 大数据分析实例 Application ID | 与 `--ip` 组合使用，表示大数据分析实例目标。 |
| `--pid <pid>`                         | 是       | 无        | 单个正整数 PID                | Java 进程 PID。只允许一个 PID。                                         |
| `--idc <idc>`                         | 否       | 无        | IDC 标识                      | 只在 `--pod` 目标下用于 Pod 歧义消解。                                  |
| `--container-type <primary\|sidecar>` | 否       | `primary` | `primary`、`sidecar`          | 只在 `--pod` 目标下用于容器歧义消解。                                   |

### Example

```bash
bytedcli bytedog profile java-gc create \
  --ip example-host \
  --pid 12345

bytedcli bytedog profile java-gc create \
  --pod demo-pod \
  --pid 12345

bytedcli bytedog profile java-gc create \
  --ip example-host \
  --app-id sample-application \
  --pid 12345
```

## `bytedcli bytedog profile java-thread create`

创建 Java thread profiling 异步任务并返回详情页 URL，不等待结果生成。适合分析线程状态、thread dump、线程阻塞、Runnable/Waiting 分布、高 CPU 线程栈或疑似死锁线索。支持在线 TCE / machine / 大数据分析实例目标，不支持 Kubernetes、Cloud IDE、本地文件上传、远端 URL 上传。

### 参数

| 参数                                  | 必填     | 默认值     | 取值                              | 说明                                                                    |
| ------------------------------------- | -------- | ---------- | --------------------------------- | ----------------------------------------------------------------------- |
| `--ip <ip>`                           | 条件必填 | 无         | 主机 IP 或 hostname               | 单独使用时表示 machine 目标；与 `--app-id` 组合表示大数据分析实例目标。 |
| `--pod <podname>`                     | 条件必填 | 无         | TCE Pod 名称                      | 用于 TCE 在线采集。 |
| `--app-id <application_id>`           | 条件必填 | 无         | 大数据分析实例 Application ID     | 与 `--ip` 组合使用，表示大数据分析实例目标。 |
| `--pid <pid>`                         | 是       | 无         | 单个正整数 PID                    | Java 进程 PID。只允许一个 PID。                                         |
| `--duration <seconds>`                | 否       | `30`       | `1` 到 `300` 的整数秒             | 采样时长。                                                              |
| `--interval <interval>`               | 否       | `10000000` | `10000000`、`100ms`、`100us` 等值 | 采样间隔。                                                              |
| `--per-thread`                        | 否       | `false`    | 布尔开关                          | 是否按线程拆分展示结果。                                                |
| `--idc <idc>`                         | 否       | 无         | IDC 标识                          | 只在 `--pod` 目标下用于 Pod 歧义消解。                                  |
| `--container-type <primary\|sidecar>` | 否       | `primary`  | `primary`、`sidecar`              | 只在 `--pod` 目标下用于容器歧义消解。                                   |

### Example

```bash
bytedcli bytedog profile java-thread create \
  --ip example-host \
  --pid 12345

bytedcli bytedog profile java-thread create \
  --pod demo-pod \
  --pid 12345 \
  --per-thread

bytedcli bytedog profile java-thread create \
  --ip example-host \
  --app-id sample-application \
  --pid 12345
```

## `bytedcli bytedog profile java-lock create`

创建 Java lock profiling 异步任务并返回详情页 URL，不等待结果生成。适合分析锁竞争、锁等待、锁冲突、monitor/synchronized 热点或疑似死锁。支持在线 TCE / machine / 大数据分析实例目标，不支持 Kubernetes、Cloud IDE、本地文件上传、远端 URL 上传。

### 参数

| 参数                                  | 必填     | 默认值     | 取值                              | 说明                                                                    |
| ------------------------------------- | -------- | ---------- | --------------------------------- | ----------------------------------------------------------------------- |
| `--ip <ip>`                           | 条件必填 | 无         | 主机 IP 或 hostname               | 单独使用时表示 machine 目标；与 `--app-id` 组合表示大数据分析实例目标。 |
| `--pod <podname>`                     | 条件必填 | 无         | TCE Pod 名称                      | 用于 TCE 在线采集。 |
| `--app-id <application_id>`           | 条件必填 | 无         | 大数据分析实例 Application ID     | 与 `--ip` 组合使用，表示大数据分析实例目标。 |
| `--pid <pid>`                         | 是       | 无         | 单个正整数 PID                    | Java 进程 PID。只允许一个 PID。                                         |
| `--duration <seconds>`                | 否       | `30`       | `1` 到 `300` 的整数秒             | 采样时长。                                                              |
| `--interval <interval>`               | 否       | `10000000` | `10000000`、`100ms`、`100us` 等值 | 采样间隔。                                                              |
| `--idc <idc>`                         | 否       | 无         | IDC 标识                          | 只在 `--pod` 目标下用于 Pod 歧义消解。                                  |
| `--container-type <primary\|sidecar>` | 否       | `primary`  | `primary`、`sidecar`              | 只在 `--pod` 目标下用于容器歧义消解。                                   |

### Example

```bash
bytedcli bytedog profile java-lock create \
  --ip example-host \
  --pid 12345

bytedcli bytedog profile java-lock create \
  --pod demo-pod \
  --pid 12345

bytedcli bytedog profile java-lock create \
  --ip example-host \
  --app-id sample-application \
  --pid 12345
```

## `bytedcli bytedog profile python-thread-dump create`

创建 Python 线程栈快照任务，用于查看各线程当前的执行位置和调用栈。

### 参数

| 参数                            | 必填     | 默认值  | 取值                | 说明                                                                               |
| ------------------------------- | -------- | ------- | ------------------- | ---------------------------------------------------------------------------------- |
| `--ip <ip>`                     | 条件必填 | 无      | 主机 IP 或 hostname | 单独使用表示主机目标；与 `--k8s-pod --container-id` 组合表示 Kubernetes 容器目标。 |
| `--pod <podname>`               | 条件必填 | 无      | TCE Pod 名称        | TCE Pod 目标，与主机/Kubernetes 目标互斥。                                         |
| `--k8s-pod <podname>`           | 条件必填 | 无      | Kubernetes Pod 名称 | 与 `--ip --container-id` 组合使用。                                                |
| `--container-id <container_id>` | 条件必填 | 无      | Kubernetes 容器 ID  | 与 `--ip --k8s-pod` 组合使用。                                                     |
| `--pid <pid>`                   | 是       | 无      | 单个正整数 PID      | Python 进程 PID；容器目标使用容器内 PID。                                          |
| `--tob`                         | 否       | `false` | 布尔开关            | 非 TTP 站点的主机或 Kubernetes 目标可选择 ToB 机器。                               |

目标组合恰好选择一种：`--ip`、`--pod`、`--ip --k8s-pod --container-id`。

### 输出

返回异步任务的详情页 `url`，不等待结果生成。使用 `bytedcli bytedog profile get` 查询状态并下载结果，按结果目录的 `data-format.md` 解读文件。

### Example

```bash
bytedcli bytedog profile python-thread-dump create \
  --pod demo-pod \
  --pid 12345

bytedcli bytedog profile python-thread-dump create \
  --ip example-host \
  --k8s-pod demo-pod \
  --container-id sample-container \
  --pid 12345
```

## `bytedcli bytedog profile python-memory create`

创建 Python 内存采样任务，用于比较各调用栈的字节权重。

### 参数

| 参数                            | 必填     | 默认值  | 取值                  | 说明                                                                               |
| ------------------------------- | -------- | ------- | --------------------- | ---------------------------------------------------------------------------------- |
| `--ip <ip>`                     | 条件必填 | 无      | 主机 IP 或 hostname   | 单独使用表示主机目标；与 `--k8s-pod --container-id` 组合表示 Kubernetes 容器目标。 |
| `--pod <podname>`               | 条件必填 | 无      | TCE Pod 名称          | TCE Pod 目标，与主机/Kubernetes 目标互斥。                                         |
| `--k8s-pod <podname>`           | 条件必填 | 无      | Kubernetes Pod 名称   | 与 `--ip --container-id` 组合使用。                                                |
| `--container-id <container_id>` | 条件必填 | 无      | Kubernetes 容器 ID    | 与 `--ip --k8s-pod` 组合使用。                                                     |
| `--pid <pid>`                   | 是       | 无      | 单个正整数 PID        | Python 进程 PID；容器目标使用容器内 PID。                                          |
| `--duration <seconds>`          | 否       | `30`    | `1` 到 `600` 的整数秒 | 采样时长。                                                                         |
| `--tob`                         | 否       | `false` | 布尔开关              | 非 TTP 站点的主机或 Kubernetes 目标可选择 ToB 机器。                               |

目标组合恰好选择一种：`--ip`、`--pod`、`--ip --k8s-pod --container-id`。

### 输出

返回异步任务的详情页 `url`，不等待结果生成。使用 `bytedcli bytedog profile get` 查询状态并下载结果，按结果目录的 `data-format.md` 解读文件。

### Example

```bash
bytedcli bytedog profile python-memory create \
  --pod demo-pod \
  --pid 12345

# 将采样窗口延长到 60 秒
bytedcli bytedog profile python-memory create \
  --ip example-host \
  --pid 12345 \
  --duration 60
```

## `bytedcli bytedog profile python-gc create`

创建 Python GC 对象统计任务，用于查看 GC 管理对象按类型统计的当前计数或计数变化。

### 参数

| 参数                            | 必填     | 默认值  | 取值                  | 说明                                                                               |
| ------------------------------- | -------- | ------- | --------------------- | ---------------------------------------------------------------------------------- |
| `--ip <ip>`                     | 条件必填 | 无      | 主机 IP 或 hostname   | 单独使用表示主机目标；与 `--k8s-pod --container-id` 组合表示 Kubernetes 容器目标。 |
| `--pod <podname>`               | 条件必填 | 无      | TCE Pod 名称          | TCE Pod 目标，与主机/Kubernetes 目标互斥。                                         |
| `--k8s-pod <podname>`           | 条件必填 | 无      | Kubernetes Pod 名称   | 与 `--ip --container-id` 组合使用。                                                |
| `--container-id <container_id>` | 条件必填 | 无      | Kubernetes 容器 ID    | 与 `--ip --k8s-pod` 组合使用。                                                     |
| `--pid <pid>`                   | 是       | 无      | 单个正整数 PID        | Python 进程 PID；容器目标使用容器内 PID。                                          |
| `--diff-time <seconds>`         | 否       | `30`    | `0` 到 `600` 的整数秒 | 两次快照间隔；`0` 获取当前计数，大于 `0` 获取计数差分。                            |
| `--tob`                         | 否       | `false` | 布尔开关              | 非 TTP 站点的主机或 Kubernetes 目标可选择 ToB 机器。                               |

目标组合恰好选择一种：`--ip`、`--pod`、`--ip --k8s-pod --container-id`。

### 输出

返回异步任务的详情页 `url`，不等待结果生成。使用 `bytedcli bytedog profile get` 查询状态并下载结果，按结果目录的 `data-format.md` 解读文件。

### Example

```bash
bytedcli bytedog profile python-gc create \
  --pod demo-pod \
  --pid 12345

# 获取当前对象计数
bytedcli bytedog profile python-gc create \
  --ip example-host \
  --pid 12345 \
  --diff-time 0
```

## `bytedcli bytedog profile oncpu list`

查询 on-cpu flamegraph 历史记录，并输出可交给 `profile get` 的详情页 URL。

### 参数

| 参数                   | 必填     | 默认值  | 取值                                               | 说明                                 |
| ---------------------- | -------- | ------- | -------------------------------------------------- | ------------------------------------ |
| `--ip <ip>`            | 条件必填 | 无      | 目标 IP 或 hostname 文本                           | 目标过滤参数之一。不会做 IP 归一化。 |
| `--pod <podname>`      | 条件必填 | 无      | TCE Pod 名称                                       | 目标过滤参数之一。                   |
| `--psm <psm>`          | 条件必填 | 无      | PSM 名称                                           | 目标过滤参数之一。                   |
| `--status <statuses>`  | 否       | 无      | `INIT`、`RUNNING`、`GOOD`、`BAD`，可用英文逗号分隔 | 按任务状态过滤。                     |
| `--creator <creators>` | 否       | 无      | 创建人标识，可用英文逗号分隔                       | 按任务创建人过滤。                   |
| `--page <n>`           | 否       | `1`     | 正整数                                             | 页码，从 `1` 开始。                  |
| `--page-size <n>`      | 否       | `20`    | 正整数                                             | 每页条数。                           |
| `--url-only`           | 否       | `false` | 布尔开关                                           | 文本模式只逐行输出详情页 URL。       |

`--ip`、`--pod`、`--psm` 至少提供一个。多个过滤参数可以同时提供，后端按组合条件查询。

### 输出

文本模式输出表格列：`ID`、`STATUS`、`TYPE`、`TARGET`、`CREATOR`、`START_AT`、`URL`，并输出 `Current Count` 与 `Has More`。

JSON 模式输出 bytedcli 标准 envelope，业务对象在 `data` 字段里：

```json
{
  "status": "success",
  "data": {
    "items": [
      {
        "id": 1001,
        "profile_type": "oncpu",
        "raw_type": "CPU_CPP_FLAMEGRAPH_ON_TCE",
        "status": "GOOD",
        "target": {
          "ip": null,
          "pod": "demo-pod",
          "psm": "demo.service"
        },
        "creator": "demo-user",
        "description": "sample task",
        "start_at": "2026-06-05T02:00:00.000Z",
        "end_at": "2026-06-05T02:00:30.000Z",
        "detail_url": "https://example.bytedog/profiling/on-cpu-profiling/detail?id=1001&from=tce"
      }
    ],
    "page": 1,
    "page_size": 20,
    "current_count": 1,
    "has_more": false
  },
  "error": null,
  "context": {
    "execution_time_ms": 123,
    "timestamp": "2026-06-08T10:00:00+08:00",
    "api_endpoint": "ByteDog Profile List"
  }
}
```

`current_count` 表示当前页返回条数，不代表历史总数。`has_more=true` 表示可能还有下一页。后面 list 子命令的 JSON envelope 形态相同，仅 `data` 内容不同。

### Example

```bash
bytedcli bytedog profile oncpu list \
  --ip example-host \
  --status GOOD
```

```bash
bytedcli bytedog profile oncpu list \
  --pod demo-pod \
  --psm demo.service \
  --status GOOD \
  --url-only
```

```bash
bytedcli --json bytedog profile oncpu list \
  --ip example-host \
  --status GOOD
```

## `bytedcli bytedog profile thread-overview list`

查询线程状态概览历史记录。命令过滤四类 `THREAD_OVERVIEW_ON_*` 任务并返回 `/profiling/cpuoverview/single` 详情页 URL；把状态为 `GOOD` 的 URL 交给 `profile get` 可下载线程状态时间线 JSON。

### 参数

| 参数                   | 必填     | 默认值  | 取值                                       | 说明                               |
| ---------------------- | -------- | ------- | ------------------------------------------ | ---------------------------------- |
| `--ip <ip>`            | 条件必填 | 无      | 目标 IP 或 hostname 文本                   | 目标过滤参数之一；不做 IP 归一化。 |
| `--pod <podname>`      | 条件必填 | 无      | TCE Pod 名称                               | 目标过滤参数之一。                 |
| `--psm <psm>`          | 条件必填 | 无      | PSM 名称                                   | 目标过滤参数之一。                 |
| `--status <statuses>`  | 否       | 无      | `INIT`、`RUNNING`、`GOOD`、`BAD`，逗号分隔 | 按状态过滤。                       |
| `--creator <creators>` | 否       | 无      | 创建人标识，逗号分隔                       | 按创建人过滤。                     |
| `--page <n>`           | 否       | `1`     | 正整数                                     | 1-based 页码。                     |
| `--page-size <n>`      | 否       | `20`    | 正整数                                     | 每页条数。                         |
| `--url-only`           | 否       | `false` | 布尔开关                                   | 文本模式只逐行输出详情页 URL。     |

`--ip`、`--pod`、`--psm` 至少提供一个。`current_count` 是当前页条数，不是总数；`has_more=true` 表示可能还有下一页。

### 输出

```json
{
  "status": "success",
  "data": {
    "items": [
      {
        "id": 1301,
        "profile_type": "thread-overview",
        "raw_type": "THREAD_OVERVIEW_ON_TCE",
        "status": "GOOD",
        "target": {
          "ip": null,
          "pod": "demo-pod",
          "psm": "demo.service"
        },
        "creator": "demo-user",
        "description": "sample task",
        "start_at": "2026-07-10T02:00:00.000Z",
        "end_at": "2026-07-10T02:00:30.000Z",
        "detail_url": "https://example.bytedog/profiling/cpuoverview/single?id=1301&from=tce"
      }
    ],
    "page": 1,
    "page_size": 20,
    "current_count": 1,
    "has_more": false
  },
  "error": null,
  "context": {
    "execution_time_ms": 123,
    "timestamp": "2026-07-10T10:00:00+08:00",
    "api_endpoint": "ByteDog Profile List"
  }
}
```

### Example

```bash
bytedcli bytedog profile thread-overview list \
  --ip example-host \
  --status GOOD

bytedcli bytedog profile thread-overview list \
  --pod demo-pod \
  --status GOOD \
  --url-only

bytedcli --json bytedog profile thread-overview list \
  --psm demo.service \
  --status GOOD
```

## `bytedcli bytedog profile sprofile list`

查询 continuous flamegraph 历史记录，并输出可交给 `profile get` 的详情页 URL。

### 参数

| 参数                   | 必填 | 默认值  | 取值                                               | 说明                               |
| ---------------------- | ---- | ------- | -------------------------------------------------- | ---------------------------------- |
| `--ip <ip>`            | 是   | 无      | 目标 IP 或 hostname 文本                           | 按机器目标过滤。不会做 IP 归一化。 |
| `--status <statuses>`  | 否   | 无      | `INIT`、`RUNNING`、`GOOD`、`BAD`，可用英文逗号分隔 | 按任务状态过滤。                   |
| `--creator <creators>` | 否   | 无      | 创建人标识，可用英文逗号分隔                       | 按任务创建人过滤。                 |
| `--page <n>`           | 否   | `1`     | 正整数                                             | 页码，从 `1` 开始。                |
| `--page-size <n>`      | 否   | `20`    | 正整数                                             | 每页条数。                         |
| `--url-only`           | 否   | `false` | 布尔开关                                           | 文本模式只逐行输出详情页 URL。     |

该命令不接受 `--pod` 和 `--psm`。

### 输出

文本模式输出表格列：`ID`、`STATUS`、`TYPE`、`TARGET`、`CREATOR`、`START_AT`、`URL`，并输出 `Current Count` 与 `Has More`。

JSON envelope 形态同 `profile oncpu list`；`data` 示例：

```json
{
  "items": [
    {
      "id": 1007,
      "profile_type": "sprofile",
      "raw_type": "STEBPF-SPLIT",
      "status": "GOOD",
      "target": {
        "ip": "example-host",
        "pod": null,
        "psm": null
      },
      "creator": "demo-user",
      "description": null,
      "start_at": "2026-06-05T02:00:00.000Z",
      "end_at": "2026-06-05T02:30:00.000Z",
      "detail_url": "https://example.bytedog/profiling/continuous-profiling/detail?id=1007&time=long"
    }
  ],
  "page": 1,
  "page_size": 20,
  "current_count": 1,
  "has_more": false
}
```

`current_count` 表示当前页返回条数，不代表历史总数。`has_more=true` 表示可能还有下一页。

### Example

```bash
bytedcli bytedog profile sprofile list \
  --ip example-host \
  --status GOOD
```

```bash
bytedcli bytedog profile sprofile list \
  --ip example-host \
  --status GOOD \
  --url-only
```

```bash
bytedcli --json bytedog profile sprofile list \
  --ip example-host \
  --status GOOD
```

## `bytedcli bytedog profile je-continuous list`

查询 jemalloc 常态化内存采集结果历史记录，并输出可交给 `profile get` 的详情页 URL。

### 参数

| 参数                   | 必填 | 默认值  | 取值                                               | 说明                           |
| ---------------------- | ---- | ------- | -------------------------------------------------- | ------------------------------ |
| `--ip <ip>`            | 否   | 无      | 目标 IP 或 hostname 文本                           | 可选历史目标过滤，不做归一化。 |
| `--pod <podname>`      | 否   | 无      | TCE Pod 名称                                       | 按后端 `podname` 字段过滤。 |
| `--status <statuses>`  | 否   | 无      | `INIT`、`RUNNING`、`GOOD`、`BAD`，可用英文逗号分隔 | 按任务状态过滤。               |
| `--creator <creators>` | 否   | 无      | 创建人标识，可用英文逗号分隔                       | 按任务创建人过滤。             |
| `--page <n>`           | 否   | `1`     | 正整数                                             | 页码，从 `1` 开始。            |
| `--page-size <n>`      | 否   | `20`    | 正整数                                             | 每页条数。                     |
| `--url-only`           | 否   | `false` | 布尔开关                                           | 文本模式只逐行输出详情页 URL。 |

该命令无需目标过滤即可查询，也可按 `--ip` 或 `--pod` 过滤；不接受 `--psm`。

### 输出

文本模式输出表格列：`ID`、`STATUS`、`TYPE`、`TARGET`、`CREATOR`、`START_AT`、`URL`。JSON 输出包含 `items`、`page`、`page_size`、`current_count`、`has_more`；每个 item 的 `profile_type` 为 `je-continuous`。

### Example

```bash
bytedcli bytedog profile je-continuous list \
  --status GOOD

bytedcli --json bytedog profile je-continuous list \
  --pod demo-pod \
  --status GOOD \
  --page-size 10
```

## `bytedcli bytedog profile offcpu list`

查询 off-cpu flamegraph 历史记录，并输出可交给 `profile get` 的详情页 URL。

### 参数

| 参数                   | 必填     | 默认值  | 取值                                               | 说明                                 |
| ---------------------- | -------- | ------- | -------------------------------------------------- | ------------------------------------ |
| `--ip <ip>`            | 条件必填 | 无      | 目标 IP 或 hostname 文本                           | 目标过滤参数之一。不会做 IP 归一化。 |
| `--pod <podname>`      | 条件必填 | 无      | TCE Pod 名称                                       | 目标过滤参数之一。                   |
| `--psm <psm>`          | 条件必填 | 无      | PSM 名称                                           | 目标过滤参数之一。                   |
| `--status <statuses>`  | 否       | 无      | `INIT`、`RUNNING`、`GOOD`、`BAD`，可用英文逗号分隔 | 按任务状态过滤。                     |
| `--creator <creators>` | 否       | 无      | 创建人标识，可用英文逗号分隔                       | 按任务创建人过滤。                   |
| `--page <n>`           | 否       | `1`     | 正整数                                             | 页码，从 `1` 开始。                  |
| `--page-size <n>`      | 否       | `20`    | 正整数                                             | 每页条数。                           |
| `--url-only`           | 否       | `false` | 布尔开关                                           | 文本模式只逐行输出详情页 URL。       |

`--ip`、`--pod`、`--psm` 至少提供一个。多个过滤参数可以同时提供，后端按组合条件查询。

### 输出

文本模式输出表格列：`ID`、`STATUS`、`TYPE`、`TARGET`、`CREATOR`、`START_AT`、`URL`，并输出 `Current Count` 与 `Has More`。

JSON envelope 形态同 `profile oncpu list`；`data` 示例：

```json
{
  "items": [
    {
      "id": 1003,
      "profile_type": "offcpu",
      "raw_type": "OFFCPU_FLAMEGRAPH_ON_TCE",
      "status": "GOOD",
      "target": {
        "ip": null,
        "pod": "demo-pod",
        "psm": "demo.service"
      },
      "creator": "demo-user",
      "description": null,
      "start_at": null,
      "end_at": null,
      "detail_url": "https://example.bytedog/profiling/off-cpu-profiling/flamegraph/detail?id=1003"
    }
  ],
  "page": 1,
  "page_size": 20,
  "current_count": 1,
  "has_more": false
}
```

### Example

```bash
bytedcli bytedog profile offcpu list \
  --pod demo-pod \
  --status GOOD
```

```bash
bytedcli bytedog profile offcpu list \
  --psm demo.service \
  --status GOOD \
  --url-only
```

```bash
bytedcli --json bytedog profile offcpu list \
  --ip example-host \
  --status GOOD
```

## `bytedcli bytedog profile pthread list`

查询 pthread lock profiling 历史记录，并输出可交给 `profile get` 的详情页 URL。

### 参数

| 参数                   | 必填     | 默认值  | 取值                                               | 说明                                 |
| ---------------------- | -------- | ------- | -------------------------------------------------- | ------------------------------------ |
| `--ip <ip>`            | 条件必填 | 无      | 目标 IP 或 hostname 文本                           | 目标过滤参数之一。不会做 IP 归一化。 |
| `--pod <podname>`      | 条件必填 | 无      | TCE Pod 名称                                       | 目标过滤参数之一。                   |
| `--psm <psm>`          | 条件必填 | 无      | PSM 名称                                           | 目标过滤参数之一。                   |
| `--status <statuses>`  | 否       | 无      | `INIT`、`RUNNING`、`GOOD`、`BAD`，可用英文逗号分隔 | 按任务状态过滤。                     |
| `--creator <creators>` | 否       | 无      | 创建人标识，可用英文逗号分隔                       | 按任务创建人过滤。                   |
| `--page <n>`           | 否       | `1`     | 正整数                                             | 页码，从 `1` 开始。                  |
| `--page-size <n>`      | 否       | `20`    | 正整数                                             | 每页条数。                           |
| `--url-only`           | 否       | `false` | 布尔开关                                           | 文本模式只逐行输出详情页 URL。       |

`--ip`、`--pod`、`--psm` 至少提供一个。多个过滤参数可以同时提供，后端按组合条件查询。

### 输出

文本模式输出表格列：`ID`、`STATUS`、`TYPE`、`TARGET`、`CREATOR`、`START_AT`、`URL`，并输出 `Current Count` 与 `Has More`。

JSON envelope 形态同 `profile oncpu list`；`data` 示例：

```json
{
  "items": [
    {
      "id": 1004,
      "profile_type": "pthread",
      "raw_type": "USER_LOCK_STAT_ON_TCE",
      "status": "GOOD",
      "target": {
        "ip": null,
        "pod": "demo-pod",
        "psm": "demo.service"
      },
      "creator": "demo-user",
      "description": null,
      "start_at": null,
      "end_at": null,
      "detail_url": "https://example.bytedog/profiling/off-cpu-profiling/lock/detail?id=1004"
    }
  ],
  "page": 1,
  "page_size": 20,
  "current_count": 1,
  "has_more": false
}
```

### Example

```bash
bytedcli bytedog profile pthread list \
  --psm demo.service \
  --status GOOD
```

```bash
bytedcli bytedog profile pthread list \
  --pod demo-pod \
  --status GOOD \
  --url-only
```

```bash
bytedcli --json bytedog profile pthread list \
  --ip example-host \
  --status GOOD
```

## `bytedcli bytedog profile je-stats list`

查询 jemalloc stats 历史记录，并输出可交给 `profile get` 的详情页 URL。

### 参数

| 参数                   | 必填     | 默认值  | 取值                                               | 说明                                 |
| ---------------------- | -------- | ------- | -------------------------------------------------- | ------------------------------------ |
| `--ip <ip>`            | 条件必填 | 无      | 目标 IP 或 hostname 文本                           | 目标过滤参数之一。不会做 IP 归一化。 |
| `--pod <podname>`      | 条件必填 | 无      | TCE Pod 名称                                       | 目标过滤参数之一。                   |
| `--psm <psm>`          | 条件必填 | 无      | PSM 名称                                           | 目标过滤参数之一。                   |
| `--status <statuses>`  | 否       | 无      | `INIT`、`RUNNING`、`GOOD`、`BAD`，可用英文逗号分隔 | 按任务状态过滤。                     |
| `--creator <creators>` | 否       | 无      | 创建人标识，可用英文逗号分隔                       | 按任务创建人过滤。                   |
| `--page <n>`           | 否       | `1`     | 正整数                                             | 页码，从 `1` 开始。                  |
| `--page-size <n>`      | 否       | `20`    | 正整数                                             | 每页条数。                           |
| `--url-only`           | 否       | `false` | 布尔开关                                           | 文本模式只逐行输出详情页 URL。       |

`--ip`、`--pod`、`--psm` 至少提供一个。多个过滤参数可以同时提供，后端按组合条件查询。

### 输出

文本模式输出表格列：`ID`、`STATUS`、`TYPE`、`TARGET`、`CREATOR`、`START_AT`、`URL`，并输出 `Current Count` 与 `Has More`。

JSON envelope 形态同 `profile oncpu list`；`data` 示例：

```json
{
  "items": [
    {
      "id": 1005,
      "profile_type": "je-stats",
      "raw_type": "JEMALLOC_STATS_ON_MACHINE",
      "status": "GOOD",
      "target": {
        "ip": "example-host",
        "pod": null,
        "psm": null
      },
      "creator": "demo-user",
      "description": null,
      "start_at": null,
      "end_at": null,
      "detail_url": "https://example.bytedog/profiling/jemalloc-profiling/stats?id=1005&from=machine"
    }
  ],
  "page": 1,
  "page_size": 20,
  "current_count": 1,
  "has_more": false
}
```

### Example

```bash
bytedcli bytedog profile je-stats list \
  --ip example-host \
  --status GOOD
```

```bash
bytedcli bytedog profile je-stats list \
  --pod demo-pod \
  --status GOOD \
  --url-only
```

```bash
bytedcli --json bytedog profile je-stats list \
  --ip example-host \
  --status GOOD
```

## `bytedcli bytedog profile je-flamegraph list`

查询 jemalloc memory flamegraph 历史记录，并输出可交给 `profile get` 的详情页 URL。

### 参数

| 参数                   | 必填     | 默认值  | 取值                                               | 说明                                 |
| ---------------------- | -------- | ------- | -------------------------------------------------- | ------------------------------------ |
| `--ip <ip>`            | 条件必填 | 无      | 目标 IP 或 hostname 文本                           | 目标过滤参数之一。不会做 IP 归一化。 |
| `--pod <podname>`      | 条件必填 | 无      | TCE Pod 名称                                       | 目标过滤参数之一。                   |
| `--psm <psm>`          | 条件必填 | 无      | PSM 名称                                           | 目标过滤参数之一。                   |
| `--status <statuses>`  | 否       | 无      | `INIT`、`RUNNING`、`GOOD`、`BAD`，可用英文逗号分隔 | 按任务状态过滤。                     |
| `--creator <creators>` | 否       | 无      | 创建人标识，可用英文逗号分隔                       | 按任务创建人过滤。                   |
| `--page <n>`           | 否       | `1`     | 正整数                                             | 页码，从 `1` 开始。                  |
| `--page-size <n>`      | 否       | `20`    | 正整数                                             | 每页条数。                           |
| `--url-only`           | 否       | `false` | 布尔开关                                           | 文本模式只逐行输出详情页 URL。       |

`--ip`、`--pod`、`--psm` 至少提供一个。多个过滤参数可以同时提供，后端按组合条件查询。

### 输出

文本模式输出表格列：`ID`、`STATUS`、`TYPE`、`TARGET`、`CREATOR`、`START_AT`、`URL`，并输出 `Current Count` 与 `Has More`。

JSON envelope 形态同 `profile oncpu list`；`data` 示例：

```json
{
  "items": [
    {
      "id": 1010,
      "profile_type": "je-flamegraph",
      "raw_type": "JEMALLOC_FLAMEGRAPH_ON_TCE_INCREMENT_PROFILE",
      "status": "GOOD",
      "target": {
        "ip": null,
        "pod": "demo-pod",
        "psm": "demo.service"
      },
      "creator": "demo-user",
      "description": null,
      "start_at": null,
      "end_at": null,
      "detail_url": "https://example.bytedog/profiling/jemalloc-profiling/detail?id=1010&from=tce"
    }
  ],
  "page": 1,
  "page_size": 20,
  "current_count": 1,
  "has_more": false
}
```

### Example

```bash
bytedcli bytedog profile je-flamegraph list \
  --pod demo-pod \
  --status GOOD
```

```bash
bytedcli bytedog profile je-flamegraph list \
  --ip example-host \
  --status GOOD \
  --url-only
```

```bash
bytedcli --json bytedog profile je-flamegraph list \
  --ip example-host \
  --status GOOD
```

## `bytedcli bytedog profile java-heapdump list`

查询 Java heap dump 历史记录，并输出可交给 `profile get` 的详情页 URL。该命令不创建任务、不是异步写入命令；它只读取已存在的历史记录。

list 会覆盖历史记录里的 machine、TCE、YARN 与 URL 上传任务；create 当前支持在线 TCE / machine / 大数据分析实例目标。可用 `--ip`、`--pod`、`--psm` 过滤。`profile java-heapdump list` 不做 IP 归一化，按传入文本过滤历史记录。查可用结果文件或可交给 `profile get` 的 detail URL 时，默认推荐加 `--status GOOD`。

### 参数

| 参数                   | 必填     | 默认值  | 取值                                               | 说明                           |
| ---------------------- | -------- | ------- | -------------------------------------------------- | ------------------------------ |
| `--ip <ip>`            | 条件必填 | 无      | 目标 IP 或 hostname 文本                           | 目标过滤参数之一。 |
| `--pod <podname>`      | 条件必填 | 无      | TCE Pod 名称                                       | 目标过滤参数之一。             |
| `--psm <psm>`          | 条件必填 | 无      | PSM 名称                                           | 目标过滤参数之一。             |
| `--status <statuses>`  | 否       | 无      | `INIT`、`RUNNING`、`GOOD`、`BAD`，可用英文逗号分隔 | 按任务状态过滤。               |
| `--creator <creators>` | 否       | 无      | 创建人标识，可用英文逗号分隔                       | 按任务创建人过滤。             |
| `--page <n>`           | 否       | `1`     | 正整数                                             | 页码，从 `1` 开始。            |
| `--page-size <n>`      | 否       | `20`    | 正整数                                             | 每页条数。                     |
| `--url-only`           | 否       | `false` | 布尔开关                                           | 文本模式只逐行输出详情页 URL。 |

`--ip`、`--pod`、`--psm` 至少提供一个。多个过滤参数可以同时提供，后端按组合条件查询。

### 输出

文本模式输出表格列：`ID`、`STATUS`、`TYPE`、`TARGET`、`CREATOR`、`START_AT`、`URL`，并输出 `Current Count` 与 `Has More`。

JSON envelope 形态同 `profile oncpu list`。`current_count` 表示当前页返回条数，不代表历史总数；`has_more=true` 表示可能还有下一页。

### Example

```bash
bytedcli bytedog profile java-heapdump list \
  --pod demo-pod \
  --status GOOD

bytedcli bytedog profile java-heapdump list \
  --ip example-host \
  --status GOOD \
  --url-only

bytedcli --json bytedog profile java-heapdump list \
  --psm demo.service \
  --status GOOD
```

## `bytedcli bytedog profile java-allocation list`

查询 Java lightweight allocation sampling 历史记录，并输出可交给 `profile get` 的详情页 URL。该命令不创建任务、不是异步写入命令；它只读取已存在的历史记录。

list 会覆盖历史记录里的 machine、TCE 与 YARN 任务；create 当前支持在线 TCE / machine / 大数据分析实例目标。可用 `--ip`、`--pod`、`--psm` 过滤。`profile java-allocation list` 不做 IP 归一化，按传入文本过滤历史记录。查可用结果文件或可交给 `profile get` 的 detail URL 时，默认推荐加 `--status GOOD`。

### 参数

| 参数                   | 必填     | 默认值  | 取值                                               | 说明                           |
| ---------------------- | -------- | ------- | -------------------------------------------------- | ------------------------------ |
| `--ip <ip>`            | 条件必填 | 无      | 目标 IP 或 hostname 文本                           | 目标过滤参数之一。 |
| `--pod <podname>`      | 条件必填 | 无      | TCE Pod 名称                                       | 目标过滤参数之一。             |
| `--psm <psm>`          | 条件必填 | 无      | PSM 名称                                           | 目标过滤参数之一。             |
| `--status <statuses>`  | 否       | 无      | `INIT`、`RUNNING`、`GOOD`、`BAD`，可用英文逗号分隔 | 按任务状态过滤。               |
| `--creator <creators>` | 否       | 无      | 创建人标识，可用英文逗号分隔                       | 按任务创建人过滤。             |
| `--page <n>`           | 否       | `1`     | 正整数                                             | 页码，从 `1` 开始。            |
| `--page-size <n>`      | 否       | `20`    | 正整数                                             | 每页条数。                     |
| `--url-only`           | 否       | `false` | 布尔开关                                           | 文本模式只逐行输出详情页 URL。 |

`--ip`、`--pod`、`--psm` 至少提供一个。多个过滤参数可以同时提供，后端按组合条件查询。

### 输出

文本模式输出表格列：`ID`、`STATUS`、`TYPE`、`TARGET`、`CREATOR`、`START_AT`、`URL`，并输出 `Current Count` 与 `Has More`。

JSON envelope 形态同 `profile oncpu list`。`current_count` 表示当前页返回条数，不代表历史总数；`has_more=true` 表示可能还有下一页。

### Example

```bash
bytedcli bytedog profile java-allocation list \
  --pod demo-pod \
  --status GOOD

bytedcli bytedog profile java-allocation list \
  --ip example-host \
  --status GOOD \
  --url-only

bytedcli --json bytedog profile java-allocation list \
  --psm demo.service \
  --status GOOD
```

## `bytedcli bytedog profile java-gc list`

查询 Java GC log profiling 历史记录，并输出可交给 `profile get` 的详情页 URL。该命令不创建任务、不是异步写入命令；它只读取已存在的历史记录。

list 会覆盖历史记录里的 machine、TCE、YARN 与 URL 上传任务；create 当前支持在线 TCE / machine / 大数据分析实例目标。可用 `--ip`、`--pod`、`--psm` 过滤。`profile java-gc list` 不做 IP 归一化，按传入文本过滤历史记录。查可用结果文件或可交给 `profile get` 的 detail URL 时，默认推荐加 `--status GOOD`。

### 参数

| 参数                   | 必填     | 默认值  | 取值                                               | 说明                           |
| ---------------------- | -------- | ------- | -------------------------------------------------- | ------------------------------ |
| `--ip <ip>`            | 条件必填 | 无      | 目标 IP 或 hostname 文本                           | 目标过滤参数之一。 |
| `--pod <podname>`      | 条件必填 | 无      | TCE Pod 名称                                       | 目标过滤参数之一。             |
| `--psm <psm>`          | 条件必填 | 无      | PSM 名称                                           | 目标过滤参数之一。             |
| `--status <statuses>`  | 否       | 无      | `INIT`、`RUNNING`、`GOOD`、`BAD`，可用英文逗号分隔 | 按任务状态过滤。               |
| `--creator <creators>` | 否       | 无      | 创建人标识，可用英文逗号分隔                       | 按任务创建人过滤。             |
| `--page <n>`           | 否       | `1`     | 正整数                                             | 页码，从 `1` 开始。            |
| `--page-size <n>`      | 否       | `20`    | 正整数                                             | 每页条数。                     |
| `--url-only`           | 否       | `false` | 布尔开关                                           | 文本模式只逐行输出详情页 URL。 |

`--ip`、`--pod`、`--psm` 至少提供一个。多个过滤参数可以同时提供，后端按组合条件查询。

### 输出

文本模式输出表格列：`ID`、`STATUS`、`TYPE`、`TARGET`、`CREATOR`、`START_AT`、`URL`，并输出 `Current Count` 与 `Has More`。

JSON envelope 形态同 `profile oncpu list`。`current_count` 表示当前页返回条数，不代表历史总数；`has_more=true` 表示可能还有下一页。

### Example

```bash
bytedcli bytedog profile java-gc list \
  --ip example-host \
  --status GOOD

bytedcli bytedog profile java-gc list \
  --pod demo-pod \
  --status GOOD \
  --url-only

bytedcli --json bytedog profile java-gc list \
  --psm demo.service \
  --status GOOD
```

## `bytedcli bytedog profile java-thread list`

查询 Java thread profiling 历史记录，并输出可交给 `profile get` 的详情页 URL。该命令不创建任务、不是异步写入命令；它只读取已存在的历史记录。

list 会覆盖历史记录里的 machine、TCE、YARN 与 URL 上传任务；create 当前支持在线 TCE / machine / 大数据分析实例目标。可用 `--ip`、`--pod`、`--psm` 过滤。`profile java-thread list` 不做 IP 归一化，按传入文本过滤历史记录。查可用结果文件或可交给 `profile get` 的 detail URL 时，默认推荐加 `--status GOOD`。

### 参数

| 参数                   | 必填     | 默认值  | 取值                                               | 说明                           |
| ---------------------- | -------- | ------- | -------------------------------------------------- | ------------------------------ |
| `--ip <ip>`            | 条件必填 | 无      | 目标 IP 或 hostname 文本                           | 目标过滤参数之一。 |
| `--pod <podname>`      | 条件必填 | 无      | TCE Pod 名称                                       | 目标过滤参数之一。             |
| `--psm <psm>`          | 条件必填 | 无      | PSM 名称                                           | 目标过滤参数之一。             |
| `--status <statuses>`  | 否       | 无      | `INIT`、`RUNNING`、`GOOD`、`BAD`，可用英文逗号分隔 | 按任务状态过滤。               |
| `--creator <creators>` | 否       | 无      | 创建人标识，可用英文逗号分隔                       | 按任务创建人过滤。             |
| `--page <n>`           | 否       | `1`     | 正整数                                             | 页码，从 `1` 开始。            |
| `--page-size <n>`      | 否       | `20`    | 正整数                                             | 每页条数。                     |
| `--url-only`           | 否       | `false` | 布尔开关                                           | 文本模式只逐行输出详情页 URL。 |

`--ip`、`--pod`、`--psm` 至少提供一个。多个过滤参数可以同时提供，后端按组合条件查询。

### 输出

文本模式输出表格列：`ID`、`STATUS`、`TYPE`、`TARGET`、`CREATOR`、`START_AT`、`URL`，并输出 `Current Count` 与 `Has More`。

JSON envelope 形态同 `profile oncpu list`。`current_count` 表示当前页返回条数，不代表历史总数；`has_more=true` 表示可能还有下一页。

### Example

```bash
bytedcli bytedog profile java-thread list \
  --psm demo.service \
  --status GOOD

bytedcli bytedog profile java-thread list \
  --pod demo-pod \
  --status GOOD \
  --url-only

bytedcli --json bytedog profile java-thread list \
  --ip example-host \
  --status GOOD
```

## `bytedcli bytedog profile java-lock list`

查询 Java lock profiling 历史记录，并输出可交给 `profile get` 的详情页 URL。该命令不创建任务、不是异步写入命令；它只读取已存在的历史记录。

list 会覆盖历史记录里的 machine、TCE 与 YARN 任务；create 当前支持在线 TCE / machine / 大数据分析实例目标。可用 `--ip`、`--pod`、`--psm` 过滤。`profile java-lock list` 不做 IP 归一化，按传入文本过滤历史记录。查可用结果文件或可交给 `profile get` 的 detail URL 时，默认推荐加 `--status GOOD`。

### 参数

| 参数                   | 必填     | 默认值  | 取值                                               | 说明                           |
| ---------------------- | -------- | ------- | -------------------------------------------------- | ------------------------------ |
| `--ip <ip>`            | 条件必填 | 无      | 目标 IP 或 hostname 文本                           | 目标过滤参数之一。 |
| `--pod <podname>`      | 条件必填 | 无      | TCE Pod 名称                                       | 目标过滤参数之一。             |
| `--psm <psm>`          | 条件必填 | 无      | PSM 名称                                           | 目标过滤参数之一。             |
| `--status <statuses>`  | 否       | 无      | `INIT`、`RUNNING`、`GOOD`、`BAD`，可用英文逗号分隔 | 按任务状态过滤。               |
| `--creator <creators>` | 否       | 无      | 创建人标识，可用英文逗号分隔                       | 按任务创建人过滤。             |
| `--page <n>`           | 否       | `1`     | 正整数                                             | 页码，从 `1` 开始。            |
| `--page-size <n>`      | 否       | `20`    | 正整数                                             | 每页条数。                     |
| `--url-only`           | 否       | `false` | 布尔开关                                           | 文本模式只逐行输出详情页 URL。 |

`--ip`、`--pod`、`--psm` 至少提供一个。多个过滤参数可以同时提供，后端按组合条件查询。

### 输出

文本模式输出表格列：`ID`、`STATUS`、`TYPE`、`TARGET`、`CREATOR`、`START_AT`、`URL`，并输出 `Current Count` 与 `Has More`。

JSON envelope 形态同 `profile oncpu list`。`current_count` 表示当前页返回条数，不代表历史总数；`has_more=true` 表示可能还有下一页。

### Example

```bash
bytedcli bytedog profile java-lock list \
  --pod demo-pod \
  --status GOOD

bytedcli bytedog profile java-lock list \
  --ip example-host \
  --status GOOD \
  --url-only

bytedcli --json bytedog profile java-lock list \
  --psm demo.service \
  --status GOOD
```

## `bytedcli bytedog profile python-thread-dump list`

查询 Python 线程栈采集的历史记录，并输出可交给 `profile get` 的详情页 URL。筛选条件均可省略；目标过滤仅支持 `--ip`。

### 参数

| 参数                   | 必填 | 默认值  | 取值                                               | 说明                           |
| ---------------------- | ---- | ------- | -------------------------------------------------- | ------------------------------ |
| `--ip <ip>`            | 否   | 无      | 目标 IP 文本                                       | 按目标 IP 筛选。               |
| `--status <statuses>`  | 否   | 无      | `INIT`、`RUNNING`、`GOOD`、`BAD`，可用英文逗号分隔 | 按任务状态过滤。               |
| `--creator <creators>` | 否   | 无      | 创建人标识，可用英文逗号分隔                       | 按任务创建人过滤。             |
| `--page <n>`           | 否   | `1`     | 正整数                                             | 页码，从 `1` 开始。            |
| `--page-size <n>`      | 否   | `20`    | 正整数                                             | 每页条数。                     |
| `--url-only`           | 否   | `false` | 布尔开关                                           | 文本模式只逐行输出详情页 URL。 |

### 输出

文本模式输出表格列：`ID`、`STATUS`、`TYPE`、`TARGET`、`CREATOR`、`START_AT`、`URL`，并输出 `Current Count` 与 `Has More`。

JSON envelope 形态同 `profile oncpu list`，包含 `page`、`page_size`、`current_count`、`has_more` 和 `items[].detail_url`。`current_count` 表示当前页返回条数，不代表历史总数。

### Example

```bash
bytedcli bytedog profile python-thread-dump list \
  --ip example-host \
  --status GOOD

bytedcli --json bytedog profile python-thread-dump list \
  --creator demo-user \
  --status GOOD
```

## `bytedcli bytedog profile python-memory list`

查询 Python 内存栈采集的历史记录，并输出可交给 `profile get` 的详情页 URL。筛选条件均可省略；目标过滤仅支持 `--ip`。

### 参数

| 参数                   | 必填 | 默认值  | 取值                                               | 说明                           |
| ---------------------- | ---- | ------- | -------------------------------------------------- | ------------------------------ |
| `--ip <ip>`            | 否   | 无      | 目标 IP 文本                                       | 按目标 IP 筛选。               |
| `--status <statuses>`  | 否   | 无      | `INIT`、`RUNNING`、`GOOD`、`BAD`，可用英文逗号分隔 | 按任务状态过滤。               |
| `--creator <creators>` | 否   | 无      | 创建人标识，可用英文逗号分隔                       | 按任务创建人过滤。             |
| `--page <n>`           | 否   | `1`     | 正整数                                             | 页码，从 `1` 开始。            |
| `--page-size <n>`      | 否   | `20`    | 正整数                                             | 每页条数。                     |
| `--url-only`           | 否   | `false` | 布尔开关                                           | 文本模式只逐行输出详情页 URL。 |

### 输出

文本模式输出表格列：`ID`、`STATUS`、`TYPE`、`TARGET`、`CREATOR`、`START_AT`、`URL`，并输出 `Current Count` 与 `Has More`。

JSON envelope 形态同 `profile oncpu list`，包含 `page`、`page_size`、`current_count`、`has_more` 和 `items[].detail_url`。`current_count` 表示当前页返回条数，不代表历史总数。

### Example

```bash
bytedcli bytedog profile python-memory list \
  --ip example-host \
  --status GOOD

bytedcli --json bytedog profile python-memory list \
  --creator demo-user \
  --status GOOD
```

## `bytedcli bytedog profile python-gc list`

查询 Python GC 采集的历史记录，并输出可交给 `profile get` 的详情页 URL。筛选条件均可省略；目标过滤仅支持 `--ip`。

### 参数

| 参数                   | 必填 | 默认值  | 取值                                               | 说明                           |
| ---------------------- | ---- | ------- | -------------------------------------------------- | ------------------------------ |
| `--ip <ip>`            | 否   | 无      | 目标 IP 文本                                       | 按目标 IP 筛选。               |
| `--status <statuses>`  | 否   | 无      | `INIT`、`RUNNING`、`GOOD`、`BAD`，可用英文逗号分隔 | 按任务状态过滤。               |
| `--creator <creators>` | 否   | 无      | 创建人标识，可用英文逗号分隔                       | 按任务创建人过滤。             |
| `--page <n>`           | 否   | `1`     | 正整数                                             | 页码，从 `1` 开始。            |
| `--page-size <n>`      | 否   | `20`    | 正整数                                             | 每页条数。                     |
| `--url-only`           | 否   | `false` | 布尔开关                                           | 文本模式只逐行输出详情页 URL。 |

### 输出

文本模式输出表格列：`ID`、`STATUS`、`TYPE`、`TARGET`、`CREATOR`、`START_AT`、`URL`，并输出 `Current Count` 与 `Has More`。

JSON envelope 形态同 `profile oncpu list`，包含 `page`、`page_size`、`current_count`、`has_more` 和 `items[].detail_url`。`current_count` 表示当前页返回条数，不代表历史总数。

### Example

```bash
bytedcli bytedog profile python-gc list \
  --ip example-host \
  --status GOOD

bytedcli --json bytedog profile python-gc list \
  --creator demo-user \
  --status GOOD
```

## `bytedcli bytedog tool process list`

列出目标上的进程，用于确认 profile create 命令需要的 PID、容器内 namespace PID、进程命令、RSS 和 CPU 信息。

### 参数

| 参数                                  | 必填     | 默认值    | 取值                          | 说明                                                                                                                       |
| ------------------------------------- | -------- | --------- | ----------------------------- | -------------------------------------------------------------------------------------------------------------------------- |
| `--pod <podname>`                     | 条件必填 | 无        | TCE Pod 名称                  | 单独使用时表示 TCE Pod 目标。 |
| `--ip <ip>`                           | 条件必填 | 无        | 主机 IP 或 hostname           | 单独使用时表示机器目标；与 `--app-id` 组合表示大数据分析实例；与 `--k8s-pod --container-id` 组合表示 Kubernetes 容器目标。 |
| `--workspace-id <workspace_id>`       | 条件必填 | 无        | Cloud IDE workspace ID        | 单独使用时表示 Cloud IDE workspace 目标。 |
| `--app-id <application_id>`           | 条件必填 | 无        | 大数据分析实例 Application ID | 与 `--ip` 组合使用，列出大数据分析实例进程。 |
| `--k8s-pod <podname>`                 | 条件必填 | 无        | Kubernetes Pod 名称           | 与 `--ip --container-id` 组合使用，列出 Kubernetes 容器进程。 |
| `--container-id <container_id>`       | 条件必填 | 无        | Kubernetes container ID       | 与 `--ip --k8s-pod` 组合使用，列出 Kubernetes 容器进程。 |
| `--idc <idc>`                         | 否       | 无        | IDC 标识                      | 只在 `--pod` 目标下可选使用，用于 Pod 歧义消解；默认不需要传。                                                             |
| `--container-type <primary\|sidecar>` | 否       | `primary` | `primary`、`sidecar`          | 只在 `--pod` 目标下可选使用，用于容器歧义消解。                                                                            |
| `--tob`                               | 否       | `false`   | 布尔开关                      | 非 TTP 站点支持机器 `--ip` 目标和 Kubernetes 容器目标。用于 ToB 或 mysql 机器模式；TTP 站点会忽略该参数。 |

目标形态必须恰好匹配一种：`--ip`、`--pod`、`--workspace-id`、`--ip --app-id`、`--ip --k8s-pod --container-id`。多传、少传或混用都会报输入错误。

### 输出

文本模式固定输出表格列：`PID`、`TID_NS`、`RSS_KB`、`CPU_%`、`CMD`，并输出 `Current Count`。当后端返回大数据分析实例或 Kubernetes 上下文时，会额外展示 `APP_ID`、`POD`、`CONTAINER` 列。

`CPU_%` / JSON `cpu` 来自目标侧 `ps` 的进程 CPU 百分比。Linux `ps` 的 `%CPU` 是进程启动以来累计 CPU time / elapsed time 的生命周期平均值，不是瞬时 CPU 采样；如果进程运行时间很长，近期 CPU 突增可能会被平均值稀释。

JSON 模式输出 bytedcli 标准 envelope，业务对象在 `data` 字段里：

```json
{
  "status": "success",
  "data": {
    "target_type": "k8s",
    "target": "example-host",
    "k8s_pod": "demo-pod",
    "container_id": "sample-container",
    "processes": [
      {
        "pid": 1001,
        "tid_ns": 11,
        "cmd": "/opt/demo/bin/server --flag",
        "rss": 2048,
        "cpu": 1.25,
        "application_id": "sample-application",
        "pod_name": "demo-pod",
        "container_name": "main",
        "container_id": "sample-container"
      }
    ],
    "current_count": 1
  },
  "error": null,
  "context": {
    "execution_time_ms": 123,
    "timestamp": "2026-06-08T10:00:00+08:00",
    "api_endpoint": "ByteDog Tool ListProcesses"
  }
}
```

### Example

```bash
bytedcli bytedog tool process list \
  --pod demo-pod
```

```bash
bytedcli bytedog tool process list \
  --ip example-host \
  --tob
```

```bash
bytedcli --json bytedog tool process list \
  --workspace-id sample-workspace
```

```bash
bytedcli bytedog tool process list \
  --ip example-host \
  --app-id sample-application
```

```bash
bytedcli bytedog tool process list \
  --ip example-host \
  --k8s-pod demo-pod \
  --container-id sample-container
```

## `bytedcli bytedog tool coredump list`

列出供 `gdb coredump create --coredump-path` 选择的远端路径候选。CLI 保留 `FILE` 节点、展开至下一层、排除明显的 `elf.*` 文件、应用可选 `--keyword`，最后按 `mod_time` 降序排列；但请求不携带文件 kind，CLI 也不读取远端文件内容，因此 JSON 固定返回 `content_verified=false`。TCE 默认查询对应容器目录；`--target-dir host` 查询宿主机 `/opt/tiger/cores`，两种目录都会额外应用 `core` basename 规则。

### 参数

| 参数                              | 必填       | 默认值                          | 说明                                                                                           |
| --------------------------------- | ---------- | ------------------------------- | ---------------------------------------------------------------------------------------------- |
| `--pod <podname>`                 | 条件必填   | 无                              | TCE Pod 目标。 |
| `--ip <ip>`                       | 条件必填   | 无                              | 机器目标；与 `--k8s-pod` 组合表示 Kubernetes。 |
| `--workspace-id <workspace_id>`   | 条件必填   | 无                              | Cloud IDE workspace。 |
| `--k8s-pod <podname>`             | 条件必填   | 无                              | Kubernetes Pod；必须同时传 `--ip`。 |
| `--target-dir <location-or-path>` | 按目标决定 | TCE：`container`；Cloud IDE：无 | TCE 只接受 `container` 或 `host`（`/opt/tiger/cores`）；Cloud IDE 必须传业务进程当前工作目录。 |
| `--keyword <text>`                | 否         | 无                              | 对返回路径做大小写不敏感的本地过滤。                                                           |

目标必须恰好匹配 `--pod`、`--ip`、`--workspace-id`、`--ip --k8s-pod` 之一。Cloud IDE 的机器不会安装 `coredump_handler`，core 文件会生成在业务进程的当前工作目录；根据团队维护的 Cloud IDE coredump 指引确认该目录，并显式传 `--target-dir`。Cloud IDE、machine 和 Kubernetes 的结果仍是未验证的路径候选，调用方必须结合文件名和部署信息确认；CLI 不把原始目录树作为结果输出。如果已经知道精确 core 文件路径，可跳过列表，直接使用 `gdb coredump create --coredump-path`。Machine 和 Kubernetes 不接收 `--target-dir`。空列表是成功结果，JSON 中返回 `files=[]`、`current_count=0` 与 `content_verified=false`。当 TCE 默认容器目录为空时，低版本 `coredump_handler` 可能把 core 放在宿主机根目录，使用相同 `--pod` 加 `--target-dir host` 重试。

### Example

```bash
bytedcli --json bytedog tool coredump list \
  --pod demo-pod

bytedcli bytedog tool coredump list \
  --pod demo-pod \
  --target-dir host \
  --keyword core.12345

bytedcli --json bytedog tool coredump list \
  --workspace-id sample-workspace \
  --target-dir /workspace/demo
```

## `bytedcli bytedog tool elf list`

列出供 `gdb coredump create --elf-path` 选择的远端路径候选。参数、目标组合、两层目录展开、排序和空列表语义与 `tool coredump list` 相同；CLI 会排除明显的 `core.*` 文件，但不会读取远端内容验证其是否为 ELF，JSON 固定返回 `content_verified=false`。调用方必须结合目标部署信息确认真实可执行文件。

### Example

```bash
bytedcli --json bytedog tool elf list \
  --pod demo-pod

bytedcli bytedog tool elf list \
  --pod demo-pod \
  --target-dir host
```

## `bytedcli bytedog gdb coredump create`

创建 coredump GDB 分析 session。GDB 需求默认使用该路径；除非用户明确要求 attach 在线进程、接受可能暂停或降低目标进程性能的风险并传入 `--confirm-performance-impact`，否则不要改用 `gdb attach create`。该命令向后端固定提交 `async=true`，返回 session ID 和当前状态，不等待异步任务完成。

### 参数

| 参数                             | 必填     | 默认值   | 说明                                                                                                                    |
| -------------------------------- | -------- | -------- | ----------------------------------------------------------------------------------------------------------------------- |
| `--pod <podname>`                | 条件必填 | 无       | TCE Pod 目标。 |
| `--ip <ip>`                      | 条件必填 | 无       | 机器目标；与 `--k8s-pod --container-id` 组合表示 Kubernetes。 |
| `--workspace-id <workspace_id>`  | 条件必填 | 无       | Cloud IDE workspace。 |
| `--k8s-pod <podname>`            | 条件必填 | 无       | Kubernetes Pod；必须同时传 `--ip --container-id`。 |
| `--container-id <container_id>`  | 条件必填 | 无       | Kubernetes container ID。 |
| `--coredump-path <path>`         | 是       | 无       | 远端 coredump 文件路径。                                                                                                |
| `--elf-path <path>`              | 条件必填 | 自动推导 | Cloud IDE 必须显式传远端 ELF 路径；其它目标省略时仅当 coredump basename 为 `core.*` 才推导同目录的 `elf.*`。            |
| `--gdb <env\|bytedog\|cuda-gdb>` | 否       | `env`    | `env`：当前环境中的gdb；`bytedog`：使用bytedog提供的gdb16；`cuda-gdb`：使用cuda-gdb，需要环境中带有 cuda-gdb 才能使用。 |

### 输出

创建接口只返回提交阶段所需的 `session_id` 和 `status`。创建返回后使用 `gdb session get --session-id <id>` 查询完整状态；只在详情明确返回 `command_executable=true` 时继续执行 GDB 命令，若为 `false`，直接读取并报告 `command_unavailable_reason`。若提交结果不确定，禁止直接重试 create，改用 `gdb session list` 找回 ID。

### Example

```bash
bytedcli --json bytedog gdb coredump create \
  --pod demo-pod \
  --coredump-path /opt/tiger/cores/demo-pod/core.12345

bytedcli bytedog gdb coredump create \
  --workspace-id sample-workspace \
  --coredump-path /workspace/demo/crash.dump \
  --elf-path /workspace/demo/demo-server
```

## `bytedcli bytedog gdb attach create`

Attach 在线目标进程并创建异步 GDB session。只有用户明确要求 attach 时才使用；先以完全相同的目标参数运行 `tool process list` 选择 PID。Attach 可能暂停目标进程或降低其性能，必须由调用方接受风险并显式传 `--confirm-performance-impact`，否则命令在解析目标和请求接口前失败。

参数与 `gdb coredump create` 的目标、`--gdb` 相同，但不接收 core/ELF 路径，改为必填 `--pid <pid>` 和 `--confirm-performance-impact`。PID 必须为正整数。

### Example

```bash
bytedcli --json bytedog tool process list \
  --pod demo-pod

bytedcli --json bytedog gdb attach create \
  --pod demo-pod \
  --pid 12345 \
  --confirm-performance-impact
```

## `bytedcli bytedog gdb session list`

分页查询 GDB session 历史记录。该命令为只读请求，也是 create 提交结果不确定时找回 session ID 的入口。

| 参数                   | 必填 | 默认值 | 说明                                        |
| ---------------------- | ---- | ------ | ------------------------------------------- |
| `--creator <creators>` | 否   | 无     | Creator 过滤，多个值用逗号分隔。            |
| `--status <statuses>`  | 否   | 无     | `INIT,RUNNING,GOOD,BAD`，多个值用逗号分隔。 |
| `--ip <ip>`            | 否   | 无     | 目标 IP 或 hostname。 |
| `--pod <podname>`      | 否   | 无     | 目标 Pod 名称。                             |
| `--keyword <keyword>`  | 否   | 无     | description 关键词。                        |
| `--page <page>`        | 否   | `1`    | 正整数页码。                                |
| `--page-size <size>`   | 否   | `20`   | 正整数每页条数。                            |

JSON 业务对象包含 `items`、`page`、`page_size`、`current_count`、`has_more`。每个 item 使用 session get 的字段结构；不返回详情 URL。空列表是成功结果。

### Example

```bash
bytedcli --json bytedog gdb session list \
  --creator sample-user \
  --pod demo-pod \
  --status RUNNING
```

## `bytedcli bytedog gdb session get`

根据正整数 session ID 获取 ByteDog GDB session。

| 参数                | 必填 | 默认值 | 说明                            |
| ------------------- | ---- | ------ | ------------------------------- |
| `--session-id <id>` | 是   | 无     | 正整数 ByteDog GDB session ID。 |

JSON 业务对象包含 `session_id`、`status`、`gdb_type`、`target_type`、`target`、`arguments`、`creator`、`description`、`start_at`、`end_at`、`welcome`、`last_ticket_time`、`tickets`、`err_id`、`command_executable`、`command_unavailable_reason`。`argument` 按 ByteDog 其它详情接口的约定兼容普通 JSON 字符串与 `json` 前缀，解析失败时输出 `arguments=null`。

`status=BAD` 时 CLI 返回可读的失败原因。其它状态由 CLI 直接给出是否能继续执行命令：`command_executable=true` 表示可以提交；`false` 时，`command_unavailable_reason` 为 `session_not_good`、`gdb_tool_coredump` 或 `session_idle_timeout`。调用方直接展示这个结论，不需要自行组合 `status`、`err_id` 和 `last_ticket_time` 判断。GDB 工具自身 coredump 或 session 空闲超时都必须新建 session；前者应改用 `--gdb bytedog` 或兼容的环境 GDB 10.2。

### Example

```bash
bytedcli --json bytedog gdb session get \
  --session-id 1001
```

## `bytedcli bytedog gdb command execute`

在可继续输入的 session 内异步提交一条 GDB 命令。CLI 会先按 session ID 查询详情，只有详情结论为 `command_executable=true` 时才向后端固定提交 `async=true`；否则按 `command_unavailable_reason` 返回对应错误。Attach session 的每次命令执行都必须显式传 `--confirm-performance-impact`；只有详情明确识别为 `gdb_type=coredump` 时才免确认，类型缺失或不可解析时失败关闭并同样要求确认。命令返回 ticket ID，不等待结果。

| 参数                           | 必填     | 默认值  | 说明                                                                               |
| ------------------------------ | -------- | ------- | ---------------------------------------------------------------------------------- |
| `--session-id <id>`            | 是       | 无      | 正整数 GDB session ID。                                                            |
| `--command <gdb_command>`      | 是       | 无      | 一条非空白 GDB 命令。                                                              |
| `--confirm-performance-impact` | 按需必填 | `false` | Attach 或类型未知的 session 每次执行命令时必填；明确的 coredump session 无需传入。 |

JSON 业务对象返回 `session_id`、`ticket_id`、`status`、`command`。拿到 ticket ID 后使用 `gdb command get --ticket-id <id>` 查询结果。若返回 `BYTEDOG_GDB_COMMAND_SUBMISSION_UNKNOWN`，禁止直接重试 execute；先执行 session get 查看 tickets，再对找到的 ticket 执行 command get。

### Example

```bash
bytedcli --json bytedog gdb command execute \
  --session-id 1001 \
  --command 'thread apply all bt'

bytedcli --json bytedog gdb command execute \
  --session-id 1001 \
  --command 'continue' \
  --confirm-performance-impact
```

## `bytedcli bytedog gdb command get`

按正整数 ticket ID 单次读取既有 GDB command 结果。该命令调用 ticket detail，不创建或重新执行远端命令；只有这个命令把原始结果写入 mode-0600 文件。

| 参数                 | 必填 | 默认值                 | 说明                       |
| -------------------- | ---- | ---------------------- | -------------------------- |
| `--ticket-id <id>`   | 是   | 无                     | 正整数 command ticket ID。 |
| `--output-dir <dir>` | 否   | `./bytedog-gdb-output` | 原始输出文件目录。         |

GOOD 响应从 ticket detail 恢复 `session_id` 和 `command`，并返回 `ticket_id`、`status`、`output_path`、`bytes`、`content_state`。ticket 尚为 `RUNNING` / `INIT` / `UNKNOWN` 等非终态时，返回 `BYTEDOG_GDB_COMMAND_NOT_READY`；等待后使用同一个 ticket ID 再次运行 `gdb command get`，不要重新执行 GDB command。

- `content_state=content`：包含至少一个非空白字符。
- `content_state=empty`：后端明确返回空字符串；仍创建零字节文件。
- `content_state=whitespace`：纯空白字符；文件按原值保留。
- 缺少 `result.plain`：结构化错误，不当作空字符串。
- `status=BAD` 且带失败提示：CLI 返回该提示，并将同一内容写入 `.error.txt`；未获得具体原因时返回通用错误文案。
- `status=GOOD` 或 `BAD` 且 `err_id=1020`：按 GDB 工具自身 coredump 返回错误；GOOD ticket 的原始结果仍会写入输出文件。
- `status=BAD` 且包含 `broken pipe`：优先按 session 通道中断处理，通常需要新建 session 后重试。

### Example

```bash
bytedcli --json bytedog gdb command get \
  --ticket-id 2001
```
