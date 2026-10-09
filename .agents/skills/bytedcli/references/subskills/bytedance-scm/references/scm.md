# SCM

```bash
# Repo list — 默认 favor tab；--all 切到 All tab；服务端 filter
bytedcli scm repo list --page 1 --page-size 10                                     # 我的收藏
bytedcli scm repo list --all                                                       # 全部仓库
bytedcli scm repo list --search sort                                               # favor tab + 名称搜索
bytedcli scm repo list --all --search sort                                         # all tab + 名称搜索
bytedcli scm repo list --create-user <username>                                    # favor tab + creator
bytedcli scm repo list --all --create-user <username> --language Go --page-size 20 # all tab + 多过滤
bytedcli scm repo search "byteapi/command/bytedcli"                                # 等价 list --all --search

bytedcli scm repo version list "byteapi/command/bytedcli" --branch master --type online --status build_ok
bytedcli scm repo version list --repo-id 533180 --branch master --type online
bytedcli scm repo artifact get --version-id 9876
# US-TTP：预览 / 提交既有 SCM 版本的 CDN 静态资源上传
bytedcli --site us-ttp scm repo artifact upload-static --repo-id 123 --version 1.0.0.1
bytedcli --site us-ttp scm repo artifact upload-static --repo-id 123 --version 1.0.0.1 --yes
bytedcli scm repo version get "byteapi/command/bytedcli" --version 1.0.0.1
bytedcli scm repo version download "byteapi/command/bytedcli" --version 1.0.0.1 --output ./bytedcli.tar.gz
bytedcli scm repo version download "byteapi/command/bytedcli" --latest --output ./bytedcli-latest.tar.gz
# Version compare — 列两个构建版本之间的精确 commit 范围（比 git log --since 准：用 build manifest pin 的 SHA，不受 force-push / merge time 漂移影响）
bytedcli scm repo version compare --repo-id 379649 --base 2.0.4.9494 --target 2.0.4.9656
bytedcli scm repo version compare "byteapi/command/bytedcli" --base 1.0.0.1686 --target 1.0.0.1720 --first-parent --page-size 20
bytedcli scm repo build "byteapi/command/bytedcli" --branch master --type test -e '{"CUSTOM_KEY":"VALUE"}' -m "trigger build reason"
# 指定 build_steps；CLI 传值优先，未传时默认回填 SCM 仓库配置里的 build_steps
bytedcli scm repo build "byteapi/command/bytedcli" --branch master --type test --build-steps '{"pre-build":[8,1]}'
# 指定编译架构（支持 x86_64 / aarch64 / riscv64，可重复或逗号分隔）
bytedcli scm repo build "byteapi/command/bytedcli" --branch master --type test --arch riscv64
# 指定构建镜像 alias；不传时默认使用仓库配置的镜像
bytedcli scm repo build "byteapi/command/bytedcli" --branch master --type test --build-image golang-1.21
# 通过完整的 40 位 commit SHA 直接打包（--commit 和 --branch 互斥，不需要指定分支，产物只在 CN CDN 落地）
bytedcli scm repo build "example-org/example-repo" --commit 0123456789abcdef0123456789abcdef01234567 --type offline
bytedcli scm repo build --repo-id 533180 --branch master --type offline

# Build log — 三种入口（任选其一）
bytedcli scm repo build-log "byteapi/command/bytedcli" "1.0.0.1686" --step building
bytedcli scm repo build-log "byteapi/command/bytedcli" "1.0.0.1686" --status failed
bytedcli scm repo build-log --repo-id 533180 "1.0.0.1686" --step building
bytedcli scm repo build-log --record-id 9056070 --step building                    # 直接按 ByteBuild record id 取

# Build diagnosis — 查询指定仓库版本的最新构建排障结果（当前支持 Go / Node.js）
bytedcli scm repo diagnose --repo "example-org/example-repo" --version "1.0.0.1"

# SCM WebShell — 验证候选或准备 session
bytedcli --site cn --json scm webshell source get --version-id 101
bytedcli --site cn --json scm webshell prepare --record-id 301 --step building
```

## `scm webshell` 工作流

- SCM version/ByteBuild source-record candidate、`source get`、`prepare`、`next_argv` 和一次 Minimal WebShell Probe: [`scm-webshell-prepare.md`](scm-webshell-prepare.md)
- 已准备 session 的 direct operation、Remote Verification Change、lifecycle、archive、audit、diagnose、recover 和 accountable resolution: [`scm-webshell-operations.md`](scm-webshell-operations.md)
- `prepare` 是唯一 create-or-reuse 入口。后续 direct operation 只使用 opaque `session_id`, 不从 SCM selector 隐式创建资源。

## `scm repo artifact get`

`--version-id` 是 SCM 版本记录的数字 ID。命令返回远端 `artifact_info` 元数据，不下载文件。

## `scm repo artifact upload-static`

- 必填 `--repo-id`（正整数）与 `--version`，全局 `--site us-ttp` 选择 US-TTP；保留既有 `--scm-site` 覆盖。
- 仅支持 `prepare_upload` / `upload_failed`，触发已有产物的 CDN 上传，不读取本地文件，也不重新构建。
- 默认只读查询版本并预览完整 POST body，显式 `--yes` 才提交。SCM 读取与 Goofy 上传使用各自站点和 ByteCloud JWT。
- JSON 返回 `dry_run`、`submitted`、`previous_status`、`request` 和 `next_command`。`submitted: true` 不等于 CDN 上传完成；按 `next_command` 查询版本状态。
- 不自动重试 POST，不轮询等待；网络失败时先确认版本状态再重试。

## `scm repo version get`

按仓库名或 `--repo-id` 查询单个版本详情：

```bash
bytedcli scm repo version get "byteapi/command/bytedcli" --version 1.0.0.1
bytedcli scm repo version get --repo-id 533180 --version 1.0.0.1
```

## `scm repo version download`

下载 SCM 归档文件，固定版本用 `--version`，最新版本用 `--latest`：

```bash
bytedcli scm repo version download "byteapi/command/bytedcli" --version 1.0.0.1 --output ./bytedcli.tar.gz
bytedcli scm repo version download "byteapi/command/bytedcli" --latest --output ./bytedcli-latest.tar.gz
bytedcli scm repo version download "byteapi/command/bytedcli" --version 1.0.0.1 --arch aarch64 --output ./bytedcli-arm.tar.gz
bytedcli scm repo version download "byteapi/command/bytedcli" --version 1.0.0.1 --resource --output ./bytedcli-res.tar.gz
```

默认使用当前 site 对应的 Luban SCM 归档域名；需要指定下载域名时使用 `--archive-site byted-cn|ttp|ttp-office|eu-ttp`。本地目标文件已存在时默认拒绝覆盖，确认覆盖时加 `--force`。

## `scm repo diagnose` 约定

- 通过固定的 Build Insight 查询接口读取最新构建诊断，不接受自定义 URL
- `--repo` 与 `--version` 必填
- 成功结果统一返回仓库、版本、语言、架构、状态、分类、失败步骤、构建信息、根因和解决方案；上游未生成的可选字段返回 `null`
- 未找到诊断时返回结构化 `SCM_DIAGNOSIS_NOT_FOUND` 错误；先确认仓库与版本。诊断不存在或未提供根因/解决方案时，改用 `scm repo build-log`
- 当前仅支持 Go 和 Node.js 构建

## `scm repo list` 选项

| 选项                   | 默认 | 说明                                              |
| ---------------------- | ---- | ------------------------------------------------- |
| `--starred`            | 默认 | 列出收藏（favor tab，`is_favor=true`）            |
| `--all`                | —    | 列出全部（`is_favor=false`），与 `--starred` 互斥 |
| `--search <kw>`        | —    | 服务端按名称模糊搜索                              |
| `--create-user <user>` | —    | 服务端按 creator 用户名过滤                       |
| `--language <lang>`    | —    | 服务端按语言（如 `Go`、`Python`）过滤             |
| `--page <n>`           | `1`  | 1 起步                                            |
| `--page-size <n>`      | `10` | 每页条数                                          |

## 区域同步 flag

`scm repo build` 支持 3 个同步开关，默认继承仓库配置（SCM 仓库设置页的 `sync_aws` / `sync_oss` / `sync_bvc`），CLI 可覆盖：

| Flag                           | 作用                   | 对应 build stage       |
| ------------------------------ | ---------------------- | ---------------------- |
| `--sync-aws` / `--no-sync-aws` | VA/US 区域上传         | `uploading-va-source`  |
| `--sync-oss` / `--no-sync-oss` | SG/Aliyun 区域上传     | `uploading-sg-source`  |
| `--sync-bvc` / `--no-sync-bvc` | BVC 多 region 发布格式 | `uploading-bvc-source` |

仅 `--branch` 模式会真正触发海外上传；`--commit` 接受 7～40 位 SHA，提交前会先在 Codebase 校验存在性，short SHA 会同时解析为完整的 40 位 SHA，查不到时禁止提交。该模式产物只在 CN CDN 落地。

## `scm repo build --build-steps` 约定

- 形态必须是 JSON object，例如 `'{"pre-build":[8,1]}'`
- 优先级：`--build-steps` > SCM repo detail 默认 `build_steps`
- 非法输入（空串、非法 JSON、数组等非对象值）会直接报 `SCM_INPUT_ERROR`

## `scm repo build --build-image` 约定

- 指定本次构建使用的镜像 alias 名称
- 优先级：`--build-image` > SCM repo detail 默认 `image`
- 不传时默认使用仓库配置的镜像
