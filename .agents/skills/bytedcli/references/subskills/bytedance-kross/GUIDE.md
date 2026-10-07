---
name: bytedance-kross
description: "Use bytedcli Kross commands to manage workspaces, container workloads, and virtual machines. Supports workspace-visible container and VM image templates, VM creation and power actions, SSH/RDP loopback port forwarding, workload execution, and file transfer. Use when tasks mention Kross, workspace, workload, virtual machine, VM image, SSH/RDP access, remote exec, or workload file transfer."
---

# bytedcli Kross

Kross 用于创建多平台（Linux、macOS、Windows）容器环境（workload）。

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

## When to use

- 查询某个 workspace 在当前 cluster 下可见的 container template
- 查询 workspace 可用的 VM 镜像模板
- 创建 VM workload，并启动、停止或重启 VM
- 通过 loopback 端口转发访问 VM 的 SSH 或 RDP
- 创建 workspace，并指定 cluster 和 workspace 配额
- 删除没有 workload 的 workspace
- 列出当前用户有权限访问的 workspace
- 查看 workspace 变量，以及 secret 变量注入到 workload 内的文件路径
- 列出某个 workspace 下的 workload
- 创建一组可随时创建和销毁的 job workload
- 删除已有 workload
- 通过 webshell 在 workload 容器里远程执行命令
- 在 workload 容器里上传或下载文件
- 创建 workspace 后继续查询模板或管理 workload

## 前置条件

- 使用通用调用方式：`../../invocation.md`
- 先完成目标站点登录：`bytedcli auth login`
- 如果是 BOE，先执行 `bytedcli --site boe auth login`
- 创建 workspace 时已知目标 active cluster 的精确名称
- 操作已有 workspace 时，已知精确 workspace 名称并且有访问权限

> 执行前缀见 `../../invocation.md`；下面示例直接写 `bytedcli`。

## Quick start

```bash
# 创建 workspace；配额未指定时默认 1 CPU、1024 MB 内存、10 GB 存储
bytedcli kross workspace create \
  --name demo-workspace \
  --cluster default-multi-platform

# 先列出当前用户可访问的 workspace
bytedcli kross workspace list

# 查看 workspace 变量和 secret 文件注入路径
bytedcli kross workspace var list --workspace demo-workspace
bytedcli --json kross workspace var list --workspace demo-workspace --type SECRET

# 先查当前 workspace 可用模板
bytedcli kross template list --workspace demo-workspace
bytedcli kross vm template list --workspace demo-workspace

# 再看当前 workspace 下已有 workload
bytedcli kross workload list --workspace demo-workspace

# quick create：创建 JOB 类型 workload
bytedcli kross workload create \
  --workspace demo-workspace \
  --name demo-job \
  --image demo/image:latest \
  --template-id linux-basic \
  --command 'sleep 300'

bytedcli kross workload create \
  --workspace demo-workspace \
  --name demo-job \
  --template-id linux-basic \
  --command 'sleep 300'

# advanced create：直接传完整 CreateWorkload body
bytedcli kross workload create \
  --workspace demo-workspace \
  --body-file ./demo-kross-job.json

# 删除 workload（按名称或 workload id 二选一）
bytedcli kross workload delete --workspace demo-workspace --name demo-job
bytedcli --json kross workload delete --workspace demo-workspace --workload-id 72

# workspace 内没有 workload 后，按名称或 workspace id 二选一提交删除
bytedcli kross workspace delete --name demo-workspace
bytedcli --json kross workspace delete --workspace-id 42

# 通过 webshell 执行命令
bytedcli kross workload exec --workspace demo-workspace --name demo-workload --command 'pwd'
bytedcli --json kross workload exec --workspace demo-workspace --workload-id 72 --container-name main-container --command-file ./diag.sh

# 上传/下载容器文件
bytedcli kross workload upload --workspace demo-workspace --name demo-workload --container-name main-container --local-path ./config.yaml --remote-path /tmp/config.yaml
bytedcli kross workload download --workspace demo-workspace --workload-id 72 --container-name main-container --remote-path /tmp/config.yaml --output ./config.yaml
```

## VM workload

先查询 VM 镜像模板，再创建虚拟机：

```bash
bytedcli kross vm template list --workspace demo-workspace

bytedcli kross vm create \
  --workspace demo-workspace \
  --name demo-vm \
  --image-template-id ubuntu-2204 \
  --vcpu 2 \
  --memory-mb 4096
```

管理电源状态与本地访问：

```bash
bytedcli kross vm execute \
  --workspace demo-workspace \
  --name demo-vm \
  --action restart

bytedcli kross vm access start \
  --workspace demo-workspace \
  --name demo-vm \
  --protocol ssh
```

SSH 默认监听 `127.0.0.1:2222`，RDP 默认监听 `127.0.0.1:13389`。监听地址仅允许
`127.0.0.1` 或 `::1`；每个本地 TCP 连接都会创建独立的短期 Kross access session。

`vm create` 和 `vm execute` 是写操作。执行前先向用户展示 workspace、VM 名称或 ID、
动作及 vCPU、内存、镜像模板等关键参数，并等待用户明确确认。

## Recommended flow

### 1. 创建或选择 workspace

创建 workspace 时需要传精确的 active cluster 名称。CPU、内存和存储配额可以通过 `--cpu-cores`、`--memory-mb` 和 `--storage-gb` 覆盖：

```bash
bytedcli kross workspace create \
  --name demo-workspace \
  --cluster default-multi-platform \
  --cpu-cores 2 \
  --memory-mb 2048 \
  --storage-gb 20
```

命令返回 workspace 和 `CREATE_WORKSPACE` work order。返回成功表示工单已提交；继续操作前应确认 work order 状态为 `COMPLETED`。

如果使用已有 workspace，先用 `kross workspace list` 查看当前用户可访问的 workspace。

### 2. 查看模板和变量

用 `kross template list --workspace <name>` 获取 workspace 在所属 cluster 下可见的 container template，并从返回结果里选择 `template id`。

如果 workload 需要使用 workspace 变量，先用 `kross workspace var list --workspace <name>` 查看注入方式。普通变量通过环境变量注入；secret 变量通过文件注入，输出会包含 `UnixPath` 和 `WindowsPath`，不会返回 secret 明文。

### 3. 创建 job workload

优先使用 quick create：

```bash
bytedcli kross workload create \
  --workspace demo-workspace \
  --name demo-job \
  --image demo/image:latest \
  --template-id linux-basic \
  --command 'sleep 300'
```

quick create 默认会带上：

- CPU request/limit = `1000m`
- memory request/limit = `2048 MB`
- `timeoutSeconds = 300`
- `autoDeleteOnCompletion = true`

如需覆盖默认规格，可显式传：

- `--cpu-request-milli`
- `--cpu-limit-milli`
- `--memory-request-mb`
- `--memory-limit-mb`
- `--timeout-seconds`

如果模板本身提供默认镜像，quick create 可以省略 `--image`。
如果模板锁定了 `image` 字段，quick create 不接受 `--image`，需要直接使用模板镜像。

### 4. 在 workload 中执行命令

```bash
bytedcli kross workload exec \
  --workspace demo-workspace \
  --name demo-workload \
  --command 'hostname; pwd'
```

- 默认使用非 TTY webshell，返回更干净的 stdout
- 只有需要终端语义时再加 `--tty`
- 如果 workload 有多个容器，显式传 `--container-name`
- 如需指定 shell，可传 `--shell`
- 如果命令预计运行时间较长，使用 `--timeout-ms` 参数设置合适的超时时长

### 5. 上传或下载容器文件

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

- `upload` 必须传本地 `--local-path` 和容器内 `--remote-path`
- `download` 必须传容器内 `--remote-path` 和本地 `--output`
- 如果 workload 只有一个容器，可以省略 `--container-name`
- 如需指定 pod，可传 `--pod-name`

### 6. 清理 workload 和 workspace

```bash
bytedcli kross workload delete --workspace demo-workspace --name demo-job

# workspace 内没有 workload 后再提交删除
bytedcli kross workspace delete --name demo-workspace
```

删除 workspace 返回 `DELETE_WORKSPACE` work order。返回成功表示删除工单已提交；确认 work order 为 `COMPLETED` 后，workspace 才算删除完成。

如果是脚本或需要稳定消费输出，推荐把 `--json` 放在 `kross` 前面：

```bash
bytedcli --json kross workload exec --workspace demo-workspace --name demo-workload --command 'pwd'
```

## Notes

- `kross` 当前还暴露 `vm template list`、`vm create`、`vm execute` 和 `vm access start`
- `workspace create` 需要精确的 active cluster 名称；默认配额为 1 CPU、1024 MB 内存、10 GB 存储
- `workspace create` 和 `workspace delete` 都是异步操作，命令返回 work order；`Status=COMPLETED` 才表示操作完成
- `workspace delete` 支持 `--name` 或 `--workspace-id` 二选一；workspace 内仍有 workload 时服务端会拒绝删除
- `workspace list` 会自动翻完分页，列出当前用户可访问的 workspace
- `workspace var list` 会返回变量的 `InjectionMode`。普通变量看 `EnvName`，secret 变量看 `UnixPath` / `WindowsPath`
- `workspace var list --type SECRET` 只看 secret 变量；secret 值只会以 `MaskedValue` 脱敏展示，不返回明文
- `workload list` 会自动翻完目标 workspace 下的 workload 分页
- CLI 会按 workspace 名称自动解析 ID，但要求名称精确；模糊名称会报错并返回候选项
- 其他 `--workspace <name>` 命令在按名称解析 workspace 时，也只会在当前用户可访问的 workspace 范围内匹配
- `template list` 会由 Kross 服务端根据 workspace 可见性和生效中的 cluster binding 返回可用模板
- `create` 固定创建 `JOB` 类型 workload，模板必填
- quick create 在模板提供默认镜像时可以省略 `--image`
- 如果模板锁定 `image` 字段，quick create 不接受 `--image`
- 使用 `--body-file` 时，也需要在请求体里包含 `TemplateID`
- quick create 模式下，`--command` / `--command-file` 会映射到容器的 `Bootstrap` 字段
- `exec` 支持 `--name` 或 `--workload-id` 二选一
- Kross 鉴权复用 bytedcli 现有登录态，通过 `auth login` 后获取 ByteCloud JWT；不需要单独执行 Kross 登录
- `upload` 会先向 Kross 申请临时 capability URL，再通过 webshell 把文件拉到目标 workload
- `download` 会让 workload 先把远端文件推送到临时 capability URL，再由 CLI 下载到本地
- 这条临时文件链路同时适用于 Linux、macOS、Windows workload；Linux/macOS 目标容器需要提供 `curl`，Windows 目标容器需要提供 `curl.exe`
- `download` 使用 Kross 文件下载 API，并把响应内容写入 `--output`

## References

- `references/kross.md`
- `../../invocation.md`
- `../../troubleshooting.md`
