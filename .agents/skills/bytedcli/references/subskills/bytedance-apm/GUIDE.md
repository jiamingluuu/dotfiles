---
name: bytedance-apm
description: "Operate APM via bytedcli: service preview (Argos overview for service-level QPS/CPU/MEM), QPS, upstream/downstream dependency analysis, per-method SLA (success rate, QPS), service call topology graphs (Argos trace topology), Argos alarm rule search/filtering and detail-page URL generation, Redis monitoring dashboards, FaaS MQ trigger consumption metrics, middleware views (TLB/TCC/MySQL/AGW/runtime via Byteheart), and APM metric querying (with Query DSL, anti-drift duration, multi-region). Use when tasks mention APM, service monitoring, QPS, CPU, MEM, dependencies, topology graph, SLA, success rate, alarm rules, alarm rule browser links, metric query, Redis monitoring, or FaaS MQ trigger metrics."
---

# bytedcli APM

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

- 服务预览、QPS 查询
- 服务级资源维度（CPU / MEM）：优先 `apm service preview --service-type service`，读 `clusters.rows`
- 上下游服务依赖分析（deps：查看服务的 upstream/downstream 依赖及其 QPS、错误率、成功率）
- 服务调用拓扑图（argos trace topology：按 PSM/method/dc/cluster 圈根节点，拉多层上下游 nodes+edges，支持 mermaid 输出）
- 接口维度 SLA 分析（methods：查看每个 method 的 QPS、成功率，支持按成功率阈值过滤）
- Metric 指标高级查询（Query DSL）、批量查询及 Metric 探索 (search, field-list, tagk-list, tagv-list)
- Redis 监控（overview/client/server/proxy）
- FaaS MQ trigger 成功消费 QPS / RocketMQ lag 查询
- Argos 告警规则按 PSM、状态、级别、类型、监控区域、通知方式或 tag 组合搜索与计数，并从命令结果获取可点击详情页链接
- 中间件专项视图（TLB/TCC/MySQL/AGW；`runtime` 走 Byteheart，不是服务级 CPU/MEM 入口）

## 前置条件

- 使用通用调用方式：`../../invocation.md`
- `apm metric query/batch-query/search/field-list/tagk-list/tagv-list` 的 Argos SDK 路径与 `apm argos log aggregate/overview` 可读取受管环境注入的服务账号 JWT。推荐按站点配置 `BYTEDCLI_SERVICE_ACCOUNT_JWT_CN`、`BYTEDCLI_SERVICE_ACCOUNT_JWT_I18N_TT`、`BYTEDCLI_SERVICE_ACCOUNT_JWT_I18N_BD`、`BYTEDCLI_SERVICE_ACCOUNT_JWT_US_TTP` 或 `BYTEDCLI_SERVICE_ACCOUNT_JWT_EU_TTP`，也可使用通用变量 `BYTEDCLI_SERVICE_ACCOUNT_JWT`。
- `us-ttp`、`us-ttp-bdee`、`us-ttp-usts` 共享 `BYTEDCLI_SERVICE_ACCOUNT_JWT_US_TTP`。使用服务账号调用上述 SDK 路径时必须设置 `BYTEDCLI_ARGOS_PROJECT=sample-argos-project`。设置 `ARGOS_SERVER_URL` 自定义 Agent Center 地址时，bytedcli 不会向该地址发送受管服务账号 JWT。

> 执行前缀见 `../../invocation.md`；下面示例直接写 `bytedcli`。

### 生产网域名切换（`BYTEDCLI_NETWORK_PROFILE=prod`）

默认走 `aiops-argos-*.tiktok-row.org` / `.tiktok-eu.org` / `.tiktok-us.org`、`aiopswebarch.tiktok-eu.org`、`aiopswebarch-og.tiktok-us.net`、`metrics-fe-*.tiktok-*.org` 等办公网网关；在 ByteDance 生产网（开发机 / BOE / PPE / 线上服务端）这些 host 不可达。设置 `BYTEDCLI_NETWORK_PROFILE=prod` 后，i18n-tt / eu-ttp / us-ttp\* 的 Argos、Argos event、Byteplot API host 会切到对应的 `byted.org` 内部网关；CN / BOE / i18n-bd 的 host 本来就是内部 host，无须切换。

- JWT 校验按站点区分：`us-ttp` / `us-ttp-bdee` 使用 `cloud.tiktok-us.net`，`us-ttp-usts` 使用 `cloud.tiktok-usts.net`。请求 Origin 仍使用对应控制台 host：前两者为 `cloud-ttp-us.bytedance.net`，USTS 为 `cloud.tiktok-usts.net`。
- 生产网 JWT issuer 同样按站点区分：`i18n-tt` 使用 `cloud-i18n.bytedance.net`，`eu-ttp` 使用 `cloud-i18n.tiktoke.org`；EU 请求 Origin 仍为 `cloud-eu.tiktok-row.net`。
- Byteplot 的 Referer 仍硬编码在 `metrics-fe-*` 办公网控制台 URL 上 —— 后端 CORS / Referer 校验只认这些公网值，对应控制台目前没有生产网镜像，不要尝试改写。
- 如默认 prod host 不可达，可以用以下任一环境变量手动覆盖：`BYTEDCLI_APM_ARGOS_I18N_HOST` / `BYTEDCLI_APM_ARGOS_US_HOST` / `BYTEDCLI_APM_ARGOS_EU_HOST` / `BYTEDCLI_APM_ARGOS_MALIVA_HOST` / `BYTEDCLI_APM_ARGOS_ALIVA_HOST` / `BYTEDCLI_APM_ARGOS_EVENT_I18N_HOST` / `BYTEDCLI_APM_ARGOS_EVENT_US_HOST` / `BYTEDCLI_APM_ARGOS_EVENT_EU_HOST` / `BYTEDCLI_APM_BYTEPLOT_I18N_HOST` / `BYTEDCLI_APM_BYTEPLOT_EU_HOST` / `BYTEDCLI_APM_BYTEPLOT_US_HOST`。
- 需要把 measurement / monitoring / event API 全部指到同一个内部 host 时，使用全局 `BYTEDCLI_APM_API_BASE_URL`（已在 master 上独立支持），优先级高于上述 per-host 覆盖。

```bash
# 在线上服务/开发机上调用 APM：
export BYTEDCLI_NETWORK_PROFILE=prod
bytedcli --json --site i18n-tt apm service qps --psm "example.service.api"
```

## Quick start

**命令行结构**：`bytedcli [全局选项] apm <子命令族> <子命令> [命令选项]`

| 类别     | 选项                              | 位置                        | 说明                             |
| -------- | --------------------------------- | --------------------------- | -------------------------------- |
| 全局选项 | `--json`、`--site`、`--debug`     | `bytedcli` 之后、子命令之前 | 对所有子命令生效                 |
| 命令选项 | `--psm`、`--region`、`--start` 等 | 子命令之后                  | 仅对当前子命令生效，见参数归属表 |

**必须严格遵守的格式**：`bytedcli --json apm service qps --psm "example.service.api"`（`--json` 在 `apm` 之前）

Commands are grouped under `apm service`, `apm redis`, `apm metric`, and `apm faas-mq-trigger`. Old flat names (e.g. `apm service-preview`, `apm redis-qps`) still work as hidden aliases.

```bash
# 服务预览（默认 --service-type service → Argos overview；含 QPS / CPU / MEM）
bytedcli --json apm service preview --psm "example.service.api"
bytedcli --site eu-ttp --json apm service preview --psm "example.service.api" --region "EU-TTP2"
bytedcli --json apm service preview --psm "cache.demo.redis" --service-type redis

# QPS
bytedcli --json apm redis qps --psm "cache.demo.redis"
bytedcli --json apm redis traffic --psm "cache.demo.redis"
bytedcli --json apm service qps --psm "example.service.api"
bytedcli --json apm service qps --psm "example.service.api" --metric "service.request.server.throughput.total"
bytedcli --json apm service measurement-params --psm "example.service.api" --metric "service.request.server.throughput.total"
bytedcli --json apm service qps --psm "example.service.api" --measurement-tag "service.env=prod"
bytedcli --json apm service downstream-qps --psm "example.service.api"
bytedcli --json apm service downstream-qps --psm "example.service.api" --metric "service.request.downstream.throughput.total"

# 上下游服务依赖分析
bytedcli --json apm service deps --psm "example.service.api"
bytedcli --json apm service deps --psm "example.service.api" --direction upstream
bytedcli --json apm service deps --psm "example.service.api" --direction downstream
bytedcli --json apm service deps --psm "example.service.api" --start 1714000000 --end 1714003600
bytedcli --json apm service deps --psm "example.service.api" --region "China-North"
bytedcli --json apm service deps --psm "example.service.api" --with-method
bytedcli --json apm service deps --psm "example.service.api" --method "QueryHotelDetail"

# 接口维度 SLA 分析
bytedcli --json apm service methods --psm "example.service.api"
bytedcli --json apm service methods --psm "example.service.api" --min-success-rate 99.9
bytedcli --json apm service methods --psm "example.service.api" --latency
bytedcli --json apm service methods --psm "example.service.api" --latency --top 10
bytedcli --json apm service methods --psm "example.service.api" --latency --method "QueryHotelDetail"
bytedcli --json apm service methods --psm "example.service.api" --start 1714000000 --end 1714003600 --region "China-North"

# i18n-bd 站点查询（deps / methods / qps / preview 均支持）
bytedcli --site i18n-bd --json apm service deps --psm "example.service.api"
bytedcli --site i18n-bd --json apm service methods --psm "example.service.api"

# Metric 基础查询（单值指标，带必要的 _psm tag）
bytedcli --json apm metric query "sum:bytedtrace.sdk.span.server.rate{}{_psm=literal_or(example.demo.api)}" --start-time 1714000000 --end-time 1714003600 --region "China-North"

# Metric 多值指标查询（delta_counter 类型，[delta] 必须放在末尾）
bytedcli --json apm metric query "sum:store:example.service.api.throughput{_psm=literal_or(example.demo.api)}{}[delta]" --start-time 1714000000 --end-time 1714003600

# Metric 多值指标查询（timer 类型，加权 P99）
bytedcli --json apm metric query "sum:store:example.service.api.latency{_psm=literal_or(example.demo.api)}{}[weighted_avg(value=pct99,weight=counter)]" --start-time 1714000000 --end-time 1714003600

# 单进程批量查询；同一进程内按 --concurrency 并发，逐项返回成功或失败
# metric-queries.json: {"defaults":{"start_time":1714000000,"end_time":1714003600,"region":"China-North"},"queries":[{"request_id":"qps","query":"sum:example.service.api.qps{}{}"},{"request_id":"latency","query":"avg:example.service.api.latency{}{}"}]}
bytedcli --no-auto-upgrade --json apm metric batch-query \
  --input-file ./metric-queries.json \
  --concurrency 6

# Metrics FE / Bosun OpenTSDB 查询（覆盖当前站点全部前端 region）
bytedcli --json apm bosun query "sum:store:example.service.metric" --duration 10m --all-regions

# Metrics FE / Bosun 多行 Argos 报警模板查询（@file 或直接传模板文本；--end-time 回放历史求值基点）
bytedcli --json apm bosun query @./alert-template.bosun --site i18n-tt --region Singapore-Central --end-time 1748284992

# Metrics FE / Bosun 时间区间扫描（同一表达式按 30s 对齐整点逐点求值，找告警触发/恢复的切换时刻）
bytedcli --json apm bosun query @./alert-template.bosun --site i18n-tt --region Singapore-Central --start-time 1748284800 --end-time 1748285100 --interval 30s

# Metrics FE / Bosun 指定一批时刻批量求值（--at 可重复，自动去重排序）
bytedcli --json apm bosun query @./alert-template.bosun --site i18n-tt --region Singapore-Central --at 1748284800 --at 1748285100

# Bosun Playground 语句分析（一次请求返回按 group 分行的全部变量值与求值树；--region 必填）
bytedcli --json apm bosun analyze @./argos-rule.bosun --region Singapore-Central --end-time 1748284992

# Redis 监控
bytedcli --json apm redis overview --psm "cache.demo.redis"
bytedcli --json apm redis client --psm "cache.demo.redis"
bytedcli --json apm redis server --psm "cache.demo.redis"
bytedcli --json apm redis proxy --psm "cache.demo.redis"

# FaaS MQ trigger 成功消费 QPS
bytedcli --json apm faas-mq-trigger metrics --function "demo-function" --mqid "demo-mqid" --duration 30m
bytedcli --json apm faas-mq-trigger metrics --function "demo-function" --mqid "demo-mqid" --start-time 1714000000 --end-time 1714003600 --step 15s
bytedcli --json apm faas-mq-trigger lag --mq-cluster "rocketmq-demo" --topic "demo-topic" --consumer-group "GID-demo" --duration 30m

# 中间件专项视图（Byteheart；不要用 runtime 代替服务级 CPU/MEM）
bytedcli --json apm service preview --psm "psm.name" --service-type tlb
bytedcli --json apm service preview --psm "psm.name" --service-type tcc
bytedcli --json apm service preview --psm "psm.name" --service-type mysql
bytedcli --json apm service preview --psm "psm.name" --service-type agw_sidecar
bytedcli --json apm service preview --psm "psm.name" --service-type runtime

# Argos 稳态码配置：查询 / 增删（默认安全：不带 --yes 只预览，不写入）
bytedcli --json apm argos stable-code get --psm "example.service.api"
bytedcli --json apm argos stable-code add --psm "example.service.api" --code 133 --dry-run
bytedcli --json apm argos stable-code add --psm "example.service.api" --code 133 --yes
bytedcli --json apm argos stable-code delete --psm "example.service.api" --code 133 --yes

# Argos bosun/data：VMP PromQL 查询（简化模式）
bytedcli --json apm argos bosun query \
  --account-id 1234567890 \
  --workspace-id 00000000-0000-0000-0000-000000000000 \
  --prom 'sum(rate(proxy_requests_total{cluster="demo-cluster"}[1m]))' \
  --duration 1h

# Argos bosun/data：VMP PromQL 查询（passthrough 模式，整段 bosun 表达式）
bytedcli --json apm argos bosun query --expr-file ./panel.bosun --duration 30m

# Argos oncall：值班计划搜索 / 查询 / 修改
bytedcli --json apm argos oncall plan search --query "demo-service"
bytedcli --site i18n-tt --json apm argos oncall plan get --uid "demo-plan-uid"
bytedcli --json apm argos oncall plan set-users --uid "demo-plan-uid" --user demo-user-a --dry-run
bytedcli --json apm argos oncall plan set-users --uid "demo-plan-uid" --user demo-user-a --user demo-user-b
bytedcli --json apm argos oncall plan set-rotation --uid "demo-plan-uid" --daily 9 --dry-run
bytedcli --json apm argos oncall plan set-rotation --uid "demo-plan-uid" --weekly 1 --hour 9 --num 2

# Argos oncall：报警接收人 / 节点配置查询
bytedcli --json apm argos oncall receiver by-node --psm "example.service.api" --vregion "ChinaSinf-North"
bytedcli --json apm argos oncall node setting --node-id "demo-node-id" --vregion "ChinaSinf-North"
bytedcli --json apm argos oncall node parents --node-id "demo-node-id" --vregion "ChinaSinf-North"

# Argos alarm：报警规则查询 / 创建 / 通知方式变更 / 接收人查询
bytedcli --json apm argos alarm rule search --filter '{"psm":"example.service.api"}'
bytedcli --json apm argos alarm rule search --filter '{"psm":"example.service.api","level":["critical"],"status":["normal"]}' --page 2 --page-size 100
bytedcli --json apm argos alarm rule get --id "demo-rule-id"
bytedcli --json apm argos alarm rule get --uid "demo-rule-uid"
bytedcli --json apm argos alarm rule enable-lark-at --id "demo-rule-id" --dry-run
bytedcli --json apm argos alarm rule enable-lark-at --id "demo-rule-id"
# 创建报警规则（默认安全：不带 --yes 只预览 payload，不写入）。--from 克隆已有规则，--set 按点路径覆盖字段
bytedcli --json apm argos alarm rule create --from "src-rule-id" --name "new-rule" --set "query.cluster=demo-target-cluster" --dry-run
bytedcli --json apm argos alarm rule create --from "src-rule-id" --name "new-rule" --set "query.cluster=demo-target-cluster" --yes
# 更新报警规则（默认安全：不带 --yes 只预览 patch，不写入）
bytedcli --json apm argos alarm rule update --id "demo-rule-id" --set "query.cluster=demo-target-cluster" --dry-run
bytedcli --json apm argos alarm rule update --id "demo-rule-id" --payload @rule-patch.json --yes
bytedcli --json apm argos alarm receiver by-rule --id "demo-rule-id" --vregion "ChinaSinf-North"

# search 的完整 filter 字段、枚举、tag 空值语义和 jq 用法见 references/argos-alarm-rule-search.md

# Argos 自定义看板：列表 / 详情 / 查询 / 创建 / 更新
bytedcli --json apm argos dashboard list --view all --keyword "demo-dashboard" --page-size 20
bytedcli --json apm argos dashboard list --tree --view my
bytedcli --json apm argos dashboard get --id "demo-dashboard-id"

# 看板查询：自动识别大盘结构，在 --max-queries 上限内展开 panel 查询并确定性拉取时序数据。
# 支持直接粘贴 console URL；URL 中的看板变量会传给服务端解析，--start/--end 覆盖 URL 时间窗。
bytedcli --json apm argos dashboard query --id "demo-dashboard-id" --start now-3h
bytedcli --json apm argos dashboard query --url "https://cloud.example.tiktok-row.net/argos/dashboard/000000000000000000000000?dashboard_from=now-12h&dashboard_region=sg&psm=example.service.api" --max-queries 20
bytedcli --json apm argos dashboard create --payload @dashboard.json --folder "demo-folder" --dry-run
bytedcli --json apm argos dashboard create --payload @dashboard.json --folder "demo-folder" --yes
bytedcli --json apm argos dashboard update --id "demo-dashboard-id" --payload @dashboard.json --dry-run
bytedcli --json apm argos dashboard update --id "demo-dashboard-id" --payload @dashboard.json --yes

# Argos event：查看服务最近变更/发布/配置事件
bytedcli --json apm argos event list --psm "demo.service.api" --duration 12h
bytedcli --json apm argos event list --psm "demo.service.api" --start 1714000000 --end 1714043200 \
  --category TCC --action open_modify_config --page-size 100

# Argos StreamLog：错误日志按代码位置聚合（默认 aggregator=location，仅看 Error）
bytedcli --json apm argos log aggregate --psm "demo.service.api" --vregion "China-North" \
  --duration 1h --log-level Error

# Argos StreamLog：按多个 log level 过滤 + 显示完整 metric/kibana 链接
bytedcli --json apm argos log aggregate --psm "demo.service.api" --vregion "China-North" \
  --duration 1h --log-level Error --log-level Warn --show-links

# Argos StreamLog：按用户自定义错误规则聚合（需带 --cluster）
bytedcli --json apm argos log aggregate --psm "demo.service.api" --vregion "China-North" \
  --duration 1h --aggregator custom --cluster default

# Argos StreamLog：同时拉 aggregate_key facets
bytedcli --json apm argos log aggregate --psm "demo.service.api" --vregion "China-North" \
  --duration 1h --with-facets
```

## Metric 探索工作流

如果你不确定具体的 metric 名称或 tag，请按以下步骤探索：

1. 查租户 → `tenant-list`
2. 找 metric → `search`
3. 查 tag keys → `tagk-list`
4. 查 tag values → `tagv-list`
5. 查询数据 → `query`

## Agent 报警排查最短链（不要先跑 `--help`）

已知 Argos rule ID、PSM 和事故窗口时，先取规则真身，再查同窗口事件，最后按规则表达式或代码埋点查询指标。所有命令使用全局 `--json` 并显式指定 site：

```bash
bytedcli --site <site> --json apm argos alarm rule get --id <ruleId>
bytedcli --site <site> --json apm argos event list --psm <psm> --start <epochSeconds> --end <epochSeconds>
bytedcli --site <site> --json apm metric search --prefix <metricPrefix> --limit 20
bytedcli --site <site> --json apm metric query '<queryDsl>' \
  --start-time <epochSeconds> --end-time <epochSeconds> --region <vregion>
```

- `alarm rule get` 只使用全局 `--site` 选择控制面，不支持局部 `--region`；metric 命令的 `--region` 仍用于查询维度。
- 只有 PSM、尚无 rule ID 时，先运行 `alarm rule search --filter '{"psm":"example.service.api"}'`；`psm` 写在 filter 内，不存在独立 `--psm`。完整契约见 [argos-alarm-rule-search.md](./references/argos-alarm-rule-search.md)。
- `alarm rule get/search` 会按当前控制面解析并返回 `detail_url`；面向用户输出规则时直接使用该字段，不要在 skill 或 Agent 提示中自行拼域名。取值命令见 [argos-alarm-rule-search.md](./references/argos-alarm-rule-search.md#规则详情页-url)。
- 规则、event、metric、StreamLog 可能访问不同后端。某一条网络失败不代表其他链路必然失败，也不代表线上没有数据。
- 比较报警窗口与基线窗口时保持同一 query、site、region、聚合与 tag，仅改变时间窗。
- 未知物理指标名时先 `metric search/tagk-list/tagv-list`，不要从函数名直接猜最终 namespace。
- 网络错误、鉴权错误和空序列是三种不同证据状态；只有成功响应中的空数据才能解释为“未查询到”。

完整的探索指南和高级用法请参考：[exploration-guide.md](./references/exploration-guide.md)、[metric.md](./references/metric.md)

## 参数归属

Agent 在构造下表所列命令时，**必须**参照下表判断参数归属。不在表中的参数表示该子命令不支持；`measurement-params` 的参数见下方说明。

### `apm metric` 系列

| 参数                          |          `query`           |  `search`   | `field-list` | `tagk-list` | `tagv-list` | `tenant-list` |
| ----------------------------- | :------------------------: | :---------: | :----------: | :---------: | :---------: | :-----------: |
| `--region`                    |        ✅ (可多次)         | ✅ (可多次) | ✅ (可多次)  | ✅ (可多次) | ✅ (可多次) |  ✅ (可多次)  |
| `--all-regions`               |             ✅             |     ❌      |      ❌      |     ❌      |     ❌      |      ❌       |
| `--start-time` / `--end-time` | ✅ (推荐，Unix 秒级时间戳) |     ❌      |      ❌      |     ❌      |     ❌      |      ❌       |
| `--duration`                  |          ⚠️ 废弃           |     ❌      |      ❌      |     ❌      |     ❌      |      ❌       |
| `--group-by-region`           |             ✅             |     ❌      |      ❌      |     ❌      |     ❌      |      ❌       |
| `--tenant`                    |    ✅ (默认 `default`)     |     ✅      |      ✅      |     ✅      |     ✅      |      ❌       |
| `--prefix`                    |             ❌             |  ✅ (必填)  |      ❌      |     ❌      |     ❌      |      ❌       |
| `--metric`                    |             ❌             |     ❌      |  ✅ (必填)   |  ✅ (必填)  |  ✅ (必填)  |      ❌       |
| `--tags`                      |             ❌             |     ❌      |      ❌      |     ❌      |  ✅ (必填)  |      ❌       |
| `--filters`                   |             ❌             |     ❌      |      ❌      |     ❌      |     ✅      |      ❌       |
| `--limit`                     |             ❌             |     ✅      |      ❌      |     ❌      |     ❌      |      ❌       |
| `--psm`                       |   ❌ (写在 query {} 内)    |     ❌      |      ❌      |     ❌      |     ❌      |      ❌       |

### `apm service` 系列

| 参数                 |         `preview`          |           `deps`           |         `methods`          |           `qps`            |      `downstream-qps`      | `runtime/tlb/tcc/mysql/agw-sidecar` |
| -------------------- | :------------------------: | :------------------------: | :------------------------: | :------------------------: | :------------------------: | :---------------------------------: |
| `--psm`              |         ✅ (必填)          |         ✅ (必填)          |         ✅ (必填)          |         ✅ (必填)          |         ✅ (必填)          |              ✅ (必填)              |
| `--region`           |        ✅ (可多次)         |        ✅ (可多次)         |        ✅ (可多次)         |        ✅ (可多次)         |        ✅ (可多次)         |                 ❌                  |
| `--start` / `--end`  | ✅ (推荐，Unix 秒级时间戳) | ✅ (推荐，Unix 秒级时间戳) | ✅ (推荐，Unix 秒级时间戳) | ✅ (推荐，Unix 秒级时间戳) | ✅ (推荐，Unix 秒级时间戳) |                 ❌                  |
| `--range`            |          ⚠️ 废弃           |          ⚠️ 废弃           |          ⚠️ 废弃           |          ⚠️ 废弃           |          ⚠️ 废弃           |                 ❌                  |
| `--service-type`     |             ✅             |             ❌             |             ❌             |             ✅             |             ✅             |              ✅ (预设)              |
| `--direction`        |             ❌             |             ✅             |             ❌             |             ❌             |             ❌             |                 ❌                  |
| `--with-method`      |             ❌             |             ✅             |             ❌             |             ❌             |             ❌             |                 ❌                  |
| `--method`           |             ❌             | ✅（隐含 `--with-method`） |             ✅             |             ✅             |             ✅             |                 ❌                  |
| `--metric`           |             ❌             |             ❌             |             ❌             |             ✅             |             ✅             |                 ❌                  |
| `--measurement-tag`  |             ❌             |             ❌             |             ❌             |        ✅（可多次）        |        ✅（可多次）        |                 ❌                  |
| `--latency`          |             ❌             |             ❌             |             ✅             |             ❌             |             ❌             |                 ❌                  |
| `--min-success-rate` |             ❌             |             ❌             |             ✅             |             ❌             |             ❌             |                 ❌                  |
| `--top`              |             ❌             |             ❌             |             ✅             |             ❌             |             ❌             |                 ❌                  |
| `--aggregator`       |             ❌             |             ❌             |             ✅             |             ✅             |             ✅             |                 ❌                  |

### `apm argos alarm rule search`

| 参数                     |    支持    | 说明                                                            |
| ------------------------ | :--------: | --------------------------------------------------------------- |
| `--filter <json\|@file>` | ✅（必填） | JSON object；`psm` 是 filter 内唯一必填字段，不提供独立 `--psm` |
| `--page <n>`             |     ✅     | 从 1 开始，默认 1                                               |
| `--page-size <n>`        |     ✅     | 默认 20，范围 1–500；每次只取指定页，不自动拉取全量             |
| `--site` / `--json`      | ✅（全局） | 必须放在 `apm` 之前；plain 适合阅读，JSON 适合脚本解析          |

完整 filter 字段、枚举、无固定枚举字段、tag 语义与输出契约见 [argos-alarm-rule-search.md](./references/argos-alarm-rule-search.md)。

### `apm redis` 系列

| 参数       |   `qps`   | `traffic` | `overview` | `client`  | `server`  |  `proxy`  |
| ---------- | :-------: | :-------: | :--------: | :-------: | :-------: | :-------: |
| `--psm`    | ✅ (必填) | ✅ (必填) | ✅ (必填)  | ✅ (必填) | ✅ (必填) | ✅ (必填) |
| `--idc`    |    ❌     |    ❌     |     ✅     |    ✅     |    ✅     |    ✅     |
| `--region` |    ❌     |    ❌     |     ❌     |    ❌     |    ❌     |    ❌     |

### `apm faas-mq-trigger` 系列

| 参数                          | `metrics` | 说明                                                     |
| ----------------------------- | :-------: | -------------------------------------------------------- |
| `--function <id>`             | ✅ (必填) | FaaS function id                                         |
| `--mqid <id>`                 | ✅ (必填) | FaaS MQ trigger id                                       |
| `--start-time` / `--end-time` |    ✅     | Unix 秒级时间戳；成对使用时覆盖 `--duration` 默认时间窗  |
| `--duration`                  |    ✅     | 相对时间窗，默认 `30m`                                   |
| `--step`                      |    ✅     | Prometheus query step，默认 `15s`                        |
| `--end-offset`                |    ✅     | 默认结束时间相对 now 的偏移，默认 `30s`                  |
| `--datasource`                |    ✅     | Grafana Prometheus datasource，默认 `vefaas-cn-beijing`  |
| `--grafana-url`               |    ✅     | Grafana base URL，默认 `https://infra-grafana.byted.org` |

| 参数                          |   `lag`   | 说明                                                               |
| ----------------------------- | :-------: | ------------------------------------------------------------------ |
| `--mq-cluster <resource_id>`  | ✅ (必填) | RocketMQ ResourceId                                                |
| `--topic <topic>`             | ✅ (必填) | RocketMQ topic                                                     |
| `--consumer-group <group>`    | ✅ (必填) | RocketMQ consumer group                                            |
| `--start-time` / `--end-time` |    ✅     | Unix 秒级时间戳；成对使用时覆盖 `--duration` 默认时间窗            |
| `--duration`                  |    ✅     | 相对时间窗，默认 `30m`                                             |
| `--bucket`                    |    ✅     | Influx `GROUP BY time(...)` 桶，默认 `1m`                          |
| `--end-offset`                |    ✅     | 默认结束时间相对 now 的偏移，默认 `2m`，避免当前分钟桶未完整       |
| `--datasource`                |    ✅     | Grafana Influx datasource，默认 `rocketmq_metrics_ops-influxdb-BJ` |
| `--database`                  |    ✅     | Influx database，默认 `rocketmq_metrics_ops`                       |
| `--grafana-url`               |    ✅     | Grafana base URL，默认 `https://infra-grafana.byted.org`           |

### 时间戳格式

| 参数                          | 格式            | 示例         | 说明                                                                                                         |
| ----------------------------- | --------------- | ------------ | ------------------------------------------------------------------------------------------------------------ |
| `--start-time` / `--end-time` | Unix 秒级时间戳 | `1714000000` | 仅支持数字时间戳，不支持相对时间                                                                             |
| `--start`                     | Unix 秒级时间戳 | `1714000000` | 也支持 RFC3339 和 `-1h`，但**必须优先使用时间戳**                                                            |
| `--end`                       | Unix 秒级时间戳 | `1714003600` | 同 `--start`，也支持 `now`，但**必须优先使用时间戳**                                                         |
| `--duration` / `--range`      | —               | —            | **⚠️ 废弃**，不要使用。相对时间导致结果不确定，Agent 必须用 `--start-time`/`--end-time` 或 `--start`/`--end` |

**Agent 构造命令时，必须将用户意图转换为 Unix 秒级时间戳。** 示例：用户说"最近 1 小时"，Agent 应计算 `当前时间戳 - 3600` 作为 `--start` 值，`当前时间戳` 作为 `--end` 值。

## Notes

- `apm argos alarm rule search` 每次只查询一页，默认 20、最大 500，并始终返回后端 `total`。JSON 中规则对象很大；分析多条规则时先重定向到临时文件，再用 `jq '.data.total'` 或 `jq '.data.rules[] | {id,uid,name,status,level,suit_type}'` 提取，避免把整页完整配置直接灌入上下文。
- `apm service deps` 基于 Argos measurement 接口，默认输出按 service 聚合的上下游依赖。
  - QPS：`service.request.{downstream|upstream}.throughput.total`
  - Error QPS：`service.request.{downstream|upstream}.throughput.error`
  - Success Rate：基于 `service.request.{downstream|upstream}.error_rate`（成功率 = `100 - error_rate`），避免用数量做除法带来的偏差。
  - `--with-method`：输出方法级依赖，包含对端 `method` 与当前 PSM 的 `self_method`。
  - `--method <name>`：只看当前 PSM 指定接口的上下游依赖（可重复/逗号分隔），自动启用方法级依赖查询。
- `apm service methods` 基于 Argos measurement 接口，输出 method 维度指标（按 `method` / `service.method` 聚合，必要时自动 fallback）。
  - Success Rate：基于 `service.request.server.error_rate`（成功率 = `100 - error_rate`，两位小数）。
  - 延迟：用 `--latency` 打开（默认指标 `service.request.server.latency.total`，并自动转成 `ms`）。
  - `--top <n>`：按 `Max QPS` 排序取前 N。
  - `--method <name>`：只看指定方法（可重复/逗号分隔）。
- `apm service deps` 和 `apm service methods` 均支持 `--site i18n-bd`（映射到 mycis region）和 `--site i18n-tt` 海外查询，以及 `--region`、`--start`/`--end`（Unix 秒级时间戳）参数。`--range` 已废弃，不要使用。
- 构造带 `--measurement-tag` 或 `--aggregator` 的查询前，优先调用 `apm service measurement-params --psm <psm> --metric <measurement>` 获取后端建议的 `tags` 与 `aggregators`，并优先使用返回原值。该列表不是完备约束；有较强理由怀疑元数据不完整或排查特殊场景时，可以尝试集合外值，空结果也不证明字段不存在。该命令要求 `--psm`、`--metric`，可选 `--service-type`（默认 `service`）和单值 `--region`。
- `apm service qps` 和 `apm service downstream-qps` 支持重复传入 `--measurement-tag <key=value>` 过滤 Argos measurement tag；同一标签的多个可选值用 `|` 连接，例如 `--measurement-tag "service.env=prod"`。JSON 输出会在 `measurement_tags` 中回显实际过滤条件。
- `apm faas-mq-trigger metrics` 通过 infra Grafana datasource proxy 查询 FaaS MQ trigger 成功消费 QPS，默认 Grafana 为 `https://infra-grafana.byted.org`，默认 datasource 为 `vefaas-cn-beijing`。输出包含 PromQL、时间窗、点位数组与 min/max/avg/last 摘要。该命令的 `--duration` 是命令自有的默认时间窗，不适用 `apm metric query` 的 Query DSL 约束；如果需要可复现窗口，优先传 `--start-time` 和 `--end-time`。
- `apm faas-mq-trigger lag` 通过 infra Grafana 的 Influx datasource 查询 RocketMQ 生产 TPS、目标 consumer TPS 与目标 consumer group lag，默认 datasource 为 `rocketmq_metrics_ops-influxdb-BJ`。默认结束时间取 `now-2m`，避免当前分钟桶返回 0；输出中明确区分 topic 总生产速度、consumer group 消费速度和 group lag。
- 上述两个 FaaS MQ trigger 命令只有在 `--grafana-url` 的 hostname 为 `infra-grafana.byted.org` 时，才是 Grafana 认证的唯一 legacy session 例外：该实例当前不接受 ByteCloud `X-JWT-Token`。仅在这个 hostname 返回 Grafana 登录态错误时运行 `bytedcli --site cn auth login --session --auto`；非 infra 的 `--grafana-url` override 使用用户 ByteCloud JWT，运行 `bytedcli auth login`，不得刷新或回退 session。普通 `grafana ...` 命令同样必须使用 ByteCloud JWT，不能回退 session。
- `apm metric query` 的查询语句是**位置参数**，且**不支持** `--psm` 与 `--query` 参数，请直接将过滤条件（如 `_psm=...`）写在 query 的标签内。
- `apm metric batch-query` 从 `--input-file` 读取一个 JSON 对象。顶层
  `defaults` 可声明共享的 `start_time`、`end_time`、`duration`、`region`、
  `tenant`、`all_regions` 和 `group_by_region`；`queries` 中每项必须包含唯一
  `request_id` 与 `query`，并可覆盖这些默认值。`--concurrency` 默认为 6，
  范围 1-32。结果保持输入顺序并返回 `executed` / `reused` 计数；单项失败记录
  在对应 item 中，不取消整批。同一 batch 复用 SDK 和 Byteplot JWT；明确的
  HTTP 401 会熔断该通道的后续请求并复用错误。该命令适合定时监控，配合全局
  `--no-auto-upgrade` 避免后台升级任务干扰采集。
- 部分指标（如 `bytedtrace.sdk.span.server.rate`）有 tag rewrite 逻辑，**必须指定 `_psm` tag** 才能查询，例如：`bytedtrace.sdk.span.server.rate{_psm=literal_or(example.demo.api)}{}`
- Metric 查询格式：`aggregator[:downsample][:rate{opts}][:topK]:metric_name{group_tags}{filter_tags}[multi_field_expr]`，**必须使用** `key=func(value)` 格式，**禁止** `key=value`。**Agent / Skills 必须严格按 `aggregator → downsample → rate → topK → metric` 的顺序拼接**（parser 实现宽松容错只是兜底，不作为推荐用法）。`[multi_field_expr]` 仅多值指标需要，**必须放在末尾**。顶层 aggregator 支持 `sum/avg/max/min/count/zimsum/pct50/pct90/pct99`（前 5 种为日常主力，`zimsum` 等价 `sum`，`pct50/pct90/pct99` 仅在百分位指标场景使用）；downsample / TopK 内部 agg 仅支持 `max\|min\|avg\|count\|sum`。downsample 必须以数字开头（如 `1m-sum-zero`），不支持旧格式 `sum-1m-zero`。详见 [metric.md](./references/metric.md)
- `apm metric query` 支持直接输入前端页面中的 Query DSL 进行解析（支持 `[xxx]` 等多值语法提取），必须用 `--start-time`/`--end-time`（Unix 秒级时间戳）指定时间窗。`--duration` 已废弃，不要使用。默认只查当前站点的默认单 region（如 `i18n-tt` 默认为 `Singapore-Central`）；只有显式多次声明 `--region` 或传入 `A|B` / `A,B` 时才做多机房联合查询；需要覆盖 Metrics FE 当前站点全部下拉 region 时用 `--all-regions`。
- `apm grafana query/search` 与 `apm bosun query` 走 Metrics FE 前端链路，使用当前用户 ByteCloud JWT，不需要 Metrics OpenAPI 的 app_name/app_secret，也不依赖浏览器 cookie。`apm grafana query` 可直接接收前端/Grafana 里的 ByteTSD DSL（`aggregator[:downsample]:metric{group_tags}{filter_tags}`），也兼容 `metric{tag=value}` 简化格式；若目标是从现有 Grafana 面板取点位，用 `bytedcli grafana query <grafana-url-or-uid> --panel <id>`，已知 Forge 指标大盘的 fountain read 面板会直接转 Metrics FE Byteplot 查询，其他面板会在 Cloud OpenAPI data 失败时自动 fallback。`apm bosun query` 调 Metrics FE 的 `/byteplot/api/v2/bosun/expr` 代理，可接收裸 OpenTSDB/ByteTSD 写法（例如 `sum:store:example.service.metric`，需配 `--duration`）、完整 `q(...)` 表达式，或多行 Argos 报警模板（直接传模板文本或 `@file`，自动翻译为可求值表达式，详见下文 bosun 条目；`--start-time/--end-time` 或 `--at` 可批量按时刻求值）。
- Metrics FE 按站点分桶：CN 用 `--site cn`，ByteIntl/BD 用 `--site i18n-bd`（兼容 `--site i18n`），ROW 用 `--site i18n-tt`（也可用别名 `--site row`），EU-TTP 用 `--site eu-ttp`，US-TTP 用 `--site us-ttp` / `--site us-ttp-bdee` / `--site us-ttp-usts`（也可用别名 `--site tx-ttp`）。不传 `--region` 时使用当前站点默认单 region；`--all-regions` 只展开当前站点包含的 VRegion；`--region` 只是当前站点内的查询维度，不会反向切换 Metrics FE 后端。若 VRegion 属于其他站点，改用对应 `--site`。
- 服务级 QPS / CPU / MEM：优先 `apm service preview --service-type service`（可加 `--region`）。QPS/SLA 读 `data.golden_signals`，CPU/MEM 读 `data.clusters.rows`（`cpu_percent` / `mem_percent`）。不要默认用 `runtime` 代替服务级资源维度；`runtime` 走 Byteheart，与 Argos service overview 不是同一条链路。
- `apm service preview --service-type service|redis` 走 Argos overview；`runtime` / `tlb` / `tcc` / `mysql` / `agw_sidecar`（以及对应 shortcut 子命令）走 Byteheart `get_global_view`。
- Redis 相关命令返回 Grafana/Argos 监控入口链接（按集群维度）
- `apm service qps` 基于 Argos measurement 接口，可用 `--metric` 指定指标，支持使用 `--region` 参数过滤 vregion；现已支持通过 `--site i18n-tt` 进行海外控制面查询。支持传入多个机房进行正则聚合查询（通过多次指定 `--region A --region B`，或直接传入 `China-North|Singapore-Central` 格式）
- `apm service downstream-qps` 基于 Argos measurement 接口，默认指标为 `service.request.downstream.throughput.total`，用于查看服务调用下游依赖的 QPS，同样支持 `--region` 参数过滤 vregion 以及 `--site i18n-tt` 海外查询。支持传入多个机房进行正则聚合查询（通过多次指定 `--region A --region B`，或直接传入 `China-North|Singapore-Central` 格式）
- APM 的 Argos measurement / monitoring / event API base URL 可用环境变量 `BYTEDCLI_APM_API_BASE_URL` 覆盖，值支持裸域名或完整 `https://...`。该变量只覆盖这些 APM Argos API 请求，不覆盖 `apm argos log aggregate` 的 StreamLog host；认证 origin / JWT host 仍按当前 `--site` 解析。
- `apm redis qps/traffic` 基于 Cache 服务详情的当前统计值
- `apm argos stable-code get/add/delete` 对应 Argos 服务配置里的「稳态码配置」页签。`add` / `delete` 只更新业务稳态码列表 `biz_status_code_config.stable_codes`，其他 config 字段保持不变。资源可用 `--psm <psm>`、`--tree-node-id <id>` 或 `--resource-type psm|tree_node --resource-name <name>` 指定；`--metrics-region` 可按需透传。默认只预览 payload，不发 POST；显式 `--dry-run` 也只预览；只有传 `--yes` 才真正写入。CLI 会自动读取当前配置版本，也可用 `--version <n>` 显式指定。
- `apm argos bosun query` 通过 Argos `bosun/data` 接口查询 VMP（Volcengine Managed Prometheus）数据，是 Argos 自定义看板 `query_type: "bosun"` 面板的同条链路；与 `apm bosun query`（走 Byteplot `/byteplot/api/v2/bosun/expr`，OpenTSDB 语法）相互独立。
  - 简化模式：`--prom` + `--account-id` + `--workspace-id`，CLI 自动包装成 `["accountID=…&workspaceID=…"]promql/promras(...)`；用 `--func promras` 切换包装函数（promras 顶层函数必须带 `by` 子句）。
  - Passthrough 模式：`--expr` 或 `--expr-file` 直接传入完整 bosun 表达式（`promras` 多变量组合或从看板面板复制的整段表达式推荐使用此模式）。
  - `--region` 是火山引擎 region（默认 `cn-beijing`），不是 Argos region。
  - 前置条件：火山账号必须先通过 Argos 多云代理工单加入；详见 [`references/vmp-bosun.md`](./references/vmp-bosun.md)。
- `apm bosun query` 通过 Byteplot `/byteplot/api/v2/bosun/expr` 查询 OpenTSDB 风格的 Bosun 表达式（与 metrics-fe Bosun 面板同链路）。同一求值链路在浏览器里有现成的交互调试页：Byteplot 控制台的 Bosun 表达式页（i18n-tt 为 `https://metrics-fe-i18n.tiktok-row.org/web/bosun`，CN 为 `https://metrics-fe.byted.org/web/bosun`），可在线编辑表达式并展示结果与每个子表达式的值（Computations 列），支持时区/求值时刻/region 切换与查询历史；注意 Computations 的 Text 是求值器规范化后的重渲染（括号剥离、group tag 解析为实际值），无法映射回变量名，按变量名逐个求值仍用 `apm bosun analyze`。
  - 输入形态三选一：`aggregator:metric{...}` 这种 OpenTSDB 简写（必填 `--duration <1h|30m|1d|...>`，CLI 自动包装成 `q("...", "<duration>s", "<downsample>")`）；含 `q(...)` 的完整表达式（含被包裹的形态，如 `avg(q("...", "1h", "")) < 10`，自带窗口，无需 `--duration`）；多行模板（见下，同样无需 `--duration`）。
  - 多行 Argos 报警模板：位置参数可直接传模板全文，或用 `@/path/to/template.txt` 读文件。CLI 只做格式翻译、不做静默纠错：剥离 `template version` 头与 Argos 专有 flag 行（映射见下方"模板全局开关"）、剥离中文注释行、并在末尾追加该变量的引用行作为末句裸表达式（Argos 模板惯例以赋值结尾，而求值器要求末句是裸表达式——末句读的是最后一次赋值后的变量值，自引用重赋值如 `$a = $a + 1` 不会被二次计算；文本输出会标注 `Template final statement: <var>`）。模板模式无需 `--duration`。注意：注释剥离按"行含 CJK 即注释"，模板格式本身不含中文字符串字面量。
  - Argos 报警规则的末行惯例是 `warn = <expr>`（变量名无 `$` 前缀，或 `warn = $xxx`）。求值器只支持 `$` 变量（裸名会被当成函数名解析并报 `non existent function warn`），因此默认 fail-fast 报错并给出两个出路：改写 `$warn = <expr>`，或改用 `apm bosun analyze`（其语句引擎原生接受 `warn=` 结尾，无需任何改写）。中间行的变量名必须带 `$` 前缀。
  - 模板全局开关（global flags）：写在模板开头的特殊变量赋值，控制求值器的空值处理行为。
    - `$nanAsZero = true`：NumberSet 层补零——算术与比较中的 NaN（缺数据）按 0 处理。这是"窗口内无成功量也能算出 0、而不是整条表达式无结果"的关键开关；关掉后无数据窗口会直接返回 "No data found"，下游链路全部为空。
    - `$fillZero = true`：SeriesSet 层补零——多序列 join 后缺失的点补 0。纯数值运算（NumberSet）的模板里无效果。
    - Argos 模板头部三行 flag 的映射：`fullJoinGroup=true` → 翻译为 `$nanAsZero = true`（建议保持开启）；`fullJoinSeries=true` → 翻译为 `$fillZero = true`；`nullAsZero=true` → 无 Byteplot 等价物，CLI 直接丢弃（Argos 引擎专属）；其他未知 flag 行不会被剥离，原样发给后端会得到 HTTP 400 `unknown key <name>`。
  - 常见错误与正确写法（CLI fail-fast，不做静默规避）：
    - 空 group tag（`{tag=,}`）：直接报 `APM_INPUT_ERROR`（后端本身也会 400）。group-by 全部取值的正确写法是 `{tag=*}`；从 Argos 复制模板时需手工把 `{tag=,}` 改成 `{tag=*,}`。
    - 除零/无数据：分母为 0 或窗口无数据时结果为 `null`，不报错；模板里的 `+1e-9` 是模板作者自己的防除零手段，CLI 不做任何兜底改写。
    - 末句规则：多语句求值要求最后一条是裸表达式；Argos 模板以赋值结尾是 Argos 引擎自己的约定，CLI 在末尾追加该变量的引用行（读最后一次赋值后的值）只是两种格式间的必要翻译，语义无损（同一变量多次赋值时以最后一次为准，自引用重赋值不会被二次计算）。末行若写成无 `$` 前缀的 `warn = <expr>`，报错并提示改写 `$warn = ...` 或改用 `apm bosun analyze`。
    - 中间行裸变量名（`rate = ...`，无 `$` 前缀）：报 `APM_INPUT_ERROR`——求值器把裸名当函数名解析，且后续行也无法引用无前缀的变量。
  - `--end-time <epochSeconds>` 可选：Bosun 表达式基于一个求值基点（"now"）执行，`q()` 中的 start/end delta 均相对于此基点。传入 Unix 秒级时间戳后 CLI 会换算成 UTC `date=YYYY-MM-DD&time=HH:MM:SS` 透传给后端；不传则基点默认为当前时间。例如 `q("sum:metric{}", "1h", "")` 查的是基点前 1 小时到基点的数据。
  - 时间区间/多时刻批量求值：`--start-time` + `--end-time` 进入 range 模式，同一表达式按 `--interval`（默认 `30s`）对齐整点逐点求值（含两端）；或用可重复的 `--at <ts>` 指定一批显式时刻（自动去重排序）。适合扫一段告警窗口看触发条件的 0/1 切换时刻，不用逐点手调 `--end-time`。`--concurrency` 控制并发（默认 10，范围 1-20），单次最多 1000 个点（超出报错，提示调大 `--interval` 或收窄窗口）。输出按时间升序每点一行；单点失败标 ERROR 不中断整体，仅当全部点失败时 exit code 为 1。JSON 输出为 `{points: [{timestamp, type, results: [{group, value}]}], failed_count}`。
  - `--region` 直接透传 Byteplot `_region`（如 `Singapore-Central|Singapore-Compliance`、`US-TTP`）。`--site` 决定调用的 Byteplot 集群（`cn` / `i18n-tt` / `eu-ttp` / `us-ttp` 等）。`--all-regions` 可展开当前站点全部前端 region。
  - 鉴权与 `apm metric` 共用 Byteplot SSO JWT，无需单独配置。
- `apm bosun analyze` 在 Bosun Playground 语句引擎（Argos 报警引擎的专用语句分析端点）上分析一条多行 Bosun 语句或 Argos 报警规则：一次请求返回按 group 分行的最终值、每个变量的值、全部子表达式求值节点和最终条件的表达式 AST，用于排查告警触发原因（如"同环比哪个窗口跌了"）。输入与 `bosun query` 相同（模板文本或 `@file`）。
  - 两种输入形态都支持，CLI 不做末行手术：Argos 规则（末行 `warn = <expr>`）原样透传；整体 Bosun 语句（末行 `$var = expr` 赋值）自动追加 `warn = $var`（末行裸表达式则转写为 `warn = <expr>`）。CLI 只剥离 `template version` 头与中文注释行；`critical=` 等其他 keyed 行不改写，引擎会以带 line:col 的 `unknown key <name>` 报错教学。
  - 惰性求值与补洞：引擎只计算最终条件依赖图内的变量；依赖图外的声明变量（如未被 `warn` 引用的 `$success_t1h`）由 CLI 自动补发 `warn = $var` 请求取值（内部固定并发），输出里列在 `Lazy-evaluation fills`。补洞失败不中断（该变量标 ERROR）。字面量变量直接展示不请求。单次引擎求值常在数秒量级，总耗时 ≈ 主请求 + 补洞请求数（`evaluated_count`）；排查慢在哪里用 `--detail profile`。
  - `--region` 必填且可重复（无默认值、无 `--all-regions`）：引擎 region 与 Byteplot region 同名但语义是执行路由。合法值：`Singapore-Central`、`Singapore-Compliance`、`MY-Compliance`、`ID-Compliance`、`ID-Compliance2`、`Asia-SouthEast`、`EasternEuro-TT`、`Europe-Central`、`I18N-BGE`。
  - 其余选项：`--end-time <epochSeconds>`（求值锚点，默认 now；`q()` 窗口相对它计算）、`--limit <0|20|50|100>`（group 上限，默认 100，0 为不限）、`--group <k=v>`（可重复，精确 tag 过滤）、`--show-expr`（打印实际发出的语句与补洞语句）、`--detail <sections>`（可选附加段，逗号分隔可重复：`tree` 求值树、`queries` 解析后的 metric 查询、`profile` 引擎耗时树、`full` 全部附加段 + 逐 group 全节点表 + 完整序列）、`--timeout-ms`（默认 120000；语句求值可能超过一分钟）。
  - 输出（文本，默认）：摘要行（start/region/group 数/请求数）→ 每个 group 一段（tag 行 + `final = <值>` + 变量表）。最终值原样呈现（如 `final = 1`），不做告警判定解读。求值树（AST 节点 id + 表达式 + 值，多 group 时树只渲染一次、值看各组变量表）按需 `--detail tree` 打开。JSON：`{engine, start, region, limit, final_var, statement_count, evaluated_count, group_count, expr, groups: [{group, info, variables, nodes}], filled_variables, not_evaluated}` 恒含 AST；序列节点默认只给统计（points/min/max/avg/last_ts），`--detail full` 才含完整序列；`queries` / `profile` 字段按 `--detail` 出现。
  - 已知引擎怪癖：`limit` 只接受 {0,20,50,100} 枚举；恰好只开一个 `with_*` 输出开关会必现 400（CLI 恒发 ≥2 个，用户无需关心）；`warn must be specified` 报错既是"语句缺 warn 行"的确定性错误、也曾在合法语句上瞬态出现——重试一次再排查。
  - analyze 是单时刻命令（只有 `--end-time` 锚点）；要横扫时间轴看最终值随时间的变化，用 `bosun query --start-time/--end-time` 或 `--at`。
  - Region 路由提示：指标可能只落在站点内某一个 region（如 i18n-tt 的 Singapore-Central），返回全零/空结果时，先换显式 `--region` 再试，避免把"无数据补零"误判为指标跌零。`--site` 对 analyze 无路由作用（语句引擎为独立 i18n 服务，无需登录）。
- `apm argos oncall` 全部子命令均通过当前 `--site` 对应的 ByteCloud OpenAPI 网关发送；当前仅支持 `cn` 与 `i18n-tt`，其他站点会报 `APM_INPUT_ERROR`，不会固定回落到 CN 控制面。`plan search/get` 查询值班计划列表与详情；`plan set-users` 支持 `--only`（仅替换）与 `--dry-run`（预览，不发 PUT），`--user` 可重复指定或逗号分隔。
- `apm argos oncall plan search/get` 查询 Argos 值班计划列表与详情；`plan set-users` 支持 `--only`（仅替换）与 `--dry-run`（预览，不发 PUT）；`--user` 可重复指定或逗号分隔。
- `apm argos oncall plan set-rotation` 修改值班计划轮转设置（`rotate_switch` / `rotate_num` / `rotate_time`）：`--daily <hour>` 生成 `rotate_time=-1,<hour>`（每天），`--weekly <1-7> --hour <0-23>` 生成 `<weekday>,<hour>`，`--rotate-time` 直接传原始串；`--num` 每次轮换人数，`--switch on|off` 轮转开关；默认更新全部 config，`--config-index` 只改指定 config；`--dry-run` 打印 before/after 不发 PUT。
