---
name: bytedance-lidar
description: "Operate Lidar (字节服务性能平台) via bytedcli: start Golang / Python / Nodejs instant pprof sampling, inspect structured call stacks for one profiling_id, query peak-period service stats and scheduled sampling details, upload local sampling data, poll status, list or download sampling results, read or safely update conditional sampling and 动态特性配置, inspect or trigger Atum cloud access, list or open optimization features, and create, inspect, or list profit evaluations. Use when tasks mention Lidar, instant sampling, 即时采样, sampling stack, 调用栈, 堆栈详情, peak stats, 高峰期指标, pprof, heap profile, goroutine profile, Golang performance profiling, 上传采样数据, 判断 PSM 是否开启 Lidar 采样, 采样开关, SamplingConfig, 条件采样配置, 动态特性配置, Atum 云控接入, 优化特性, 灰度策略, or 收益评估. For C++/Java/jemalloc/off-CPU flamegraphs, use bytedance-bytedog instead."
---

# bytedcli Lidar

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

- 对 Golang / Python / Nodejs 服务发起即时 pprof 采样（heap / profile / goroutine / allocs / trace / ...）
- 查询 profiling_id 状态，获取火焰图 URL
- 上传本地采样数据并生成 profiling_id
- 列出最近 6h（默认）的采样历史
- 下载原始 pprof 采样数据到本地
- 判断单个 PSM 是否开启 Lidar 条件采样（agent 接入状态 + 6 条触发规则启用情况）
- 查看并安全修改单个 PSM 的条件采样与动态特性配置，包括全局默认值和集群/阶段 zone 覆盖
- 查询单日高峰期服务指标，并关联当天各 cluster 的定时采样 ID、类型与 VRegion
- 查询或触发 Atum 云控接入，并在已接入时查看全部已开启特性
- 查询 PSM 的全部可选优化特性及开启状态、推荐理由和操作限制
- 为 PSM 开启优化特性，并在需要时选择灰度策略
- 创建异步收益评估、查询任务详情或按 PSM 列出计算记录
- 对单次采样执行 AI 驱动的性能分析（提交异步任务、轮询状态、查看分析报告、导出到飞书文档）

## Do not use

- C++ / Java jemalloc / off-CPU 火焰图 → 使用 `bytedance-bytedog`
- 部门级总览或当前命令未覆盖的可视化看板 → 使用 Lidar Web 页面

## 前置条件

使用 `bytedcli auth login` 完成 SSO 登录后，CLI 会自动获取 ByteCloud JWT，Lidar 命令无需手动配置认证。

> 执行前缀见 `../../invocation.md`；下面示例直接写 `bytedcli`。

## Quick start

```bash
# 发起即时 heap 采样（瞬时类型，无需 --duration）
bytedcli lidar sampling create --psm demo.psm.lidar --type heap

# 发起 profile 采样（时长类型），并等待完成后输出结果（含火焰图 URL）
bytedcli lidar sampling create --psm demo.psm.lidar --type profile --duration 30 --wait

# 查询采样状态（含火焰图 URL 和下载 URL）
bytedcli lidar sampling get --id demo.psm.lidar_202604181600_abc

# 在 get 中查看按 profile 默认指标排序的调用栈（默认前 20 条，leaf → root）
bytedcli lidar sampling get --id demo.psm.lidar_202604181600_abc --stack
bytedcli --json lidar sampling get --id demo.psm.lidar_202604181600_abc --stack --profile-type heap --sample-type inuse_space --limit 50

# 列出最近 6h 的采样历史（默认）
bytedcli lidar sampling list --psm demo.psm.lidar

# 下载原始 pprof 采样数据到本地文件
bytedcli lidar sampling download --id demo.psm.lidar_202604181600_abc
bytedcli lidar sampling download --id demo.psm.lidar_202604181600_abc --output /tmp/heap.pb.gz

# 上传本地采样数据，成功后输出 profiling_id、火焰图 URL 和下载 URL
bytedcli lidar sampling upload --psm demo.psm.lidar --type profile --file ./profile.pb.gz

# 查询 PSM 的条件采样与动态特性配置
bytedcli lidar config get --psm demo.psm.lidar
bytedcli --json lidar config get --psm demo.psm.lidar

# partial update 默认只预览；确认 request 后追加 --yes
bytedcli --json lidar config set --psm demo.psm.lidar --config-json '{"rules":{"mem":{"value":84}}}'
bytedcli --json lidar config set --psm demo.psm.lidar --config-json '{"rules":{"mem":{"value":84}}}' --yes

# 查询某天高峰期服务指标和定时采样详情
bytedcli lidar peak stats --psm demo.psm.lidar --date 2026-08-05
bytedcli --json lidar peak stats --psm demo.psm.lidar --date 2026-08-05 --region China-North --cluster demo-cluster
bytedcli lidar sampling get --id demo.psm.lidar_202608050900_sample --peak
bytedcli lidar sampling get --id demo.psm.lidar_202608050900_sample --peak --stack

# 查询云控接入状态；已接入时同时返回全部已开启特性
bytedcli lidar opt stats --psm demo.psm.lidar

# 查询全部可选特性及详情，包括尚未开启的特性
bytedcli lidar opt list --psm demo.psm.lidar

# 写操作默认预览；确认后加 --yes
bytedcli --json lidar opt access --psm demo.psm.lidar
bytedcli --json lidar opt open --psm demo.psm.lidar \
  --feature demo-feature-a --feature demo-feature-b

# 创建收益评估时默认仅预览；确认后提交并按 task ID 查询
bytedcli lidar profit create --psm demo.psm.lidar --vregion China-North --new-begin-time 1785772800 --new-end-time 1785776400 --old-begin-time 1785686400 --old-end-time 1785690000
bytedcli lidar profit create --psm demo.psm.lidar --vregion China-North --new-begin-time 1785772800 --new-end-time 1785776400 --old-begin-time 1785686400 --old-end-time 1785690000 --yes
bytedcli lidar profit create --psm demo.psm.lidar --profit-times-json '{"China-North":{"new_begin_time":1785772800,"new_end_time":1785776400,"old_begin_time":1785686400,"old_end_time":1785690000},"China-East":{"new_begin_time":1785859200,"new_end_time":1785862800,"old_begin_time":1785772800,"old_end_time":1785776400}}'
bytedcli lidar profit create --psm demo.psm.lidar --profit-times-file ./profit-times.json --yes
bytedcli lidar profit get --task-id demo-task-id
bytedcli lidar profit get --task-id demo-task-id --peak
bytedcli lidar profit list --psm demo.psm.lidar
bytedcli lidar profit list --psm demo.psm.lidar --date 2026-07-22

# 提交 AI 分析任务
bytedcli lidar analysis analyze --profiling-id demo.psm.lidar_202604181600_abc
bytedcli lidar analysis analyze --profiling-id demo.psm.lidar_202604181600_abc --thinking --web-search
bytedcli lidar analysis analyze --profiling-id demo.psm.lidar_202604181600_abc --wait
bytedcli lidar analysis analyze --profiling-id demo.psm.lidar_202604181600_abc --language English

# 查询 AI 分析任务状态
bytedcli lidar analysis status --task-id <task-id>

# 获取 AI 分析结果（按 task-id）
bytedcli lidar analysis get --task-id <task-id>

# 查询 profiling 的最新分析记录（按 profiling-id）
bytedcli lidar analysis get --profiling-id demo.psm.lidar_202604181600_abc
bytedcli lidar analysis get --profiling-id demo.psm.lidar_202604181600_abc --history-task-id <task-id>

# 导出 AI 分析结果到飞书文档
bytedcli lidar analysis export-doc --profiling-id demo.psm.lidar_202604181600_abc

# i18n 站点（i18n / i18n-bd 在 Lidar 下统一走 i18n-tt）
bytedcli --site i18n-tt auth status
bytedcli --site i18n lidar peak stats --psm demo.psm.lidar --date 2026-08-05
bytedcli --site i18n-bd lidar sampling create --psm demo.psm.lidar --type heap

# BOE / US-TTP 站点
bytedcli --site boe lidar sampling get --id demo.psm.lidar_202604181600_abc --stack
bytedcli --site us-ttp lidar sampling get --id demo.psm.lidar_202604181600_abc --stack
```

## Notes

- `--type heap/goroutine/allocs/memstats/block/mutex/waitduration/dynconf` 等为瞬时类型，`--duration` 传 `-` 或省略
- `--type profile/trace/latency` 属于时长类型，需通过 `--duration` 传秒数（常用 30）
- Golang 服务需在 TCE 开启 pprof 端口，否则采样请求会失败
- `--wait` 会轮询直到采样完成或超时；超时后 profiling_id 仍有效，稍后用 `lidar sampling get --id <id>` 继续查询
- 采样有副作用，PUT 请求不自动重试；瞬时失败可手动重新发起
- 火焰图 URL 在命令输出末尾，直接粘贴到浏览器打开即可查看
- 普通 `sampling get` 与 `sampling create` 的输出包含 `download_url`，可直接在浏览器打开下载原始 pprof 数据；`sampling get --stack` 改为返回本次解析所用的 `source_url`
- `sampling get` 默认只查询即时采样状态。查询 `peak stats` 返回的定时采样 ID 时必须显式追加 `--peak`；CLI 会从 `<psm>_<YYYYMMDD...>_<suffix>` 格式的完整 ID 自动推导 PSM 和日期，并在 `peak stats` 使用的 service profilings map 中精确匹配。后端不提供通用的 schedule status 查询；仅当 Bytedog 的 `pod_cpu` / `pyspy` map 值是类型占位符时，CLI 才按 PSM、日期和采样类型读取 schedule history 并在本地匹配真实 ID。定时采样详情仅返回可确认的描述字段，未知状态、创建人和地域使用 `null`，文本模式显示 `-`；`flamegraph_url` 与 `download_url` 使用同一个 pprof 地址，前者不带 `download=true`；需要标准 pprof 调用栈时追加 `--stack`，CLI 会直接下载并解析
- agent 组合采样默认选择 `profile` 子结果；可用 `--profile-type heap|goroutine|...` 选择其他 pprof 子结果，再用 `--sample-type` 选择该 pprof 内的 metric
- `sampling get --stack` 的 frame 顺序固定为 leaf → root；默认返回前 20 条，`--limit` 范围为 1～500，JSON 中用 `truncated` 明确标记截断
- stack 读取在 CN、BOE、i18n-tt 经 ByteCloud 管控代理完成，在 US-TTP 经 Lidar 的直连 API/Data 域完成；默认单次超时 60 秒且不自动重试，可用 `--timeout-ms` 在 1～600000 毫秒内调整。pprof int64/uint64 值在 JSON 中使用十进制字符串，避免精度丢失
- `sampling download` 使用站点对应的数据域名：CN 为 `lidar.bytedance.net`，BOE 为 `lidar-boe-cn.bytedance.net`，i18n-tt 为 `lidar-i18n.tiktok-row.org`，US-TTP 为 `lidar-ttp.tiktok-row.org`
- Lidar domain 内 `--site i18n` 和 `--site i18n-bd` 都归一到 `i18n-tt`，包括管理 API、JWT、页面 URL 与下载 URL；运行前使用 `bytedcli --site i18n-tt auth login` 建立 TikTok SSO 登录态
- `--site boe` 使用 BOE 管理面和数据面；`--site us-ttp`、`us-ttp-bdee`、`us-ttp-usts` 在 Lidar 内统一使用 US-TTP 管理面、认证与数据面
- `sampling upload` 会把本地采样文件上传为已完成记录；creator 由后端根据当前登录 JWT 识别，可用 `--pod-name` 记录实例，用 `--uname` 指定 MLC profile 文件名
- `--begin` / `--end` 支持 `YYYY-MM-DD`、`YYYY-MM-DD HH:mm`（按本机时区解析）或 unix 秒字符串
- `peak stats` 的 Details 行按 `cpu_usage` 降序排列，缺失 CPU Usage 的行在最后；`peak_samplings` 包含 `profiling_id`、`sampling_type` 与 VRegion
- `config get` 的文本输出会分别展示条件采样和动态特性配置的全局默认值与 zone 覆盖；JSON 顶层包含 `rules`、`runtime_strategy`、`runtime_strategy_zones`，并保留 `raw`
- `config set` 是非破坏性 partial update：shortcut 只支持六类固定条件采样规则；动态特性配置、删除 sampling type 或创建新 zone 必须通过 `--config` / `--config-json`
- `--config <file>`、`--config-json '<json>'`、`--rule` shortcut 三种输入模式严格互斥；inline JSON 建议使用 shell 单引号包裹
- shortcut 的 `--threshold` / `--bottleneck` 支持非负有限小数；`--sampling-duration` 只支持非负整数秒
- `monitoring_period`、`ping_period` 的 patch 路径是 `rules_extra`，不能放在 `rules`；未显式修改时 CLI 会从当前配置自动补入实际 request
- Lidar 后端会隐藏关闭规则的主 `profilings`；修改这类规则时若未显式提供 `profilings`，CLI 会阻断写入，避免用空数组覆盖未知存量
- `config get` 的 `source` 若不是 `rules defined by:`，说明当前为继承或默认配置；`config set` 会阻断，需先在 Lidar Web 建立直接配置
- `opt access` 默认只返回英文 `--yes` 确认提示和 request，加 `--yes` 后只返回最终接入状态；`opt stats` 在云控已接入时同时返回全部 `is_open=true` 特性
- `opt access --yes` 只触发异步接入任务，后端不会后台轮询任务状态；后续执行 `opt stats --psm <psm>` 才会触发状态刷新。由于接口先返回当前状态再执行刷新，第一次仍为 `Access submitted` 时应再查一次
- `Access submitted` 变为 `Ready to merge` 或 `Access not detected`，表示异步任务已经结束并刷新状态；持续超过 30 分钟仍为 `Access submitted` 时，提醒用户任务可能卡住并发起 Lidar Oncall
- `opt list` 展示后端返回的全部可选特性，包括尚未开启项，并提供开启状态、描述、推荐信息、操作限制、灰度要求和文档链接等详情
- `opt open --feature` 可重复或传逗号分隔列表；已开启特性会自动跳过，剩余特性作为一个批次共用一个策略
- `opt open` preview 的 `features` 保留全部请求特性，`features_to_open` 表示本次实际提交项，`already_open_features` 表示无需重复提交的已开启项
- 批次中任一特性需要灰度但未传 `--strategy-id` 时，`opt open` 会返回整批共同可用的策略；选择 ID 后再加 `--yes` 提交
- `profit create` 默认只输出完整 request payload，并用英文提示以同一命令加 `--yes` 执行；显式传 `--yes` 创建成功后只输出 task ID。单 vregion 模式使用 `--vregion` 和四个 Unix 秒时间戳；多 vregion 模式使用 `--profit-times-json` 或 `--profit-times-file`，每个 vregion 可指定不同的新/旧时间窗口，两种模式不能混用
- `profit create` 的新/旧时间窗口推荐 1h 或 2h；更长时间窗口不保证计算成功率和准确性
- `profit get` 按 task ID 返回创建人、完成时间、PSM、计算状态、飞书报告链接，以及各集群可节省 CPU core 和 CPU 使用率降低比率；指定 `--peak` 时查询平台自动识别前后高峰期生成的收益报告，输出中的 `report_mode` 为 `peak`
- `profit list` 必须指定 `--psm`，默认查询最近 1 周；可用 `--date YYYY-MM-DD` 按本地自然日查询历史记录；文本模式按 PSM、task ID、事件类型、开始时间、结束时间和操作人展示分页列表

### AI Analysis

- AI 分析为异步任务：`lidar analysis analyze` 提交后返回 `task_id`，通过 `lidar analysis status --task-id <id>` 轮询状态（`submitted` → `running` → `succeeded`/`failed`），完成后用 `lidar analysis get --task-id <id>` 获取 Markdown 格式的分析报告
- `--thinking` 启用深度思考模式，分析更详细但耗时更长
- `--web-search` 启用联网搜索增强（仅 CN 站点可用）
- `--language English` 可指定输出语言为英文，默认中文
- `--wait` 模式会阻塞直到分析完成（默认超时 5 分钟），适合脚本中一步到位
- `lidar analysis get --profiling-id <id>` 可查询某个 profiling 的最新分析记录；带 `--history-task-id` 则返回特定任务
- `lidar analysis export-doc --profiling-id <id>` 将分析结果导出为飞书文档，返回 doc_token 和 URL

### 火焰图与 pprof 基础概念

- **火焰图（Flamegraph）**：一种可视化 CPU 采样结果的图形，横轴表示采样到的函数调用，纵轴表示调用栈深度。**方块越宽**，表示该函数被采样到的次数越多、占 CPU 时间越多。图形化火焰图可在浏览器中交互式查看：点击方块可以放大查看子调用链，鼠标悬停可查看函数名和占比。
- **栈顶（leaf）**：火焰图最顶层的方块，对应 `pprof -top` 的 `flat` 列。表示**当前正在 CPU 上执行的函数**（调用栈的叶子节点）。如果栈顶是系统调用（如 `Syscall6`、`futex`），说明 CPU 正在执行内核态操作（网络 IO、锁等待）。
- **栈底（root）**：火焰图最底层的方块，对应 goroutine 入口或框架入口函数（如 `Server.Serve`、`main`）。表示**调用链的起点**。
- **flat**：函数自身的 CPU 耗时（不包括其子调用）。`flat` 高的函数是**真正在消耗 CPU 的指令位置**，通常是最值得关注的热点。如果 `flat` 远小于 `cum`，说明该函数主要是个"调度/分发"角色，实际开销在它调用的子函数里。
- **cum（cumulative）**：函数自身 + 所有子调用的 CPU 总耗时。`cum` 高说明该函数及其调用链整体是热点路径。
- 判断优先级：`flat` 高 → 该函数本身是热点（看具体指令）；`flat` 低但 `cum` 高 → 该函数是调用链入口，需往下看子调用找真正热点。
- 用户要求分析已下载的 pprof 数据时，推荐使用 `go tool pprof -top -nodecount=<N> <file.pb.gz>` 获取 `flat` 和 `cum` 聚合热力图。
- 用户要求查看采样结果的结构化调用栈时，使用 `bytedcli lidar sampling get --id <profiling_id> --stack --limit <N>`。CLI 内部先下载 pprof 二进制数据，再解析为按 CPU 耗时降序排列的调用栈列表，每条栈的 frame 顺序为 leaf → root。

## References

- `../../invocation.md`
- `references/lidar.md`

## Agent Guidance

- 触发场景：用户问 "xxx 服务有没有开 Lidar 采样 / 采样开关开了吗 / 为什么 Lidar 里没采样数据 / SamplingConfig / 条件采样配置"。
- 推荐命令：`bytedcli lidar config get --psm <psm>`。
- 判读优先级：
  1. `enabled_summary.effective` — 综合开关；false 直接告诉用户未开启。
  2. `access_status.prod` / `access_status.ppe` — Agent 是否接入；都 false 说明根本没接 agent。
  3. 6 条规则的全局 `on` 与 `zones[].on`（rules.cpu / mem / goroutine / cpu_burst / mem_burst / goroutine_burst）— `enabled_summary.any_rule_on` 已同时计入两类开关。
- 修改规则时先运行 `config get` 核对当前值，再运行不带 `--yes` 的 `config set` 审阅实际 request；确认后以同一参数追加 `--yes`。
- 用户需要分析某个自然日的服务高峰指标或定位对应定时采样时，运行 `bytedcli lidar peak stats --psm <psm> --date <YYYY-MM-DD>`；需要缩小范围时追加 `--region` 或 `--cluster`。
- 用户给出普通即时采样 `profiling_id` 并要求查看详情时，运行 `bytedcli lidar sampling get --id <profiling_id>`；如果 ID 来自 `peak stats`，必须运行 `bytedcli lidar sampling get --id <profiling_id> --peak`。需要调用栈/堆栈详情时再追加 `--stack`；agent 组合采样可用 `--profile-type` 选择子结果，多 metric 的 heap profile 可从错误或 JSON 的 `available_sample_types` 中选择 `--sample-type`。
- 云控接入前先运行 `opt stats`；特性接入前先运行 `opt list`。
- `opt access`、`opt open` 必须先不带 `--yes` 审阅预览；若 `opt open` 返回 `available_strategies`，从中选择整批特性共同可用的 `--strategy-id`，再以同一参数加 `--yes` 提交。
- 执行 `opt access --yes` 后，用 `opt stats --psm <psm>` 主动刷新状态；若仍返回 `Access submitted`，再执行一次读取刷新后的状态。`Ready to merge` 表示任务成功并等待 MR 合入，`Access not detected` 表示任务结束但接入未建立；持续超过 30 分钟仍为 `Access submitted` 时建议发起 Lidar Oncall。
- 解读 `opt stats` 时，`features` 是当前已开启特性；需要选择新特性或查看完整详情时使用 `opt list`。
- 收益评估写操作先运行不带 `--yes` 的 `profit create` 审阅预览，确认后以同一参数加 `--yes` 提交；不要把预览结果当成已创建。
- 用户要求查看某个采样结果的热点排名（top N）时，优先使用 `bytedcli lidar sampling get --id <profiling_id> --stack --limit <N>` 获取结构化调用栈，然后按 `value`（CPU 耗时）降序展示前 N 条栈，并告知用户：每条栈的 `rank` 是从高到低排列的，`value` 是该条调用栈被采样到的 CPU 耗时，`ratio` 是其占总采样时间的比例。frame 顺序为 leaf → root（栈顶 → 栈底）。
- 如果用户已经下载了 pb.gz 文件并希望看到函数级别的聚合热点（而非完整调用栈），推荐先运行 `go tool pprof -top -nodecount=<N> <file.pb.gz>` 获取 flat/cum 表格，然后解释：`flat` 是该函数自身 CPU 耗时（出现在栈顶的总和），`cum` 是该函数及其所有子调用的 CPU 总耗时；`flat` 高的函数是最值得关注的真正热点。
- 当用户问"火焰图怎么读"、"栈顶是什么意思"、"flat 和 cum 有什么区别"等概念问题时，参考 `## Notes` 中的「火焰图与 pprof 基础概念」小节进行解释。
- 用户要求对某个 profiling_id 做性能分析或诊断时，使用 `bytedcli lidar analysis analyze --profiling-id <id>` 提交 AI 分析任务。如果用户希望等待结果，追加 `--wait`。
- AI 分析结果包含 token 用量和耗时信息；可用 `lidar analysis export-doc --profiling-id <id>` 将 Markdown 报告导出到飞书文档共享。
- 如果用户多次对同一 profiling 执行 AI 分析，可以使用 `lidar analysis get --profiling-id <id>` 查看历史记录，避免重复提交。
- `thinking` 模式分析更深入但耗时更长，建议默认启用；`web-search` 仅 CN 站点可用，可提供更丰富的上下文。
