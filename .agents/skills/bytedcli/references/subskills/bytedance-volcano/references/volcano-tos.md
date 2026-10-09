# Volcano TOS (对象存储 / Object Storage)

## 认证方式

TOS 命令支持两种认证，推荐使用无需静态 AK/SK 的 SSO Session：

1. **SSO Session 认证（推荐）**：`--volc-account-id <babi-account-id>`。命令会复用已缓存的火山/BytePlus 控制台 session，向控制台 STS（service 名 `tos`）换取临时 AK/SK/SessionToken 后再签名，全程不落地长期密钥。
2. **AK/SK 认证**：显式传 `--access-key-id` / `--secret-access-key`（可选 `--session-token`），或走环境变量 `VOLC_ACCESSKEY` / `VOLC_SECRETKEY` / `VOLC_SESSION_TOKEN`，也支持官方 `VOLCENGINE_ACCESS_KEY` / `VOLCENGINE_SECRET_KEY` / `VOLCENGINE_SESSION_TOKEN`。旧变量优先，每组 AK/SK 必须完整，token 不跨来源混用。

签名走 TOS 原生的 `TOS4-HMAC-SHA256` 方案（不是 OpenAPI top 网关）。

## Endpoint 与 Region

- 火山（volc）：`tos-<region>.volces.com`，默认 region `cn-beijing`。
- BytePlus：`tos-<region>.bytepluses.com`。BytePlus 没有 `cn-beijing` 的 TOS endpoint，未显式传 `--region` 时自动默认 `ap-southeast-1`。
- 命令格式与 DBW/RDS 一致：使用 `--volc-account-id <id> --region <region>`，SSO Session 根据账号自动识别火山或 BytePlus。
- 使用 AK/SK 时，火山走默认 endpoint；BytePlus 需用受限的 `--host tos-<region>.bytepluses.com` 指定官方 endpoint。
- `--host` 仅允许覆盖为 `tos-<region>.volces.com` 或 `tos-<region>.bytepluses.com` 官方 endpoint；`--region` 覆盖签名 region。

## 命令示例

### 列出 Bucket

```bash
# 列出账号下全部 bucket
bytedcli volcano tos bucket list --volc-account-id <babi-account-id> --region cn-beijing

# 只看名字包含 demo 的 bucket
bytedcli volcano tos bucket list --volc-account-id <babi-account-id> --region cn-beijing --keyword demo

# BytePlus SSO 账号（平台自动识别，region 缺省自动 ap-southeast-1）
bytedcli volcano tos bucket list --volc-account-id <byteplus-account-id> --region ap-southeast-1
```

### 列出对象

```bash
bytedcli volcano tos object list \
  --volc-account-id <babi-account-id> \
  --bucket <bucket> --prefix data/ --delimiter / --page-size 50

# 翻页：把上一页返回的 next_page_token 传给 --page-token
bytedcli volcano tos object list \
  --volc-account-id <babi-account-id> \
  --bucket <bucket> --page-token <token>
```

### 列出对象历史版本

```bash
# 每次读取一页；limit 默认 20，最大 1000
bytedcli volcano tos version list \
  --volc-account-id <babi-account-id> --region cn-beijing \
  --bucket demo-bucket --prefix releases/ --limit 50

# 下一页：原样使用同一页返回的两个 marker，保持账号、地域和过滤条件不变
bytedcli volcano tos version list \
  --volc-account-id <babi-account-id> --region cn-beijing \
  --bucket demo-bucket --prefix releases/ --limit 50 \
  --key-marker <next-key-marker> --version-id-marker <next-version-id-marker>
```

- JSON 分别返回 `versions`、`delete_markers` 和 `common_prefixes`；每条版本记录包含 `key`、`version_id`、`is_latest`，对象版本另有大小、ETag 等元信息。
- `current_count` 是本页对象版本与删除标记的数量之和，不是桶中总数；`--delimiter` 产生的每个分组也占用服务端 `--limit` 配额。
- 使用 `has_more` 判断是否还有下一页，不以当前条数判断结束。继续查询时同时保留 `next_key_marker` 与 `next_version_id_marker`；后者为空时可省略，但非空的版本游标必须配合 key 游标。
- 删除标记代表删除事件，没有可下载内容；同一 key 的较早对象版本仍可通过对应 `version_id` 下载。
- `--prefix` 是字符串前缀，不是精确 key 过滤。分层桶不支持历史版本列举。

### 查看对象元信息

```bash
bytedcli volcano tos object get \
  --volc-account-id <babi-account-id> \
  --bucket <bucket> --key path/to/object

# 下载前检查指定历史版本的大小、ETag 和修改时间
bytedcli volcano tos object get \
  --volc-account-id <babi-account-id> --region cn-beijing \
  --bucket demo-bucket --key releases/demo.zip --version-id <version-id>
```

元信息查询使用 HEAD，不下载对象内容。省略 `--version-id` 时查询当前版本；版本号按不透明字符串原样传递，包括字面值 `null`。结果中的 `version_id` 来自服务端响应头，缺失时为 JSON `null`。指定版本不存在、权限不足或服务端拒绝读取删除标记时，直接返回错误，不会回退查询当前版本；服务端明确返回不同版本号时也会报错。

### 下载对象

```bash
bytedcli volcano tos object download \
  --volc-account-id <babi-account-id> \
  --bucket <bucket> --key path/to/object --output ./local-file
# 下载指定历史版本；省略 --version-id 时下载当前版本
bytedcli volcano tos object download \
  --volc-account-id <babi-account-id> --region cn-beijing \
  --bucket demo-bucket --key releases/demo.zip \
  --version-id <version-id> --output ./demo.previous.zip

# 不传 --output 时按对象 key 的 basename 落到当前目录
# 目标文件已存在时默认拒绝覆盖，需显式加 --force 才会覆盖
```

版本号按不透明字符串原样传递，包括字面值 `null`。下载结果的 `version_id` 来自服务端响应头；服务端未返回该头时为 JSON `null`。版本不存在、权限不足或选中删除标记时会失败，不会退回下载当前版本。若服务端明确返回了不同的版本号，也会拒绝落盘。

下载复用流式临时文件、长度及适用的 ETag 校验。归档、冷归档和深度冷归档对象需先恢复后才能下载；软链接版本固定的是软链接本身，其内容仍由服务端解析目标对象。

## 参数说明

| 参数                                                          | 说明                                                                |
| ------------------------------------------------------------- | ------------------------------------------------------------------- |
| `--volc-account-id <id>`                                      | Babi 火山账号 ID，用于 SSO session 鉴权（推荐）                     |
| `--access-key-id` / `--secret-access-key` / `--session-token` | AK/SK 鉴权，缺省按组读取 `VOLC_*` 或 `VOLCENGINE_*` 环境变量                              |
| `--region <region>`                                           | 签名 region；volc 默认 `cn-beijing`，byteplus 默认 `ap-southeast-1` |
| `--host <host>`                                               | 覆盖官方 endpoint host（默认按 region + 平台推导）                  |
| `--bucket <bucket>`                                           | 目标 bucket（object 子命令必填）                                    |
| `--prefix` / `--delimiter` / `--page-size` / `--page-token`   | 对象列举的过滤、分组、分页                                          |
| `--limit <n>` | 历史版本列表的单页上限，默认 20，范围 1–1000 |
| `--key-marker` / `--version-id-marker` | 历史版本列表的双游标，原样使用上一页返回值 |
| `--version-id <id>` | 查询指定历史版本元信息（get）或下载指定历史版本（download）；省略时使用当前版本 |
| `--key <key>`                                                 | 对象 key（get / download 必填）                                     |
| `--output <path>`                                             | 下载落盘路径（download 可选）                                       |
| `--force`                                                     | 下载时覆盖已存在的本地文件（默认拒绝覆盖）                          |

## Notes

- 结构化输出加全局 `--json`（放在子命令之前）。
- 不同平台/region 的 bucket 需匹配对应 endpoint，跨 region 访问必须显式传 `--region`；自定义 endpoint 时同时传 `--host`。
