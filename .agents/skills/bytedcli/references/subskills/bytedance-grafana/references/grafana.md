# Grafana

所有 Grafana leaf command 都支持 `--grafana-version <v7|v10>`。不传时保持 V7；完整 URL 的 allowlist host 会自动推断实例。URL host 与 flag 冲突时报 `GRAFANA_INPUT_ERROR`，未知 URL host 报 `GRAFANA_SITE_UNSUPPORTED`。V10 当前只支持 CN。

直连 Grafana API 的命令支持 `--grafana-url <origin>` 覆盖请求地址，并要求用 `--grafana-version v7|v10` 显式选择最接近的官方 API 协议族。folder 默认值和 JWT 站点继续沿用 `--grafana-version` / 全局 `--site` 的既有逻辑；该参数不为自定义实例提供额外兼容适配。只接受无路径、query、fragment、credentials 或自定义端口的内部 HTTPS origin；同时传 dashboard URL 时两者 origin 必须一致。OpenAPI 命令 `dashboard describe`、顶层 `query`、`screenshot`、`data`、`expr-parse` 不支持该参数。

```bash
# V7 默认调用
bytedcli --json grafana search "demo service"
bytedcli --json grafana info "demo-uid"
bytedcli --json grafana query "demo-uid" --panel 123 --from now-30m --to now --var dc=hl

# 自定义内部实例：仅用于直连 API 命令
bytedcli --site cn --json grafana dashboard get --uid "demo-uid" --grafana-url "https://grafana-team.example.byted.org" --grafana-version v10
bytedcli --site cn --json grafana panel query --uid "demo-uid" --panel-id 123 --grafana-url "https://grafana-team.example.byted.org" --grafana-version v10

# V10：仅有 UID、search 或 create 时显式选择版本
bytedcli --json grafana search "demo service" --grafana-version v10
bytedcli --json grafana dashboard get --uid "demo-uid" --grafana-version v10
bytedcli grafana dashboard create --title "demo-v10-dashboard" --folder-uid "demo-folder-uid" --grafana-version v10

# V10：完整 dashboard/panel URL 自动推断
bytedcli --json grafana info "https://grafana-10.bytedance.net/d/demo-uid/demo-slug?var-dc=lf"
bytedcli --json grafana dashboard describe --url "https://grafana-10.bytedance.net/d/demo-uid/demo-slug"

# Dashboard
bytedcli grafana dashboard get --uid "demo-uid"
bytedcli grafana dashboard create --title "demo-dashboard"
bytedcli grafana dashboard update --uid "demo-uid" --title "demo-updated"
bytedcli grafana dashboard delete --uid "demo-uid"

# Group
bytedcli grafana group list --uid "demo-uid"
bytedcli grafana group create --uid "demo-uid" --title "demo-group"
bytedcli grafana group get --uid "demo-uid" --group-title "demo-group"
bytedcli grafana group update --uid "demo-uid" --target-group-title "demo-group" --title "demo-renamed"
bytedcli grafana group delete --uid "demo-uid" --group-title "demo-group"

# Panel：V7 新建默认 graph；V10 新建默认 timeseries
bytedcli grafana panel list --uid "demo-uid"
bytedcli grafana panel get --uid "demo-uid" --panel-id 123
bytedcli grafana panel create --uid "demo-uid" --panel-json '{"title":"demo-panel","type":"graph"}'
bytedcli grafana panel create --uid "demo-uid" --grafana-version v10 --panel-json '{"title":"demo-timeseries","datasource":{"type":"demo-sql","uid":"demo-ds-uid"},"options":{"legend":{"displayMode":"table","placement":"bottom"}}}'
bytedcli grafana panel update --uid "demo-uid" --panel-id 123 --panel-json '{"title":"demo-updated"}'
bytedcli grafana panel delete --uid "demo-uid" --panel-id 123

# Panel query：V7 /api/tsdb/query；V10 普通 datasource /api/ds/query；OpenTSDB UID proxy
bytedcli --json grafana panel query --uid "demo-uid" --panel-id 123 --from now-1h --to now --var applicationId=application_demo_123
bytedcli --json grafana panel query --uid "demo-uid" --panel-id 123 --grafana-version v10 --from now-1h --to now

# Variable / link
bytedcli grafana variable get --uid "demo-uid"
bytedcli grafana variable update --uid "demo-uid" --variables-json '[{"name":"interval","type":"custom","query":"30s,1m,5m"}]'
bytedcli grafana link get --uid "demo-uid"
bytedcli grafana link update --uid "demo-uid" --links-json '[{"title":"demo-link","url":"https://example.com","targetBlank":true}]'

# Tools
bytedcli grafana inject-metrics-links --uid "demo-uid"
bytedcli grafana data --url "https://grafana-10.bytedance.net/d/demo-uid/demo-slug?viewPanel=123"
bytedcli grafana screenshot --url "https://grafana-10.bytedance.net/d/demo-uid/demo-slug?viewPanel=123"
bytedcli grafana expr-parse --url "https://grafana-10.bytedance.net/d/demo-uid/demo-slug"
```

- V7 create 未传 folder 时继续使用 site 默认 `folderId`。V10 未传时使用 root folder；可传 `--folder-uid` 或 `--folder-id`，二者不能同时使用。
- V10 panel datasource `{type,uid}`、`options.legend`、targets、field overrides 与未知字段会按 dashboard JSON 原样保留。读取已有 graph panel 后更新不会强制迁移为 timeseries。
- `grafana data` 在 V10 公司 OpenAPI data 不兼容时读取 panel 与真实 datasource type：普通 datasource 回退到 `/api/ds/query`，OpenTSDB/ByteTSD 直接走 `/api/datasources/proxy/uid/<uid>/api/query`，不会先探测 `/api/ds/query`，也不会切到 V7。
- `grafana panel query` 的 `query_api` 为 `tsdb`、`ds` 或 `opentsdb_proxy`，并提供 `datasource_uid`、`datasource_type`、`columns`、`column_names`、`row_count`。OpenTSDB proxy 的 HTTP 200 + 空 series 是成功零行结果；鉴权、HTTP 查询和 response schema 错误分别返回结构化错误。
