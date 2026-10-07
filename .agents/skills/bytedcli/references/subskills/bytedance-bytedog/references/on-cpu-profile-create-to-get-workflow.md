# ByteDog On-CPU Profile Create 到 Get 流程

本文只描述使用 `bytedcli bytedog profile oncpu create` 创建 on-cpu 火焰图任务，再通过 `bytedcli bytedog profile get` 获取结果的流程。完整参数、输出字段和边界条件见 `bytedog-command-reference.md`。

## Table of Contents

- [输入与目标](#输入与目标)
- [Step 1: 确认目标与 PID](#step-1-确认目标与-pid)
- [Step 2: 创建 On-CPU 任务](#step-2-创建-on-cpu-任务)
- [Step 3: 等待并获取结果](#step-3-等待并获取结果)
- [Agent 输出要求](#agent-输出要求)

## 输入与目标

目标参数必须恰好匹配以下一种形态：

| 目标            | 参数                                                | 约束                                                                                |
| --------------- | --------------------------------------------------- | ----------------------------------------------------------------------------------- |
| 主机            | `--ip <ip>`                                         | 可选 `--pid` 限定单个进程。                                                         |
| TCE Pod         | `--pod <podname>`                                   | 可选 `--idc` 消歧、`--container-type primary\|sidecar` 选择容器、`--pid` 限定进程。 |
| Cloud IDE       | `--workspace-id <id>`                               | 可选 `--pid` 限定单个进程。                                                         |
| 大数据分析实例  | `--ip <ip> --app-id <application_id> --pid <pid>`   | `--pid` 必填，只支持 `--type cpp/java/python`。                                     |
| Kubernetes 容器 | `--ip <ip> --k8s-pod <podname> --container-id <id>` | 仅非 TTP 站点支持，可选 `--pid` 限定单个进程。                                      |

TTP 站点支持主机、TCE Pod、Cloud IDE 和大数据分析实例目标，不支持 Kubernetes 容器目标。`--site` 是 bytedcli 全局参数，需要写在 `bytedcli` 后、`bytedog` 前。

主要采样参数：

- `--duration <seconds>`：默认 `30` 秒，最多 `300` 秒；Python `ebpf_profiler` 至少 `10` 秒。
- `--type <type>`：默认 `cpp`，可选 `cpp`、`java`、`python`、`go`、`rust`。
- `--tools-type <type>`：native 默认 `bytekd`；Python 默认 `ebpf_profiler`，TTP 站点默认且只支持 `pyspy`；Java 不使用该参数。
- `--reason <text>` / `--question <text>`：可选且可单独使用；非 US/EU TTP 调用时分别说明为什么选择该命令及期望的信息、要解决的问题或观察到的现象。

## Step 1: 确认目标与 PID

只有要限定单个进程或使用大数据分析实例目标时才需要 PID。先使用 `tool process list` 查询进程，并让查询和后续 create 使用相同的目标参数组合：

```bash
bytedcli bytedog tool process list \
  --pod demo-pod

bytedcli bytedog tool process list \
  --ip example-host \
  --app-id sample-application

bytedcli bytedog tool process list \
  --ip example-host \
  --k8s-pod demo-pod \
  --container-id sample-container
```

从结果中确认目标进程后，把单个 `PID` 传给 `profile oncpu create --pid`。不要把不同目标形态的进程结果混用。

## Step 2: 创建 On-CPU 任务

create 只提交异步任务，不等待结果生成。根据目标选择一条命令执行，并记录返回的 detail URL：

```bash
bytedcli bytedog profile oncpu create \
  --ip example-host

bytedcli bytedog profile oncpu create \
  --pod demo-pod \
  --pid 12345 \
  --type go

bytedcli bytedog profile oncpu create \
  --ip example-host \
  --app-id sample-application \
  --pid 12345 \
  --type python

bytedcli bytedog profile oncpu create \
  --ip example-host \
  --k8s-pod demo-pod \
  --container-id sample-container
```

非 US/EU TTP 站点可按需为本流程中的独立命令追加 `--reason <text>`、`--question <text>`，两者可单独或同时使用。轮询或重复查询同一任务时，后续命令无需重复携带；需要更新诊断上下文时再传。需要机器可读输出时，把全局 `--json` 写在 `bytedcli` 后。

## Step 3: 等待并获取结果

等待采样和处理完成后，把 create 返回的 detail URL 原样传给 `profile get`：

```bash
bytedcli bytedog profile get \
  --url 'https://example.bytedog/profiling/on-cpu-profiling/detail?id=1001&from=machine' \
  --output-dir ./bytedog-output
```

`profile get` 只在任务状态为 `GOOD` 时获取结果。任务仍在运行时，稍后使用同一个 detail URL 重试；任务失败时，保留错误信息和 detail URL。

存在结果文件时，输出目录会包含 `data-format.md` 和下载后的 on-cpu 结果文件。先读取 `data-format.md`，再解析结果文件。若详情页没有返回结果 URL，命令会返回 `status`、`result_urls` 和空 `files`，此时不要读取不存在的 `data-format.md`。

## Agent 输出要求

- 汇报 detail URL、任务 `status`、输出目录、`result_urls` 和实际生成的结果文件路径。
- 只有输出中实际包含 `data-format.md` 时才汇报并读取它。
- 任务未完成时，给出可直接重试的 `profile get --url ... --output-dir ...` 命令。
- 任务失败时，保留后端错误信息，并建议用户核对站点、目标参数、PID、语言类型和采样工具。
