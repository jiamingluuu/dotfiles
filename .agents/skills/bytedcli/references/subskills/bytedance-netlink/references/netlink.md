# Netlink

Netlink 相关能力用于排查域名接入、TLB servername 与 Location(path) 配置。

## 环境与站点

Use global `--site` to select the ByteCloud deployment. Per-service `--netlink-site` is a hidden alias for backward compatibility.

- CN: `--site cn`（默认）
- BOE: `--site boe`
- I18N(BD): `--site i18n-bd`
- I18N-TT: `--site i18n-tt`
- US-TTP: `--site us-ttp`

站点差异（bytedcli 内部已处理）：

- CN/BOE：API host 在 ByteCloud 控制台域名下（`cloud.bytedance.net` / `cloud-boe.bytedance.net`），请求需要 `x-bcgw-tenant-id: bytedance`
- I18N：API host 为 `netlink-i18nbd.byteintl.net`，JWT 从 `cloud.byteintl.net` 获取
- I18N-TT：API host 为 `cloud.tiktok-row.net`，JWT 从 `cloud-i18n.bytedance.net` 获取
- US-TTP：API host 为 `cloud.tiktok-us.net`，JWT 从同站点 ByteCloud 获取
- `business-ticket`：只支持 `cn|i18n-tt|us-ttp`，分别选择对应 TI Platform API 和控制台 JWT 目标；其他站点会明确报错
- NetArch Observe：只支持 `cn|boe|i18n-bd|i18n-tt`；`us-ttp` 会在鉴权和请求前明确报错，不会回退 CN
- forward-proxy：部分接口使用 Netlink 独立网关（如 CN 搜索走 `netlink.bytedance.net`），而详情仍在 ByteCloud 控制台网关下

## 命令映射

- `netlink search-domain`：通过 domain list 搜索域名，返回 `servername_id/namespace_id` 等信息
- `netlink list-services`：通过 PSM 反查部署信息（上游精确匹配，不支持模糊），走 v2 `list_router` 接口，文本表格展示域名(`ServiceName`)、集群(`TLB Cluster`)、部署路径(`Location` Name)，并按「域名 + 路径」聚合（仅集群不同则合并到同一行）；`--json` 返回未聚合的原始 `routers` 行
- `netlink business-ticket list`：在有界创建时间窗内查询 `TRAFFIC_SCHEDULE` 工单
- `netlink business-ticket get`：按 TI Platform 统一工单 ID 或 Netlink 控制台 URL 获取详情
- `netlink list-domain-configs`：拉取 servername 详情并列出所有 Location
- `netlink search-path`：在 servername locations 中按关键字搜索
- `netlink get-path-config`：获取单个 Location（支持 `=/path` 或 `/path`）
- `netlink get-topology`：按域名获取拓扑信息（best-effort）
- `netlink get-servername`：按 servername id 获取完整配置（best-effort）
- `netlink servername upstream update`：精确替换单个 location 的 PSM、backend cluster 与 TLB service id；默认 dry-run，提交需要 servername version 与 `--yes`
- `netlink servername location create`：为 servername 追加一个新的 location（路径 + 上游 PSM/cluster/service id）；默认 dry-run，提交需要 servername version 与 `--yes`
- `netlink forward-proxy search`：按 account 或 PSM 搜索正向代理列表
- `netlink forward-proxy get`：按 account、id、cluster 获取正向代理详情（包含出口白名单 IP）；`--ips-only` 可仅输出白名单 IP 列表（每行一个）
- `netlink forward-proxy whitelist add`：为一个正向代理批量追加目的域名白名单；默认 dry-run，提交需要实时 `update_time` 与 `--yes`
- `netlink ticket approve`：由当前阶段审批人同意一张 `BYTEPROXY` 工单；默认 dry-run，提交需要实时 `update_time` 与 `--yes`
- `netlink ticket child approve`：显式推进 ByteProxy 子工单系统 review；默认 dry-run，不会发布小流量
- `netlink ticket deploy`：按 `canary|full|finish` 阶段发布一张 `BYTEPROXY` 工单；默认 dry-run，提交需要子工单实时 `update_time` 与 `--yes`
- `netlink locate`：通过 URL 或域名+路径一步定位后端 PSM、代码仓库（Overpass）和匹配的 RPC 方法（Thrift IDL 解析）；支持 `--url` 或 `--domain` + `--path`，并支持通配域名兜底匹配（例如 FaaS `*.fn.bytedance.net`）；对于可访问的 HTTPS 目标，还会补发 `HEAD` probe 尝试提取 `x-gw-dst-psm` 等运行时 headers。对于 FaaS gateway 域名，若 probe 命中了 `x-gw-dst-psm`，CLI 会优先使用这个运行时目标 PSM 继续查询 repo / IDL
- `netlink observe log list`：查询 NetArch observe 日志明细
- `netlink observe log aggregate`：查询同一批 observe 日志明细后，在 CLI 本地按 response 字段聚合
- `netlink observe namespace list`：发现当前登录用户可访问的空间，返回用于 `--account-id` 的 ID
- `netlink observe dataset list`：发现指定空间内可选的数据集，供日志与 OLAP 共用
- `netlink observe field list`：列出字段、类型、筛选操作符和指标聚合函数
- `netlink observe option list`：按时间窗和筛选上下文列出字段候选值
- `netlink observe olap query`：提交并完整读取服务端异步 `timeChart` OLAP 聚合

## 参数

- `--unified-platform-id`：按特定业务平台过滤结果；需要收窄结果范围时显式指定

## Forward Proxy 目的域名白名单

先用 `forward-proxy search --account` 或 `--psm` 获取精确的 account、id、cluster 与业务平台信息，再读取详情或准备白名单变更。详情接口要求三个标识同时提供。

`netlink forward-proxy whitelist add` 原子追加一批 `account_config.dst_host_filter_set.exact_match.allow` 条目：

- `--domain` 可重复或逗号分隔；只接收 hostname，不接收带 scheme 或 path 的 URL；比较时忽略大小写与末尾的点
- 批次内任一域名已经存在时整批阻断，不会静默跳过部分条目
- 只替换 `exact_match.allow`；`child_match` 等 `dst_host_filter_set` 同级配置原样保留
- 默认和 `--dry-run` 都不创建工单；全局 `--json` 返回完整 before/after、endpoint 与 request
- CLI 先查询目的域名过滤灰度状态，自动选择专用 dst-filter endpoint 或整账号 endpoint
- 实际提交必须传 dry-run 返回的 `data.plan.source.update_time` 作为 `--expected-update-time`，并加 `--yes`
- 至少传一个 `--reviewer`；提交前会再次校验 account/id/cluster、`update_time`、已有 allow 列表和灰度 endpoint，任一变化都会阻断写入
- 写请求禁用自动重试；若提交结果不确定，先用 `business-ticket list` 检查近期工单，不要直接重复提交

```bash
bytedcli --json netlink forward-proxy whitelist add \
  --account "proxy-abc123" \
  --id 12345 \
  --cluster "normal_flow_fixed_l7" \
  --domain "api.example.com" \
  --domain "assets.example.com,static.example.com" \
  --unified-platform-id 67890 \
  --reviewer "demo-reviewer" \
  --change-reason "Allow a plugin to reach an internal service"
```

创建结果区分 `netlink_ticket_id`、下游 `downstream_ticket_id`、`unified_platform_ticket_id` 和 `unified_platform_business_id`。旧字段 `ticket_id` 与 `unified_platform_id` 分别作为主工单 ID 和业务 ID 的兼容别名保留。审批与发布命令都只接受 Netlink 主工单 ID：

```bash
# 当前审批人先预览；命令同时校验活动阶段与当前登录人的 common.approve 权限
bytedcli --json netlink ticket approve --ticket-id 543210

# 向用户展示 dry-run 的工单、阶段、动作和版本；仅在用户明确同意本次审批后，
# 使用 data.plan.ticket.update_time 同意当前阶段
bytedcli --json netlink ticket approve \
  --ticket-id 543210 \
  --expected-update-time "2026-09-04T15:30:00+08:00" \
  --yes
```

`ticket approve` 仅支持 `BYTEPROXY` 工单。必须先向用户展示 dry-run，并在用户明确同意当前审批后才能实际提交；提交前会重读当前阶段和 `update_time` 并再次校验审批权限，审批写请求禁用自动重试。

主工单审批完成后，子工单 review 必须作为独立步骤执行，不与小流量自动衔接：

```bash
bytedcli --json netlink ticket child approve --ticket-id 543210

# 向用户展示 dry-run 的主/子工单、阶段、动作和版本；仅在用户明确同意本次 review 后，
# 使用 data.plan.child_ticket.update_time
bytedcli --json netlink ticket child approve \
  --ticket-id 543210 \
  --expected-update-time "2026-09-04T15:40:00+08:00" \
  --yes
```

`ticket child approve` 通过主工单 `fp.deploy` 推进由系统账号负责的 ByteProxy 子工单 review，不直接调用小流量动作。必须先向用户展示 dry-run，并在用户明确同意当前 review 后才能实际提交；提交前会重读主/子工单、校验两个活动阶段、版本和当前登录人的 `fp.deploy` 权限，写请求禁用自动重试。

发布阶段同样默认 dry-run，并显式区分小流量、全流量与完成：

```bash
# phase 可选 canary、full、finish
bytedcli --json netlink ticket deploy --ticket-id 543210 --phase full

# 向用户展示 dry-run 的阶段、目标子工单、动作和版本；仅在用户明确同意本次发布后，
# 使用 data.plan.child_ticket.update_time 执行当前阶段
bytedcli --json netlink ticket deploy \
  --ticket-id 543210 \
  --phase full \
  --expected-update-time "2026-09-04T15:45:00+08:00" \
  --yes
```

`ticket deploy` 会从主工单解析 ByteProxy 子工单。必须先向用户展示 dry-run，并在用户明确同意当前发布动作后才能实际提交；提交前重读主/子工单、校验阶段和当前用户权限。它不会自动处理子工单 review；`--phase canary` 仅在子工单已进入 `canary/common.canary` 后执行。`--phase full` 还会执行平台 Metrics 门禁；观察窗口未完成时阻断发布，CLI 不提供紧急跳过 Metrics 的入口。所有发布写请求禁用自动重试；响应不确定时应先回查工单，不能直接重试。

## Location upstream 更新

`netlink servername upstream update` 只修改一个精确匹配的 location upstream 三元组：

- `--from-psm`、`--from-cluster`、`--expected-service-id` 必须与实时配置一致
- `--to-psm`、`--to-cluster`、`--target-service-id` 指定目标 upstream；CLI 会确认目标 service id 属于 servername 所在的同一个 TLB cluster，并验证目标 backend cluster 可从该 TLB cluster 的 IDC 发现
- 默认和 `--dry-run` 都不创建工单；文本模式返回摘要，全局 `--json` 返回完整 diff 与 request
- 实际提交必须传 dry-run 返回的 `--expected-version` 并加 `--yes`；执行前必须向用户展示 dry-run 的 diff、request 与 version，并取得用户对创建工单的明确确认
- 必须传至少一个 `--reviewer` 和一个 `--platform-reviewer`；`--ticket-owner` 默认取当前登录用户，可显式覆盖
- 命令保留 service routes 和未选中的 location，设置 `auto_deploy=false`，不修改 DNS

```bash
bytedcli --json netlink servername upstream update \
  --servername-id 12345 \
  --unified-platform-id 67890 \
  --location "/" \
  --from-psm "demo.legacy.gateway" \
  --from-cluster "default" \
  --expected-service-id 11111 \
  --to-psm "demo.web.gateway" \
  --to-cluster "default" \
  --target-service-id 22222 \
  --reviewer "demo-reviewer" \
  --platform-reviewer "demo-platform-reviewer" \
  --change-reason "Move the web entry to the managed gateway" \
  --dry-run
```

## Location 新增

`netlink servername location create` 在 servername 上追加一个新的 location，不改动任何已有 location：

- `--location` 是 nginx location 名（如 `/api`、`=/health`），该名在 servername 上必须尚未存在；要改已有 location 的上游用 `netlink servername upstream update`
- `--psm`、`--cluster`、`--service-id` 指定新 location 的上游；校验方式与 upstream update 一致：目标 service id 必须属于 servername 所在的同一个 TLB cluster，目标 backend cluster 必须可从该 TLB cluster 的 IDC 发现
- 目标 PSM 必须已经是该 TLB cluster 上的一个 TLB service；尚未接入的 PSM 会被 `NETLINK_LOCATION_PRECHECK_BLOCKED` 拒绝，需要先在 Netlink 建好上游 service
- 普通路径默认用自身作为 `--api-path`，精确匹配 `=/health` 默认推导为 `/health`；正则或命名 location 必须显式传 `--api-path`。`--index` 默认取现有最大 index + 1；`--proxypass-type` 支持 `http`(默认)、`https`、`custom`，选 `custom` 时必须给 `--custom-proxypass`
- 默认不创建工单；文本模式返回摘要，全局 `--json` 返回完整 diff 与 request
- 实际提交必须传 dry-run 返回的 `--expected-version` 并加 `--yes`；执行前必须向用户展示 dry-run 的 diff、request 与 version，并取得用户对创建工单的明确确认
- 必须传至少一个 `--reviewer` 和一个 `--platform-reviewer`；`--ticket-owner` 默认取当前登录用户，可显式覆盖
- 命令保留已有 location 与其余 servername 字段，设置 `auto_deploy=false`，不修改 DNS；若提交前 servername 的 version 或 location 列表发生变化，提交会被拒绝

```bash
bytedcli --json netlink servername location create \
  --servername-id 12345 \
  --unified-platform-id 67890 \
  --location "/api" \
  --psm "demo.api.service" \
  --cluster "default" \
  --service-id 22222 \
  --reviewer "demo-reviewer" \
  --platform-reviewer "demo-platform-reviewer" \
  --change-reason "Expose the API entry through the managed gateway"
```

## NetArch Observe

Observe 命令需要个人 ByteCloud JWT。生产网仅在显式设置 `BYTEDCLI_USE_ZTI_JWT=1` 且存在 `SEC_TOKEN_STRING` / `SEC_TOKEN_PATH` 时才优先执行 ZTI→JWT；不可用或失败时回退同站点 `bytedcli auth login`。可用 `bytedcli --json auth status` 检查当前认证来源。

推荐流程是先发现 namespace、dataset 和字段，再查看候选值，最后执行日志或服务端 OLAP 查询：

```bash
bytedcli --json netlink observe namespace list --keyword demo

bytedcli --json netlink observe dataset list \
  --account-id "demo-account-id" --keyword "demo.access"

bytedcli --json netlink observe field list \
  --account-id "demo-account-id" \
  --dataset-id "demo-dataset-id"

bytedcli --json netlink observe option list \
  --account-id "demo-account-id" \
  --dataset-id "demo-dataset-id" \
  --target-field env --metric metric_value \
  --region "demo-region" --duration 10m \
  --filter domain:in:api.example.com

bytedcli --json netlink observe olap query \
  --account-id "demo-account-id" \
  --dataset-id "demo-dataset-id" \
  --region "demo-region" --duration 1h \
  --select 'avg(metric_value)' \
  --group-by ts --group-by dst_line \
  --granularity 30s --time-zone Asia/Shanghai \
  --filter domain:in:api.example.com
```

- `field list` 合并 dimensions 与 measures 元数据。文本和 JSON 均保留字段 ID；JSON 还包含 `source_groups`、dimensions 类型、操作符详情和 metric 自身的数据类型、默认/支持聚合函数；同名不同 ID 分开返回。
- `option list` 通过 `--target-field <name>` 选择要查询候选值的字段，并使用互斥的 `--metric <name>` 或 `--metric-id <id>` 提供指标上下文。候选项是否穷尽、是否采样或受隐含上限约束尚未确认；JSON 中 `count_ratio` 原样保留后端返回的百分数值，文本表格的 `Count %` 列保留两位小数并追加 `%`，不额外缩放；`value` 是筛选应使用的原始值，`label` 仅供展示。
- `olap query` 构建模式接受 `func(field)` 聚合表达式；同名指标用 `func(name@id)` 消歧。CLI 通过 metadata 校验 ID 与支持函数，Select 请求发送原始字段名和 `FieldId`。后端 `Groups` 协议没有字段 ID，因此 `--group-by` 只接受唯一字段名；同名 group 字段会明确报错。`timeChart` 必须显式传具体 `--granularity` 和 IANA `--time-zone`，不接受 `auto`，并要求 `--group-by` 包含 metadata 的 time 字段。
- 完整请求体可通过 `--query-json` 或 `--query-file` 传入。raw 模式不自动注入 dataset、region、时间、筛选、缓存或时区，且不能与这些构建参数混用；只承诺经过验证的 `timeChart` 协议，不是任意图表或 SQL 执行入口。
- OLAP 的 `Progress` 是批次序号，`Total` 是总批次数。`Progress: 0, Total: 1` 已完成唯一批次；空 `Data` 是未就绪，CLI 会在同一整体 deadline 内继续轮询。JSON 保留批次边界、`QueryMeta.TimeField` / `FieldType`、`UnitConf`、`ContentCmp`、`Statistics` 和数字字符串。`complete=true` 只代表本次预期批次均已取回。

### namespace 与 dataset 发现

- namespace 命令无需 `--account-id`，返回当前用户可访问的空间。输出 `account_id` 对应页面 URL 的 `ns_id`，是后续所有 Observe 命令的 `--account-id`。
- dataset 命令必填 `--account-id`，返回该空间本地和已订阅的可选数据集，沿用页面审批过滤；公共目录中尚未订阅的资源不属于默认结果。
- `--keyword` 是本地、不区分大小写的包含匹配：空间匹配名称/ID，数据集匹配名称/ID/`dataset_key`。空字符串应省略，不能传空白筛选。
- 两个命令支持全局 `--site`/`--json`、可选 `--business-id` 和 `--timeout-ms <正整数毫秒>`；无需查询时间窗和 region。
- 文本显示完整 ID 与摘要；JSON 的 `namespaces`/`datasets` 包含资源列表，`returned_count` 为过滤后返回条数。dataset 结果还稳定返回 `hidden_pending` / `hidden_rejected`，表示当前 `--keyword` 命中但因审批状态未展示的数量；文本模式在任一计数非零时输出 warning。无客户端分页/截断，也不把返回条数冒充服务端总数。
- dataset JSON 包含 `dataset_id`、`name`、`dataset_key`、`description`、`data_type`、`storage_engine`、`source_type`、`origin_dataset_id`、`origin_account_id`、`regions`、`time_attribute_id`、`time_attribute_units` 和 `period`；缺失元数据为 `null`，缺失 regions 为 `[]`。JSON 不包含存储连接配置。
- 订阅数据集用当前空间的 `dataset_id` 继续查询，来源 `origin_dataset_id` 仅用于解释来源。`source_type=shared` 可以是本地数据集；`data_type=log/span` 也可能支持 OLAP。
- 同名资源按 ID 区分。无结果返回成功空集合；权限、接口或响应格式失败明确报错。空间成员关系和 dataset 可选状态不保证任意时间窗、region、字段组合查询成功。

### 日志查询

`netlink observe log list` 查询 NetArch observe 日志明细接口。Agent 或脚本消费明细时优先使用全局 `--json`，以保留完整 rows、查询窗口、region、返回条数和 warning 信息：

```bash
bytedcli --json netlink observe log list \
  --account-id "demo-account-id" \
  --business-id "demo-business-id" \
  --dataset-id "demo-dataset-id" \
  --region "demo-region" \
  --duration 10m \
  --filter application_id:in:demo-app-id
```

也可以用绝对时间窗口：

```bash
bytedcli --json netlink observe log list \
  --account-id "demo-account-id" \
  --dataset-id "demo-dataset-id" \
  --region "demo-region" \
  --start 1780214400 \
  --end 1780215000 \
  --filter-json '{"Field":"span_id","Operator":"in","Value":["demo-span-id"]}'
```

协议映射：

- `--account-id` -> `x-netarch-account-id` header，必填
- `--business-id` -> optional `x-netlink-business-id` header
- `--dataset-id` -> body `From`，必填
- `--region` / global `--vregion` -> body `Regions`；`--region` 可重复或逗号分隔，未传时回退全局 `--vregion`
- `--start` / `--end` or `--duration` -> body `StartTime` / `EndTime`；默认相对窗口可用于快速查询，精确复现页面结果时用绝对 Unix seconds；最大窗口 `7d`
- `--times` -> body `Times`，默认 `1`，最大 `100`
- `--where-json` / `--where-file` -> raw body `Where`
- `--filter-json` / `--filter field:operator:value1,value2` -> backend leaf filters wrapped in the browser-compatible nested `Where`
- `list --field` -> list 文本输出展示列；JSON 输出仍保留完整 row
- `list --max-rows` -> list 本地文本展示行数限制，不改变后端查询；实际截断时会输出展示行数提示

Filter 优先级固定为 `--where-json/--where-file > --filter-json > --filter`。不同优先级不要混用；需要复杂嵌套条件或复现浏览器抓包时使用 raw `Where`，简单字段过滤使用 `--filter`。

`netlink observe log aggregate` performs local grouping over returned rows. It does not call a backend aggregation endpoint; it first queries the same detail rows as `list`, then groups them locally by `--group-field`. Missing fields are grouped as `(missing)`, and empty string values as `(empty)`. It does not expose `--field` or `--max-rows`; use `--sample-size` to control sample rows per bucket.

```bash
bytedcli --json netlink observe log aggregate \
  --account-id "demo-account-id" \
  --dataset-id "demo-dataset-id" \
  --region "demo-region" \
  --duration 10m \
  --group-field span_id \
  --sample-size 3
```

When `returned_count` is close to or equals `100`, treat it as a possible backend soft cap. Narrow the time window with `--duration` or `--start`/`--end`, or add filters before drawing conclusions from the result set.

High-level error-code meaning:

- Auth errors: ZTI exchange or login/JWT state is unavailable, expired, or rejected by NetArch; inspect `bytedcli --json auth status`, then log in to the target site only when no reusable credential is available.
- Input errors: required options, region fallback, time window, or filter JSON/compact filter syntax is invalid.
- API errors: NetArch returned a failure envelope, such as account, dataset, region, or permission rejection.
- Parse errors: the backend response shape did not match the expected observe-log success envelope.
