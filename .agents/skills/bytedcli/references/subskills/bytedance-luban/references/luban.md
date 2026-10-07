# Luban

## Command map

- `bytedcli luban ohpm search`
  - `--package <name>`：必填，`@demo/sdk` 或 `demo-sdk`；`--version-prefix <prefix>`：可选版本前缀
  - `--repository <name>`：可选，默认内置 OHPM 仓库；`--page <n>` / `--page-size <n>`：默认 1 / 20；当前仅接受已验证的 `--page-size 20`，其他值在请求前报错
  - JSON 返回 `items`、`total`、`page`、`page_size`、`has_more`；`items[].assets` 包含 asset ID、大小和校验值
- `bytedcli luban ohpm get`
  - `--id <id>`：必填，搜索结果中的 component ID，返回组件元数据和资源列表
- `bytedcli luban ohpm download`
  - `--asset-id <id>` / `--output <file>`：必填，下载指定 HAR 到新文件，不覆盖现有文件、不解包
  - 返回 `outputPath`、`bytes`、`sha256`、`verifiedChecksums` 和制品标识；核对大小及服务端提供的全部校验值，失败时清理临时文件
- `bytedcli luban search`
  - `--npm <packageName>`：必填，传 `@scope/name` 形式的 npm 包名
  - `-v, --package-version <version>`：可选，按版本前缀过滤；不传时搜索该包名的所有结果
  - `--site us-ttp`：可选，切换到 TTP Luban 环境；不传时走默认 Bytedance Luban 环境
- `bytedcli luban npm repo search`
  - `--name <name>` / `--git-name <name>`：至少传一个，按包/仓库名或 git 仓库名搜索
  - `--favor`：可选，只看收藏仓库
  - `--create-date-order asc|desc`：默认 `desc`
  - `--page <n>` / `--page-size <n>`：默认 `1` / `10`
- `bytedcli luban npm repo get`
  - `--repo-id <id>`：必填，NPM 发布仓库 ID
- `bytedcli luban npm branch list`
  - `--repo-id <id>`：必填
- `bytedcli luban npm commit list`
  - `--repo-id <id>`：必填；`--branch <branch>` 可选
- `bytedcli luban npm tag search`
  - `--repo-id <id>` / `--keyword <prefix>`：必填
- `bytedcli luban npm version list`
  - `--repo-id <id>`：必填
  - `--task-version <version>`：按 Luban task version 过滤
  - `--branch` / `--status` / `--type` / `--create-user`：可选过滤条件
  - `--page <n>` / `--page-size <n>`：默认 `1` / `20`
- `bytedcli luban npm version get`
  - `--version-id <id>`：必填
- `bytedcli luban npm version publish`
  - `--repo-id <id>` / `--desc <desc>`：必填
  - `--task-version <version>`：可选；省略时使用 Luban 推荐 task version
  - `--pub-base branch|commit|tag`：默认 `branch`
  - `--branch` / `--commit` / `--tag`：选择并固定源码引用
  - `--region cn|oci|cn,oci`：可选，默认根据仓库配置决定
  - `--dry-run`：解析仓库配置、task version 和 commit，输出完整请求但不创建任务
  - `--yes`：确认创建真实任务
  - `--no-wait`：创建后立即返回；默认等待全部配置地域终态
- `bytedcli luban maven get`
  - `-g, --group <groupId>`：必填，Maven group id，例如 `com.example.demo`
  - `-a, --artifact <artifactId>`：必填，Maven artifact id，例如 `demo-sdk`
  - `--version <version>`：必填，Maven 版本，例如 `1.0.0` 或 `1.0.0-SNAPSHOT`（Snapshot 会通过 `maven-metadata.xml` 解析实际构建）
  - `--repository <name>`：可选，只查指定的 `maven.byted.org` 制品仓库；默认按 `releases → snapshots → android_public → public` 探测（`-SNAPSHOT` 版本先探测 `snapshots`）。它不是下面 `maven publish --repository` 的 Luban 发布仓库名
- `bytedcli luban maven publish`
  - `--repository <name>`：必填，Luban Maven 仓库精确名称
  - `--branch <branch>`：必填，待发布分支
  - `--version <version>`：必填，目标版本号
  - `--commit <hash>`：可选固定 commit；真实发布应复用当前轮 dry-run 预览的 Commit
  - `--dry-run`：解析仓库、commit 与发布配置并预览请求
  - `--yes`：确认并创建真实发布任务
  - Version 创建成功后的 Luban Meta 组件同步为 best-effort；同步失败时命令仍返回发布成功结果，并在 JSON 中提供 `sync_error`
- `bytedcli luban pypi repo search`
  - `--name <name>` / `--git-name <name>`：至少传一个，按 pip 包名或 git 仓库名搜索 PyPI 制品仓库
  - `--favor`：可选，只看收藏仓库
  - `--create-date-order asc|desc`：可选，创建时间排序方向，默认 `desc`
  - `--page <n>` / `--page-size <n>`：分页参数，默认 `1` / `10`
- `bytedcli luban pypi repo get`
  - `--repo-id <id>`：必填，PyPI 制品仓库 ID
- `bytedcli luban pypi version list`
  - `--repo-id <id>`：必填，PyPI 制品仓库 ID
  - `--keyword <version>`：可选，按版本号关键字过滤
  - `--branch <branch>` / `--status <status>` / `--type <type>` / `--create-user <user>`：可选过滤条件
- `bytedcli luban pypi version get`
  - `--version-id <id>`：必填，PyPI 版本 ID
- `bytedcli luban pypi version publish`
  - `--repo-id <id>` / `--version <version>` / `--desc <desc>`：必填
  - `--pub-base branch|commit|tag`：默认 `branch`
  - `--branch <branch>`：分支发布，默认 `master`
  - `--commit <hash>`：commit 发布必填；分支或 tag 发布时可显式覆盖 commit
  - `--tag <tag>`：tag 发布必填
  - `--dry-run`：只解析并输出最终请求体，不创建版本
  - `--yes`：确认真实发布
  - `--no-wait`：创建发布任务后立即返回，不轮询最终状态
- `bytedcli luban bpt repo list`
  - `--keyword <text>`：可选，按仓库名搜索
  - `--page <n>` / `--page-size <n>`：分页参数，默认 `1` / `20`
- `bytedcli luban bpt repo get`
  - `--repo-id <id>`：必填，BPT 仓库 ID
- `bytedcli luban bpt branch list`
  - `--repo-id <id>`：必填，BPT 仓库 ID
- `bytedcli luban bpt commit list`
  - `--repo-id <id>`：必填，BPT 仓库 ID
  - `--branch <branch>`：可选，按分支名过滤
- `bytedcli luban bpt version list`
  - `--repo-id <id>`：必填，BPT 仓库 ID
  - `--page <n>` / `--page-size <n>`：分页，默认 `1` / `20`
  - `--version <version>` / `--branch <branch>` / `--status <status>` / `--type <type>` / `--arch <arch>` / `--create-user <user>`：可选过滤条件
- `bytedcli luban bpt version get`
  - `--version-id <id>`：必填，BPT 版本 ID
- `bytedcli luban bpt version log`
  - `--version-id <id>`：必填，BPT 版本 ID
  - `--step <step>`：可选，指定 ByteBuild step；传入后不再默认按失败状态过滤
  - `--status <status>`：可选，按 step 状态过滤，默认 `failed`
  - `--scm-site <site>`：可选，覆盖从 `build_url` 推断出的 SCM / ByteBuild 站点
- `bytedcli luban bpt version publish`
  - `--repo-id <id>`：必填，BPT 仓库 ID
  - `--version <version>`：可选兼容参数；正常 BPT 发版应省略，让 Luban Version 字段保持为空
  - `--desc <desc>`：可选，发布说明；默认使用 `BPT publish`
  - `--pub-base branch|commit`：默认 `branch`
  - `--branch <branch>`：分支发布，默认 `master`
  - `--commit <hash>`：commit 发布必填
  - `--type <type>`：版本类型，默认 `online`
  - `--arch <arch>`：架构列表，逗号分隔或 JSON 数组，默认 `x86_64`
  - `--build-images <images>`：构建镜像别名列表，逗号分隔或 JSON 数组
  - `--region <region>`：地域列表，逗号分隔或 JSON 数组
  - `--deps <name:branch>`：依赖名称与分支；多个依赖重复传入 `--deps`
  - `--dry-run`：只解析并输出最终请求体，不创建版本
  - `--yes`：确认真实发布
  - `--wait`：轮询接口返回的全部 version ID，直到全部进入终态
  - `--poll-interval-ms <ms>`：`--wait` 的轮询间隔，默认 `5000`，范围 `1000..3600000`
  - `--wait-timeout-ms <ms>`：`--wait` 的最大等待时间，默认 `600000`，范围 `1000..3600000`

## Inputs

### NPM package name

`--npm` 需要传完整包名，例如 `@demo/uploader`。CLI 会自动把：

- `scope` 映射为请求体里的 `group`
- `name` 映射为请求体里的 `name`

### Version prefix

`--package-version` 为可选参数。传入时会映射为请求体里的 `version_prefix`，适合按 `2.1.5`、`2.1` 这类前缀过滤；不传时返回该包名的全部匹配结果。

### NPM repository and version tasks

`luban npm` 管理 Portal 中的 NPM 发布仓库和 version task。`repo`、`branch`、`commit`、`tag` 是发布前的只读发现能力，`version list/get` 返回任务以及独立的 CN / OCI 状态。

`--task-version` 只代表 Luban task version，不代表源码 `package.json` 中的包版本、npm dist-tag 或 Git tag。发布时通常省略，让 Luban 的 recommendation 接口生成下一 task version。NPM 包版本仍由固定 commit 中的包清单和仓库发布命令决定。

真实发布必须先 dry-run，再把预览中的 `base_commit_hash` 通过 `--commit` 固定到确认后的请求。命令默认复用仓库 install/build/CN publish/non-CN publish 配置；默认等待所有配置地域，任一地域失败则整体失败。`--no-wait` 只证明任务创建成功，不能证明包已经进入 registry。

`--has-version-stage` / `--publish-version` 可能触发源码版本修改或 Git tag 行为，具体取决于仓库配置；普通发布不要默认启用。

### Environment

默认会请求 Bytedance Luban API，并从 `https://cloud.bytedance.net` 获取 JWT。传入 `--site us-ttp` 时，会切换到 TTP Luban API，并从 `https://cloud-ttp-us.bytedance.net` 获取 JWT；请求头里的 `origin` / `referer` 也会同步切换到 TTP Luban Web 域名。

### Maven coordinate lookup

`luban maven get` 用于根据 Maven 坐标反查制品对应的 git 仓库与 commit。它只读取 `maven.byted.org` 上的公开 pom 与 `maven-metadata.xml`（无需 `auth login`）。

- 仓库定位：默认按 `releases → snapshots → android_public → public` 顺序探测制品仓库（`-SNAPSHOT` 版本先探测 `snapshots`），命中即停，结果 `repository` 字段给出实际提供 pom 的仓库；`--repository <name>` 可跳过探测只查一个制品仓库（不是 `maven publish --repository` 的 Luban 发布仓库名）。`releases`/`snapshots` 是托管仓；`android_public` 聚合 `releases` 与 Android SDK 自托管制品（Snapshot 也在这里）；`public` 聚合 `releases` 与 `snapshots`，不含 Android 自托管制品。默认列表里某个仓库暂时不存在时会跳过并记录在 `details.unknown_repositories`。
- 坐标校验：`group` 的每个点分段、`artifact`、`version`、`repository` 都只允许字母、数字与 `. _ + -`（`repository` 不含 `+`），且不能为空或以 `.`/`-` 开头，因此 `..`、`/`、`?`、`#` 之类无法改写请求路径，结果里的 `pomUrl` 就是实际请求过的 URL；不合法时报 `LUBAN_INPUT_ERROR` 并给出示例命令。
- Snapshot 解析：`-SNAPSHOT` 版本（按 Maven 语义只认大写后缀）的实际文件名带时间戳与构建号（如 `demo-sdk-1.0.0-20240102.030405-7.pom`）。命令先读版本目录下的 `maven-metadata.xml`，取 `snapshotVersions` 中 `extension=pom` 且无 `classifier` 的 `value`，缺失时回退到 `snapshot.timestamp`/`buildNumber` 拼接，再下载对应 pom；`resolvedVersion` 返回实际构建，`version` 保持输入原值。没有元数据、或元数据未列出带时间戳构建（非唯一快照，常见形态只有 `buildNumber`/`localCopy`，或 `value` 就是 `-SNAPSHOT` 版本本身）时，回退到文件名直接带 `-SNAPSHOT` 的 pom。某个仓库的元数据指向的 pom 缺失时不会中断，继续探测后续仓库。
- 溯源解析：优先取 `project.scm.url`（自动剥离 `scm:<provider>:` 前缀）与 `project.scm.tag`（Maven 默认占位值 `HEAD` 视为缺失）；缺失时逐字段回退到 `project.description` 中的 JSON `{"sha1","module_sha1","git","project"}`（`git → gitRepo`、`sha1 → commit`、`project → module`、`module_sha1 → moduleCommit`；支持 XML 命名/数字实体与 CDATA，每个实体只解一层）。`module`/`moduleCommit` 只来自该 JSON。
- 错误区分：所有候选仓库都没有该制品时以 `LUBAN_MAVEN_ARTIFACT_NOT_FOUND` 报错，`details.probed` 列出尝试过的 URL，`hint` 按是否 pin 了仓库分别建议核对坐标 / 去掉 `--repository`（版本以小写 `-snapshot` 结尾时会额外提示改用大写）；`--repository` 指向不存在的仓库（上游返回 `repository named <x> not found`）时报 `LUBAN_INPUT_ERROR` 并列出默认仓库；探测完所有仓库只命中了指向缺失 pom 的 `maven-metadata.xml` 时报 `LUBAN_MAVEN_API_ERROR`，`details.inconsistencies` 列出各仓库的 `metadata_url` / `pom_url` / `resolved_version`；pom 存在但没有任何溯源字段时仍按成功返回，`gitRepo`/`commit` 为 `null`（文本模式显示 `N/A` 并附一行说明）。`maven.byted.org` 异常（5xx、网络故障、单个响应超过 4 MiB 上限等）时命令报错而非误报成功。

### PyPI artifact publish

`luban pypi` 用于 Luban PyPI 制品仓库搜索、详情查询、版本发布任务管理。查询和发布会复用 ByteCloud JWT，访问 Luban 发布页对应的 SCM API；发布成功创建后会返回 Luban 版本页 URL。

`luban pypi repo search` 至少传 `--name` 或 `--git-name` 之一。按 pip 包名查仓库时用 `--name`，例如：

```bash
bytedcli --json luban pypi repo search --name demo-package --page 1 --page-size 10
```

发布命令默认是等待模式：创建发布任务后轮询版本详情直到成功或失败，stderr 会打印 URL 和轮询进度，stdout 在 `--json` 模式下保持单个最终 JSON。传 `--no-wait` 时只返回创建结果。

发布前会先查询已有版本。如果同一版本号已经存在成功发布记录，命令返回 `LUBAN_PYPI_VERSION_EXISTS`，不会创建新任务。真实发布需要 `--yes`；建议先用 `--dry-run` 检查最终请求体。

### BPT artifact operations

`luban bpt` 用于 BPT 制品的仓库查询、版本列表/详情查询和版本发布。查询和发布会复用 ByteCloud JWT，走 Luban SCM API。

仓库、分支和提交按资源分组，常用查询链路为 `repo list/get` → `branch list` → `commit list`：

```bash
bytedcli --json luban bpt repo list --keyword sample-package --page 1 --page-size 20
bytedcli --json luban bpt repo get --repo-id 12345
bytedcli --json luban bpt branch list --repo-id 12345
bytedcli --json luban bpt commit list --repo-id 12345 --branch demo-main
```

`luban bpt version list` 支持丰富的过滤条件，例如：

```bash
# 按状态和架构过滤
bytedcli luban bpt version list --repo-id 12345 --status build_ok --arch x86_64

# 按分支和版本号过滤
bytedcli luban bpt version list --repo-id 12345 --branch demo-main --version 1.2.3
```

发布命令默认在任务创建后立即返回，不持续占用当前进程。JSON 结果的 `response.version_ids` 包含本次创建的全部版本 ID；Agent 应逐个查询并跟踪到终态：

```bash
bytedcli --json luban bpt version get --version-id 67890
bytedcli --json luban bpt version get --version-id 67891
```

按 `version get` 返回的 `status` / `status_display` 判断状态：`build_ok`、`success`、`succeeded`、`completed` 或成功文案视为成功；包含 `fail`、`cancel`、`error`，以及 `discard` 或失败/取消文案视为失败；其他状态继续查询。只有全部版本都成功时才能报告整次发布成功；任一版本失败则报告失败。需要由当前命令完成轮询时显式传 `--wait`：默认每 `5000ms` 查询一次、最多等待 `600000ms`，`--poll-interval-ms` 与 `--wait-timeout-ms` 均限制在 `1000..3600000`。轮询 URL 和进度写入 stderr，`--json` 的 stdout 仍只包含最终 JSON。

失败版本的 ByteBuild 日志用 `version log` 获取。命令会先读取 BPT version detail 的 `build_url`，从 `/bytebuild/log/<record_id>` 推导 ByteBuild record id，再复用 SCM ByteBuild 日志接口。默认拉 failed step；需要指定步骤或站点时加 `--step` / `--scm-site`：

```bash
bytedcli luban bpt version log --version-id 67890
bytedcli --json luban bpt version log --version-id 67890 --status failed
bytedcli luban bpt version log --version-id 67890 --step bpt-build
```

正常 BPT 发版不要传 `--version`，请求体会省略 `version`，Luban 详情页的 Version 字段为空是预期行为。只有显式传 `--version` 时才会先查询已有版本；如果同一版本号已经存在成功发布记录，命令返回 `LUBAN_BPT_VERSION_EXISTS`，不会创建新任务。真实发布必须在当前一轮获得用户明确授权：先用相同业务参数执行 `--dry-run` 并展示最终 payload，确认后才能追加 `--yes`；若 dry-run 自动解析了 commit，真实发布时显式复用该 commit，避免引用漂移。请求里的 `create_user` 固定取当前 SSO 用户，不能通过 CLI 覆盖。

`--arch`、`--build-images`、`--region` 支持逗号分隔值或 JSON 数组形式。`--channel` 是可选参数，只在明确指定时原样传给 Luban；包含 shell 特殊字符时使用单引号。`--deps` 使用 `name:branch` 格式；多个依赖重复传入该 option，不使用逗号聚合。省略 `--deps` 时请求会发送空依赖列表。多个依赖的示例：

```bash
bytedcli luban bpt version publish \
  --repo-id 12345 \
  --desc "demo release" \
  --branch demo-main \
  --arch "x86_64,aarch64" \
  --build-images "sample-image" \
  --region "sample-region-a,sample-region-b" \
  --deps sample-lib:sample-branch \
  --deps demo-lib:demo-branch \
  --dry-run
```

## Output

- `luban search`：文本模式输出包名、版本、仓库和创建时间的表格；JSON 模式返回包列表数组
- `luban npm repo search/get`：返回规范化仓库配置；搜索结果包含 `total/page/page_size/has_more`
- `luban npm branch/commit/tag`：返回源码引用列表和 `current_count`
- `luban npm version list/get`：返回 `task_version`、CN / OCI 原始状态、`aggregate_status`、源码引用、任务 ID 和地域信息
- `luban npm version publish`：dry-run 返回 `method/endpoint/request/url`；真实发布还返回 `version_ids`、`final_status`、`final_versions` 和 `poll_attempts`
- `luban maven get`：文本模式输出 Group ID / Artifact ID / Version / Repository / Git Repo / Commit 的 KV 表格，末行恒为 POM URL；`-SNAPSHOT` 解析到不同实际构建时在 Repository 之后插入 Resolved Version 行，`<description>` JSON 形态的 pom 在 Commit 之后追加 Module / Module Commit 行；四个溯源字段全为空时表格下方多一行说明。JSON 模式返回 `{ group, artifact, version, repository, snapshot, resolvedVersion, pomUrl, gitRepo, commit, module, moduleCommit }`，字段恒存在，无值为 `null`
- `luban pypi repo search`：文本模式输出仓库 ID、包名、git 仓库、默认分支、创建人和创建时间；JSON 模式返回搜索响应对象
- `luban pypi *`：文本模式输出对应资源摘要表格；JSON 模式返回资源对象
- `luban bpt repo list`：文本模式输出仓库 ID、名称、仓库地址、默认分支、镜像和创建人表格；JSON 模式返回 `{ repos, total, current_count, page, page_size, has_more }`，后端未返回总数时 `total` 为 `null`
- `luban bpt repo get`：文本模式输出仓库详情 KV 表格；JSON 模式返回仓库对象
- `luban bpt branch list`：文本模式输出分支名列表表格；JSON 模式返回 `{ branches, current_count }`
- `luban bpt commit list`：文本模式输出 commit hash 和 message 表格；JSON 模式返回 `{ commits, current_count }`
- `luban bpt version list`：文本模式输出版本 ID、版本号、状态、类型、分支、架构、commit 和创建时间表格；JSON 模式返回 `{ versions, total, current_count, page, page_size, has_more }`，后端未返回总数时 `total` 为 `null`
- `luban bpt version get`：文本模式输出版本详情 KV 表格；JSON 模式返回版本对象
- `luban bpt version log`：文本模式输出 ByteBuild record id、过滤条件和日志正文；JSON 模式返回 `{ version, version_id, build_num, build_url, inferred_scm_site, step_filter, steps, warnings }`
- `luban bpt version publish`：文本模式输出发布请求摘要或结果 KV 表格；JSON 模式返回 `{ method, endpoint, request, url, version_id, response.version_ids, final_status, final_version, final_versions, poll_attempts, ... }`；默认立即返回时四个终态字段均为 `null`，传 `--wait` 时 `final_versions` 包含全部发布任务的最后观测状态
