---
name: bytedance-log
description: "Use bytedcli logs for PSM/LogID/instance/pod search, clusters, TCE logs/看 pod 日志, Footprint TCE Sync tail/head/ls/grep and viewlog search; download standalone Footprint or TTP/EU-TTP concrete mljob-log-proxy URLs only without Primus application/History/role/pod/Forge/Reckon context. Primus redirect_log.html, executor logs or contextual mljob URLs require bytedance-primus discovery/content."
---

# bytedcli Log

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

- 按 PSM / 时间搜索日志
- 按 LogID 查询单区域或多区域日志
- 按接口维度查看 BytedTrace 总体性能分析
- 按 LogID 查看 BytedTrace 调用树与节点延迟
- 按环境 / 实例 / Pod 搜索日志
- 查看日志聚类
- Footprint TCE Sync pod 文件日志：`log footprint get`
- 独立 Footprint / TTP/EU-TTP concrete 日志 URL 下载（无 Primus application/History/role/pod 上下文）：`log footprint download`
- Footprint viewlog 开放 API（受支持 log type：argos / dorado / tce / primus ...）：`log footprint search`

## 前置条件

- 使用通用调用方式：`../../invocation.md`
- 应用账号 AK/SK（非交互式 / CI）认证：`references/service-account.md`

> 执行前缀见 `../../invocation.md`；下面示例直接写 `bytedcli`。

## 重试策略（Skill 行为）

- 范围受限的只读查询遇到明确的瞬时网络错误、超时或服务端 5xx，且命令未启用 transport-level retry 时，可在 Skill 层自动重试 1 次；网络错误/5xx 保持或收窄范围，超时则先退避并收窄范围。必须展示首次失败原因和重试结果，不要静默循环。
- 自动重试只允许一层：幂等 GET 默认由 transport 层在统一预算内处理 408/425/429/5xx，Skill 不再自动重跑整条命令；如果由 Skill 控制整条命令重试，从首次执行起传 `--http-retry-count 0`。transport 耗尽后仍返回 429 时，不再通用自动重试，按 `Retry-After` 或命令专属规则串行处理；遇到 timeout、429 或 5xx 后，其余日志查询也降为串行。
- 参数校验、鉴权/权限、错误 region 和其他确定性 4xx 不得原样重试；先修正输入、路由或权限，命令专属的错误处理规则优先。
- 全量 dump、超过 6 小时的查询、扩大时间窗/条数、第二次及以上重试，或其他可能明显增加后端负载的操作，先取得用户确认；用户已在当前任务明确授权范围时按该范围执行。
- 同一查询的自动请求预算（初次 attempt + transport/Skill 重试）硬上限为 3 次；除经确认的扩窗/增量和命令专属恢复规则外，每次保持或收窄范围，并记录 attempts。

## 权限缺失处理

当日志查询页面或 CLI 报 `PSM 日志查看权限缺失`、`缺少以下 PSM 的 argos.streamlog.view 权限`、`AccessForbidden`、`101403`，或等价的 PSM 日志访问拒绝时，先提取缺权限的 PSM 列表，不要直接重试查询。

处理步骤：

1. 对每个缺权限 PSM 先运行只读检查，确认推荐角色和当前授权状态：

```bash
bytedcli --json iam permission apply --permission argos.streamlog.view --psm "<psm>" --reason "Need PSM log view access for troubleshooting" --check-only
```

2. 向用户展示检查结果：PSM、是否已有权限、`default_role_id`、可申请角色。优先建议 `--check-only` 返回的最小访问角色；角色 ID 与控制面有关，例如 CN 常见 `argos.streamlog_viewer.cn` / `日志访问人`。
3. 明确询问用户是否需要代为申请权限；未得到确认前，不创建工单。
4. 用户确认后再提交申请。若用户没有指定角色，使用 `--check-only` 返回的 `default_role_id`；若 `default_role_id` 为空，先让用户从 `available_roles` 中确认一个角色：

```bash
bytedcli --json iam permission apply --permission argos.streamlog.view --psm "<psm>" --role "<default_role_id>" --reason "Need PSM log view access for troubleshooting" --yes
```

完成标准：每个缺权限 PSM 都已完成 `--check-only`，并且要么用户确认后已提交申请，要么已明确记录用户未确认/拒绝申请。

## 查询策略（Skill 喜好）

- PSM 关键词查询保持 `--index-mode legacy` 默认以兼容已有调用。Agent 需要根据全部 PSM 的索引配置自动选择索引和 TERM 时，显式传 `--index-mode auto`；明确关闭时传 `--index-mode off`。`auto/on/off` 会忽略旧 `--enable-index`，不要同时传。
- LogID 查询优先级更高：当用户诉求包含某个/某些 LogID（即便同时给出 PSM），优先用 `log get-logid-log <logid> --psm <psm>` 查询。
- 如果用户明确要“先看接口总体瓶颈，再决定查哪些 logid”，优先用 `log analysis performance --psm <psm> --method <method> --start <time> --end <time>`。
- 如果用户明确要“看链路耗时 / 各节点延迟 / 调用树”，优先用 `log trace-tree --log-id <logid>`，不要继续用 `get-logid-log` 解析日志明细代替。
- 相互独立、非 rolling/非 dump、扫描范围不重叠且时间窗和条数均显式受限的只读查询，最多并发 2 个。同一取数任务的 pagination、retry、rolling slice、Footprint 分段，或相同/重叠扫描范围必须串行；全量 dump 不并发。
- 时间范围尽量精准且渐进扩展：优先使用用户给出的精确时间点（或从告警/工单/调用链获得的时间），先用 15m~30m 窗口定位；只有在证据不足时才逐步扩大窗口，避免一上来用小时级或天级范围。`get-logid-log` 支持 `--start`/`--end`（RFC3339 或 epoch 秒）显式指定时间范围，不传时服务端自动从 logid 嵌入的时间戳推导查询窗口（无需手动指定时间）。
- 超过 6 小时的 rolling 日志查询要按 6h 粒度串行执行：`search-psm-log`、`get-logid-log` rolling 模式（显式 `--rolling` 或 `--dump`）、`search-prod-instance-log`、`get-lane-instance-log` 在查询窗口超过 6h 时，会自动拆成多个不超过 6h 的时间片并串行请求；不要并发放大查询压力。
- 日志条数尽量最小且可控：`search-psm-log` 默认 `--max-logs 1000`；全量滚动需要显式传 `--max-logs 0`。`get-logid-log --psm` / `get-logid-log --rolling` 面向 LogID 定位，默认可全量滚动；首次排查仍优先显式设置较小的收集上限（如 `--max-logs 200`）与单次请求上限（如 `--limit 50` 或 `--limit 100`），只有用户明确要求全量 dump 时才使用 `--max-logs 0`。
- 扩大范围前先收窄条件：时间窗口不变时，优先通过 `--keyword/--exclude/--kv-filter/--idc` 收敛结果，再考虑扩大时间范围或提高 `--max-logs`。
- 大时间窗空查询要直接避免：当日志查询窗口超过 6h 且没有显式收窄条件（如 `--keyword`、`--exclude`、`--kv-filter`、`--level`、`--idc`）时，不要继续执行；先要求补充过滤条件或缩短时间范围。
- 关键词传参优先用重复选项：多关键词场景优先重复传 `--keyword/--exclude`（例如 `--keyword "a,b" --keyword "c"`），避免使用逗号分隔写法导致关键词内包含逗号时被误拆分。
- 多排除词需要任意命中即排除时，`search-psm-log` 传 `--exclude-operator OR`；默认 `AND` 会要求同一条日志同时命中全部排除词才排除。
- `get-lane-instance-log` 自定义日志文件：省略 `--path` 时默认只查 `app/${psm}.log`；用 `--path` 指定要查的日志文件，可重复或逗号分隔。传了 `--path` 会**整体替换**默认值（不是追加），因此若既要默认日志又要 verbose 等其它文件，必须把 `app/${psm}.log` 一并显式列出（例如 `--path 'app/${psm}.log' --path '/opt/tiger/log/app/<psm>_verbose.log'`）。示例里的路径统一用单引号，避免 `${psm}` 被 shell 提前展开。
- **site 与 vregion 优先精确匹配**：Logservice HTTP host 由 `(site, vregion)` 显式映射决定，不再根据 vregion 字符串动态拼域名。`--vregion` 默认值按站点不同：`cn` 为 `China-North`，`boe` 为 `China-BOE`，`i18n`/`i18n-bd` 为 `Singapore-SaaS`，`i18n-tt` 为 `Singapore-Central`，`us-ttp`/`us-ttp-bdee`/`us-ttp-usts` 为 `US-TTP`。无论是否显式传入 `--vregion`，表中未命中时都使用当前 site 的默认 host。如果不确定目标区域，应先询问用户服务部署在哪个 region。
- **i18n / i18n-bd + China-\* 路由变更**：`--site i18n-bd --vregion China-*` 会回退到 `logservice-mya.sinf.net`，`--site i18n --vregion China-*` 会回退到 `logservice-sg.tiktok-row.org`，均不再路由到 China endpoint。查询 `China-North`、`China-North6`、`China-East`、`China-Pay` 等 CN 路由时使用 `--site cn`；查询 `China-BOE`、`China-BOE2` 时使用 `--site boe`。

## Quick start

```bash
# PSM 日志搜索
bytedcli log search-psm-log --psm "psm.name" --start "2026-02-02T08:00:00" --end "2026-02-02T09:00:00"

# PSM 日志搜索（直接输出到控制台）
bytedcli log search-psm-log --psm "psm.name" --start "2026-02-02T08:00:00" --end "2026-02-02T09:00:00" --output console

# PSM 日志搜索（指定输出文件）
bytedcli log search-psm-log --psm "psm.name" --start "2026-02-02T08:00:00" --end "2026-02-02T09:00:00" --output file --output-file "/tmp/bytedcli.search.log"

# PSM 日志搜索（按 KV 过滤）
bytedcli log search-psm-log --psm "example.service.api" --keyword "deploy" --kv-filter "method=Deploy|Rollback" --kv-filter "_idc=lf|hl"

# PSM 日志搜索（按日志级别过滤）
bytedcli log search-psm-log --psm "example.service.api" --level Error --level Warn --max-logs 200 --output console

# PSM 日志搜索（错误/告警快捷过滤）
bytedcli log search-psm-log --psm "example.service.api" --error-warn --keyword "timeout" --max-logs 200

# PSM 日志搜索（多关键词按 OR 组合：命中任意关键词即返回，默认是 AND）
bytedcli log search-psm-log --psm "example.service.api" --keyword "GetFoo" --keyword "GetBar" --keyword-operator OR --max-logs 200 --output console

# PSM 日志搜索（多排除词按 OR 组合：命中任意排除词即过滤，默认是 AND）
bytedcli log search-psm-log --psm "example.service.api" --keyword "error" --exclude "known timeout" --exclude "known quota" --exclude-operator OR --max-logs 200 --output console

# PSM 日志搜索（超过 6h 会自动按 6h 串行分片）
bytedcli log search-psm-log --psm "example.service.api" --start "2026-02-02T00:00:00" --end "2026-02-02T18:00:00" --keyword "timeout" --output console

# PSM 日志搜索（索引加速查询：enable_index=true）
bytedcli log search-psm-log --psm "psm.name" --start "2026-02-02T08:00:00" --end "2026-02-02T09:00:00" --keyword "error" --enable-index

# PSM 日志搜索（索引加速 + 短语查询：is_term=true，不分词）
bytedcli log search-psm-log --psm "psm.name" --start "2026-02-02T08:00:00" --end "2026-02-02T09:00:00" --term "User not found" --enable-index

# PSM 日志搜索（BOE 的 boei18n 分区 US-BOE）
bytedcli --site boe --json log search-psm-log --psm "demo.psm" --vregion "US-BOE" --start "2026-04-16T21:08:48-07:00" --end "2026-04-16T21:33:48-07:00" --keyword "demo-keyword" --output console

# LogID 查询（默认走 logid_prune 精确查询，无需 PSM 和时间参数）
bytedcli log get-logid-log "20260202085428C91A145A63CB5F0B9D80" --vregion "China-North"

# 多区域 LogID 查询（默认 logid_prune 模式；用 | 分隔并加引号）
bytedcli --site cn log get-logid-log --logid sample-log-id --vregion 'China-North|China-North6' --output console

# 保留日志中 object/array 形态的 JSON string，不按默认 prune 行为展开
bytedcli log get-logid-log "20260202085428C91A145A63CB5F0B9D80" --vregion "China-North" --preserve-json-string

# LogID 查询 + PSM 过滤
bytedcli log get-logid-log "20260202085428C91A145A63CB5F0B9D80" --psm "psm.name" --vregion "China-North"

# LogID 查询 + 日志级别过滤（客户端过滤，无需 PSM）
bytedcli log get-logid-log "20260202085428C91A145A63CB5F0B9D80" --level Error,Warn --output console

# LogID 查询（显式 rolling：通过 PSM 日志搜索 + __logid KV 过滤滚动拉取并输出覆盖证明）
bytedcli log get-logid-log "20260202085428C91A145A63CB5F0B9D80" --psm "psm.name" --rolling --max-logs 0 --output console

# LogID 查询（全量 dump 快捷方式；需要提供 PSM）
bytedcli log get-logid-log "20260202085428C91A145A63CB5F0B9D80" --psm "psm.name" --dump --output file

# 接口总体性能分析（默认把完整结果落到本地文件）
bytedcli log analysis performance --psm "psm.name" --method "QueryFoo" --start "2026-02-02T08:00:00+08:00" --end "2026-02-02T09:00:00+08:00"

# 接口总体性能分析（默认 only-normal-trace=true；如需放宽可显式传 false）
bytedcli log analysis performance --psm "psm.name" --method "QueryFoo" --start "1776866375" --end "1776952775" --only-normal-trace false

# LogID 调用树（默认 region=China-North，默认 time_range_right_shift=600，并把完整结果落到本地文件）
bytedcli log trace-tree --log-id "sample-trace-logid-001"

# LogID 调用树（指定保存路径）
bytedcli log trace-tree --log-id "sample-trace-logid-001" --output-file "/tmp/trace-tree-demo.json"

# LogID 调用树（调整 trace 搜索窗口）
bytedcli log trace-tree --log-id "sample-trace-logid-001" --time-range-right-shift 900

# LogID 查询（BOE 的 boei18n 分区 US-BOE）
bytedcli --site boe log get-logid-log "20260417132015F8E8485573EF893978AE" --psm "demo.psm" --vregion "US-BOE" --output console

# LogID 查询（指定时间范围，RFC3339 或 epoch 秒；不传时服务端自动从 logid 推导）
bytedcli log get-logid-log "20260202085428C91A145A63CB5F0B9D80" --vregion "EU-Compliance2" --start "2026-06-12T05:31:02" --end "2026-06-12T05:41:02"

# LogID 查询（国际化，新加坡区域）
BYTEDCLI_CLOUD_SITE=i18n-bd bytedcli log get-logid-log "20260202085428C91A145A63CB5F0B9D80" --psm "psm.name" --vregion "Singapore-Central"

# LogID 查询（EU TTP 区域，支持 EU-Compliance2/EU-Compliance/EU-TTP/EU-TTP2/US-EastRed）
bytedcli --site eu-ttp log get-logid-log "20260202085428C91A145A63CB5F0B9D80" --vregion "EU-Compliance2"

# LogID 查询（直接输出到控制台）
bytedcli log get-logid-log "20260202085428C91A145A63CB5F0B9D80" --psm "psm.name" --vregion "China-North" --output console

# LogID 查询（指定输出文件）
bytedcli log get-logid-log "20260202085428C91A145A63CB5F0B9D80" --psm "psm.name" --vregion "China-North" --output file --output-file "/tmp/bytedcli.logid.log"

# 泳道实例日志
bytedcli log get-lane-instance-log "psm.name" --env "ppe_xxx" --start "2026-02-02T08:00:00"

# 生产实例日志（按 Pod）
bytedcli log search-prod-instance-log --psm "psm.name" --env prod --region "China-North" --range 1h --keyword "error"

# 生产实例日志（直接输出到控制台）
bytedcli log search-prod-instance-log --psm "psm.name" --env prod --region "China-North" --range 1h --keyword "error" --output console

# 生产实例日志（指定输出文件）
bytedcli log search-prod-instance-log --psm "psm.name" --env prod --region "China-North" --range 1h --keyword "error" --output file --output-file "/tmp/bytedcli.prod.instance.log"

# 日志聚类
bytedcli log get-log-cluster "psm.name" --start "2026-02-02T08:00:00"

# 日志聚类（按 KV 过滤，如日志级别）
bytedcli log get-log-cluster "psm.name" --start "2026-02-02T08:00:00" --kv-filter "level=ERROR|WARN"
```

## Notes

- `--start/--end` 支持 RFC3339 或时间戳（秒/毫秒），不传则默认近 1 小时
- `--start/--end` 的 RFC3339 形式支持显式时区偏移（如 `2026-04-16T21:08:48-07:00`、`2026-04-16T21:08:48+08:00`、`2026-04-16T21:08:48Z`）；不带偏移时按运行机器的本地时区解析，跨机器/跨时区场景建议显式带偏移避免歧义
- `--range` 和 `--start -1h` 相对语法仅 `search-prod-instance-log` 支持
- 日志查询时间范围上限为 7 天（`end - start <= 7d`），超出会报错
- `search-psm-log`、`get-logid-log` rolling 模式（显式 `--rolling` 或 `--dump`）、`search-prod-instance-log`、`get-lane-instance-log` 在查询窗口超过 6h 时，会自动拆成多个不超过 6h 的时间片并串行请求；JSON 输出会额外返回 `query_slices`，`retrieval_coverage` 中也会标记 `sliced/time_slices`
- 当 `search-psm-log`、`search-prod-instance-log`、`get-lane-instance-log` 的查询窗口超过 6h 且没有显式过滤条件时，CLI 会直接拒绝，避免长时间范围空查询
- `--keyword/--exclude` 支持重复或逗号分隔
- `search-psm-log` 可用 `--keyword-operator <AND|OR>` 控制多个 `--keyword`/`--term` 的组合方式：`AND`（默认）要求同一条日志命中全部关键词，`OR` 命中任意关键词即返回；JSON 输出会回显 `keyword_operator`
- `search-psm-log` 可用 `--exclude-operator <AND|OR>` 控制多个 `--exclude` 的组合方式：`AND`（默认，兼容历史行为）要求同一条日志命中全部排除词才过滤，`OR` 命中任意排除词即过滤；JSON 输出会回显 `exclude_operator`
- `search-psm-log` 可用 `--enable-index` 开启索引加速查询（`enable_index=true`），适用于 PSM 关键词搜索
- `search-psm-log` 可用 `--term` 开启短语查询（`is_term=true`，不分词）；legacy 模式下配合 `--enable-index`，新模式下配合 `--index-mode auto` 或 `--index-mode on`，不能与 `--index-mode off` 同时使用
- `search-psm-log` 开启 `--enable-index` 时会提示二次确认 PSM 是否已开索引，并给出索引说明文档：`https://bytedance.larkoffice.com/docx/K1lHdQppSo0d1HxkAMscn1Wfnff`；非交互场景可加 `--yes` 跳过确认
- `--index-mode auto` 仅在首轮索引请求返回索引专属错误时安全降级；`on`、显式 `--term`、鉴权/权限/网络错误会原样返回，不做静默降级
- 显式模式首轮沿用 `--limit`，后续索引页请求 1000 条、非索引页请求 200 条；后端按调用方每页传入的 limit 执行，不会自行改写
- 显式模式响应缺少服务端最终 `enable_index` 时，说明可能命中不支持该契约的旧实例；应从首轮重试，不要继续复用 cursor
- `search-psm-log` 默认 `--max-logs 1000`；JSON 输出会包含 `retrieval_coverage`（含 `verdict`、`pagination_proof`、`rounds`）证明本次拉取覆盖程度
- `search-psm-log` 支持 `--max-logs N` 显式限制收集条数；需要全量滚动到后端 `finished=true` 或 `--poll-timeout` 时，显式传 `--max-logs 0`
- `search-psm-log` 支持 `--level <level>` 日志级别过滤（可重复或逗号分隔），常用快捷方式：`--error-warn` 等价于 `--level Error --level Warn`，`--error-only` 等价于 `--level Error`
- `get-logid-log` 默认走 `log.logid_prune` MCP tool 精确查询（SDK 可用时），无需 PSM 和时间参数，服务端自动从 logid 推导时间窗口。提供 `--psm` 时会作为 `psm_list` 过滤传给服务端。若日志中的 object/array JSON 文本必须保持 string，可显式加 `--preserve-json-string`；该参数默认关闭，只作用于默认 `logid_prune` 模式。显式传 `--rolling`/`--dump` 时切换到 rolling 模式（需要 PSM）
- `get-logid-log` 的权限是链路级自动授权：logid 链路中存在有权限的 PSM 时，整条链路（含无单独权限的 PSM）日志均可返回；`--psm` 可重复或逗号分隔传多个，查询时需确保传入的 PSM 中至少包含 1 个查询者有权限的 PSM
- `get-logid-log` 支持 `--level <level>`（可重复或逗号分隔）按日志级别过滤，快捷方式同 `search-psm-log`：`--error-warn`、`--error-only`；SDK 路径下为客户端过滤（先查全量再按 level 筛选），rolling 模式下为服务端过滤
- `get-logid-log` rolling 文本导出默认透出全部字段；支持 `--fields` 指定字段导出（可重复或逗号分隔），仅影响 `--output console/file` 的文本内容，JSON 输出保持完整 payload
- `get-logid-log --dump` 是全量 rolling dump 快捷方式，等价于 `--rolling --max-logs 0`，需要同时提供 `--psm`
- `search-psm-log` 和 `get-log-cluster` 支持 `--kv-filter key=value1|value2`，可重复传递多个过滤条件
- `--idc` 在 `search-psm-log` 中会自动映射为 `_idc` 过滤
- `get-log-cluster` 使用 `--kv-filter` 可按日志级别等字段过滤聚类结果，例如 `--kv-filter "level=ERROR|WARN"`
- **多区域 LogID 查询**：`get-logid-log` 默认 `logid_prune` 模式支持 `--vregion 'China-North|China-North6'`，可同时带 `--psm example.service` 过滤。整个区域值必须加引号，避免 `|` 被 shell 当成管道；不要用逗号或重复 `--vregion`，重复选项只保留最后一个值。
- 上述多区域写法依赖默认 SDK 路径（未通过 `ARGOS_SDK=0` 等配置关闭），不适用于 `--rolling` / `--dump` 或旧 HTTP 路径。`search-psm-log`、`search-log-matchers`、`get-log-cluster` 等命令没有相同的多区域约定，需要多区域结果时按区域分别执行。区域应属于所选 `--site` 的控制面；跨站点查询分别指定对应 `--site` 和区域。
- `search-psm-log` / `get-logid-log` 使用 `--vregion`，`search-prod-instance-log` / `get-lane-instance-log` 使用 `--region`；在 `i18n-tt` 站点时，`search-psm-log` / `get-logid-log` 不提供 `--vregion` 的话默认使用 `Singapore-Central`
- `log analysis performance` 使用 `--metrics-region`，默认 `cn`；它表示分析接口所使用的指标区域，不是 logservice 的 `--vregion`。
- `trace-tree` 使用 `--region`（BytedTrace region），`cn` 站点支持 `China-North`、`China-North6`、`China-East`，默认仍为 `China-North`；`i18n-bd` 支持 `Asia-SouthEastBD`；它不是 logservice 的 `--vregion`
- `log analysis performance` 默认把完整分析 JSON 保存到本地临时文件；可用 `--output-file` 指定路径；stdout 固定返回 summary preview，不支持 stdout JSON
- `log analysis performance` 默认使用 `--only-normal-trace true`；如需分析不完整链路，显式传 `--only-normal-trace false`
- 如果 agent 需要理解 `log analysis performance` 完整结果的字段语义，先看 `references/log.md` 里的“完整结果 JSON 关键字段语义”，不要只靠字段名猜测 `cost_in_us`、`called_percentage`、`analysis_span_histogram` 等含义
- `trace-tree` 默认把完整 trace JSON 保存到本地临时文件；可用 `--output-file` 指定路径；stdout 固定返回 summary preview，不支持 stdout JSON
- `trace-tree` 遇到 `others` / merge span 聚合导致下游挂载不稳定时，可能补充 `[raw]` 预览子节点；更精确的 parent-child 关系以保存下来的完整 payload 为准
- `--vregion` 默认值按站点不同：`cn` 为 `China-North`，`boe` 为 `China-BOE`，`i18n`/`i18n-bd` 为 `Singapore-SaaS`，`i18n-tt` 为 `Singapore-Central`，`us-ttp`/`us-ttp-bdee`/`us-ttp-usts` 为 `US-TTP`。Logservice HTTP host 按 `(site, vregion)` 显式映射；表中未命中时使用当前 site 默认 host，无论是否显式传入 vregion。常见 vregion 值：`China-North`、`Singapore-SaaS`、`Singapore-Central`、`US-East`、`US-EastBD`、`US-TTP3`、`US-TTP`、`US-TTP2`、`China-BOE`、`US-BOE`、`EU-Compliance2`、`EU-Compliance`、`EU-TTP`、`EU-TTP2`、`US-EastRed`
- **Breaking change**：`--site i18n-bd --vregion China-*` 不再按 vregion 模糊匹配 China endpoint，而是回退到 `logservice-mya.sinf.net`；`--site i18n --vregion China-*` 则回退到 `logservice-sg.tiktok-row.org`。`China-North`、`China-North6`、`China-East`、`China-Pay` 等路由改用 `--site cn`；`China-BOE`、`China-BOE2` 改用 `--site boe`。
- `--site i18n-bd --vregion US-EastBD` 会路由到 US-EastBD 专用 logservice（`logservice-us-eastbd.byted.org`），JWT 继续使用 `i18n-bd` 站点凭证，BCGW vregion/header 与请求体保留用户传入的 vregion。
- `--site i18n-bd --vregion US-TTP3` 会路由到 `logservice-useast15a.lark-us.org`；大小写不影响 host 匹配，请求 header/body 仍保留用户传入的原始 vregion。
- `--site us-ttp` / `--site us-ttp-bdee` 的 `US-TTP`、`US-TTP2` 分别路由到 limited 域名 `logservice-tx.tiktok-us.org`、`logservice-tx2.tiktok-us.org`，JWT 获取走 `cloud-ttp-us.bytedance.net`。
- `--site us-ttp-usts` 的 `US-TTP`、`US-TTP2` 分别路由到 `logservice-tx.tiktok-usts.org`、`logservice-useast8.tiktok-usts.org`，不要与 limited 域名混用。
- `--vregion US-BOE`（BOE 的 boei18n 分区）会路由到 `logservice-boei18n.byted.org`，JWT 从 `cloud.bytedance.net`（bytedance SSO）获取，与 China-BOE 的 `logservice-boe.byted.org` + `cloud-boe.bytedance.net` 不同。使用方式：`bytedcli --site boe log search-psm-log --psm demo.psm --vregion US-BOE ...`（传错 China-BOE 分区会报 `vregion ... is not in the same site/partition`，error_code=101400）
- `--vregion` 支持 EU TTP 域的 5 个区域：`EU-Compliance2`、`EU-Compliance`、`EU-TTP`、`EU-TTP2`、`US-EastRed`。使用 `--site eu-ttp` 或 `--site i18n-tt` 时，这些 vregion 会自动路由到 `tiktok-eu.org` 域的专用 logservice，JWT 使用 i18n-tt 站点凭证
- 切换 i18n 站点时建议显式使用 `--site i18n-bd` 或 `--site i18n-tt`。认证隔离按 SSO 环境生效：`i18n-tt`、`eu-ttp` 与 `cn`/`i18n`/`i18n-bd` 隔离，使用前需先确认对应站点已登录（如 `BYTEDCLI_CLOUD_SITE=i18n-tt ... auth status`），否则可能报 `获取字节云 JWT 失败: 401`，详见 `../../troubleshooting.md`
- **建议在 `i18n-tt` 站点查询实例日志时显式指定 `--region`**：`search-prod-instance-log` 和 `get-lane-instance-log` 在 `--site i18n-tt` 时，不提供 `--region` 的话默认使用 `Singapore-Central`。如需查询其他区域的日志，建议显式传入 `--region`，例如 `--region "Singapore-Central"`、`--region "US-East"`等。常见的 i18n-tt 站点 region 值包括：`Singapore-Central`、`US-East` 等。
- `search-psm-log` / `get-logid-log` / `get-log-cluster` 等命令需要结构化输出时可加 `--json`（全局选项，放在子命令之前，如 `bytedcli --json log search-psm-log ...`）；`log analysis performance` 与 `trace-tree` 不支持 stdout JSON
- `search-psm-log` / `search-prod-instance-log` / `get-logid-log` 默认 `--output file`，会在控制台打印输出文件路径；可用 `--output console` 直接打印日志
- `search-psm-log` 文本导出默认透出全部字段；支持 `--fields` 指定字段导出（可重复或逗号分隔）
- `trace-tree` 默认直接输出文本树，不支持 `--output file|console` 切换；文本模式仍会打印保存下来的结果文件路径
- CLI 格式化文本可能按 UTC+8 展示；`--json` 中的原始时间戳和时间字符串保留日志源值，不保证统一转换为 UTC+8。分析和汇报时保留原始值并显式标注时区，不要把 `Z`/UTC 无条件解释为 UTC+8。
- **沙箱环境优先使用 `--output file`**：在沙箱环境（如 Trae IDE）中，`--output console` 可能因输出缓冲或权限限制导致结果不显示，建议使用默认的 `--output file`。
-

## Footprint (TCE Sync + URL Download)

`log footprint get` 封装 `footprint.tiktok-row.net` 的 TCE Sync 日志查看 API，直接在指定 TCE pod 的容器内本地文件系统上按 `--mode` 选择 `tail` / `head` / `ls` / `grep`。

`log footprint download` 封装 Footprint 的日志 URL 下载模型，输入独立 Footprint 页面 URL 或已经解析出的 Footprint-backed concrete 文件 URL，解析出最终 `applicationId` 后调用 `search-log` 与 `download-log` 下载内容。它适合用户已经持有 Footprint URL，以及长 pod 名导致 TCE Sync 报 `search keyword is too long` 的场景。

它们与上面的 `log search` / `log get-logid-log` / `log trace-tree` 等命令查的是不同来源：BytedLog 查询的是已采集日志库；Footprint TCE Sync 查 pod 文件系统；Footprint URL 下载查页面内嵌或直接给出的 concrete 文件。

不要把 Footprint 页面或 concrete URL 传给 `log footprint get --file`；`get --file` 只接 pod 内文件名，例如 `app.log`。URL 型输入使用 `log footprint download --url <url>`；landing page 不是 concrete 文件时，不要把它当作已可下载的日志正文。

### 什么时候用 Footprint

- 想看某个具体 pod 当下还在写的最新日志、还没被采集滚动归档的内容 → 用 `log footprint get --mode tail` / `--mode grep`
- 已知 logid / trace_id、想跨 pod 查已采集字段 → 还是用前文的 `log search` / `log get-logid-log`
- 想看 pod 上 `/var/log/tiger` 目录下有哪些文件、各自多大 → `log footprint get --mode ls`
- 用户直接给出独立 Footprint 页面或 Footprint-backed concrete 文件直链 → 用 `log footprint download --url <url>`

### 支持的 region

| `--region` 取值          | 页面 idc | backend 字段 `idc` |
| ------------------------ | -------- | ------------------ |
| `us-ttp`（别名 `ttp`）   | US-TTP   | `ttp`              |
| `us-ttp2`（别名 `ttp2`） | US-TTP2  | `ttp2`             |

CLI 暴露 `--region`（对齐仓库标准 flag），内部映射成 Footprint 后端的 `idc` 字段。其它机房暂未接入。

`log footprint download` 使用 `--region`（可省略，优先从 URL 推断），支持 `US-TTP` / `ttp` / `usttp` → `ttp`，`US-TTP2` → `ttp2`，`EU-TTP` / `euttp` → `eu_ttp_no1a`，`EU-TTP-GCP` / `euttp-gcp` → `eu_ttp_gcp`，`EU-TTP-USEAST2A` → `eu_ttp_useast2a`，`EU-TTP-USEAST2B` → `eu_ttp_useast2b`。

### Usage

```bash
# tail：默认 --lines 2000、--path /var/log/tiger
bytedcli log footprint get --mode tail --region us-ttp --psm example.service.rank --pod dp-xxx --file app.log

# head：默认 --lines 200
bytedcli log footprint get --mode head --region us-ttp --psm example.service.rank --pod dp-xxx --file app.log --lines 200

# ls：默认 --args "-alh"，--mode ls 不接受 --file
bytedcli log footprint get --mode ls --region us-ttp2 --psm example.data.gpu --pod dp-yyy

# grep：必填 --pattern，--lines 控制结果尾部裁剪行数（默认 1000）
bytedcli log footprint get --mode grep --region us-ttp --psm example.service.rank --pod dp-xxx --file app.log --pattern ERROR --lines 1000

# grep：递归搜索目录（--file .）、使用扩展正则，重复 --pattern 做 OR 匹配，并通过受限 head 管道先截取前 20 行
bytedcli log footprint get --mode grep --region us-ttp --psm example.service.rank --pod dp-xxx --file . -r -i -n -E --pattern ERROR --pattern FATAL --head-lines 20 --lines 500

# Agent 调用统一加 --json
bytedcli --json log footprint get --mode tail --region us-ttp --psm example.service.rank --pod dp-xxx --file app.log

# 日志 URL 型下载：独立 Footprint 页面或已经解析的 Footprint-backed concrete 直链
bytedcli log footprint download --url 'https://footprint.example/?applicationId=https%3A%2F%2Fmljob-log-us-proxy.example%2Fyodel-logs%2Fproxy%2Fdemo%2Frunner.log&idc=US-TTP'
bytedcli log footprint download --url 'https://mljob-log-ttp-proxy.example/yodel-logs/proxy/demo/dataio.log.INFO' --start '0-200000' --output ./dataio-front.log
bytedcli log footprint download --url 'https://mljob-log-eu-proxy.example/yodel-logs/proxy/demo/runner.log' --region EU-TTP-GCP --start '100-200' --output ./demo-runner.log
bytedcli --json log footprint download --url 'https://mljob-log-ttp-proxy.example/yodel-logs/proxy/demo/runner.log' --start '-200'
```

### Footprint Agent Guidance

- 用户直接给出 `footprint.tiktok-row.net` 页面或已经解析的 Footprint-backed concrete 文件直链时，使用 `bytedcli log footprint ...`；当前 CLI 入口不是顶层 `bytedcli footprint`。如果 URL 只是 landing page，没有具体 `.log` / `.out` / `.err` / `.txt` 文件，不要把它当作 concrete 文件下载。
- `--mode` 必填，取值仅 `tail` / `head` / `ls` / `grep`，1:1 映射后端 `tce_search_mode`。
- 默认日志路径 `/var/log/tiger`，绝大多数 TCE pod 都用这个；除非用户明确给了 `--path`，否则不要自己改。
- `--mode tail` / `head` / `grep` 必填 `--file`；`--mode ls` 不接受 `--file`（要看具体文件请改用 tail/head）。
- `--file` 只接 pod-local 文件名；如果用户手上是 Footprint 页面或 concrete URL，不要拆成 `get --mode tail/grep`，使用 `log footprint download --url <url>`。
- `--mode grep` 必填 `--pattern`；CLI 会自动补 `| tail -n <--lines>`，用户不要自己拼，想控制条数改 `--lines` 即可。
- grep 模式支持 `-r/--recursive`、`-i/--ignore-case`、`-n/--line-number`、`-E/--extended-regexp`。`--file .` 可用于递归搜索当前日志目录；`--head-lines N` 会在必需的 tail cap 前加入受限的 `| head -n N` 管道。不要把任意 shell 管道塞进 `--pattern`。
- Footprint 会在尊重 shell 引号之前按**每一个** `|` 拆分 `tce_search_cmd`，因此 `--pattern 'ERROR|FATAL'` 不能可靠表达 ERE alternation。CLI 会拒绝 pattern 内的 `|`；用 `--pattern ERROR --pattern FATAL`，生成 `grep -e 'ERROR' -e 'FATAL' ...`。这已在真实 TCE pod 上验证。
- 每个 `--pattern` 都会被单引号包裹为一个 `grep -e '<pattern>'`。CLI 还拒绝会破坏该包裹的 `'`、`\`、`\n`、`\r`；空格、`<`、`>`、`$`、括号、regex anchor 等仍原样传给 grep。
- Footprint 后端对所有 mode 的行数都有 2000 上限：`tail -n`/`head -n` 服务端会报 `tail: limit exceeded (max 2000)` / `head: limit exceeded (max 2000)`；CLI 在 tail、head、grep 上都把 `--lines` 上限统一卡在 2000（超过直接抛 `FOOTPRINT_INPUT_ERROR` 不发请求），需要更多日志请分多次串行查询。
- 文本输出按 `currentLine` 顺序逐行打印 `matched_pattern`；JSON 输出额外带 `mode`、`region`、`unique_search_id`、`status`、`line_count` 等元信息字段。
- `log footprint download` 支持从 Footprint query 的 `applicationId` / `logUrl` / `originUrl` / `url` 提取 concrete 文件 URL。若 URL query 里 `file` 双重 encode 了 `&pod_name=...&start=...`，CLI 会修复成最终下载 query。
- `log footprint download --start` 支持 `0`、`100-`、`100-200`、`-200`，并写入最终 resolved mljob-log-proxy URL query；命令行 `--start` 会覆盖 URL 里已有的 `start`。较大的范围（例如 `0-200000`）会自动按后端可接受的窗口分片下载再拼接，不要手工改成只看 `-4096` 尾部。
- `log footprint download --json` 成功输出包含 `input_url`、`resolved_url`、`source`、`idc`、`start`、`byte_count`、`empty_content`；未指定 `--output` 时包含 `content`（大内容会截断并带 `content_truncated`），指定 `--output` 时包含 `output_file` 且不输出日志正文；不会输出 cookie/JWT/token。
- 部分 concrete 文件能被 Footprint 索引出来，但 `download-log` 返回空 `fileContent`；这时 JSON 里会有 `empty_content: true` 和 `empty_content_hint`。不要反复用同一空链接重试；如果用户提供了多个 concrete 文件，优先尝试较小的文本日志。
- 鉴权失败常见原因：当前账号没有 Footprint 访问权限，或某一侧 SSO session 过期。Footprint 横跨两套 SSO realm（`sso.tiktok-intl.com` + `sso.bytedance.com`），CLI 首次调用会驱动 i18n / tx 两条 cloud-X JWT 链和 footprint 自身的 `/api/login` CAS 回跳链来补齐 `bd_sso_3b6da9` + `titan_passport_id` + `api_sid` cookie。两个 jar 都必须有：报错时先让用户跑 `bytedcli auth status`；缺哪侧就补哪侧：tiktok 侧 `bytedcli --site i18n-tt auth login --session`，bytedance 侧 `bytedcli auth login --session`，再重试命令。

## Footprint Search (`log footprint search`)

除了上面 `log footprint get` / `log footprint download`，`log footprint search` 是 **官方维护的命令**，封装 Footprint 的开放 API `POST /v1/open/bytedcli/viewlog`，用于按 `log_id` / trace / `psm`+时间窗拉取受支持的 log type。它与另外两个子命令是不同机制：

- `log footprint get` → TCE Sync，读 pod 本地文件。
- `log footprint download` → 下载 concrete 日志文件 URL。
- `log footprint search` → 通过 viewlog 开放 API，按 log type 拉日志。

ByteCloud JWT 由命令自动解析（优先级：`--jwt` > `FOOTPRINT_JWT` 环境变量 > 自动获取 i18n-tt 站点 ByteCloud JWT），JWT 只在内存中用于 `x-Footprint-JWT` 请求头，不会打印或写入输出。请优先用该命令，而不是手写 `curl` / Python。

**仅支持官方 log-type enum 中的类型**（含 `argos`、`argos_keyword`、`dorado`、`rpc`、`ftf`/`ftf2`、`tce`、`primus`、`slardar`、`clickhouse`、`physical`、`yarn`、`hdfs` 等）；未列出的类型会在发请求前被拒绝。

### Usage

```bash
# argos：按 log_id + 时间窗
bytedcli log footprint search --log-type argos --log-id 20260609221616XXXXXXXXXXXXXXXXXXXX --region ttp --start 1781042400 --end 1781044200

# dorado：按 job log_id，从 office / 笔记本网络访问
bytedcli log footprint search --log-type dorado --log-id demo-job-001 --network office

# argos_keyword：关键词搜索（Agent 调用统一加 --json）
bytedcli --json log footprint search --log-type argos_keyword --keyword timeout --start 1781042400 --end 1781044200

# 其它 log-type-specific 字段用可重复的 --field key=value 透传
bytedcli log footprint search --log-type ftf2 --log-id demo-case --field response_index=0 --field response_slice_mode=1

# 把结果写入本地文件
bytedcli log footprint search --log-type argos --log-id demo --region ttp --output ./argos.log
```

### Search Agent Guidance

- `--log-type` 必填，且必须是官方支持类型；不支持的类型 CLI 会以 `FOOTPRINT_INPUT_ERROR` 拒绝，不要绕过。
- `--region` 默认 `ttp`，支持 `ttp` / `ttp2` / `ttp_usswdt` / `ttp_uswest6` / `eu_ttp_gcp` / `eu_ttp_ie` / `eu_ttp_de` / `eu_ttp_ie2` / `eu_ttp_iedt` / `eu_ttp_no1a` / `eu_ttp_useast2a` / `eu_ttp_useast2b`（映射到后端 `idc` 字段）。
- `--network` 默认 `server`（on-cluster / IDE / prod-network）；从笔记本或办公网访问用 `--network office`。遇到 `403 [Segregator]` 就在 server/office 之间切换重试。
- `--unique-search-id` 默认生成确定性的 `FP_BYTEDCLI_<sha1>`，保证重试命中同一 bytedoc bucket；只有需要复用他人的 search id 时才显式传。
- `--field key=value` 只能补充 log-type-specific 字段，不能覆盖 `log_type` / `idc` / `log_id` / `psm` / `start_time` / `end_time` / `keyword` / `unique_search_id` 这些保留字段（用对应的专用 flag 传）；否则会以 `FOOTPRINT_INPUT_ERROR` 拒绝。
- `--start` / `--end` 是 Unix epoch 秒；时间窗要覆盖 `log_id` 内嵌时间戳，否则 `data` 可能为空。异步 log type 未拉全时（`completed: false`）可加 `--poll-timeout-seconds` 提高等待再重试（命令会同步放宽客户端 HTTP 超时到不小于该 poll 窗口）。
- `429 Too Many Requests` 是部门级限流；退避后再试，不要连续重试。
- 用户给的是 TCE pod 文件、独立 Footprint 页面，或没有 Primus application/History/role/pod/Forge-Reckon 上下文的独立 TTP/EU-TTP concrete mljob URL → 用 `log footprint get` / `log footprint download`。
- 用户给的是 Primus `redirect_log.html`、Primus executor 日志，或带 application/History/role/pod/Forge-Reckon Primus 上下文的 mljob URL → 始终使用 `bytedcli primus log list/get`；不要把 Primus 已发现的 concrete URL 再交给 Log skill。CN/ROW Primus/mljob 上下文同样走 `bytedcli primus ...`。

原始 API 细节（认证链路、host 选择说明、请求字段、polling override、响应结构、完整 enums、排错）见 `references/footprint-viewlog.md`；日常使用请优先用 `log footprint search` 命令。

## References

- `references/log.md`
- `references/footprint-viewlog.md` — Footprint `viewlog` 开放 API 原始细节（认证 / 请求 / 响应 / enums / 排错）；日常使用优先用 `log footprint search` 命令
