---
name: bytedance-slardar
description: "Use bytedcli Slardar Web/App/OS/PC/Media SDK and Perfsee Lab for alarm pages, Web/Hybrid Query Assistant, dashboards/kanban, JS errors, PC detail/native-crash/logQuery_v2, reporter logs, Perfsee project/lab/snapshot/report URLs, App/OS issue links, crash/ANR/native/app/start trends, stack logs/retrace/symbolization, Android .so BuildID/crash_lib_uuid/symbol URLs, App log search/download/decrypt (#/track/logSearch), /node/os_detail and system ANR/native stacks."
---

# bytedcli Slardar

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

- Slardar Web / Hybrid 查询、Dashboard / Kanban、Workflow Studio、Data Explore、Flex 元数据、告警规则、告警历史、JS error issue、SOP 与 Investigation。
- Slardar App issue URL、异常趋势、事件日志、Slardar retrace、native 栈符号化、native symbol URL。
- Slardar App 日志文件检索（`#/track/logSearch/logs`）：按设备 ID 列出、筛选、下载日志文件；本地加密 ALog zip 解密。
- Slardar OS issue URL、事件 summary、main thread stack、APK embedded native stack 符号化。
- Slardar PC 大盘、native-crash issue 列表/事件/结构化堆栈，以及按 UID 或 DID 查询 PC / Media SDK reporter 日志。
- Slardar PC ALog 文件检索：`slardar pc alogfile list --aid <aid> --did <did> --date YYYY-MM-DD` 返回文件时间戳、类型和鉴权下载链接；完整参数见 `references/slardar.md`。
- Perfsee Lab 项目配置、Settings Pages/Environment/权限/选项、Snapshot 列表/详情、Report 列表/详情、Report artifact 下载，或从 Perfsee URL 解析 project/snapshot/report 参数。
- 用户只贴 Slardar URL 时，先按 URL path 区分 `web`、`app`、`os`、`pc`、`perfsee` 子命令。

## Command layout

- Web: `bytedcli slardar web <command>`
- App: `bytedcli slardar app <command>`
- App CLI: `bytedcli slardar app-cli [args...]` — interactive AI agent for Slardar App diagnostics
- OS: `bytedcli slardar os <command>`
- PC / Media SDK: `bytedcli slardar pc dashboard get`, `pc issue list|log`, `pc log list`
- Perfsee: `bytedcli slardar perfsee <command>`

## URL routing

- App log file search URL containing `#/track/logSearch/logs`: use `bytedcli --json slardar app file list --url "<url>"` to list log files, or `bytedcli slardar app file download --all --url "<url>" --output ./logs` to download all files.
- Encrypted App ALog zip: use `bytedcli slardar app log decrypt --aid <aid> --os Android --input ./sample-alog.zip --output ./sample-alog.txt`; `--region` defaults to `cn` and can be overridden.
- App issue URL containing `/node/app_detail/`: use `bytedcli --json slardar app issue log --symbolicate --url "<url>"` when the user wants readable native stacks; omit `--symbolicate` when they only want the raw event log.
- OS issue URL containing `/node/os_detail/issue/overview/system/detail`: use `bytedcli --json slardar os issue log --symbolicate --url "<url>"` when the user wants readable native stacks; omit `--symbolicate` when they only want the event summary.
- PC dashboard URL containing `/node/pc_detail/dashboard`: load `references/slardar.md`, then use `bytedcli --json slardar pc dashboard get --url "<url>"` for overview/trends/distribution, `pc issue list --url "<url>"` for native-crash issues, or `pc log list --url "<url>" --user-id <id>|--device-id <id>` for detail logs.
- PC crash URL containing `/node/pc_detail/crash/overview`: use `bytedcli --json slardar pc issue list --url "<url>"`. For `/node/pc_detail/crash/detail`, use `bytedcli --json slardar pc issue log --url "<url>"` to return the selected event, context, process parameters, threads, and parsed frames.
- PC jank URL containing `/node/pc_detail/jank/detail`: use `bytedcli --json slardar pc issue log --url "<url>"` to return the selected event and hung thread stack. Use `--thread-index` to select a specific thread.
- PC log URL containing `/node/pc_detail/logQuery_v2`: use `bytedcli --json slardar pc log list --url "<url>"`. The URL may already contain a selector as `search_type=user_id|device_id` plus `search_key`. PC commands use direct structured APIs and do not depend on Slardar Assistant.
- Any Slardar Web URL (`*.bytedance.net`, `*.byteintl.net`, `*.tiktok-row.net`): use `bytedcli --json slardar web analyze-url --url "<url>"` to parse the URL into structured fields and a recommended follow-up command without making a network request. Use this first when the URL is unknown or ambiguous.
- Call Slardar Web Agent (Slardar CAT): use `slardar web chat send|get|download-artifact|cancel|list|check-auth` to invoke Slardar CAT Agent for open-ended analysis, diagnostics, complex task orchestration, artifact downloads, and multi-turn collaboration. CAT Agent can query metrics, logs, dashboards, alarms, and more through a single conversational interface. Load `references/slardar-cat.md` for the full workflow.
- Web alarm URL (`/node/web/alarm`): use `bytedcli --json slardar web analyze-alarm-url --url "<url>"`, then fetch alarm history and optionally start an investigation.
- Web dashboard URL containing `/node/web/kanban/detail/`: use `bytedcli --json slardar web dashboard get --url "<url>"` to inspect one dashboard, or `slardar web dashboard list|get|create|update-name|like|unlike|item add|update|delete|migrate|migrate-hybrid-v3` for dashboard management. Prefer `--url` for existing dashboards so the CLI can parse `dashboard_id / bid / env / site_type / region / lang` from the page URL.
- Web JS error tasks: use `slardar web js-error-list`, `slardar web js-error-issue-detail`, or `slardar web js-error-issue-stack`. For Hybrid / Lynx pages (Slardar URL `site_type=hybrid&container_type=lynx`), pass `--site-type hybrid --container-type lynx` together with the URL's `--region` / `--subregion` so Slardar can narrow the JS error list to that container. When the URL carries `filter_id=<hex>`, pass `--filter-id <hex>` to replicate the saved filter the user sees in the browser; use `slardar web js-error-filter-get` first if you want to inspect or capture the resolved `filter_conditions` for reuse.
- Web Workflow Studio tasks: use `slardar web workflow list|get`, `slardar web workflow trigger list`, or `slardar web workflow tool list`.
- Web Data Explore tasks: use `slardar web data ev-types|columns|trend|list|get|session-list`. Prefer `data list` for event rows and `data get --dh-key <dh-key>` for the full `metric_map/json` of one row. Use `--filter-conditions-json`, `--metrics-json`, `--dh-keys-json`, and `--request-json` when mirroring a browser request.
- Web Flex meta tasks: use `slardar web flex meta`, `slardar web flex event-list`, `slardar web flex event-measure`, or `slardar web flex metric-related`; add `--filter-label` to narrow local output by display label. In JSON mode, top-level `raw` is off by default for meta commands; use `--with-raw` to include it and `--without-row-raw` to trim row-level `raw`.
- Web Flex query-config tasks: use `slardar web flex config get` / `save`. `config save` reads `--query-config` / `--query-config-file` as the base config, then applies high-frequency overrides such as `--start-time` / `--end-time` / `--measure-list-json`.
- Web Flex chart queries: use `slardar web flex query candidate|series|pie|indicator-card|pivot-table|histogram`. Prefer `--request-json` / `--request-file` for the full body, then use override flags like `--group-by-list-json`, `--topn-json`, `--time-shift-list-json`, `--cond-settings-json`, `--long-term-options-json`, and `--histogram-config-list-json` when only a few top-level fields need to change. For custom-event line charts, load `references/slardar.md` and follow "Web Flex custom-event line chart".
- Web event metric design application: use `slardar web event apply --design-file <path>` or `--design-json <json>` to create missing events and merge their keys by `key_name + key_type`. `--dry-run` previews the planned create/update actions without writing. `--update-existing-event` also applies the design's description and owners to already existing events; without it, existing event metadata is preserved while keys are merged.
- Web event key deletion: use `slardar web event key delete --event-name <event-name> --key-name <key-name> [--key-type category|metric|extra]` to remove one or more keys from an existing event. Use it before `event apply` when you need to remove a legacy key entry and re-apply the desired design shape.
- Perfsee URL containing `/perfsee/projects/<projectId>/lab`: use `slardar perfsee project config --url "<url>"`, `snapshot list --url "<url>"`, or `report list --url "<url>" --snapshot-id <snapshot-id>`. Perfsee report URL containing `/lab/reports/<reportId>` can be used directly with `slardar perfsee report get --url "<url>"` or `report download --url "<url>"`.
- Perfsee Settings URL containing `/perfsee/projects/<projectId>/settings/<name>`: use `slardar perfsee permission get`, `setting get`, `page list|get|create|update|delete`, or `environment list|get|create|update|delete` with `--url "<url>"`.

## Investigation policy

If the user intent matches any of these keywords: `排查`, `排障`, `探索`, `分析`, prefer triggering a Slardar Investigation for Web alarm tasks via `slardar web start-investigation`.

Recommended ways to obtain `history_id`:

1. If the user provides a Slardar alarm page URL, run `slardar web analyze-alarm-url` to extract `rule_id / bid / site_type / time window`, then run `slardar web alarm-history` and choose a suitable `history_id`.
2. If the user provides `origin + bid + rule_id + start_time + end_time (+ env)`, directly run `slardar web alarm-history`.
3. If neither path has enough data, ask for `history_id`, the alarm page URL, or the rule/time window.

Then run:

```bash
bytedcli slardar web start-investigation --history-id <history_id> --origin <slardar-origin>
bytedcli slardar web get-investigation --investigation-id <investigation_id> --origin <slardar-origin>
```

After `get-investigation`, read `status`. If it is `ongoing`, tell the user it is still running. If `sop_data` is present, parse it and check `is_default`: official SOPs can be mentioned without custom SOP links; custom SOPs can include the SOP link.

## Quick start

```bash
# Web Chat — Slardar CAT Agent (recommended for open-ended analysis)
bytedcli --json slardar web chat check-auth
bytedcli --json slardar web chat send --input "<问题或任务描述>"
bytedcli --json slardar web chat send --input "<问题>" --stream
bytedcli --json slardar web chat get --thread-id <thread-id>
bytedcli --json slardar web chat download-artifact --thread-id <thread-id> --path '<artifact-path>'
bytedcli --json slardar web chat send --thread-id <thread-id> --input "<追问>"
bytedcli --json slardar web chat cancel --thread-id <thread-id>

# Web / Hybrid
bytedcli slardar web query-assistant "查询bid为slardar_test，最近1天的JS错误数，按照错误信息分组"
bytedcli slardar web alarm-rule-list --origin <slardar-origin> --bid <bid> --site-type web
bytedcli slardar web alarm-history --origin <slardar-origin> --bid <bid> --site-type web --rule-id <rule-id> --start-time <start-time> --end-time <end-time> --env <env>
bytedcli slardar web analyze-alarm-url --url "<slardar-alarm-url>"
bytedcli slardar web analyze-url --url "<slardar-web-url>"
bytedcli --json slardar web dashboard list --url "https://slardar.example/node/web/kanban/detail/123456?env=production&bid=demo_bid&region=cn&lang=zh&site_type=web"
bytedcli --json slardar web dashboard get --url "https://slardar.example/node/web/kanban/detail/123456?env=production&bid=demo_bid&region=cn&lang=zh&site_type=web" --with-raw
bytedcli slardar web dashboard create --origin "https://slardar.example" --bid demo_bid --env production --site-type web --region cn --lang zh --name "demo-dashboard"
bytedcli slardar web dashboard update-name --url "https://slardar.example/node/web/kanban/detail/123456?env=production&bid=demo_bid&region=cn&lang=zh&site_type=web" --name "demo-dashboard-renamed"
bytedcli slardar web dashboard like --url "https://slardar.example/node/web/kanban/detail/123456?env=production&bid=demo_bid&region=cn&lang=zh&site_type=web"
bytedcli slardar web dashboard unlike --url "https://slardar.example/node/web/kanban/detail/123456?env=production&bid=demo_bid&region=cn&lang=zh&site_type=web"
bytedcli slardar web dashboard item add --url "https://slardar.example/node/web/kanban/detail/123456?env=production&bid=demo_bid&region=cn&lang=zh&site_type=web" --item-file ./sample-dashboard-item.json
bytedcli slardar web dashboard update --url "https://slardar.example/node/web/kanban/detail/123456?env=production&bid=demo_bid&region=cn&lang=zh&site_type=web" --items-file ./sample-dashboard-items.json --extra-file ./sample-dashboard-extra.json
bytedcli slardar web dashboard migrate --origin "https://slardar.example" --aid 123 --dashboard-detail-json '{"demo":{"bid":"demo_bid","env":"production","site_type":"web","region":"cn","lang":"zh"}}'
bytedcli slardar web dashboard migrate-hybrid-v3 --url "https://slardar.example/node/web/kanban/detail/123456?env=production&bid=demo_bid&region=cn&lang=zh&site_type=web"
bytedcli slardar web dashboard delete --url "https://slardar.example/node/web/kanban/detail/123456?env=production&bid=demo_bid&region=cn&lang=zh&site_type=web"
bytedcli slardar web event apply --bid demo_bid --site-type hybrid --region cn --lang zh --design-file ./sample-event-design.json
bytedcli slardar web event apply --bid demo_bid --site-type hybrid --region cn --lang zh --design-json '{"events":[{"event_name":"sample_event","description":"sample description","owners":["demo-owner"],"keys":[{"key_name":"sample_metric","key_type":"metric","description":"sample metric"}]}]}' --dry-run
bytedcli slardar web event apply --bid demo_bid --site-type hybrid --region cn --lang zh --design-file ./sample-event-design.json --update-existing-event
bytedcli slardar web event key delete --bid demo_bid --site-type hybrid --region cn --lang zh --event-name sample_event --key-name status_code --key-type metric
bytedcli slardar web start-investigation --history-id <history_id> --origin <slardar-origin>
bytedcli slardar web get-investigation --investigation-id <investigation_id> --origin <slardar-origin>
bytedcli slardar web workflow list --bid <bid> --env <env> --filter-name <workflow-name>
bytedcli slardar web workflow get --bid <bid> --env <env> --flow-id <flow-id>
bytedcli slardar web workflow trigger list --bid <bid> --env <env> --workflow-name <workflow-name>
bytedcli slardar web workflow tool list
bytedcli slardar web data ev-types --bid <bid> --env <env>
bytedcli slardar web data columns --bid <bid> --env <env> --ev-type <ev-type>
bytedcli slardar web data trend --bid <bid> --env <env> --ev-type <ev-type> --start-time <start-time> --end-time <end-time>
bytedcli slardar web data list --bid <bid> --env <env> --ev-type <ev-type> --start-time <start-time> --end-time <end-time> --metrics-json '["timestamp","url","session_id"]'
bytedcli slardar web data get --bid <bid> --env <env> --ev-type <ev-type> --dh-key <dh-key>
bytedcli slardar web data session-list --bid <bid> --env <env> --session-id <session-id> --start-time <start-time> --end-time <end-time>
bytedcli slardar web flex meta --bid <bid> --env <env> [--filter-label <label>] [--with-raw] [--without-row-raw]
bytedcli slardar web flex event-list --bid <bid> --env <env> [--filter-label <label>] [--with-raw] [--without-row-raw]
bytedcli slardar web flex event-measure --bid <bid> --env <env> --event-name <event-name> [--filter-label <label>] [--with-raw] [--without-row-raw]
bytedcli slardar web flex metric-related --bid <bid> --env <env> --measure-list-json '[{"measure_name":"sample.metric"}]'
bytedcli slardar web flex config get --bid <bid> --env <env> --id <analyze-id>
bytedcli slardar web flex config save --bid <bid> --env <env> --query-config-file ./sample-query-config.json
bytedcli slardar web flex query series --bid <bid> --env <env> --request-file ./sample-request.json --group-by-list-json '[{"group_by_name":"sample.dimension"}]'
bytedcli slardar web flex query histogram --bid <bid> --env <env> --request-file ./sample-request.json --histogram-config-list-file ./sample-histogram-config.json
bytedcli slardar web js-error-list --bid <bid> --env <env> --start-time <start-time> --end-time <end-time> --origin <slardar-origin> [--site-type hybrid --container-type lynx --region <region> --subregion <subregion>] [--filter-id <filter-id> [--filter-lang <lang>]] [--filter-conditions-json <json>|--filter-conditions-file <path>]
bytedcli slardar web js-error-filter-get --filter-id <filter-id> --bid <bid> [--origin <slardar-origin>] [--region <region>] [--site-type <site-type>] [--lang <lang>]
bytedcli slardar web js-error-issue-detail --bid <bid> --env <env> --issue-id <issue-id> --start-time <start-time> --end-time <end-time> --origin <slardar-origin>
bytedcli slardar web js-error-issue-stack --bid <bid> --env <env> --issue-id <issue-id> --release <release> --start-time <start-time> --end-time <end-time> --origin <slardar-origin>

# PC / Media SDK logs
bytedcli --json slardar pc log list --url "https://slardar-demo.tiktok-row.net/node/pc_detail/dashboard?aid=123&region=demo-region&start_time=1770000000&end_time=1770000300&lang=zh" --user-id demo-user-0001 --time-type client --order asc --report-type mediasdk_log --keyword SetBackgroundImage --keyword SDKRespTimeoutEvent
bytedcli --site i18n-tt --json slardar pc log list --aid 123 --region demo-region --start 1770000000 --end 1770000300 --device-id demo-device-0001 --time-type client --order asc --regex 'create texture fail|media sdk crash'
bytedcli --site i18n-tt --json slardar pc log list --aid 123 --region demo-region --start 1770000000 --end 1770000300 --device-id demo-device-0001 --log-type exception --log-type custom-log
bytedcli --json slardar pc log list --url "<pc_detail_url>" --user-id demo-user-0001 --page-token "<next_page_token>"

# PC dashboard and native-crash drilldown
bytedcli --site i18n-tt --json slardar pc dashboard get --aid 123 --region demo-region --start 1770000000 --end 1770604800
bytedcli --json slardar pc issue list --url "<pc_dashboard_or_crash_overview_url>" --page 1 --page-size 10
bytedcli --json slardar pc issue list --url "<pc_crash_overview_url>" --keyword 'EXCEPTION_ACCESS_VIOLATION_READ' --order-by errors
bytedcli --json slardar pc issue log --url "<pc_crash_detail_url>"

# Org BID list
bytedcli --json slardar web bid-list --origin <slardar-origin> --oid "<oid>" [--start-time <ts>] [--end-time <ts>] [--metric-list-json '<json-array>'] [--metric-list-file <path>]

# --metric-list-json format: array of objects, each with:
#   description: string  — display label (e.g. "PV")
#   name: string         — metric key (e.g. "hybrid_pv.count_recover")
#   type: string         — value type (e.g. "number")
#   unit: string         — unit suffix (e.g. "", "%")
#   groupKey?: string    — grouping key (e.g. "base")
#   groupName?: string   — group display name (e.g. "用户分析")
#   isDefault?: boolean  — whether this is a default metric
# Note: Available metrics vary by organization. If omitted, metricMap will be empty.

# Alarm rule management (dry-run by default, requires --confirm)
# Recommended workflow: use alarm-rule-list to get the existing full config, modify, then pass via --alarm-param-file
# alarm-rule-update is full-payload: the submitted alarm_param replaces the whole rule, so always edit a complete rule fetched from alarm-rule-list.
# To disable a rule, set "is_close": true on its full alarm_param and submit via alarm-rule-update (there is no separate close command).
bytedcli slardar web alarm-rule-create --origin <slardar-origin> --bid <bid> --alarm-param-file ./alarm.json [--confirm]
bytedcli slardar web alarm-rule-update --origin <slardar-origin> --bid <bid> --alarm-param-file ./alarm.json [--confirm]

# Alarm region sync (two independent base APIs)
# 1) List the regions an alarm entity is already synced to (entity-id/region = any one existing synced region)
bytedcli --json slardar web entity-region-get --origin <slardar-origin> --bid <bid> --entity-id <entity-id> --entity-region <sg|us_ttp|eu_ttp>
# 2) Set the full synced region map (dry-run by default, requires --confirm; region_map is full-payload overwrite).
#    To add a new region, first run alarm-rule-create in that region to get its entity id, then include all regions here.
bytedcli slardar web entity-region-update --origin <slardar-origin> --bid <bid> --region-map-file ./region-map.json [--confirm]
# These two endpoints only accept the control-panel JWT (x-slardar-global-control-panel-jwt) and do NOT accept the
# ByteCloud JWT fallback. Point --origin at the global console host (e.g. https://slardar-sg.tiktok-row.net) so the
# panel JWT is minted automatically.

# Perfsee Lab
bytedcli slardar perfsee url parse --url "https://slardar.example/perfsee/projects/demo-project/lab/reports/85/overview"
bytedcli --site cn auth login --session
bytedcli slardar perfsee auth login --origin "https://slardar.example"
bytedcli slardar perfsee auth status --origin "https://slardar.example"
bytedcli --json slardar perfsee project config --url "https://slardar.example/perfsee/projects/demo-project/lab"
bytedcli slardar perfsee permission get --url "https://slardar.example/perfsee/projects/demo-project/settings/pages"
bytedcli slardar perfsee setting get --url "https://slardar.example/perfsee/projects/demo-project/settings/pages"
bytedcli slardar perfsee page list --url "https://slardar.example/perfsee/projects/demo-project/settings/pages"
bytedcli slardar perfsee page get --url "https://slardar.example/perfsee/projects/demo-project/settings/pages" --page-id 11
# All six Settings writes default to dry-run and return the complete GraphQL variables. Add --yes after reviewing the preview.
bytedcli slardar perfsee page create --url "https://slardar.example/perfsee/projects/demo-project/settings/pages" --page-file ./page.json --yes
bytedcli slardar perfsee page update --url "https://slardar.example/perfsee/projects/demo-project/settings/pages" --page-id 11 --page-file ./page.json --yes
bytedcli slardar perfsee page delete --url "https://slardar.example/perfsee/projects/demo-project/settings/pages" --page-id 11 --yes
bytedcli slardar perfsee environment list --url "https://slardar.example/perfsee/projects/demo-project/settings/pages"
bytedcli slardar perfsee environment get --url "https://slardar.example/perfsee/projects/demo-project/settings/pages" --environment-id 21
bytedcli slardar perfsee environment create --url "https://slardar.example/perfsee/projects/demo-project/settings/pages" --environment-file ./environment.json --yes
bytedcli slardar perfsee environment update --url "https://slardar.example/perfsee/projects/demo-project/settings/pages" --environment-id 21 --environment-file ./environment.json --yes
bytedcli slardar perfsee environment delete --url "https://slardar.example/perfsee/projects/demo-project/settings/pages" --environment-id 21 --yes
bytedcli slardar perfsee snapshot list --url "https://slardar.example/perfsee/projects/demo-project/lab"
bytedcli slardar perfsee snapshot get --url "https://slardar.example/perfsee/projects/demo-project/lab?snapshotId=31"
bytedcli slardar perfsee report list --url "https://slardar.example/perfsee/projects/demo-project/lab?snapshotId=31"
bytedcli slardar perfsee report get --url "https://slardar.example/perfsee/projects/demo-project/lab/reports/85/overview"
bytedcli slardar perfsee report download --url "https://slardar.example/perfsee/projects/demo-project/lab/reports/85/overview" --kind lhr,requests,trace -o ./perfsee-report
bytedcli slardar perfsee snapshot run --url "https://slardar.example/perfsee/projects/demo-project/lab" --page <page-name-or-id> --profile <profile-name-or-id> --env <env-name-or-id> --wait
bytedcli slardar perfsee snapshot run-temp --url "https://slardar.example/perfsee/projects/demo-project/lab" --target-url "https://example.com/" --profile <profile-name-or-id> --env <env-name-or-id> --wait

# App
bytedcli --json slardar app issue log --url "https://slardar.example/node/app_detail/?region=cn&aid=123&os=Android&type=app&lang=zh#/abnormal/detail/crash/demo_issue?params=%7B%22start_time%22%3A1773410940%2C%22end_time%22%3A1776089340%2C%22event_index%22%3A1%7D"
bytedcli --json slardar app issue log --symbolicate --url "https://slardar.example/node/app_detail/?region=cn&aid=123&os=Android&type=app&lang=zh#/abnormal/detail/crash/demo_issue?params=%7B%22start_time%22%3A1773410940%2C%22end_time%22%3A1776089340%2C%22event_index%22%3A1%7D"
bytedcli slardar app symbol url --build-id 00112233445566778899aabbccddeeff00112233
bytedcli slardar app symbol url --uuid 33221100554477660
bytedcli slardar app trend --origin "https://slardar.example" --aid 123 --os Android --region cn --start-time 1778673780 --end-time 1778760180 --crash-type app --app-version 10.7.0 --channel gp
bytedcli slardar app trend --aid 123 --os Android --region cn --start-time 1778673780 --end-time 1778760180 --all-crash-types
bytedcli --json slardar app file list --aid 123 --os Android --region cn --device-id demo_device --start-time 1776092520 --end-time 1776351720
bytedcli --json slardar app file range --aid 123 --os Android --region cn --device-id demo_device --start-time 1776092520 --end-time 1776351720 --dimension scene
bytedcli slardar app file download --all --aid 123 --os Android --region cn --device-id demo_device --start-time 1776092520 --end-time 1776351720 --output ./logs
bytedcli slardar app log decrypt --aid 123 --os Android --input ./sample-alog.zip --output ./sample-alog.txt

# OS
bytedcli --json slardar os issue log --url "https://slardar.example/node/os_detail/issue/overview/system/detail?app_id=123&start_time=1775491200&end_time=1776133985&region=cn&category=3&time_type=client_time&filter_conditions=%257B%2522type%2522%253A%2522and%2522%252C%2522sub_conditions%2522%253A%255B%255D%257D&issue_id=demo_issue&pgno=1"
bytedcli --json slardar os issue log --symbolicate --url "https://slardar.example/node/os_detail/issue/overview/system/detail?app_id=123&start_time=1775491200&end_time=1776133985&region=cn&category=3&time_type=client_time&filter_conditions=%257B%2522type%2522%253A%2522and%2522%252C%2522sub_conditions%2522%253A%255B%255D%257D&issue_id=demo_issue&pgno=1" --max-frames 20
```

## Behavior notes

- `slardar web dashboard get --with-raw` is the easiest way to capture the current dashboard payload before editing. Reuse the returned `items` and `extra` with `dashboard update --items-file ... --extra-file ...` when you need a full dashboard rewrite.
- `slardar web dashboard item add` accepts a single dashboard item JSON object; `slardar web dashboard update` accepts the full dashboard `items` array plus optional `extra`.
- `slardar pc log list` extracts `aid / region / start_time / end_time / is_cts_time / reverse`, the selector, and the active category from a `logQuery_v2` URL. Repeat semantic `--log-type` values to combine `exception / process-status / custom-event / custom-log / network / fulldump`; bytedcli maps them to the verified page wire contract. `active_tab=did` means all six categories. The backward-compatible `--report-type mediasdk_log` shortcut selects `custom-log`; it cannot be combined with `--log-type`. Without an explicit filter or a `logQuery_v2` category, the default remains `mediasdk_log`. A query window cannot exceed 7 days. `--time-type client|server` and `--order asc|desc` override the URL values; the defaults are client time and ascending order. Keywords/regex filter the fetched page locally, and `next_page_token` continues server pagination without embedding the selected UID/DID. Regex matching runs in a time-bounded worker. Query output follows existing Slardar log commands and does not redact authorized fields by default; treat JSON/text output as sensitive.
- `slardar pc dashboard get` returns process-start and active-user totals/trends, native-crash totals/rates/trends, and app-version distribution. `slardar pc issue list` exposes page-verified search, time basis, ordering, and standard pagination. `slardar pc issue log` resolves one event and calls the current structured `exception/stack_v2` contract; it is not the detail-log search endpoint.
- Without `--url` or `--origin`, all `slardar pc` read commands derive the PC origin from global `--site` only for the verified `cn` and `i18n-tt` mappings. Other sites require an explicit origin rather than guessing a PC host.
- For PC queries, the host-derived control plane and `--region` are independent. For example, `i18n-tt` identifies the ROW authentication/control plane while `maliva` identifies the Slardar data partition; neither represents the user's country or Tea region.
- A ROW `pc log list --user-id` request can return `SLARDAR_PC_PERMISSION_DENIED` when the Operations Gateway applies its data-access policy to plaintext `ReqBody.user_id`. The decision depends on the caller's access level and the UID's EU-data classification; it is not a Slardar application/region permission failure. If the UID should not be EU TikTok data, verify its DECC/PnS tags; otherwise use an approved compliant-access or pseudonymized query path. There is no general gateway whitelist bypass, and `--device-id` must not be used as a workaround unless DID is the identifier actually intended. An authorized query with zero rows is a successful no-data result, not a permission failure.
- `slardar app issue log --symbolicate` calls Slardar App retrace first, then falls back to local `.zst` native symbol download/decompression and `llvm-addr2line`.
- For `type=sdk` App issue pages, event list uses the SDK `aid` from the URL, but `issue log` / retrace use the host-app `aid` from the selected event. Using the SDK `aid` on `/event/log/get` returns `log not found`.
- `slardar app trend` queries `/api_v2/app/crash/trend` for App abnormal metrics. Android and iOS App abnormal `crash_type` values share the same response schema; `--all-crash-types` follows the selected OS meta list, while the no-flag default remains Android `anr` and iOS `watch_dog`. Text summaries use `*_total_` fields (`count_total_`, `count_start_total_`, `active_total_`, `user_active_total_`, `user_active_total_all_`) instead of summing trend series points.
- `slardar app log decrypt` uploads the encrypted ALog zip as base64 to Slardar App and downloads the decrypted txt through the existing Slardar file download flow. The command always requests a download URL internally, so large decrypted logs are saved as a file instead of being printed.
- `slardar os issue log --symbolicate` extracts native frames from the OS event main thread stack, groups APK embedded frames by `BuildId + APK offset`, then reuses Slardar App native symbol helpers.
- If one native symbol group fails to download or symbolize, the result keeps unresolved frames for that group and continues with the remaining groups.
- `slardar perfsee` accepts `--token`, `--authorization`, or `--cookie`; without explicit auth it reuses cached Perfsee cookies, then exchanges the `bytedcli --site cn auth login --session` SSO session. For CI, prefer a Perfsee access token via `PERFSEE_TOKEN`.

## References

- `references/slardar-cat.md`
- `references/slardar.md`
