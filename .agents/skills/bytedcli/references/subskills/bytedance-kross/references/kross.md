# Kross 命令说明

Kross 用于创建多平台（Linux、macOS、Windows）容器环境（workload）。

## 命令面

当前 Kross CLI 暴露这几组能力：

- `kross workspace list`
- `kross workspace create`
- `kross workspace delete`
- `kross workspace var list`
- `kross template list`
- `kross vm template list`
- `kross vm create`
- `kross vm execute`
- `kross vm access start`
- `kross workload list`
- `kross workload follow`
- `kross workload create`
- `kross workload delete`
- `kross workload exec`
- `kross workload upload`
- `kross workload download`

`workspace create` 和 `workspace delete` 会提交 Kross work order。命令返回成功表示工单已提交，work order 状态为 `COMPLETED` 才表示创建或删除完成。

## Workspace 创建

```bash
bytedcli kross workspace create \
  --name demo-workspace \
  --cluster default-multi-platform
```

- `--cluster` 必须使用精确的 active cluster 名称
- 默认配额为 1 CPU、1024 MB 内存、10 GB 存储
- 使用 `--cpu-cores`、`--memory-mb`、`--storage-gb` 覆盖默认配额
- 返回 workspace 和 `CREATE_WORKSPACE` work order；继续操作前应确认 work order 状态为 `COMPLETED`

## Workspace 查询

```bash
bytedcli kross workspace list
```

- 返回当前用户有权限访问的 workspace
- CLI 会自动翻完分页，不需要手动指定 page 参数

## Workspace 删除

```bash
bytedcli kross workspace delete --name demo-workspace
bytedcli --json kross workspace delete --workspace-id 42
```

- `--name` 和 `--workspace-id` 二选一
- workspace 内仍有 workload 时服务端会拒绝删除
- 返回 `DELETE_WORKSPACE` work order；确认 work order 状态为 `COMPLETED` 后，workspace 才算删除完成

## Workspace 变量查询

```bash
bytedcli kross workspace var list --workspace demo-workspace
bytedcli --json kross workspace var list --workspace demo-workspace --type SECRET
```

- 入参使用 workspace 名称，不需要手动传 workspace id
- 支持通过 `--type PLAIN` 或 `--type SECRET` 过滤变量类型
- 返回变量的 `InjectionMode`。普通变量看 `EnvName`，secret 变量看 `UnixPath` / `WindowsPath`
- secret 变量只返回脱敏后的 `MaskedValue` 和文件注入路径，不返回明文值

## 模板查询

```bash
bytedcli kross template list --workspace demo-workspace
```

- 入参使用 workspace 名称，不需要手动传 workspace id
- CLI 会先解析 workspace，再由 Kross 服务端根据 workspace 可见性和生效中的 cluster binding 返回可用模板

## 查询 workload

```bash
bytedcli kross workload list --workspace demo-workspace
```

- 返回目标 workspace 下的 workload
- CLI 会自动翻完分页，不需要手动指定 page 参数
- 支持通过 `--name`、`--type`、`--status-cached` 做过滤

## 观察 workload 状态

```bash
bytedcli kross workload follow --workspace demo-workspace --name demo-job
bytedcli --json kross workload follow --workspace demo-workspace --workload-id 72
```

- `--name` 和 `--workload-id` 二选一
- 依次输出 Kross 提供的 `SNAPSHOT`、`MODIFIED` 和 `DELETED` 事件
- `--json` 输出 JSONL，每行是一个事件，不附加最终 envelope
- 这是无界流，只能在直接 CLI 会话中运行，不支持 MCP 或 captured execution
- 服务端关闭 SSE 流后命令结束；客户端不会自动重连

## 虚拟机

查询当前 workspace 可用的 VM 镜像模板：

```bash
bytedcli kross vm template list --workspace demo-workspace
```

创建 VM workload：

```bash
bytedcli kross vm create \
  --workspace demo-workspace \
  --name demo-vm \
  --image-template-id ubuntu-2204 \
  --vcpu 2 \
  --memory-mb 4096 \
  --architecture x86_64 \
  --timeout-seconds 300
```

- `--architecture` 支持 `x86_64`、`arm64`
- `--firmware` 支持 `bios`、`uefi`、`uefi-secure-boot`；省略时使用镜像模板值
- `--cloud-init-user-data-secret-name` 引用 workspace namespace 中已有的 Secret
- `--cloud-init-network-data-file` 从本地文件读取 network-data
- `--retain-disk-on-delete` 请求在删除 workload 时保留平台管理的持久盘；默认不启用
- `--timeout-seconds` 设置 VM 的存活时间，必须为正整数且没有固定上限；超时后 Kross 自动回收 VM
- VM 不支持 `autoDeleteOnCompletion`，`vm create` 不会发送该字段

启动、停止或重启 VM：

```bash
bytedcli kross vm execute \
  --workspace demo-workspace \
  --name demo-vm \
  --action restart
```

通过本地端口访问 SSH 或 RDP：

```bash
bytedcli kross vm access start \
  --workspace demo-workspace \
  --name demo-vm \
  --protocol ssh

ssh -p 2222 user@127.0.0.1
```

- SSH 默认本地端口为 `2222`，RDP 默认本地端口为 `13389`
- `--address` 仅允许 `127.0.0.1` 或 `::1`，不会监听外部网卡
- 可用 `--local-port` 覆盖默认端口，用 `--ttl-seconds` 指定 1 到 900 秒的 access session 生命周期
- 每个本地 TCP 连接都会创建独立的 Kross access session

## 创建 job workload

### Quick create

```bash
bytedcli kross workload create \
  --workspace demo-workspace \
  --name demo-job \
  --image demo/image:latest \
  --template-id linux-basic \
  --command 'sleep 300'
```

Quick create 默认行为：

- workload 类型固定为 `JOB`
- `container-name` 默认是 `main-container`
- CPU request/limit 默认 `1000m`
- memory request/limit 默认 `2048 MB`
- `timeoutSeconds` 默认 `300`
- `autoDeleteOnCompletion` 默认 `true`

常用覆盖参数：

```bash
bytedcli kross workload create \
  --workspace demo-workspace \
  --name demo-job \
  --image demo/image:latest \
  --template-id linux-basic \
  --cpu-request-milli 2000 \
  --cpu-limit-milli 2000 \
  --memory-request-mb 4096 \
  --memory-limit-mb 4096 \
  --timeout-seconds 900 \
  --command 'sleep 300'
```

### Advanced create

如果需要完整控制 `CreateWorkload` 请求体，使用：

```bash
bytedcli kross workload create \
  --workspace demo-workspace \
  --body-file ./demo-kross-job.json
```

注意：

- `--body-file` 不能和 quick create 参数混用
- 请求体里仍然必须包含 `TemplateID`
- 如果模板提供默认镜像，quick create 可以省略 `--image`
- 如果模板锁定 `image` 字段，quick create 不接受 `--image`

## 删除 workload

```bash
bytedcli kross workload delete --workspace demo-workspace --name demo-job
bytedcli --json kross workload delete --workspace demo-workspace --workload-id 72
```

- `--name` 和 `--workload-id` 二选一
- 推荐脚本场景使用 `--json`

## 远程执行命令

```bash
bytedcli kross workload exec --workspace demo-workspace --name demo-workload --command 'pwd'
```

可选能力：

- `--container-name`：多容器 workload 时显式指定目标容器
- `--shell`：请求特定 shell
- `--pod-name`：指定 pod
- `--tty`：请求 TTY，会更接近交互终端语义
- `--output-file`：把命令输出落到本地文件

默认行为：

- 使用非 TTY webshell
- 自动剥离 ANSI 控制序列，得到更干净的 stdout
- 默认超时 `30000 ms`

## 上传/下载容器文件

```bash
bytedcli kross workload upload \
  --workspace demo-workspace \
  --name demo-workload \
  --container-name main-container \
  --local-path ./config.yaml \
  --remote-path /tmp/config.yaml

bytedcli kross workload download \
  --workspace demo-workspace \
  --workload-id 72 \
  --container-name main-container \
  --remote-path /tmp/config.yaml \
  --output ./config.yaml
```

- `upload` 和 `download` 都支持 `--name` 或 `--workload-id` 二选一
- `upload` 必须传 `--local-path` 和容器内目标 `--remote-path`
- `download` 必须传容器内来源 `--remote-path` 和本地 `--output`
- 如果 workload 有多个容器，显式传 `--container-name`
- 如需指定 pod，可传 `--pod-name`
- `upload` 会先向 Kross 申请临时 capability URL，再通过 webshell 把文件拉到目标 workload
- `download` 会让 workload 先把远端文件推送到临时 capability URL，再由 CLI 下载到本地
- 这条临时文件链路同时适用于 Linux、macOS、Windows workload；Linux/macOS 目标容器需要提供 `curl`，Windows 目标容器需要提供 `curl.exe`

## 推荐闭环

```bash
# 1. 创建 workspace，并等待返回的 work order 完成
bytedcli kross workspace create \
  --name demo-workspace \
  --cluster default-multi-platform

# 2. 查 workspace、变量和模板
bytedcli kross workspace list
bytedcli kross workspace var list --workspace demo-workspace
bytedcli kross template list --workspace demo-workspace

# 3. 创建 workload
bytedcli kross workload create \
  --workspace demo-workspace \
  --name demo-job \
  --image demo/image:latest \
  --template-id linux-basic \
  --command 'sleep 300'

# 4. 远程执行命令
bytedcli kross workload exec \
  --workspace demo-workspace \
  --name demo-job \
  --command 'hostname; pwd'

# 5. 上传或下载容器文件
bytedcli kross workload upload \
  --workspace demo-workspace \
  --name demo-job \
  --container-name main-container \
  --local-path ./config.yaml \
  --remote-path /tmp/config.yaml

bytedcli kross workload download \
  --workspace demo-workspace \
  --name demo-job \
  --container-name main-container \
  --remote-path /tmp/config.yaml \
  --output ./config.yaml

# 6. 删除 workload
bytedcli kross workload delete --workspace demo-workspace --name demo-job

# 7. workspace 内没有 workload 后提交删除，并等待返回的 work order 完成
bytedcli kross workspace delete --name demo-workspace
```
