# ByteDog GDB workflow

本流程用于通过 `bytedcli bytedog` 分析 coredump，或在用户明确要求时 attach 在线进程。默认选择 coredump 分析；“看 core”“分析崩溃”“用 GDB 看栈”等请求不等于 attach 授权。

GDB 命令和文件列表仅支持 `cn`、`i18n-bd`、`i18n-tt`。切换站点时，把全局 `--site` 放在 `bytedog` 前。

## 分析 coredump

1. 确认目标类型，并用相同的目标参数列出 coredump 路径候选。列表不会读取远端文件内容，`content_verified=false`；已经知道精确 core 路径时，可以跳过文件列表。
2. 根据文件名和目标部署信息确认并选择正确的 core 文件。Cloud IDE 必须用 `tool elf list` 获取 ELF 路径候选、确认真实可执行文件后显式传 `--elf-path`；其它目标可从 `core.*` 自动推导同目录的 `elf.*`，其它文件名也必须显式传 ELF 路径。
3. 用 `gdb coredump create` 创建 session，保存返回的 session ID。
4. 用 `gdb session get` 查询该 session。只在返回 `command_executable=true` 时继续；若为 `false`，直接向用户报告 `command_unavailable_reason`，不要让用户自行判断原始状态字段。尚未可用时，按命令提示稍后查询同一个 ID。
5. 用 `gdb command execute` 提交一条 GDB 命令，保存返回的 ticket ID；再用 `gdb command get` 查询同一个 ticket，并读取返回的输出文件。若 session 详情无法明确确认 `gdb_type=coredump`，execute 也会失败关闭并要求显式传 `--confirm-performance-impact`。

```bash
bytedcli --json bytedog tool coredump list \
  --pod demo-pod

bytedcli --json bytedog gdb coredump create \
  --pod demo-pod \
  --coredump-path /opt/tiger/cores/demo-pod/core.12345

bytedcli --json bytedog gdb session get \
  --session-id 1001

bytedcli --json bytedog gdb command execute \
  --session-id 1001 \
  --command 'thread apply all bt'

bytedcli --json bytedog gdb command get \
  --ticket-id 2001
```

### 目标参数

- TCE Pod：`--pod <podname>`。
- 机器：`--ip <ip-or-hostname>`。
- Cloud IDE：`--workspace-id <workspace-id>`。
- Kubernetes session：`--ip <ip> --k8s-pod <podname> --container-id <container-id>`；文件列表不需要 `--container-id`。

TCE 默认查询容器对应的 core 目录。低版本 `coredump_handler` 返回空列表时，使用相同的 `--pod` 加 `--target-dir host` 查询 `/opt/tiger/cores`：

```bash
bytedcli --json bytedog tool coredump list \
  --pod demo-pod \
  --target-dir host
```

Cloud IDE 的 core 文件位于业务进程的当前工作目录。先根据团队维护的 Cloud IDE coredump 指引确认目录，再分别列出 core 和 ELF；创建 session 时必须显式传入选中的 `--elf-path`：

```bash
bytedcli --json bytedog tool coredump list \
  --workspace-id sample-workspace \
  --target-dir /workspace/demo

bytedcli --json bytedog tool elf list \
  --workspace-id sample-workspace \
  --target-dir /workspace/demo

bytedcli --json bytedog gdb coredump create \
  --workspace-id sample-workspace \
  --coredump-path /workspace/demo/core.12345 \
  --elf-path /workspace/demo/demo-server
```

### GDB 选择

- `--gdb env`：使用目标环境中的 GDB，默认值。
- `--gdb bytedog`：使用 ByteDog 提供的 GDB。
- `--gdb cuda-gdb`：使用目标环境中的 `cuda-gdb`。

## 查找已有 session

使用 `gdb session list` 按创建人、状态、IP、Pod 或备注筛选历史记录，再用 session ID 查询详情：

```bash
bytedcli --json bytedog gdb session list \
  --creator sample-user \
  --pod demo-pod

bytedcli --json bytedog gdb session get \
  --session-id 1001
```

## Attach 在线进程

仅当用户明确要求 attach 在线进程时使用。先列出进程并选择 PID；确认可接受 attach 可能暂停或降低目标进程性能后，使用完全相同的目标参数并显式传 `--confirm-performance-impact` 创建 attach session。不要因为暂时没有找到 coredump 就自动改用 attach。

```bash
bytedcli --json bytedog tool process list \
  --pod demo-pod

bytedcli --json bytedog gdb attach create \
  --pod demo-pod \
  --pid 12345 \
  --confirm-performance-impact
```

创建完成后的 session 查询与 coredump 流程相同。attach session 的每次 `gdb command execute` 都必须再次显式传 `--confirm-performance-impact`：

```bash
bytedcli --json bytedog gdb command execute \
  --session-id 1001 \
  --command 'continue' \
  --confirm-performance-impact
```
