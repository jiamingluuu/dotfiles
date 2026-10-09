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

## cdn metric query

查询指定域名的指标时间序列。`cn` 为只读 GET，`i18n-tt` / `us-ttp` 为只读 POST；两条接口使用不同原生指标名，不做隐式语义映射。参数如下：

| 参数 | 含义 |
| --- | --- |
| 全局 `--site` | `cn`（默认）、`i18n-tt`、`us-ttp`；其它站点拒绝，不回退 `cn` |
| `--domain` | 必填，域名；可重复或逗号分隔，不接受 URL、路径或端口 |
| `--metric` | 必填，后端指标名；可重复或逗号分隔 |
| `--endpoint` | `edge` / `origin`；默认 `edge`，`i18n-tt` / `us-ttp` 可重复或逗号分隔，`cn` 只允许一个 |
| `--interval` | `1min|5min|1hour|1day`，默认 `5min` |
| `--group-by` | 仅 `i18n-tt` / `us-ttp`：`domain|vendor|cdn_type`，可重复或逗号分隔；默认聚合 |
| `--vendor` | 仅 `i18n-tt` / `us-ttp`：后端厂商名称，可重复或逗号分隔 |
| `--start` | 起始时间，默认结束时间前一小时 |
| `--end` | 结束时间，默认当前时间 |

时间接受 Unix 秒/毫秒、ISO 8601 或相对时间（如 `'1h ago'`）；发送给后端及 JSON 返回的时间戳统一为 Unix 秒，开始必须早于结束。建议 ISO 8601 显式带时区。

`--start` 和 `--end` 都支持相对时间；分钟写 `'20m ago'`，小时写 `'1h ago'`，不要写 `'20min ago'`。例如查询结束于 20 分钟前的一小时：`--end '20m ago'` 并省略 `--start`（默认相对 end 向前一小时）。

```bash
bytedcli --site cn --json cdn metric query --domain static.example.com --metric status
bytedcli --site i18n-tt --json cdn metric query --domain static.example.com --metric status_bucket_4xx,status_bucket_5xx --interval 5min --start '1h ago'
bytedcli --site us-ttp --json cdn metric query --domain static.example.com --metric bandwidth --endpoint origin --start 1700000000 --end 1700003600
bytedcli --site i18n-tt --json cdn metric query --domain static.example.com,assets.example.com --metric request,traffic_hit_ratio --group-by domain,vendor --interval 1hour
```

`i18n-tt` / `us-ttp` 的 `request` 是请求总数，单位 `count`；`traffic_hit_ratio` / `request_hit_ratio` / `edge_traffic_hit_ratio` / `edge_request_hit_ratio` 是 0~1 ratio，文本与 JSON 都保留该原始值，不标为百分数。`status_bucket_summary` 返回各状态码段总数，`status_bucket_4xx` / `status_bucket_5xx` 返回对应段内各具体状态码。

已验证 `bandwidth` 单位为 `bps`、`traffic` 为 `bytes`、`qps` 返回单位为 `count`（指标语义仍为每秒请求速率）。`status_bucket_5xx` 返回多个具体 `status_code_*` 指标，单位为 `count`。CLI 仅接受下表列出的 16 个 `i18n-tt` / `us-ttp` 指标，不编造映射或推导错误率。

JSON envelope 的 `data`：

```json
{
  "query": {
    "domains": ["static.example.com"],
    "metrics": ["bandwidth"],
    "endpoints": ["edge"],
    "interval": "5min",
    "start": 1700000000,
    "end": 1700003600
  },
  "results": [{
    "metric": "bandwidth",
    "unit": "bps",
    "series": [{
      "tags": {},
      "data": [{"timestamp": 1700000100, "value": 1024}]
    }]
  }],
  "metadata": {"dataSource": "sample-source", "executionMs": 12},
  "traceId": "sample-trace"
}
```

`tags` 保留后端各条序列的分组标签，不臆造域名/节点分组；`metadata` 与 `traceId` 取决于响应。文本输出逐序列列出时间、值、单位，不截断数据点。零值保留，缺失值 `null` 显示为 `-`，不补点。空数组表示无返回数据，不能解释为全零。后端明确失败或响应结构不符均报错，不返回成功空数组。

指标查询使用站点 JWT：`cn` 复用 `cdn domain` 的 ByteCloud console proxy host/path 和代理固定头，使用 GET `describe-cdn-data` / `describe-cdn-origin-data`，附加对应 `x-dm-schema-name`；`i18n-tt` 和 `us-ttp` 复用 `cdn domain` 的 TI SG / TI TX host/path，均 POST 调用 `stat-query-metrics`，`us-ttp` 保留 action schema header。host 在 `site.ts` 维护，HTTP/header 在 client，请求映射在 API，响应规范化在 parser；ife 上传服务独立。

### cn 数据与权限

`cn` 请求参数为 `start_time`、`end_time`、`domain`（逗号列表）、`metric`（逗号列表）、`interval`。CLI 的 `1hour` / `1day` 映射为 `hour` / `day`。原生指标：`bandwidth`、`flux`、`pv`、`status`、`hitrate`、`pvhitrate`；origin 仅支持前四项。具体厂商的可用粒度/指标由 `describe-cdn-vendor-stat-ability` 决定，并非所有厂商均支持全部组合。

`cn` `response.resources[].metrics[].values[]` 规范化为 `results[].series[].data[]`。保留原生指标名；资源名在 `tags.resource`（域名或 `total`），区域/运营商标签分别保留。上游无单位字段，输出 `unit=upstream`；不把命中率自动当作 0~1 ratio，不从 `pv` 擅自推导 QPS。

JSON 额外返回 `isRandomized`、`invalidDomains` 和 `metadata.dataSource`。**`isRandomized=true` 表示随机化数据，不能作为真实指标使用**，文本模式有明确警告。不要将 total 和分域名累加，也不要将 `status_4xx` 汇总与 `status_404` 等明细重复累加。

无域名权限时，`bandwidth/flux/pv` 可能返回上游权限错误（如 `7000000` / `PermissionDenied`）；CLI 使用统一 `CDN_METRIC_API_ERROR`，保留上游 message、code、error 和 traceId；状态码和命中率可能成功但返回随机化数据。先在 `cn` 控制台按“有权限”筛选目标域名；列表为空时，需由域名管理员授予权限，再确认 `isRandomized=false`。一次请求混入需要权限的指标可能导致整批失败；CLI 不删除失败指标后伪装成完整查询成功。

### 指标验证范围

以下是 CLI 支持的完整 `i18n-tt` / `us-ttp` metric 集合，共 16 项。已使用 `i18n-tt` 的构建产物逐项独立查询（edge、5min），每项均返回时间序列；`us-ttp` 也已逐项验证。该集合不代表后端完整枚举，也不保证任意域名、厂商、时间范围或 origin 均有数据。未列出的名字（包括独立 0xx、1xx、3xx bucket）在发请求前明确拒绝；summary/full_breakdown 响应中的对应状态码段仍原样保留。

| metric | `i18n-tt` | `us-ttp` | 含义/响应 |
| --- | --- | --- | --- |
| `bandwidth` | 返回序列 | 返回序列 | 带宽，bps |
| `traffic` | 返回序列 | 返回序列 | 流量，bytes |
| `request` | 返回序列 | 返回序列 | 请求数，count |
| `qps` | 返回序列 | 返回序列 | 请求速率，后端 unit 为 count |
| `traffic_hit_ratio` | 返回序列 | 返回序列 | 流量命中率，ratio |
| `request_hit_ratio` | 返回序列 | 返回序列 | 请求命中率，ratio |
| `edge_traffic_hit_ratio` | 返回序列 | 返回序列 | 边缘流量命中率，ratio |
| `edge_request_hit_ratio` | 返回序列 | 返回序列 | 边缘请求命中率，ratio |
| `hit_traffic` | 返回序列 | 返回序列 | 命中流量 |
| `hit_request` | 返回序列 | 返回序列 | 命中请求数 |
| `status_bucket_summary` | 返回序列 | 返回序列 | 各状态码段汇总 |
| `status_full_breakdown` | 返回序列 | 返回序列 | 状态码段和具体码 |
| `status_bucket_2xx` | 返回序列 | 返回序列 | 2xx 内具体码 |
| `status_bucket_4xx` | 返回序列 | 返回序列 | 包含 404 等具体码 |
| `status_bucket_5xx` | 返回序列 | 返回序列 | 5xx 内具体码 |
| `status_code_404` | 返回序列 | 返回序列 | 单个状态码；未逐个测试所有 HTTP code |

| `cn` metric | 当前账号实测 | 验证边界 |
| --- | --- | --- |
| `status` | 返回序列，`isRandomized=true` | edge/origin 均验证；有 4xx 汇总及具体码，非真实数据验收 |
| `hitrate` | 返回序列，`isRandomized=true` | edge，非真实数据验收 |
| `pvhitrate` | 返回序列，`isRandomized=true` | edge，非真实数据验收 |
| `bandwidth` | PermissionDenied | 需要有权限的域名；未验证真实数据 |
| `flux` | PermissionDenied | 同上 |
| `pv` | PermissionDenied | 同上 |

依据为用户请求、控制台 statistical-analysis 源码、CDN 统计分析用户指南和在线厂商统计能力接口。`cn` 的真实数据验收仍需权限，离线 fixtures 只证明协议解析，不替代线上验收。
