# TCE Pod On-CPU Profile Workflow

本文描述 Agent 根据 TCE `psm` 和 `podname` 查找目标实例，并创建 ByteDog on-cpu 火焰图，再获取结果文件的标准流程。需要完整 `profile oncpu create` / `profile get` 参数时，同时阅读 `bytedog-command-reference.md` 和 `on-cpu-profile-create-to-get-workflow.md`。

## Table of Contents

- [输入](#输入)
- [Step 1: 确认 PSM 所在站点](#step-1-确认-psm-所在站点)
- [Step 2: 用 PSM 查询 TCE 实例并定位 podname](#step-2-用-psm-查询-tce-实例并定位-podname)
- [Step 3: 创建 on-cpu 火焰图任务](#step-3-创建-on-cpu-火焰图任务)
- [Step 4: 等待任务完成并获取结果](#step-4-等待任务完成并获取结果)
- [Step 5: 失败或找不到结果时的回退](#step-5-失败或找不到结果时的回退)

## 输入

- `psm`：TCE 服务 PSM，例如 `demo.service.api`
- `podname`：TCE Pod 名称，例如 `demo-pod-abc123`
- `env`：TCE 环境，默认使用 `prod`
- `site`：可选。若用户没有给出，先按站点探测步骤查找
- `idc`：可选。只有 Pod 名称跨 IDC 有歧义时才作为 ByteDog 消歧参数使用
- `container-type`：可选。未指定时 ByteDog 默认使用 `primary`
- `type`：可选，on-cpu 语言类型，默认 `cpp`；只有确认服务语言不是 C++ 时才显式传 `go`、`rust`、`java` 或 `python`

## Step 1: 确认 PSM 所在站点

如果用户已经明确给出 `--site`，直接使用该站点。否则按常见站点查询 TCE 实例数量，找到能返回目标 PSM 实例的站点。

```bash
for site in cn boe i18n-bd i18n-tt us-ttp eu-ttp; do
  bytedcli --json --site "$site" tce instance list \
    --psm demo.service.api \
    --env prod \
    --page-size 1
done
```

选择能返回该 PSM 实例的站点作为后续 `--site`。如果多个站点都有结果，让用户确认实际流量或问题发生的站点。

## Step 2: 用 PSM 查询 TCE 实例并定位 podname

`tce instance list` 支持按 `--psm` + `--env` 查询实例，但不提供 `--pod-name` 过滤参数。Agent 需要在 JSON 结果中按用户给出的 `podname` 过滤，并确认只命中一个实例。

```bash
bytedcli --json tce instance list \
  --psm demo.service.api \
  --env prod \
  --page-size 50
```

从返回结果中查找目标 Pod，优先匹配这些字段之一：

- `name`
- `pod_name`
- `podName`

命中目标后记录：

- Pod 名称：传给 ByteDog 的 `--pod`
- IDC：如果结果里有 `idc`、`idc_name`、`idcName`、`zone` 等字段，先记录；只有 Pod 名称跨 IDC 有歧义或用户明确指定时，才传给 ByteDog 的 `--idc`
- 容器类型：如果用户明确说要采 sidecar，或 Pod 解析需要按容器消歧，才传 `--container-type sidecar`；否则使用默认 `primary`
- 状态/健康信息：优先选择运行中、健康、近期仍存在的实例

如果第一页没有目标 Pod，增加 `--page-size`、翻页或使用 `--no-pagination` 查询完整列表：

```bash
bytedcli --json tce instance list \
  --psm demo.service.api \
  --env prod \
  --no-pagination
```

也可以用 Pod 名称做全局实例搜索辅助定位，再回到 `instance list --psm --env` 确认 PSM 与站点：

```bash
bytedcli --json tce instance search --keyword demo-pod-abc123
```

不要在未确认 PSM、site 和唯一 Pod 的情况下创建 profiling 任务。

## Step 3: 创建 on-cpu 火焰图任务

使用 `bytedog profile oncpu create` 创建任务。对 TCE Pod 目标，目标选择参数只传 `--pod`，不要同时传 `--ip` 或 `--workspace-id`。`--idc` 与 `--container-type` 都是可选消歧参数：只有 Pod 名称跨 IDC/容器有歧义，或用户明确要采 sidecar 时才需要传；未传 `--container-type` 时默认使用 `primary`。

```bash
bytedcli --json bytedog profile oncpu create \
  --pod demo-pod-abc123
```

需要按 IDC 或 sidecar 消歧时再追加；两者都是可选项，按实际需要传：

```bash
bytedcli --json bytedog profile oncpu create \
  --pod demo-pod-abc123 \
  --idc sample-idc \
  --container-type sidecar
```

创建成功后，记录 JSON 输出里的 `url` 字段；文本模式下记录输出提示中的 ByteDog detail URL。`profile <type> create` 只提交异步任务，不等待结果文件生成。

常用选择：

- `--type` 默认是 `cpp`；只有确认目标服务是 Go/Rust/Java/Python 时才显式传 `--type go`、`--type rust`、`--type java` 或 `--type python`
- C++/Go/Rust：默认工具通常使用 `bytekd`；需要 perf event 或 inline frame 时再显式改 `--tools-type perf`
- Java：指定 `--type java`，`--tools-type` 会被忽略
- Python：指定 `--type python`；TTP 站点默认/仅允许 `pyspy`
- 只想采某个进程时，先用 `bytedog tool process list --pod <pod>` 查 PID，再给 `oncpu` 增加 `--pid <pid>`

查 PID 示例：

```bash
bytedcli --json bytedog tool process list \
  --pod demo-pod-abc123
```

## Step 4: 等待任务完成并获取结果

等待采样时长加处理时间后，用 detail URL 获取结果。任务仍在运行时，`profile get` 会提示稍后重试；任务失败时会输出错误信息；任务状态可用但详情页没有结果 URL 时，命令会成功返回 `status` / `result_urls` / `files: []`，不要继续读取不存在的 `data-format.md`。

```bash
bytedcli bytedog profile get \
  --url 'https://example.bytedog/profiling/on-cpu-profiling/detail?id=1001&from=tce' \
  --output-dir ./bytedog-output
```

获取成功且输出包含 `data-format.md` 时，先读输出目录里的 `data-format.md`，再解析 `.collapse`、`.json` 等结果文件。若 `files` 为空，向用户说明详情页未返回可下载结果 URL，并保留 detail URL 与 `result_urls` 字段。

## Step 5: 失败或找不到结果时的回退

- 找不到 PSM：确认 `--site`、`--env` 和 PSM 是否正确；必要时跨 `cn`、`boe`、`i18n-bd`、`i18n-tt`、`us-ttp`、`eu-ttp` 探测。
- 找不到 podname：用 `tce instance search --keyword <podname>` 辅助定位，再用 PSM 列表确认唯一目标。
- 多个 Pod 命中：让用户确认具体 Pod、IDC 或容器类型。
- `profile <type> create` 目标解析失败：先只用 `--pod` 验证；如果 Pod 名称跨 IDC 或容器有歧义，再确认 `--idc` / `--container-type` 是否来自同一个 TCE 实例，必要时用 `bytedog tool process list` 验证 ByteDog 能解析该 Pod。
- `profile get` 未就绪：保留 detail URL，等待后重试同一条 `profile get` 命令。
