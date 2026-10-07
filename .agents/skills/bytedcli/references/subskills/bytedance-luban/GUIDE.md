---
name: bytedance-luban
description: "Operate Luban package workflows via bytedcli. Use for OHPM/Harmony package searches, artifact details and verified HAR downloads, Bytedance or TTP npm package lookup, Luban NPM repository/source/version-task queries and guarded publishing, Maven package resolution/publishing, PyPI repository/version publishing, and BPT repository/version operations and ByteBuild logs."
---

# bytedcli Luban

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

- 需要确认某个 Bytedance 或 TTP npm 包是否已进入 Luban 组件库
- 需要在默认 Bytedance Luban 与 TTP Luban 两个环境之间切换查询
- 需要按版本前缀筛某个 bnpm 包的记录
- 需要把 `@scope/name` 形式的包名映射成 Luban 查询里的 `group` 和 `name`
- 需要查询 Luban NPM 仓库、分支、commit、tag 或版本任务，或基于固定 commit 创建并跟踪 NPM 发布任务
- 需要根据 Maven 包的 group/artifact/version 反查其对应的 git 仓库地址与 commit
- 需要按 Maven 仓库名、分支和版本号预览或发起 Luban Maven 发布
- 需要按 pip 包名或 git 仓库名搜索 Luban PyPI 制品仓库，查询版本列表/详情，或创建 PyPI 版本发布任务
- 需要查询 Luban BPT 仓库、分支、commit、版本，获取失败版本 ByteBuild 日志，或预览/发起 BPT 版本发布任务

## Prerequisites

- `luban ohpm` 需要先完成 `bytedcli auth login`，仅支持 CN；查询复用 ByteCloud JWT，访问 OHPM 专用源服务，HAR 下载不携带凭据。
- `luban search`、`luban npm` 与 `luban pypi` 需要先完成 `bytedcli auth login`
- 默认 Luban 查询会复用 ByteCloud 凭据，并从 `https://cloud.bytedance.net` 获取 JWT
- 传入 `--site us-ttp` 时，会改为查询 TTP Luban，并从 `https://cloud-ttp-us.bytedance.net` 获取 TTP JWT
- `luban pypi` 走 Luban 发布页使用的 SCM API，并返回 Luban 版本页 URL
- `luban npm` 走同一套 Luban SCM API；发布任务会出现在 NPM Portal 版本列表，并分别跟踪 CN / OCI 状态
- `luban maven get` 只读取 `maven.byted.org` 上的公开 pom 与 `maven-metadata.xml`，不需要 `auth login`，也不依赖 ByteCloud JWT
- `luban bpt` 走 Luban SCM API，需要先完成 `bytedcli auth login`

## Quick start

```bash
# 查询 OHPM 制品、查看详情并下载指定 HAR（CN）
bytedcli --json luban ohpm search --package @demo/sdk --version-prefix 1.2 --page-size 20
bytedcli --json luban ohpm get --id 12345
bytedcli luban ohpm download --asset-id 23456 --output ./demo-sdk.har

# 查询某个包的全部结果
bytedcli luban search --npm @demo/uploader

# 查询某个包的指定版本前缀
bytedcli luban search --npm @demo/uploader -v 2.1.5

# 查询 NPM 发布仓库、分支和版本任务
bytedcli --json luban npm repo search --name demo-package
bytedcli --json luban npm branch list --repo-id 12345
bytedcli --json luban npm version list --repo-id 12345

# NPM 发布先 dry-run；省略 --task-version 时使用 Luban 推荐值
bytedcli --json luban npm version publish \
  --repo-id 12345 \
  --desc "demo release" \
  --branch demo-main \
  --dry-run

# 明确确认后固定 dry-run 得到的 commit，再创建并等待 CN / OCI 终态
bytedcli --json luban npm version publish \
  --repo-id 12345 \
  --desc "demo release" \
  --branch demo-main \
  --commit sample-commit-hash \
  --yes

# 查询 TTP Luban 环境
bytedcli luban search --npm @demo/uploader --site us-ttp

# 使用长参数写法
bytedcli luban search --npm @demo/uploader --package-version 2.1.5

# 根据 Maven 坐标反查 git 仓库地址与 commit
bytedcli luban maven get -g com.example.demo -a demo-sdk --version 1.0.0

# Snapshot 版本：自动读取 maven-metadata.xml 定位带时间戳的实际构建；已知仓库时可用 --repository 直达
bytedcli luban maven get -g com.example.demo -a demo-sdk --version 1.0.0-SNAPSHOT
bytedcli luban maven get -g com.example.demo -a demo-sdk --version 1.0.0-SNAPSHOT --repository android_public

# Maven 发布先 dry-run；真实写操作必须显式确认
bytedcli luban maven publish --repository demo-sdk --branch master --version 1.2.3 --dry-run
bytedcli luban maven publish --repository demo-sdk --branch master --version 1.2.3 --commit abc123 --yes

# 需要机器可读结果时，优先加 --json
bytedcli --json luban search --npm @demo/uploader --package-version 2.1.5
bytedcli --json luban maven get -g com.example.demo -a demo-sdk --version 1.0.0

# 查询 PyPI 制品仓库和版本
bytedcli --json luban pypi repo search --name demo-package --page 1 --page-size 10
bytedcli --json luban pypi repo get --repo-id 12345
bytedcli --json luban pypi version list --repo-id 12345 --page 1 --page-size 20
bytedcli --json luban pypi version get --version-id 67890

# PyPI 发布 dry-run；会先检查同版本是否已有成功发布
bytedcli --json luban pypi version publish \
  --repo-id 12345 \
  --version 1.2.3 \
  --desc "demo release" \
  --branch master \
  --dry-run

# 基于指定 commit 发布，真实写操作必须显式确认
bytedcli --json luban pypi version publish \
  --repo-id 12345 \
  --version 1.2.3 \
  --desc "demo release" \
  --pub-base commit \
  --commit abcdef123 \
  --yes

# 查询 BPT 制品仓库
bytedcli luban bpt repo list --keyword sample-package --page 1 --page-size 20

# BPT 发布 dry-run；会先检查同版本是否已有成功发布
bytedcli luban bpt version publish \
  --repo-id 12345 \
  --version 1.0.0 \
  --desc "demo release" \
  --branch demo-main \
  --dry-run

# 用户明确确认后追加 --yes；默认创建任务后立即返回
bytedcli --json luban bpt version publish \
  --repo-id 12345 \
  --version 1.0.0 \
  --branch demo-main \
  --commit sample-commit-hash \
  --yes

# 仅在需要当前命令等待全部版本终态时追加 --wait
bytedcli --json luban bpt version publish \
  --repo-id 12345 \
  --version 1.0.0 \
  --branch demo-main \
  --commit sample-commit-hash \
  --yes \
  --wait

# 查询失败 BPT version 对应的 ByteBuild 日志；默认拉 failed step
bytedcli luban bpt version log --version-id 67890
bytedcli --json luban bpt version log --version-id 67890 --status failed
```

## Agent Guidance

- OHPM 查询使用 `luban ohpm`，NPM 查询使用 `luban search --npm`；两者源服务不同，不能用 NPM 空结果判断 OHPM 包不存在。
- OHPM 搜索提供 `--page`（默认 1）和 `--page-size`（默认 20）；当前仅接受已验证的 `--page-size 20`，其他值在请求前报错，已观察到 `page_size: 200` 返回 HTTP 500。JSON 的 `has_more` 为 true 时递增 `--page`，不要把第一页当作全部版本。`--version-prefix` 是前缀筛选，下载前从结果确认精确版本及 asset ID。
- OHPM 搜索和详情会展示禁用制品，下载仅接受未禁用的 HAR。列表包含表头和元数据，不预览包内文件；完整 HAR 使用 `luban ohpm download --asset-id <id> --output <file>` 获取。
- OHPM 下载要求新文件路径，验证大小和服务端返回的校验值后才写入目标文件。缺校验值、重定向、大小或哈希不匹配均报错；不自动安装或解包。JSON 下载结果包含 `outputPath`、`bytes`、`sha256`、`verifiedChecksums`。
- OHPM 仅支持 CN；其他站点请明确改用 `bytedcli --site cn luban ohpm ...`。完整参数和输出见 [Luban reference](references/luban.md)。
- NPM 的真实发布是写操作。Agent 必须在当前一轮先执行同参数 `--dry-run` 并展示最终 payload；只有用户明确确认后，才能复用 dry-run 的 `base_commit_hash` 并追加 `--yes`。历史授权、只要求查看或成功的 dry-run 都不是发布授权。
- `--task-version` 是 Luban 发布任务版本，不是 npm 包版本，也不是 npm dist-tag 或 Git tag。通常省略它，让 Luban 返回推荐 task version；包版本由仓库源码与发布命令决定。
- NPM 发布默认复用仓库的 install/build/CN publish/non-CN publish 配置，并按仓库配置选择 CN / OCI。只有用户明确要求临时覆盖时才传 command/region flags。
- 默认等待全部配置地域终态；只有 CN 和 OCI（若启用）都成功，才能报告整体成功。`--no-wait` 仅表示任务已创建，不能报告包已发布。
- `--has-version-stage` / `--publish-version` 可能修改源码版本元数据或创建 Git tag，取决于仓库配置；除非用户明确要求版本阶段，否则不要启用。
- BPT 的真实发布是写操作。Agent 必须在**当前一轮**获得用户对本次发布的明确授权；历史授权、文档示例和用户仅要求查看发布参数，都不能视为授权。
- 发起 BPT 真实发布前，先运行同参数的 `--dry-run`，向用户展示最终 payload，然后暂停等待确认。只有收到明确确认后，才在同一参数集上追加 `--yes`；不得自行推断或预先附加 `--yes`。若 dry-run 自动解析了分支的 commit，真实发布时还应显式复用 payload 中的 commit，避免授权后引用漂移。
- BPT 的 `--pub-base` 只支持 `branch` / `commit`。branch 模式未传 `--commit` 时会解析指定分支的最新 commit；commit 模式必须显式传 `--commit`。
- BPT 的 `--channel` 是可选参数，只在用户明确指定时传入，且会原样传给 Luban；包含 shell 特殊字符时使用单引号。
- BPT 的 `--version` 是调用方指定的制品版本号，CLI 不会自动生成。
- BPT 发布请求里的 `create_user` 固定使用当前 SSO 用户，不接受身份覆盖参数。
- BPT 发布默认在任务创建后立即返回。Agent 必须读取 JSON 结果的 `response.version_ids`，对每个 ID 运行 `bytedcli --json luban bpt version get --version-id <id>` 并跟踪到终态；只有全部成功才能报告整次发布成功，任一失败则报告失败。
- BPT version 失败时，优先用 `bytedcli luban bpt version log --version-id <id>` 读取对应 ByteBuild failed step 日志；需要指定步骤时传 `--step <step>`，跨站点 build_url 解析不准时传 `--scm-site <site>`。
- 只有用户明确要求当前命令等待终态时才追加 `--wait`。轮询参数、状态判断与边界见 [references/luban.md](references/luban.md)。

## Notes

- `--npm` 需要传 `@scope/name` 形式的 npm 包名。
- `-v, --package-version` 为可选参数；传入时会映射为 Luban 请求体里的 `version_prefix`，不传时会搜索该包名的所有结果。
- `--site us-ttp` 为可选参数；传入时切换到 TTP Luban API、JWT host 与 Web origin，不传时走默认 Bytedance Luban 环境。
- `luban npm` 使用资源化命令树：`repo search/get`、`branch list`、`commit list`、`tag search`、`version list/get/publish`。旧的 `luban search` 继续用于按 `@scope/name` 查询组件库记录，两者语义不同且都保留。
- `luban npm version publish` 的 branch 模式在未传 `--commit` 时解析分支最新 commit；真实发布必须显式复用 dry-run 的 commit。commit 模式要求 `--commit`，tag 模式要求 `--tag`，并可用显式 `--commit` 固定 tag 指向。
- NPM task 默认等待所有配置地域；`--no-wait` 仅返回任务 ID 和 Portal URL。`version get` 会同时返回 CN / OCI 原始状态与 `aggregate_status`。
- `luban maven get` 需要同时传 `-g/--group`、`-a/--artifact`、`--version`，可选 `--repository <name>`。默认按 `releases → snapshots → android_public → public` 顺序探测 `maven.byted.org` 的制品仓库（`-SNAPSHOT` 版本先探 `snapshots`），命中即停，结果 `repository` 字段给出实际提供 pom 的仓库；`--repository` 只查指定的制品仓库，注意它不是 `luban maven publish --repository` 的 Luban 发布仓库名。
- `-SNAPSHOT` 版本（只认大写后缀）会通过版本目录的 `maven-metadata.xml` 自动定位带时间戳的实际构建，`resolvedVersion` 返回实际构建、`version` 保持输入原值；溯源优先取 `<scm>`，缺失时回退到部分 SDK 写在 `<description>` 里的 JSON，并额外返回 `module` / `moduleCommit`。仓库聚合关系、元数据解析与字段映射细则见 [references/luban.md](references/luban.md) 的 Maven coordinate lookup。
- 错误区分：所有候选仓库都没有该制品时报 `LUBAN_MAVEN_ARTIFACT_NOT_FOUND`（`details.probed` 列出尝试过的 URL）；坐标含非法字符或 `--repository` 指向不存在的仓库时报 `LUBAN_INPUT_ERROR`；只命中了指向缺失 pom 的 `maven-metadata.xml` 时报 `LUBAN_MAVEN_API_ERROR`；pom 存在但没有任何溯源字段时仍按成功返回，`gitRepo` / `commit` 为 `null`（文本模式显示 `N/A` 并附一行说明）。`maven.byted.org` 异常（5xx、网络故障、响应超限等）同样报错而非误报成功。
- `luban maven publish` 需要 `--repository`、`--branch`、`--version`。命令按精确仓库名解析 repo id，读取分支最新 commit，并复用 Luban 仓库已有的 Module、JDK、构建工具和区域配置。真实发布必须传 `--yes`；必须先在当前轮执行 `--dry-run` 检查最终请求，再把预览中的 Commit 通过 `--commit` 原样传给真实发布，避免分支引用漂移。
- Maven Version 创建成功后会 best-effort 同步 Luban Meta 组件。同步失败不会把已创建的 Version 误报为发布失败；JSON 结果会保留发布 `response`，并返回 `sync_response: null` 与结构化 `sync_error`，需要单独重试或排查组件同步。
- `luban pypi repo search` 至少传 `--name` 或 `--git-name` 之一；`--name` 按 pip 包名过滤，`--git-name` 按 git 仓库名过滤，默认 `--create-date-order desc`、`--page 1 --page-size 10`。
- 文本模式输出紧凑表格；`--json` 模式返回命令特定的结构化结果（`luban search` 返回包列表，`luban maven get` 返回 `{ group, artifact, version, repository, snapshot, resolvedVersion, pomUrl, gitRepo, commit, module, moduleCommit }`，`luban pypi *` 返回对应资源对象）。
- `luban pypi version publish` 默认等待并轮询发布状态；`--no-wait` 只创建任务并返回。
- `--dry-run` 与真实发布都会先检查同版本成功记录；命中时返回 `LUBAN_PYPI_VERSION_EXISTS`，不会继续创建发布任务。
- `--pub-base` 支持 `branch` / `commit` / `tag`；commit 模式必须传 `--commit`，tag 模式必须传 `--tag`。
- 轮询时会在 stderr 打印 URL 与进度动画，不影响 `--json` stdout 的最终 JSON。
- `luban bpt version publish --pub-base` 支持 `branch` / `commit`；commit 模式必须传 `--commit`。
- `luban bpt version log` 会读取 BPT version detail 的 `build_url`，从 `/bytebuild/log/<record_id>` 推导 ByteBuild record id，并复用 SCM ByteBuild 日志接口；默认 `--status failed`。

## References（按需加载）

- 命令参数、BPT / PyPI 发布流程、轮询边界和输出字段：[references/luban.md](references/luban.md)
- 安装、全局参数、站点切换与 JSON 输出约定：[../../invocation.md](../../invocation.md)
- 认证、版本和常见报错排查：[../../troubleshooting.md](../../troubleshooting.md)
