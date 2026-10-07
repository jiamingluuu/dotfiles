# FTF OpenAPI 枚举参考

## 用途

本文件沉淀 FTF / TeslaX OpenAPI 常见枚举字段，供 `task-api.md`、`plan-api-schema.md` 和 diff 分析文档引用。CLI 对外优先暴露语义值，后端数字值只作为解释 API 响应和 `--payload` 深字段时的参考。

## 目录

- [任务状态](#任务状态)
- [任务回调状态](#任务回调状态)
- [单条流量回放失败码](#单条流量回放失败码failed_reason)
- [触发与流量来源](#触发与流量来源)
- [方法与协议](#方法与协议)
- [环境与回放](#环境与回放)
- [Mock 与外调](#mock-与外调)
- [Assertion 相关](#assertion-相关)
- [diff 聚类标注原因](#diff-聚类标注原因optype)
- [similar diff 标注来源](#similar-diff-标注来源operateuser)

## 任务状态

### `status`

| 值   | 后端常量                    | 含义                     |
| ---- | --------------------------- | ------------------------ |
| `0`  | `TaskStatusInit`            | 任务初始化               |
| `1`  | `TaskStatusRunning`         | 回放中                   |
| `2`  | `TaskStatusReplayDone`      | 回放完成                 |
| `3`  | `TaskStatusAborted`         | 任务失败                 |
| `5`  | `TaskStatusAssertRunning`   | 断言中                   |
| `6`  | `TaskStatusAssertDone`      | 断言完成                 |
| `7`  | `TaskStatusAssertNodata`    | 没有数据，断言未取到数据 |
| `8`  | `TaskStatusAssertTooLarge`  | 数据太多，未进行断言     |
| `10` | `TaskStatusAssertException` | 断言异常                 |
| `11` | `TaskStatusAbandoned`       | 已废弃                   |
| `13` | `TaskStatusRetryRunning`    | 重放中                   |
| `14` | `TaskStatusRetryFail`       | 重放失败                 |
| `15` | `TaskStatusRetryDone`       | 重试完成                 |

### `detail_status`

业务分析通常重点关注 `40`，它表示报告聚合真正结束。

| 值   | 后端常量                                  | 含义                                   |
| ---- | ----------------------------------------- | -------------------------------------- |
| `24` | `TaskDetailStatusReplayDone`              | 回放完成                               |
| `36` | `TaskDetailStatusInAssert`                | 断言中                                 |
| `39` | `TaskDetailStatusDiffAggregateDoneFailed` | 聚合报告失败                           |
| `40` | `TaskDetailStatusDiffAggregateDone`       | 聚合报告生成完成，系统级或沙箱任务结束 |

### 终态判定

| 条件                               | 判定                   |
| ---------------------------------- | ---------------------- |
| `status = 6 && detail_status = 40` | 正常结束               |
| `status = 7`                       | 无流量                 |
| `status ∈ {3, 8, 10, 14}`          | 异常                   |
| `status = 11`                      | 已废弃                 |
| 其它状态                           | 运行中或未到可消费状态 |

## 任务回调状态

第三方回调中的 `process` 字段常见取值：

| 值                        | 含义                   |
| ------------------------- | ---------------------- |
| `process_create`          | 创建任务               |
| `process_retry`           | 重试创建               |
| `process_abort`           | 提前终止               |
| `process_start_replay`    | 启动回放               |
| `process_after_replay`    | 回放结束，尚未断言     |
| `process_start_retry`     | 启动重放               |
| `process_start_rerun`     | 启动重放               |
| `process_after_rerun`     | 重放结束               |
| `process_assert_done`     | 断言结束               |
| `process_no_data`         | 没有数据               |
| `process_aggregate_start` | 开始生成报告           |
| `process_aggregate_done`  | 完成生成报告           |
| `process_done`            | 最终结束状态，可消费   |
| `process_abandoned`       | 废弃任务               |
| `process_mark_done`       | 用户完成全部 diff 确认 |

## 单条流量回放失败码（`failed_reason`）

DIFF 流量上的 `failed_reason` 是单条流量发送阶段的回放错误码：`0` 表示没有发送失败，
非 `0` 表示该流量回放失败。单条流量的权威值从
`ftf task flow get --task-id <id> --pid <pid>` 返回的 `data.diff.failed_reason` 读取。任务级
`failed_reason_count` 是错误码计数分布，method 报告的 `log_id_classify_map` 用于按错误码定位
流量；聚合字段用于发现和对账，不能替代单条 Flow 详情中的值。

源码锚点（权威来源）：`pdi-qa/ftf_nova_utils/biz/model/replay_error.go` 中的
`ReplayErrorCode`、`replayErrorCodeNames` 和 `ResolveReplayErrorInfo`。当前目录镜像其中的静态码
和已知 ByteMesh 目录；核实时应以任务对应版本的该文件为准。

### 使用边界与证据优先级

- 本目录用于解释错误码、定位大致责任组件和提供首轮排查方向，不单独证明根因。
- 同一错误码只能作为候选预分组；`err_msg`、责任组件、触发条件或失败机制不同的流量必须拆分。
- 任务对应的请求、响应、状态码、日志、Trace、部署、配置和代码是更强的直接证据；与本目录
  冲突时，以这些任务级证据为准，并说明目录仅提供了初始线索。
- `UnknownError`、各组件 `*UnknownError`、未登记的 `901xxx` 和其它未识别数字都是兜底分类，
  不能作为最终根因。在同一诊断预算内检查一个代表样本和一个可比反例，并各补一次可获得的
  `err_msg` 脱敏摘要、回放日志、请求/响应、outbound、部署/配置或相关代码证据。证据不再增加、
  达到预算、限流或连续超时时停止，标记“根因未定位”、已排除范围与唯一补证动作；禁止无界
  扩页、扩大日志时间窗或重复查询同一 selector。

### 编码范围与通用责任边界

| 范围            | 位置       | 通用含义                                               | 通用处理                                                       |
| --------------- | ---------- | ------------------------------------------------------ | -------------------------------------------------------------- |
| `100000-199999` | `core`     | 回放核心流程失败                                       | 检查任务、流量配置及回放服务日志                               |
| `200000-299999` | `proxy`    | 跨环境回放代理失败                                     | 检查目标环境与代理可用性，再按代表日志定位                     |
| `300000-399999` | `mocker`   | Mocker 处理失败                                        | 检查 Mock 配置、Mocker 状态和 outbound 证据                    |
| `400000-499999` | `vanguard` | Vanguard RPC 代理失败                                  | 除 `400001` 先核对 IDC 外，提供任务、日志和时间由 FTF 平台排查 |
| `900000-900999` | `biz`      | 被测业务服务回放失败                                   | 检查部署、实例、请求、响应与业务日志                           |
| `901001-909999` | `biz`      | ByteMesh 错误，实际 Mesh 码为 `failed_reason - 900000` | 结合错误正文中的 `cds_key`、方法、IP 和子类型排查              |
| 其它非零值      | `unknown`  | 未识别的回放错误                                       | 不下结论，按未知错误继续取证并在必要时升级平台                 |

### 静态错误码

| `failed_reason` | 类型                        | 含义                             | 首轮处理建议                                              |
| --------------: | --------------------------- | -------------------------------- | --------------------------------------------------------- |
|             `0` | `OK`                        | 回放成功                         | 不计入回放失败清单                                        |
|            `-1` | `UnknownError`              | 未知回放错误                     | 继续查 `err_msg`、回放日志和请求/响应，不以“未知错误”结案 |
|        `100000` | `InternalUnknownError`      | 回放服务内部未知错误             | 查 core 日志与上下游错误链，不以兜底类型结案              |
|        `100001` | `ValidationError`           | 任务或流量参数校验失败           | 核对任务 ID、协议、请求数据和回放环境                     |
|        `100002` | `DuplicateError`            | 流量已被任务消费，重复回放被丢弃 | 不重复提交；确需重试时使用单条重试能力                    |
|        `100003` | `TaskFinished`              | 任务已结束，不能继续消费流量     | 创建新的回放任务后验证                                    |
|        `100004` | `ReachedFlowLimit`          | 任务达到流量数量限制             | 调整流量上限或新建任务                                    |
|        `100005` | `UnimplementedProtocol`     | 当前协议不支持回放               | 核对流量协议与 FTF 支持范围                               |
|        `100006` | `BeforeReplayError`         | 回放前置处理失败                 | 结合前置处理日志定位具体步骤                              |
|        `100007` | `BeforeEditError`           | 回放前置脚本执行失败             | 检查脚本语法、参数和返回值                                |
|        `100008` | `SelectInstanceError`       | 查询被测服务回放实例失败         | 检查目标环境实例与实例选择日志                            |
|        `100009` | `GetIDLConfigError`         | 获取 RPC 回放 IDL 配置失败       | 核对被测服务 BAM IDL 配置                                 |
|        `100010` | `MessageDecodeError`        | MQ 回放消息解析失败              | 核对录制消息内容和协议配置                                |
|        `100021` | `AfterEditError`            | 回放后置脚本执行失败             | 检查脚本语法、参数和返回值                                |
|        `100022` | `AfterReplayError`          | 回放后置计数或状态更新失败       | 查回放后处理、计数和状态更新日志                          |
|        `100023` | `SaveDiffError`             | 保存回放 DIFF 结果失败           | 查 DIFF 持久化链路和平台日志                              |
|        `200000` | `ProxyUnknownError`         | 跨环境回放代理未知失败           | 继续查代理响应和日志，不以兜底类型结案                    |
|        `200011` | `ProxyTimeout`              | 跨环境回放代理请求超时           | 核对目标环境、代理状态和超时证据                          |
|        `200012` | `ProxyConnectionRefused`    | 跨环境回放代理拒绝连接           | 核对代理监听、网络与目标环境                              |
|        `200013` | `ProxyConnectionClosed`     | 跨环境回放代理连接关闭           | 查连接关闭时点与代理日志                                  |
|        `200014` | `ProxyEOF`                  | 跨环境回放代理连接异常结束       | 查响应完整性和代理日志                                    |
|        `200015` | `ProxyStatusCode`           | 跨环境回放代理返回异常状态码     | 读取实际状态码与响应正文后定位                            |
|        `200016` | `ProxyInvalidResponse`      | 跨环境回放代理返回空或非法响应   | 检查原始响应和协议解析日志                                |
|        `300000` | `MockerUnknownError`        | Mocker 未知失败                  | 继续查 Mock 配置、outbound 和 Mocker 日志                 |
|        `300001` | `MockerDiscoveryError`      | 发现 Mocker 实例失败             | 检查服务发现与 Mocker 实例状态                            |
|        `300002` | `MockerInvalidInstance`     | Mocker 实例地址无效              | 核对实例地址和服务发现结果                                |
|        `300003` | `MockerCacheError`          | 缓存 Mock 数据失败               | 检查 Mock 数据、缓存和 Mocker 日志                        |
|        `300004` | `MockerCollectError`        | 收集 Mock 回放结果失败           | 检查结果收集链路与 Mocker 日志                            |
|        `300011` | `MockerTimeout`             | Mocker 请求超时                  | 核对 Mocker 状态、负载和超时配置                          |
|        `300012` | `MockerConnectionRefused`   | Mocker 拒绝连接                  | 核对实例可达性和监听状态                                  |
|        `300013` | `MockerConnectionClosed`    | Mocker 连接关闭                  | 查连接关闭时点和服务日志                                  |
|        `300014` | `MockerEOF`                 | Mocker 连接异常结束              | 查响应完整性和服务日志                                    |
|        `300015` | `MockerStatusCode`          | Mocker 返回异常状态码            | 读取实际状态码和响应正文                                  |
|        `300016` | `MockerInvalidResponse`     | Mocker 返回空或非法响应          | 检查原始响应和反序列化日志                                |
|        `400000` | `VanguardUnknownError`      | Vanguard 未知失败                | 不以兜底类型结案，交由 FTF 平台结合日志定位               |
|        `400001` | `VanguardUnsupported`       | 目标 IDC 不支持 Vanguard 回放    | 先核对目标 IDC；确认无误仍失败再升级 FTF 平台             |
|        `400011` | `VanguardTimeout`           | Vanguard 请求超时                | 提供任务 ID、回放日志 ID 和发生时间给 FTF 平台            |
|        `400012` | `VanguardConnectionRefused` | Vanguard 拒绝连接                | 提供任务 ID、回放日志 ID 和发生时间给 FTF 平台            |
|        `400013` | `VanguardConnectionClosed`  | Vanguard 连接关闭                | 提供任务 ID、回放日志 ID 和发生时间给 FTF 平台            |
|        `400014` | `VanguardEOF`               | Vanguard 连接异常结束            | 提供任务 ID、回放日志 ID 和发生时间给 FTF 平台            |
|        `400015` | `VanguardStatusCode`        | Vanguard 返回异常状态码          | 保留实际状态码和响应摘要并升级 FTF 平台                   |
|        `400016` | `VanguardInvalidResponse`   | Vanguard 返回空或非法响应        | 保留原始响应摘要并升级 FTF 平台                           |
|        `900000` | `BizUnknownError`           | 被测业务服务未知失败             | 继续查业务响应、日志、部署和代码，不以兜底类型结案        |
|        `900001` | `BizInvalidProtocol`        | 被测服务回放协议无效             | 核对回放协议与服务实际协议                                |
|        `900002` | `BizInvalidData`            | 被测服务回放请求数据无效         | 核对请求结构、必填字段和反序列化错误                      |
|        `900003` | `BizInvalidIDL`             | 被测服务 IDL 配置不可用          | 核对两侧 IDL 分支、主文件、include 和 BAM 已发布版本      |
|        `900004` | `BizServiceNotFound`        | 被测服务未部署                   | 确认服务已部署到目标环境                                  |
|        `900005` | `BizNoAvailableInstances`   | 被测服务没有可用实例             | 检查目标环境、集群和 IDC 实例                             |
|        `900006` | `BizBeforeEditError`        | 业务原因导致回放前置脚本失败     | 结合脚本与业务日志定位                                    |
|        `900007` | `BizACLForbidden`           | 被测服务 ACL 拒绝回放请求        | 核对回放服务到被测服务的 ACL 权限                         |
|        `900011` | `BizTimeout`                | 被测服务请求超时                 | 查业务耗时、下游依赖和超时配置                            |
|        `900012` | `BizConnectionRefused`      | 被测服务拒绝连接                 | 查服务监听、部署和网络可达性                              |
|        `900013` | `BizConnectionClosed`       | 被测服务连接关闭                 | 查实例状态和连接关闭日志                                  |
|        `900014` | `BizEOF`                    | 被测服务连接异常结束             | 查响应完整性和业务日志                                    |
|        `900015` | `BizStatusCode`             | 被测服务返回异常状态码           | 读取实际状态码、响应和业务日志                            |
|        `900016` | `BizInvalidResponse`        | 被测服务返回空或非法响应         | 检查原始响应、协议和序列化日志                            |
|        `900021` | `BizAfterEditError`         | 业务原因导致回放后置脚本失败     | 结合脚本与业务日志定位                                    |

### 已知 ByteMesh 动态错误码

`901xxx` 的类型统一为 `BizMeshError`。下表只列源码已登记的 Mesh 四位码；其它 `901xxx`
只说明进入了 ByteMesh 错误兜底，不能据此确定具体根因。

| `failed_reason` | 含义                                               | 首轮处理建议                                                                  |
| --------------: | -------------------------------------------------- | ----------------------------------------------------------------------------- |
|        `901112` | 下游没有健康节点                                   | 按错误中的 `cds_key` 核对健康实例、熔断和摘除状态                             |
|        `901113` | 获取下游实例列表失败                               | 核对服务发现能否返回实例列表                                                  |
|        `901115` | 创建连接池失败，远端连接失败                       | 核对 `cds_key`、目标 IP、端口可达性、连接池和 TLS；不要直接归因为实例数量不足 |
|        `901116` | 超过连接资源限制                                   | 核对下游连接数与资源上限                                                      |
|        `901117` | 没有可用节点                                       | 核对可用节点和路由是否命中空实例集合                                          |
|        `901118` | 传输层错误，常见于 TLS 握手                        | 核对 TLS 和传输层配置                                                         |
|        `901201` | 连接下游超时                                       | 核对网络、实例负载和连接耗时                                                  |
|        `901204` | RPC 调用整体超时                                   | 核对方法处理耗时与超时配置                                                    |
|        `901301` | 协议错误，常见于下游 PSM 或 request base info 缺失 | 核对下游 PSM 和 `Base` 字段                                                   |
|        `901303` | 反序列化错误，常见于协议或 IDL 不匹配              | 核对流量协议、服务协议和 IDL                                                  |
|        `901501` | 服务发现失败，典型为 endpoint 列表为空             | 按 `cds_key` 核对目标集群 endpoint                                            |
|        `901601` | 访问控制拒绝                                       | 按错误子类型分别核对严格授权、服务鉴定或匿名上游的身份注入与 ACL              |
|        `901602` | 按降级配置比例丢弃流量                             | 核对方法降级规则及本次流量是否预期命中                                        |
|        `901604` | 超过 QPS 限流                                      | 核对方法级限流规则、当前流量和是否预期触发；错误码本身不能证明规则误配        |
|        `901605` | host 或 cluster-key 级熔断                         | 核对下游熔断状态与错误率                                                      |
|        `901606` | 动态过载保护拒绝                                   | 核对下游负载和过载保护状态                                                    |
|        `901607` | 压测流量被拒绝                                     | 核对压测标记与被测服务压测配置                                                |
|        `901608` | Kirin 鉴权被拒绝                                   | 核对调用身份和 Kirin 鉴权配置                                                 |
|        `901609` | 跨域鉴权被拒绝                                     | 核对调用区域与跨域合规配置                                                    |
|        `901610` | 请求体过大                                         | 核对请求体大小限制                                                            |
|        `901611` | 响应体过大                                         | 核对响应体大小限制                                                            |
|        `901612` | 自适应限流拒绝（BBR）                              | 核对持续错误率与自适应限流状态                                                |
|        `901613` | 故障注入拒绝                                       | 核对故障注入规则是否命中回放流量                                              |
|        `901701` | 被调方主动关闭连接                                 | 核对目标实例异常退出或重启                                                    |
|        `901702` | 主调方主动关闭连接，仅 Mesh 日志可见               | 结合 Mesh 日志定位主动关闭原因                                                |
|        `901703` | 主调方远端关闭连接，仅 Mesh 日志可见               | 结合 Mesh 日志定位远端关闭原因                                                |
|        `901704` | 主调方本地关闭连接，仅 Mesh 日志可见               | 结合 Mesh 日志定位本地关闭原因                                                |
|        `901801` | 边缘代理 ACL token 解析失败                        | 核对 EdgeProxy 白名单、EPKey 与 ACL token                                     |
|        `901802` | 边缘代理 ACL token 验证失败                        | 核对 EdgeProxy 白名单、EPKey 与 ACL token                                     |
|        `901803` | 边缘代理权限认证失败                               | 核对 EdgeProxy 访问白名单                                                     |
|        `901804` | 同 DC/Region 服务不允许走边缘代理                  | 核对调用是否应使用跨 Region/Unit 边缘代理                                     |
|        `901805` | 边缘代理反向代理白名单认证失败                     | 核对目标服务反向代理白名单                                                    |
|        `901806` | 边缘代理 EPKey 未找到                              | 核对 EPKey 和边缘代理配置                                                     |
|        `901901` | 染色请求被拒绝                                     | 核对流量染色标记与被测服务入流量配置                                          |

## 触发与流量来源

### `trigger_type`

| 值  | 含义           | CLI 语义值                |
| --- | -------------- | ------------------------- |
| `0` | 平台手动触发   | `manual`                  |
| `1` | 第三方 OpenAPI | `third-party` / `openapi` |
| `2` | 定时任务       | `schedule` / `cron`       |
| `3` | CI             | `ci`                      |
| `4` | 调试触发       | 暂无专门 CLI 语义值       |
| `5` | 基准任务       | 暂无专门 CLI 语义值       |

### `case_filter_mode`

| 值  | 含义                           |
| --- | ------------------------------ |
| `0` | 实时流量                       |
| `1` | 场景流量                       |
| `2` | 历史流量                       |
| `3` | 手动圈选流量，部分创建接口出现 |
| `4` | 第三方流量                     |
| `6` | 智选流量                       |
| `7` | 自定义流量                     |

`ftf plan execute` 和 `ftf task create` 对外只接受 `realtime`、`scene`、
`non-realtime`、`third-party`，分别映射为 `0`、`1`、`2`、`4`。其它数字只用于解释
存量 API 数据，不作为这两个创建命令的可选值。

### `flow_source`

| 值                           | 含义                 |
| ---------------------------- | -------------------- |
| `sdk`                        | SDK 录制的实时流量   |
| `bytecopy`                   | ByteCopy 录制流量    |
| `thirdparty` / `third_party` | 第三方注入流量       |
| `bits`                       | Bits 平台注入        |
| `debug`                      | 调试来源             |
| `manual` / `case_set`        | 用户手动选择或用例集 |

## 方法与协议

### `interface_type`

| 值  | 含义       | CLI 语义值 |
| --- | ---------- | ---------- |
| `0` | 未声明类型 | `unknown`  |
| `1` | 读接口     | `read`     |
| `2` | 写接口     | `write`    |

### `protocol`

| 值          | 含义                   |
| ----------- | ---------------------- |
| `http`      | HTTP 协议              |
| `thrift`    | Thrift RPC             |
| `mysql`     | MySQL DB 出流量或 Mock |
| `redis`     | Redis 出流量或 Mock    |
| `rocketmq`  | RocketMQ               |
| `tcc`       | TCC 配置外调           |
| `byteconf`  | ByteConf 配置外调      |
| `dolphin`   | Dolphin 相关           |
| `bizmethod` | 业务自定义方法         |

### 接口唯一键

| 协议     | 唯一键规则                                    |
| -------- | --------------------------------------------- |
| `thrift` | `method`                                      |
| `http`   | `method_HTTPMETHOD`，例如 `/api/v1/demo_POST` |
| 其它协议 | `method`                                      |

`method_list` 或深层 `replay_method_list` 中需要稳定标识接口时，优先保持和后端唯一键规则一致。

## 环境与回放

### IDC 字段

| 字段                          | 大小写 | 示例              | 说明               |
| ----------------------------- | ------ | ----------------- | ------------------ |
| `ReplayIDC` / `BaseReplayIDC` | 大写   | `LF`, `HL`, `SG1` | 回放与基准回放机房 |
| `ByteCopyIdc`                 | 小写   | `lf`, `hl`, `sg1` | ByteCopy 采集机房  |

### `host_env`

| 值       | 含义     |
| -------- | -------- |
| `online` | 线上环境 |
| `ppe`    | PPE 环境 |
| `boe`    | BOE 环境 |

### `replay_mode`

| 值  | 含义           |
| --- | -------------- |
| `0` | 普通回放       |
| `1` | Diffy 双跑对比 |

### `limit_mode`

| 值  | 含义         |
| --- | ------------ |
| `0` | PSM 维度限流 |
| `1` | 任务维度限流 |

## Mock 与外调

### `mock_enable`

| 值  | 含义        |
| --- | ----------- |
| `0` | 不开启 Mock |
| `1` | 开启 Mock   |

### `next_decision`

| 值  | 含义                    |
| --- | ----------------------- |
| `0` | Mock 未命中时不直连下游 |
| `1` | Mock 未命中时直连下游   |

### `call_scene`

| 值     | 含义              |
| ------ | ----------------- |
| `diff` | diff 回放对比场景 |
| `case` | 普通用例场景      |

## Assertion 相关

| 字段                                 | 值           | 含义         |
| ------------------------------------ | ------------ | ------------ |
| `type`                               | `inbound`    | 主调断言     |
| `type`                               | `outbound`   | 外调断言     |
| `scope`                              | `base`       | 基准侧       |
| `scope`                              | `replay`     | 回放侧       |
| `scope`                              | `all`        | 全部         |
| `conjunction` / `preRuleConjunction` | `and` / `or` | 规则组合逻辑 |

### Assertion 配置

| 字段                 | 值  | 含义         |
| -------------------- | --- | ------------ |
| `configType`         | `0` | 默认配置     |
| `configType`         | `1` | 强制忽略     |
| `configType`         | `2` | 自定义配置   |
| `needDiff`           | `0` | 不参与 diff  |
| `needDiff`           | `1` | 参与 diff    |
| `ignoreKeyAddOrLost` | `1` | 忽略回放新增 |
| `ignoreKeyAddOrLost` | `2` | 忽略回放缺失 |
| `ignoreKeyAddOrLost` | `3` | 忽略数组新增 |
| `ignoreKeyAddOrLost` | `4` | 忽略数组缺失 |

## diff 聚类标注原因（`opType`）

diff cluster 对象的 `opType` 字段表示该聚类被平台/人工标注成什么原因；`opType=0` 或缺失表示“未处理过”。这是 diff 聚类专用的编码空间，和上文任务级 `status`（例如 `status=8` 是 `TaskStatusAssertTooLarge`）**不是同一套编码**，不要跨表套用。

CLI 的 `--annotation-op-type` 语义值、JSON 输出里的 `opTypeKey` / `opTypeLabel` 都以本表为准，源码落点是 `src/services/ftf/annotation_op_types.ts` 的 `FTF_CLUSTER_OP_TYPES`。

| `opType` | 后端常量                 | CLI 语义值（`key`）     | 含义（`label`）                    | 分析口径                               |
| -------- | ------------------------ | ----------------------- | ---------------------------------- | -------------------------------------- |
| `0`      | `OP_INIT`                | `unannotated`           | 未处理                             | 默认待分析聚类                         |
| `1`      | `OP_SYS_BUG`             | `system-bug`            | 系统BUG                            | 真实缺陷，重点排查                     |
| `2`      | `OP_BIZ_CHANGE`          | `biz-change`            | 业务变更                           | 结合本分支改动确认是否符合预期         |
| `3`      | `OP_FTF_NOISE`           | `recognition-error`     | 识别错误（断言错误）               | FTF 断言侧误判，非业务问题             |
| `4`      | `OP_MANUAL_TASK_INVALID` | `task-invalid`          | 人工标识任务无效                   | 人工判定任务无效                       |
| `5`      | `OP_EXCEPTION`           | `exception`             | FTF系统异常                        | 平台异常，非业务问题                   |
| `6`      | `OP_CONFIRMING`          | `confirming`            | 确认中                             | 尚在人工确认                           |
| `7`      | `OP_FTF_NOISE_AUTO`      | `system-noise-auto`     | 系统噪音（策略识别）               | 策略自动识别的噪音，可降噪             |
| `8`      | `OP_FTF_NOISE_EQRMWQRK`  | `system-noise-template` | 系统噪音（模板识别）               | 噪音模板配置命中的无需分析字段，可降噪 |
| `9`      | `OP_FTF_LOW_RISK`        | `low-risk`              | 低风险自动确认                     | 平台自动判定低风险                     |
| `10`     | `OP_STABILITY`           | `stability`             | 稳定性问题                         | 稳定性相关，非功能回归                 |
| `11`     | `OP_FILTER`              | `filter-field`          | 过滤字段                           | 被配置过滤的字段                       |
| `31`     | `OP_ASSERTION_FILTER`    | `case-noise`            | 断言侧case过滤（平台问题）         | 平台侧 case 过滤，非业务问题           |
| `32`     | `OP_ASSERTION_MAX_SIZE`  | `big-json`              | 流量JSON过大未执行断言（平台问题） | 因流量过大未断言，非业务问题           |

- `opType=7` 与 `opType=8` 都是“系统噪音”，区别只在识别来源：`7` 是策略自动识别，`8` 是噪音模板配置命中。二者都属于无需业务分析的降噪项，不要读成“系统BUG”。
- 只有 `opType=1(system-bug)` 才是真实系统缺陷；`opType=3/5/31/32` 是 FTF 平台侧问题，`opType=7/8/10/11` 是噪音或非功能项，分析时都应与 `1` 区分开。

## similar diff 标注来源（`operateUser`）

similar diff 对象的 `operateUser` 字段承载“这条 diff 的标注者/标注来源”。它是 `String` 类型，**不是 Java enum**：绝大多数取值是后端 `Common.java` 里的 `static final String` 哨兵常量，另有两个裸字面量与一批经 open 接口写入的具名来源，剩下则是自由格式的真实用户名，全部靠字符串比较区分。

判断某个取值代表什么来源，最权威、无遗漏的单一出处是后端 `SimilarDiffHistory.getSourceDesc()`：它枚举了全部哨兵值 + `default` 分支「人工标注」。**本表镜像自 `getSourceDesc()`，新增来源以后端为准。**

第一类 · 历史/标注同步哨兵（后端 `getHistorySyncOperateUsers()`）：

| `operateUser`                   | 含义（`getSourceDesc`） | 说明                                          |
| ------------------------------- | ----------------------- | --------------------------------------------- |
| `from_history`                  | 历史继承                | 早期/简单路径，从历史记录继承标注             |
| `from_history_same_branch`      | 同分支历史继承          | reduce 阶段命中同分支历史                     |
| `from_history_inherited_branch` | 继承分支历史继承        | reduce 阶段命中继承分支历史                   |
| `from_history_same_demand`      | 同需求历史继承          | reduce 阶段命中同需求历史                     |
| `from_history_all_branch`       | 全分支历史继承          | reduce 阶段当前环境无分支信息时，跨全分支继承 |
| `from_label_sync_same_branch`   | 同分支标注同步          | 标注接口按同分支同步过来的标注                |
| `from_label_sync_same_demand`   | 同需求标注同步          | 标注接口按同需求同步过来的标注                |

第二类 · FTF 平台内部降噪哨兵（`Common.java` 常量，属 `getSystemOperateUsersExcludedFromHistoryQuery()`）：

| `operateUser`   | 含义（`getSourceDesc`） | 说明                                           | 关联 `opType`                         |
| --------------- | ----------------------- | ---------------------------------------------- | ------------------------------------- |
| `from_strategy` | 策略识别                | 策略自动识别降噪                               | `opType=7`（`system-noise-auto`）     |
| `from_formwork` | 模板识别                | 噪声模板识别降噪                               | `opType=8`（`system-noise-template`） |
| `from_branch`   | 主干/Base Compare 降噪  | base/main 分支对比降噪，**不是**同分支历史同步 | —                                     |

第三类 · 外部智能归因写入（open 接口，中国交易与广告智能归因能力）：

| `operateUser`          | 含义                                                  | 说明                                 |
| ---------------------- | ----------------------------------------------------- | ------------------------------------ |
| `ecom_life_ai_denoise` | 中国交易与广告智能归因能力识别并标注（inbound diff）  | 经 open 接口写入，标注 inbound diff  |
| `order_avalon`         | 中国交易与广告智能归因能力识别并标注（outbound diff） | 经 open 接口写入，标注 outbound diff |

第四类 · 非用户兜底字面量（裸字面量，未在 `Common.java` 定义为常量）：

| `operateUser`      | 含义                   | 说明                          |
| ------------------ | ---------------------- | ----------------------------- |
| `from_third_party` | 第三方（外部回调）标注 | 经 assert-sender 集成写入     |
| `system`           | 未传标注人时的默认兜底 | 请求未携带标注人时的 fallback |

其余取值（真实用户名）：以上都不匹配时，`operateUser` 即真实的人工标注操作人用户名（或触发 AI 标注的人），对应 `getSourceDesc()` 的 `default` 分支「人工标注」；来源于当前登录用户 / 请求参数（手动标注取 `userInfo.getUsername()`，AI 标注取 `param.getUserName()`）。

- 降噪来源联动：`ecom_life_ai_denoise` / `order_avalon` / `from_strategy` / `from_formwork` 都属自动降噪标注，区别在写入方——前两者是外部业务系统经 open 接口回写（中国交易与广告智能归因），后两者是 FTF 平台内部策略/模板识别；`from_strategy` / `from_formwork` 分别对应 `opType=7` / `opType=8`（见上「diff 聚类标注原因」表）。
- 相关字段：响应里还有 `originOperateUser`（当 `operateUser` 被同步哨兵值覆盖时，保留的原始真实操作人）和 `aiOperateUser`（AI 标注操作人）；三者含义不同，前端展示来源时用 `operateUser` 走 `getSourceDesc()`。当前 CLI 透传 `operateUser` 与 `operateTime`（标注时间字符串），`originOperateUser` / `aiOperateUser` 未纳入 schema。
