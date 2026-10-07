---
name: bytedance-kefu
description: "Operate ByteDance kefu (kefu.bytedance.net) — the unified user-feedback console — via bytedcli. Use when tasks mention kefu, 客服反馈, 标签搜索, new_search, 反馈列表分页, feedback_list_single, 用户反馈附件, 草稿 ZIP, 反馈截图, 反馈录屏, ab_settings_download, 草稿 tos, 录屏 tos, 反馈链接排查, draft_download, video_download, slardar crash log 链接, alog 链接, 或 paste a `https://kefu.bytedance.net/united/feedback/feedback_list_single/<product_type>?ids=<id>` URL."
---

# bytedcli kefu

`kefu.bytedance.net` 是字节统一的用户反馈控制台（剪映、剪映专业版、CapCut 等多款产品在用）。`kefu feedback get` 默认只取轻量反馈行；加 `--assets` 时会把控制台两条核心私有接口（`get_feedback_list` + `get_full_extra_form`）合并成排障资产视图，并把所有可消费的远端 URL 都暴露在结构化 JSON 里。下载/解压/OCR 等文件 I/O 不在 CLI 范畴，由本 skill 或上游 skill 自行编排。

## 何时使用

- 收到 kefu 反馈链接（`feedback_list_single/<product_type>?ids=<id>`）需要排查问题。
- 按 `new_search` 页面的标签和时间筛选反馈列表，再用 DID/UID 与反馈时间关联用户行为或日志。
- 拿到 `feedback_id`、需要补全设备/版本/AB 配置/草稿/录屏/截图/Slardar 诊断链接。
- 需要消费 Slardar crash log、ALog、Vega 草稿、用户录屏、AB 配置 ZIP 等远端附件。

## 命令

```bash
# 按标签搜索一页；示例 ID 均为占位值，替换为目标控制台 URL 中的值
bytedcli --json kefu feedback search --product-type 123 --label1-id 101 --label2-id 201 --label3-id 301 --start '2026-01-01 00:00:00' --end '2026-01-02 00:00:00'

# 指定下一页，或从第一页自动遍历
bytedcli --json kefu feedback search --product-type 123 --label1-id 101 --start '2026-01-01 00:00:00' --end '2026-01-02 00:00:00' --page 2 --page-size 100
bytedcli --json kefu feedback search --product-type 123 --label1-id 101,102 --start '2026-01-01 00:00:00' --end '2026-01-02 00:00:00' --all

# 轻量反馈详情（默认 product_type=69 剪映移动端）
bytedcli --json kefu feedback get --id 1956513378

# 单 id 取整套反馈排障资产
bytedcli --json kefu feedback get --id 1956513378 --assets

# 用可读 alias 指定产品线：69=剪映移动端，138=剪映专业版
bytedcli --json kefu feedback get --id 1956513378 --product jianying-mobile --assets
bytedcli --json kefu feedback get --id 2032330537 --product jianying-pro --assets

# 直接贴控制台 URL，自动从 path 解析 product_type、从 query 解析 ids
bytedcli --json kefu feedback get --url "https://kefu.bytedance.net/united/feedback/feedback_list_single/138?ids=2032330537" --assets

# 复制粘贴变形容错：重复 `?` 也能正确解析（去重保留首个 id）
bytedcli --json kefu feedback get --url "https://kefu.bytedance.net/united/feedback/feedback_list_single/138?ids=2032330537?ids=2032330537" --assets

# 显式指定 product_type
bytedcli --json kefu feedback get --id 1956513378 --product-type 69 --assets

# 检查本地 cookie 缓存
bytedcli kefu auth status
bytedcli --json kefu auth status

# 使用 bytedcli 已保存的 BDSSO 会话，通过纯 HTTP 显式登录 kefu
bytedcli kefu auth login
bytedcli --json kefu auth login
```

> `--assets` 是单 id 设计：批量诊断请在外层 shell/Node 里循环调用。未加 `--assets` 的轻量反馈查询可接受多个 id。

## 输出结构（JSON）

`bytedcli --json kefu feedback get --assets` 返回扁平 `KefuAssetsResult`，字段分组：

| 分组 | 字段 |
|------|------|
| 标识 | `feedback_id`、`product_type`、`product`、`link`、`uid`、`did`、`install_id` |
| 设备/版本 | `app_version`、`update_version_code`、`channel`、`language`、`device`、`os_version`、`platform`、`network_type`、`ip`、`city`、`create_time` |
| 反馈正文 | `content`、`comment` |
| extra-form | `resolution`、`dpi`、`oaid`、`openudid`、`uuid`、`cdid`、`ab_settings_tos_key`、`image_ocr_text` |
| 截图/录屏 | `images: string[]`（CDN URL）、`videos: { url, duration_ms, size_bytes, raw }[]`（`raw` 保留接口原始 record，给需要额外字段的 skill 兜底） |
| 远端附件 | `links.{draft_download, ab_settings_download, video_download, cloud_database_download, setting_url, data_model_url, alog_url, crash_log_url, monitor_url, action_url, fabric_url, north_star_url, video_history_url}` |
| 多端扩展 | `custom_links: { name, en_name, url }[]`（PC 端常见 `Mac端crashlog`/`Win端crashlog`/`ALog_Mac`/`ALog_Win`） |
| 原始数据 | `extra_form_raw`（key/value map）、`row_raw`（接口原始 row） |

> 字段为空时取 `null`/`[]`；`links` 始终返回固定字段集，缺失链接用 `null` 占位。

## 标签搜索与分页

- `feedback search` 必须显式指定 `--product-type` 或 `--product`、`--start`、`--end`，以及至少一级标签 ID。`--product` 优先于 `--product-type`；搜索不沿用详情命令的默认产品，避免查错产品。
- 标签 ID 从控制台 URL 的 `label1_ids` / `label2_ids` / `label3_ids` 获取；每个 flag 支持重复或逗号分隔。不把标签名称猜成 ID，也不自动查询其他产品。
- `--channel-type` 为 `online`（默认，线上）、`internal`（内测）、`gray`（灰度）。
- 时间接受控制台时区的 `YYYY-MM-DD HH:mm:ss`，原样发送；不依赖运行机器时区、不猜测转换为 UTC。统计图和反馈列表的时间范围相互独立，使用列表范围。
- 默认 `--page 1 --page-size 50`，页大小支持 `50 / 100 / 200 / 500`。`--all` 从第一页顺序遍历，不能与 `--page > 1` 同用。
- CLI 按控制台已观察到的 10000 条窗口保守限制翻页；不是对后端无限分页的承诺。达到窗口、异常短页/空页、重复反馈 ID 或翻页期间总数变化时，返回 `truncated=true` 和 `truncation_reason`，不要把部分结果当全量。缩小时间范围或标签后重查。
- JSON 的 `data.feedbacks[]` 保留现有 snake_case 字段风格，新增 `app_id`、`label1/2/3`、`latest_active_user_id`、`session_id`、`op_time`、`admin_user`、`rd_comment`，并保留每条原始 `raw` 和可回看的 `link`。ID 按字符串输出；上游若给出超出安全整数范围的数值 ID，报解析错误，避免传播已舍入的 ID。
- 分页元数据包含 `total`、`page`、`page_size`、`pages_fetched`、`last_page`、`next_page`、`has_more`、`complete`、`truncated`、`truncation_reason`、`limit`。单页有后续结果时 `has_more=true`，但 `truncated=false`；`complete=true` 仅表示从第一页读完本次观察到的结果，不代表服务端快照一致性。
- 关联排障使用 `device_id` / `user_id` / `create_time`，不要用 `latest_active_user_id` 或“做表时间” `op_time` 替代。反馈提交时间不等于故障发生时间；TEA project 和身份口径需另行确认，`app_id` 不能当 TEA project ID。
- 搜索不逐条获取附件/诊断链接、不创建异步导出任务、不发送飞书消息。需要选中反馈的详细资产时，再按 ID 调 `feedback get --assets`。

## 消费远端附件的推荐流程

CLI 只负责给链接，下面这些远端附件由 skill / Agent 自己 fetch / unzip / 调下游工具消费：

### 1. Slardar crash log（`links.crash_log_url`、`custom_links.Mac端crashlog`、`custom_links.Win端crashlog`）

链接形如 `https://slardar.bytedance.net/node/app_detail/?aid=...&os=Android#/abnormal/...`（或 `pc_detail/logQuery_v2`）。直接转交 `bytedance-slardar`：

```bash
# Android / iOS 客户端 crash issue（复用 kefu feedback get --assets 拿到的 crash_log_url）
bytedcli --json slardar app issue log --symbolicate --url "<crash_log_url>"

# PC 端（Mac/Win）crash log：URL 走 pc_detail/logQuery_v2，使用直接 PC 日志接口
bytedcli --json slardar pc log list --url "<custom_links.Mac端crashlog>"
```

> 若 PC URL 未携带 `search_type/search_key`，再显式补 `--uid <uid>` 或 `--did <did>`；两者只能选一个。

> PC 日志认证由 URL host 决定 control plane。若返回 401，请执行错误里的 `auth_command`（例如 ROW 为 `bytedcli --site i18n-tt auth login`）后重试；不要把 URL 的数据 region 当作登录 site。

### 2. ALog（`links.alog_url`、`custom_links.ALog_Mac`、`custom_links.ALog_Win`）

链接形如 `#/track/logSearch/logs?...`。直接交给 Slardar App 文件搜索/下载/解密：

```bash
# 列出该 device + 时间窗内的 ALog 文件
bytedcli --json slardar app file list --url "<alog_url>"

# 全量下载到本地目录
bytedcli slardar app file download --all --url "<alog_url>" --output ./alogs

# 加密 ALog zip 解密成 txt
bytedcli slardar app log decrypt --aid <aid> --os Android --input ./encrypted.zip --output ./decrypted.txt
```

### 3. Vega/CapCut 草稿 ZIP（`links.draft_download`）

链接形如 `http://p-pc-feedback-draft.bytedance.net/tos-cn-i-m2uu4xaej5/<key>` 或 `https://lf-feedback-draft.byteoversea.com/...`。直接 GET 落盘，再按业务自行解包：

```bash
DRAFT_URL=$(bytedcli --json kefu feedback get --id 2032330537 --assets | jq -r '.data.links.draft_download')
curl -fsSL -o /tmp/draft.zip "$DRAFT_URL"
unzip -d /tmp/draft /tmp/draft.zip
# 后续把 draft 解包结果交给客户端工具（Android: faceu-android/vega；iOS: faceu-ios/iMovie；PC: 剪映专业版）继续分析
```

> 注意：草稿 ZIP 仅在用户主动选择"上传草稿"时才存在；很多反馈没有这条链接。

### 4. 用户录屏（`links.video_download`、`videos[]`）

- `videos[]` 是反馈正文里的录屏，每条带 `url`/`duration_ms`/`size_bytes`，`url` 通常是 CDN 直链；
- `links.video_download` 是平台聚合的"诊断视频"链接，跳转到 `cloud.bytedance.net/vod/diagnostic_tools/video_info/...`（需要登录 cloud 控制台后下载）。

```bash
# 用户主动上传的录屏
URL=$(bytedcli --json kefu feedback get --id <id> --assets | jq -r '.data.videos[0].url')
curl -fsSL -o /tmp/feedback.mp4 "$URL"
```

### 5. AB 配置 ZIP（`links.ab_settings_download`）

下载并解压后即可获得当前用户在客户端实际命中的全部 AB 配置（剪映 Android 一般 1700+ 项）：

```bash
AB_URL=$(bytedcli --json kefu feedback get --id <id> --assets | jq -r '.data.links.ab_settings_download')
curl -fsSL -o /tmp/ab.zip "$AB_URL"
unzip -d /tmp/ab /tmp/ab.zip
# 在解包目录里 grep 你关心的 key，例如：
grep -R "import_live_photo" /tmp/ab
```

> iOS / PC 端反馈通常没有 `ab_settings_download`；这是上游接口本身就为空，不是 CLI 漏抓。

### 6. AppSettings / 数据模型 / 行为日志（其他 `links.*`）

| 字段 | 含义 | 消费方式 |
|------|------|----------|
| `setting_url` | AppSettings 后台 report | 直接在浏览器打开（cloud.bytedance.net 控制台） |
| `data_model_url` | 媒资模型 / 视频解码诊断 | 浏览器打开 |
| `action_url` | Tea 用户行为时间线 | 浏览器打开（data.bytedance.net） |
| `monitor_url` | Slardar Monitor / Track | 见上文 ALog/Slardar |
| `north_star_url` | 北极星营销 / Luckycat 任务 | 浏览器打开 |
| `video_history_url` | VOD 视频历史 | 浏览器打开 |
| `fabric_url` / `cloud_database_download` | 云配置/云数据库导出 | curl 下载或浏览器打开 |

CLI 只输出链接、不打开浏览器；用户/Agent 按需消费。

## 与 VOC 的关系

`bytedance-voc` 走的是抖音 CEM 平台（`voc.bytedance.net`），主要面向"标签 + 情感分析"。`bytedance-kefu` 走的是统一客服平台（`kefu.bytedance.net`），主要面向"客户端调试附件"。两者的反馈 id 经常是同一个，但接口与登录态完全独立：

- 想要 ES doc / issue 标签 / 三级问题分类：用 `bytedance-voc`。
- 想要 AB 配置 ZIP / Slardar crash 链接 / ALog / 草稿 / 录屏：用 `bytedance-kefu`。

## 认证

- 认证查找顺序：① 本地 6h 缓存 `~/.local/share/bytedcli/data/kefu_session.json` → ② 本机 Chromium cookie 库（Chrome / Chrome Beta / Chromium / Vivaldi）的 `kefu.bytedance.net` host-scoped cookie + `.bytedance.net` apex SSO cookie → ③ SSO fallback：headless puppeteer + `sso_session.json` 走一次 SSO 重定向，由 kefu 后端现场颁发 `SHARE_SESSION_ID`。
- `bytedcli kefu auth login` 是显式的纯 HTTP 登录入口：读取 bytedcli 已保存的 `sso_session.json`，完成 MPSSO OAuth、ticket 交换和 kefu `/sso_login`，再调用 kefu API 验证会话后写入缓存。该命令不启动 Chrome，也不读取本机浏览器 Cookie。
- `kefu auth login` 可能使同一身份的其他活跃 kefu 会话失效。仅在明确需要新建登录态时调用；普通查询仍优先复用缓存和本机浏览器 Cookie，不会隐式调用该命令。
- 跨机器迁移（`bytedcli auth export` / `auth import`）会携带 `sso_session.json` 与 `kefu_session.json`。如果导入后的 `SHARE_SESSION_ID` 被业务接口拒绝，CLI 会优先用 SSO fallback 现场换一枚新的 kefu cookie，再重试一次请求。
- 新版搜索在正常 SSO 会话下调用平台 `get_secret` 初始化，secret 仅存于进程内并随 Cookie 更新；不要求用户提供 Cookie/Token。HTTP 或业务 `401` 最多刷新并重试一次，`403` 不重试；搜索请求及响应正文不进入 HTTP trace。
- `bytedcli kefu auth status` 可看缓存路径与剩余有效期；删除缓存文件即强制刷新（不会触发 puppeteer，仅清缓存）。
- 与 `bytedance-voc` 的 cookie/缓存完全独立，不会互相污染。

## 错误与排查

- `KEFU_AUTH_REQUIRED` — 缓存、本地浏览器 cookie、SSO fallback 三条路径都没拿到 `SHARE_SESSION_ID`。打开 `https://kefu.bytedance.net` 在 Chrome 登录一次；或迁移机器场景下确认已跑过 `bytedcli auth import`、SSO 未过期，再重试。
- `KEFU_HTTP_SSO_REQUIRED` — `kefu auth login` 找不到可复用的 BDSSO 会话。先运行 `bytedcli auth login --session`，再重试。
- `KEFU_HTTP_LOGIN_FAILED` — 纯 HTTP 登录链路、ticket 交换或 kefu API 探活失败。不要把失败结果写入缓存；检查 SSO 会话和网络后重试。
- `KEFU_PUPPETEER_NOT_FOUND` — SSO fallback 需要的 puppeteer 可选依赖没装（bytedcli 声明为 optional peer，不随安装拉取）。运行 `npm install -g puppeteer-core@24` 后重试。
- `KEFU_CHROME_NOT_FOUND` — SSO fallback 找不到系统 Chrome 可执行文件（bytedcli 不下载 bundled Chromium）。先安装 Google Chrome / Chromium 到系统标准路径再重试。
- `KEFU_INPUT_ERROR` — `--id` 必须是纯数字，URL 必须是 `feedback_list_single/<product_type>?ids=<id>` 形态。
- `KEFU_ASSETS_SINGLE_ID_REQUIRED` — `kefu feedback get --assets` 仅支持单 id；批量请在外层循环调用。
- `KEFU_NOT_FOUND` — 指定 product_type 下查不到该 feedback id（多半是 product_type 错了，剪映移动端 = 69，剪映专业版 = 138，CapCut 等其他业务请看控制台 URL path）。

## 调用约定

`bytedcli` 的安装与执行方式参考 `../../invocation.md`。所有示例默认全局安装后直接 `bytedcli ...`；npx 形态请把 `bytedcli` 替换成 `NPM_CONFIG_REGISTRY=http://bnpm.byted.org npx -y @bytedance-dev/bytedcli@latest`。

## Out of scope

- 不实现下载、解压、OCR、视频抽帧、AB 配置 grep（这些副作用属于上层 skill / Agent）。
- 不暴露写操作（标签、状态机、回复用户）。
- 内置的产品 alias 只覆盖常用剪映线：`jianying-mobile`/`lv-mobile`/`jianying`/`lv` = 69，`jianying-pro`/`lv-pro`/`jianying-pc`/`lv-pc` = 138；其他业务沿用控制台 URL 中的数字。
