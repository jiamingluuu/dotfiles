---
name: bytedance-tea
description: "Operate TEA (DataOpen / tea-next) via bytedcli: run semantic analysis queries, manage dashboard reports and DSL, inspect session replay, read LLM workbench operations-agent sessions with their rounds and model/tool/MCP steps (SG titan only), list project roles, invite project members with dry-run confirmation, query event metadata, and send one TEA / ByteIO event. Supports cn/va/sg/sglark for general TEA operations; project permissions are CN titan only. Use for TEA dashboards, reports, snapshots, DSL, permissions, roles, members, session replay, agent sessions, LLM workbench journeys, behavior detail, event metadata, analysis links, or 事件分析/漏斗/留存/权限/角色/成员."
---

# bytedcli TEA

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

**做数据分析时，先在 `tea analysis` 与 `tea query` 之间二选一：**

- **默认用 `tea analysis`**：做事件 / 漏斗 / 留存 / 构成 / 路径 / 生命周期 / 分布查询时，只要你能用「事件名 + 指标 + 过滤 + 分组」描述清楚要查什么，就用它——CLI 自动构造 DSL，**你不需要懂 DSL**。前置条件：必须提供有效的 `--project-id`（analysis 的 DSL 直接带 project_id，缺了会报 `TEA_INPUT_ERROR`；project_id 可从 tea-next 看板 URL 的 `/project/<id>/` 段获取）。需要检查 CLI 构造出的 DSL 时，加 `--print-dsl`，它只打印 DSL，不鉴权、不发请求。
- **仅当你手上已经有现成的 DSL JSON 时，才用 `tea query`**：比如 DSL 是你自己写好的，或先用 `tea get-dsl` 从 tea-next 看板 / 报表 / 快照链接提取出来的。`tea query` 默认原样投递 DSL；需要覆盖时间窗时可成对传 `--window-start/--window-end`，CLI 只转换 timestamp spans，保留 DSL 原有的 `timezone`、粒度和对齐设置。

其它能力：

- 需要从 tea-next 看板 / 报表链接提取 DSL（用 `tea get-dsl`，常配合 `tea query`）
- 需要从 tea-next 行为细查详情页查询用户行为流（behavior-detail/detail）
- 需要按公共事件属性 + 时间范围搜索会话回放，并读取回放事件、操作流或播放器原始数据
- 需要读 LLM workbench 里 agent 的会话：会话列表、每轮问答、每轮的模型 / 工具 / MCP 步骤（`tea operations-agent session`，SG titan only）。接入的 agent 不限于 iDA；只要 TEA 项目权限，也能读其他用户的会话
- 需要根据 DSL 生成 tea-next 分析结果链接
- 需要查看有权限的看板信息 / 看板内报表列表
- 需要用 DSL 创建 tea-next report，或把已有 report 添加到 dashboard
- 需要列出 TEA project 可分配角色，或邀请邮箱账号并绑定角色（CN titan only）
- 查询多个区域的 tea 数据，支持 cn、va、sg、sglark 地区
- 需要查询事件元数据（event metadata）
- 需要用 `app_id`、单个 `event` 和 `params` 上报一条 TEA / ByteIO 事件，或需要
  自动身份解析、`--dry-run`（用 `tea event send`）。已有获批 MCS HTTPS origin
  和完整 1～50 event envelope 时改用 `byteio event send`。

## Auth 模式

tea 子命令支持两种鉴权模式，通过 `--auth-mode` 选择，默认 `auto` 自动判定：

| 模式       | 适用                                                | 凭据来源                                                                      |
| ---------- | --------------------------------------------------- | ----------------------------------------------------------------------------- |
| `dataopen` | DataOpen openapi（cn / va / sg）                    | 环境变量 `TEA_APP_ID` + `TEA_APP_SECRET`，或 `--app-id` / `--app-secret` 参数 |
| `titan`    | tea-next 内部 API（cn / va / sg / sglark 全部支持） | `bytedcli auth login` 后自动换 `titan_passport_id` cookie                     |

判定优先级（`decideAuthMode`）：

1. 显式 `--auth-mode dataopen|titan` 最高优先
2. site 为 `sglark` → 强制 `titan`（sglark 不支持 DataOpen）
3. 当 `TEA_APP_ID`+`TEA_APP_SECRET` 均存在 → `dataopen`
4. 其他情况 → `titan`（cn / va / sg 在没有 DataOpen 凭据时会自动走 titan，无需申请 App，仅需扫码登录一次）

### Prerequisites (DataOpen 模式)

```env
TEA_APP_ID=123
TEA_APP_SECRET=***
```

申请地址：https://data.bytedance.net/dataopen/tea-next/app

### Prerequisites (titan 模式)

```bash
bytedcli auth login  # 扫码登录即可，无需申请 DataOpen App
```

### Region / Control plane

所有 tea 子命令支持 `--region` 或 `--tea-site` 切换控制面：

| 区域         | 值       | DataOpen 域名（办公网）                         | DataOpen 域名（生产网）                       | Titan internal 域名                                                                                                        | DataOpen | Titan |
| ------------ | -------- | ----------------------------------------------- | --------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------- | -------- | ----- |
| 中国（默认） | `cn`     | `data.bytedance.net/dataopen/open-apis`         | 同左                                          | `data.bytedance.net/datafinder/api/v1`                                                                                     | ✅       | ✅    |
| Virginia     | `va`     | `data-va.tiktok-row.net/dataopen/open-apis`     | `data-va.bytedance.net/dataopen/open-apis`    | `tea-va.bytedance.net` 或 `tea-va.tiktok-row.net` `/datafinder/api/v1`                                                     | ✅       | ✅    |
| Singapore    | `sg`     | `tea-captain.tiktok-row.net/dataopen/open-apis` | `tea-captain.byteintl.net/dataopen/open-apis` | `tea-captain.tiktok-row.net/datafinder/api/v1`（生产网 `tea-captain.byteintl.net`；旧 `tea-sg.tiktok-row.net` 作为 alias） |
| SG Lark      | `sglark` | —                                               | —                                             | `tea-sglark.bytedance.net/datafinder/api/v1`                                                                               | ❌       | ✅    |

> cn / va / sg 三个区域 DataOpen 与 Titan 任选其一；如果没有 DataOpen App 凭据，可直接 `bytedcli auth login` 后用 `--auth-mode titan`（或留空 `--auth-mode` 让默认逻辑兜底）。SG Lark 仅支持 titan。
>
> VA 区域同时识别 `tea-va.bytedance.net` 与 `tea-va.tiktok-row.net` 两个 host，用户给的 URL host 会优先于 site 默认值，避免请求被改写到错误后端。
>
> SG 的 `tea-captain.tiktok-row.net` / `tea-captain.byteintl.net` 同时承担 DataOpen 与部分 analysis/snapshot 入口。`tea get-dsl` 通过 URL 能保留该 host；但 `get-dsl | tea query` 的管道只传 DSL，query 阶段若只写 `--tea-site sg` 会丢失来源 host。处理 tea-captain 链接时，query 阶段也传同一个 `--url`。
>
> **生产网模式**：在 ByteDance 生产网（如 FaaS、TCE 容器）中运行时，设置 `BYTEDCLI_NETWORK_PROFILE=prod` 可将 VA / SG 的 DataOpen 域名切换为生产网可达的内部域名（见上表"生产网"列）。CN 不受影响。

- `--tea-site cn|va|sg|sglark|auto`：显式选择控制面；`auto` 会按 tea-next URL host 自动推断（识别 `data.bytedance.net` / `tea.bytedance.net` / `tea-va.bytedance.net` / `tea-va.tiktok-row.net` / `data-va.tiktok-row.net` / `data-va.bytedance.net` / `tea-captain.tiktok-row.net` / `tea-captain.byteintl.net` / `dataopen-sg.tiktok-row.net` / `tea-sg.bytedance.net` / `tea-sg.tiktok-row.net` / `tea-sglark.bytedance.net`）
- `--tea-base-url <url>`：直接覆盖 DataOpen API 基址（仅 DataOpen 模式有效）

优先级：`--tea-base-url` > `--tea-site` > `--region`

## Quick start

```bash
# 语义化查询：事件渗透率（无需手写 DSL，CLI 自动构造并投递 /analysis）
# 这是 7 个分析模型之一；event/funnel/retention/composition/path-find/life-cycle/distribution 的完整用法见下方 `## tea analysis` 章节
# --project-id 必填（有效 TEA project_id，可从看板 URL 的 /project/<id>/ 段获取）
bytedcli tea analysis event --project-id 123 --event example.play --indicator penetration --last 30d

# 看板信息
bytedcli tea search --type dashboard_info --url https://data.example.net/tea-next/project/3/dashboard/7446993126637437450

# 看板内报表列表
bytedcli tea report list --dashboard-url https://data.example.net/tea-next/project/123/dashboard/456 --tea-site cn

# 用 DSL 创建 report（tea-next 写接口仅支持 titan 模式）
bytedcli tea report create --project-id 123 --name sample-report --dsl-file ./dsl.json --auth-mode titan --tea-site cn

# 获取已有 report 的 DSL，修改后可用于原地更新
bytedcli tea report get --project-id 123 --report-id 789 --tea-site cn --dsl-only > report.dsl.json

# 获取 dashboard card 使用的内嵌 report 配置（排查看板卡片渲染时优先用这个）
bytedcli --json tea report get --dashboard-url https://data.example.net/tea-next/project/123/dashboard/456 --report-id 789 --tea-site cn

# 原地更新已有 report，保留线上其它配置字段，只替换显式传入字段
bytedcli tea report update --project-id 123 --report-id 789 --tea-site cn --dsl-file ./report.dsl.json

# 把 report 订阅到 dashboard，并默认补齐 layout/page_config
bytedcli tea dashboard subscribe-reports --project-id 123 --dashboard-id 456 --report-ids 789 --auth-mode titan --tea-site cn

# 列出项目可分配角色（CN titan only）
bytedcli tea role list --project-id 123

# role list 只返回 status=1 的可分配角色，并隐藏 role_admins 人员详情

# 预览邀请，不提交
bytedcli tea member invite --project-id 123 --email sample.user@example.com --role-id 456

# 确认邀请；一个成员可重复传多个角色 ID
bytedcli tea member invite --project-id 123 --email sample.user@example.com --role-id 456 --role-id 789 --yes

# 判断某人是否为项目成员并查看其角色（CN titan only；只读，非成员返回 is_member=false）
# 被禁用账号仍计为成员，需结合 is_forbidden 判断是否有效
bytedcli tea member check --project-id 123 --email sample.user@example.com
bytedcli --json tea member check --project-id 123 --email sample.user@example.com

# 只建立 dashboard-report 订阅关系，不修改看板布局
bytedcli tea dashboard subscribe-reports --url https://data.example.net/tea-next/project/123/dashboard/456 --report-ids 789 --no-update-layout

# 从报表 URL 获取 DSL（report 类型）
bytedcli tea get-dsl --url https://data.example.net/tea-next/project/3/event-analysis/7447021494577660443?dashboardId=7446993126637437450

# 从快照 URL 获取 DSL（snapshot 类型）
bytedcli tea get-dsl --url https://data.example.net/tea-next/project/3/event-analysis/result/zaa4ac0427bb59b3fbc4589

# 获取 DSL 后直接查询（建议加 --json 便于机器读取）
bytedcli --json tea get-dsl --url https://data.example.net/tea-next/project/3/event-analysis/7447021494577660443 | \
  bytedcli --json tea query

# 按用户输入的 UTC+8 时间覆盖查询窗口；目标 DSL 的 timezone 不会被改写
bytedcli --json tea get-dsl --url https://data.example.net/tea-next/project/3/event-analysis/7447021494577660443 | \
  bytedcli --json tea query \
    --window-start 2026-08-24T00:00:00+08:00 \
    --window-end 2026-08-24T23:59:59+08:00

# 根据 DSL 生成 tea-next 分析结果链接（DSL 通过管道传入，query-type 从 DSL 自动推断）
bytedcli tea get-dsl --url https://data.example.net/tea-next/project/3/event-analysis/7447021494577660443 | \
  bytedcli tea dsl2link

# 根据 DSL 生成链接（直接传入 DSL，query-type 从 DSL content.query_type 自动推断）
# 自动映射：event→event-analysis, retention→retention-analysis, funnel→funnel-analysis, path_find→pathfind-analysis, life_cycle→life_cycle-analysis, event_topk→distribution-analysis, composition→compositon-analysis
bytedcli tea dsl2link --dsl '{"resources":[{"project_ids":[55]}],"content":{"query_type":"event"}}'

# 也可以显式指定 --query-type 覆盖自动推断
bytedcli tea dsl2link --query-type event-analysis --dsl '{"resources":[{"project_ids":[55]}],"content":{}}'

# 查询事件元数据
bytedcli tea get-event --project-id 123 --status 1 --dump ./events.json
bytedcli tea get-event --project-id 123 --events example.play
bytedcli tea get-event --project-id 123 --events example.play,example.view

# 上报单条事件；默认从 bytedcli auth 解析当前用户作为 user_unique_id
bytedcli tea event send --app-id 123456 --event demo_click --param button=submit --param page=home

# 调试上报 payload，不真正发送
bytedcli tea event send --app-id 123456 --event demo_click --params-json '{"page":"home","duration_ms":120}' --dry-run

# 纯设备事件：禁用自动用户解析，显式传 device_id
bytedcli tea event send --app-id 123456 --event device_boot --no-auto-user --device-id device-1

# 查询行为细查行为流（URL 自动解析 project/query/app/time/eventFilterList）
bytedcli tea behavior --url 'https://data.bytedance.net/tea-next/project/<project_id>/behavior-detail/detail?query_id=<id>&query_type=device_id&appId=<app_id>&timestamp=<start_ms>&timestamp=<end_ms>&eventFilterList=%5B%5D&sort=desc' --dump ./behavior.json

# 按公共事件属性和值及时间范围搜索会话回放（titan 模式，扫码登录态）
bytedcli tea session-replay list --project-id 123 \
  --filter sample_property=sample-value --filter another_property=another-value \
  --start 2026-07-14T17:50:00+08:00 --end 2026-07-14T18:00:00+08:00

# 根据搜索结果中的 recording_id 读取操作事件流
bytedcli tea session-replay flow get --project-id 123 --recording-id demo-recording-id \
  --dump ./flow.json

# 获取回放事件元数据 / 播放器原始数据
bytedcli tea session-replay event list --project-id 123 --recording-id demo-recording-id \
  --dump ./events.json
bytedcli tea session-replay play get --project-id 123 --recording-id demo-recording-id \
  --dump ./play.json

# LLM workbench operations-agent 的 agent 会话（SG titan）：ID 取自链接
# /tea-next/project/<project-id>/llm-workbench/operations-agent/<页面>/<space-id>
bytedcli tea operations-agent session list --project-id 123 --space-id 45 --start '7d ago'
# 下一页：next_page_token 原样传给 --page-token，--start / --end 用上一页 JSON 的 start_time / end_time
bytedcli --json tea operations-agent session list --project-id 123 --space-id 45 \
  --start 1788000000 --end 1790000000 --page-token 1001:1790000000000000
# 一个会话的每轮问答和每一步；--full 让 JSON 带每一步完整的 input/output
bytedcli --json tea operations-agent session get --project-id 123 --space-id 45 --session-id 1001

# 行为细查：用精确事件名做服务端前置过滤，避免拉取大量无关埋点
bytedcli tea behavior --project-id 123 --behavior-app-id 456 --query-id '<device_id>' --query-type device_id --start-time 1776096000 --end-time 1776182399 --events example.play,example.view --dump ./behavior.json

# 查询事件元数据（VA 区域）
bytedcli tea get-event --project-id 123 --events example.play --region va

# 按 tea-next URL host 自动推断控制面
bytedcli tea get-dsl --tea-site auto --url https://tea-va.example.net/tea-next/project/302625/funnel-analysis/result/sample-snapshot-id

# 显式指定 VA 控制面
bytedcli tea get-dsl --tea-site va --url https://tea-va.example.net/tea-next/project/302625/funnel-analysis/result/sample-snapshot-id

# 直接覆盖 DataOpen 基址
bytedcli tea query --tea-base-url https://data-va.example.net/dataopen/open-apis --dsl '{"use_app_cloud_id":true,"version":3,"content":{}}'

# 查询事件元数据（JSON 输出数据量大，需搭配 --dump）
bytedcli tea get-event --project-id 123 --events example.play,example.view --json --dump ./events.json

# 查询事件元数据并将原始 JSON 写入文件
bytedcli tea get-event --project-id 123 --events example.play --with params,virtual_params --dump ./events.json

# VA 区域查询
bytedcli tea search --type dashboard_info --url https://data-va.example.net/tea-next/project/3/dashboard/7446993126637437450 --region va
bytedcli --json tea get-dsl --url https://data-va.example.net/tea-next/project/3/event-analysis/7447021494577660443 --region va | \
  bytedcli --json tea query --region va

# SG Lark 租户（titan 模式，扫码即用）
# 先扫码登录一次
bytedcli auth login

# 看板信息（sglark 自动走 titan 模式）
bytedcli tea search --type dashboard_info \
  --url https://tea-sglark.bytedance.net/tea-next/project/<pid>/dashboard/<did>

# 看板报表列表（sglark titan 模式下可直接从响应抽取 DSL）
bytedcli tea report list \
  --dashboard-url https://tea-sglark.bytedance.net/tea-next/project/<pid>/dashboard/<did>

# 拿某个 report 的 DSL（sglark titan 模式下 --dashboard-id 必填；URL 中含 /dashboard/<id> 会自动识别）
bytedcli tea get-dsl \
  --url https://tea-sglark.bytedance.net/tea-next/project/<pid>/event-analysis/<rid>?dashboardId=<did>

# 执行报表分析（sglark titan 模式走三元组 project/dashboard/report）
bytedcli tea query \
  --url https://tea-sglark.bytedance.net/tea-next/project/<pid>/dashboard/<did>/reports/<rid>

# cn / va / sg titan 模式（无需申请 DataOpen App，扫码即用）
bytedcli auth login

# cn 区域 titan 看板信息
bytedcli tea search --type dashboard_info --tea-site cn --auth-mode titan \
  --url https://data.bytedance.net/tea-next/project/<pid>/dashboard/<did>

# va 区域 titan 从 snapshot 链接拿 DSL（走 /analysis/<id>/result?pack_dsl=1，不需要 dashboardId）
bytedcli tea get-dsl --tea-site va --auth-mode titan \
  --url https://tea-va.tiktok-row.net/tea-next/project/<pid>/event-analysis/result/<snapshot-id>

# SG tea-captain 链接：query 阶段也传同一个 --url，避免管道只保留 DSL 后丢失来源 host
URL='https://tea-captain.tiktok-row.net/tea-next/project/<pid>/event-analysis/result/<snapshot-id>'
bytedcli --json tea get-dsl --tea-site auto --auth-mode titan --url "$URL" | \
  bytedcli --json tea query --tea-site auto --auth-mode titan --url "$URL"

# cn 区域 titan 执行查询（与 DataOpen 一样直接 pipe DSL，不需要三元组；CLI 自动轮询异步结果）
bytedcli --json tea get-dsl --tea-site cn --auth-mode titan \
  --url https://data.bytedance.net/tea-next/project/<pid>/event-analysis/result/<snapshot-id> \
  | bytedcli --json tea query --tea-site cn --auth-mode titan
```

## tea analysis（语义化查询，推荐）

`tea analysis` 把 7 个分析模型封装成语义化子命令：直接传事件名、指标、过滤、分组等显式 option，CLI 自动构造 DSL 并投递 `/analysis`，**不需要手写 JSON DSL**。优先用它来回答数据问题；只有需要手搓复杂 DSL（如多层组合指标、特殊 option）时才回退到「动态事件分析」流程。

| 子命令                      | 模型     | 用途一句话                           |
| --------------------------- | -------- | ------------------------------------ |
| `tea analysis event`        | 事件分析 | 单/多事件、渗透率、度量与组合公式    |
| `tea analysis funnel`       | 漏斗分析 | 多步人数、备选路径、逐步转化与流失   |
| `tea analysis retention`    | 留存分析 | 单/多事件对的留存或流失矩阵          |
| `tea analysis composition`  | 用户构成 | 时间窗内按用户属性统计人数与构成占比 |
| `tea analysis path-find`    | 路径分析 | 桑基图，从起点事件追踪后续路径       |
| `tea analysis life-cycle`   | 生命周期 | 用户新增/回流/流失/留存阶段序列      |
| `tea analysis distribution` | 分布分析 | 度量值落在各区间的分布               |

**参数、取值、跨模型差异、鉴权与错误码一律以 CLI Help 为准，本文档不复述。**

- `bytedcli tea analysis --help`：选型指引、跨模型对照（各模型粒度与度量支持范围不同）、字段元数据怎么查、常见错误码。
- `bytedcli tea analysis <model> --help`：该模型的全部参数、可验证规则、经验与示例。

## 动态事件分析

如果用户期望根据指定事件进行多个维度下钻的复杂分析，参考 `references/usages/usages.md`的流程进行。

## Notes

- `tea search` 会从 URL 自动解析 `project_id` 与 `dashboard_id`；其中 `--type dashboard_reports` 底层同 `tea report list`，仅支持 titan 模式。
- `tea report create` 用 `--dsl` 或 `--dsl-file` 创建 report；写接口仅支持 titan 模式，默认走扫码登录态。若还要展示到看板，创建后继续执行 `tea dashboard subscribe-reports`。创建或更新事件报表、排查独立页参数空白和日期不一致时，先读 [报表 UI 配置与迁移](references/report-ui.md)。
- `tea report get` 读取已有 report 配置；`--dsl-only` 只输出 `dsls[--dsl-index].dsl_content`（默认 index 0），适合保存后局部编辑。若要导出后用 `report update` 写回，请使用普通 report detail 路径；dashboard 模式读取 card 内嵌配置，仅用于排查渲染差异。
- `tea report list` 列出 dashboard 当前绑定的 reports；仅支持 titan 模式。该接口单页全量返回，JSON 顶层 `total` 是后端 total，`page=1`，`page_size` = `total`（单页全量，避免 JSON 消费方误判为还有分页），`accessible_count` = 本次返回的可访问 reports 数。
- `tea report update` 原地更新已有 report；写接口仅支持 titan 模式，会先 GET 当前 report，再 PATCH 同一路径，保留线上其它字段，只替换显式传入的 `--dsl/--dsl-file`、`--name`、`--desc`、`--report-type`、`--dsl-name`。用显式 `--project-id/--report-id` 而不是 URL 时需要传 `--tea-site`。
- `tea dashboard subscribe-reports` 订阅已有 report 到 dashboard；写接口仅支持 titan 模式，默认会读取现有 reports/layout，保留已有卡片位置，只给新 report 自动补位置并 PATCH `layout/page_config`。若只想订阅不改布局，传 `--no-update-layout`。
- `tea dashboard subscribe-reports` 的订阅接口会同时传 `report_id` 和 `report_ids`；后端返回 `401003` 表示订阅关系已存在，CLI 按幂等成功处理。验证时 `GET /projects/<pid>/dashboards/<did>/reports` 的返回结构通常是 `{ [dashboardId]: { reports, layout } }`。
- `tea get-dsl` 支持从 stdin 读取 URL；`tea query`（DataOpen 模式）支持从 stdin 读取 DSL JSON。
- `tea behavior` 查询行为细查行为流，支持从 `/behavior-detail/detail` URL 自动解析 `project_id/query_id/query_type/appId/timestamp/eventFilterList/sort`。`--behavior-app-id` 是行为细查请求体 `app_id`；`--app-id` 是 DataOpen 凭证 app id。`--events` 会下发为 OpenAPI `event_name`，用于精确事件名服务端前置过滤。**注意：`--json` 模式下必须搭配 `--dump` 使用**，原始行为流会写入文件。
- `tea session-replay list` 通过 tea-next internal `POST /projects/<pid>/session_replay/analysis` 按公共事件属性和值及时间范围搜索录制。`--filter` 使用 `key=value` 格式并可重复，多个条件按 AND 组合；同一组条件可能命中多个用户和多条回放。该资源组仅支持 CN titan 模式。
- `tea session-replay event list`、`flow get`、`play get` 分别读取录制事件元数据、操作事件流和播放器原始数据。结构化输出统一使用放在 domain 之前的全局 `bytedcli --json tea ...`；事件/操作流在 JSON 模式下必须搭配 `--dump`，播放数据始终必须 `--dump`。dump 文件权限固定为 `0600`。录制过期或被清理时，`play get` 可能返回 `BR_RECORDING_NOT_EXISTS`。
- `tea operations-agent session list` / `get` 读 LLM workbench operations-agent 模块里 agent 的会话，仅 SG titan 模式。接入的 agent 不限于 iDA。`--project-id` 和 `--space-id` 取自链接 `/tea-next/project/<project-id>/llm-workbench/operations-agent/<页面>/<space-id>`（如 `home`、`journeys` 页）；project 只有一个 space 时 `--space-id` 可省，有多个时报错并列出可选的 space。iDA agent ID 推不出这两个 ID。
  - `--start` / `--end` 按会话第一轮的开始时间过滤，默认近 30 天；列表按最近一轮的开始时间倒序。`get` 要求会话在时间窗内开始，否则返回 `TEA_OPERATIONS_AGENT_SESSION_NOT_FOUND`，这时用 `--start` 放宽，不能据此判定会话不存在。
  - 列表翻页：`has_more` 为 true 时把 `next_page_token` 原样传给 `--page-token`，`--start` / `--end` 用上一页 JSON 的 `start_time` / `end_time`（不传时时间窗会随当前时间移动），`--project-id`、`--space-id` 不变。
  - `get` 的 JSON 里每一步的 `input` / `output` 默认截到前 2000 个字符，并带 `input_chars` / `output_chars` 和 `input_truncated` / `output_truncated`；要完整文本加 `--full`。每轮最多读 1000 步、每个会话最多读 100 轮，达到上限时 `steps_truncated` / `rounds_truncated` 为 true，之后的步骤或轮次可能没读到。
  - 某一轮 `steps_found` 为 false 表示 TEA 没有返回这一轮的 trace，这一轮的步骤没读到，不代表这一轮没有步骤。
- `tea get-event` 查询事件元数据；不传 `--events` 时列出全部事件，传入时精确查询一个或多个事件（逗号分隔）。精确查询默认展开 `params`，全量查询默认不展开附加信息；可用 `--with` 显式控制。`--dump <filepath>` 可将原始 JSON 结果写入文件（相对路径基于工作目录）。**注意：`--json` 模式下必须搭配 `--dump` 使用**，原始数据量较大不适合直接输出到终端。
- `--region`：切换 DataOpen 区域（`cn` | `va` | `sg`，默认 `cn`）。使用管道联动时，每个子命令都需要指定 `--region`。
- `--tea-site`：切换控制面（`cn` | `va` | `sg` | `sglark` | `auto`）；需要按 tea-next URL host 路由海外控制面时优先推荐使用。
- SG tea-captain 链接（host 为 `tea-captain.tiktok-row.net` 或 `tea-captain.byteintl.net`）做 `get-dsl | query` 时，query 阶段也传原始 `--url`。现在 sg 默认 host 已切为 `tea-captain.tiktok-row.net`，管道只写 `--tea-site sg` 也能正确路由；但传 `--url` 仍是最稳妥的写法。
- `--tea-base-url`：直接覆盖 DataOpen API 基址，适合调试特殊网关或临时验证。
- `--auth-mode`：`dataopen` / `titan` / `auto`（默认），titan 模式下无需 TEA_APP_ID/SECRET，先 `bytedcli auth login` 扫码登录即可。
- `--project-id`：不传时优先从 URL 自动解析，兜底使用 3。

### Titan 模式说明

Titan 走的是 tea-next 的内部 API（`/datafinder/api/v1/*`），只暴露了一部分 endpoint。下面按命令列出实际能力：

| 命令                                  | dataopen                            | cn / va / sg titan                                                                           | sglark titan                                                                                        |
| ------------------------------------- | ----------------------------------- | -------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------- |
| `tea search --type dashboard_info`    | ✅                                  | ✅                                                                                           | ✅                                                                                                  |
| `tea search --type dashboard_reports` | ❌（dashboard reports 走 internal） | ✅ GET `/projects/<pid>/dashboards/<did>/reports`                                            | ✅ GET `/projects/<pid>/dashboards/<did>/reports`                                                   |
| `tea report create`                   | ❌（写接口仅 tea-next internal）    | ✅ POST `/projects/<pid>/reports`                                                            | ✅ POST `/projects/<pid>/reports`                                                                   |
| `tea report get/update`               | ❌（report 详情写回走 internal）    | ✅ GET/PATCH `/projects/<pid>/reports/<rid>`                                                 | ✅ GET/PATCH `/projects/<pid>/reports/<rid>`                                                        |
| `tea report list`                     | ❌（dashboard reports 走 internal） | ✅ GET `/projects/<pid>/dashboards/<did>/reports`                                            | ✅ GET `/projects/<pid>/dashboards/<did>/reports`                                                   |
| `tea dashboard subscribe-reports`     | ❌（写接口仅 tea-next internal）    | ✅ POST `/projects/<pid>/reports/subscription` + PATCH `/dashboards/<did>`                   | ✅ POST `/projects/<pid>/reports/subscription` + PATCH `/dashboards/<did>`                          |
| `tea get-dsl`                         | ✅ POST `/projects/<pid>/dsls`      | ✅ GET `/analysis/<id>/result?pack_dsl=1`（snapshot/report 都不需要 dashboardId）            | ✅ GET `/dashboards/<did>/reports` 兜底（需要 dashboardId；snapshot URL 不支持）                    |
| `tea query`                           | ✅ POST `/analysis`（同步）         | ✅ POST `/analysis`（异步：返回 `result_id` 后 CLI 自动轮询 `/analysis/<result_id>/result`） | ✅ POST `/reports/<rid>/analysis`（需要 project/dashboard/report 三元组，只能走 URL 或显式三个 ID） |
| `tea behavior`                        | ✅                                  | ❌（内部 API 未暴露 `behaviors/flows_v3`）                                                   | ❌                                                                                                  |
| `tea session-replay *`                | ❌                                  | ✅ CN（VA / SG 未验证）                                                                      | ❌（未验证）                                                                                        |
| `tea operations-agent session *`      | ❌                                  | ✅ SG（CN / VA 未验证）                                                                      | ❌（未验证）                                                                                        |
| `tea role list`                       | ❌                                  | ✅ CN（VA / SG 未验证；只返回 `status=1`）                                                   | ❌（未验证）                                                                                        |
| `tea member invite`                   | ❌                                  | ✅ CN（VA / SG 未验证；默认 dry-run，`--yes` 提交）                                          | ❌（未验证）                                                                                        |
| `tea member check`                    | ❌                                  | ✅ CN（VA / SG 未验证；只读，按邮箱精确匹配）                                                | ❌（未验证）                                                                                        |
| `tea get-event`                       | ✅                                  | ❌（内部 API 未暴露 `metadata/list/events`）                                                 | ❌                                                                                                  |
| `tea get-profile`                     | ✅                                  | ❌（内部 API 未暴露 `metadata/list/user_profiles`）                                          | ❌                                                                                                  |
| `tea get-param`                       | ✅                                  | ❌（内部 API 未暴露 `metadata/list/params`）                                                 | ❌                                                                                                  |
| `tea dsl2link`                        | ✅                                  | ❌（内部 API 未暴露 `dsls/jumper`）                                                          | ❌                                                                                                  |

要点：

- `sglark` 站点只支持 titan 模式；显式传 `--auth-mode dataopen --tea-site sglark` 会报错。
- `tea query` 在 cn / va / sg titan 下与 DataOpen 一样直接传 DSL（通过 `--dsl` 或 stdin），不需要三元组。`/analysis` 是异步 endpoint，CLI 默认轮询超时取 `max(60s, --http-timeout-ms)`；超时会输出 `result_id` 与最近状态，可用同一条命令重试。
- `tea get-dsl` 在 cn / va / sg titan 下走 `GET /analysis/<id>/result?pack_dsl=1`，对 snapshot 与 report URL 都适用，**不需要** `--dashboard-id`。
- `tea get-dsl` 在 sglark titan 下没有 `/analysis/<id>/result` 兜底，必须有 `--dashboard-id`（URL 中含 `dashboardId=` 或 `/dashboard/<id>` 时会自动解析）；snapshot URL 在 sglark 上不支持。
- `tea behavior` / `tea get-event` / `tea get-param` / `tea get-profile` / `tea dsl2link` 在所有区域 titan 模式下都不支持（tea-next 内部 API 没有对应路径），会报 `TEA_TITAN_NOT_SUPPORTED`；想用这些命令必须切到 DataOpen 模式（cn/va/sg）。

## Monitor CRUD

Use the `tea monitor` command group for TEA tea-next monitor management. These endpoints use Titan authentication and the tea-next v2 monitor API.

- List monitors: `bytedcli --json tea monitor list --project-id <project_id> --tea-site cn --auth-mode titan`
- VA/SG: prefer a full tea-next URL with `--url` so the host is preserved.
- Create: `tea monitor create --config-file <monitor.json>`
- Update: `tea monitor update --monitor-id <monitor_id> --config-file <monitor-update.json>`
- Delete: `tea monitor delete --monitor-id <monitor_id> --yes`
- `--status` accepts semantic values `all`, `enabled`, or `disabled`.
- Write operations require a complete JSON object through `--config` or `--config-file`; delete requires explicit `--yes`.
