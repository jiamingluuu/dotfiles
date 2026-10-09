# Log

```bash
# PSM 日志搜索
bytedcli log search-psm-log --psm "psm.name" --start "2026-02-02T08:00:00" --end "2026-02-02T09:00:00"

# PSM 日志搜索（默认写入临时文件，并在控制台打印文件路径）
bytedcli log search-psm-log --psm "psm.name" --start "2026-02-02T08:00:00" --end "2026-02-02T09:00:00" --output file

# PSM 日志搜索（直接输出到控制台）
bytedcli log search-psm-log --psm "psm.name" --start "2026-02-02T08:00:00" --end "2026-02-02T09:00:00" --output console

# PSM 日志搜索（指定输出文件）
bytedcli log search-psm-log --psm "psm.name" --start "2026-02-02T08:00:00" --end "2026-02-02T09:00:00" --output file --output-file "/tmp/bytedcli.search.log"

# PSM 日志搜索（按字段导出，适合只保留 logid/podname 等关键字段）
bytedcli log search-psm-log --psm "psm.name" --start "2026-02-02T08:00:00" --end "2026-02-02T09:00:00" --fields "logid,podname,_idc"

# PSM 日志搜索（按 KV 过滤）
bytedcli log search-psm-log --psm "example.service.api" --keyword "deploy" --kv-filter "method=Deploy|Rollback" --kv-filter "_idc=lf|hl"

# PSM 日志搜索（多关键词按 OR 组合：命中任意关键词即返回，默认 AND；JSON 回显 keyword_operator）
bytedcli log search-psm-log --psm "example.service.api" --keyword "GetFoo" --keyword "GetBar" --keyword-operator OR --max-logs 200 --output console

# PSM 日志搜索（多排除词按 OR 组合：命中任意排除词即过滤，默认 AND；JSON 回显 exclude_operator）
bytedcli log search-psm-log --psm "example.service.api" --keyword "error" --exclude "known timeout" --exclude "known quota" --exclude-operator OR --max-logs 200 --output console

# PSM 日志搜索（超过 6h 会自动按 6h 串行分片）
bytedcli log search-psm-log --psm "example.service.api" --start "2026-02-02T00:00:00" --end "2026-02-02T18:00:00" --keyword "timeout" --output console

# PSM 日志搜索（索引加速查询：enable_index=true）
bytedcli log search-psm-log --psm "psm.name" --start "2026-02-02T08:00:00" --end "2026-02-02T09:00:00" --keyword "error" --enable-index

# PSM 日志搜索（索引加速 + 短语查询：is_term=true，不分词）
bytedcli log search-psm-log --psm "psm.name" --start "2026-02-02T08:00:00" --end "2026-02-02T09:00:00" --term "User not found" --enable-index

# 非交互环境执行索引加速查询（跳过二次确认提示）
bytedcli log search-psm-log --psm "psm.name" --start "2026-02-02T08:00:00" --end "2026-02-02T09:00:00" --keyword "error" --enable-index --yes

# PSM 日志搜索（BOE 的 boei18n 分区 US-BOE）
bytedcli --site boe --json log search-psm-log --psm "demo.psm" --vregion "US-BOE" --start "2026-04-16T21:08:48-07:00" --end "2026-04-16T21:33:48-07:00" --keyword "demo-keyword" --output console

# LogID 查询（默认 logid_prune 模式，PSM 作为过滤条件）
bytedcli log get-logid-log "20260202085428C91A145A63CB5F0B9D80" --psm "psm.name" --vregion "China-North"

# 保留 object/array 形态的 JSON string（仅默认 logid_prune 模式）
bytedcli log get-logid-log "20260202085428C91A145A63CB5F0B9D80" --vregion "China-North" --preserve-json-string

# 多区域 LogID 查询（默认 logid_prune 模式，可选 PSM 过滤）
bytedcli --site cn log get-logid-log --logid sample-log-id --psm example.service --vregion 'China-North|China-North6' --output console

# LogID 查询 + 日志级别过滤（默认模式下客户端过滤，--level 可重复或逗号分隔；快捷方式 --error-warn / --error-only）
bytedcli log get-logid-log "20260202085428C91A145A63CB5F0B9D80" --psm "psm.name" --level Error,Warn --output console

# LogID 查询（rolling 文本输出按字段导出，适合只保留 logid/podname/level 等关键字段）
bytedcli log get-logid-log "20260202085428C91A145A63CB5F0B9D80" --psm "psm.name" --rolling --fields "logid,podname,level" --output console

# 接口总体性能分析（默认把完整结果落到本地文件）
bytedcli log analysis performance --psm "psm.name" --method "QueryFoo" --start "2026-02-02T08:00:00+08:00" --end "2026-02-02T09:00:00+08:00"

# 接口总体性能分析（默认 only-normal-trace=true；如需放宽可显式传 false）
bytedcli log analysis performance --psm "psm.name" --method "QueryFoo" --start "1776866375" --end "1776952775" --only-normal-trace false

# LogID 调用树（默认把完整 trace JSON 落到本地文件）
bytedcli log trace-tree --log-id "sample-trace-logid-001"

# LogID 调用树（指定保存路径）
bytedcli log trace-tree --log-id "sample-trace-logid-001" --output-file "/tmp/trace-tree-demo.json"

# LogID 调用树（调整 trace 搜索窗口）
bytedcli log trace-tree --log-id "sample-trace-logid-001" --time-range-right-shift 900

# LogID 查询（BOE 的 boei18n 分区 US-BOE）
bytedcli --site boe log get-logid-log "20260417132015F8E8485573EF893978AE" --psm "demo.psm" --vregion "US-BOE" --output console

# LogID 查询（指定时间范围，RFC3339 或 epoch 秒）
bytedcli log get-logid-log "20260202085428C91A145A63CB5F0B9D80" --vregion "EU-Compliance2" --start "2026-06-12T05:31:02" --end "2026-06-12T05:41:02"

# LogID 查询（TikTok ROW 新加坡区域）
bytedcli --site i18n-tt log get-logid-log "20260202085428C91A145A63CB5F0B9D80" --psm "psm.name" --vregion "Singapore-Central"

# LogID 查询（i18n-bd US-TTP3）
bytedcli --site i18n-bd log get-logid-log "20260202085428C91A145A63CB5F0B9D80" --psm "psm.name" --vregion "US-TTP3"

# LogID 查询（EU TTP 区域，支持 EU-Compliance2/EU-Compliance/EU-TTP/EU-TTP2/US-EastRed）
bytedcli --site eu-ttp log get-logid-log "20260202085428C91A145A63CB5F0B9D80" --vregion "EU-Compliance2"

# LogID 查询（默认写入临时文件，并在控制台打印文件路径）
bytedcli log get-logid-log "20260202085428C91A145A63CB5F0B9D80" --psm "psm.name" --vregion "China-North" --output file

# LogID 查询（直接输出到控制台）
bytedcli log get-logid-log "20260202085428C91A145A63CB5F0B9D80" --psm "psm.name" --vregion "China-North" --output console

# LogID 查询（指定输出文件）
bytedcli log get-logid-log "20260202085428C91A145A63CB5F0B9D80" --psm "psm.name" --vregion "China-North" --output file --output-file "/tmp/bytedcli.logid.log"

# 泳道实例日志
bytedcli log get-lane-instance-log "psm.name" --env "ppe_xxx" --start "2026-02-02T08:00:00"

# 泳道实例日志（自定义日志文件路径，--path 可重复或逗号分隔；省略时默认只查 app/${psm}.log）
# 传了 --path 会整体替换默认值，若仍要保留默认路径需显式一并列出：
bytedcli log get-lane-instance-log "psm.name" --env "ppe_xxx" --keyword "<logid>" --path 'app/${psm}.log' --path '/opt/tiger/log/app/psm.name_verbose.log'

# 生产实例日志
bytedcli log search-prod-instance-log --psm "psm.name" --env prod --region "China-North" --range 1h --keyword "error"

# 生产实例日志（默认写入临时文件，并在控制台打印文件路径）
bytedcli log search-prod-instance-log --psm "psm.name" --env prod --region "China-North" --range 1h --keyword "error" --output file

# 生产实例日志（直接输出到控制台）
bytedcli log search-prod-instance-log --psm "psm.name" --env prod --region "China-North" --range 1h --keyword "error" --output console

# 生产实例日志（指定输出文件）
bytedcli log search-prod-instance-log --psm "psm.name" --env prod --region "China-North" --range 1h --keyword "error" --output file --output-file "/tmp/bytedcli.prod.instance.log"

# 日志聚类
bytedcli log get-log-cluster "psm.name" --start "2026-02-02T08:00:00"

# 日志聚类（按 KV 过滤，如日志级别）
bytedcli log get-log-cluster "psm.name" --start "2026-02-02T08:00:00" --kv-filter "level=ERROR|WARN"
```

说明：

- **多区域 LogID 查询**：`get-logid-log` 默认 `logid_prune` 模式支持 `--vregion 'China-North|China-North6'`，可同时带 `--psm example.service` 过滤。整个区域值必须加引号，避免 `|` 被 shell 当成管道；不要用逗号或重复 `--vregion`，重复选项只保留最后一个值。
- 上述多区域写法依赖默认 SDK 路径（未通过 `ARGOS_SDK=0` 等配置关闭），不适用于 `--rolling` / `--dump` 或旧 HTTP 路径。`search-psm-log`、`search-log-matchers`、`get-log-cluster` 等命令没有相同的多区域约定，需要多区域结果时按区域分别执行。区域应属于所选 `--site` 的控制面；跨站点查询分别指定对应 `--site` 和区域。
- SDK 默认 `--index-mode legacy` 以兼容已有调用；需要按全部 PSM 的索引配置自动选择索引、TERM 和分页参数时显式传 `--index-mode auto`。`auto/on/off` 会忽略旧 `--enable-index`，不要同时传；HTTP fallback 保留原有 7d/6h、默认 CN IDC 与显式 `--enable-index` 行为。
- `auto` 仅在首轮索引请求返回索引专属错误时安全降级；`on`、显式 `--term`、鉴权/权限/网络错误会原样返回。
- 显式模式首轮沿用 `--limit`，后续索引页请求 1000 条、非索引页请求 200 条；后端按每页传入的 limit 执行。响应缺少最终 `enable_index` 时，应从首轮重试且不要复用 cursor。
- `search-psm-log`、`get-logid-log` rolling 模式（显式 `--rolling` / `--dump`，需要 PSM）、`search-prod-instance-log`、`get-lane-instance-log` 的时间窗口超过 6h 时，会自动拆成多个不超过 6h 的时间片并串行请求。
- 当 `search-psm-log`、`search-prod-instance-log`、`get-lane-instance-log` 的时间窗口超过 6h 且没有显式收窄条件（例如 `--keyword`、`--exclude`、`--kv-filter`、`--level`、`--idc`）时，CLI 会直接拒绝，避免长时间范围空查询。
- `search-psm-log` 可用 `--exclude-operator OR` 让多个 `--exclude` 任意命中即过滤；默认 `AND` 保持历史行为。
- `--site i18n-bd --vregion US-EastBD` 会路由到 `logservice-us-eastbd.byted.org`，用于查询 i18n-bd US-EastBD 区域日志。
- Logservice HTTP host 由 `(site, vregion)` 显式映射决定，vregion 大小写不影响匹配；表中未命中时使用当前 site 的默认 host，无论是否显式传入 vregion，不再动态拼接域名。
- **Breaking change**：`--site i18n-bd --vregion China-*` 不再按 vregion 模糊匹配 China endpoint，而是回退到 `logservice-mya.sinf.net`；`--site i18n --vregion China-*` 则回退到 `logservice-sg.tiktok-row.org`。`China-North`、`China-North6`、`China-East`、`China-Pay` 等路由改用 `--site cn`；`China-BOE`、`China-BOE2` 改用 `--site boe`。
- `--site i18n-bd --vregion US-TTP3` 会路由到 `logservice-useast15a.lark-us.org`。
- `--site us-ttp` / `--site us-ttp-bdee` 的 `US-TTP`、`US-TTP2` 使用 `tiktok-us.org` limited 域名；`--site us-ttp-usts` 使用对应的 `tiktok-usts.org` 域名。

## `log analysis performance` 完整结果 JSON 关键字段语义

- `report_base_info`：这次分析报表的基础信息，例如 `report_id`、`psm`、`method`、分析时间窗、分析到的 trace 数。
- `analysis_criteria`：请求条件快照；通常用来回看本次分析实际用了哪些过滤条件和默认值。
- `performance_tree`：聚合后的调用树；根节点通常就是目标接口本身。
- `analysis_span_histogram`：按耗时区间聚合的慢 span 分桶；这里的 `start_time_us` / `end_time_us` 表示**耗时桶边界**，不是事件发生时间。
- `performance_tree.log_ids`、各子节点上的 `log_ids`、以及 `analysis_span_histogram[].span_list[].log_id` 都只是接口返回的**样本线索**，不是 CLI 内置推荐结果。
- `cost_in_us`：当前聚合节点的耗时指标；排查时通常先按它看热点节点。
- `local_pure_cost_in_us`：节点本地纯耗时。
- `network_cost_in_us`：节点网络相关耗时。
- `called_percentage`：该聚合节点在分析样本中的调用占比；它不是固定含义的“错误率/成功率”。
- `span_list`：当前耗时桶中的样本 span，常带 `log_id`、`trace_id`、`duration_us`。
- CLI 会在 stdout footer 里打印保存路径；落盘文件本身不包含 额外路径字段。

## 使用约束

- CLI 只做确定性摘要，不做 AI 根因判断。
- CLI 不内置固定 logid 推荐策略。
- 需要继续深挖时，优先读取命令 footer 提示的完整 JSON 文件，再挑选 `log_id` 去跑 `bytedcli log trace-tree --log-id <id>`。
