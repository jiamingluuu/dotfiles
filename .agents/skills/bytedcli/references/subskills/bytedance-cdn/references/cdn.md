# bytedcli CDN 命令参考

## cdn domain list

列出 CDN 域名，支持关键词过滤。

```bash
# 默认查 CN 站点
bytedcli cdn domain list --domain api.coze.cn

# 查 i18n-tt 站点
bytedcli --site i18n-tt cdn domain list --domain api.coze.com

# 查 i18n-bd / eu-ttp / us-ttp 站点
bytedcli --site i18n-bd cdn domain list --domain api.example.com
bytedcli --site eu-ttp cdn domain list --domain api.example.com
bytedcli --site us-ttp cdn domain list --domain api.example.com

# 分页
bytedcli cdn domain list --domain coze --page 1 --page-size 20

# JSON 输出
bytedcli --json cdn domain list --domain api.coze.cn
```

文本输出字段：ID, Name, Type, Status, CNAME, Owner。其中 Type / Status 会显示枚举名；`Deploying` 状态会显示为 `Domain ticket in progress`。JSON 输出保留后端原始字段。

## cdn domain get

查看单个域名的完整 CDN 配置。

```bash
# 通过 ID
bytedcli cdn domain get --id cdn-157402

# 通过域名（精确匹配）
bytedcli cdn domain get --domain api.coze.cn

# i18n-tt 站点
bytedcli --site i18n-tt cdn domain get --domain api.coze.com

# i18n-bd / eu-ttp / us-ttp 站点
bytedcli --site i18n-bd cdn domain get --domain api.example.com
bytedcli --site eu-ttp cdn domain get --domain api.example.com
bytedcli --site us-ttp cdn domain get --domain api.example.com

# JSON 输出（适合程序消费）
bytedcli --json cdn domain get --domain api.coze.cn
```

站点选择：CN 域名使用默认 `--site cn`；i18n-tt 站点使用 `--site i18n-tt`；i18n-bd 站点使用 `--site i18n-bd`；eu-ttp 站点使用 `--site eu-ttp`；us-ttp 站点使用 `--site us-ttp`。`cdn domain` 的站点由全局 `--site` 决定，与 `cdn file --region` 无关。

输出包含：

- 基本信息：ID, Name, Type, Status, CNAME, Owner, Host, CreatedAt, UpdatedAt
- Origin：GTM Instance、源站列表、OriginScheme、Disaster Recovery、端口、SNI；OriginScheme 会显示为 `Http`、`Https` 或 `Follow`
- HTTPS：启用状态、HTTP/2、OCSP、Redirect、Redirect Code、TLS 版本、证书 ID 与过期时间
- Response Headers：响应头开关与具体 header 列表
- Compression：Gzip、Brotli
- Cache：FollowOrigin、RemoveQueryParams
- Advanced Configuration：IPv6、QUIC、WebSocket

## cdn file

CDN 文件操作走 CDN 上传服务。办公网调用 SG/VA2 默认使用 ROW host；生产网或服务端调用 SG/VA2 时设置 `BYTEDCLI_NETWORK_PROFILE=prod`。`upload` / `download` / `delete` / `refresh` / `list` 共用参数：`--dir`、`--team-space`、`--region`（`INTERNAL|CN|SG|VA2`，默认 `CN`）、`--email`、`--cdn-token`、`--cdn-token-file`。`permission` 子命令不共用这组参数，见下文。

```bash
# 上传单个文件到个人空间根目录
bytedcli cdn file upload --file ./demo-icon.png

# 上传到团队空间指定目录并自动刷新
bytedcli cdn file upload --file ./demo-icon.png --team-space demo-team --dir assets --auto-refresh

# 办公网上传 SG 区域（默认走 ife-cdn.tiktok-row.net）
bytedcli cdn file upload --file ./demo-icon.png --region SG

# 办公网上传 VA2 区域（默认走 ife-cdn.tiktok-row.net）
bytedcli cdn file upload --file ./demo-icon.png --region VA2

# 生产网或服务端上传海外区域（SG/VA2 走 ife-cdn.byteintl.net）
BYTEDCLI_NETWORK_PROFILE=prod bytedcli cdn file upload --file ./demo-icon.png --region SG

# 上传压缩包并解压（本地包，加 --unzip）
bytedcli cdn file upload --unzip --file ./demo-bundle.zip --dir assets

# 上传压缩包并解压（远端 URL）
bytedcli cdn file upload --unzip --url https://example.com/demo-bundle.zip --dir assets

# 递归上传本地目录（保留相对结构落到 --dir 下；已存在默认跳过，--force 覆盖）
bytedcli cdn file upload --local-dir ./demo-dist --dir assets
bytedcli cdn file upload --local-dir ./demo-dist --dir assets --force

# 删除文件（不可逆，仅交互终端可执行，会弹 y/yes 确认；脚本 / JSON / 非 TTY 会报错拒绝）
bytedcli cdn file delete --file demo-icon.png --dir assets --auto-refresh

# 刷新文件
bytedcli cdn file refresh --file demo-icon.png --dir assets

# 列出目录内容（文本输出逐文件附带 CDN 加速 URL）
bytedcli cdn file list --dir assets

# 下载单个文件到本地（--dest 缺省落到当前目录同名文件，已存在即报错不覆盖）
bytedcli cdn file download --file demo-icon.png --dir assets --dest ./demo-icon.png

# 申请团队空间管理员权限（--region 必填，无默认值）
bytedcli cdn file permission apply --team-space demo-team --user demo.user --permission admin --region INTERNAL

# 申请团队空间只读权限
bytedcli cdn file permission apply --team-space demo-team --user demo.user --permission view --region INTERNAL

# 列出团队空间已授权用户（需本人已登录且在该空间有权限）
bytedcli cdn file permission list --team-space demo-team

# 同时解析每个成员的权限级别（逐用户查询，成员多时更慢）
bytedcli cdn file permission list --team-space demo-team --with-permission-type

# JSON 输出
bytedcli --json cdn file upload --file ./demo-icon.png
bytedcli --json cdn file download --file demo-icon.png --dir assets --dest ./demo-icon.png
```

`upload` 默认返回 `cdnUrl`（完整 CDN 加速地址），JSON 模式额外包含 `domain` / `path` / `tosKey`；加 `--unzip` 时把上传内容当压缩包解压，返回解压后的文件 URL 列表。加 `--local-dir` 时递归上传本地目录（保留相对目录结构、与 `--file`/`--url`/`--unzip`/`--auto-refresh` 互斥）：已存在文件默认跳过并逐条列出，`--force` 才覆盖；并发 2 路、失败逐条汇总，JSON 输出 `{uploaded[], skipped[], failed[]}`（uploaded 项带 `cdn_url`，failed 项带 `error`）；存在 failed 时 `status` 为 `error`、退出码非 0，修复后重跑即可（已上传文件自动跳过）。

`download` 下载 CDN 单文件：`--dest` 为本地完整目标路径（含文件名，不是目录，缺省落到当前目录同名文件），已存在时直接报错、不覆盖；多加速域名按序尝试，首个成功即返回；JSON 输出为 `{local_path, bytes, cdn_url, tos_key}`。`list` 文本输出逐文件附带 CDN 加速 URL（域名接口不可用时降级为只列文件名）；INTERNAL 的 URL 需带 `X-Tos-Access: internal` 请求头访问，INTERNAL 场景统一用 `cdn file download` 下载。

身份与护栏：`--email` 默认取本地登录用户；显式传他人邮箱（local-part 与登录用户不一致）直接报错拒绝（`CDN_IFE_IDENTITY_MISMATCH`，无放行开关），只能改用本人身份。`delete` 不可逆且仅限交互终端执行（弹 y/yes 确认）；JSON / 非交互（Agent / 脚本）场景一律抛 `CDN_IFE_CONFIRM_REQUIRED`、不能删除。`--cdn-token` 明文会进 shell history，建议改用 `--cdn-token-file <path>` 或环境变量 `BYTEDCLI_CDN_TOKEN`。`upload --unzip --url` 由服务端拉取 URL，只传可信来源。上传内容公网可读且无签名，不要上传密钥或未脱敏数据。

`permission apply` 会创建 CDN 团队空间权限 BPM 工单，而不是直接修改权限。`--team-space`、`--user`、`--permission`、`--region` 均为必填。`--permission` 支持 `admin`（管理员）和 `view`（只读）；`--region` 支持 `INTERNAL|CN|SG|VA2`，可重复或逗号分隔，**没有默认值**：授权按区域生效，一个区域的权限不会带到另一个区域，必须与后续 `cdn file list --region` 实际使用的区域一致。一张工单只授权一个用户，`--user` 传逗号串直接报错，多人授权分多次执行。命令默认先搜索校验 `--user`，必要时可加 `--skip-user-check` 跳过预检。

`permission list` 列出某团队空间已授权的用户。`--team-space` 必填，不支持全量列举。命令要求本机已登录（无登录态报 `CDN_TEAM_SPACE_AUTH_REQUIRED`），`--email` 只能与登录用户一致、不能用来切换身份；发起方必须在目标空间确有授权，否则报 `CDN_TEAM_SPACE_FORBIDDEN` 且不返回任何名单。`--with-permission-type` 会为每个成员各发一次查询补全权限级别，成员多时明显更慢，且只有全部成员都探测成功才会 `permission_type_resolved: true`，失败数在 `permission_type_failed`。`--timeout-ms` 覆盖全量授权表拉取的超时（默认 60000）。JSON 输出为 `{team_space, requester, total, user_count, permission_type_resolved, permission_type_failed, members[]}`；`total` 是授权记录数（一条记录 = 一个 user+region），`user_count` 才是去重人数。

上游授权表免鉴权且单次返回全公司数据，`permission list` 的三道门（`--team-space` 必填、身份只认登录态、发起方须在名单内）是客户端输出门，不是服务端授权。
