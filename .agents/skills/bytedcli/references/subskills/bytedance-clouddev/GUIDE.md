---
name: bytedance-clouddev
description: "CloudDev BOE lane development instance skill. Use when tasks mention CloudDev, BOE 泳道开发实例, dev instance, syncing local code to a BOE lane, TCE runtime dev pod, bytesuite (legacy backend name only), rsync/bsync code sync, or local CloudDev space bindings. Provides bytedcli commands to create/list/get/start/reload/stop/delete CloudDev instances, capture instance runtime logs, and manage locally remembered spaces. Command entry is `bytedcli clouddev`."
---

# bytedcli CloudDev

本 Skill 用于创建、部署和管理 CloudDev BOE 泳道开发实例。命令入口是 `bytedcli clouddev`，子组为 `instance`（实例生命周期）与 `space`（本地记住的 space 绑定）。

首版范围：TCE runtime、BOE region。FaaS、Goofy、Cloud IDE 代理模式不在覆盖范围内。

## 前置条件

- 使用通用调用方式：`../../invocation.md`
- 需要先完成 ByteCloud 登录：`bytedcli auth login`（CloudDev 后端固定归入 cn 凭据分区，与 `--site` 无关）
- 需要结构化输出时，把 `--json` 放在 `clouddev` 前面：`bytedcli --json clouddev ...`
- `instance start` / `instance reload` 走 rsync 的同步路径时对**本机** rsync 有环境要求（GNU rsync、协议号 ≥ 32）。是否走 rsync 由实例决定，先跑一次不带 `--yes` 的 dry-run（只读预览、不提交）看 `Sync plan:` 的 `method=`；为 `rsync` 时按下方「rsync 同步排查」自检本机 rsync 后再 `--yes` 提交。

## Agent Guidance

- `instance delete` 永久销毁实例，不可恢复，与 `instance stop`（只停服务、实例保留、可再 start）语义不同。dry-run 会实时查询并回显该实例的 status 与 psm，供确认删的是不是目标实例；运行中的实例不会被阻止删除（不打断自动化清理），status 回显就是唯一提醒，因此提交前务必看一眼 dry-run。删除后本地 space 绑定不受影响（绑定是 space 级、非 instance 级），`space delete` 才清理本地记录。
- `instance start` 有两种互斥模式：传 `--id <id>` 启动已有实例；省略 `--id` 而传创建参数（`--name`/`--psm`/`--env` 必填，可选 `--space-key`）则一条命令内创建实例、报告 instance id、再启动它。`--id` 与 `--name`/`--psm`/`--env`/`--space-key` 中任意一个同传会报 `CLOUDDEV_INPUT_ERROR` 冲突错误；都不传或创建参数不全同样报错并在 hint 里列出缺失项。注意 `--runtime`/`--region`/`--cluster` 有默认值、不参与模式判定，只在创建模式下生效，`--id` 模式下传了会被静默忽略。
- 创建并启动模式的三个关键行为：① v4 创建返回同一 space 下同名冲突时，默认报 `CLOUDDEV_INSTANCE_EXISTS`；只有显式传 `--reuse` 才会按 space + name 定位并复用它继续启动。**复用会把本地代码同步到该实例并删除其远端原有内容**，因此复用时会在 stderr 打一条显式提示（含被复用的 id 与 name）。定位不到或命中多条无法判定时仍报冲突并给出检索命令。`instance create` 同样支持显式 `--reuse`，默认不复用。② 新建实例到暴露 sync 信息之间有空窗，命令会自动轮询等待就绪再同步启动（等待时长为内置上限，不暴露成 CLI 参数）。③ `--dir` 在该模式下统一归一化到 git 根后同时用于 space 绑定与代码同步，传仓库子目录不会出现「绑定 git 根、只同步子目录」的偏差。
- 创建并启动模式下实例一旦建出，**id 一定拿得到**：实例创建成功后立刻在 stderr 报告 `id=... space_key=...`，且创建之后的任何失败（等待 sync 超时、上传失败、TCE 冲突、`--wait` 构建失败）都会把 instance id 写进错误的 `details.instance_id` 与 hint，并附可直接复制的 `instance start --id <id> --yes` 重试命令。文本模式的创建摘要先于启动摘要输出，但它只在整条链路成功后渲染，所以失败时以 stderr 提示和错误 hint 为准。
- `instance start` 的 JSON 输出恒含 `create` 字段：创建并启动模式下是创建阶段摘要（instance id、space key、workspace 绑定、复用状态），`--id` 模式下为 `null`。两种模式共用同一套 schema，下游脚本无需先判断模式再解析。该摘要**不含**创建 payload（`params`）——那份平台推荐配置里的 `run_env` 含服务运行时环境变量，可能带凭据，只在 `instance create` 的 dry-run 预览里输出。
- `instance create`/`start`/`reload`/`stop`/`delete` 都是写操作，默认 dry-run，只预览不提交；必须显式加 `--yes` 才会真正创建实例、同步代码或改变实例状态。先看 dry-run 输出再决定是否加 `--yes`。创建并启动模式的 dry-run 只预览创建侧的平台推荐配置（实例尚不存在，故 `id` 与 sync plan 的远端字段均为 `null`；未做本地扫描，`fileCount`/`isGitRepo` 同样为 `null` 而非 0/false）。
- `instance create` 的 dry-run 不是纯本地校验：它会请求一次 v4 `instance_config` 推荐配置，预览里看到的是实际提交的 snake_case body；`tce_config` 原样用于真实请求，但预览中的 `new_env_vars` 值会脱敏。
- space 语义：`instance create` 成功后会把 space key 与当前工作目录（按 git 根归一化）的绑定记到本地 `clouddev/state.json`；space 记录本身只存在本地，`space delete` 也只删除本地记录。`instance list`/`instance get` 的实例字段永远来自远端实时查询，不读本地状态。
- `space list` 会为每个本地 space 实时查询远端实例并附带展示（ID / PSM / 状态）；某个 space 查询失败（未登录、断网）时该 space 降级为 `instances: null` + `instancesError`，命令整体仍成功。
- `space delete` 删除前会检查该 space 是否有运行中实例（状态为 `running`/`starting`/`debugging`）：有则报 `CLOUDDEV_SPACE_HAS_RUNNING_INSTANCES` 阻止删除，按 hint 先 `bytedcli clouddev instance stop --id <id> --yes` 停止实例再重试；实例检查失败（离线、未登录）时不阻止删除，仅输出 warning。`--stale` 批量清理时跳过含运行中实例的 space（结果中的 `skippedSpaces`），其余照常清理。
- `--space-key` 在 `instance create`、`instance list` 与 `instance start` 的创建并启动模式上可用：未显式传时优先复用当前工作目录已绑定的 space。只有 `instance create` 与 `instance start` 创建模式会在从未绑定过时新建 space；`instance list` 此时报 `CLOUDDEV_SPACE_NOT_BOUND`。`instance start --id` 与 `instance reload` 没有 `--space-key`，它们按 `--id` 查到的实例所属 space 反查本地工作目录（未绑定时回退到当前目录），也可以用 `--dir` 直接指定。
- `start`/`reload` 会按实例返回的 `sync.method` 自动选 rsync 或 bsync，两者都不会在文本或 JSON 输出中暴露 token、SSH key 或未脱敏的 host；不要尝试从命令输出里读取这些字段去手动同步。
- `start --wait` 会轮询实例状态直到 `running`/`ready`（或返回了 main service address）判定成功，`unhealthy`/`stopped`超时或轮询超过 `--timeout-ms` 会报错并保留已提交的 run，不会自动重试。
- `instance log` 读取运行中实例的平台日志流：连接时先回放滚动 backlog（约最近 8KB，低流量服务约覆盖最近 1 分钟），再收 `--duration-ms` 窗口内的实时日志后返回，不是完整历史日志。捕获总量有滚动字节上限（默认 64MiB），超限丢最旧内容并在输出中标记 `bytesTruncated`；长窗口 + 大日志量场景可用 `--max-capture-bytes` 调整。
- `instance log --follow` 是不限时长的流式模式：逐行输出直到 Ctrl-C 或实例停止，断线自动退避重连，并对重连时的 backlog 重放做重叠去重（去重按"宁可少量重复、不可丢行"取舍）。`--follow` 与 `--duration-ms`/`--limit`/`--max-capture-bytes` 互斥。`--output-file <path>` 把日志行（已剥 ANSI）追加写入文件（仅 follow 模式）；`--json` 下必须搭配 `--output-file`，stdout 只在流结束时输出一个 summary envelope，连接状态通知走 stderr。注意：录制器断线期间产生、又被 8KB backlog 冲掉的日志会永久丢失，follow 不承诺完整性。
- `instance start --yes --log-file <path>` 在提交 start 后立即 attach 日志流并全程落盘直到 session 结束或 Ctrl-C。构建失败的 session 会被平台删除、日志不可事后恢复，start 时原生录制是保住 build 日志的唯一可靠方式。start 提交阶段平台自身短暂占用日志通道，录制器内置初次连接重试；attach 最终失败只降级为结果里的 `logRecording.outcome: "attach_failed"`，不影响 start 本身成败。
- 端到端调试的两种读取模式：默认用事后读取——触发请求后立刻串联执行 `curl "http://<main-service-address>/api/demo" ; bytedcli clouddev instance log --id demo-instance-id`，backlog 足以覆盖 shell 串联的百毫秒级间隔；日志量大到 backlog 秒级即被冲掉的服务改用先挂后触发——先 `bytedcli clouddev instance log --id demo-instance-id --follow --output-file /tmp/demo.log &` 建立连接再触发请求。
- 日志通道是单消费者：`CLOUDDEV_LOG_CHANNEL_BUSY` 表示另一客户端或平台启动流程正占用日志流，稍后重试即可（busy 时命令会吃满两次连接超时、默认约 20 秒后才报错）；若确认没有其他消费者仍持续报 busy，排查到日志网关的网络可达性，`details.last_error` 在有显式 socket 错误时会给出底层原因（握手挂起超时则为 `null`）。
- 日志流仅覆盖运行中实例；实例非 running 时报 `CLOUDDEV_LOG_UNAVAILABLE`。启动失败的详细日志平台不保留，改用 `bytedcli clouddev instance get --id <id>` 看 `failure_message`。
- 错误码：
  - `CLOUDDEV_INSTANCE_EXISTS`（后端 `-1234`）：同一 space 下已有同名实例，不是网络错误。改用 `bytedcli clouddev instance list --space-key <key>` 查已有实例；确认要覆盖远端目录时显式加 `--reuse`。
  - `CLOUDDEV_INSTANCE_NOT_EXISTS`（后端 1216）：目标实例不存在，按 hint 用 `instance list --space-key <key>` 排查。
  - `CLOUDDEV_TCE_CONFLICT`（后端 1221）：TCE lane 冲突。先 `bytedcli clouddev instance get --id <id>` 确认状态。
  - `CLOUDDEV_SPACE_NOT_BOUND`：当前目录没有绑定过 space。显式传 `--space-key`，或先在该目录跑一次 `instance create --yes` 建立绑定。
  - `CLOUDDEV_SPACE_HAS_RUNNING_INSTANCES`：`space delete` 的目标 space 还有运行中实例。按 hint 先停实例再重试删除；`details.instances` 列出全部运行中实例可供逐个停止。
  - `CLOUDDEV_SYNC_ERROR`：实例还没暴露 sync 信息，或 bsync 既没 token 也没 rsync 需要的 port/ssh key；先确认实例状态再重试。同一错误码也用于本地侧同步前置检查失败：待同步的 git 仓库为空或 `git ls-files` 执行失败时会直接中止（不会用空文件列表把远端目录删空），按 hint 里的 `git -C <dir> status` 排查。该码同样覆盖本机 rsync 环境不达标（缺失、openrsync、协议号过低），排查见「rsync 同步排查」章节。

## Quick Start

```bash
# 创建实例：先 dry-run 预览平台推荐配置，确认无误再加 --yes 真正创建
bytedcli clouddev instance create --name demo-run --psm example.service.api --env boe_demo_lane
bytedcli clouddev instance create --name demo-run --psm example.service.api --env boe_demo_lane --yes
bytedcli clouddev instance create --name demo-run --psm example.service.api --env boe_demo_lane --reuse --yes

# 显式复用已有 space，或绑定非当前目录的本地代码
bytedcli clouddev instance create --name demo-run --psm example.service.api --env boe_demo_lane --space-key demo-space-key --yes
bytedcli clouddev instance create --name demo-run --psm example.service.api --env boe_demo_lane --dir /local/demo --yes

# 列出 / 查看实例（未传 --space-key 时用当前工作目录绑定的 space）
bytedcli clouddev instance list
bytedcli clouddev instance list --space-key demo-space-key
bytedcli clouddev instance get --id demo-instance-id

# 同步本地代码并启动 run：先 dry-run 看同步计划，再 --yes 提交；--wait 轮询到就绪
bytedcli clouddev instance start --id demo-instance-id
bytedcli clouddev instance start --id demo-instance-id --yes --wait --timeout-ms 600000
bytedcli clouddev instance start --name demo-run --psm example.service.api --env boe_demo_lane --reuse --yes

# 一条命令创建并启动：省略 --id 改传创建参数，先建实例、打印 id、再启动（冲突默认报错；显式 --reuse 才复用）
bytedcli clouddev instance start --name demo-run --psm example.service.api --env boe_demo_lane
bytedcli clouddev instance start --name demo-run --psm example.service.api --env boe_demo_lane --yes
bytedcli clouddev instance start --name demo-run --psm example.service.api --env boe_demo_lane --dir /local/demo --yes --wait

# 启动并同时录制日志流到文件（build 日志失败即删，start 时录制是唯一可靠覆盖）
bytedcli clouddev instance start --id demo-instance-id --yes --log-file /tmp/demo-build.log

# 改完代码后重新同步并 reload
bytedcli clouddev instance reload --id demo-instance-id --yes

# 读取运行时日志：backlog 回放 + 实时窗口（默认 10 秒），仅运行中实例
bytedcli clouddev instance log --id demo-instance-id
bytedcli clouddev instance log --id demo-instance-id --duration-ms 30000 --limit 200

# 流式跟随：不限时长、断线自动重连并去重 backlog 重放；后台录制配 --output-file
bytedcli clouddev instance log --id demo-instance-id --follow
bytedcli --json clouddev instance log --id demo-instance-id --follow --output-file /tmp/demo-instance.log

# 停止实例
bytedcli clouddev instance stop --id demo-instance-id --yes

# 永久删除实例（不可恢复）：dry-run 先回显该实例的 status/psm，确认后再加 --yes
bytedcli clouddev instance delete --id demo-instance-id
bytedcli clouddev instance delete --id demo-instance-id --yes

# 本地记住的 space：list 附带各 space 的远端实例（ID/PSM/状态），delete 默认 dry-run 且会阻止删除仍有运行中实例的 space
bytedcli clouddev space list
bytedcli clouddev space delete --space-key demo-space-key
bytedcli clouddev space delete --space-key demo-space-key --yes
bytedcli clouddev space delete --stale --yes

# 机器可读输出
bytedcli --json clouddev instance get --id demo-instance-id
```

## Notes

- `--runtime`（默认 `tce`）与 `--region`（默认 `boe`）当前都只接受首版支持的取值；`--cluster` 默认 `default`。
- `start`/`reload` 未传 `--dir` 时优先用实例 space 绑定的工作目录，其次才回退到当前目录；`create` 未传 `--dir` 时直接用当前目录（按 git 根归一化）。
- 用户可见 domain 名统一是 `clouddev`；`bytesuite` 只是历史后端 host/path，不要在命令、示例或文案中使用。

## rsync 同步排查

`start`/`reload` 走 rsync 的同步路径时，调用的是**本机** rsync 可执行文件。bytedcli 传给它的是 GNU rsync 的参数集（恒定使用 `-avP`/`--stats`/`--rsync-path`/`-e ssh …`，git 仓库另加 `--include-from`/`--exclude=*`/`--delete-excluded`，非 git 目录用 `--delete`），因此实现必须是 GNU rsync，openrsync 这类只支持参数子集的实现无法工作。此外要求协议号 **≥ 32**。

> 协议号只能逐机实测，不能按版本号推断：upstream 自 3.4.0 起为 32，但部分发行版把协议号 32 回传（backport）进了 3.2.7 的安全更新（如 Debian 12 的 `3.2.7-1+deb12u1`），而未打该补丁的 3.2.7 构建仍是 31 —— 同一个版本号两种协议号都存在。bytedcli 自身不做协议号校验，不达标只表现为 `CLOUDDEV_SYNC_ERROR`。

**适用范围**：以 dry-run 输出里 `Sync plan:` 的 `method=` 为准——`rsync` 时适用，`bsync` 时不受约束。

```bash
# 不带 --yes 只预览不提交，看 Sync plan 的 method
bytedcli clouddev instance start --id demo-instance-id
```

这个 `method` 是归一化结果：实例侧原始 method 为 `bsync` 但只暴露 `port` + `ssh_key`（无 token）时会回退成 `rsync`，而 token 不出现在任何命令输出中，因此不要试图自行判断 token 是否存在。

**典型表现**：

- 报 `CLOUDDEV_SYNC_ERROR`。非零退出时消息形如 `rsync exited with code <n>: <stderr>`（已脱敏并截断到 400 字符），超时为 `rsync timed out after 600000ms`。
- rsync 完全没装时报 `Failed to run rsync: spawn rsync ENOENT`。
- macOS Sequoia 及更高版本的系统自带 `/usr/bin/rsync` 已换成 openrsync（`protocol version 29`，只支持 rsync 参数的一个子集），必然失败。

**处置阶梯**（按顺序走，不要反复重试 start）：

1. **优先升级** rsync 到协议号 ≥ 32 的版本，升级后用 `rsync --version` 复验协议号。
2. **升级受限时先确认是否真的需要 rsync**：按上方「适用范围」跑一次 dry-run 看 `method=`；为 `bsync` 说明本次同步不走 rsync，本门槛不适用、可直接 `--yes` 提交。
3. **仍判定为 rsync 且无法升级**：停止本次同步尝试，并向用户报告 ① 实测的 `rsync --version` 首行；② 已尝试的升级路径与受阻原因；③ 可选后续（升级 rsync / 换一台达标机器 / 使用带 token 的 bsync 实例）。不要重试 `instance start`，也不要改用手工 scp/rsync 绕过同步链路。

**分平台升级要点**：

- **macOS**：系统自带 openrsync 位于 `/usr/bin/rsync`，装完 GNU rsync 必须确认 PATH 优先级，否则仍会命中 openrsync。用 `which -a rsync` 看全部命中路径，确认新版本排在 `/usr/bin/rsync` 之前；复验时 `rsync --version` 首行协议号应 ≥ 32 且不含 `openrsync`。
- **Linux**：先跑 `rsync --version` 看当前协议号——发行版的安全更新可能已把 32 回传进现有版本，无需升级。确实不达标时用发行版安全源/backports 升级或自行编译。无 root 的容器/CI 环境往往无法升级，直接走处置阶梯第 2、3 步。

## References

- `../../invocation.md`：通用调用方式、全局参数、JSON 模式。首次使用本 skill 前读。
- `../../troubleshooting.md`：工具版本过期、site 错配、未认证 / 401、网络与权限的排查路径。rsync 相关的同步失败见上方「rsync 同步排查」。
