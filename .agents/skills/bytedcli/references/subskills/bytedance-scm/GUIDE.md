---
name: bytedance-scm
description: "Operate SCM via bytedcli: repositories, versions, artifacts, builds, logs, failure diagnoses, and native SCM WebShell preparation, remote diagnosis, session operations, and recovery. Use for SCM repository or build work, SCM/ByteBuild URLs, WebShell preparation, prepared WebShell sessions, controlled remote verification, or WebShell lifecycle recovery."
---

# bytedcli SCM

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

- 仓库检索、创建、版本与远端产物查询、触发构建
- 拉取构建日志
- 查询 Go / Node.js 构建失败的根因与修复建议
- 从 SCM 版本或 ByteBuild source record 准备 WebShell, 并执行一次最小 `pwd` 验证
- 在用户授权范围内执行 WebShell 远端诊断、session 操作、证据读取与恢复

## 前置条件

- 使用通用调用方式：`../../invocation.md`

> 执行前缀见 `../../invocation.md`；下面示例直接写 `bytedcli`。

## Quick start

Commands are grouped under `scm repo`. Old flat names (e.g. `scm list-starred-repo`, `scm search-repo`, `scm build-repo`, `scm get-build-log`, `scm list-repo-version`) still work as hidden aliases.

```bash
# Repo list — favor (default) / all + 服务端 search / create-user / language 过滤
bytedcli scm repo list --page 1 --page-size 10                          # 我的收藏列表
bytedcli scm repo list --all                                            # 全部仓库列表
bytedcli scm repo list --all --search sort                              # 按名称搜索（all tab）
bytedcli scm repo list --create-user <username>                         # 按 creator 过滤（favor tab）
bytedcli scm repo list --all --create-user <username> --language Go     # all tab + 多过滤组合

bytedcli scm repo search "example-org/example-repo"                     # 等价 list --all --search
bytedcli scm repo create --name "example-org/example-repo"
# 创建仓库时附带 CDN 业务线绑定（创建成功后自动调用 goofy cdn bind；绑定失败抛 GOOFY_CDN_BIND_FAILED）
bytedcli scm repo create --name "example-org/example-repo" --description "demo" --git-repo "example-org/example-source" --cdn-business-line-identifier example_web_static
# 单独绑定（用于已有仓库或自动绑定失败后手动重试）；该命令属于 Goofy 域，因为后端走的是 Goofy Deploy host
bytedcli goofy cdn bind --scm-name "example-org/example-repo" --cdn-business-line-identifier example_web_static
bytedcli scm repo version list "example-org/example-repo" --branch master --type online --status build_ok
bytedcli scm repo artifact get --version-id 9876                         # 查询远端 artifact_info 元数据
# US-TTP 手动上传已有版本的静态资源，默认预览；不是上传本地文件
bytedcli --site us-ttp scm repo artifact upload-static --repo-id 123 --version 1.0.0.1
bytedcli --site us-ttp scm repo artifact upload-static --repo-id 123 --version 1.0.0.1 --yes
# 列两个构建版本之间的精确 commit 范围（比 git log --since 更准确：用 build manifest pin 的 SHA，不受 force-push / merge time 漂移影响）
bytedcli scm repo version compare --repo-id 379649 --base 2.0.4.9494 --target 2.0.4.9656
bytedcli scm repo version compare "example-org/example-repo" --base 1.0.0.1686 --target 1.0.0.1720 --first-parent
bytedcli scm repo build "example-org/example-repo" --branch master --type test -e '{"DEMO_KEY":"VALUE"}' -m "trigger build reason"
# 指定 build_steps；CLI 传值优先，未传时默认回填 SCM 仓库配置里的 build_steps
bytedcli scm repo build "example-org/example-repo" --branch master --type test --build-steps '{"pre-build":[8,1]}'
# 指定编译架构（支持 x86_64 / aarch64 / riscv64，可重复或逗号分隔）
bytedcli scm repo build "example-org/example-repo" --branch master --type test --arch riscv64
# 指定构建镜像 alias；不传时默认使用仓库配置的镜像
bytedcli scm repo build "example-org/example-repo" --branch master --type test --build-image golang-1.21
# 通过完整的 40 位 commit SHA 直接打包（--commit 和 --branch 互斥，不需要指定分支）
bytedcli scm repo build "example-org/example-repo" --commit 0123456789abcdef0123456789abcdef01234567 --type offline

# Build log — 三种入口（任选其一）
bytedcli scm repo build-log "example-org/example-repo" "1.0.0.1686" --step building
bytedcli scm repo build-log --repo-id 533180 "1.0.0.1686" --step building
bytedcli scm repo build-log --record-id 9056070 --step building          # 直接按 ByteBuild record id 取

# Build diagnosis — 查询指定仓库版本的最新构建排障结果（当前支持 Go / Node.js）
bytedcli scm repo diagnose --repo "example-org/example-repo" --version "1.0.0.1"

# SCM WebShell — 候选验证、prepare 和结构化 handoff
bytedcli --site cn --json scm webshell source get --version-id 101
bytedcli --site cn --json scm webshell prepare --repo-name "example-org/example-repo" --version "1.0.0.1" --arch x86_64

# Deployments — 按 SCM 仓库反查跨 region/平台的部署服务/任务/配置
bytedcli scm repo deployment list --repo "example-org/example-repo"                                    # 默认 cn,boe,i18n-bd,i18n-tt,us-ttp × 全平台
bytedcli scm repo deployment list --repo "example-org/example-repo" --region cn,boe --platform tce     # 指定 region + 平台
bytedcli scm repo deployment list --repo "example-org/example-repo" --platform goofy,faas --page 2     # 仅 goofy/faas，分页
```

## SCM WebShell

`bytedcli scm webshell` 负责从 SCM/ByteBuild 候选验证到 session 生命周期的完整工作流。标准准备请求会通过一个 `prepare` 调用统一验证候选并返回结构化 `next_argv`; Agent 校验 handoff 后最多自动执行一次最小 `pwd` probe。

- 遇到 SCM version URL、ByteBuild source-record URL、version ID、repository + version、prepare-only 或禁止远端执行时, 必须先读 `references/scm-webshell-prepare.md`。
- 遇到已准备 session 的额外 `execute`、`stream`、`upload`、`diff apply`, 或 session、attempt、claim、conflict、archive、audit、diagnose、recover、delete 操作时, 必须读 `references/scm-webshell-operations.md`。

自动 probe 只授权 `pwd`。任何后续远端命令、变更、清理、恢复或人工处置都受用户原始授权范围约束。Remote Verification Change 只用于临时验证; 最终修复回到本地 repository 完成、测试并提交。

## Deployments 平台与认证

`scm repo deployment list` 并行扇出到以下平台（每个 region × platform 独立执行，单点失败不影响其他单元，结果汇总返回）：

- `tce` / `cronjob` / `faas` / `goofy` / `gecko`：复用 region 对应 ByteCloud Auth JWT，走 `x-jwt-token` header
- `tao`：使用 `Authorization: Bearer <jwt>`；需要先按 region 解析 SCM 仓库数字 id
- `arnold`：仅靠 origin/referer + 浏览器风 UA，不需要 JWT

部分 region × platform 组合在公网或上游侧不可达（如 `us-ttp` 的 cronjob/faas、`i18n-*` 的 arnold/tao），结果中会显式标 `unsupported: true`，不计为错误。

## 构建模式与海外 region 同步

`scm repo build` 有两种模式，直接影响构建产物能否推到 VA / SG CDN：

- **Branch 模式**（`--branch <name>`）：`pub_base=branch_base`，SCM 走分支发布流水线，如果仓库配置开启了 `sync_aws` / `sync_oss`，就会自动跑 `uploading-va-source` / `uploading-sg-source` stage，把产物推到海外 CDN。海外业务部署的构建**必须用这个模式**。
- **Commit 模式**（`--commit <hash>`）：提交 SCM 任务前会先在 Codebase 校验 commit 存在；short SHA 会同时解析成完整的 40 位 commit SHA，查不到时禁止提交。`pub_base=commit_base`，只在国内 CDN 落地。适合一次性 hotfix 验证，不适合交付给海外环境。

区域同步开关默认继承仓库配置，可用 `--sync-aws` / `--sync-oss` / `--sync-bvc` 显式覆盖（也支持 `--no-sync-aws` 等反向开关）。

`--build-steps <json>` 也遵循相同的"CLI 覆盖优先"约定：

- 传了 `--build-steps`：直接把该 JSON 对象透传给 create version API 的 `build_steps`
- 没传：先从 SCM repo detail API 读取仓库默认 `build_steps`
- 仅接受 JSON object；空串、非法 JSON、数组等非对象值会直接报 `SCM_INPUT_ERROR`

`--build-image <alias>` 同样遵循"CLI 覆盖优先"约定：

- 传了 `--build-image`：使用指定的镜像 alias
- 没传：使用 SCM repo detail API 返回的仓库默认 `image`

```bash
# 显式只同步 SG，不同步 VA
bytedcli scm repo build "example-org/example-repo" --branch master --type test --no-sync-aws --sync-oss

# 仓库配置没开但本次想走 BVC 多 region 发布
bytedcli scm repo build "example-org/example-repo" --branch master --type test --sync-bvc
```

查看某个版本实际跑没跑海外 stage：`bytedcli scm repo build-log <repo> <version>` 里看有没有 `uploading-va-source` / `uploading-sg-source`。

构建失败时，先运行 `scm repo diagnose` 获取 Build Insight 已生成的诊断；如果返回未找到，或结果没有根因/解决方案，再结合 `scm repo build-log` 查看失败步骤日志。当前诊断服务只覆盖 Go 和 Node.js 构建。

## Notes

- 需要结构化输出加 `--json`（全局选项，放在子命令之前，如 `bytedcli --json scm repo list ...`）
- `scm repo artifact get` 查询指定 SCM 版本的远端 `artifact_info` 元数据，不下载文件
- `scm repo artifact upload-static` 对应 US-TTP 的手动“上传静态资源”功能，必须显式选择 `--site us-ttp`（或既有 `--scm-site` 覆盖）。只接受 `prepare_upload` / `upload_failed` 版本，先读取并校验版本，再预览完整请求；`--yes` 才提交。读取走 SCM 站点，上传走 Goofy US-TTP 网关，复用 ByteCloud JWT 鉴权。
- 上传结果 `submitted: true` 仅表示请求已受理，不代表 CDN 上传完成；使用输出中的 `next_command` 查询状态。默认不轮询、不重试写请求；网络失败后先查版本状态，避免重复提交。没有本地文件、CDN 业务线绑定或重新构建行为。
- 构建后的 JSON 结果里有 `pub_base` 字段，branch 模式应为 `branch_base`。若本该走海外却是 `commit_base`，先确认用的是 `--branch` 而非 `--commit`

## References

- `references/scm.md`
- `references/scm-webshell-prepare.md`
- `references/scm-webshell-operations.md`
