---
name: bytedance-bam
description: 'BAM API 管理平台官方 skill，提供 API 接口元数据查询/管理、IDL 组件打包/检测修复等。当用户请求"API 查询/管理"、"接口元数据"、"接口/方法查询"、"IDL 查询/检测/同步"、"IDL 组件打包"、"IDL 版本更新"等时使用。'
---

# bytedcli BAM

本 Skill 提供两条使用路径：

| 用户意图                                                                 | 路径                  | 参考                      |
| ------------------------------------------------------------------------ | --------------------- | ------------------------- |
| 搜索 PSM、查方法、查版本、创建 IDL 版本、管理代码生成规则、打包 IDL 组件 | **A: BAM 元数据管理** | `references/metadata.md`  |
| IDL 改了要检查、提 MR 前检查、同步 BAM                                   | **B: IDL 一致性检测** | `references/idl-check.md` |

## 前置条件

- 使用通用调用方式：`../../invocation.md`

> 执行前缀见 `../../invocation.md`；下面示例直接写 `bytedcli`。

---

## 路径 A: BAM 元数据管理

### When to use

- PSM 搜索、收藏
- 查询本人最近访问过的 PSM（本机历史）→ 优先使用 `bam psm list --recent`
- 查询平台聚合的最近接口动态（与登录用户无强绑定）→ 使用 `bam psm list`（默认行为）
- 方法列表 / 方法详情
- 服务版本查询
- 创建服务版本（IDL 版本更新）
- 查询、创建、更新 BAM scaffold 代码生成规则，并触发代码生成或按仓库打包 IDL 组件

### Quick start

Commands are grouped under `bam psm`, `bam method`, `bam codegen`, `bam version`, and `bam idl`. Old flat names (e.g. `bam list-recent-psm`, `bam search-psm`, `bam list-method`, `bam get-method`, `bam versions`, `bam update-idl-version`) still work as hidden aliases (注：`bam list-recent-psm` 行为已反转，现路由到本地缓存视图，与 `bam psm list --recent` 同义；命令执行时会在文本模式打印一次性迁移提示，JSON 模式静默)。

```bash
# PSM 列表（三视图，互斥；缺省走 BAM 服务端聚合的平台动态视图）
bytedcli bam psm list --cluster default                    # 默认：BAM 服务端聚合的平台最近接口动态视图（与登录用户无强绑定）
bytedcli bam psm list --recent --cluster default           # 推荐：查询本人最近访问过的 PSM（bytedcli 本机历史，按 cloud site 隔离，上限 20 条；缺省字段会通过 service/info 单查并发回填，--no-enrich 关闭）
bytedcli bam psm list --recent --no-enrich                 # 关闭 lazy enrich，仅渲染本地缓存中已存在的字段
bytedcli bam psm list --starred --cluster default          # 收藏列表
bytedcli bam psm search "example.service.api" --cluster default

# 方法列表 / 详情（支持 --cluster 指定集群，--version 指定版本）
bytedcli bam method list --psm "example.service.api"
bytedcli bam method list --psm "example.service.api" --cluster i18n
bytedcli bam method list --psm "example.service.api" --cluster i18n --version 1.0.155
bytedcli bam method get --endpoint-id 123456 --version 1.2.3
bytedcli bam method get --psm "example.service.api" --method "DemoMethod"
bytedcli bam method get --psm "example.service.api" --method "DemoMethod" --ep-type rpc
bytedcli bam method get --psm "example.service.api" --method "DemoMethod" --cluster i18n
bytedcli bam method gencode --endpoint-id 123456
bytedcli bam method gencode --psm "example.service.api" --method "DemoMethod"
bytedcli bam method gencode --psm "example.service.api" --method "DemoMethod" --ep-type rpc
bytedcli bam method gencode --psm "example.service.api" --method "DemoMethod" --schema-type response
bytedcli bam method gencode --psm "example.service.api" --method "DemoMethod" --struct "DemoMethodRequest"

# Endpoint 查询（通过 HTTP path 查 PSM 归属）
bytedcli bam endpoint list --path "/api/example/path"

# 代码生成规则与生成任务
bytedcli bam codegen rule list --psm "example.service.api" --cluster default
bytedcli bam method list --psm "example.service.api" --cluster default
bytedcli bam codegen rule create --psm "example.service.api" --name "robot_demo_rule" --app-id 1234 --package "com.example.demo.model" --methods "GetDemoInfo"
bytedcli bam codegen rule update --rule-id 123456 --psm "example.service.api" --name "robot_demo_rule" --app-id 1234 --package "com.example.demo.model" --generate selected --methods "GetDemoInfo"
bytedcli bam codegen generate --rule-id 123456 --branch master
bytedcli bam codegen generate --rule-id 123456 --branch master --create-permission-ticket --permission-reason "need codegen access"
bytedcli bam codegen component build --component-repo "example-org/example-component" --idl-branch master
bytedcli bam codegen component build --component-repo "example-org/example-component" --idl-branch feature/idl --output-branch feature/generated

# 版本历史
bytedcli bam version list "example.service.api" --cluster default

# 按 git_branch 找 master/main 的最新版本（版本号是全服务自增的，列表第一条未必来自 master；
# 版本列表可能上千条，--json 落盘后用 jq 过滤，不要人工浏览全量输出；无输出 = 该分支没有 BAM 版本）
bytedcli --json bam version list "example.service.api" --cluster default > /tmp/bam-versions.json
jq -r '[.data.versions[] | select(.git_branch=="master" or .git_branch=="main")] | max_by(.ctime) | .version // empty' /tmp/bam-versions.json

# 找指定开发分支的最新版本（同名分支可能对应多个版本，取最新；无输出 = 该分支没有 BAM 版本）
jq -r '[.data.versions[] | select(.git_branch=="feature/demo-branch")] | max_by(.ctime) | .version // empty' /tmp/bam-versions.json

# 创建/更新 IDL 版本
bytedcli bam idl update --psm "example.service.api" --branch master --next-version
bytedcli bam idl update --psm "example.service.api" --branch "codex/fix-idl" --version "1.2.4" --commit-id "abc1234" --commit-msg "update idl"

# 引用 schema 查询（struct、enum、const）
bytedcli bam idl schema --psm "example.service.api" --version 1.0.155
bytedcli bam idl schema --psm "example.service.api" --version 1.0.155 --type enum --search EntityType
```

### Notes

- `psm list` 提供三种视图：`bam psm list`（不带视图开关）默认调用 BAM 服务端 `service/list?type=recent`，展示平台维度的最近接口动态（与登录用户无强绑定）；`--recent` 展示本人最近访问过的 PSM（bytedcli 本机访问历史，按 cloud site 隔离、上限 20 条、LRU 写入，命中具体 PSM 的命令成功后自动追加）；`--starred` 调用 BAM 服务端 `subscribe/list` 显示当前用户收藏的 PSM，与控制台「我的收藏」面板完全一致（按收藏时间倒序，不接受 `cluster`/`type` 过滤；`--cluster` 选项仍接受但内部忽略，仅用于保持 CLI 兼容性）。`--recent` 与 `--starred` 互斥（同时传入会抛 `BAM_INPUT_ERROR`）；隐藏别名 `bam list-recent-psm` 行为已反转，现路由到本地缓存视图（与 `--recent` 同义，break change）；命令执行时会在文本模式打印一次性迁移提示，JSON 模式静默；老脚本如需原服务端聚合视图，请迁移到 `bam psm list`（不带视图开关）。三视图文本表格列保持一致（`PSM/Owners/Protocol/Level/Service ID`）；JSON `services[]` 字段集合在三视图间略有差异：`server` / `starred` 视图直接透出 BAM `BamServiceInfo[]` 完整字段（`level`/`service_id` 为 number），`local` (`--recent`) 视图为显式裁剪后的 7 字段（`psm`/`owners`/`protocol`/`level`/`service_id`/`cluster`/`visited_at`，其中 `level`/`service_id` 为 string）。顶层 `source` 字段（`server`/`local`/`starred`）区分来源；`--recent` 与 `--starred` 均为只读视图，调用前后不会刷新本地缓存的 `visited_at`，也不会向本地访问历史新增条目。`--starred` 分页与默认视图一致（`--count` / `--offset`），不会自动拉全；`--recent` 视图下 `--cluster` 用于本地过滤、`--count` / `--offset` 用于本地分页切片，本地切片完成后会针对当前页缺失 `owners/protocol/level/service_id` 的条目并发调用 `service/info`（并发上限有界（默认 20）、单条失败 swallow），把回填字段以非破坏方式合并到内存与本地缓存（不刷新 `visited_at`）；如需完全离线渲染加 `--no-enrich`
- 输出 JSON 中顶层带 `source: "server" | "local" | "starred"`，便于 Agent 区分数据来源；`data` 顶层另带 `cluster_applied`（boolean）显式声明 cluster 过滤是否真实生效：`server` / `local` 视图为 `true`，`--starred` 视图为 `false` 并附带 `filter_note: "subscribe/list ignores cluster; returning all favorites"`，机读消费者据此判定无需依赖 `cluster` 字段反向推断。
- `method list` 和 `method get` 支持 `-c, --cluster <cluster>` 指定集群（默认 `default`），适用于 i18n 等非默认集群
- `method list` 支持 `--version <version>` 查询指定版本的方法列表；不带 `--version` 时走分页搜索接口，带 `--version` 时返回该版本全量方法
- `method get` 支持 `--endpoint-id` 或 `--psm` + `--method` 两种定位方式；RPC 方法按 PSM + 方法名定位时传 `--ep-type rpc`
- `method get --schema ref` 会保留 HTTP `query_param` / `header_param` / `body_param` 与 RPC `rpc_param` schema
- `method gencode` 支持 `--endpoint-id` 或 `--psm` + `--method` 两种定位方式，RPC 方法按 PSM + 方法名定位时传 `--ep-type rpc`；`--version` 默认为最新版本，`--lang` 默认为 `ts`，`--schema-type` 默认为 `request`，也支持生成 `response`
- `codegen rule create` 和 `codegen rule update` 已拆分；创建会传 `only_create=true`，更新必须传 `--rule-id` 并传 `only_create=false`
- `codegen rule create/update` 默认 `--generate selected`，因此通常需要先用 `bam method list` 查询方法名，再把 `endpoint.rpc_method || endpoint.name` 作为 `--methods` 传入
- `codegen rule create/update` 不内置业务默认值，`--app-id`、`--package`、`--psm`、`--name` 都需要显式提供；`--owner` 不传时使用当前 ByteCloud JWT 用户
- `codegen generate --rule-id` 若返回 `has_permission=false` 或带 `escape_params`，会自动执行 IAM 权限检查；需要自动创建权限工单时显式加 `--create-permission-ticket`，默认权限角色为 `bam.developer.cn`，必要时用 `--permission-role` 覆盖
- `codegen component build --component-repo` 接受 BAM 组件产物仓库的 Codebase URL 或 `namespace/repository`，按组件配置的 `cmpt_git_repo` 精确匹配后触发打包；IDL 来源仓库由该组件的 BAM 规则管理，不通过命令参数指定
- `--idl-branch` 指定 BAM 规则读取 IDL 的分支；`--output-branch` 指定组件产物仓库的发布分支，省略时与 `--idl-branch` 相同
- `codegen component build` 会立即触发组件打包；仅在用户明确要求并确认组件仓库、IDL 分支、产物分支后执行，否则只说明命令，不要触发
- `pipeline_id` 和 `run_seq` 从 `task_url` 尽力解析，无法解析时为 `null`；非空时可用 `bytedcli bits pipeline <pipeline_id> --run-seq <run_seq>` 查询，命令不会等待打包完成，并保留 `task_url`、`record_id`
- `idl schema` 拉取指定服务版本的全部引用 schema（struct、enum、const），支持 `--search <keyword>` 按名称过滤和 `--type enum|struct|const|string_enum` 按类型过滤
- `--schema ref|raw` 控制 schema 展示方式
- `endpoint list` 通过 HTTP path 查询其归属的 PSM/Endpoint 信息；`--path` 为必填参数，支持 `--count`、`--offset`、`--newest`、`--ep-type`、`--cluster` 等过滤条件
- `idl update` 必须提供 `--psm` 和 `--branch`，版本号通过 `--version` 指定或 `--next-version` 自动在最新版本基础上 patch +1
- `version list` 每条版本记录带 `version` / `git_branch` / `ctime` / `commit_id` 等字段（文本表格列：Version/Branch/Creator/Time/Commit）。版本号是全服务自增的：开发分支刚创建的版本号会高于 master/main 的最新版本，因此「取最新版本」必须先按 `git_branch` 过滤再取（见 Quick start 的 jq 示例），不要直接取列表第一条。`--cluster` 要与服务的 BAM 集群一致（国内服务 `default`，TikTok/海外服务通常 `i18n`；不确定时两个 cluster 都查，取版本号更新的一份）；查询 site 也要与后续消费方一致（如 api-test 调用用什么 site，查版本列表就用什么 site），不同 site 的版本视图不同
- 缺少必填参数会自动输出帮助信息
- 需要结构化输出加 `--json`（全局选项，放在子命令之前，如 `bytedcli --json bam method get ...`）

---

## 路径 B: IDL 一致性检测

### When to use

- 修改 .thrift/.proto 后快速检查
- 提交代码 / 提 MR 前全量检查
- 联调前 / 发版前验证
- 同步 BAM 远端接口

### 总体流程

```
项目探测 → 选择检查范围 → 执行检查 → 输出报告 → 辅助修复
```

| 用户意图          | 执行范围 |
| ----------------- | -------- |
| 改了 IDL 快速检查 | C1, C3   |
| 提交代码 / 提 MR  | C1 ~ C4  |
| 联调前 / 发版前   | C1 ~ C5  |
| 同步 BAM          | C5, C6   |
| 全量检查          | C1 ~ C6  |

### 检查项速览

| 编号 | 检查内容                  | 依赖                       |
| ---- | ------------------------- | -------------------------- |
| C1   | IDL ↔ 生成代码一致性      | 本地 gen 命令 + git        |
| C2   | IDL 接口 ↔ 业务代码一致性 | Agent 静态分析             |
| C3   | IDL 注解/语义检查         | Agent 静态分析             |
| C4   | Git 变更一致性            | git diff                   |
| C5   | 本地 IDL ↔ BAM 远端差异   | `bytedcli bam method list` |
| C6   | 本地 → BAM 同步           | `bytedcli bam idl update`  |

### ⚠️ 约束

- **不要** 未经确认执行 BAM 版本创建 (C6)
- **不要** 删除用户的 IDL 或业务代码
- C1 中执行生成后 **默认回滚**，让用户决定是否保留

> 完整操作指南见 `references/idl-check.md`

---

## References

- `references/metadata.md` — BAM 元数据管理命令速查
- `references/idl-check.md` — IDL 一致性检测完整操作指南
- `../../invocation.md` — 通用调用方式
- `../../troubleshooting.md` — 常见问题与处理
