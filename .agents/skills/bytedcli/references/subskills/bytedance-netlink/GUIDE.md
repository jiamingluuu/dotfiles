---
name: bytedance-netlink
description: "Operate Netlink (DNS/TLB/Forward Proxy/traffic-change business tickets/NetArch observe logs and OLAP metrics) via bytedcli: discover traffic scheduling around IDC QPS changes, search domains and paths, look up deployment info by PSM, fetch topology/servername details, create guarded servername or batched forward-proxy destination-whitelist tickets, approve and deploy active forward-proxy ticket stages, discover Observe namespaces/datasets/fields/options, and query server-side aggregates across CN/BOE/I18N/I18N-TT. Use when tasks mention Netlink, forward proxies, destination-domain whitelists, ticket approval or deployment, traffic scheduling, IDC traffic shifts, NetArch observe logs/metrics/OLAP, Observe namespace/dataset discovery, domain routing, adding a servername location or route path, upstream changes, or PSM deployment lookup."
---

# bytedcli Netlink

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

- Netlink 平台：域名检索、路由/Location 配置排查
- 在一个域名内搜索 path/location
- 拉取 servername(TLB) 配置与拓扑（best-effort）
- 查询正向代理，并为目的域名白名单创建受保护的变更工单
- 按域名和创建时间窗查询原生域名工单；按故障时间窗、PSM、IDC 等线索发现独立的 TI 调流业务工单
- 通过 URL 或域名+路径定位后端 PSM、代码仓库和 RPC 方法

## 前置条件

- 使用通用调用方式：`../../invocation.md`
- 需要鉴权的命令使用个人 ByteCloud JWT。生产网仅在显式设置 `BYTEDCLI_USE_ZTI_JWT=1` 且存在 `SEC_TOKEN_STRING` / `SEC_TOKEN_PATH` 时，CLI 才按目标站点优先执行 ZTI→个人 JWT；交换不可用或失败时自动回退同站点 `bytedcli auth login`。办公网仍使用原有 SSO 链路。

> 执行前缀见 `../../invocation.md`；下面示例直接写 `bytedcli`。

## Quick start

```bash
# 发现 Netlink 支持的站点（best-effort）
bytedcli netlink list-sites

# 搜索域名（CN 默认）
bytedcli netlink search-domain --keyword "api.example.com" --page 1 --page-size 10

# 通过 PSM 反查部署信息（域名 / 集群 / 部署路径）
bytedcli netlink list-services --psm "demo.example.service"
bytedcli netlink list-services --psm "demo.example.service" --page 1 --page-size 20

# 原生域名工单（单页；与 TI 调流工单独立）
bytedcli --site i18n-tt --json netlink ticket list \
  --domain "api.example.com" --start "2026-08-27T14:30:00+08:00" \
  --end "2026-08-27T17:00:00+08:00" --page 1 --page-size 100

# 省略域名，按有界时间窗查询原生工单的单页
bytedcli --site i18n-tt --json netlink ticket list \
  --start "2026-08-27T14:30:00+08:00" --end "2026-08-27T17:00:00+08:00" --page 1

# IDC QPS 阶跃时，查询故障时间窗内的调流工单
bytedcli --json netlink business-ticket list \
  --start "2026-08-27T14:30:00+08:00" \
  --end "2026-08-27T17:00:00+08:00"

# 已有统一工单 ID 或 Netlink 控制台 URL 时读取详情
bytedcli --json netlink business-ticket get --ticket-id 123456

# 列出一个域名的所有 Location 配置（TLB servername locations）
bytedcli netlink list-domain-configs --domain "api.example.com"

# 搜索一个域名内的 path/location
bytedcli netlink search-path --domain "api.example.com" --keyword "demo-path"

# 查看具体 path 的配置（支持 =/path 或 /path）
bytedcli netlink get-path-config --domain "api.example.com" --path "=/v3/chat/demo-path"
bytedcli netlink get-path-config --domain "api.example.com" --path "/v3/chat/demo-path"

# 获取域名拓扑信息（best-effort）
bytedcli netlink get-topology --domain "api.example.com"

# 按 servername id 获取 TLB 完整配置
bytedcli netlink get-servername --servername-id 12345 --unified-platform-id 67890

# 预览单个 location 的 upstream 替换；默认只 dry-run
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

# 先向用户展示 dry-run 的 diff、request 与 version；仅在用户明确确认创建工单后执行
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
  --expected-version 33333 \
  --yes

# 预览为 servername 新增一个 location；默认只 dry-run
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

# 先向用户展示 dry-run 的 diff、request 与 version；仅在用户明确确认创建工单后执行
bytedcli --json netlink servername location create \
  --servername-id 12345 \
  --unified-platform-id 67890 \
  --location "/api" \
  --psm "demo.api.service" \
  --cluster "default" \
  --service-id 22222 \
  --reviewer "demo-reviewer" \
  --platform-reviewer "demo-platform-reviewer" \
  --change-reason "Expose the API entry through the managed gateway" \
  --expected-version 33333 \
  --yes

# 切换环境（BOE / I18N / I18N-TT）
bytedcli --site boe netlink search-domain --keyword "example.com"
bytedcli --site i18n-bd netlink search-domain --keyword "docs.example.com"
bytedcli --site i18n-tt netlink search-domain --keyword "example.com"

# 需要结构化输出时加 --json
bytedcli --json netlink list-domain-configs --domain "api.example.com"

# 搜索正向代理（forward-proxy）
bytedcli netlink forward-proxy search --account "proxy-abc123"
bytedcli netlink forward-proxy search --psm "demo.proxy.service"

# 获取正向代理出口白名单 IP（每行一个）
bytedcli netlink forward-proxy get --account "proxy-abc123" --id 12345 --cluster "normal_flow_fixed_l7" --ips-only

# 预览为正向代理目的域名白名单批量新增 hostname；重复 --domain 或逗号分隔
bytedcli --json netlink forward-proxy whitelist add \
  --account "proxy-abc123" \
  --id 12345 \
  --cluster "normal_flow_fixed_l7" \
  --domain "api.example.com" \
  --domain "assets.example.com,static.example.com" \
  --unified-platform-id 67890 \
  --reviewer "demo-reviewer" \
  --change-reason "Allow a plugin to reach an internal service"

# 展示并确认 dry-run 后，使用返回的 update_time 提交工单
bytedcli --json netlink forward-proxy whitelist add \
  --account "proxy-abc123" \
  --id 12345 \
  --cluster "normal_flow_fixed_l7" \
  --domain "api.example.com" \
  --unified-platform-id 67890 \
  --reviewer "demo-reviewer" \
  --change-reason "Allow a plugin to reach an internal service" \
  --expected-update-time "2026-09-03T10:00:00+08:00" \
  --yes

# 审批人预览当前待审批阶段；必须使用创建结果中的 Netlink main ticket id
bytedcli --json netlink ticket approve --ticket-id 543210

# 向用户展示 dry-run 的工单、阶段、动作和版本；仅在用户明确同意本次审批后，
# 使用 data.plan.ticket.update_time 同意当前阶段
bytedcli --json netlink ticket approve \
  --ticket-id 543210 \
  --expected-update-time "2026-09-04T15:30:00+08:00" \
  --yes

# 主工单审批完成后，单独预览 ByteProxy 子工单 review
bytedcli --json netlink ticket child approve --ticket-id 543210

# 向用户展示 dry-run 的主/子工单、阶段、动作和版本；仅在用户明确同意本次 review 后，
# 使用 data.plan.child_ticket.update_time 显式推进子工单 review
bytedcli --json netlink ticket child approve \
  --ticket-id 543210 \
  --expected-update-time "2026-09-04T15:40:00+08:00" \
  --yes

# 工单发起人预览小流量、全流量或完成阶段；这里以全流量为例
bytedcli --json netlink ticket deploy --ticket-id 543210 --phase full

# 向用户展示 dry-run 的阶段、目标子工单、动作和版本；Metrics 门禁通过且用户明确同意本次发布后，
# 使用 data.plan.child_ticket.update_time 发布
bytedcli --json netlink ticket deploy \
  --ticket-id 543210 \
  --phase full \
  --expected-update-time "2026-09-04T15:45:00+08:00" \
  --yes

# 通过 URL 定位 PSM、代码仓库和 RPC 方法（一步到位）
bytedcli netlink locate --url "api.example.com/v1/demo-path"
bytedcli netlink locate --domain "api.example.com" --path "/v1/demo-path"

# JSON 输出
bytedcli --json netlink locate --url "api.example.com/v1/demo-path"

# 发现当前用户可访问的 namespace；account_id 对应页面 ns_id
bytedcli --json netlink observe namespace list

# 列出空间内可选的数据集，供日志与 OLAP 共用
bytedcli --json netlink observe dataset list --account-id "demo-account-id"

# 按数据集名称、ID 或 dataset_key 做本地包含匹配（不区分大小写）
bytedcli --json netlink observe dataset list \
  --account-id "demo-account-id" --keyword "demo.access"

# 选定数据集后发现字段、操作符和指标支持的聚合函数
bytedcli --json netlink observe field list \
  --account-id "demo-account-id" \
  --dataset-id "demo-dataset-id"

# 在当前时间窗和筛选上下文中查看字段候选值
bytedcli --json netlink observe option list \
  --account-id "demo-account-id" \
  --dataset-id "demo-dataset-id" \
  --target-field env --metric metric_value \
  --region "demo-region" --duration 10m \
  --filter domain:in:api.example.com

# 服务端按时间桶计算指标平均值；这是 OLAP 聚合，不是日志抽样
bytedcli --json netlink observe olap query \
  --account-id "demo-account-id" \
  --dataset-id "demo-dataset-id" \
  --region "demo-region" --duration 1h \
  --select 'avg(metric_value)' \
  --group-by ts --group-by dst_line \
  --granularity 30s --time-zone Asia/Shanghai \
  --filter domain:in:api.example.com

# 查询 NetArch observe 日志明细（JSON 适合 Agent/脚本消费）
bytedcli --json netlink observe log list \
  --account-id "demo-account-id" \
  --dataset-id "demo-dataset-id" \
  --region "demo-region" --duration 10m \
  --filter application_id:in:demo-app-id

# 按 response 字段做本地日志聚合
bytedcli --json netlink observe log aggregate \
  --account-id "demo-account-id" \
  --dataset-id "demo-dataset-id" \
  --region "demo-region" --duration 10m \
  --group-field span_id --sample-size 3
```

## Notes

- `netlink ticket list` 读取原生 `/tickets/` 域名变更工单，`business-ticket` 仍读取 TI 调流单，两者不能互相替代。`--domain` 映射服务端 `name` 搜索；结果保留 `resources` 等原始字段，调用方需据此精确校验域名和资源 ID，不能把子串搜索视为精确归属。
- 原生列表按创建时间查询，默认最近 24 小时，可传 `--start/--end` 或 `--range`。`--domain` 可选；省略时不发送 `name` 参数，返回该窗口的一页工单，输出 `domain=null`。每次只返回一页，输出 `page/page_size/total/total_pages/truncated`；缺失总数或后续页标记时保留 `null`，不代表完整。按返回分页信息继续请求并按工单 ID 去重；信息不足或请求失败时报告覆盖缺口。
- US-TTP 网关不接受 `page_size`，请求会省略该参数，使用服务端默认每页 10 条并保留响应页大小；`--page` 仍有效。其它已登记站点使用所选站点的原生 API 和鉴权目标，不借用 CN 地址。
- 使用全局 `--site` 选择站点（`cn|boe|i18n-bd|i18n-tt|us-ttp`，默认 `cn`）。Per-service `--netlink-site` is a hidden alias for backward compatibility.
- `netlink list-services --psm <psm>` 走 v2 `list_router` 接口反查部署信息（上游按 PSM 精确匹配，不支持模糊）。文本表格展示三列：`ServiceName`(域名) / `TLB Cluster`(集群) / `Location`(部署路径)，并按「域名 + 路径」聚合，仅集群不同的结果合并到同一行的 `TLB Cluster` 列（逗号分隔），域名或路径不同则分行。`--json` 模式返回未聚合的原始 `routers` 行（每行含 `service_name` / `tlb_cluster` / `location`），不含聚合视图。JWT 与请求域名随 `--site` 自动切换。
- `netlink business-ticket list` 查询 `cn|i18n-tt|us-ttp` 对应 TI Platform 时间窗内的 `TRAFFIC_SCHEDULE` 工单，默认最近 24 小时，因此不需要预先知道 business ID、ticket ID 或工单中的实际资源名；`truncated=true` 时缩小时间窗。BOE 和 I18N-BD 未配置该工单路由，命令会明确报错。
- NetArch Observe 仅支持 `cn|boe|i18n-bd|i18n-tt`。`--site us-ttp` 会在鉴权和请求前明确报错，不会回退到 CN Observe。
- `netlink business-ticket get --ticket-id <id-or-url>` 接受 TI Platform 统一工单 ID 或完整 Netlink 控制台 URL；`business_id` 和 `netlink_ticket_id` 不能当作统一工单 ID 使用。
- 若单 IDC QPS 出现阶跃或流量重分配，且 TCE 发布、RM 或 TCC 变更不能解释，应立即用 `business-ticket list` 查询同一时间窗。只有工单时间、资源、IDC 和流量方向都与指标变化一致时，才能归因为调流；generic RCA 的 IDC 标签需要用指标复核。
- `--unified-platform-id` 用于按特定业务平台过滤结果；`list-domain-configs`、`search-path`、`get-path-config`、`get-topology` 会自动从域名的 `business.node_id` 解析，通常无需手动指定；`get-servername` 因无域名上下文，仍需显式传入
- `netlink servername upstream update` 默认只输出 dry-run。文本模式输出摘要，全局 `--json` 输出完整 diff 与 request。命令会精确匹配一个 location，校验当前 PSM/cluster/service id，并确认目标 service id 属于同一 TLB cluster、目标 backend cluster 可从该 TLB cluster 的 IDC 发现；它保留其他 location、service routes 与 servername 字段。提交必须同时传 `--expected-version` 和 `--yes`；命令创建 `auto_deploy=false`、不修改 DNS 的 Netlink 工单，且至少需要一个 `--reviewer` 和一个 `--platform-reviewer`。`--ticket-owner` 默认取当前登录用户，可显式覆盖。
- `netlink servername location create` 为 servername 追加一个新的 location，默认只输出 dry-run。文本模式输出摘要，全局 `--json` 输出完整 diff 与 request。命令会校验该 location 名在 servername 上尚未存在、servername 允许新增 location，并复用与 upstream update 相同的目标校验：目标 service id 属于同一 TLB cluster、目标 backend cluster 可从该 TLB cluster 的 IDC 发现；已有 location 与其余 servername 字段原样保留。`--location` 是 nginx location 名（如 `/api`、`=/health`）；普通路径默认用自身作为 `api_path`，精确匹配 `=/health` 默认推导为 `/health`，正则或命名 location 必须显式传 `--api-path`。`--index` 默认取现有最大 index + 1；`--proxypass-type` 支持 `http`(默认)、`https`、`custom`，选 `custom` 时必须给 `--custom-proxypass`。提交必须同时传 `--expected-version` 和 `--yes`；命令创建 `auto_deploy=false`、不修改 DNS 的 Netlink 工单，且至少需要一个 `--reviewer` 和一个 `--platform-reviewer`。
- 新增 location 前，目标 PSM 必须已经是该 TLB cluster 上的一个 TLB service；若该 PSM 尚未接入，`location create` 会以 `NETLINK_LOCATION_PRECHECK_BLOCKED` 拒绝，需要先在 Netlink 建好上游 service 再重试。
- `netlink forward-proxy search` 支持用 `--account` 或 `--psm` 定位代理；详情命令必须同时传该搜索结果中的 `--account`、`--id` 与 `--cluster`，避免同名或多集群资源歧义。
- `netlink forward-proxy whitelist add` 向 `account_config.dst_host_filter_set.exact_match.allow` 原子追加一批 hostname；`--domain` 可重复或逗号分隔。已有条目原序保留，且不会覆盖 `child_match` 等同级过滤规则；批次内任一域名已存在时整批在本地阻断。命令默认只输出 dry-run；全局 `--json` 会展示完整 diff、endpoint 与 request。提交必须把 dry-run 返回的 `data.plan.source.update_time` 作为 `--expected-update-time` 并加 `--yes`，且至少传一个 `--reviewer`。提交前 CLI 会重读代理详情与灰度路由，若 `update_time`、已有 allow 列表或更新 endpoint 发生变化则拒绝提交；写请求不会自动重试。创建结果会明确区分 `netlink_ticket_id`、`downstream_ticket_id`、`unified_platform_ticket_id` 与 `unified_platform_business_id`；旧字段 `ticket_id`、`unified_platform_id` 分别作为主工单 ID 和业务 ID 的兼容别名保留。
- `netlink ticket approve` 仅处理 `BYTEPROXY` 工单当前阶段的 `common.approve`，参数必须是 `netlink_ticket_id`。命令先检查活动阶段和当前登录人的审批权限，默认 dry-run；必须先向用户展示预览，并在用户明确同意当前审批后，才能带 `data.plan.ticket.update_time` 和 `--yes` 实际提交。提交前会重读工单并重新检查权限，写请求禁用自动重试。
- `netlink ticket child approve` 显式处理主工单审批后的 ByteProxy 子工单系统 review。它要求主工单活动阶段为 `fp_deploy/fp.deploy`、子工单活动阶段为 `review/common.approve`，并通过主工单 `fp.deploy` 推进系统账号 review；不会发布小流量。命令默认 dry-run；必须先向用户展示预览，并在用户明确同意当前 review 后，才能带 `data.plan.child_ticket.update_time` 和 `--yes` 实际提交。提交前会重读主/子工单并重新校验 `fp.deploy` 权限，写请求禁用自动重试。
- `netlink ticket deploy` 使用 Netlink 主工单 ID 自动解析 ByteProxy 子工单，支持 `--phase canary|full|finish`，分别对应小流量、全流量和完成阶段。它不会自动处理子工单 review；`--phase canary` 仅在子工单已进入 `canary/common.canary` 时执行。命令默认 dry-run；必须先向用户展示预览，并在用户明确同意当前发布动作后，才能带 `data.plan.child_ticket.update_time` 和 `--yes` 实际执行。全流量发布会调用平台 Metrics 门禁，观察未完成时拒绝发布且不提供跳过入口。提交前会重读主/子工单、重新校验阶段与当前用户权限，写请求禁用自动重试。
- `locate` 命令支持 `--url`（自动拆分域名和路径）或 `--domain` + `--path` 两种方式；它会依次查询 TLB 路由（Netlink）→ IDL 和仓库信息（Overpass）→ 解析 Thrift IDL 中的 RPC 方法；如果 Overpass 不可用，仍会返回 TLB 路由信息；域名查找支持通配域名兜底匹配，例如 FaaS `*.fn.bytedance.net`；对于可访问的 HTTPS 目标，还会补发 `HEAD` probe 尝试提取 `x-gw-dst-psm`、request id、trace id 等运行时 headers。对于 FaaS gateway 域名，若 probe 命中了 `x-gw-dst-psm`，CLI 会优先使用这个运行时目标 PSM 继续查询 repo / IDL
- `netlink observe log list` 调用 NetArch observe 日志明细接口，沿用上述 ZTI→个人 JWT / SSO fallback；必填 `--account-id`、`--dataset-id`，region 通过 `--region` 或全局 `--vregion` 提供，`--business-id` 是可选的 `x-netlink-business-id`。
- `netlink observe log aggregate` 不调用后端聚合接口；它先查询同一批 `data[]` 明细，再在 CLI 本地按 `--group-field` 字段分组统计。字段缺失归 `(missing)`，空值归 `(empty)`。
- `netlink observe namespace list` 列出当前登录用户可访问的空间，无需预先提供账号；返回的 `account_id` 就是页面 `ns_id`，用于后续 `--account-id`。`--keyword` 按空间 ID/名称做本地、不区分大小写的包含匹配。
- `netlink observe dataset list --account-id <id>` 列出当前空间本地和已订阅且通过页面审批过滤的数据集，供日志与 OLAP 共用；`--keyword` 匹配 ID、名称或 `dataset_key`。JSON 包含查询用 `dataset_id`、名称、类型、引擎、来源 ID、regions、时间字段元数据，以及未展示的 `hidden_pending` / `hidden_rejected` 数量；文本模式在存在被过滤数据集时显示相同计数。订阅场景用 `dataset_id` 查询，不替换成 `origin_dataset_id`。`data_type=log/span` 的数据集也可能用于 OLAP，不按 `olap` 类型过滤。
- 两个发现命令均支持 `--business-id`、正整数毫秒 `--timeout-ms` 及全局 `--site`/`--json`；默认返回过滤后的本次集合，无客户端分页/截断。`returned_count` 是返回条数，不是权限资源总数；空集合为成功，认证或后端失败会明确报错。可选数据集不保证任意查询参数都能执行成功。
- `netlink observe field list` 合并 dimensions 与 measures 元数据，文本和 JSON 均列出字段 ID、来源分组、类型、操作符以及指标支持的聚合函数。发现 namespace/dataset 后运行该命令，再构造 OLAP 查询；同名不同 ID 不会静默合并。
- `netlink observe option list` 通过 `--target-field <name>` 选择要查询候选值的字段；使用 `--metric <name>` 或 `--metric-id <id>` 提供一个指标上下文，二者互斥。候选值是否穷尽、是否采样或受隐含上限约束尚未确认，不能把 `returned_count` 当作全集大小。JSON 中 `count_ratio` 原样保留后端返回的百分数值，文本表格的 `Count %` 列保留两位小数并追加 `%`，不额外缩放；`value` 保留后端原始类型，`label` 仅供展示，筛选时使用 `value`。
- `netlink observe olap query` 提交一次异步 `timeChart` 查询并按 `Progress` 批次序号读取全部结果。`Progress: 0, Total: 1` 表示唯一批次已经返回，不等待 100%。JSON 保留批次边界、`QueryMeta.TimeField`、字段类型、单位、比较数据和原始数字字符串；`complete=true` 只表示预期批次已取回，不承诺后端无 limit 或采样。
- OLAP 构建模式要求具体 `--granularity`（不接受 `auto`）、显式 IANA `--time-zone`、至少一个 `--select 'func(field)'`、以及包含元数据确认时间字段的 `--group-by`。指标名重复时使用 field list 展示的 `name@id`，例如 `--select 'avg(metric_value@demo-field-id)'`；Select 请求仍发送原始字段名，并由 `FieldId` 消歧。后端 `Groups` 协议没有字段 ID，因此 `--group-by` 只接受唯一字段名；同名 group 字段会明确报错。也可用 `--query-json` 或 `--query-file` 传完整、已验证的 `timeChart` 请求体；raw 模式不注入 dataset、region、时间、筛选、缓存或时区，且不能与构建参数混用。
- Observe log 查询窗口使用 `--duration`，或使用 `--start` + `--end`；两种方式不要混用。
- Filter 优先级固定为 `--where-json/--where-file > --filter-json > --filter`。不要混用不同优先级；复杂嵌套条件用 `--where-file`。
- NetArch observe 返回的 row 字段很多；Agent 或脚本消费明细时优先对命令使用全局 `--json` 保留完整 rows。聚合命令在全局 `--json` 模式下保留每个 bucket 的完整 sample rows；文本模式默认展示紧凑字段，`list` 可以用 `--field` 指定展示列，用 `--max-rows` 限制展示行数时会明确提示本地截断。
- 当返回 `returned_count` 接近或等于 `100` 时，按可能命中后端软上限处理，缩短时间窗口或增加过滤条件后重试。
- 常见错误码含义：认证失败通常是 JWT/登录态问题；输入错误通常是缺必填参数、时间窗口或 filter 格式不合法；API 错误表示 NetArch 后端拒绝请求；解析错误表示响应结构和 CLI 预期不一致。

## References

- `references/netlink.md`
