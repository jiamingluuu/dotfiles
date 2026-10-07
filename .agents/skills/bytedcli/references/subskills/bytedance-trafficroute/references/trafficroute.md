# TrafficRoute

TrafficRoute 相关能力覆盖 `privatezone` 和 `dns` 子域。

## 命令映射

- `trafficroute privatezone resolver-endpoint list`：按账号查询 resolver endpoint，支持 `--resolver-id` / `--name` / `--vpc-id`
- `trafficroute privatezone resolver-rule list`：按账号查询 resolver rule，支持 `--name` / `--endpoint-id`
- `trafficroute privatezone zone list`：按 `--account-id` / `--z-id` / `--domain` 查询 zone，支持分页
- `trafficroute privatezone record list`：按 `--z-id` 查询 record，支持可选 `--account-id` 和分页
- `trafficroute dns zone list`：按 `--account-id` / `--z-id` / `--domain` / `--trade-code` / `--stage` 查询云解析DNS zone，支持分页
- `trafficroute dns record list`：按 `--z-id` 查询云解析DNS record，支持分页

## 认证约定

- TrafficRoute 直连 TIAGW（Traffic Infrastructure API Gateway，流量基础设施网关），认证走通用 ByteCloud JWT（JSON Web Token，云账号访问令牌，与 tcc/tce 等一致）。privatezone 与 dns 共用同一套认证，无需区分 context。
- 先看登录态：

```bash
bytedcli --json auth status
```

- 缺认证时再执行：

```bash
bytedcli auth login
```

- 也可注入现成 ByteCloud JWT（含服务账号换取的 JWT）：`export BYTEDCLI_USER_CLOUD_JWT=<jwt>`；受管运行时也可能注入 `AIME_USER_CLOUD_JWT`。
- 若业务命令返回 401 / Unauthorized，先检查是否设置了 `BYTEDCLI_USER_CLOUD_JWT` 或 `AIME_USER_CLOUD_JWT`。显式 JWT 优先级高于本地登录态，过期 JWT 会导致 `auth status` 显示 ready 但 TrafficRoute 请求仍失败。可先 `unset BYTEDCLI_USER_CLOUD_JWT AIME_USER_CLOUD_JWT`，再执行 `bytedcli auth status --force-refresh` 或 `bytedcli auth login` 后重试。

## 查询语义

### zone list

- `--account-id`：按账号过滤
- `--domain`：按域名关键字过滤
- `--z-id`：按 zone id 精确查询
- `--page` / `--page-size`：分页

行为要点：

- 域名关键字查询默认按页面语义走 `SearchMode=like`
- 传入 `--z-id` 时，CLI 会走精确查询路径，并返回最准确的绑定 VPC 信息
- 普通列表查询会对当前页 zone 按需补详情请求，以尽量补齐 `bindVpcs`

### record list

- `--z-id` 必填
- `--account-id` 可选
- `--page` / `--page-size` 可用

行为要点：

- 后端返回是 `SubDomains[].Records[]`
- CLI 会把它展平成单条 record 行，方便文本展示和 JSON 消费

### dns zone list

- `--account-id` / `--z-id` / `--domain` / `--trade-code` / `--stage` / `--page` / `--page-size`
- `--account-id`：按账号过滤，透传为上游 `AccountID=<id>`
- `--stage` 使用语义值：`normal` / `needs-recovery` / `not-using-trafficroute` / `abnormal` / `change-dns`
- 文本模式顶部的 `DNS Zones Query` 是查询条件和分页摘要，不是结果字段

### dns record list

- `--z-id` 必填
- `--page` / `--page-size` 可用
- 后端返回是 `SubDomains[].Records[]`，CLI 会展平成单条 record 行

### resolver-endpoint list

- `--account-id` 必填
- 支持 `--resolver-id` / `--name` / `--vpc-id`

### resolver-rule list

- `--account-id` 必填
- 支持 `--name` / `--endpoint-id`
- 当前 list-rules 结果是 OUTBOUND 规则

## 推荐示例

```bash
# zone 列表
bytedcli trafficroute privatezone zone list --account-id demo-account-id --page 1 --page-size 20

# 精确查询某个 zone
bytedcli trafficroute privatezone zone list --z-id demo-zone-id

# 查询某个 zone 下的 record
bytedcli trafficroute privatezone record list --z-id demo-zone-id

# 查询云解析DNS zone
bytedcli trafficroute dns zone list --account-id demo-account-id --domain "demo.example.com" --stage change-dns

# 查询云解析DNS record
bytedcli trafficroute dns record list --z-id demo-zone-id

# 查询 resolver endpoint
bytedcli trafficroute privatezone resolver-endpoint list --account-id demo-account-id --name "demo-resolver"

# 查询 resolver rule
bytedcli trafficroute privatezone resolver-rule list --account-id demo-account-id --endpoint-id demo-endpoint-id
```

## 使用建议

- 用户只说“TrafficRoute / PrivateZone / 私有域名 / Resolver / zone / record”时，优先路由到这个 skill
- 用户如果贴的是 TrafficRoute 控制台场景，先判断他要的是：
  - 认证排障
  - resolver endpoint/rule 查询
  - privatezone zone/record 查询
  - dns zone/record 查询
- 当用户想确认绑定 VPC 是否准确时，优先建议直接用 `--z-id`
