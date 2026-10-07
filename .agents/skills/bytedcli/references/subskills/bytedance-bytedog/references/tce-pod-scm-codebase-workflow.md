# TCE Pod 到 SCM / Codebase 溯源

ByteDog 的 profile、线程、内存和 GDB 结果通常只能指出热点或异常调用栈。要判断根因，需要把这些证据映射到目标 Pod 实际部署的代码。收到 TCE podname 后，优先按本流程解析集群级 SCM 版本，再定位对应的 Codebase 仓库和 commit。

## 证据优先级

1. `tce instance search` 精确匹配的 Pod 身份：`psm`、`tce_env`、`cluster_id`。
2. `tce service get` 中 `data.repo_info[cluster_id]` 的集群级 SCM 快照。
3. SCM 精确版本记录中的 `base_commit_hash` 和 `commit_url`。
4. Codebase 中该 commit 对应的源码。

`data.latest_repo_info`、`data.runtime.latest_repo_info` 和分支最新代码只能作为补充线索，不能覆盖集群级 SCM 快照。已有精确 commit 时，不要用默认分支代码代替。

## 1. 用 podname 定位 TCE 实例

`--site` 必须选择目标 Pod 所在的 TCE 站点；它不一定与 ByteDog detail URL 的站点名称相同。下面使用占位站点和 Pod：

```bash
bytedcli --site cn --json tce instance search --keyword "sample-pod-7d9f6b8c4f-demo1"
```

从 `data.pods[]` 中选择 `pod_name` 与输入完全相等的唯一记录，并保存：

- `psm`
- `tce_env`
- `cluster_id`
- `pod_name`

搜索是模糊匹配。若没有完全相等的记录，先检查站点和完整 podname；若存在多个完全匹配项，结合用户给出的环境或集群消歧，不要任选一条。

## 2. 获取集群级 SCM 快照和 Codebase 入口

把上一步的 `psm` 和 `tce_env` 原样传给服务详情命令：

```bash
bytedcli --site cn --json tce service get --psm "example.service.api" --env "prod"
```

按以下顺序读取结果：

- 优先读取 `data.repo_info["<cluster_id>"]`。这是目标 Pod 所属集群的 SCM 快照；记录每个条目的 `name` / `path`、`version`、`scm_repo_id` 和 `type`。
- `type=main` 是主仓库；依赖仓库也可能包含 profile 或调用栈里的符号，不要在证据指向依赖时忽略它们。
- `data.latest_repo_info` 是服务级最新仓库信息。只有目标集群快照缺失时才把它作为候选，并明确说明它不能证明目标 Pod 正在运行该版本。
- `data.build.scm_repo_info` 描述构建配置，不是目标 Pod 当前部署版本的直接证据。
- `data.codebase_repo_url` 是服务关联的 Codebase 主仓入口。它可能为空，也可能只覆盖主仓。

## 3. 核对 SCM 精确版本

对目标集群快照中的每个相关仓库，先搜索 SCM 仓库并确认名称唯一：

```bash
bytedcli --json scm repo search "example/service/api"
```

再用集群快照里的 `version` 精确查询版本记录：

```bash
bytedcli --json scm repo version list "example/service/api" --version "1.0.0.123" --page-size 20
```

非默认 SCM 站点可在命令末尾补 `--scm-site <site>`。从 `data.versions[]` 中选择版本号完全匹配的记录，并保存：

- `base_commit_hash`
- `commit_url`
- `branch_name`
- `status`

如果精确版本没有结果，不要静默改查最新版本。先核对 SCM 站点、仓库名和版本号；仍无法匹配时，把缺失的 commit 映射作为分析限制报告出来。

## 4. 查询 Codebase 仓库并按部署 commit 读取源码

Codebase 仓库路径优先从 `data.codebase_repo_url` 解析；多仓库或该字段为空时，使用 SCM 精确版本记录的 `commit_url`。两者都没有时，不要根据名称猜测仓库映射。

```bash
bytedcli --json codebase repo get "example-org/example-service"
bytedcli --json codebase commit get -R "example-org/example-service" --revision "0123456789abcdef0123456789abcdef01234567"
bytedcli --json codebase repo directory list -R "example-org/example-service" --path . --revision "0123456789abcdef0123456789abcdef01234567" --page-size 100
bytedcli codebase repo file "src/example.ts" -R "example-org/example-service" --revision "0123456789abcdef0123456789abcdef01234567"
```

源码读取始终优先使用 SCM 版本记录的 `base_commit_hash`。只有 SCM 无法提供 commit，且 `latest_repo_info[].commit_id` 的仓库和版本都与目标集群快照一致时，才可使用该 `commit_id`；否则只报告分支或仓库线索，不把默认分支内容当作线上代码。

## 5. 与 ByteDog 结果联合分析

- CPU / on-CPU：把热点符号定位到该 commit 的函数实现、调用方和配置分支。
- off-CPU / pthread / Java lock：检查等待栈涉及的锁、阻塞调用、超时和临界区代码。
- jemalloc / Java allocation / heap：定位分配热点、缓存生命周期、容器持有关系和释放路径。
- thread overview / Java thread：把异常线程名、状态和栈帧映射到线程池、队列和任务入口。
- GDB / coredump：使用与目标 SCM 版本一致的源码和构建信息解释崩溃栈，不用主分支代码代替。

结论中至少保留以下溯源信息：目标 `pod_name / psm / tce_env / cluster_id`、SCM 仓库与版本、commit、Codebase 仓库路径，以及版本证据来自集群快照还是服务级 fallback。这样可以区分“profile 观察到什么”和“哪一版代码导致了它”。
