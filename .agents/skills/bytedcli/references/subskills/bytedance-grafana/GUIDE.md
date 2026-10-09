---
name: bytedance-grafana
description: "Use bytedcli Grafana for dashboard search/info, panel data or screenshots, dashboard/group/panel/variable/link CRUD and Metrics link injection."
---

# bytedcli Grafana

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

- Grafana 大盘的增删查改
- 大盘分组（Row）管理
- 面板的创建、更新、删除、查询
- 大盘变量与链接管理
- Metrics 链接注入
- 搜索大盘、按 URL/UID 获取大盘摘要、按 panel 查询数据
- 面板截图

## 前置条件

- 使用通用调用方式：`../../invocation.md`
- 认证：所有 `grafana ...` 命令统一通过 `X-JWT-Token` 调用 Grafana/OpenAPI。默认保持当前用户的 ByteCloud JWT；显式传全局 `--as app` 或设置 `BYTECLOUD_AUTH_AS=app` 时，严格使用对应 site 的应用账号 JWT，不回退个人身份。收到服务端 401 时只强刷同一身份的 JWT 并**最多重试一次**。纯服务器/远程 devbox 不依赖浏览器 Cookie。
- 登录：个人模式下 ByteCloud Auth 未就绪时运行 `bytedcli auth login`；应用模式先用 `bytedcli auth app status --refresh` 检查配置，再以 `bytedcli --as app grafana ...` 调用。执行本 skill 时**禁止**运行 `bytedcli auth login --session`，禁止读取或回退到 `grafana_session` / `grafana_session_v1`，也不要把 JWT 放进 `Authorization: Bearer`。
- 实例边界：`infra-grafana.byted.org` 当前不接受 `X-JWT-Token`，且只用于 APM FaaS MQ trigger datasource proxy。遇到该域名时不要用本 skill 或回退 session；改用 `bytedance-apm` skill 的 `apm faas-mq-trigger metrics|lag`。
- 生产网用：`export BYTEDCLI_NETWORK_PROFILE=prod`（i18n-bd / i18n-tt / us-ttp / eu-ttp 切到 `-api` 域名）

> 示例省略 invocation 前缀。

## Quick start

```bash
# V7 是默认行为
bytedcli --json grafana search "demo service"
bytedcli --json grafana info "demo-uid"
bytedcli --json grafana query "demo-uid" --panel 123 --from now-30m --to now --var dc=hl

# 无人值守只读排查：应用账号必须显式选择 --as app
bytedcli --as app --json grafana info "demo-uid"
bytedcli --as app --json grafana query "demo-uid" --panel 123 --from now-30m --to now

# V10：仅传 UID/search/create 时必须显式选择版本
bytedcli --json grafana search "demo service" --grafana-version v10
bytedcli grafana dashboard create --title "demo-v10-dashboard" --folder-uid "demo-folder-uid" --grafana-version v10

# V10：完整 URL 会按 allowlist host 自动推断，不需要重复传版本
bytedcli --json grafana dashboard get --url "https://grafana-10.bytedance.net/d/demo-uid/demo-slug"
bytedcli --json grafana info "https://grafana-10.bytedance.net/d/demo-uid/demo-slug?var-dc=lf"

# 不知道 panel ID 时，先 info 看 panels[].id/title，再把选中的 id 传给 query
bytedcli --json grafana info "demo-uid"
bytedcli --json grafana query "demo-uid" --panel 123

# 大盘
bytedcli grafana dashboard get --uid "demo-uid"
bytedcli --json grafana dashboard describe --url "https://grafana-10.bytedance.net/d/demo-uid/demo-slug"
bytedcli grafana dashboard create --title "demo-dashboard"
# 用从 Grafana UI 导出的完整 JSON 重新提交（保留 time/refresh/tags/timezone 等设置）
bytedcli --json grafana dashboard create --title "demo-dashboard" \
  --dashboard-json "$(jq -c . exported.json)" \
  --time-json '{"from":"now-6h","to":"now"}' --refresh 1m \
  --tags "flink,sid-stream" --graph-tooltip crosshair
bytedcli grafana dashboard update --uid "demo-uid" --title "demo-updated"
bytedcli grafana dashboard delete --uid "demo-uid"

# 分组
bytedcli grafana group list --uid "demo-uid"
bytedcli grafana group create --uid "demo-uid" --title "demo-group"
bytedcli grafana group get --uid "demo-uid" --group-title "demo-group"

# 面板
bytedcli grafana panel list --uid "demo-uid"
bytedcli grafana panel get --uid "demo-uid" --panel-id 123
bytedcli grafana panel create --uid "demo-uid" --panel-json '{"title":"demo-panel","type":"graph"}'
# V10 新建 panel 默认 timeseries，并无损保留 datasource {type,uid} 与 options.legend
bytedcli grafana panel create --uid "demo-uid" --grafana-version v10 --panel-json '{"title":"demo-timeseries","datasource":{"type":"demo-sql","uid":"demo-ds-uid"},"options":{"legend":{"displayMode":"table","placement":"bottom"}}}'
# V7 使用 /api/tsdb/query；V10 普通 datasource 使用 /api/ds/query；OpenTSDB 使用 UID proxy
bytedcli --json grafana panel query --uid "demo-uid" --panel-id 123 --from now-1h --to now --var applicationId=application_demo_123
bytedcli --json grafana panel query --uid "demo-uid" --panel-id 123 --grafana-version v10 --from now-1h --to now

# 变量
bytedcli grafana variable get --uid "demo-uid"
bytedcli grafana variable update --uid "demo-uid" --variables-json '[{"name":"interval","type":"custom","query":"30s,1m,5m"}]'

# 链接
bytedcli grafana link get --uid "demo-uid"

# 工具
bytedcli grafana inject-metrics-links --uid "demo-uid"
bytedcli grafana data --url "https://grafana-10.bytedance.net/d/demo-uid/demo-slug?viewPanel=123"
bytedcli grafana screenshot --url "https://grafana-10.bytedance.net/d/demo-uid/demo-slug?viewPanel=123"
```

## 命令速查

```bash
grafana search <keyword> [--limit <limit>] [--grafana-version <v7|v10>]
grafana info <url-or-uid> [--grafana-version <v7|v10>]
grafana query <url-or-uid> [--panel <id>] [--from <time>] [--to <time>] [--var <KEY=VALUE>] [--timeout <duration>] [--grafana-version <v7|v10>]
grafana dashboard create --title <title> [--folder-id <id> | --folder-uid <uid>] [--panels-json <json>] [--templating-json <json>] [--links-json <json>] [--dashboard-json <json>] [--tags <a,b>] [--time-json <json>] [--refresh <interval|false>] [--timezone <tz>] [--timepicker-json <json>] [--graph-tooltip <off|crosshair|tooltip>] [--annotations-json <json>] [--schema-version <n>] [--grafana-version <v7|v10>]
grafana dashboard get (--uid <uid> | --url <url>) [--grafana-version <v7|v10>]
grafana dashboard describe --url <url> [--grafana-version <v7|v10>]
grafana dashboard update (--uid <uid> | --url <url>) [--title <title>] [--panels-json <json>] [--templating-json <json>] [--links-json <json>] [--tags <a,b>] [--time-json <json>] [--refresh <interval|false>] [--timezone <tz>] [--timepicker-json <json>] [--graph-tooltip <off|crosshair|tooltip>] [--annotations-json <json>] [--schema-version <n>] [--grafana-version <v7|v10>]
grafana dashboard delete (--uid <uid> | --url <url>) [--grafana-version <v7|v10>]
grafana variable get (--uid <uid> | --url <url>) [--grafana-version <v7|v10>]
grafana variable update (--uid <uid> | --url <url>) --variables-json <json> [--mode <append|overwrite>] [--grafana-version <v7|v10>]
grafana link get (--uid <uid> | --url <url>) [--grafana-version <v7|v10>]
grafana link update (--uid <uid> | --url <url>) --links-json <json> [--mode <append|overwrite>] [--grafana-version <v7|v10>]
grafana group create (--uid <uid> | --url <url>) --title <title> [--collapsed] [--position-json <json>] [--grafana-version <v7|v10>]
grafana group get (--uid <uid> | --url <url>) (--group-id <id> | --group-title <title>) [--no-panels] [--grafana-version <v7|v10>]
grafana group list (--uid <uid> | --url <url>) [--keyword <keyword>] [--grafana-version <v7|v10>]
grafana group update (--uid <uid> | --url <url>) (--group-id <id> | --target-group-title <title>) [--title <title>] [--collapsed] [--position-json <json>] [--grafana-version <v7|v10>]
grafana group delete (--uid <uid> | --url <url>) (--group-id <id> | --group-title <title>) [--keep-panels] [--grafana-version <v7|v10>]
grafana panel create (--uid <uid> | --url <url>) --panel-json <json> [--group-id <id>] [--target-group-title <title>] [--position-json <json>] [--enable-compare <offsets>] [--grafana-version <v7|v10>]
grafana panel get (--uid <uid> | --url <url>) (--panel-id <id> | --panel-title <title>) [--grafana-version <v7|v10>]
grafana panel list (--uid <uid> | --url <url>) [--keyword <keyword>] [--grafana-version <v7|v10>]
grafana panel update (--uid <uid> | --url <url>) (--panel-id <id> | --panel-title <title>) [--panel-json <json>] [--group-id <id>] [--target-group-title <title>] [--position-json <json>] [--enable-compare <offsets>] [--grafana-version <v7|v10>]
grafana panel delete (--uid <uid> | --url <url>) (--panel-id <id> | --panel-title <title>) [--grafana-version <v7|v10>]
grafana panel query (--uid <uid> | --url <url>) [--panel-id <id> | --panel-title <title>] [--from <time>] [--to <time>] [--var <KEY=VALUE>] [--datasource <name>] [--datasource-id <id>] [--sql <sql>] [--grafana-version <v7|v10>]
grafana inject-metrics-links (--uid <uid> | --url <url>) [--grafana-version <v7|v10>]
grafana data --url <url> [--timeout <duration>] [--grafana-version <v7|v10>]
grafana screenshot --url <url> [--width <px>] [--height <px>] [--timeout <duration>] [--device-scale-factor <factor>] [--only-data] [--grafana-version <v7|v10>]
grafana expr-parse --url <url> [--grafana-version <v7|v10>]
```

## 便捷查询入口

- `grafana info <url-or-uid>` 会合并输出 dashboard 标题、URL 中的 `var-*` 变量、模板变量列表和展开后的面板列表；collapsed row 内的子面板也会列出。JSON 模式下从 `data.panels[]` 读取 `id/title/groupTitle/datasource/targets_count`，用于选择下一步 `grafana query --panel <id>`。
- `grafana search <keyword>` 走 Grafana 原生搜索 API，返回匹配 dashboard 的 `uid/title/url/tags` 等字段。
- `grafana query <url-or-uid>` 会复用 URL 里的 `from/to/viewPanel/panelId/var-*`，也可用 `--panel`、`--from`、`--to`、重复 `--var KEY=VALUE` 覆盖；多值变量会按重复 `var-*` 参数保留。
- 当用户给的是 dashboard URL 且不知道 panel ID，不要猜 panel ID，也不要发明 `--panel-title` / `--panel-keyword` 参数；先执行 `bytedcli --json grafana info <url>`，根据用户意图在 `data.panels[]` 里挑选候选 panel，再执行 `bytedcli --json grafana query <url> --panel <id>`。若无法唯一判断，回复候选 panel 的 `id/title/groupTitle`。
- `grafana info/query` 支持现代 `/d/<uid>/<slug>` URL，也支持老式 `/dashboard/db/<slug>` URL；`query` 对已知 Forge 指标大盘的 fountain read 面板会本地转换为现代 URL，其他老式 URL 会先解析为真实 UID。
- `grafana query` 对已知 Forge 指标大盘的 fountain read 面板会优先从 URL 变量合成 Metrics FE Byteplot 查询；其余面板先尝试 Cloud Grafana OpenAPI，失败后读取 dashboard JSON，将 ByteTSD panel target 转成 Metrics FE Byteplot 查询。真正点位请求按 datasource / Grafana host 选择 CN / ROW / EU-TTP / US-TTP 对应 Metrics FE 后端。
- `grafana data` 先调用公司 OpenAPI；V10 OpenAPI data 不兼容时会读取 panel 与 datasource 元数据：普通 datasource 回退到 `/api/ds/query`，OpenTSDB/ByteTSD datasource 直接回退到 `/api/datasources/proxy/uid/<uid>/api/query`，不会先探测 `/api/ds/query`，也不会切到 V7。所有兼容路径都失败时返回 `GRAFANA_V10_OPENAPI_UNSUPPORTED`，`details` 会分别保留 OpenAPI、direct datasource 与 Byteplot 错误。
- `grafana panel query` 按实例和真实 datasource type 使用版本化 adapter：V7 保持 `/api/tsdb/query` + datasource 数字 ID + Arrow dataframe 解码；V10 普通 datasource 使用 `/api/ds/query` + datasource `{type,uid}` + JSON frames；V10 OpenTSDB/ByteTSD 使用 UID datasource proxy，并将 panel 的 metric、aggregator、tenant、downsample、tags/filters、模板变量和 compact multi-field 转成浏览器同款请求。`--to now` 与浏览器一致不发送 `end`，显式历史结束时间发送 epoch milliseconds。输出都保留 `columns`、`column_names`、`row_count`、`datasource_uid`/`datasource_type`；`query_api` 取值为 `tsdb`、`ds` 或 `opentsdb_proxy`。OpenTSDB 使用 `time/value/metric/tags/aggregate_tags/series` 长表列，多 series 不互相覆盖；HTTP 200 + `[]` 是成功的零行结果，不是查询失败。
- 对于单个 Bosun/ByteTSD 点位表达式，优先使用 `bytedcli apm bosun query "sum:store:example.metric" --duration 10m --all-regions` 或 `bytedcli apm metric query ...`，不要为了点位查询反向拼 Grafana URL。

## Bosun 表达式格式（重要）

创建/更新面板时，targets 中的 `expr` 必须使用标准 Bosun `nv(q(...))` 语法，分两种格式：

**非多值指标**（QPS使用 `rate{counter}:`）：

```
$child= nv(q("sum:30s-avg-zero:rate{counter}:指标名{}{}","$start", "30s"),0)
$child
```

示例：

```json
{
  "title": "激活成功率",
  "targets": [
    {
      "expr": "$child= nv(q(\"sum:30s-avg-zero:rate{counter}:caijing.fe.akali.do_active_success{}{}\",\"$start\", \"30s\"),0) \n$mother = nv(q(\"sum:30s-avg-zero:rate{counter}:caijing.fe.akali.do_active{}{}\",\"$start\", \"30s\"),0) \n$child/$mother"
    }
  ]
}
```

**多值指标**（QPS使用 `.delta_counter` + `[rate]`）：

```
$child= nv(q("sum:30s-avg-zero:指标名.delta_counter{}{}[rate]","$start", "30s"),0)
$child
```

示例：

```json
{
  "title": "绑卡量",
  "targets": [
    {
      "expr": "$child= nv(q(\"sum:30s-avg-zero:kepler.finance_fe.monitor.wallet_bcard_institution_bind_result.delta_counter{}{}[rate]\",\"$start\", \"30s\"),0) \n$child"
    }
  ]
}
```

**转化率（多变量除法）**：

```json
{
  "title": "激活转化率",
  "targets": [
    {
      "expr": "$child= nv(q(\"sum:30s-avg-zero:rate{counter}:caijing.fe.akali.do_active_success{}{}\",\"$start\", \"30s\"),0) \n$mother= nv(q(\"sum:30s-avg-zero:rate{counter}:caijing.fe.akali.do_active{}{}\",\"$start\", \"30s\"),0) \n$child/$mother"
    }
  ]
}
```

### Bosun 分组与过滤语法

指标格式：`metric{group}{filter}`，两个 `{}` 分别是分组条件和过滤条件。

- **分组 `{group}`**（= SQL GROUP BY）
  - `{tag=*}`：按 tag 值分组展示
  - `{}`：不分组（聚合所有数据）
- **过滤 `{filter}`**（= SQL WHERE）
  - `{tag=value}`：精确匹配
  - `{tag=literal_or(a|b|c)}`：WHERE IN（区分大小写）
  - `{tag=not_literal_or(a|b)}`：WHERE NOT IN
  - `{tag=wildcard(*.douyin.com)}`：通配符匹配
  - `{tag=regexp(data\\-[0-9])}`：正则匹配
  - 多条件逗号分隔：`{host=web*, dc=lf}`
- **注意**：两个 Group 必须互为子集才能运算，否则报 `unjoined group`

示例：按 method 分组，过滤 err_code=0：

```
sum:30s-avg-zero:rate{counter}:metric{method=*}{err_code=literal_or(0)}
```

### 注意事项

- 不要传简单的 `metric{tag}` 格式，必须包裹在 `nv(q(...))` 中
- 系统会兜底转换简单格式：含 `.delta_counter` 走多值，否则走非多值 `rate{counter}`
- tags 的 `{}` 中只放确定存在的固定值，不要使用 Grafana 模板变量（如 `$xxx`），避免目标大盘缺少该变量导致查询失败
- 支持多变量计算如 `$a/$b`、`$a + $b` 等
- 如果用户未指定 `target` 字段，系统自动设为 `"Bosun Query"`
- 如果用户未指定 `datasource`，默认使用 `"bosun"`

## Notes

- 大盘标识支持 `--uid` 或 `--url`（至少传一个），URL 支持带 `var-*` 模板变量
- 复杂参数（panels、variables、links、position）通过 `--xxx-json` 传递 JSON 字符串
- 所有 Grafana leaf command 都支持 `--grafana-version <v7|v10>`；不传时保持 V7。完整 URL 的已知 host 优先于 flag 和全局 `--site`；host 与 flag 冲突返回 `GRAFANA_INPUT_ERROR`，未知 URL host 返回 `GRAFANA_SITE_UNSUPPORTED`。
- V10 当前只支持 CN。V7 创建大盘未传 folder 时保持 CN 默认 `folderId=164421972`（其他 site 使用各自默认值）；V10 未传时使用 root folder，也可显式传 `--folder-uid`。`--folder-id` 与 `--folder-uid` 不能同时使用。
- i18n 有多套互不共享 dashboard 数据的 V7 实例：`grafana-i18n.byted.org`（`--site i18n-bd` 默认）、`grafana-i18n.byteintl.net`、`grafana-us*.byted.org`。传完整 URL 时请求保留原始 host；只传 `--uid` 会落到 `--site` 的默认实例，跨实例查 uid 会得到 `404 Dashboard not found`，此时改传完整 URL。
- 所有命令通过 MCP 自动暴露为 `grafana_*` 系列 tool
