# Lidar 即时采样参数参考

Lidar 是字节服务性能平台，支持对 Golang / Python / Nodejs 服务发起即时 pprof 采样，无需提前部署采集 agent。

## 采样类型

### Golang

| 类型           | 分类 | `--duration`    | 说明                                            |
| -------------- | ---- | --------------- | ----------------------------------------------- |
| `heap`         | 瞬时 | 省略或 `-`      | 堆内存分配快照，用于定位内存泄漏                |
| `goroutine`    | 瞬时 | 省略或 `-`      | 当前所有 goroutine 栈，用于排查 goroutine 泄漏  |
| `allocs`       | 瞬时 | 省略或 `-`      | 自启动以来累计分配快照                          |
| `memstats`     | 瞬时 | 省略或 `-`      | Go 运行时内存统计                               |
| `block`        | 瞬时 | 省略或 `-`      | 阻塞事件采样                                    |
| `mutex`        | 瞬时 | 省略或 `-`      | mutex 竞争采样                                  |
| `waitduration` | 瞬时 | 省略或 `-`      | goroutine wait duration 采样                    |
| `dynconf`      | 瞬时 | 省略或 `-`      | Tango 子组：动态配置快照                        |
| `pod_cpu`      | 瞬时 | 省略或 `-`      | Pod CPU 使用快照                                |
| `profile`      | 时长 | 秒数（如 `30`） | CPU 热点火焰图，最常用的性能分析类型            |
| `trace`        | 时长 | 秒数            | Go 运行时 trace，包含 goroutine 调度、GC 事件等 |
| `latency`      | 时长 | 秒数            | Tango 子组：请求延迟分析                        |

完整可用值以 `bytedcli lidar sampling create --help` 输出为准。

### 本地上传支持的类型

`sampling upload` 只接受后端允许落库和写 TOS 的类型：

`profile`、`heap`、`goroutine`、`allocs`、`mutex`、`block`、`threadcreate`、`mlc_profile`。

`trace`、`latency`、`memstats`、`dynconf`、`pod_cpu`、Nodejs `cpuprofile` / `heapprofile` / `heapsnapshot` 等不属于通用上传白名单。

### Python / Nodejs

与 Golang 使用相同命令，`--type` 可用值取决于服务端对该服务支持的采样类型。常用：

| 类型           | 语言   | 说明        |
| -------------- | ------ | ----------- |
| `profile`      | Python | CPU profile |
| `pyspy`        | Python | py-spy 采样 |
| `heap`         | Python | 堆内存快照  |
| `cpuprofile`   | Nodejs | CPU profile |
| `heapprofile`  | Nodejs | 堆采样      |
| `heapsnapshot` | Nodejs | 堆快照      |

## Lidar vs ByteDog 对照

| 场景                                           | 使用                |
| ---------------------------------------------- | ------------------- |
| Golang pprof（heap / profile / goroutine ...） | `bytedance-lidar`   |
| Python / Nodejs 即时采样                       | `bytedance-lidar`   |
| C++ CPU 火焰图                                 | `bytedance-bytedog` |
| Java 性能分析（GC / Heap / Thread / Stack）    | `bytedance-bytedog` |
| jemalloc 内存火焰图                            | `bytedance-bytedog` |
| off-CPU 火焰图（锁等待 / IO 等待）             | `bytedance-bytedog` |

## 域名说明

Lidar 的管理面与数据面按 site 使用不同域名：

| 域名                         | 用途                                               |
| ---------------------------- | -------------------------------------------------- |
| ByteCloud 站点域名           | 管理 API（创建采样、查询状态、列表历史、页面展示） |
| `lidar.bytedance.net`        | CN 数据服务（pprof 下载、火焰图渲染）              |
| `lidar-boe-cn.bytedance.net` | BOE 数据服务（pprof 下载、火焰图渲染）             |
| `lidar-i18n.tiktok-row.org`  | i18n-tt 数据服务（pprof 下载、火焰图渲染）         |
| `lidar-ttp.tiktok-row.org`   | US-TTP API 与数据服务                              |

CLI 内部已做好域名路由，用户无需关心。

## 常见 Flow

### CPU 热点分析

```bash
# 1. 发起 profile 采样（30 秒），等待完成
bytedcli lidar sampling create --psm demo.psm.lidar --type profile --duration 30 --wait

# 2. 输出末尾会包含火焰图 URL 和下载 URL，直接在浏览器打开
# flamegraph_url: https://cloud.bytedance.net/lidar/service/instant-sampling?profilingId=<id>&psm=<psm>
# download_url:   https://lidar.bytedance.net/api/v1/pprof/ui/<id>/flamegraph?trigger_type=manual&download=true

# 3. 如果 --wait 超时，用 get 继续查
bytedcli lidar sampling get --id demo.psm.lidar_202604181600_abc

# 4. 完成后在 get 中查看结构化调用栈（leaf → root）
bytedcli lidar sampling get --id demo.psm.lidar_202604181600_abc --stack
```

### Heap 内存泄漏排查

```bash
# 瞬时类型，不需要 --duration
bytedcli lidar sampling create --psm demo.psm.lidar --type heap --wait

# 对比不同时间点的 heap 快照
bytedcli lidar sampling list --psm demo.psm.lidar --type heap
```

### 下载原始 pprof 数据

```bash
# 下载到当前目录（自动命名为 <profiling_id>.pb.gz）
bytedcli lidar sampling download --id demo.psm.lidar_202604181600_abc

# 指定输出路径
bytedcli lidar sampling download --id demo.psm.lidar_202604181600_abc --output /tmp/heap.pb.gz

# 下载后可用 go tool pprof 本地分析
go tool pprof /tmp/heap.pb.gz
```

### 查看结构化调用栈

```bash
# 使用 profile 默认 metric，按 value 降序返回前 20 条调用栈
bytedcli lidar sampling get --id demo.psm.lidar_202604181600_abc --stack

# 返回更多调用栈（最大 500）
bytedcli lidar sampling get --id demo.psm.lidar_202604181600_abc --stack --limit 50

# heap 等多 metric profile 可显式选择 sample type
bytedcli --json lidar sampling get --id demo.psm.lidar_202604181600_abc --stack --profile-type heap --sample-type inuse_space
```

`sampling get` 默认只查询即时采样状态，不会在失败后自动切换数据源。查询 `peak stats` 返回的定时采样 ID 时必须显式追加 `--peak`；CLI 会从 `<psm>_<YYYYMMDD...>_<suffix>` 格式的完整 ID 自动推导 PSM 和日期，并在 `peak stats` 使用的 service profilings map 中精确匹配。后端不提供通用的 schedule status 查询；仅当 Bytedog 的 `pod_cpu` / `pyspy` map 值是类型占位符时，CLI 才按 PSM、日期和采样类型读取 schedule history，并在本地匹配真实 ID，不向故障的 history keyword 查询传 ID。定时采样详情只返回可确认的描述字段；`profiling_status`、`creator`、`vregion` 未知时在 JSON 中为 `null`，文本模式显示 `-`。该模式的 `flamegraph_url` 与 `download_url` 使用同一个 pprof 地址，前者不带 `download=true`，后者带该参数。追加 `--stack` 后会沿用 `trigger_type=schedule` 直接下载并解析标准 pprof，不执行状态校验。CN、BOE、i18n-tt 经 ByteCloud 管控代理读取，US-TTP 经 Lidar 的直连 API/Data 域读取。每条 stack 的 frame 顺序固定为 leaf → root；文本模式用 `->` 展示调用链，JSON 模式同时返回 `frames`、`location_ids`、各 sample type 的 `values`、选定指标占比和 profile metadata。

agent 组合采样会生成多个 `<profiling_id>_<profile-type>` 子结果，默认优先选择 `profile`；用 `--profile-type heap|goroutine|...` 可选择其他 pprof 子结果。默认 metric 使用所选 pprof 的 `default_sample_type`，未声明默认值时使用最后一个 sample type；可用 `--sample-type` 显式选择 `available_sample_types` 中的其他指标。默认返回 20 条，`--limit` 支持 1～500；`total_stacks` 大于 `returned_stacks` 时 `truncated=true`。所有 pprof int64/uint64 值均以十进制字符串输出，避免精度丢失。

stack 下载默认单次超时 60 秒且不自动重试，避免一次失败被重试放大成数分钟等待；如确有大 profile，可用 `--timeout-ms` 在 1～600000 毫秒内调整。

该命令只支持标准 pprof 结果。`trace`、`memstats`、动态配置快照、Node.js cpuprofile/heapsnapshot 等非 pprof 内容会返回结构化错误；这类结果使用 `sampling download` 和对应的本地分析工具。

### 上传本地采样数据

```bash
# 上传本地采样文件；creator 由后端根据当前登录 JWT 识别
bytedcli lidar sampling upload --psm demo.psm.lidar --type profile --file ./profile.pb.gz

# 记录实例字段，上传后可在前端采样记录里作为“实例”查看
bytedcli lidar sampling upload --psm demo.psm.lidar --type heap --file ./heap.pb.gz --pod-name demo-pod

# 上传 MLC profile；--uname 可选，省略时后端默认使用 rank_0
bytedcli lidar sampling upload --psm demo.psm.lidar --type mlc_profile --file ./mlc-profile.pb --uname rank_0
```

上传成功后会输出 `profiling_id`、`creator`、`flamegraph_url` 和 `download_url`。后端会把记录标记为成功状态，并要求当前登录用户是 Lidar 管理员或具备目标 PSM 的 `tce.service.update` 权限。

### 查询历史采样

```bash
# 最近 6h（默认）
bytedcli lidar sampling list --psm demo.psm.lidar

# 指定时间窗（支持 YYYY-MM-DD、YYYY-MM-DD HH:mm 或 unix 秒）
bytedcli lidar sampling list --psm demo.psm.lidar --begin "2026-04-18 10:00" --end "2026-04-18 18:00"

# 只看 profile 类型
bytedcli lidar sampling list --psm demo.psm.lidar --type profile

# 输出 JSON
bytedcli --json lidar sampling list --psm demo.psm.lidar
```

### 指定 Pod 采样

```bash
# 指定 pod 名称（不指定时服务端自动选择）
bytedcli lidar sampling create --psm demo.psm.lidar --type profile --duration 30 --pod-name demo-pod-xxx

# 指定 cluster
bytedcli lidar sampling create --psm demo.psm.lidar --type heap --cluster-id 123456
```

### 判断 PSM 是否开启 Lidar 条件采样

```bash
bytedcli lidar config get --psm demo.psm.lidar
bytedcli --json lidar config get --psm demo.psm.lidar
```

文本输出顶部含：

- `access_status`：Lidar Agent 在 prod / ppe 环境的接入状态（文本模式扁平展示为 `prod=... ppe=...`，JSON 模式保留对象结构）
- `effective`：综合开关，对应 JSON 里的 `enabled_summary.effective`；true 表示采样会真正触发
- `source` / `owners`：规则定义来源与负责人

下方按配置层级分区展示：

- `Rules (Global Defaults)`：6 条命名规则（cpu / mem / goroutine / cpu_burst / mem_burst / goroutine_burst）的全局阈值、瓶颈值、启用状态与 profilings。
- `Rule Zone Overrides`：条件采样的单集群覆盖，显示 `vregion`、`env`、`cluster_id` 和覆盖后的规则值。
- `动态特性配置（全局默认）`：动态特性配置的全局字段和值。
- `动态特性配置 Zone 覆盖`：动态特性配置的集群/阶段覆盖；`cluster_ids` 是生效集群，`stages` 为空数组时文本模式显示 `all`。

JSON 输出顶层包含 `rules`、`runtime_strategy`、`runtime_strategy_zones` 与
`enabled_summary`，并保留 `raw`。`enabled_summary.any_rule_on` 同时检查规则的全局
`on` 和 `zones[].on`。

### 修改条件采样配置

先查询当前值，再预览修改。`config set` 默认不写入；只有原参数追加 `--yes`
才提交。更新是非破坏性的 partial update：

- shortcut 要求同时提供 `--rule`、`--threshold`、`--on`、
  `--sampling-type`、`--sampling-duration`；三类 `_burst` 规则还要求
  `--bottleneck`。
- `--threshold` / `--bottleneck` 接受非负有限小数；`--sampling-duration`
  只接受非负整数秒。
- shortcut 只新增指定 sampling type，或更新已有同名 type 的 duration，并保留
  其他 sampling types；`--cluster-id` 只更新已存在的 zone。
- `--config` / `--config-json` 可更新 `rules`、`rules_extra`、
  `runtime_strategy`、`runtime_strategy_zones`。省略字段会先与当前配置合并。
- 动态特性配置按 feature 和字段 `name` 合并。修改 `maxheap` 时，当前配置中
  未出现在 patch 里的 `fight_recorder` 等动态 feature 以及 zones 都会保留；CLI
  最终按后端整图替换语义发送合并后的完整动态特性配置映射。
- preview 展示的 request 就是追加 `--yes` 后实际发送的 payload。
- 普通规则更新只发送目标规则，以及后端强制要求的 `monitoring_period`、
  `ping_period`。这两个字段未显式修改时会从当前配置自动补入。
- Lidar 后端会隐藏关闭规则的主 `profilings`。修改关闭规则时必须在 JSON patch
  中显式提供目标 `profilings`，否则 CLI 会阻断写入。
- `source` 必须以 `rules defined by:` 开头；继承或默认配置需要先在 Lidar Web
  建立直接配置。

```bash
# 查询当前完整配置
bytedcli --json lidar config get --psm demo.psm.lidar

# 快捷修改 mem 的 heap duration，并保留其他 sampling types
bytedcli --json lidar config set --psm demo.psm.lidar --rule mem --threshold 84 --on true --sampling-type heap --sampling-duration 0
bytedcli --json lidar config set --psm demo.psm.lidar --rule mem --threshold 84 --on true --sampling-type heap --sampling-duration 0 --yes

# 直接传 JSON 字符串：先预览，再提交
bytedcli --json lidar config set --psm demo.psm.lidar --config-json '{"rules":{"mem":{"value":84}}}'
bytedcli --json lidar config set --psm demo.psm.lidar --config-json '{"rules":{"mem":{"value":84}}}' --yes

# 从 JSON 文件读取复杂 partial update
bytedcli --json lidar config set --psm demo.psm.lidar --config ./sampling-config.json
bytedcli --json lidar config set --psm demo.psm.lidar --config ./sampling-config.json --yes
```

`--rule` 支持 `cpu`、`mem`、`goroutine`、`cpu_burst`、`mem_burst`、
`goroutine_burst`。`--rule`、`--config`、`--config-json` 三种输入模式必须且只能
选择一个。`--psm` 始终必填，`--yes` 始终可选；`--cluster-id` 可选，
`--bottleneck` 仅 `_burst` 规则支持且必填。

JSON patch 顶层只允许 `rules`、`rules_extra`、`runtime_strategy`、
`runtime_strategy_zones`。`monitoring_period` 与 `ping_period` 属于
`rules_extra`，不能放进 `rules`：

```json
{
  "rules": {
    "mem": {
      "value": 84
    }
  },
  "rules_extra": {
    "monitoring_period": 3,
    "ping_period": 240
  }
}
```

如果只是修改 `mem.value`，应省略 `rules_extra`，CLI 会读取并保留当前周期。
`--config` 当前读取 JSON 文件；文件扩展名不影响解析，但不支持 YAML 语法。

动态特性配置 partial update 示例：

```json
{
  "runtime_strategy": {
    "maxheap": [
      {
        "name": "on",
        "value": false
      }
    ]
  }
}
```

`maxheap` 会先与当前动态特性配置映射合并，再提交完整 `runtime_strategy` 和
`runtime_strategy_zones`。显式 `zones: []` 或动态特性的 zone 空数组表示清空对应
zone 集合。

## Atum 云控与优化特性

```bash
# 查询 Atum 云控接入状态；已接入时同时展示全部已开启特性
bytedcli lidar opt stats --psm demo.psm.lidar

# 触发云控接入：默认预览，确认后提交
bytedcli --json lidar opt access --psm demo.psm.lidar
bytedcli --json lidar opt access --psm demo.psm.lidar --yes

# 查询该 PSM 的全部可选优化特性及详情，包括尚未开启项
bytedcli lidar opt list --psm demo.psm.lidar

# 批量开启不需要灰度策略的特性：--feature 可重复或使用逗号分隔
bytedcli --json lidar opt open --psm demo.psm.lidar \
  --feature demo-feature-a --feature demo-feature-b
bytedcli --json lidar opt open --psm demo.psm.lidar \
  --feature demo-feature-a,demo-feature-b --yes
```

`opt access` 固定使用 Git 预定义 MR 路径完成 Atum 接入，不提供切换接入
方式的参数。这条命令不同时开启特性，也不接受特性放量阶段使用的
`--skip-standalone-clusters` 或 `--skip-i18nbd`。

`opt access --yes` 只触发异步接入任务，后端不会在后台持续轮询。需要主动
执行 `bytedcli lidar opt stats --psm <psm>` 才会触发状态刷新。后端会先用
刷新前的数据组装本次响应，再执行刷新，因此第一次仍返回
`Access submitted` 时应再执行一次 `opt stats`：

- `Access submitted`：任务仍在执行，或本次查询刚触发刷新但返回的仍是旧状态。
- `Ready to merge`：异步任务已成功结束，MR 已创建并等待合入。
- `Access not detected`：异步任务已结束，但接入未建立或任务失败后已重置状态。
- `Accessed`：MR 已合入且 Atum 接入完成。

若从任务发起起超过 30 分钟，多次执行 `opt stats` 后仍保持
`Access submitted`，认为任务可能卡住，应提醒用户发起 Lidar Oncall。

```bash
# 需要灰度的批次：首次不传 strategy-id，读取整批共同可用的候选策略
bytedcli --json lidar opt open --psm demo.psm.lidar \
  --feature demo-feature-a --feature demo-feature-b

# 从 available_strategies 选择 ID 后预览
bytedcli --json lidar opt open --psm demo.psm.lidar \
  --feature demo-feature-a,demo-feature-b --strategy-id 123

# 确认提交
bytedcli --json lidar opt open --psm demo.psm.lidar \
  --feature demo-feature-a,demo-feature-b --strategy-id 123 --yes
```

- `opt stats` 在 Atum 云控已接入时，同时返回后端记录的全部
  `is_open=true` 特性；未接入时只展示接入状态。
- `opt list` 返回 service detail 中的全部可选特性，包括尚未开启项，并展示
  开启状态、描述、推荐信息、操作限制、灰度要求、灰度状态、在线比例、工单、
  更新时间和文档链接。
- `opt open` 会先读取服务状态，校验已接入云控、所有特性存在且允许操作；
  已开启特性会自动从本次提交批次中剔除，但仍保留在 preview 的
  `features` 中。
- `--feature` 可重复，也可传逗号分隔列表；去重后的剩余特性通过同一个后端
  请求提交，并共用一个 `strategy_detail`。
- 批次中任一特性需要灰度且未传 `--strategy-id` 时，JSON 返回整批共同可用的
  `available_strategies`，不会提交。
- 已传 `--yes` 但缺少必须的策略时，CLI 抛 `LIDAR_INPUT_ERROR` 并在
  `details.available_strategies` 中返回候选项。
- `opt access` 默认只输出英文 `--yes` 确认提示和 `request`；加
  `--yes` 后只返回最终接入状态，不返回 `before` 或 `request`。
- `opt open` preview 的 `features` 保留全部请求特性，`features_to_open`
  是本次实际提交项，`already_open_features` 是无需重复提交的已开启项；
  同时输出 `message` 和已选 `strategy`，不输出 `before`、`after` 或
  `request`。确认后以同一参数加 `--yes`，CLI 才写入并批量回读特性状态。

## 高峰期服务指标

```bash
# 查询单日高峰期六组服务指标和定时采样详情
bytedcli lidar peak stats --psm demo.psm.lidar --date 2026-08-05

# 按 VRegion 和精确 cluster 过滤
bytedcli --json lidar peak stats --psm demo.psm.lidar --date 2026-08-05 --region China-North --cluster demo-cluster
```

结果按 cluster 聚合 `qpc`、`qps`、`cpu_usage`、`cpu_rate`、`mem_usage` 和
`mem_rate`，并关联当天的定时采样：

- `vregions`：该行涉及的 VRegion。
- `profiling_ids`：指标和定时采样中出现的 profiling ID 去重集合。
- `peak_samplings`：每项包含 `profiling_id`、`sampling_type` 和 `vregions`。

复制其中的定时采样 ID 后，用 `--peak` 查询详情或标准 pprof 调用栈：

```bash
bytedcli lidar sampling get --id demo.psm.lidar_202609040900_sample --peak
bytedcli lidar sampling get --id demo.psm.lidar_202609040900_sample --peak --stack
```

文本模式的结果表标题为 `Details`，结果行按 `cpu_usage` 降序排列，缺失 CPU
Usage 的行排在最后；CPU Usage 相同时按日期降序、cluster 升序稳定排序。即使
某个 cluster 没有非零指标，只要存在当天定时采样，仍会保留该行并将缺失指标
输出为 `null`（文本模式为 `-`）。

CLI 直接读取 Lidar service profilings 接口返回的 profiling map，不依赖数据库
查询函数展开 map keys。仅当 Bytedog 的 `pod_cpu` / `pyspy` 映射缺少真实
profiling ID 时，才使用带 `sampling_type` 的 schedule history 精确回退。

## 收益评估

```bash
# 创建异步任务：先预览，再确认提交
bytedcli --json lidar profit create --psm demo.psm.lidar --vregion China-North --new-begin-time 1785772800 --new-end-time 1785776400 --old-begin-time 1785686400 --old-end-time 1785690000
bytedcli --json lidar profit create --psm demo.psm.lidar --vregion China-North --new-begin-time 1785772800 --new-end-time 1785776400 --old-begin-time 1785686400 --old-end-time 1785690000 --yes

# 多 vregion 可为每个区域指定独立时间窗口；复杂输入推荐使用 JSON 文件
bytedcli lidar profit create --psm demo.psm.lidar --profit-times-json '{"China-North":{"new_begin_time":1785772800,"new_end_time":1785776400,"old_begin_time":1785686400,"old_end_time":1785690000},"China-East":{"new_begin_time":1785859200,"new_end_time":1785862800,"old_begin_time":1785772800,"old_end_time":1785776400}}'
bytedcli lidar profit create --psm demo.psm.lidar --profit-times-file ./profit-times.json --yes

# 按 task ID 查询任意状态
bytedcli lidar profit get --task-id demo-task-id
bytedcli lidar profit get --task-id demo-task-id --peak

# 按 PSM 查询收益计算列表
bytedcli lidar profit list --psm demo.psm.lidar
bytedcli lidar profit list --psm demo.psm.lidar --date 2026-07-22
bytedcli lidar profit list --psm demo.psm.lidar --page 2 --page-size 10
```

`profit get` 返回创建人、完成时间、PSM、计算状态、飞书报告链接，以及
`ReportData.Sheets` 中各集群的可节省 CPU core 和 CPU 使用率降低比率。
默认读取事件前后时段的收益报告，JSON 中 `report_mode` 为 `around`；指定
`--peak` 时 CLI 发送 `peak=1`，读取平台自动识别前后高峰期生成的报告，
`report_mode` 为 `peak`。
CPU 使用率降低比率按
`(new_mem - old_mem) / old_mem` 计算；基准值为 0 时返回 `null`，文本显示
`-`。

`profit list` 必须指定 `--psm`，默认查询最近 1 周。若要查询更早的某一天，
传 `--date YYYY-MM-DD`，CLI 会按运行机器本地时区查询该自然日的
`00:00:00` 到 `23:59:59`。文本模式按 PSM、task ID、事件类型、开始时间、
结束时间和操作人展示分页列表；JSON 模式保留 `query_date`、查询窗口、完整
事件和分页字段。

`profit create` 的 `--new-begin-time`、`--new-end-time`、`--old-begin-time`
和 `--old-end-time` 都必须是 Unix 秒。新/旧时间窗口推荐 1h 或 2h；更长时间
窗口不保证计算成功率和准确性。

多 vregion 模式的 `--profit-times-json` / `--profit-times-file` 使用以下结构：

```json
{
  "China-North": {
    "new_begin_time": 1785772800,
    "new_end_time": 1785776400,
    "old_begin_time": 1785686400,
    "old_end_time": 1785690000
  },
  "China-East": {
    "new_begin_time": 1785859200,
    "new_end_time": 1785862800,
    "old_begin_time": 1785772800,
    "old_end_time": 1785776400
  }
}
```

每个 vregion 的四个字段均必填，且 begin 必须早于对应 end。多 vregion 输入不能
与 `--vregion`、`--new-begin-time`、`--new-end-time`、`--old-begin-time`、
`--old-end-time` 混用。

未传 `--yes` 时，`profit create` 只输出完整 request payload，并提示
`No request was submitted. Re-run the same command with --yes to execute.`；
传入 `--yes` 且创建成功后只输出 task ID，不展示 before/after 对比信息。

`profit create --vregion` 是服务部署 vregion，例如 `China-North` 或
`China-East`，不是 bytedcli 全局 `--site`。

## 多 Site 说明

| Lidar 控制面      | `--site` 值                              | 认证                         |
| ----------------- | ---------------------------------------- | ---------------------------- |
| 国内（默认）      | `cn` 或省略                              | ByteDance SSO                |
| BOE               | `boe`                                    | BOE SSO                      |
| TikTok 国际控制面 | `i18n` / `i18n-bd` / `i18n-tt`           | TikTok SSO，统一走 `i18n-tt` |
| US-TTP            | `us-ttp` / `us-ttp-bdee` / `us-ttp-usts` | TikTok SSO，统一走 `us-ttp`  |

```bash
# 三种输入在 Lidar 下等价；先建立 i18n-tt 登录态
bytedcli --site i18n-tt auth status
bytedcli --site i18n-tt auth login
bytedcli --site i18n lidar peak stats --psm demo.psm.lidar --date 2026-08-05
bytedcli --site i18n-bd lidar sampling create --psm demo.psm.lidar --type heap
bytedcli --site i18n-tt lidar sampling create --psm demo.psm.lidar --type profile --duration 30

# BOE 使用独立的管理面和 pprof 数据域
bytedcli --site boe auth status
bytedcli --site boe lidar sampling get --id demo.psm.lidar_202604181600_abc --stack

# 三种 US-TTP 输入在 Lidar 下统一走 us-ttp 认证和路由
bytedcli --site us-ttp auth status
bytedcli --site us-ttp lidar sampling get --id demo.psm.lidar_202604181600_abc --stack
```

该映射只在 Lidar domain 内生效，不会改变其他 bytedcli domain 的全局站点语义。

## 时区说明

`--begin` / `--end` 按**本机时区**解析，接受以下格式：

- `YYYY-MM-DD`（当天 00:00:00）
- `YYYY-MM-DD HH:mm`
- unix 秒字符串（如 `1775306700`）

CLI 内部会将解析后的 Date 转换为 unix 秒再下发给 API，与本机时区无关。

## 输出说明

- `sampling create` 成功后输出 profiling_id、pod_name、cluster 信息，以及 `download_url`
- `sampling get` 输出采样状态（`running` / `success` / `fail`）、火焰图 URL（成功时）和 `download_url`
- `sampling get --stack` 输出指定 profiling_id 的 ranked call stacks；frame 顺序为 leaf → root，客户端截断通过 `truncated` 明示
- `sampling list` 以表格展示历史记录，含 profiling_id、类型、状态、发起时间
- `sampling download` 将原始 pprof 数据下载到本地，默认文件名为 `<profiling_id>.pb.gz`
- `sampling upload` 将本地采样数据上传成成功记录，输出 profiling_id、火焰图 URL 和下载 URL
- `profit create` 默认只输出 request payload 和 `--yes` 提示，提交成功后只输出 task ID；单 vregion 使用 flags，多 vregion 使用 `--profit-times-json` / `--profit-times-file`；`profit get` 返回任务与集群收益详情；`profit list --psm` 返回计算列表
- `--json` 模式返回完整结构化 JSON；普通 `sampling get` / `sampling create` 包含 `download_url`，`sampling get --stack` 包含本次解析所用的 `source_url`，不承诺 `log_id` 或 `download_url`
