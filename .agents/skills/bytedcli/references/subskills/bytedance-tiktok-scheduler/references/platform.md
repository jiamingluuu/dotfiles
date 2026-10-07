# TikTok Scheduler 平台背景

本文是 TikTok Scheduler 平台能力的精简说明，帮助你理解 `bytedcli tiktok-scheduler` 各命令背后的语义与默认行为。命令用法见 [tiktok-scheduler.md](tiktok-scheduler.md)。

## 产品定位

TikTok Scheduler 是面向在线业务的可靠任务调度与异步执行平台，提供**延时执行**与**周期执行**能力。用户只描述「做什么」（任务动作）和「何时做」（调度规格），执行过程、状态追踪、重试策略与故障处理都由平台自动完成。底层调度**不依赖消息队列（MQ）**，可直接调用已有的 RPC / HTTP 接口，接入成本低。

相比常见替代方案的关键差异：

- 对比 MQ 自建：不会有消息堆积 / 丢失 / 重复投递，且有「任务」概念可观测、可治理。
- 对比 CronJob：支持秒级调度（CronJob 最小约 3 分钟），适合在线业务。
- 对比 ByteFaaS 定时触发器：可直接调用已有 RPC/HTTP 接口，无需额外包一层 FaaS 函数。
- 延迟时长无上限；默认无限重试。

## 任务动作（Action）

任务到达调度周期后执行的具体内容，对应 CLI 的 `--action-type rpc|http|workflow`：

- **RPC Action**：配置 PSM / cluster / 请求参数 / 重试策略 / 是否异步 / 限流；平台借助 Kitex 二进制泛化调用完成请求。
- **HTTP Action**：配置 URL / Method / Body / 重试 / 异步 / 限流；**仅支持域名类型 URL，不支持 consul 服务发现**。
- **Workflow Action**：多个 RPC / HTTP Action 的工作流编排。与 BPM / ByteFlow 不同，**无需预先定义流程**，由每个步骤自行声明下一步要执行什么。

## 一次性任务（onetime）

仅执行一次任务动作，支持：

- 延迟时长（无上限）：决定动作是创建后立即执行还是延迟执行。
- 抖动区间：打散同一时间的大规模请求，避免打挂下游。
- 终止操作：只要任务在运行中（含等待延迟 / 等待重试），均可立即终止。

典型场景：优惠券过期、超时订单关单等延迟业务处理、延迟重试、LLM 类长耗时消费（不走 MQ 避免重复投递）、只求触达不关心返回的委托调用。

## 周期性任务（recurring）

周期性执行 N 次任务动作，支持：

- 调度规格：7 位秒级 crontab（`秒 分 时 日 月 周 年`）或固定时间间隔（interval，可带 offset）。
- 抖动区间。
- 开始 / 结束时间限制生效区间；**若配置了结束时间，周期任务会在结束时间一周后被自动删除**。
- 并发处理策略（上一周期未结束时新触发如何处理）：Skip / BufferOne / BufferAll / CancelOther / TerminateOther / AllowAll。
- 暂停 / 启动 / 手动触发一次 / 更新配置 / 删除；可查看所有执行记录。

## 重试策略（重要：默认无限重试）

平台理念是默认对异常尽可能重试且不限次数。RPC / HTTP Action 均可自定义，共性配置：

- **MaxAttempts**（最大执行次数，含第一次）：`0` = 无限重试。
- **InitialIntervalMs**（初始重试间隔）：默认 1 秒。
- **BackoffCoefficient**（退避指数）：第 N 次间隔 = 系数 × 第 N-1 次间隔；`1` = 间隔恒为 InitialIntervalMs。
- **MaxIntervalMs**（最大重试间隔）：默认 `100 × InitialIntervalMs`。

类型特有：

- RPC `NonRetryableConfig.BizStatusCodes`：RPC 默认对除 `BaseResp.StatusCode = 0` 外的所有报错（Kitex 报错、超时、Mesh 报错等）重试；列在此处的业务错误码不重试。
- HTTP `NonRetryableConfig.HttpStatusCodes`：HTTP 默认对除响应码 `200` 外的所有报错重试；列在此处的状态码不重试。

## 异步执行

RPC / HTTP 默认**同步**（返回即视为本次执行完成）。开启异步执行后需额外配一个异步完成超时：下游收到调用时先快速正常响应（RPC `BizStatusCode = 0` / HTTP `200`），再异步执行长耗时逻辑，完成后回调平台告知成功 / 失败 / 是否需要重试。未在超时内回调或返回需重试时，按重试策略重新调用；下游异常响应则直接判失败并重试，不再接收回调。适合小时级及更长的异步处理。

## 全局限流

为 Namespace 创建限流 Key 与各 VRegion 的限流值（未配置 = 不限流，`0` = 拒绝全部请求），创建任务时为 RPC / HTTP Action 指定该限流 Key（不区分一次性 / 周期性）。**命中限流的那次调用会被视为失败**，需靠重试策略再次发起调用。

## 幂等创建（仅一次性任务）

ScheduleId 可选；不指定时平台自动生成 UUID。指定时：若同一 Namespace 内存在运行中（含延迟中）的相同 ScheduleId 任务，该次调用直接返回成功**但不新建任务**；否则用该 ScheduleId 新建。可用订单 ID、流水 ID 等唯一字符串作为 ScheduleId 来去重。

## 任务治理：GroupKey / CustomKey / 保留时长

- 除按 ScheduleID 检索外，平台提供 **GroupKey**（标识同 Namespace 下不同业务类型）和 **CustomKey**（更细化，可设订单 ID / UID / DID 等）辅助分类与检索。
- ScheduleID / GroupKey / CustomKey 最大长度均为 **128 字符**。
- 执行历史按 Namespace 配置保留时长，**最大 14 天**，过期数据自动清理。

## Context 透传

每次执行时，任务动作会通过 Context Transient Value（**只透传至第一跳下游，不全链路透传**）携带任务元信息，下游可用 `metainfo.GetAllValues(ctx)` 读取：

- `TTSCHED_NS`：命名空间。
- `TTSCHED_SCHEDULE_ID`：任务 ID。
- `TTSCHED_GROUP_KEY` / `TTSCHED_CUSTOM_KEY`：创建时指定的 Group / Custom Key。
- `TTSCHED_START_TIMESTAMP_MS`：动作开始执行时间 = 创建时间 + 延迟 + 抖动。
- `TTSCHED_ATTEMPT_TIMES`：当前执行次数，从 1 开始（含第一次）。
- `TTSCHED_SCHEDULED_TIMESTAMP_MS`：按 Cron / Interval 计算的预期启动时间，不含抖动（**仅周期性任务有**）。

创建任务时所携带 Context 中的以下数据也会透传至后续调用：`K_LOGID`（统一 logid，便于跨创建/执行检索日志）、`K_ENV`（环境标识，PPE 创建则下游也路由到相同 PPE）、`K_STRESS`（压测标识）、以及全链路透传的 Persistent Metainfo。

## 多租户隔离与多机房

- **Namespace** 是多租户隔离单元，每个 Namespace 独享底层执行资源（部署在 TCE）。
- 平台只有一个线上控制面，Namespace 在生产环境**全局唯一**。
- 创建 Namespace 时选择部署的 VRegion，目前支持：`Singapore-Central / EU-TTP2 / US-EastRed / US-TTP / US-TTP2`，在同一控制面即可浏览各 VRegion 的任务数据。
- 周期任务支持 **VRegion 间克隆**。
- 周期任务 ScheduleId 仅需在单个 VRegion 内唯一；延迟任务的幂等创建也**仅在本 VRegion 生效**。
- Namespace 授权操作只需在全局控制面配置一次，即对所有 VRegion 生效。

## 接入注意事项（易踩坑）

- **RPC 目标开启 Neptune 严格鉴权**：需先给 `tiktok.scheduler.worker` 服务加权限，上游集群选择与命名空间同名的集群。
- **控制台创建 RPC 任务**：目标 PSM 的接口 IDL 需先在元数据平台完成配置，否则无法创建。
- **下游部署在 PPE 机房**：先提交 PPE 跨 VDC BPM 工单，caller psm 填 `tiktok.scheduler.worker`，跨机房类型选「默认」，否则请求可能打到线上环境。

## 控制台与 SDK

- 控制台 host：`https://ttscheduler.aipa.bytedance.net`（线上 `?env=prod`，US-BOE `?env=boe`）；详情页链接拼法见 [tiktok-scheduler.md](tiktok-scheduler.md) 的「控制台详情页链接」一节。
- Golang SDK 仓库：`code.byted.org/eventbus/scheduler-client-go`（使用前需先为调用 SDK 的 PSM 增加命名空间授权）。
- `bytedcli tiktok-scheduler` 直接操作控制面 HTTP API，已覆盖控制面基本全部操作，无需自行接 SDK 即可创建 / 查询 / 管理任务。

## SLA

- 任务创建可用性 ≥ 99.9%。
- 单个 Namespace 默认支持 1k QPS，有更高诉求可联系平台扩容（最高可至万级 QPS）。
- 调度精准度（默认 1k QPS 下）：一次性延迟任务与周期性任务均**不会提前执行**，延后执行 p99 < 500ms。
