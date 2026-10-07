---
name: bytedance-cdn
description: "Operate ByteCloud CDN via bytedcli: list CDN domains and get domain detail configuration (origin, HTTPS, cache, compression); upload files (single file, archive extraction, or recursive local directories), download, delete, refresh and list files on the CDN upload service; apply for team-space file permissions and list the users already granted on a team space. Use when tasks mention CDN domain lookup, CDN configuration, CDN CNAME, CDN certificate, CDN origin, fusion-cdn, CDN file upload, CDN upload, CDN download, downloading files from CDN, uploading static assets or a whole directory to CDN, CDN team-space permission, or who has access to a CDN team space."
---

# bytedcli CDN

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

- 查询 CDN 域名列表（按域名关键词搜索）
- 查看 CDN 域名的详细配置（源站、HTTPS、缓存、压缩等）
- 确认域名是否被 CDN 系统托管（对比 CNAME 与实际 DNS 解析）
- 检查证书到期时间
- 上传文件到 CDN（单文件、压缩包解压上传、本地目录递归上传）
- 下载 CDN 单文件到本地（不覆盖已存在的本地文件）
- 删除、刷新 CDN 文件，列出 CDN 目录内容（文本输出附带每个文件的 CDN 加速 URL）
- 申请 CDN 团队空间文件权限（管理员或只读）
- 列出 CDN 团队空间已授权的用户（需本人已登录且在该空间有权限）

## 前置条件

- 使用通用调用方式：`../../invocation.md`
- `cdn domain` 命令（fusion-cdn 配置查询）：
  - 需要个人 ByteCloud JWT。在生产网且存在 `SEC_TOKEN_STRING` / `SEC_TOKEN_PATH` 时，CLI 会按目标站点优先执行 ZTI→个人 JWT；交换不可用、不支持该站点或失败时自动回退同站点 `bytedcli auth login`
  - 办公网仍使用原有 SSO 链路；登录时按目标站点执行，例如 `bytedcli auth login`、`bytedcli --site i18n-tt auth login`
- `cdn file` 命令（CDN 上传服务）：
  - 身份由 `--email` 承载，后端不校验；bytedcli 默认以本地登录用户身份操作，并在客户端侧拦截冒名与误删
  - 不传 `--email` 时回退到本地登录用户名拼 `@bytedance.com`；显式传他人邮箱（local-part 与登录用户不一致）直接报错拒绝（`CDN_IFE_IDENTITY_MISMATCH`），无放行开关，只能改用本人身份
  - `delete` 不可逆且仅限交互终端执行（弹 y/yes 确认）；JSON / 非交互（Agent / 脚本）场景一律抛 `CDN_IFE_CONFIRM_REQUIRED`、不能删除
  - 需在办公网/VPN 环境下执行（`ife.bytedance.net` 等 host 仅办公网可达）
  - 加密团队空间额外需要 `--cdn-token`（明文会进 shell history，建议用 `--cdn-token-file` 或环境变量 `BYTEDCLI_CDN_TOKEN`）
  - 团队空间权限申请走 ByteCloud BPM，个人 JWT 同样优先使用生产网 ZTI，失败时回退 `bytedcli auth login`，并会提交审批工单

> 执行前缀见 `../../invocation.md`；下面示例直接写 `bytedcli`。

## Quick start

```bash
# 查询域名列表（CN 站点，默认）
bytedcli cdn domain list --domain example.com

# 查询域名列表（i18n-tt 站点）
bytedcli --site i18n-tt cdn domain list --domain example.com

# 查询域名列表（i18n-bd / eu-ttp / us-ttp 站点）
bytedcli --site i18n-bd cdn domain list --domain example.com
bytedcli --site eu-ttp cdn domain list --domain example.com
bytedcli --site us-ttp cdn domain list --domain example.com

# 通过域名查看详细配置
bytedcli cdn domain get --domain example.com

# 通过 ID 查看详细配置
bytedcli cdn domain get --id cdn-112997

# JSON 输出
bytedcli --json cdn domain list --domain example.com
bytedcli --json --site i18n-tt cdn domain get --domain example.com

# 上传文件到 CDN（个人空间根目录）
bytedcli cdn file upload --file ./demo-icon.png

# 上传到团队空间指定目录
bytedcli cdn file upload --file ./demo-icon.png --team-space demo-team --dir assets

# 递归上传本地目录（dist 内容落到 assets/ 下，保留相对结构；已存在的文件默认跳过）
bytedcli cdn file upload --local-dir ./dist --dir assets

# 覆盖已存在的文件
bytedcli cdn file upload --local-dir ./dist --dir assets --force

# 列出 CDN 目录内容（文本输出附带每个文件的 CDN 加速 URL）
bytedcli cdn file list --dir assets

# 下载 CDN 单文件（--dest 缺省落到当前目录同名文件，已存在即报错不覆盖）
bytedcli cdn file download --file demo-icon.png --dir assets --dest ./demo-icon.png

# 申请团队空间管理员权限
bytedcli cdn file permission apply --team-space demo-team --user demo.user --permission admin --region INTERNAL

# 申请团队空间只读权限
bytedcli cdn file permission apply --team-space demo-team --user demo.user --permission view --region INTERNAL

# 列出团队空间已授权用户（需本人已登录且在该空间有权限）
bytedcli cdn file permission list --team-space demo-team

# 同时解析每个成员的权限级别（逐用户查询，成员多时更慢）
bytedcli cdn file permission list --team-space demo-team --with-permission-type
```

## Commands

### cdn domain list

列出 CDN 域名。

```bash
bytedcli cdn domain list [--domain <keyword>] [--page <n>] [--page-size <n>]
```

| 参数          | 说明                         |
| ------------- | ---------------------------- |
| `--domain`    | 按域名关键词过滤（模糊匹配） |
| `--page`      | 页码，默认 1                 |
| `--page-size` | 每页条数，默认 10            |

### cdn domain get

查看 CDN 域名详细配置。支持 `--id` 或 `--domain` 二选一。

```bash
bytedcli cdn domain get --id <domain-id>
bytedcli cdn domain get --domain <domain-name>
```

| 参数       | 说明                                  |
| ---------- | ------------------------------------- |
| `--id`     | CDN 域名 ID（如 cdn-112997）          |
| `--domain` | 域名（精确匹配，先 list 再取 detail） |

输出包含：基本信息、源站配置、HTTPS/TLS 配置、缓存策略、压缩策略、IPv6/QUIC/WebSocket 状态。

### cdn file

CDN 文件操作，走 CDN 上传服务（与 `cdn domain` 的 fusion-cdn 控制台是不同 host、不同鉴权）。

`upload` / `download` / `delete` / `refresh` / `list` 共用以下参数（`permission` 子命令不共用，见下文）：

| 参数               | 说明                                                                                              |
| ------------------ | ------------------------------------------------------------------------------------------------- |
| `--dir`            | 目标目录；个人空间直接填目录名，留空表示空间根目录                                                |
| `--team-space`     | 团队空间名；传入时 `--dir` 解析为团队空间下的目录                                                 |
| `--region`         | 区域 `INTERNAL\|CN\|SG\|VA2`，默认 `CN`                                                           |
| `--email`          | 用户邮箱，默认取本地登录用户；以他人身份操作直接报错拒绝                                          |
| `--cdn-token`      | 加密团队空间的 `x-cdn-token`（明文，建议改用 `--cdn-token-file` / 环境变量 `BYTEDCLI_CDN_TOKEN`） |
| `--cdn-token-file` | 从文件读取 `x-cdn-token`，避免明文进 shell history                                                |

```bash
# 上传单个文件
bytedcli cdn file upload --file <path> [--dir <dir>] [--team-space <name>] [--auto-refresh]

# 上传压缩包并解压（加 --unzip；--file 与 --url 二选一）
bytedcli cdn file upload --unzip --file <archive> [--dir <dir>]
bytedcli cdn file upload --unzip --url <archive-url> [--dir <dir>]

# 递归上传本地目录（与 --file/--url/--unzip/--auto-refresh 互斥；已存在默认跳过，--force 覆盖）
bytedcli cdn file upload --local-dir <path> [--dir <dir>] [--team-space <name>] [--force]

# 删除文件
bytedcli cdn file delete --file <name> [--dir <dir>] [--auto-refresh]

# 刷新文件
bytedcli cdn file refresh --file <name> [--dir <dir>]

# 下载单个文件（--dest 缺省落到当前目录同名文件，已存在即报错不覆盖）
bytedcli cdn file download --file <name> [--dest <path>] [--dir <dir>] [--team-space <name>]

# 列出目录内容
bytedcli cdn file list [--dir <dir>] [--team-space <name>]

# 申请团队空间权限（--region 必填，无默认值）
bytedcli cdn file permission apply --team-space <name> --user <username-or-email> --permission <admin|view> --region <region>

# 列出团队空间已授权用户
bytedcli cdn file permission list --team-space <name> [--email <addr>] [--with-permission-type] [--timeout-ms <ms>]
```

`upload` 默认上传单个文件，成功后返回 `cdnUrl`（完整 CDN 加速地址），JSON 模式下还包含 `domain` / `path` / `tosKey`（服务端透传的 camelCase）；加 `--unzip` 时把上传内容当压缩包解压，返回解压后的文件 URL 列表。加 `--local-dir <path>` 时递归上传本地目录：目录内容落到 `--dir`（及 `--team-space`）之下并保留相对目录结构，已存在的文件**默认跳过并逐条列出**，传 `--force` 才覆盖；并发 2 路、单文件失败不中断；`--local-dir` 与 `--file`/`--url`/`--unzip`/`--auto-refresh` 互斥。目录模式 JSON 汇总为 `{uploaded[], skipped[], failed[]}`（snake_case，与单文件模式的 camelCase 形态不同）：uploaded 项为 `{local_path, cdn_path, cdn_url}`（无 URL 时 `cdn_url` 为 null），skipped 项为 `{local_path, cdn_path}`，failed 项为 `{local_path, cdn_path, error}`。**存在 failed 时整体判失败**：JSON 的 `status` 为 `error` 且退出码非 0；修复失败文件后重跑同一命令即可——已上传的文件会被默认 skip 语义自动跳过。

`download` 下载 CDN 单文件：`--file` 为远端文件名，`--dest` 为本地完整目标路径（含文件名，不是目录，缺省落到当前目录同名文件），`--dest` 已存在时直接报错、不提供覆盖开关；一个 region 挂多个加速域名时按序尝试，首个成功即返回。JSON 输出为 `{local_path, bytes, cdn_url, tos_key}`。`list` 的文本输出逐文件附带 CDN 加速 URL（与 `download` 实际下载地址同源；域名接口不可用时降级为只列文件名）。

`permission apply` 会先按 `--user` 做 ByteDance 用户预检，再提交 CDN 团队空间权限 BPM 工单。`--team-space`、`--user`、`--permission`、`--region` 均为必填，`--region` **没有默认值**：授权按区域生效，一个区域的权限不会自动带到另一个区域，必须显式声明，且要与后续 `cdn file list --region <region>` 实际使用的区域一致（`cdn file` 其他子命令的 `--region` 默认 `CN`，两者互不影响）。`--region` 支持 `INTERNAL|CN|SG|VA2`，可重复或逗号分隔；`--permission admin` 表示管理员权限，`--permission view` 表示只读权限。一次只能给一个用户授权，`--user` 传逗号串会直接报错，多个用户分多次执行。若用户搜索接口临时不可用，可加 `--skip-user-check` 直接提交工单。

`permission list` 列出某团队空间当前已授权的用户。`--team-space` 必填，不支持全量列举。身份只认本机登录态：未登录直接报 `CDN_TEAM_SPACE_AUTH_REQUIRED`（`--email` 不能替代登录），`--email` 只允许与登录用户一致。命令再校验该用户在目标空间确有授权，无授权时报 `CDN_TEAM_SPACE_FORBIDDEN` 且不返回任何名单。默认的 `Permission` 列取自授权记录自带字段，历史记录可能为空；加 `--with-permission-type` 会为每个成员各发一次查询来补全，成员多的空间明显更慢——只有全部成员都探测成功才会 `permission_type_resolved: true`，失败数在 `permission_type_failed`。`--timeout-ms` 覆盖全量授权表拉取超时（默认 60000）。JSON 输出为 `{team_space, requester, total, user_count, permission_type_resolved, permission_type_failed, members[]}`，`members` 项为 `{user, region, permission_type, created_at}`；`total` 是授权记录数（一条记录 = 一个 user+region 组合），`user_count` 才是去重人数。

上游授权表免鉴权且单次返回全公司授权关系，`permission list` 的三道门是**客户端输出门，不是服务端授权**：命令会先取回完整响应再在本地过滤和判权。不要依赖它做敏感隔离，也不要在该命令上开 `--http-debug` / `--http-trace-file`（响应体已标记为敏感、不进 trace，但仍不要把这类查询接到不可信环境）。

## Agent Guidance

### 站点选择

- CN 域名（`*.bytedance.net`、`*.coze.cn` 等）使用默认 `--site cn`
- i18n-tt 站点使用 `--site i18n-tt`
- ByteIntl 站点使用 `--site i18n-bd`
- EU TTP 站点使用 `--site eu-ttp`
- US TTP 站点使用 `--site us-ttp`
- SSO 环境：`i18n-tt`、`eu-ttp`、`us-ttp` 属 TikTok SSO；`cn`、`i18n-bd` 属 ByteDance SSO
- 生产网（存在 `SEC_TOKEN_STRING` / `SEC_TOKEN_PATH`）时，`cn` / `i18n-tt` / `i18n-bd` 优先用 ZTI 换个人 ByteCloud JWT，失败再回退对应 SSO；`eu-ttp` / `us-ttp` 暂不支持 ZTI，始终走 TikTok SSO 登录态。办公网所有站点仍走原有 SSO 链路

### 判断域名是否被 CDN 托管

1. 通过 `cdn domain get --domain <name>` 获取 CDN 系统中的 CNAME
2. 通过 `dig +short <name> CNAME` 获取实际 DNS 解析
3. 若两者一致，说明域名已被 CDN 系统托管，证书可自动续期
4. 若 CDN 中找不到该域名，则未托管

### CDN 文件上传

- `cdn domain` 查询和 `cdn file` 上传是不同服务：`cdn domain` 按全局 `--site` 选择 fusion-cdn 配置查询网关；`cdn file` 忽略全局 `--site`，使用文件命令自己的 `--region` 和 network profile 路由。
- `cdn file` 的 `--region` 与网络环境共同决定请求 host：`INTERNAL`/`CN` 固定走 `ife.bytedance.net`；`SG`/`VA2` 默认办公网走 `ife-cdn.tiktok-row.net`，生产网或服务端调用设置 `BYTEDCLI_NETWORK_PROFILE=prod` 后走 `ife-cdn.byteintl.net`。这与 `cdn domain` 的 `--site` 互不影响。
- 上传服务为弱鉴权：身份由 `--email` 承载且后端不校验。bytedcli 默认以本地登录用户身份操作；显式传他人邮箱（local-part 与登录用户不一致）直接报错拒绝（`CDN_IFE_IDENTITY_MISMATCH`，无放行开关）。**不要为了让命令通过而随手填别人的 `--email`**：以本人身份操作即可，去掉 `--email` 会自动用登录用户。
- `delete` 不可逆且仅限交互终端执行：JSON / 非交互（Agent / 脚本）场景一律抛 `CDN_IFE_CONFIRM_REQUIRED`、无法删除——删除 CDN 文件不开放给自动化，需由人在交互终端确认。
- 上传内容即公网可读（返回 `cdnUrl` 无签名、无过期）：不要上传密钥、token、个人隐私或未脱敏的内部数据。
- 团队空间不要手写固定前缀，统一用 `--team-space <name>` + `--dir <subdir>`，CLI 会自动拼接。
- `download` 的 `--dest` 是本地完整文件路径（含文件名），不是目录，缺省落到当前目录同名文件；已存在即报错（`--dest already exists`），不提供覆盖开关——要重新下载请先删本地文件或换一个 `--dest`。
- `list` 文本输出的 URL 列与 `download` 实际下载地址同源：CN/SG/VA2 的 URL 可直接复制用于浏览器或其他工具；INTERNAL 的 URL 需带 `X-Tos-Access: internal` 请求头访问，浏览器直接打不开，INTERNAL 场景统一用 `cdn file download` 下载。
- 报错提示“团队空间已被加密”时，补 `--cdn-token <token>` 重试；`--cdn-token` 是团队级共享凭据，不要写进命令行明文（会进 shell history），改用 `--cdn-token-file <path>` 或环境变量 `BYTEDCLI_CDN_TOKEN`。
- `upload --unzip --url <url>` 会由 CDN 服务端去拉取该 URL，只传可信来源。
- 给团队空间加权限时使用 `cdn file permission apply`。它创建 BPM 工单而不是直接改权限；输出中的 `ticket_url` / `record_id` 用于后续审批跟踪。
- `permission apply --region` 必填且无默认值：授权按区域生效，填错区域产出的工单即使审批通过也不解决问题。填之前先确认目标文件实际所在区域——与 `cdn file list --region <region>` 用的值保持一致。
- `permission apply --user` 一次只接受一个用户，传 `a,b` 会报 `CDN_PERMISSION_INPUT_ERROR`；给多人授权就多跑几次命令，每次一张工单。
- 查团队空间有哪些人有权限时使用 `cdn file permission list --team-space <name>`。它只读、不改任何权限，但要求本机已登录且本人在该空间已有授权；报 `CDN_TEAM_SPACE_AUTH_REQUIRED` 先 `bytedcli auth login`，报 `CDN_TEAM_SPACE_FORBIDDEN` 说明当前登录用户不在该空间、先用 `permission apply` 申请。**`--email` 不能用来切换身份**：它只接受与登录用户一致的地址，传他人邮箱会被 `CDN_IFE_IDENTITY_MISMATCH` 拒绝。
- `permission list` 的 `--with-permission-type` 会对每个成员各发一次请求，几百人的空间会明显变慢；只在确实要区分 admin / view 时才加。读结果前先看 `permission_type_resolved`：为 false 说明有 `permission_type_failed` 个成员没探测成功，那些行的权限列不可信。
- `upload --unzip` 的压缩包应为扁平结构（文件直接在包根目录）；若包内含顶层目录，服务端只解压根层文件，目录内条目不会落地，返回的 URL 列表也会相应为空。
- `upload --local-dir` 递归上传整个目录（无 ignore/排除规则），包括隐藏文件；上传前自行确认目录里没有密钥、token 等敏感内容。已存在判定按目标目录批量查询，不会逐文件探测。
- 上传服务仅面向 QPS ≤ 10 的内部低频场景；对外业务或高 QPS 上传应改用 TOS。

### 常见错误

- `Not authenticated`：需要登录对应站点，提示中包含完整登录命令
- `Domain "xxx" not found`：该域名在指定站点的 CDN 系统中不存在，尝试切换站点
- `cdn file` 请求超时/不可达：办公网确认 VPN 并使用默认 profile；生产网或服务端设置 `BYTEDCLI_NETWORK_PROFILE=prod`
