# SIP（智能运维平台）

SIP 是一个承载多个**独立子平台**的平台，不同子平台技术栈、后端接口、认证方式都不同。使用前先按下表选对子平台，**不要混用二者的命令、参数或认证**：

| 子平台 | 命令前缀 | 定位 | 后端接口 | 认证栈 |
| --- | --- | --- | --- | --- |
| 事件查询 | `sip event` | 只读查询线上稳定性事件（LIBRA / Demotion / TCE / Release / recall_center） | `/api/v1/assistant/event/*` | 自签 JWT（`token:` header），支持 `BYTEDCLI_SIP_TOKEN` 覆盖 |
| 智能发布平台 | `sip release` | 一整个发布管理子平台；当前已暴露的子功能是代码库锁定 / 解锁（`repo lock` / `repo unlock`）与调度定时任务暂停 / 恢复（`cron pause` / `cron resume`），后续会有更多发布相关子功能 | `/api/v1/assistant/release/*` | SSO CAS cookie（经 `/cas/login` 换同源会话），**不吃** `BYTEDCLI_SIP_TOKEN` |

对应 UI：

- CN: <https://sip.bytedance.net/stability/event>
- SG: <https://sip-sg.byteintl.net/stability/event>
- TikTok ROW: <https://sip.tiktok-row.net/stability/event>

## 命令总览

```bash
bytedcli sip event list [options]                  # 事件查询：时间窗口内列事件
bytedcli sip event get --id <event_id>             # 事件查询：单个事件详情
bytedcli sip release repo lock --psm-id <id> ...    # 智能发布平台：锁定代码库（禁止合码）
bytedcli sip release repo unlock --psm-id <id> ...  # 智能发布平台：解锁代码库（放开合码）
bytedcli sip release cron pause --job-id <id> --psm <psm>   # 智能发布平台：暂停调度定时任务
bytedcli sip release cron resume --job-id <id> --psm <psm>  # 智能发布平台：恢复调度定时任务
```

`sip` / `sip event` / `sip release` / `sip release repo` / `sip release cron` 不带子命令时打印帮助。`sip release` 是一个会持续扩子功能的子平台，`repo lock` / `repo unlock` 与 `cron pause` / `cron resume` 是它当前的两组子命令。

## `--site` 到 SIP region 的映射（两个子平台共用）

| `--site` | SIP 后端 |
|---|---|
| `cn` / `boe` | `https://sip.bytedance.net`(Douyin / Toutiao / ...) |
| `i18n` / `i18n-bd` | `https://sip-sg.byteintl.net`(ByteIntl SG) |
| `i18n-tt` / `us-ttp` / `us-*` / `eu-ttp` | `https://sip.tiktok-row.net`(TikTok ROW) |

> bytedcli 的全局默认站点是 `--site cn`，所以**不带 `--site` 时命中的是 CN region（`sip.bytedance.net`）**，不是 TikTok ROW。上表里 `row` 只是"非 `cn`/`boe`/`i18n-bd` 站点"的兜底分支，不是 CLI 默认值。要访问 UI 上的 `sip.tiktok-row.net`，必须显式带 `--site i18n-tt`（或其他映射到 `row` 的站点，或 `BYTEDCLI_SIP_REGION=row`）。

也可以用 `BYTEDCLI_SIP_REGION=cn|sg|row` 或 `BYTEDCLI_SIP_BASE_URL=https://...` 显式覆盖。

---

# 子平台一：事件查询 `sip event`

只读查询线上稳定性事件，走事件平台接口 `/api/v1/assistant/event/*`，认证用自签 JWT。

## `sip event list`

在时间窗口内查询 SIP 事件列表。默认 30 分钟窗口、全部 4 个 region、`--biz tiktok_feeds`(对应 SIP UI 的 product tab,filter 从 `/product` 动态抓)。

| 参数 | 默认 | 说明 |
|------|------|------|
| `--duration <dur>` | `30m` | 相对时间窗口（`15m`/`1h`/`24h`），`--start` 存在时忽略 |
| `--start <time>` | — | 绝对起始时间（ISO 8601、epoch ms、或 `-1h` 相对偏移） |
| `--end <time>` | `now` | 绝对结束时间 |
| `--region <r>` | `SG,GCP,VA,TTP` | region / vdc，可重复。别名自动归一：`us-ttp→TTP`、`sg1→SG`、`va1→VA` |
| `--biz <biz>` | `tiktok_feeds` | Product line,对应 SIP UI 顶部的 product tab(`tiktok_feeds` / `tiktok_live` / ...)。bytedcli 启动时自动调 `/product` 接口抓取对应产品的 `product_config`,展开成过滤树,和 UI 点击 product tab 等价 |
| `--filter <json>` | 从 `--biz` 自动推导 | 服务端过滤树 JSON,显式传时**原样覆盖** `--biz` 的默认值。SIP 后端要求至少一个过滤字段,否则返回空 |
| `--category <cat>` | — | 客户端子串过滤 `category`：`LIBRA`/`Demotion`/`TCE`/`Release` |
| `--keyword <kw>` | — | 关键字（映射为 `main_search`） |
| `--page-no <n>` | `1` | 页码 |
| `--page-size <n>` | `12` | 每页条数 |
| `--mode <m>` | `card` | `card`（主卡片视图）或 `simple`（时间线简表） |

### 过滤树示例

从 `https://sip.tiktok-row.net/api/v1/assistant/event/product` 返回的 `product_config` 可以看到完整字段。bytedcli `--biz <name>` 默认会自动把对应产品的整份 config 展开,和 UI 点顶部 product tab 一致;只有需要更细粒度过滤时才手动传 `--filter`:

```jsonc
// 仅 LIBRA 实验变更（TikTok 主 app）— 覆盖 --biz 的全量配置
{"libra": {"app": ["TikTok"]}}

// Demotion 事件
{"holmes_demotion": {"status": ["启用", "执行", "结束"]}}

// TCE 变更
{"tce": {"status": ["upgrade", "update", "rollback_ticket"]}}

// Release 变更
{"release": {"type": ["abonly", "reversalab", "ab", "noab"]}}

// recall_center
{"recall_center": {"status": ["小流量发布", "全量发布"]}}
```

可以组合多个子树，对应 UI 里多个 section 同时勾选。

### 输出

- **文本模式**：表格列 `ID / Category / Name / Product / Region / PSM / Creator`。标题栏会显示 `返回数 / 总数`。
- **JSON 模式**：`data.events[]` 为扁平化后的卡片字段，`data.raw.list[]` 保留后端原始响应，`data.total_count` 是过滤前的总数，`data.returned` 是本地 category 过滤之后的条数。

## `sip event get`

```bash
bytedcli --site i18n-tt sip event get --id <event_id>
```

`--id` 必填，对应 `card_list` 返回里的 `id`（LIBRA flight ID、Demotion job ID 等）。响应字段会同时兼容 `{value}` 包装和扁平两种格式。

## 认证（`sip event`）

默认零交互:bytedcli 自动用当前 SSO 身份换取事件平台的自签 JWT(`token:` header),不需要任何配置。

```bash
bytedcli --site i18n-tt sip event list --duration 1h
```

> 认证按 SSO 环境隔离：`row`（`i18n-tt` / `eu-ttp`，TikTok SSO）与 `cn` / `sg`（ByteDance SSO）互相独立。首次使用某个 site 前，先确认目标 site 的登录态，只有顶层 `authenticated` 为 `false` 时才 `auth login`（别对已登录的 site 重复扫码；请以顶层 `authenticated` 为准，不要 grep 嵌套 `bytecloud_auth_sdk.status` 里的 `need_login`，那会漏掉 JWT override / session cache 场景）：
>
> ```bash
> BYTEDCLI_CLOUD_SITE=i18n-tt bytedcli --json auth status
> BYTEDCLI_CLOUD_SITE=i18n-tt bytedcli auth login   # 仅当上面顶层 authenticated 为 false
> ```

CI / agent 场景下如果要跳过自动鉴权,可用 `BYTEDCLI_SIP_TOKEN` 传入已准备好的 token:

```bash
export BYTEDCLI_SIP_TOKEN='eyJhbGci...'
bytedcli --site i18n-tt sip event list --duration 1h
```

> 注意：`BYTEDCLI_SIP_TOKEN` 只对 `sip event` 生效，对 `sip release` 无效。

## 常见使用姿势（`sip event`）

**根因分析 / 告警回溯**：告警发生在 `2026-04-14 14:30 TTP`，反查前 30 分钟的所有变更：

```bash
bytedcli --site i18n-tt sip event list \
  --start 2026-04-14T14:00:00+08:00 \
  --end   2026-04-14T14:30:00+08:00 \
  --region us-ttp \
  --filter '{"libra":{"app":["TikTok"]},"tce":{"status":["upgrade","update"]},"holmes_demotion":{"status":["启用","执行"]}}'
```

**每日事件概览**：最近 24h 的 LIBRA + Demotion：

```bash
bytedcli --json --site i18n-tt sip event list --duration 24h --page-size 50 \
  --filter '{"libra":{"app":["TikTok"]},"holmes_demotion":{"status":["启用","执行","结束"]}}'
```

**快速定位某个实验的变更链**：

```bash
bytedcli --site i18n-tt sip event list --duration 7d --keyword "admix_my_lry"
```

## 常见错误（`sip event`）

- `SIP token sign endpoint returned an unexpected response` → SIP 的 JWT 签发端点 `/api/v1/sip/base_common/jwt_token/` 返回异常。用 `bytedcli auth userinfo` 确认当前 SSO username 是否有效
- `Could not determine SIP username` → `auth.userinfo()` 拿不到 username。先跑 `bytedcli auth login`
- `SIP API authentication failed: need login with sso` / HTTP 401 → 签发端点拿到的 token 被 SIP gateway 拒绝(罕见,比如 username 在该 region 无效)。换 region 或换账号再试;也可以 `export BYTEDCLI_SIP_TOKEN='<jwt>'` 传一个已知有效的 JWT
- HTTP 500 `KeyError: 'vdc'` → SIP 后端要求 `vdc` 必须非空数组。bytedcli 默认传 `["SG","GCP","VA","TTP"]`;如果你显式传 `--region` 但值全部无法识别,归一化后可能为空,改用默认或合法值(`us-ttp`/`sg`/`va`/`gcp`/`ttp`/`cn`)
- 返回 `events: []` 但 UI 里能看到事件 → SIP 后端只在至少一个产品过滤字段存在时才返回结果。默认 `--biz tiktok_feeds`(TikTok ROW)会自动从 `/product` 拉整份 product_config 展开;在 CN region 要改用 `--biz aweme` / `--biz toutiao` 等。如果被 `--filter` 收紧过或 `biz_matched=false`,可以去掉 `--filter` 或换 `--biz`
- `--filter is not valid JSON` → 用单引号包整个 JSON,JSON 内部全部用双引号,不要混用或转义:`--filter '{"libra":{"app":["TikTok"]}}'`

---

# 子平台二：智能发布平台 `sip release`

`sip release` 是 SIP 下的**智能发布平台**子平台，负责发布相关的管理能力，走 release 子平台接口 `/api/v1/assistant/release/*`，认证方式与 `sip event` 完全不同（SSO CAS cookie）。这是一个会持续扩子功能的命名空间，**当前已实现的子功能是代码库锁定 / 解锁**（`repo lock` / `repo unlock`）**与调度定时任务暂停 / 恢复**（`cron pause` / `cron resume`），后续会有更多发布相关子命令挂到 `sip release` 下。

## 子功能：代码库锁定 / 解锁 `repo lock` / `repo unlock`

用于**代码封禁期、故障排查期的代码库管理**：锁定后禁止新的 MR 合入 master（可选定向放行指定用户），期满解锁后恢复合码。

底层接口 `POST /api/v1/assistant/release/lock/update_master_ban_status`。一次操作由 `(psm_id, release-type, release-site)` 三元组在服务端定位对应的发布登记，操作人由当前登录身份推导，**不需要也不能在参数里传操作人**。

`repo lock` / `repo unlock` 两个命令共用同一组参数（`repo unlock` 不支持 `--allow-users`）：

| 参数 | 必填 | 默认 | 说明 |
|------|------|------|------|
| `--psm-id <id>` | 是 | — | 发布登记的 PSM ID（正整数） |
| `--release-type <type>` | 否 | `code` | 发布类型：`code`=代码、`config`=配置、`bits`=bits |
| `--release-site <site>` | 否 | `TTP` | 部署 site（如 `TTP`），与全局 `--site` 区分开。**默认 `TTP`，但建议每次都显式写出 `--release-site TTP`，避免与全局 `--site` 混淆、并让 `(psm_id, release-type, release-site)` 三元组一目了然** |
| `--reason <text>` | 否 | — | 操作原因（会展示在 Lark 通知里） |
| `--release-id <id>` | 否 | — | 关联的 release ID |
| `--allow-users <users>` | 否 | — | 仅 `repo lock`：逗号分隔的用户名，仍允许这些人合码（定向锁定） |

### 示例

```bash
# 全量锁定：代码封禁期 / 故障排查期禁止任何新 MR 合入 master
# --release-site 默认 TTP，建议每次都显式写出
bytedcli --site i18n-tt sip release repo lock --psm-id 17 --release-site TTP --reason "code freeze"

# 定向锁定：只放行指定用户
bytedcli --site i18n-tt sip release repo lock --psm-id 17 --release-site TTP --allow-users demo-user1,demo-user2

# 指定发布类型 / 部署 site / 关联 release
bytedcli --site i18n-tt sip release repo lock \
  --psm-id 17 --release-type config --release-site TTP --release-id demo-release-001

# 解锁：封禁 / 排查结束后放开合码（不吃 --allow-users）
bytedcli --site i18n-tt sip release repo unlock --psm-id 17 --release-site TTP

# JSON 输出（agent / 脚本消费）
bytedcli --json --site i18n-tt sip release repo lock --psm-id 17 --release-site TTP
```

### 输出

- **文本模式**：`renderKvTable` 展示 `Status / PSM ID / Type ID / Site / Reason / Release ID / Allow Users`。
- **JSON 模式**：`data` 包含 `status`、`psm_id`、`type_id`、`site`、`reason`、`release_id`、`specified_usernames`，以及 `result`（后端返回的内层业务 envelope）。

## 子功能：调度定时任务暂停 / 恢复 `cron pause` / `cron resume`

用于**暂停 / 恢复发布调度的定时任务（cron job）**：`pause` 停掉定时触发、`resume` 恢复。

底层接口 `POST /api/v1/assistant/release/scheduler/trigger/update_cron_job/`（**尾部斜杠必须保留**：后端路由按函数名反射分发，缺斜杠会 404，区别于锁库端点 `update_master_ban_status` 无尾斜杠）。CLI 动词映射后端数字 `status`：`pause` → `0`、`resume` → `1`（后端还支持 `2` 软删除，CLI 暂不暴露）。

`cron pause` / `cron resume` 共用同一组参数，两者都必填：

| 参数 | 必填 | 说明 |
|------|------|------|
| `--job-id <id>` | 是 | 调度任务 ID（正整数），实际操作的唯一键 |
| `--psm <psm>` | 是 | 完整点分 PSM（如 `demo.recommend.predict_cpp`），**仅用于鉴权**：后端用它解析 `ReleasePsm` 并校验操作人是否在 operator 名单里，不下沉到 cron 逻辑 |

### 示例

```bash
# 暂停调度定时任务
bytedcli --site i18n-tt sip release cron pause --job-id 12345 --psm demo.recommend.predict_cpp

# 恢复调度定时任务
bytedcli --site i18n-tt sip release cron resume --job-id 12345 --psm demo.recommend.predict_cpp

# JSON 输出（agent / 脚本消费）
bytedcli --json --site i18n-tt sip release cron pause --job-id 12345 --psm demo.recommend.predict_cpp
```

### 输出

- **文本模式**：`renderKvTable` 展示 `Action / Job ID / PSM / Status`。
- **JSON 模式**：`data` 包含 `action`、`psm`、`job_id`、`status`，以及 `result`（后端返回的内层业务 envelope）。

## 认证（`sip release`）

智能发布平台走 **SSO CAS 同源会话**：bytedcli 用当前 SSO 登录态经 `/cas/login?next=%2F` 换取 host session cookie，再带 cookie 请求 release 接口。这条链路依赖磁盘上已存在的 **SSO 浏览器会话 cookie jar**，而该 jar **只有 session 登录流程会写入**。因此：

- 必须用 **`bytedcli --site <site> auth login --session`** 建立 / 刷新该 SSO 会话（`--site` 决定 SSO env：`row → tiktok`，`cn / sg → bytedance`，例如 `--site i18n-tt` → `tiktok`）：

  ```bash
  bytedcli --site i18n-tt auth login --session
  ```

- ⚠️ **普通 `bytedcli auth login`（不带 `--session`）走的是 ByteCloud Auth device_code 流程，只写 ByteCloud Auth 凭据，不会生成 CAS 所需的 SSO cookie jar**，因此对 `sip release` 无效——按它登录后 `sip release` 仍会 401。
- **`BYTEDCLI_SIP_TOKEN` 对 `sip release` 无效**——它只用于事件平台的 JWT，不能顶替 CAS 会话。
- 401 时先 `bytedcli auth status` 确认，再 `bytedcli --site <site> auth login --session` 重新登录。

## 常见错误（`sip release`）

- `SIP release lock rejected: <message>` → 后端 release 子平台业务失败。注意：外层网关会返回 `code:0`（看似成功），但内层业务 envelope 的 `code` 才是真结果；bytedcli 已识别这种"假成功"并在内层 `code != 0` 时报错。常见原因是当前身份对该 PSM 没有锁定权限，或 `(psm_id, release-type, release-site)` 三元组没有对应的发布登记
- `SIP API authentication failed: need login with sso` / HTTP 401 → SSO CAS 会话无效或过期。跑 `bytedcli auth status` 确认，再 `bytedcli --site <site> auth login --session` 重新登录；不要用普通 `auth login`（device_code 不写 SSO 会话），也不要用 `BYTEDCLI_SIP_TOKEN` 顶替
- `--psm-id is required` / `--psm-id must be a positive integer` → `--psm-id` 必须传且为正整数
- `--job-id is required` / `--job-id must be a positive integer` → `cron pause` / `cron resume` 的 `--job-id` 必须传且为正整数
- `--psm is required` → `cron pause` / `cron resume` 的 `--psm` 必须传（完整点分 PSM，仅用于鉴权）
