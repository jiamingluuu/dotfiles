---
name: bytedance-cloud-ide
description: "Operate Cloud IDE via bytedcli: manage workspace lifecycle (list/status/start/stop/restart across i18n & cn) and drive the compliance dev flow as sync → pull → run (sync the working tree to the shadow branch, pull it onto the online workspace, run the wrapper), plus read process logs and call the workspace agent. Use when tasks mention Cloud IDE, workspace lifecycle, compliance dev pod, shadow repo, workspace agent, process logs, compliance sync/pull/run, or running code on a Cloud IDE online workspace."
---

# bytedcli Cloud IDE

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

**Workspace 生命周期**(控制面操作,不依赖合规 pod,`cloud-ide workspace`):

- 列出可切换的所有 workspace(`cloud-ide workspace list`,`--site i18n`(默认)/ `cn`)
- 看某个 workspace 的生命周期状态(state / operation / agent 端口 / 资源)(`cloud-ide workspace status`)
- 启停/重启 workspace,可 `--wait` 轮询到收敛(`cloud-ide workspace start|stop|restart`)

**合规 dev 流**(`cloud-ide compliance`,三步流 `sync → pull → run`):

- 查看当前是否为合规开发 pod、影子仓 / 进程日志目录 / workspace agent 是否就绪(`cloud-ide compliance status`)
- **① sync**:把当前 git 工作树同步到合规影子仓分支 `compliance_bytedcli_<online id>` 并 force-push(`cloud-ide compliance sync`)
- **② pull**:让 online 空间把该分支拉到 online cwd(带 exit-code 闸门)(`cloud-ide compliance pull`)
- **③ run**:在 online agent 上触发 wrapper(run\_/build_cloudide.sh)(`cloud-ide compliance run`)
- **端口转发**:把 online 空间里某个监听端口暴露成公网 URL(`cloud-ide compliance expose`)/ 移除转发(`cloud-ide compliance unexpose`)
- 查看 / tail 合规进程日志(`cloud-ide compliance logs`)
- 直接调用本地 workspace agent 的 action(高级用法,如 `ComponentStatus` / `ExecRepoConfig`)(`cloud-ide compliance agent`)

> 老的一步到位 `execute` 已拆成 `sync / pull / run` 三条独立命令(便于 agent/人分步排查、单环重试;详见下方"完整工作流"与"合规插件 ↔ CLI 对应")。

## 诊断走 SDP,改编跑走 sync/pull/run(跨工具分工)

`sync → pull → run` 是「改+编+跑」链路,每次 force-push + pull、会动 online 工作树、整链 ~15–30s。**别拿它做只读巡检**(看远端文件、grep 日志、看/杀进程)—— 会造成大量无效 round-trip,且 pull 可能改动你正在编译的工作树。

只读诊断/巡检改用 **`gpcp sdp`**:白名单指令(`ls`/`cat`/`grep`/`tail`/`find`/`ps`/`kill`/`pkill`,支持管道 `|`),直打 online 空间真实文件系统,单条 ~5–8s、不 sync、不动工作树。online 空间 id 取自 `cloud-ide compliance status` 的 "online workspace"。完整用法见 `bytedance-gpcp` skill;典型:

```bash
bytedcli --site i18n-tt gpcp sdp job create --target cloudide \
  --workspace-id <online-ws-id> --user <user> --region sg --http-timeout-ms 90000   # → jobId
bytedcli --site i18n-tt gpcp sdp command execute --job-id <jobId> --region sg \
  --command "tail -n 200 /cloudide/compliance/processlog/bash-<uuid>/process.log"
```

**怎么选:** 看文件 / 日志 / 进程、判断「远端到底有没有 X / DAG 里有没有某节点」→ **SDP**;改代码后真正编译 / 起服务 / 拉特征(需同步代码 + doas)→ **sync/pull/run**;杀跑飞的远端进程 → SDP `pkill -9 -f <name>`。SDP 用管道别用 `&&`/`;`(复合易超时),输出首行是命令回显(消费时跳过)。

## 运行环境(不限于 Cloud IDE BOE pod)

按命令组分两类:

- **`cloud-ide workspace *`(控制面)**:只需 ByteCloud 登录,不依赖本地合规 pod 资源。从任意机器都能列/看/启停 workspace。默认 region `i18n`(tiktok-row);`--site cn` 走 `cloud.bytedance.net`,**需要单独的 cn SSO 登录**(`bytedcli --site cn auth login`),i18n 登录不认 cn 控制面,反之亦然。合规链路本身固定 i18n。

- **`cloud-ide compliance *`(合规 dev 流)**:
  - **在合规 pod 内**:零配置直接用(本地有 `/cloudide/compliance/`、`/cloudide/socket/workspace.sock`、`/cloudide/workspace/` 等)。
  - **离 pod / 非 BOE 机器**:也能跑,但要满足三件事——(1)用环境变量把硬编码的本地根改掉:`CLOUDIDE_COMPLIANCE_ROOT` / `CLOUDIDE_SHADOW_REPO_ROOT` / `CLOUDIDE_PROCESSLOG_DIR` / `CLOUDIDE_WORKSPACE_ROOT`(本地仓库所在根),避免"非 pod 直接 throw";(2)本地仓库路径与 online 路径不一致时,用 `--remote-dir <online 路径>`(在 `/cloudide/workspace/` 下,可用 `CLOUDIDE_ONLINE_WORKSPACE_ROOT` 覆盖)把远端 cwd 与本地仓库目录解耦;(3)online 空间必须就绪——加 `--ensure-ready` 让它在 pull 前自动探活(停了会先 start 再等)。
  - **注意**:从非 BOE 机器"触发合规 online 空间"是否被允许,是**合规政策**问题(需合规组放行),与代码是否跑得通无关——上线用途前先确认。
  - 缺前置资源(如 `compliance status` 找不到 workspace agent socket)时命令返回带 hint 的结构化错误,而不是静默失败。

## Quick start

```bash
# --- Workspace 生命周期(控制面,不依赖合规 pod) ---
# 列出所有 workspace(默认 i18n;cn 需 cn SSO 登录)
bytedcli cloud-ide workspace list
bytedcli --json cloud-ide workspace list --site cn --page-size 20

# 看某个 workspace 状态(不传 --id 默认取 CLOUDIDE_RELATED_WORKSPACE_ID 绑定的 online 空间)
bytedcli cloud-ide workspace status --id <workspaceId>

# 启停/重启,--wait 轮询到收敛;restart 可带 --cpu/--mem/--disk 改配额
bytedcli cloud-ide workspace start --id <workspaceId> --wait
bytedcli cloud-ide workspace restart --id <workspaceId> --wait

# --- 合规 dev 流 ---
# 环境与前置状态自检
bytedcli cloud-ide compliance status

# 同步当前工作树到影子仓分支(先 dry-run 预览,不真正 push)
bytedcli cloud-ide compliance sync --dry-run

# --- 改编跑三步流:sync -> pull -> run(按顺序) ---
# ① sync:写 wrapper + force-push compliance_bytedcli_<online id> 分支
#   有 --script 就写 wrapper:默认 run_cloudide.sh,--build 写 build_cloudide.sh(--wrapper-as 可覆盖)
bytedcli cloud-ide compliance sync --dir /cloudide/workspace/demo-repo --script run_tool.sh --args '-f WITH_BFS_TRACE'

# ② pull:让 online 拉该分支(--ensure-ready 停了先起;带 exit-code 闸门,拉挂了不会往下跑)
bytedcli cloud-ide compliance pull --dir /cloudide/workspace/demo-repo --ensure-ready

# ③ run:触发 wrapper(默认 self-doas,需先 kinit;--follow 流式看输出)
bytedcli cloud-ide compliance run --dir /cloudide/workspace/demo-repo --follow

# 只改一行想重跑:不用重来,单独再 run 一次(不重 sync/pull)
bytedcli cloud-ide compliance run

# build:sync 写 build wrapper,run 用 --build 触发 Build(两处类型要一致)
bytedcli cloud-ide compliance sync --script build.sh --build
bytedcli cloud-ide compliance run --build

# '指定 PSM' 模式:预取该 psm 的 doas SEC token
bytedcli cloud-ide compliance run --psm demo.service.psm

# 端口转发:把 online 空间里正在监听的端口暴露成公网 URL(返回 Result.url);
# 底层经 sync → pull → run 在 online pod 上执行,需先 kinit(同 run)。
bytedcli cloud-ide compliance expose --port 8080 --dir /cloudide/workspace/demo-repo --ensure-ready
# 移除转发
bytedcli cloud-ide compliance unexpose --port 8080 --dir /cloudide/workspace/demo-repo

# 多仓:pull 的 --dir + 每个 --repo 都必须先 sync 过(pull 从各自 shadow 仓推导);
# sync 用变参 --dir 同步多仓(只有带 --script 的那次写 wrapper);run 只跑主仓
bytedcli cloud-ide compliance sync --dir /cloudide/workspace/main-repo --script run_tool.sh
bytedcli cloud-ide compliance sync --dir /cloudide/workspace/dep-a
bytedcli cloud-ide compliance pull --dir /cloudide/workspace/main-repo --repo /cloudide/workspace/dep-a
bytedcli cloud-ide compliance run --dir /cloudide/workspace/main-repo

# 任意机器/离 pod:--workspace 指定 online 目标 + --remote-dir 指 online cwd(本地路径可任意)
bytedcli cloud-ide compliance sync --dir ~/src/myrepo --script run_tool.sh --workspace <onlineId>
bytedcli cloud-ide compliance pull --dir ~/src/myrepo --remote-dir /cloudide/workspace/main/myrepo --workspace <onlineId> --ensure-ready
bytedcli cloud-ide compliance run --dir ~/src/myrepo --remote-dir /cloudide/workspace/main/myrepo --workspace <onlineId> --follow

# 强制拉取(删 online 仓库目录重新 clone,丢 online 未提交改动):破坏性,必须配 --yes
bytedcli cloud-ide compliance pull --force --yes

# 列出已记录的 run(进程列表,含 CLI + IDE)
bytedcli cloud-ide compliance session list
bytedcli --json cloud-ide compliance session list --all

# 按 pid 流式看某次 run 的远端日志(可离 pod,只要登录 + 有 session 记录)
bytedcli cloud-ide compliance logs --session 261239 --follow

# 列出最近的本地进程日志
bytedcli cloud-ide compliance logs --list

# tail 最新进程日志的末尾 500 行(自动从文件尾部有界读取,支持超大日志)
bytedcli cloud-ide compliance logs --tail 500

# 调用本地 workspace agent(高级)
bytedcli cloud-ide compliance agent --action ComponentStatus

# 机器可读输出
bytedcli --json cloud-ide compliance status
```

## 完整工作流(端到端)

在任意环境下开发 / 运行 / 看日志的规范流程:

1. **(离 pod 才需)配置**:`bytedcli --site i18n-tt auth login`;`kinit`(self-doas 模式);设 `CLOUDIDE_RELATED_WORKSPACE_ID`(或每条命令带 `--workspace <onlineId>`)、以及 `CLOUDIDE_COMPLIANCE_ROOT` 等本地根 env。pod 内这些都自带,跳过。
2. **选/确保 online 空间**:`workspace list` 选目标 → `workspace status --id <id>` 看就绪;停了 `workspace start --id <id> --wait`(或下一步直接加 `--ensure-ready`)。
3. **改代码**:本地随便改,不用先 commit(sync 抓工作树现状,不碰你真实仓库 git 状态)。
4. **① sync**:`compliance sync --dir <repo> --script <run_tool.sh>` — 写 wrapper + force-push `compliance_bytedcli_<online id>`。
5. **② pull**:`compliance pull --dir <repo> --ensure-ready` — online 拉分支到 online cwd;**带 exit-code 闸门**,拉失败/未确认就报错,不会往下跑旧代码。
6. **③ run**:`compliance run --dir <repo> --follow` — 触发 wrapper,`--follow` 流式看输出。**改一行想重跑,只重 run**,不用重 sync/pull。
7. **看日志**:`compliance logs --session <pid> --follow`(跟某次 run,离 pod 也行)/ `logs --tail 500`(本地镜像);**只读巡检(grep/看文件/看进程)走 SDP**,别用 run。

离 pod 且本地路径 ≠ online 路径时,每步加 `--workspace <onlineId>` + `--remote-dir <online 路径>`(见 Quick start 末段)。

## 合规插件 ↔ CLI 对应

Cloud IDE 里的「合规插件」(DevKit)按钮,在 CLI 里都有等价命令——CLI 适合脚本化 / agent 驱动 / 离 IDE 使用。注意:插件是"一步到位"一个按钮,CLI 刻意拆成 `sync / pull / run` 三条(便于分环排查、单环重试):

| 合规插件里的动作                                      | CLI 命令                                                                            | 说明                                                                                                                                                                                                                                                               |
| ----------------------------------------------------- | ----------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| "运行" / "编译" 按钮(一步)                            | `compliance sync --script <name>` → `pull` → `run [--build]`                        | 三步等价插件一次点击。sync 写 wrapper(名字按 `--script` 前缀或 `--build` 选 `run_`/`build_cloudide.sh`);**run 的 `--build` 要和 sync 写的 wrapper 类型一致**。插件只允许 `run_`/`build_` 开头脚本是插件侧逻辑。                                                    |
| "强制同步"(提示"远端代码仓库会被删除并重新 clone")    | `compliance pull --force --yes`                                                     | 破坏性:删 online 仓库目录重新 clone,丢 online 未提交改动。CLI 要求 `--yes` 二次确认。                                                                                                                                                                              |
| 插件的"端口转发" / 端口列表                           | `compliance expose --port <n>` / `compliance unexpose --port <n>`                   | 端口转发是 **per-pod、只走 pod 本地 workspace-agent socket**(`?Action=Expose`);online agent 的 HTTP 面**不暴露** Expose,所以 CLI 经 `sync → pull → run` 在 online pod 上代跑 expose 步骤,`expose` 从 run 日志里解析回 `Result.url`(公网地址)。需先 kinit(同 run)。 |
| 插件的 stop / restart 空间按钮                        | `cloud-ide workspace stop\|restart --id <id>`                                       | 走同一个 PartialUpdateWorkspace 控制面接口。                                                                                                                                                                                                                       |
| 看空间状态 / 是否就绪                                 | `cloud-ide compliance status`(本地视角) 或 `cloud-ide workspace status`(控制面视角) |                                                                                                                                                                                                                                                                    |
| 插件运行报 "build_cloudide.sh: No such file" 类隐晦错 | `pull --ensure-ready` / `run --ensure-ready`                                        | 多半是 online 空间被回收/停了;`--ensure-ready` 先探活自愈。                                                                                                                                                                                                        |

**分支名注意**:CLI 推的是 `compliance_bytedcli_<online id>`(带 `bytedcli_` 前缀),与插件的 `compliance_<local id>` **故意错开**,两者互不覆盖。所以同一仓库用插件和 CLI 各推各的分支,不冲突但也不共享。

只读诊断(看远端文件/日志/进程)**不要**用 run,走 SDP(见上"诊断走 SDP")。

## Agent Guidance

- `sync` 使用 GIT_DIR 重映射到 shadow repo(默认 `/cloudide/compliance/shadow_repo`,可用 `CLOUDIDE_SHADOW_REPO_ROOT` 等 env 改),不污染你真实仓库的 git 状态;`git add -A` 抓工作树现状(**不要求先 commit**,tracked-but-ignored 文件也会带上);**没有本地 git identity 也能 sync**(用固定 CLI author);commit 真失败(hook / index / 权限)会抛 `CLOUD_IDE_COMMIT_FAILED` 而不是假成功;不修改你的 `.gitignore`;仅支持本地 workspace 根(默认 `/cloudide/workspace/`,可用 `CLOUDIDE_WORKSPACE_ROOT` 改)下的仓库;不确定先 `--dry-run`。
- `pull` 让 online 拉 sync 推的分支,复用现有 **exit-code 闸门**(非 0 → `CLOUD_IDE_PULL_FAILED`;无完成标记 → `CLOUD_IDE_PULL_UNCONFIRMED`)——保证不在旧代码上跑。`pull` 从本地 shadow 仓**重新推导** repo/branch/commit,所以**必须先 sync**(没 shadow 分支会报 `CLOUD_IDE_NOT_SYNCED`)。
- `run` 只触发 online agent 的 Run/Build(不 sync/不 pull/不碰 git),返回 PID + 日志路径;`--follow` 流式看。鉴权两模式:默认 self-doas(带 kinit 的 kerberos 票据,需先 `kinit`);`--psm <psm>` 预取该 psm 的 doas SEC token。**一致性由 pull 的闸门保证,run 只跑现场**——所以顺序是 sync → pull → run。
- `logs` 默认文本;进程日志可能数 GB,`--tail` 从尾部有界读取。
- Workspace 生命周期命令(`workspace list/status/start/stop/restart`)是控制面操作,`--site i18n`(默认)/`cn` 选 region;token 按 region 铸造,cn 需单独 cn SSO 登录。合规链路本身固定 i18n。
- `agent` 是低层逃生舱:`ComponentStatus` 只读;`ExecRepoConfig` 会按 `.bytediderc.json` 初始化/重建开发环境,非只读,谨慎使用。

## 可能有问题的点(踩坑清单)

- **顺序不能乱**:`run` 不带闸门,只跑 online 现场。想跑最新代码必须 `sync → pull → run`;直接 `run` 会跑上一次 pull 的代码。忘了 sync 就 pull → `CLOUD_IDE_NOT_SYNCED`。
- **`--build` 要一致**:wrapper 类型由 `--build` 决定(不是脚本名):`sync --build` 写 build_cloudide.sh,必须配 `run --build`;`sync`(默认)写 run_cloudide.sh,配 `run`(默认)。不一致会触发另一个不存在的 wrapper,报 "No such file"。
- **`--remote-dir` 不与 `--repo` 同用**:依赖仓仍假设本地==online 路径;组合会报 `CLOUD_IDE_RUN_INPUT_ERROR`。
- **online id 是分支键**:分支 `compliance_bytedcli_<online id>`。pod 内也用 online id(取自 `CLOUDIDE_RELATED_WORKSPACE_ID`),**没有本地 id 兜底**——pod 上若没设 RELATED、又没传 `--workspace`,会报"no target online workspace"。
- **cn 要单独 SSO**:`--site cn` 需 `bytedcli --site cn auth login`;i18n 登录不认 cn 控制面。
- **非 BOE 触发合规是政策 gate**:代码跑得通 ≠ 被允许;上线前问合规组。
- **池化 online 空间会被回收**:闲置(尤其只有 CLI/agent 无 IDE 交互)可能被 stop/重置,导致 pull "not a git repository" / run "No such file"。用 `--ensure-ready` 自愈,或 `workspace status` 排查。
- **就绪判定看 agent,不看 Operation**:就绪 = `State=started` 且 agent 端口 `online`。真实平台会长期保留 `Operation=start` / `LastOperationStatus.State=Running` 作为**健康稳态**(不是"操作进行中"),所以 `workspace status` 看到这两个非空/Running 是正常的,`--ensure-ready` / `start --wait` 只要 agent online 就会立即放行。
- **shadow 首次拷贝开销**:sync 首次会 `cp` 整个**公共 git dir**(`--git-common-dir`)到 shadow 根;超大 monorepo 会慢/占盘。
- **linked worktree 已支持**:在 `git worktree add` 出来的 linked worktree 里跑 sync/pull 也 OK——repo 根按 `--show-toplevel` 定、shadow 按**公共 git dir** 派生(对象/refs/remotes 都在那,per-worktree dir 没有对象),快照基于**当前 worktree 的 HEAD** 且**绝不动你的工作树文件**(用 ref plumbing + `read-tree`,不用会覆盖文件的 `checkout`)。shadow 首拷后靠 `objects/info/alternates` 指回真实对象库读新提交对象,所以**别删/搬真实 `.git`**,否则 shadow 解析不到对象。
- **self-doas 要先 `kinit`**;`--follow` 到 maxPolls 会截断(提示里给 resume 命令),不代表进程结束。
- **只读巡检别用 run**:看文件/日志/进程走 SDP(`gpcp sdp`),run 每次都 force-push + 动 online 工作树。
- **端口转发走 run 通道**:`expose`/`unexpose` 暴露的是 **online pod 自己**的端口(不是本机 / dev pod);它复用 `sync → pull → run`,所以同样需要一个 synced repo 的 CWD(`--dir` / `--remote-dir`)+ kinit。它会临时把该 repo 的 `run_cloudide.sh` 写成 expose wrapper 并在结束后恢复本地原文件;online compliance 分支上会留一次快照,你下次正常 `sync` 会覆盖它。要暴露的端口必须**已在 online pod 上监听**,`expose` 才有意义。
