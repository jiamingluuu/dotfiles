# TEA（DataOpen / tea-next）

## Auth modes

| 模式       | 适用站点              | 凭据来源                                             | 何时使用                                                                                        |
| ---------- | --------------------- | ---------------------------------------------------- | ----------------------------------------------------------------------------------------------- |
| `dataopen` | cn / va / sg          | `TEA_APP_ID` + `TEA_APP_SECRET`（申请 DataOpen App） | 已有 DataOpen App，或需稳定后端对接                                                             |
| `titan`    | cn / va / sg / sglark | `bytedcli auth login` 扫码（走 titan_passport）      | 没有 DataOpen App，或想用扫码身份直接调内部 API；sglark 唯一可用，cn/va/sg 与 DataOpen 任选其一 |

通过 `--auth-mode dataopen|titan|auto` 显式切换；默认 `auto` 按下列优先级判定：

1. 命令行显式 `--auth-mode ...` 优先
2. `--tea-site sglark` 或 URL host 是 `tea-sglark.bytedance.net` → 强制 `titan`
3. 存在 `TEA_APP_ID/TEA_APP_SECRET` → `dataopen`
4. 站点支持 titan（当前 cn / va / sg / sglark 全部支持） → `titan`
5. 否则 `dataopen`（此时若无凭据会抛 `TEA_INPUT_ERROR`）

`sglark` 不支持 `dataopen`；cn / va / sg 两条路径任选其一。

## Command map

- `bytedcli tea event send`
  - 上报单条 TEA / ByteIO 事件；不支持批量文件上报
  - `--app-id <id>`：TEA / ByteIO app_id，必填
  - `--event <name>`：事件名，必填；事件名需以字母开头，只包含字母、数字、下划线、点或短横线
  - 身份默认值：不传身份参数时，CLI 从 bytedcli auth / userinfo / JWT / SSO 解析当前用户作为 `user_unique_id`；解析失败回退 `installation_id`
  - `--user-unique-id <id>`：覆盖自动解析出的用户 ID；`--device-id <id>` 与 `--web-id <id>` 可同时传，不互斥
  - `--no-auto-user`：禁用自动用户解析和 `installation_id` 回退，此时必须显式传 `--user-unique-id` / `--device-id` / `--web-id` 至少一个；仅传 `device_id` 或 `web_id` 时，会将该值同步作为 payload 与 SDK 配置里的 `user_unique_id`
  - `--require-user`：要求最终必须存在 `user_unique_id`，无法从登录态解析且未传 `--user-unique-id` 时失败
  - 事件属性：`--params-file <file>` 先加载 JSON object，`--params-json <json>` 覆盖同名字段，重复 `--param key=value` 最后覆盖；`--param` 的 value 按字符串处理，数字/布尔请用 JSON
  - `--timestamp-ms <ms>`：事件发生时间，默认当前时间；`--caller <caller>`：ByteIO caller，默认 `bytedcli.tea.event_send`；`--dry-run` 只构造 payload 不上报；`--dump <file>` 写出最终 payload
- `bytedcli tea search`
  - `--type dashboard_info`：按看板 URL 解析出的 `dashboard_id` 获取看板信息
  - `--type dashboard_reports`：列出看板内报表（包含 report_id / report_type / 简要描述）
  - `--tea-site <site>`：cn | va | sg | sglark | auto
  - `--auth-mode <mode>`：dataopen | titan | auto
  - `--tea-base-url <url>`：直接覆盖 DataOpen 基址（仅 dataopen 模式）
- `bytedcli tea report create`
  - 用 DSL 创建 tea-next report；输入 `--dsl <dslJson>` 或 `--dsl-file <file>`；写接口仅支持 titan 模式，默认走扫码登录态
  - `--project-id <projectId>`：TEA project_id；也可从 `--url` 解析
  - `--name <name>`：report 名称
  - `--dashboard-id <dashboardId>`：可选，写入创建 payload；展示到看板仍建议继续执行 `tea dashboard subscribe-reports`
  - `--report-type <type>`：默认 `event_analysis`
  - `--report-app-id <appId>`：创建 payload 的 `app_id`，默认使用 `project_id`；注意不是 DataOpen 鉴权用的 `--app-id`
  - 实际 endpoint：`POST /datafinder/api/v1/projects/<pid>/reports`（仅 titan 模式）
- `bytedcli tea report get`
  - 获取已有 tea-next report 配置；`--url` 可解析 project/report 和控制面 host，或显式传 `--project-id --report-id --tea-site <site>`
  - 传入 `--dashboard-url <url>` 或 `--dashboard-id <id>` 时，改为读取 dashboard 绑定的 card report 对象；用于排查 report detail 与 dashboard card 渲染配置不一致的情况
  - dashboard 模式可用 `--report-id <id>` 指定目标 report，也可同时传 tea-next report `--url` 解析 report_id
  - `--dsl-only`：仅输出 `dsls[--dsl-index].dsl_content`，`--dsl-index` 默认 0，便于保存成 JSON 文件后修改
  - 如果要导出后再用 `report update` 写回，请使用普通 report detail 路径（`--project-id/--report-id` 或 report `--url`），不要带 `--dashboard-url/--dashboard-id`；dashboard 模式读取的是 card 内嵌 report，主要用于排查渲染配置
  - 实际 endpoint：普通模式 `GET /datafinder/api/v1/projects/<pid>/reports/<report_id>`；dashboard 模式 `GET /datafinder/api/v1/projects/<pid>/dashboards/<did>/reports`（均仅 titan 模式）
- `bytedcli tea report list`
  - 列出 dashboard 当前绑定的 reports：`--dashboard-url <url>`，或 `--project-id <pid> --dashboard-id <did> --tea-site <site>`
  - JSON 模式返回完整 dashboard reports 原始块 `dashboard_reports`，包含 `reports`、`layout`、`denied`、`total`、`available` 等字段；文本模式只展示 report 摘要
  - 该接口单页全量返回；JSON 顶层 `total` 是后端 total，`page=1`，`page_size` = `total`（单页全量，避免被误判为还有分页），`accessible_count` = 本次返回的可访问 reports 数；原始 `available/denied` 保留在 `dashboard_reports` 中
  - 用于先确认 dashboard card 绑定的是哪些 report，以及获取 dashboard card 使用的内嵌 report DSL/`show_option`/`extra`
  - 实际 endpoint：`GET /datafinder/api/v1/projects/<pid>/dashboards/<did>/reports`（仅 titan 模式）
- `bytedcli tea report update`
  - 原地更新已有 tea-next report；先 GET 当前 report，再 PATCH 同一路径，保留线上其它字段
  - `--dsl <json>` / `--dsl-file <file>`：替换 `dsls[--dsl-index].dsl_content`；`--dsl-index` 默认 0；从普通 report detail 路径的 `report get --dsl-only` 导出后写回时，两边使用相同 `--dsl-index`
  - 可同时更新 `--name`、`--desc`、`--report-type`、`--dsl-name`
  - 用显式 `--project-id --report-id` 而不是 URL 时，需要传 `--tea-site <site>` 让 titan 模式确定 tea-next host
  - 实际 endpoint：`PATCH /datafinder/api/v1/projects/<pid>/reports/<report_id>`（仅 titan 模式）
- `bytedcli tea dashboard subscribe-reports`
  - 把已有 report 添加到 dashboard：`--project-id <pid> --dashboard-id <did> --report-ids <rid1,rid2>`
  - 写接口仅支持 titan 模式，默认走扫码登录态
  - 默认会读取当前 dashboard reports/layout，保留已有卡片位置，只给新增 report 补自动布局，并 PATCH `layout/page_config`
  - `--no-update-layout`：只建立订阅关系，不修改 dashboard 布局
  - 订阅接口 body 同时传 `report_id` 和 `report_ids`；后端返回 `401003`（订阅关系已存在）时按幂等成功处理
  - 验证接口 `GET /projects/<pid>/dashboards/<did>/reports` 通常返回 `{ [dashboardId]: { reports, layout } }`
- `bytedcli tea get-dsl`
  - 输入：tea-next 报表链接（report）或快照链接（snapshot）
  - 输出：DSL JSON（文本模式直接打印到 stdout；JSON 模式输出 JSON Lines 的 data=DSL 本体，可直接 pipe 到 `tea query`）
  - `--tea-site <site>`：cn | va | sg | sglark | auto
  - `--auth-mode <mode>`：dataopen | titan | auto
  - `--project-id <projectId>`：TEA project_id（不传时优先从 URL 解析）
  - `--dashboard-id <dashboardId>`：仅 sglark titan 必填（sglark 没有 `/analysis/<id>/result` endpoint，要靠 `dashboards/<did>/reports` 兜底）；DataOpen 与 cn/va/sg titan 都不需要
  - `--tea-base-url <url>`：直接覆盖 DataOpen 基址（仅 dataopen 模式）
  - 实际 endpoint：
    - dataopen：`POST /dataopen/open-apis/datafinder/openapi/v1/projects/<pid>/dsls`，snapshot/report 通用
    - cn / va / sg titan：`GET /datafinder/api/v1/analysis/<id>/result?pack_dsl=1`，snapshot/report 通用，DSL 在 envelope 顶层 `dsl` 字段
    - sglark titan：`GET /datafinder/api/v1/dashboards/<did>/reports` 兜底，仅支持 report 类型 URL（带 `dashboardId`）；snapshot URL 不支持
- `bytedcli tea query`
  - **dataopen / cn-va-sg titan 模式**：输入 DSL JSON（`--dsl` 或 stdin），输出 analysis 数据
  - **sglark titan 模式**：需传 `--url` 或同时传 `--project-id/--dashboard-id/--report-id` 三元组；输出报表 analysis 数据
  - `--window-start <rfc3339>` / `--window-end <rfc3339>`：成对覆盖 DSL 的查询时间，输入必须包含 `Z` 或 `+08:00` 形式的显式偏移；CLI 转成 Unix 秒写入 timestamp spans，但保留每个 period 原有的 `timezone`、`granularity`、`align_unit` 等查询端设置
  - JSON 输出的 `context.time_conversion` 同时记录 requested/source/effective timezone、原始窗口和目标时区中的精确窗口；文本模式将同一审计信息写到 stderr
  - 如果用户窗口与 DSL 粒度边界不对齐（例如 UTC+8 自然日配 UTC day），TEA 可能返回多个 UTC 日期桶。不得改写 DSL timezone 来强行得到单桶，也不得把多个桶简单相加后称为看板单日值；应按返回日期标签和 `context.time_conversion` 说明口径
  - 自动时间覆盖不支持 sglark report 三元组路径、对比周期、多个不同原始时间窗或同一 DSL 内混用多个查询时区；这些场景会返回 `TEA_INPUT_ERROR`，避免静默破坏报表/基线语义
  - SG `tea-captain.tiktok-row.net` / `tea-captain.byteintl.net` 链接做 `get-dsl | query` 时，query 阶段也传同一个 `--url`；管道只传 DSL，不携带来源 host，只写 `--tea-site sg` 会回到默认 `tea-captain.tiktok-row.net`（旧 `tea-sg.tiktok-row.net` 已作为 alias 保留）
  - `--tea-site <site>`：cn | va | sg | sglark | auto
  - `--auth-mode <mode>`：dataopen | titan | auto
  - `--tea-base-url <url>`：直接覆盖 DataOpen 基址（仅 dataopen 模式）
  - 实际 endpoint：
    - dataopen：`POST /dataopen/open-apis/datafinder/openapi/v1/analysis`，同步返回数组
    - cn / va / sg titan：`POST /datafinder/api/v1/analysis` 返回 `{ result_id }`，CLI 自动轮询 `GET /datafinder/api/v1/analysis/<result_id>/result`；默认轮询超时取 `max(60s, --http-timeout-ms)`（结果尚未就绪时会输出 `result_id`/`status`，可重新执行同一条命令）
    - sglark titan：`POST /datafinder/api/v1/projects/<pid>/dashboards/<did>/reports/<rid>/analysis`
- `bytedcli tea behavior`
  - 查询行为细查行为流（behavior-detail/detail）。**仅 dataopen 模式可用，所有区域 titan 模式都不支持**（tea-next 内部 API `/datafinder/api/v1/...` 未暴露 `behaviors/flows_v3`），titan 调用会抛 `TEA_TITAN_NOT_SUPPORTED`。
  - API: `/dataopen/open-apis/datafinder/openapi/v1/projects/:project_id/behaviors/flows_v3`
  - `--url <url>`：tea-next `behavior-detail/detail` 链接，会自动解析 `project_id/query_id/query_type/appId/timestamp/eventFilterList/sort`
  - `--project-id <projectId>`：TEA project_id（不用 URL 时必填）
  - `--query-id <queryId>`：查询 ID，如 device_id / user_unique_id / user_id
  - `--query-type <queryType>`：`device_id` | `user_unique_id` | `user_id`
  - `--behavior-app-id <appId>`：行为细查请求体 `app_id`；注意不是 DataOpen 凭证 `--app-id`
  - `--start-time <ts>` / `--end-time <ts>`：秒或毫秒时间戳
  - `--events <events>`：精确事件名列表（逗号分隔），会下发为 OpenAPI `event_name` 做服务端前置过滤
  - `--dump <filepath>`：将原始行为流 JSON 写入文件；`--json` 模式下必须搭配 `--dump`
- `bytedcli tea get-event`
  - 查询事件元数据（event metadata）。**仅 dataopen 模式可用，所有区域 titan 模式都不支持**（tea-next 内部 API 未暴露 `metadata/list/events`），titan 调用会抛 `TEA_TITAN_NOT_SUPPORTED`。
  - API: `/dataopen/open-apis/datafinder/openapi/v1/metadata/projects/:project_id/list/events`
  - `--project-id <projectId>`：TEA project_id
  - `--events <events>`：可选事件名列表（逗号分隔，如 `example.play,example.view`）；不传时列出全部事件
  - `--status <status>`：事件状态列表（逗号分隔；可选值 0=审批中 1=已上报 3=停止采集 4=隐藏，默认 0,1,3,4）
  - `--with <with>`：附加返回信息（逗号分隔；可选值 params|virtual_params|property_dict|values|alias|event_groups|event_sample）；精确查询默认 `params`，全量查询默认不展开
  - `--dump <filepath>`：将原始 JSON 结果写入文件（相对路径基于工作目录）
- `bytedcli tea get-param`
  - 查询事件属性与公共属性元数据（event / common param metadata）。**仅 dataopen 模式可用，所有区域 titan 模式都不支持**（tea-next 内部 API 未暴露 `metadata/list/params`），titan 调用会抛 `TEA_TITAN_NOT_SUPPORTED`。
  - API: `/dataopen/open-apis/datafinder/openapi/v1/metadata/projects/:project_id/list/params`
  - 用途：解决「analysis 的 `--filter` / `--group` 该写 `:common` 还是 `:event`」——输出的 scope 列直接给出该写哪个后缀
  - `--project-id <projectId>`：（必填）TEA project_id
  - `--names <names>`：属性名列表（逗号分隔；不传则返回项目下全部属性）
  - `--scope <scope>`：只看某一类属性，`all` | `common` | `event`（默认 `all`）；`common` 对应过滤/分组的 `:common`，`event` 对应 `:event`
  - `--limit <n>`：文本模式最多展示多少行（默认 50）；达上限会提示用 `--names` 精确查询或调大 `--limit`
  - `--dump <filepath>`：将原始 JSON 结果写入文件（相对路径基于工作目录）；`--json` 模式下必须搭配 `--dump`
- `bytedcli tea get-profile`
  - 查询用户属性元数据（user profile metadata）。**仅 dataopen 模式可用，所有区域 titan 模式都不支持**（tea-next 内部 API 未暴露 `metadata/list/user_profiles`），titan 调用会抛 `TEA_TITAN_NOT_SUPPORTED`。
  - API: `/dataopen/open-apis/datafinder/openapi/v1/metadata/projects/:project_id/list/user_profiles`
  - `--project-id <projectId>`：（必填）TEA project_id
  - `--names <names>`：用户属性名列表（逗号分隔，如 `country,age`；不传则返回全部）
  - `--status <status>`：用户属性状态列表（逗号分隔，如 `0,1`；可单独使用，不依赖 `--names`）
  - `--region <region>`：DataOpen 区域（如 `va`、`sg`），用于自动推导 DataOpen 基址
  - `--dump <filepath>`：将原始 JSON 结果写入文件（相对路径基于工作目录）；`--json` 模式下必须搭配 `--dump`
- `bytedcli tea dsl2link`
  - 根据 DSL 生成 tea-next 分析结果链接。**仅 dataopen 模式可用，所有区域 titan 模式都不支持**（tea-next 内部 API 未暴露 `dsls/jumper`），titan 调用会抛 `TEA_TITAN_NOT_SUPPORTED`。
  - API: `/dataopen/open-apis/datafinder/openapi/v1/projects/:project_id/dsls/jumper`
  - `--query-type <queryType>`：查询类型（不传时从 DSL 的 `content.query_type` 自动推断）；可选值 `event-analysis` | `retention-analysis` | `funnel-analysis` | `compositon-analysis` | `pathfind-analysis` | `life_cycle-analysis` | `distribution-analysis`
  - DSL `content.query_type` 自动映射：`event`→`event-analysis`, `retention`→`retention-analysis`, `funnel`→`funnel-analysis`, `path_find`→`pathfind-analysis`, `life_cycle`→`life_cycle-analysis`, `event_topk`→`distribution-analysis`, `composition`→`compositon-analysis`
  - `--dsl <dslJson>`：DSL JSON（字符串形式；也支持从 stdin 读取）
  - `project_id` 从 DSL 的 `resources[0].project_ids[0]` 自动提取，无需手动指定

### analysis 语义化查询

`bytedcli tea analysis <model>` 把 7 个分析模型封装成语义化子命令，CLI 自动构造 DSL 并投递 `/analysis`，无需手写 JSON。7 个模型：`event` / `funnel` / `retention` / `composition` / `path-find` / `life-cycle` / `distribution`。

支持 dataopen cn/va/sg 与 titan cn/va/sg。sglark titan 不支持裸 `/analysis`，需要 sglark 时改用 `tea query` 的报表路径。

> 与本文件其他命令不同，analysis 的参数不在此处逐条罗列。它的参数、取值、跨模型差异与错误码由能力契约驱动 CLI Help 生成，Help 是唯一事实来源：`bytedcli tea analysis --help` 看选型与跨模型对照，`bytedcli tea analysis <model> --help` 看该模型全部参数。此处复述一遍就是第二份会过期的手抄。

## Sites

| 区域      | 值       | 前端入口 host（用户浏览器）                       | DataOpen 基址（办公网）                         | DataOpen 基址（生产网）                       | Titan internal host                                                                                      |
| --------- | -------- | ------------------------------------------------- | ----------------------------------------------- | --------------------------------------------- | -------------------------------------------------------------------------------------------------------- |
| 中国      | `cn`     | `data.bytedance.net` / `tea.bytedance.net`        | `data.bytedance.net/dataopen/open-apis`         | 同左                                          | `data.bytedance.net`                                                                                     |
| Virginia  | `va`     | `tea-va.bytedance.net` 或 `tea-va.tiktok-row.net` | `data-va.tiktok-row.net/dataopen/open-apis`     | `data-va.bytedance.net/dataopen/open-apis`    | `tea-va.bytedance.net` 或 `tea-va.tiktok-row.net`（与 URL host 一致）                                    |
| Singapore | `sg`     | `tea-captain.tiktok-row.net`                      | `tea-captain.tiktok-row.net/dataopen/open-apis` | `tea-captain.byteintl.net/dataopen/open-apis` | `tea-captain.tiktok-row.net`（生产网 `tea-captain.byteintl.net`；旧 `tea-sg.tiktok-row.net` 作为 alias） |
| SG Lark   | `sglark` | `tea-sglark.bytedance.net`                        | —（titan only）                                 | —                                             | `tea-sglark.bytedance.net`                                                                               |

`--tea-site auto` 会按 URL host 自动推断（识别 `data.bytedance.net` / `tea.bytedance.net` / `tea-va.bytedance.net` / `tea-va.tiktok-row.net` / `data-va.tiktok-row.net` / `data-va.bytedance.net` / `tea-captain.tiktok-row.net` / `tea-captain.byteintl.net` / `dataopen-sg.tiktok-row.net` / `tea-sg.bytedance.net` / `tea-sg.tiktok-row.net` / `tea-sglark.bytedance.net`）；`--tea-base-url <url>` 可直接覆盖 DataOpen 基址（海外私有部署场景）。

VA 区域的 titan host 会保留 URL 中的实际 host：用户给的链接是 `tea-va.tiktok-row.net` 时，CLI 会同时把 cookie 签发与后续请求都发到 `tea-va.tiktok-row.net`，避免被改写到 `tea-va.bytedance.net` 后命中错误后端。

SG 的 `tea-captain.tiktok-row.net` / `tea-captain.byteintl.net` 是 DataOpen origin，也能服务 analysis/snapshot。`tea get-dsl --url <tea-captain-url>` 会保留 URL host；但文本管道只把 DSL 传给 `tea query`，不会把来源 host 传过去。推荐写法：

```bash
URL='https://tea-captain.tiktok-row.net/tea-next/project/<pid>/event-analysis/result/<snapshot-id>'
bytedcli --json tea get-dsl --tea-site auto --auth-mode titan --url "$URL" | \
  bytedcli --json tea query --tea-site auto --auth-mode titan --url "$URL"
```

如果 query 阶段只写 `--tea-site sg --auth-mode titan`，CLI 按 sg 默认 host 走 `tea-captain.tiktok-row.net`。旧 `tea-sg.tiktok-row.net` 已作为 alias 保留，仍然兼容。

**生产网模式**：在 ByteDance 生产网（如 FaaS、TCE 容器）中运行时，设置 `BYTEDCLI_NETWORK_PROFILE=prod` 可将 VA / SG 的 DataOpen 域名自动切换为生产网可达的内部域名（见上表"生产网"列）。CN 不受影响。

## Inputs

### Dashboard URL

`.../tea-next/project/<project_id>/dashboard/<dashboard_id>`

### Report URL

`.../tea-next/project/<project_id>/event-analysis/<report_id>?dashboardId=<dashboard_id>`

### Snapshot URL

`.../tea-next/project/<project_id>/event-analysis/result/<snapshot_id>`

### Behavior detail URL

`.../tea-next/project/<project_id>/behavior-detail/detail?query_id=<id>&query_type=<type>&appId=<app_id>&timestamp=<start_ms>&timestamp=<end_ms>&eventFilterList=%5B%5D`
