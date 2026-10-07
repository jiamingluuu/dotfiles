---
name: bytedance-holmes
description: "Manage Holmes demotion plan search/list/get, AI Task prompts, TrustPress/TikDiff tasks, TrustData SQL and follow-up registration, TikTok Debug video detail/batch/covers, ByteCore coredump analysis, IndexService proto/record/debug inverted queries, TBase product/config/field/trigger/row-key queries, Archon traffic recording onboarding/dependency upgrades, release checker reports, and code-review ticket info via bytedcli. Invoke for Holmes、demotion、降级预案、AI Task、ai-task、aweme-debug、trust-press、tanker ID、TikDiff、TrustData、sql-submit、annotation_required、table registration、ByteCore、coredump、SIGSEGV、Holmes IndexService、holmes indexservice、proto 查询、record 查询、倒排查询、index_service_inverted、Holmes TBase、holmes tbase、TBase、row key、查字段、新增字段、field list/add/describe/get、trigger list、Archon 流量录制接入、TrustPress 接入、TikDiff 接入、traffic_sinker_lib、dep_graph.blade 依赖核对、release checker、checker report、code-review、ticket-detail."
---

# bytedcli Holmes

## 工具适用场景

- 在本地电脑上使用 bytedcli 访问 CN 和 RoW 的 Holmes 工具
- 在 CN CloudIDE 上使用 bytedcli 访问 CN Holmes 工具
- 暂不支持在 CN CloudIDE 访问 RoW Holmes 工具

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

## Demotion plans (read-only)

Supports `cn`, `i18n-tt`, and `us-ttp`. EU demotion plans are served by `i18n-tt`.
US plan URLs use the US Holmes console host. As in the console, US demotion
API calls use the BDEE backend and its ByteDance CAS session; CN and i18n use
their standard Holmes API origins. If US API authentication is missing, run
`bytedcli --site cn auth login --session` to prepare that ByteDance CAS session.
Use `--region` on the command or global `--site` (default: configured site).
Global `boe` maps to `cn`, `i18n` and EU profiles to `i18n-tt`, and US profiles
to `us-ttp`. Other sites (such as `i18n-bd`) require an explicit `--region`.
`get --url` infers the region from the Holmes URL and overrides the global site;
an explicit conflicting `--region` is rejected. Supply exactly one of `--id` or
`--url`; URLs must be trusted Holmes HTTPS plan links ending in
`/demotion/view-plan/<id>` (legacy `/platform/demotion/view-plan/<id>` also works).

```bash
bytedcli holmes demotion search --region i18n-tt --keyword 'demo-key'
bytedcli holmes demotion list --region cn --psm example.search.rank --page 1 --page-size 20
bytedcli holmes demotion search --region us-ttp --keyword 'demo-plan' --psm example.search.rank
bytedcli holmes demotion get --region us-ttp --id 123 --json
bytedcli holmes demotion get --url '<Holmes plan URL>' --json
```

Search uses the console's server-side keyword matching on plan title, config key,
and plan ID. `--psm` filters the service. Queries include all matching plans,
not just favorites. List and search are paginated (default page 1, page size 20);
JSON returns `plans`, `total`, `page`, `page_size`, `has_more`, and `region`.
Get returns the full plan configuration under `plan`, plus `region` and `url`.
These commands inspect plans; they do not activate or modify demotions.

Authentication reuses the Holmes SSO session. A `need login with bdsso` response
requires session login even if its API code is 0. For CN and i18n, run
`bytedcli --site <region> auth login --session` with the selected region; for US
demotion, run `bytedcli --site cn auth login --session` for the BDEE API session.

## Authentication

**抖音业务线与 TikTok 业务线需要注意区分。**

TrustData 默认使用 i18n ByteCloud JWT，通过 `x-jwt-token` 直接鉴权，无需 Holmes 浏览器 session。CLI 自动获取 i18n JWT；显式设置 `BYTEDCLI_HOLMES_COOKIE` 时优先使用该 Cookie。CN JWT 不适用于 TrustData 的 i18n 后端。

其他 Holmes 能力使用以下浏览器 session 认证。

### 抖音业务线认证

```bash
bytedcli auth login --session
```

扫码完成后，后续命令会自动通过 `sso.bytedance.com` 完成 CAS 认证，无需重复操作。
在 CN CloudIDE 上没有浏览器可用，可以手动复制浏览器 cookie 设置环境变量 `export BYTEDCLI_HOLMES_COOKIE="<cookie>"`。

### TikTok 业务线认证

```bash
bytedcli --site i18n-tt auth login --session --session-method interactive-browser
```

## Site URL

Holmes 主站 API 的 base URL 由全局 `--site` / `BYTEDCLI_CLOUD_SITE` 决定：

| site                     | Holmes API origin                      | CAS host                    |
| ------------------------ | -------------------------------------- | --------------------------- |
| `cn` / `boe`             | `https://holmes.bytedance.net`         | 按站点默认值                |
| `i18n` / `i18n-tt`       | `https://holmes.tiktok-row.net`        | 按站点默认值                |
| `i18n-bd`                | `https://holmes-i18n.sinf.net`         | 按站点默认值                |
| `us-ttp` / `us-ttp-usts` | `https://holmes-ttp-us.tiktok-row.net` | 按站点默认值                |
| `us-ttp-bdee`            | `https://holmes-bdee.tiktok-us.net`    | `https://sso.bytedance.com` |
| `eu-ttp`                 | `https://holmes-eu.tiktok-row.net`     | 按站点默认值                |

访问 US/EU TTP Holmes 主站能力时显式传对应 `--site`；不要手工拼写或覆盖 base URL。`us-ttp-bdee` 的普通 Holmes/IndexService API 使用 `aid=1749`、ByteDance CAS，且不携带 `is_ttp=1`。TrustData 查询固定使用 i18n Holmes 后端。

TBase 查询由 `holmes tbase --region` 独立决定业务区域，且页面入口、API origin、CAS host 是三套不同概念：

| TBase region | 页面入口                                                     | API origin                          | CAS host                      |
| ------------ | ------------------------------------------------------------ | ----------------------------------- | ----------------------------- |
| `cn`         | `https://holmes.bytedance.net/tbase/home?region=cn`          | `https://holmes.bytedance.net`      | `https://sso.bytedance.com`   |
| `sg` / `va`  | `https://holmes.tiktok-row.net/tbase/home?region=<sg_or_va>` | `https://holmes.tiktok-row.net`     | `https://sso.bytedance.com`   |
| `ttp`        | `https://holmes-ttp-us.tiktok-row.net/tbase/home?region=ttp` | `https://holmes-bdee.tiktok-us.net` | `https://sso.tiktok-usts.com` |
| `gcp`        | `https://holmes-eu.tiktok-row.net/tbase/home?region=gcp`     | `https://holmes.tiktok-eu.net`      | `https://sso.tiktok-eu.net`   |

TBase 的 BDSSO 登录与登录态检查都使用 `aid=1749`。`ttp` 额外携带 `is_ttp=1`，`cn`、`sg`、`va`、`gcp` 不携带该参数。所有 TBase API 请求的 `Origin` / `Referer` 都绑定当前 region 的 API origin，而不是页面入口。

## When to use

### AI Task

- **直接执行 AI Task**（`holmes ai-task execute --prompt <text>`）：通过 Holmes AI Task 默认 graph 执行一条 prompt，等待 AG-UI/SSE 流结束后返回最终文本、thread/run/message ID。`--prompt` 为必填项。该链路不需要打开 Holmes Web 页面，但首次使用前仍需执行 `bytedcli auth login --session` 获取 BDSSO 登录态。
- 默认由 graph 选择模型；需要固定模型时传 `--model <name>`。`--thread-id` 可复用会话，省略时自动生成新线程；Agent/脚本推荐配合全局 `--json` 使用。

### TrustPress

- 查询 TrustPress 压测任务详情（任务类型、创建人、成功/失败数、成功率等）
- 获取压测任务的 Test Parameters（AB 参数、方法配置）
- 通过 tanker ID 查看压测结果
- 创建 TrustPress deploy-mode 压测任务
- 列出指定服务的可用 pod（空闲实例）
- 为业务仓库接入或升级 Archon 流量录制依赖（TrustPress / TikDiff 共用的 `dep_graph.blade` / BUILD / sinker 注入点），见 [archon-traffic](references/archon-traffic/GUIDE.md)
- 校验某个仓库或某个 MR 的 Archon 流量录制依赖是否达标（下限校验 + 生成给 CR 用的依赖 code diff 链接），见 [archon-traffic](references/archon-traffic/GUIDE.md)
- 体检只有 `BUILD`、没有 `dep_graph.blade` 的 C++ 业务仓，或 Archon 初始化由共享框架仓承载的仓库（输出业务仓 / 框架仓两栏改动清单），见 [archon-traffic](references/archon-traffic/GUIDE.md)

### TikDiff

- 创建 TikDiff 引流、压测、diff 任务：
  - 1）引流到指定 CloudIDE IP:Port；
  - 2）基于 SCM 版本/Git branch 分支/Git commit 等创建引流任务，在远程自动编译、部署服务后自动引流一条龙；
- 查询 TikDiff 引流、压测、diff 任务的报告详情（`get` 会展示服务端失败分类 `error_desc` / `error_code`，例如 `[Business Error] Indicator Failed`）；
- 查询某个 TikDiff task 的逐指标 diff 明细（`indicator list`）：默认只列被拦截的失败指标（就是报告页红色的"失败指标"），`--all` 列全部；用于定位一个 `failed` task 到底是哪个业务指标被拦。该接口一次返回全部指标，无分页；多机/多实例部署时每个 address 一组 diff，`--json` 保留全部 address，文本模式只展示第一组
- 上述引流任务创建既支持单机引流，又支持多机引流或多实例部署引流
- 不在本 skill 范围（属 `bytedance-libra` skill）：列出 / 重跑 Libra 实验 peer-review 评审页 iframe 关联的整组 TikDiff 子任务（命令为 `libra experiment tikdiff-status` / `tikdiff-rerun`，走 `/api/v1/tikdiff/libra/*` bridge + Titan Passport 鉴权）

### ByteCore

- **C++ coredump 聚合查询**（`holmes bytecore search --psm <psm>`）：当线上出现崩溃（SIGSEGV / OOM / 其它 signal）时，按 `frames_hash_id` 聚合同类崩溃，查看各独立签名的发生次数、涉及的 version / idc / cluster / env、崩溃调用栈、LLM 归因结论。支持按 `--env / --cluster / --version / --idc / --zone / --signum / --reason` 等维度过滤，`--with-frames` 可带回完整调用栈。需要 BDSSO session（首次使用先 `bytedcli auth login --session`）。

### IndexService

- **Proto 管理**（`holmes indexservice proto list` / `create` / `get`）：在 Holmes 平台查询、创建和读取 IndexService debug proto。`proto list` 支持 `--service-id`，也支持 `--psm` 自动解析 Holmes 自己的 `service_id`；`proto create` 只创建 debug proto，不会由 `record get` 自动触发。
- **Record 查询**（`holmes indexservice record get`）：调用 Holmes IndexService debug read 接口读取 record。正排 / proto-backed record 查询需要显式传 `--pb` 与 `--pb-class`；部分 packed 正排查询还要传 `--key-pack`，让每个 key 携带 `pack:true`。倒排查询使用 `--service-type index_service_inverted`，不要传 `--pb` / `--pb-class`，需要给 key 带 score 时用 `--key-score <score>`。`--key-score` 可只传一次复用于所有 `--key`，也可按 `--key` 顺序重复传入。
- **参数选择**：查询 record / group info 时，默认直接进入 Holmes proto / record 链路；不要先查询 `byterec indexservice product get`。`--psm` 会同时用于解析 Holmes `service_id`，并作为 debug 请求体里的业务字段。

### TBase

- 查询指定 TBase 产品的完整详情（`holmes tbase product get`）
- 查询指定 TBase 产品的运行配置（`holmes tbase config get`）
- 列出指定 TBase 产品的字段列表（`holmes tbase field list`）
- 列出指定 TBase 产品的 Trigger 列表（`holmes tbase trigger list`）
- 获取单个字段元信息列表行（`holmes tbase field describe`）
- 创建字段新增提审工单（`holmes tbase field add`）
- 按 row key 查询单字段、多字段或整行全部字段值（`holmes tbase field get`）

### TikTok Debug Video

- **视频详情**（`holmes video get`）：给 item id 或 Holmes detail URL，获取 TikTok Debug 页面里的基础视频信息、作者信息、统计、封面 URL、media URL。默认调用 `video_profile_v2` 和 `video_server_data`；需要页面 Index Service tab 的 Push 数据时加 `--include-index-service`。
- **批量视频卡片**（`holmes video list`）：给 item id 列表、batch 页面 `video_ids` 短 id，或 Holmes batch URL，按页面同款链路解码/检测/批量拉取 simple info、profile、server data，并汇总封面 URL 和基础信息。
- **封面下载**：detail 和 batch 都支持 `--cover-dir <dir>`，把能下载的封面写入本地目录；JSON 输出里读取 `cover_downloads[]` 和每条 item 的 `cover_file`。
- **Agent 处理建议**：需要稳定解析时使用 `--json`；如需排查原始字段再加 `--include-raw`。batch 页面可能包含非数字 `OGV...` 类 id，CLI 会标记为 `skipped_item_ids`，不让它们拖垮整批 profile 请求。

#### Constants & Defaults

- **DEFAULT_BUSINESS**: `"0"` — HTTP `business` header value sent on every Holmes video API call (both get and batch). Advanced users on non-default business lines override with `--business <value>`.
- **DEFAULT_REGION**: `"SG"` — default region used only by `video get --include-index-service` to set the legacy `index_service` dc query parameter. `profile` and `server_data` endpoints do not consume region.
- **DEFAULT_BATCH_CHUNK_SIZE**: `30` — number of items per `video_profile_v2` / `video_server_data` / `batchGetVideoSimpleInfo` batch request. On transient errors, each collector automatically falls back to chunkSize=1 (single-item) retry to isolate the failing item.

### TrustData

- **数据质量查询与 SQL 执行**（`holmes trust-data sql-submit`）：向 TrustData 提交 ClickHouse 或 Hive SQL 查询，TrustData API 默认走 i18n Holmes 后端，输出可直接打开的 i18n TrustData 控制台 URL。支持 `--sql` 直接传 SQL 或 `--sql-file` 从文件读取（避免 shell 转义问题）。CLI 会从 SQL 的 `FROM`/`JOIN` 中识别完整表名（如 `db.table`），先调用 i18n `get_table_info` 查询活跃表元数据并自动确定 `region`；如果只命中一个活跃 region，会自动带该 region 提交。`--region` 可手动覆盖自动检测。CLI 不要求用户传 `--repo-id` 或 `--data-source-type`；后端会以 bytedcli platform 识别请求，并在缺省 repo_id 时自动创建/关联 CLI 查询使用的 repo。
- **表名或 region 冲突处理**：如果 `get_table_info` 返回多个活跃 region，交互式终端会提示用户选择 region 后继续提交；JSON/非 TTY 模式会返回 `HOLMES_TRUSTDATA_REGION_AMBIGUOUS` 错误并要求用 `--region` 重跑（推荐语义值：`us-ttp`、`eu-ttp`、`eu-ttp-no`、`us-ttp2`；兼容旧数字 1/2/4/5）。TrustData 不再执行 ROW/VA 查询，命中 VA 元数据时返回 `HOLMES_TRUSTDATA_REGION_UNSUPPORTED`，改用 `bytedcli aeolus query-editor`。CLI 只用元数据确定 submit region，不改写 SQL；如果候选 region 超过一个，提交和结果输出会展示本次实际使用的 selected region，避免把不同 region 的结果混淆。提交到某个 region 后若查询失败，默认停止并报告失败 task/URL；Agent 不要自动尝试其他 region，必须先询问用户是否要换 region 重跑。
- **Annotation required 流程**：若后端判定 SQL 涉及未标注字段或表达式，`sql-submit` 输出 `annotation_required`、`annotation_url`、`annotation_meta`、`encoded_annotation_meta`。CLI 会直接尝试打开浏览器；用户文本模式还会展示可点击的 OSC 8 terminal hyperlink，JSON 模式仍保持 stdout 为纯 JSON，可直接读取 `annotation_url` 给上层 Agent/脚本。标注表单由 TrustData 前端基于后端返回的 encoded metadata 预填。
- **Table registration required 流程**：若后端判定 SQL 涉及未注册表（`code=100008`），`sql-submit` 输出 `table_register_required`、`table_register_url`、`new_table_name`。CLI 只使用后端返回的第一个缺失表名生成 `/trust-data/annotation/table-register?table_name=<name>&modal=1` 深链，并会直接尝试打开浏览器；用户文本模式还会展示可点击链接，JSON 模式仍保持 stdout 为纯 JSON，可读取 `table_register_url` 交给上层 Agent/脚本。
- **提交后等待结果**：Agent/脚本需要直接拿结果时，可以使用 `bytedcli --json holmes trust-data sql-submit --sql-file <file> --wait`。JSON 模式不会关闭 TrustData 的自动能力：提交前 region preflight、`--wait` 轮询都会继续执行；只是 stdout 保持纯 JSON，且不会自动打开浏览器。CLI 会在提交成功并拿到 `task_id` 后调用 result API 轮询查询结果，默认每 5 秒请求一次、最长等待 3 分钟；可用 `--poll-interval-ms 5000` 明确间隔，用 `--wait-timeout-ms <ms>` 控制最长等待。成功时从 JSON 读取 `data.result.rows`/`columns`，并在回复用户时渲染成表格；不要把单行结果只拼成纯文本值。用户直接在终端运行且未传 `--json` 时，CLI 自身会把查询结果渲染成表格。result API 偶尔会在查询刚提交后短暂返回 `failed`/`unknown`，CLI 需要至少 15 秒且连续确认失败后才停止；超时仍 pending/completed/running/unknown 时 JSON status 为 `running` 且带 `message`，请用户打开 `data.url` 对应的 TrustData 页面检查进度，也可继续用 `sql-result --task-id <task_id>` 查询。确认失败时 JSON 顶层 `status=error`，从 `error.details` 读取 `task_id`、`url`、`preflight` 与后端 `detail`。若返回 `annotation_required` 或 `table_register_required`，不会轮询结果，先按对应 follow-up URL 处理。
- **查询结果获取**（`holmes trust-data sql-result`）：根据 task_id 拉取查询结果，自动解析 `data_source` JSON 为行列结构，`--limit` 控制展示行数；CLI 会在 API 请求中自动传默认 `data_source_type`，用户不需要提供该参数。顶层 `status=success` 只表示结果接口调用成功，查询状态读取 `data.status`：`success`、`failed`、`pending`、`completed`；失败原因保留在 `data.detail`。`data.row_count` 是实际返回行数，扫描与过滤规模分别读取 `data.executed_rows`、`data.filtered_rows`。
- **查询历史**（`holmes trust-data sql-history`）：获取最近的 SQL 查询历史记录，可用于找回 task_id 或确认提交记录。
- **表与字段信息**：`holmes trust-data list-tables` 默认列出全部已注册表，`--active-only` 只列活跃表；`holmes trust-data table-info --table-name <table>` 调用 i18n `get_table_info` 查询提交元数据（region、data_source_type 等），适合排查同名表冲突；`holmes trust-data fields --table-info <table>` 查询字段树、类型以及 aggregate/singular 两类 annotation 状态。字段结果中的 `total` 包含所有递归 `nested_fields`，`top_level_count` 只统计顶层字段。若同名表对应多条注册记录，先用不带筛选的 `list-tables` 获取包含 `table_id` 的完整记录，再把所选记录 JSON 作为 `--table-info` 传入。
- **Repo 详情**（`holmes trust-data repo`）：至少传入 repo_id 或 query_id，返回 `query_repository` 中的仓库信息及 `data` 中的关联查询；可同时传两者，用 repo_id 定位仓库、query_id 指定需要完整结果的查询。`sql-submit` 不需要显式 repo_id。
- **文件夹树**（`holmes trust-data folder-tree`）：列出 TrustData 文件夹目录结构。`--folder-id` 在 CLI 本地选择返回的子树；`--exclude-folder-id` 会保留指定目录本身，但让后端裁剪它的所有子目录。

### Code Review

- **MR code-review ticket 信息**（`holmes code-review get --url <mr_url>`）：从 GitLab MR URL 一步拿到 Holmes ticket 的 Change Type、Ticket Status、Reviewers、IDCs、以及分组 Checks（diff / release_manager_tested / compatibility / other）的状态表;blocking failure 单独高亮。对应页面 `https://holmes.tiktok-row.net/code-review/ticket-detail`。同时支持 `--repo <group/project> --mr-id <n>` 和 `--no-include-checks`(只拉 header)。

### Release Checker

- **release_id → report ids**（`holmes release get --release-id <id>`）：把一个 release_id 解析成该发布详情页各 checker tab 的 report id，返回 metrics（`metrics_indicator`，线上稳定性卡点信号）与 libra（`libra_realtime_indicator`，AB 实验指标）两个 tab 的首个 report id，以及完整的 tab 列表。只拿到 release_id、还不知道具体 report id 时，先跑这一步。可选 `--region` 过滤。
- **checker 报告**（`holmes checker report get --report-id <id>`）：按 report id（发布详情页 URL 里的 flight/report id，**不是** release id）拉取单份 drone checker 报告。`--kind metrics`（默认，线上稳定性）或 `--kind libra`（AB 指标）选择端点。默认返回完整报告并附带一个 pass/fail verdict；只要结论时加 `--summary` 省略完整报告体。报告体本身 schema 大且多变，CLI 原样透传，不做建模。

## Quick start

### AI Task

```bash
# 直接调用 Holmes AI Task，不打开 Web 页面
bytedcli --json holmes ai-task execute --prompt "分析这个问题并给出排查建议"

# 指定模型或复用已有线程
bytedcli --json holmes ai-task execute \
  --prompt "继续上一个问题" \
  --model <model_name> \
  --thread-id <thread_id>
```

### TrustPress

```bash
# 查看压测任务详情
bytedcli holmes trust-press get --tanker-id <tanker_id>

# 列出可用 pod
bytedcli holmes trust-press pod list --service-name <svc> --region ttp

# 创建压测任务（branch 模式，pod 参数省略时交互选择）
bytedcli holmes trust-press create \
  --service-name <svc> --region ttp --qps 10 --branch master

# 创建压测任务（SCM 版本模式）
bytedcli holmes trust-press create \
  --service-name <svc> --region ttp --qps 10 --scm 2.0.4.7452

# 创建压测任务（commit 模式）
bytedcli holmes trust-press create \
  --service-name <svc> --region ttp --qps 10 --commit 9bbd0ad41137f9fa82430e860c8d9236bb00b433

# JSON 输出（适合脚本消费）
bytedcli --json holmes trust-press get --tanker-id <tanker_id>
                               # 查可用 change_type 等枚举
```

### TikDiff

```bash
# 创建引流、压测、diff 任务
bytedcli holmes tikdiff create --case-id 2 --endpoints '[fd00:ffff:ffff:69::7a]:8080' # for CN Holmes TikDiff
bytedcli --site i18n-tt holmes tikdiff create --case-id 1 --endpoints '[fdbd:dccd:cde2:1701:d425:bcd6:c169:ae25]:53085' # for RoW Holmes TikDiff

bytedcli --json holmes tikdiff get --task-id 2493426  # for CN Holmes TikDiff
bytedcli --json --site i18n-tt holmes tikdiff get --task-id 2503983 # for RoW Holmes TikDiff

# 一个 task 报 failed 但 test_error_count=0 时，看到底哪个业务指标被拦（"失败指标"）
bytedcli --site i18n-tt holmes tikdiff indicator list --task-id 2503983            # 仅失败指标
bytedcli --site i18n-tt holmes tikdiff indicator list --task-id 2503983 --all      # 全部指标
bytedcli --json --site i18n-tt holmes tikdiff indicator list --task-id 2503983     # 结构化 per-version diff/rate

```

> 一个 TikDiff task 可能 `test_error_count=0` 却仍判 `failed`——那是业务指标 diff 超阈值被拦截（`error_desc="[Business Error] Indicator Failed"`）。`get` 只给请求级 count，具体是哪些指标要用 `indicator list`（走 `/api/v1/tikdiff/report/<task_id>/indicator`）。

> **要诊断 / 重跑 Libra 实验评审里的 TikDiff Test 子任务？** 那是另一组命令，挂在 libra skill 下：`bytedcli libra experiment tikdiff-status` / `tikdiff-rerun`。它们走 Holmes 给 Libra iframe 暴露的 `/api/v1/tikdiff/libra/*` bridge（与本节的通用 `holmes tikdiff create/get` 互补），鉴权用 Titan Passport cookie 而非 BDSSO。详见 `bytedance-libra` skill。

### TikTok Debug Video

```bash
# 按 item id 获取详情；需要 Index Service Push 时加 --include-index-service
bytedcli --json holmes video get --item-id <item_id> --region SG --include-index-service

# 直接传 Holmes detail 页面 URL
bytedcli --json holmes video get \
  --url 'https://holmes.tiktok-row.net/tiktok-debug/tiktok/video/detail?item_id=<item_id>&region=SG'

# 下载单条视频封面
bytedcli holmes video get --item-id <item_id> --region SG --cover-dir ./covers

# 非默认业务线；--business 作为 HTTP header 发送到每个 API
bytedcli --json holmes video get --item-id <item_id> --business "1"

# 只拿 profile，跳过 server_data（更快、字段更少、用于定位缺字段问题）
bytedcli --json holmes video get --item-id <item_id> --no-server-data

# 按 item id 列表批量获取基础信息和封面
bytedcli --json holmes video list --item-ids <item_id_1>,<item_id_2> --cover-dir ./covers

# 按 Holmes batch 页面 URL 获取；CLI 会先解 video_ids 短 id，--model 存到输出 metadata
bytedcli --json holmes video list \
  --url 'https://holmes.tiktok-row.net/tiktok-debug/tiktok/video/batch?model=Default&video_ids=<short_id>'

# 非默认业务线（batch 同样支持 --business）
bytedcli --json holmes video list --item-ids <id1>,<id2> --business "1"

# 传 model 名（仅 metadata，写入 data.source.model，不影响 API 请求）
bytedcli --json holmes video list --video-ids <short_id> --model Default
```

**video get 关键参数**：

- `--region <region>`：仅在 `--include-index-service` 时生效，控制旧版 `index_service` 的 dc 查询参数。默认 `SG`。
- `--business <value>`：每次调用都发送的 HTTP `business` header，默认 `"0"`。高级用户在非默认业务线时传对应值。
- `--no-server-data`：跳过 `video_server_data` 采集器；适合只看 profile 字段、或排查 server_data 缺字段、或追求最快返回的场景。默认会调用 `video_server_data`；传此 flag 跳过该采集器。

**video list 关键参数**：

- `--business <value>`：同 get，默认 `"0"`，每次 API 调用携带的业务线 header。
- `--model <model>`：**仅用于 batch** 的元数据 flag。从 batch URL 解析或手动传入，写入 `data.source.model`；对 API 请求本身没有任何影响（purely provenance）。
- `--no-server-data`：跳过 `video_server_data` 采集器（与 get 语义一致）。
- `--chunk-size <n>`：**仅用于 batch**，每批 `video_profile_v2` / `video_server_data` / `batchGetVideoSimpleInfo` 发送的 item 数，默认 30。遇到瞬时失败时（如 i/o timeout code=2），三个 collector 都会降级到 chunkSize=1 逐个重试，以定位具体出错 item。

**Output shapes（--include-raw）**：`--include-raw` 会在 JSON 输出的 `data.raw` 中保留各端点原始响应片段，具体结构如下：

- `video get`：`data.raw = { profile_item: {...}, server_data_item: {...}, index_service: {...} }` — 分别来自 `video_profile_v2`、`video_server_data` 和（开启 `--include-index-service` 时）`index_service` 的单条 item 原始响应。
- `video list`：`data.raw = { detect: {...}, simple_info: [...chunk fragments], profile: [...chunk fragments], server_data: [...chunk fragments] }` — `detect` 来自 tools/detect，其余三个字段均为 chunk 级原始响应数组（包含每批 30 条为单位的完整 envelope），可用于逐字段溯源。

### ByteCore

```bash
# 查看 ByteCore 聚合查询结果
bytedcli holmes bytecore search --psm example.cn.service
bytedcli --site i18n-tt holmes bytecore search --psm example.row.service
```

### IndexService

```bash
# 列 debug proto（显式 service_id）
bytedcli holmes indexservice proto list --service-id 12345

# 按 PSM 自动解析 Holmes service_id 后再列 proto
bytedcli holmes indexservice proto list --psm sample.service.psm

# 创建 debug proto
bytedcli holmes indexservice proto create --name SampleRecordPb --content 'message SampleRecordPb { string id = 1; }'

# 按 proto_id 获取 proto classes
bytedcli holmes indexservice proto get --proto-id 1001

# 正排 / proto-backed record 查询
bytedcli --json holmes indexservice record get \
  --psm sample.service.psm \
  --idc sg1 \
  --index-name sample_index:v1:sample \
  --key sample-record-key \
  --service-type sample_service \
  --shard-num 2 \
  --pb SampleRecordPb \
  --pb-class SampleRecordPb

# 多 key packed 正排查询
bytedcli --json holmes indexservice record get \
  --psm sample.service.psm \
  --idc sample-idc \
  --index-name sample_common:v1 \
  --key sample-item-1 \
  --key sample-item-2 \
  --key-pack \
  --service-type index_service_group_info \
  --shard-num 2 \
  --pb sample_common_info \
  --pb-class SampleCommonInfo

# 倒排 record 查询；倒排请求不带 pb / pb_class
bytedcli --json holmes indexservice record get \
  --psm sample.service.inverted \
  --idc sg1 \
  --index-name sample_inverted:v2 \
  --key sample-record-key \
  --key-score 1 \
  --service-type index_service_inverted \
  --shard-num 8
```

### TBase

```bash
# 查询产品详情
bytedcli holmes tbase product get --produce-name example.tbase.demo --region sg

# 查询产品运行配置
bytedcli holmes tbase config get --produce-name example.tbase.demo --region sg

# 列字段列表
bytedcli holmes tbase field list --produce-name example.tbase.demo --region sg

# 按字段名筛选字段
bytedcli holmes tbase field list --produce-name example.tbase.demo --region sg --keyword activity

# 只看 trigger 字段
bytedcli holmes tbase field list --produce-name example.tbase.demo --region sg --only-trigger

# 列出 triggers
bytedcli holmes tbase trigger list --produce-name example.tbase.demo --region sg

# 获取单个字段元信息列表行
bytedcli holmes tbase field describe --produce-name example.tbase.demo --field-name activity_id --region sg

# 新增字段提审；默认 dry-run，不会提交
bytedcli holmes tbase field add --produce-name example.tbase.demo --region sg --from field.json

# 真正创建字段 review 工单
bytedcli holmes tbase field add --produce-name example.tbase.demo --region sg --body-json '{"field_name":"demo_field","field_type":"TYPE_STRING","field_version":"0","template_name":"demo_template","owner":"user.name","comments":"add demo field"}' --yes

# 查询单字段值
bytedcli holmes tbase field get --produce-name example.tbase.demo --field-name activity_id --row-key 1 --region sg

# 查询多字段值（显式版本）
bytedcli holmes tbase field get --produce-name example.tbase.demo --field activity_id:2 --field activity_ids:2 --row-key 1 --region sg

# 查询整行全部字段值
bytedcli holmes tbase field get --produce-name example.tbase.demo --all-fields --row-key 1 --region sg

# JSON 输出
bytedcli --json holmes tbase field get --produce-name example.tbase.demo --field-name activity_id --row-key 1 --region sg

# 覆盖默认读路由
bytedcli holmes tbase field get --produce-name example.tbase.demo --field-name activity_id --row-key 1 --region sg --psm example.psm --dc sg1 --cluster default
```

### TrustData

```bash
# 提交 SQL 查询；TrustData API 默认走 i18n Holmes，CLI 会先用 get_table_info 自动确定 region，不要求 repo_id
bytedcli holmes trust-data sql-submit \
  --sql "SELECT count(*) FROM example_db.example_table WHERE p_date = '2026-04-01'"

# 从文件读取 SQL；若 JSON/非 TTY 模式提示 region 歧义，可用 --region 消歧
bytedcli holmes trust-data sql-submit --sql-file ./query.sql --region us-ttp

# JSON 模式适合 Agent/脚本：不会关闭 preflight 或 --wait 轮询，但不会自动打开浏览器
# 成功时读取 data.result.rows 并在回复用户时渲染成表格；需要标注/注册表时读取对应 URL
bytedcli --json holmes trust-data sql-submit --sql-file ./query.sql --wait --poll-interval-ms 5000

# 查询结果（task_id 可从 sql-submit 输出 URL 的 taskid 参数获取）
bytedcli holmes trust-data sql-result --task-id <task_id> --limit 50

# 查看查询历史
bytedcli holmes trust-data sql-history

# 列出所有活跃的 TrustData 表
bytedcli holmes trust-data list-tables --active-only

# 查询表字段
bytedcli holmes trust-data fields --table-info "example_db.example_table"

# 查询表提交元数据（region / data_source_type），用于排查同名表冲突
bytedcli holmes trust-data table-info --table-name "example_db.example_table" --active-only

# 若仅表名无法解析字段元数据，先 list-tables 获取完整 metadata，再以 JSON 传给 --table-info
bytedcli --json holmes trust-data list-tables
bytedcli holmes trust-data fields \
  --table-info '{"table_id":123,"table_name":"example_db.example_table","cluster_name":"example_cluster","table_type":0,"region":"1","is_active":true}'

# 获取 repo 详情；sql-submit 通常不需要传 repo_id，后端自动处理
bytedcli holmes trust-data repo --repo-id <repo_id>
bytedcli holmes trust-data repo --query-id <query_id>

# 查看文件夹树
bytedcli holmes trust-data folder-tree

```

### CodeReview

```bash
# 查 code-review ticket + checks(Change Type、Reviewers、Checks 汇总)
bytedcli holmes code-review get --url https://code.byted.org/tiktok-plus/tiktok_sort/merge_requests/3984
bytedcli holmes code-review get --repo tiktok-plus/tiktok_sort --mr-id 3984
bytedcli holmes code-review get --url <mr_url> --no-include-checks   # 只要 header
bytedcli holmes code-review enums

# 修改 code-review ticket(change_type / 受影响 IDCs / 全局不一致原因 / check_input)
bytedcli holmes code-review update --ticket-id 76617 --idcs ttp \
    --change-type release_manager_tested --global-inconsistent-reason US
bytedcli holmes code-review update --url <mr_url> \
    --idcs i18n,ttp,i18n_sg,i18n_va,i18n_gcp \
    --change-type release_manager_tested --global-inconsistent-reason US
bytedcli holmes code-review update --ticket-id 76617 --rm-url https://cloud-ttp-us.bytedance.net/release_manager/pipeline/...
```

### Release Checker

```bash
# release_id → 各 checker tab 的 report id（metrics / libra）
bytedcli holmes release get --release-id <release_id>
bytedcli --json holmes release get --release-id <release_id> --region US

# 按 report id 拉 metrics（线上稳定性）checker 报告；只要结论加 --summary
bytedcli holmes checker report get --report-id <report_id>
bytedcli holmes checker report get --report-id <report_id> --summary
bytedcli --json holmes checker report get --report-id <report_id> --kind libra
```

## Notes

- `holmes ai-task execute` 调用 `/api/v3/debug/ai_chat/run/stream` 并在本地消费 SSE；不打开网页。默认超时 120000 毫秒，可用 `--timeout-ms` 调整（正整数，单位毫秒）。`--prompt` 必填，非 TTY/Agent 场景缺省时直接报 `HOLMES_AI_TASK_INPUT_ERROR`，不会交互补问。
- AI Task 的 `--json` 返回字段：`content`（聚合后的最终文本）、`event_count`（诊断流是否正常完成）、`thread_id`/`run_id`/`message_id`、`requested_model`（`--model` 传入值，缺省为 null 表示 graph 选模）、`model`（服务端在流事件中回报的实际模型，未回报时为 null）。文本模式输出 Thread ID / Run ID / Message ID / Requested Model / Actual Model / Event Count / Response 的键值表。
- AI Task 错误分流：登录态失效（200 登录页或 401/403）报 `HOLMES_AUTH_ERROR`，按 hint 重新执行 `bytedcli auth login --session`；服务端在流里报 `RUN_ERROR` 时报 `HOLMES_AI_TASK_RUN_ERROR`；流正常结束但没有任何文本消息时报 `HOLMES_AI_TASK_EMPTY_RESPONSE`（可能是协议漂移或模型空响应，结合 `event_count` 判断）。
- `--tanker-id` 对应 TrustPress 页面 URL 中的 `tankerId` 参数。
- 认证通过 BDSSO CAS 流程自动完成，需要先执行 `bytedcli auth login --session` 获取 SSO session；或通过 `BYTEDCLI_HOLMES_COOKIE` 环境变量注入 cookie。
- `get` 输出包含 Task Type、Task ID、Service Name、Creator、Create/Start/End Time、**Task State**（从 `display_status`/`state`/`execute_state` 推导，例如 `Stopped/Failed` / `Running` / `Completed`）、Success/Failure Count、Success Rate 和 Test Parameters；当任务有 orchestrator 级错误时（`error_msg` 非空 或 `state=3`），会以 `⚠ Error` 行高亮错误信息，避免读者只看 metric counts 而漏掉任务本身已失败这件事。
- **Success Rate 边界**：当后端只发了 `throughput` 但没有 `success:*` 也没有 `resp.error:*` 时（数据不完整），CLI 显示 `Unknown` 而不是假装 100%（这是个真实存在的 bug，先前的旧版本会在这种情况下错报全部成功）；JSON 模式同样 `success_count: 0, failure_count: 0, success_rate: "Unknown"`。
- JSON 模式额外返回 `deploy_info`、`metric_counters`、`task_state`、`state`、`execute_state`、`display_status`、`orchestrator_error`、`error_msg`、`raw`。
- `create` 的 pod 参数（`--ip`/`--port`/`--instance-shard-id`/`--instance-name`）省略时在 TTY 中交互选择；非 TTY 场景（Agent、CI）需先运行 `pod list` 获取后显式传入。
- `create` 的部署版本必须三选一：`--branch <branch>`（branch 模式）、`--scm <version>`（SCM 版本模式，例如 `2.0.4.7452`）、`--commit <sha>`（commit 模式，传完整 commit SHA）。多传或都不传都会被拒绝。
- `pod list` 默认只显示空闲 pod，`--all` 显示全部。
- `code-review get` 接受 GitLab MR URL 或 Holmes ticket-detail URL，也可改用 `--repo <group/project> --mr-id <n>`；默认同时拉 `/openapi/mr_ticket_meta_status`（header）+ `/ticket/{id}/check_info`(checks)，加 `--no-include-checks` 只拉 header；JSON 模式里 `check_summary.by_status` 是状态计数,`check_summary.blocking_failures` 是 block=true 且 status 为 failed/error/timeout 的列表,`check_groups[].checks[]` 保留每条 check 的原始字段。
- `code-review update` 是 PATCH 操作（`PATCH /api/v3/code_review/ticket/<ticketId>`），对应 web 上「编辑 ticket」面板。Selector 三选一：`--ticket-id <id>`、`--url <mr_or_holmes_url>`、`--repo <path> --mr-id <n>`；至少要传一个可改字段（`--change-type` / `--idcs` / `--global-inconsistent-reason` / `--rm-url` / `--related-mr` / `--related-release` / `--check-input`）。`--idcs` 用逗号分隔（例 `ttp` 或 `i18n,ttp,i18n_sg,i18n_va,i18n_gcp`）；`--check-input <json>` 是兜底入口，传任意 JSON 对象覆盖 `check_input` 子树。`--change-type` 取值见 `holmes code-review enums`。
- `holmes video get` 的 `--url` 会读取 detail 页面 URL 中的 `item_id` 和 `region`。`--include-index-service` 会额外调用旧版 `/api/debug/index_service?gid=<item_id>&region=<region>`，用于拿页面 Index Service / Push 数据。
- `holmes video list` 的 selector 三选一：`--item-ids <ids>`、`--video-ids <short_id>`、`--url <batch_url>`。`--video-ids`/`--url` 会先调用 Holmes short-str 解码，再批量请求 simple info、profile 和 server data。`--chunk-size` 可控制每批 item 数。
- `holmes video get|list --cover-dir <dir>` 会下载 `cover_image_url` 指向的封面；失败项写入 `cover_downloads[].error`，不会中断其他 item。batch 中非数字 id 会进入 `skipped_item_ids`。
- `holmes indexservice proto list` 文本输出包含最终使用的 `service_id`、可选的 `Resolved From PSM`，以及 proto 列表分页表格。
- `holmes indexservice proto create` 文本输出包含 `Name`、`Request ID`、`Message`；创建 proto 需要用户提供真实 proto 定义，Agent 不能自行猜测或补写。
- `holmes indexservice proto get` 文本输出包含 proto classes 表格。
- `holmes indexservice record get` 文本输出包含最终使用的 `service_id`、可选的 `Resolved From PSM`、请求参数、record items，以及正排 / proto-backed 查询的 `decoded_message` / `decode_error`。
- `holmes indexservice record get` 的 `--pb` / `--pb-class` 只对正排 / proto-backed record 查询必需；正排需要每个 key 带 `pack:true` 时传 `--key-pack`，CLI 会给所有 `--key` 生成 `{key, pack:true}`。倒排查询传 `--service-type index_service_inverted` 时省略 `--pb` / `--pb-class`，CLI 请求体也不会发送 `pb` / `pb_class`。倒排 key 需要 score 时传 `--key-score`。
- 当正排 / proto-backed record 查询存在多个可用 `pb` / `pb-class` 候选时，必须先向用户展示候选并让用户明确选择；不能由 Agent 自行决定最终使用哪一个。
- 当正排 / proto-backed record 查询不存在可用 `pb` / `pb-class` 候选时，先向用户说明问题，并让用户选择新建 proto 还是检查其他参数是否出错；如果用户选择新建 proto，必须先向用户索取 proto 定义，再执行 `holmes indexservice proto create`。
- `holmes indexservice record get` 不会自动 create proto，也不会自动查询 proto class；正排 / proto-backed 查询的 `--pb` 和 `--pb-class` 需要显式传入。
- `holmes tbase` 命令都要求显式传 `--region`，当前支持：`cn`、`sg`、`va`、`ttp`、`gcp`。常规使用只需要传 `--region`；不需要手工指定 base URL。`sg` / `va` 的 CAS host 是 `https://sso.bytedance.com`。TBase 的 `ttp` 页面入口是 `https://holmes-ttp-us.tiktok-row.net/tbase/home?region=ttp`，API origin 是 `https://holmes-bdee.tiktok-us.net`，CAS host 是 `https://sso.tiktok-usts.com`；`gcp` 页面入口是 `https://holmes-eu.tiktok-row.net/tbase/home?region=gcp`，API origin 是 `https://holmes.tiktok-eu.net`，CAS host 是 `https://sso.tiktok-eu.net`。
- TBase US/EU API 只接受对应区域的 BDSSO session；普通 ByteCloud device-code JWT、`x-jwt-token`、Bearer JWT、`titan_passport_id`，以及 `sso.tiktok-intl.com` 的通用 TikTok SSO session 都不能代替区域登录态。当前 bytedcli 的通用 `auth login --session` 不会创建 `sso.tiktok-usts.com` / `sso.tiktok-eu.net` session；纯命令行运行时只能通过 `BYTEDCLI_HOLMES_COOKIE` 注入预先取得的区域 Holmes cookie。完全无人值守需要 Holmes 后端提供机器身份认证接口。
- `holmes tbase` 参数名是 `--produce-name`，不是 `--product-name`。
- `holmes tbase field describe` 只返回字段列表中的单条记录，不会拉取 scheme/diff detail。
- `holmes tbase field add` 创建的是 Holmes review 工单，不会自动审批或上线；不加 `--yes` 时只 dry-run 并输出最终 payload。`--body-json` 与 `--from` 二选一；CLI 会自动补齐 `produce_id`、`resource_id`、`review_link`、`id=0`，提交成功后返回带 review id 的 `review_ticket_link`。
- `holmes tbase field get` 支持 `--field-name <name>`、重复 `--field <name[:version]>`、`--all-fields` 三种主路径；当字段存在多版本时，可以配合 `--field-version` 或直接使用 `--field name:version`。
- `holmes tbase field list` 支持分页与筛选：`--page`、`--page-size`、`--keyword`、`--only-trigger`、`--template-name`。
- **OGV / 非数字 ID 过滤**：batch 输入中，带 `OGV...` 前缀或长度不足 8 位的非纯数字 ID（例如 `OGV1234567890123`、`abc`）会在进入任何 profile 调用之前被过滤掉，计入 `counts.skipped`，避免它们导致整个 chunk 返回 HTTP 400。例如 `--item-ids 7350000000000000000,OGV1234567890123,short` — 后两项会被跳过，只有第一项参与后续请求。
- **hiding_status-only profile 响应**：当某个 item 的 `video_profile_v2` 返回 `data: {id, hiding_status}`（仅有 hiding_status，没有其他字段）时，CLI 将该 item 判定为 `profile_data` 阶段失败，计入 `counts.failures`，并附带描述性错误消息；原始响应仍可在 `--include-raw` 的 `profile` chunk 片段中查看。
- **瞬时 i/o timeout code=2 隔离**：`video_server_data` chunk 请求偶尔会返回 code=2 且 message 形如 `"dial tcp ... i/o timeout"` 的瞬时错误。CLI 捕获到该类（及其他瞬时网络）错误后，会自动将整个 chunk 降级为 chunkSize=1 逐条重发，从而精准定位是哪一个 item 引发了后端超时；个别失败的 item 会计入 `counts.failures`（stage=`server_data`），其余正常返回的 item 不受影响。
- TrustData API 默认走 i18n Holmes 后端，不需要额外传 `--site i18n`。`sql-submit` 参数说明：`--sql` 和 `--sql-file` 二选一，`--sql-file` 优先；CLI 请求体固定使用 bytedcli platform，并默认让后端处理 `data_source_type` 与 repo 归属。`--repo-id` 和 `--data-source-type` 不是 submit 命令参数；缺省 repo_id 时，TrustData 后端会为 CLI 来源自动创建/关联 repo。CLI 会根据 SQL 中的 `FROM`/`JOIN` 完整表名调用 `get_table_info --active-only` 自动确定 region；多个活跃 region 时，交互式终端提示选择，JSON/非 TTY 模式返回 `HOLMES_TRUSTDATA_REGION_AMBIGUOUS`，需要显式传 `--region`。当候选 region 超过一个时，文本结果会展示本次实际使用的 selected region。`--region` 推荐取值：`us-ttp`、`eu-ttp`、`eu-ttp-no`、`us-ttp2`（兼容旧数字 1/2/4/5）；ROW/VA 查询使用 Aeolus。
- TrustData `sql-submit` 对提交阶段的 `HTTP 502 Bad Gateway` 会自动做简单重试，最多重试 2 次；若仍失败，再把 502 错误返回给用户。
- TrustData region fallback：当某个 region 的 `sql-submit` 已成功创建 task 但执行结果为 `failed`/`unknown`，Agent 必须停止并汇报 task_id、TrustData URL、已使用 region 与可选候选；不要自动尝试其他 region。只有用户明确要求继续，才可用另一个 `--region` 重跑同一 SQL。
- TrustData 表信息排查：用 `list-tables --active-only` 查看活跃表、region、active 状态；用 `table-info --table-name <table> --active-only` 查看 i18n `get_table_info` 返回的 submit metadata，包括 `region`、`region_name`、`data_source_type`、`data_source_type_name`；用 `fields --table-info <name-or-json>` 查看字段树及 aggregate/singular annotation 状态。`fields` 会尽量从表列表补全 metadata；如果表名不唯一或补全失败，传入包含 `table_id`、`table_name`、`cluster_name`、`table_type`、`region`、`is_active` 的 JSON。
- TrustData JSON 模式说明：Agent 使用 `--json` 是为了稳定解析结果，不会关闭 submit 前 region preflight 或 `--wait` 自动轮询；JSON 模式不会自动打开 annotation/table registration 浏览器，只返回对应 URL。唯一不会在 JSON/非 TTY 中进行的是交互式 region 选择，遇到 `HOLMES_TRUSTDATA_REGION_AMBIGUOUS` 后应读取候选并用 `--region` 重跑。成功查询结果应把 `data.result.columns` + `data.result.rows` 组织成表格回复用户。
- TrustData annotation required：若 `sql-submit` 返回 `annotation_required`，CLI 输出可打开的 `annotation_url`；文本模式会尝试自动打开浏览器并额外展示 OSC 8 terminal hyperlink。JSON 模式保持 stdout 为纯 JSON，不打开浏览器。由 TrustData 前端承接 encoded metadata 并完成标注表单。
- TrustData table registration required：若 `sql-submit` 返回 `table_register_required`，CLI 输出可打开的 `table_register_url` 和 `new_table_name`；文本模式会尝试自动打开浏览器并额外展示 OSC 8 terminal hyperlink。JSON 模式保持 stdout 为纯 JSON，不打开浏览器。由 TrustData 前端通过 `table_name` 和 `modal=1` 打开注册表单。
- TrustData submit-and-wait：需要提交后直接拿查询结果时使用 `sql-submit --wait`。CLI 会在成功提交并拿到 task_id 后轮询 `sql-result`，默认 5 秒一次，最长 3 分钟；若超时仍 pending/completed/running/unknown，JSON status 为 `running` 且带 `message`，请用户打开返回的 TrustData URL 检查进度，也可继续用 `sql-result --task-id <task_id>` 查询。
- TrustData status 枚举为 `1=success`、`2=failed`、`3=pending`、`4=completed`；其中 `completed` 表示执行已完成、结果仍在完整性验证阶段。`sql-submit --wait` 会继续轮询 pending/completed，确认 failed 后返回 `HOLMES_TRUSTDATA_QUERY_FAILED`，并保留后端 `detail`。
- TrustData 页面 URL 中的 `taskid` 即 CLI `sql-result` 的 `--task-id`。
- `holmes release get` 走 `/api/v3/agile/release_info`，解析响应里的 `tab_config` 数组，取 `report_type=metrics_indicator` / `libra_realtime_indicator` 的首个 `report_id` 作为 metrics / libra；tab 缺失时对应字段为 `null`，JSON 里 `tabs[]` 保留全部 tab 的 `report_type` + `report_id`。
- `holmes checker report get` 走 `/api/drone/v2/checker/{metrics_indicator,libra_realtime_indicator}/report?report_id=<id>`，READ-ONLY。`--report-id` 是发布详情页 URL 的 flight/report id（不是 release id），只有 release id 时先用 `release get` 解析。verdict 的 `ok` 以报告体顶层 `code===0` 判定；`--summary` 只返回 verdict，省略完整报告体（JSON 里 `report` 字段随之省略）。checker 报告与 release_info 都通过 Holmes BDSSO CAS session 统一鉴权，需要先 `bytedcli auth login --session`（或注入 `BYTEDCLI_HOLMES_COOKIE`）。

## Sub-Domain References

只加载当前 action 所需文件，不要一次读完。

| Action / 场景                                                                                                                                                            | 必读资料                                             |
| ------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ---------------------------------------------------- |
| Archon 流量录制依赖接入（TrustPress / TikDiff 共用底座）、依赖最新值核对与升级、给定仓库或 MR 的依赖下限校验（`--verify` / `--mr`）、BUILD-only 仓与共享框架承载仓的体检 | [archon-traffic](references/archon-traffic/GUIDE.md) |

## References

- [holmes.md](./references/holmes.md)
- [invocation.md](./../../invocation.md)
- [troubleshooting.md](./../../troubleshooting.md)
