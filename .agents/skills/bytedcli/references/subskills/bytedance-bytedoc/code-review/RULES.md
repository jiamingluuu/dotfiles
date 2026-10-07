# ByteDoc 业务代码 Review 规则

本文件是 `GUIDE.md` 的规则目录。finding 必须引用 `BDCR-*` ID；流程规则用于保证覆盖和证据边界，不应被伪装成代码缺陷。

## 证据与置信度

- **confirmed**：diff、必要上下文、依赖文件或经授权的线上证据直接证明问题。
- **conditional**：风险依赖未确认的 ByteDoc 版本、流量、数据分布或配置来源。说明触发条件并请求最小证据，不把条件写成事实。索引是否存在未知不属于 conditional finding；按 `BDCR-INDEX-001` 的专门边界只请求 metadata consent 或记录 evidence gap。
- 只有“可能有问题”但说不清触发条件、影响和修复方式时，不输出 finding。
- 注释不能单独证明 client 一定复用、查询一定有索引或 collection 一定很小；应沿构造和调用路径验证。

## 语言适配矩阵

五种语言使用同一套连接、timeout、查询、cursor 结果完整性、索引、DML、DDL 和敏感信息规则。官方依赖的识别必须结合依赖文件；import/header 名可能保留上游命名空间。

| 语言    | ByteDoc 依赖证据                                           | 源码识别要点                                                                                                         | 连接生命周期                                                                                 |
| ------- | ---------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------- |
| Go      | module `code.byted.org/bytedoc/mongo-go-driver`            | import 通常以 `code.byted.org/bytedoc/mongo-go-driver/...` 开头；同时检查 `go.mod/go.sum`                            | 进程/组件级 `*mongo.Client` 注入复用；一次性命令可在进程退出时关闭                           |
| Python  | 安装 distribution `bytedpymongo`                           | 代码仍可能 `import pymongo` 或 `from pymongo ...`，必须检查 requirements、Poetry/Pipenv 配置和 lock，不能只看 import | 模块/应用级 `MongoClient` 复用，不在请求或每条消息里创建/关闭                                |
| Node.js | package `@byted/bytedmongodb`                              | 检查 `package.json` 和 lock；API 名可能与 `mongodb` 接近                                                             | 复用已 connect 的 client/db/collection，不在 handler 中反复 connect/close                    |
| Java    | Maven coordinate `com.bytedance.bytedoc:mongo-java-driver` | Java import 仍可能是 `com.mongodb.*`，必须检查 `pom.xml`、Gradle 配置和 lock/catalog                                 | `MongoClient` 通常由容器管理为 singleton，DAO/repository 只持有引用                          |
| C++     | Blade dependency `bytedoc/mongo-cxx-driver`                | header 仍可能是 `mongocxx/*`，必须检查 BUILD/Blade 依赖                                                              | 多线程服务使用共享 `mongocxx::pool` 并按操作 acquire；不要跨线程共享非线程安全 client handle |

依赖文件不在 diff 中时，读取仓库已有清单的最小上下文。只有源码 import 与依赖清单共同证明使用了上游 driver，才按 `BDCR-SDK-001` 报告；不要因 Python/Java/C++ 的兼容命名空间误报。

Cursor 的错误 API 因语言而异，但 review 目标相同：遍历异常必须向调用方传播，不能把已读取的前半段数据伪装成完整成功结果。Go 使用 `cursor.Next(ctx)` 手动遍历时必须在循环后检查 `cursor.Err()`；`cursor.All(ctx, &result)` 已经通过返回值传递读取错误。Python、Node.js、Java 和 C++ 的遍历通常通过异常或 rejected Promise 传播失败，重点检查宽泛的 catch/except 是否吞掉异常并返回部分结果，不机械要求它们实现 Go 的 `Err()` API。

## BDCR-SCOPE-001 增量覆盖

**类型：流程规则，不作为 finding。**

- 提交前本地 review 必须组合 committed branch diff（适用时）、staged、unstaged 和 untracked 文件。
- untracked 文件直接读取，禁止用 `git add -N` 或 `git add` 改变用户 index。
- `git status --porcelain=v1` 的 `??` 只表示 untracked，不属于 unstaged；untracked 文件不进入 `git diff`，所以 `git diff` 为空时必须记录 `unstaged=false`。
- rename/delete、依赖清单、锁文件中的相关片段也属于覆盖范围。
- 宿主已经提供完整范围时复用宿主，不自行扩大为无目标全仓扫描。

## BDCR-SDK-001 官方 SDK 与接入方式

**默认级别：High；只有证据完整时报告。**

报告条件：

- 生产业务明确依赖上游 Mongo driver，而依赖清单没有 ByteDoc 官方 distribution/module/artifact。
- 代码自行拼接 direct Mongo/Atlas URI、host、Consul endpoint 或认证材料，绕开已生成的 ByteDoc 接入方式。
- SDK 版本、初始化方式与仓库内 `sdk generate` 产物或已确认接入文档明显冲突。

避免误报：

- Python 的 `pymongo` import、Java 的 `com.mongodb.*` import、C++ 的 `mongocxx/*` header 本身不是上游依赖证据，先查依赖清单。
- 测试桩、接口类型适配层和显式隔离的本地单测依赖，不自动按生产风险报告。
- 依赖文件不可见时先读上下文；仍不可确认则记录覆盖缺口，不猜。

## BDCR-CONN-001 Client/Pool 生命周期

**默认级别：High；高 QPS 请求路径反复建连、持续资源泄露或已能推导出 pool 耗尽时可升为 Blocker。**

报告条件：

- HTTP/RPC handler、消息消费函数、DAO 单次调用或循环内创建并关闭 Mongo client。
- 每次请求执行 connect/ping/disconnect，或失败后立即重建 client，导致连接池失效和握手放大。
- 无上限并发重连、无 backoff 的立即重试，或者每次重试都新建一套 pool。
- client 创建成功后，后续 Ping、认证检查、依赖构造或其它初始化步骤失败，但错误路径没有 Disconnect 已创建的 client。
- 由应用生命周期持有的共享 client 被请求、repository 或单个任务关闭，导致其它并发调用继续使用已关闭的 pool。
- session/transaction 创建后，成功、失败、取消或 panic/exception 路径没有执行 `EndSession`；事务失败路径没有按 driver 语义执行 `AbortTransaction` 或确认提交结果。
- C++ 多线程服务直接共享不安全的 client handle，或完全绕开 `mongocxx::pool`。
- C++ 从 pool acquire 的 handle 脱离 RAII 生命周期、被长期缓存或未归还 pool。

避免误报：

- 一次性迁移、CLI、离线脚本可以在进程级创建一次并在退出时关闭；关键是“每进程一次”，不是永不关闭。
- repository 构造出现在请求文件中不等于每请求建连；沿依赖注入和调用方确认实例作用域。
- repository 或 handler 没有调用 Disconnect 不代表泄露；如果 client 由 App/container owner 注入并在 graceful shutdown 统一关闭，这是正确的 owner 分工。
- client 初始化函数把成功创建的 client 返回给调用方时，关闭责任随返回值转移；只在函数自己后续初始化失败时负责清理。
- driver/session helper 已通过 `WithSession`、defer/finally、try-with-resources 或 RAII 覆盖所有退出路径时不报。
- C++ pool handle 由 RAII 对象管理并在作用域结束时自动归还 pool，不要求额外显式 release。
- 仅设置 pool 参数不是问题；结合实例数量、并发和 retry 判断总连接数。

修复方向：先确认资源 owner，再把 client/pool 提升到应用生命周期，启动阶段初始化并验证，DAO 注入复用；client 一旦创建成功就立即建立失败清理责任，只有成功返回后才把 owner 转交给 App/container；关闭动作放到优雅退出；重试复用同一 pool 并使用有上限的指数退避和 jitter。session/transaction 同样在获取后立即建立 `EndSession`/abort 责任。

## BDCR-TIMEOUT-001 Timeout 分层与预算

**默认级别：High；缺少部分配置但调用已有明确上层预算时不直接报告。**

Timeout 至少分三层审查，不能混为一个数字：

1. **调用层 deadline/cancellation**：业务 SLA、请求取消和任务生命周期。例如 Go `context`、Java future/request deadline、Node `AbortSignal`。
2. **driver 网络与连接池**：`connectTimeoutMS`、`socketTimeoutMS`、`serverSelectionTimeoutMS`、`waitQueueTimeoutMS` 等，分别约束建连、socket I/O、server selection 和等待 pool。
3. **服务端执行上限**：`maxTime/maxTimeMS`，由 mongod/mongos 执行侧处理，不等价于客户端等待时间。

不要把每条查询必须设置 context deadline 当作机械规则。Go 代码在调用链已有生命周期控制，并通过官方 driver 的 `socketTimeoutMS`、`waitQueueTimeoutMS` 等限制 I/O/排队时，可以不额外创建短 context；反复套很短的 context 反而会压缩握手和重试预算。反过来，长生命周期后台任务如果所有层都无上限，也应报告。

当 diff 直接拥有 client 构造，却未配置 connect/server-selection/socket/wait-queue 预算，也看不到受控的官方生成配置或 URI 来源时，输出 `conditional` 的 `BDCR-TIMEOUT-001`，并说明需要确认配置来源；不要因为构造参数名叫 `uri` 就假定其中已经包含 timeout。若同一位置还有每请求建连或短 MaxTime，可以合并成一条 finding，但 `ruleIds` 必须同时保留对应规则；合并 finding 的总置信度可以随已确认的主问题，摘要仍须明确 timeout 配置证据尚不可见。

ByteDoc Go 接入还可能出现 `TcpWriteTimeThreshold`、`DialTimeThreshold`、`LimitEveryMS` 等 driver 参数。检查它们是否来自官方生成配置、是否被业务改成异常小值，以及是否与 connect/socket/wait-queue 预算冲突；不要脱离版本和文档编造统一推荐值。

重点问题：

- 上层 deadline 比正常 server selection/握手时间还短，导致健康请求也频繁取消。
- socket/wait queue 无边界，同时业务层立即重试，放大 goroutine/thread/promise 和连接占用。
- server maxTime 很短，但 client deadline 很长且失败后无 backoff 重试，形成持续压力。
- 多层 timeout 的错误分类丢失，所有失败都被当作“数据库慢”并触发重连。

## BDCR-MAXTIME-001 修复版本之前的短 MaxTime 连接池风险

**适用条件：目标 ByteDoc 4.0 mongos 构建严格早于 `4.0.13-286-4`，且 `0 < maxTimeMS < 5000`。两个条件同时成立才报告本规则。默认 Medium；存在高频调用、时延波动或重试放大证据时可升为 High/Blocker。**

`4.0.13-286-4` 是包含修复的首个版本，该版本及之后的版本已修复“短 MaxTime 导致 mongos 向 mongod 获取不到连接”的问题。不能笼统把所有 4.x 或所有短 MaxTime 配置标成此缺陷。

### 版本取证与比较

- 使用目标 mongos 的内核构建版本，例如 `bytedoc get` 返回的 `detail.raw.bin_version_mongos`、`detail.raw.topology.mongos[].bin_version`。SDK 包版本、`svc_version`、数据库服务版本 `1.2` 或单独的 mongod 版本不能代替 mongos 证据。
- 官方 release/repository tag 可去掉开头的 `r` 或 `v`；按十进制数字段比较内核、build、hotfix，不能使用字符串排序，也不能直接套用把连字符当 prerelease 的 SemVer 比较。已给出 build 但未给 hotfix 的正式版本（如 `4.0.13-286`）按 hotfix=0 比较。
- 只有 `4.0`、`4.0.13`，或自定义/无法解析的后缀时，版本证据不完整；请求元数据授权或记录无法判断适用性，不输出本规则的 finding。
- 多个 mongos 混合版本时逐个判断。存在旧构建时只对可能路由到该旧构建的请求说明风险；只有所有相关 mongos 均已确认修复，才能给出整体已修复结论。仅取得部分节点或聚合字段与节点版本冲突时，说明覆盖缺口。

| 已确认的 mongos 版本                       | 短 MaxTime 下本规则的处理                             |
| ------------------------------------------ | ----------------------------------------------------- |
| `4.0.13-273`、`4.0.13-286`、`4.0.13-286-3` | 在修复前，报告潜在连接池风险并说明触发条件            |
| `4.0.13-286-4`、`r4.0.13-286-4`            | 已包含修复，不报告 `BDCR-MAXTIME-001`                 |
| `4.0.13-286-10`、`4.0.13-302`              | 在修复后，不报告 `BDCR-MAXTIME-001`                   |
| 仅 `4.0` / `4.0.13`、未知或不明构建        | 先取证；不把未知版本当成旧版本                        |
| 其它 MongoDB 主版本                        | 不套用本 ByteDoc 4.0 缺陷；有独立证据时按对应规则审查 |

### 风险与误报边界

- 修复前的短 MaxTime 需要结合网络抖动/丢包、慢查询、mongod 负载、跨机房时延等触发条件解释，不能声称每个请求必然失败。同时检查立即重试、反复重建 client/pool 和并发放大。
- `maxTimeMS=0` 表示未设置服务端执行上限，不属于本规则的短 MaxTime；负数/无效值也不按此事故模式解释。
- 已修复版本即使设置 100ms 或 1s，也不得输出本规则、要求为此升级或机械改成 5s。若独立证据表明该值与业务 SLA/实际耗时不匹配，或无边界重试、查询无索引，使用 `BDCR-TIMEOUT-001` / `BDCR-QUERY-001` / `BDCR-INDEX-001` 描述具体问题，不能换个规则 ID 重述已修复的连接池缺陷。
- 版本未知或用户拒绝查证时，只记录 evidence gap，不输出 conditional `BDCR-MAXTIME-001`。没有版本信息不妨碍报告其它由代码直接证明的问题。

## BDCR-QUERY-001 查询边界与代价

**默认级别：High；明确的小型管理集合或受上游唯一键约束时可不报。**

审查：

- 多租户/多业务集合是否包含必要的 tenant/account/business key，且不能由用户输入绕过。
- 返回多条记录的 find/aggregate 是否有可证明的业务边界、分页/limit、时间窗或唯一键；`findOne`、唯一键查询不机械要求 limit。
- sort 是否在过滤后进行；聚合是否尽早 `$match`，是否在无边界输入上 `$lookup/$unwind/group/sort`。
- projection 是否避免读取大 payload；不要把“未写 projection”一律报告，先确认模型大小和调用是否真的需要全字段。
- 无锚点 regex/前导通配、低选择性 `$ne/$nin`、超大 `$in`、用户可控 pipeline、全量 cursor materialization。
- 查询在循环中 N 次执行、批处理没有 chunk，或分页使用高 offset/skip 导致后页扫描放大。

写 finding 时列出实际 filter/sort/range/limit shape 和触发规模。不要只写“可能慢查”。

## BDCR-CURSOR-001 Cursor 释放、错误传播与结果完整性

**默认级别：High；高频路径持续泄露 cursor、已能推导出连接池耗尽，或完整性敏感路径把部分结果当成功时可升为 Blocker。**

报告条件：

- cursor 创建成功后没有建立 `Close` 责任；Go 通常在成功检查后立即 `defer cursor.Close(ctx)`，其它语言使用 finally、context manager、try-with-resources、RAII 或等价机制。
- Decode、业务校验、下游调用、主动 `break`、取消或其它提前 return 路径绕过 cursor Close。
- 代码只检查 `cursor.Err()`，但没有关闭 cursor；错误检查与资源释放是两个独立责任。
- Go 代码使用 `for cursor.Next(ctx)` 遍历，但循环结束后未检查 `cursor.Err()` 就返回成功结果、推进分页水位或提交后续副作用。
- `Decode`、异步迭代或 driver 异常被记录后吞掉，函数仍以 `nil` error、resolved Promise、正常返回值或成功状态返回已读取的部分数据。
- 批处理在确认 cursor 完整结束前更新 checkpoint、offset 或“已完成”状态，导致重试无法补回缺失数据。
- 包装层把“正常耗尽”和“遍历失败”都压成同一个 `false`/空结果，调用方无法判断数据是否完整。
- cursor 跨请求、跨 goroutine/thread 或被放入长期缓存，但没有明确的单一 owner、并发契约和关闭入口。

为什么危险：

- `Next` 返回 `false` 既可能表示正常读完，也可能表示网络、服务端或解码错误；只看循环退出无法区分。
- 错误可能发生在已经成功读取若干条之后。此时返回的 slice/list 看起来合法，但实际只是前缀，容易造成漏单、少算、错误对账或不完整同步。
- 未关闭的 cursor 可能保留服务端 cursor、socket 或连接池资源；高频累积后会表现为 pool wait、超时和连接耗尽。
- `limit`、匹配索引和正确 filter 只能控制查询代价，不能证明 cursor 在传输和解码阶段完整结束。

修复方向：

- cursor 创建成功并确认无错误后立即注册 Close；把 defer/finally 放在最靠近获取资源的位置，覆盖 Decode 失败、提前 return、break 和取消。
- Go 手动遍历在循环后立即检查并返回 `cursor.Err()`；检查通过后才返回结果或推进 checkpoint。
- 可以使用会返回错误的整体读取 API（例如 Go `cursor.All`），但必须检查它的返回错误。
- Python、Node.js、Java 和 C++ 保留 driver 原生异常传播；若业务确实支持 partial result，返回结构必须显式包含“不完整”状态和原始错误，调用方不得按完整成功处理。

避免误报：

- Go `cursor.All(ctx, &result)` 的错误已被检查且 cursor 有 Close 责任，或手动 `Next` 循环后同时明确检查了 `cursor.Err()`。
- Python/Node.js/Java/C++ 没有吞掉异常，driver 的遍历异常会自然向上传播。
- 当前函数返回原始 cursor 或包装后的 stream，并在 API/类型上明确把 owner 转移给上层；上层拥有遍历、错误检查和关闭入口时不报。沿调用链确认，不能只因创建函数内没有 Close 就判断泄露。
- change stream/tailable cursor 是有意的长生命周期资源；只要有明确 owner、取消信号、Close 方法和 graceful shutdown，不因存活时间长而报告。
- driver 文档明确保证特定单文档/完全耗尽路径自动释放时可以记录为低风险证据，但不要用这一点掩盖提前退出路径；优先保留显式 owner。
- best-effort 预览明确返回 `complete=false` 和错误，且调用方不会将其用于对账、状态推进或成功口径。

## BDCR-INDEX-001 查询与索引匹配

**默认级别：High（已证明缺失或不匹配）；索引未知时不直接报告“缺索引”。**

1. 从代码提取 equality、sort、range、projection、collation、partial 条件和数组字段。
2. 发现业务查询后，直接按 `GUIDE.md` 列出目标库/集合及待确认信息，请求 metadata-only 查库授权。不要搜索仓库中的 index migration/声明来判断线上索引是否存在；索引通常由控制台管理。
3. 使用 ESR（equality-sort-range）作为起点，但考虑字段选择性、sort 方向、multikey、hashed、partial/sparse、collation 和前缀复用；ESR 不是无需证据的固定模板。
4. 索引存在不等于一定可用：partial filter、collation、类型不一致、数组路径和 sort/range 顺序都可能使查询不匹配。
5. 只有已确认目标的完整线上索引证据证明没有可用索引时，才输出 confirmed finding。证据缺失时请求授权或记录 gap，不编造索引名，不自动创建索引。
6. 同一目标/集合只取证一次并复用于相关查询；本次 review 已授权获取或用户提供的线上快照，确认来源、目标、时间与完整性后可复用。仓库声明不能替代 live 信息。
7. 综合索引字段顺序、类型、partial/sparse、collation、multikey 与可用 schema/版本判断。元数据没有提供执行计划、数据分布或扫描量时，说明这些限制；不凭索引名称或存在性承诺查询一定快。

主动授权触发器：review 范围内存在业务查询，即请求目标确认与 metadata consent；包括简单点查和看似有匹配仓库声明的查询。按库/集合合并请求；用户已授权相同范围、本次已有有效线上证据或明确拒绝/只要求静态 review 时不重复询问。没有业务查询时，不为索引检查请求查库。

`BDCR-INDEX-001` 只有 confirmed 形态。索引未知时不得输出 conditional `BDCR-INDEX-001`，也不得把候选索引建议伪装成 finding；此时只请求 metadata consent 或记录 evidence gap。确定性的空 filter、无 limit、全量 materialization 等问题继续使用 `BDCR-QUERY-001`，不依赖索引证据。

修复建议给出 query shape 和候选 key 顺序的理由，但明确候选仍需结合数据分布、写放大和现有索引评估。不要把每个查询都变成独立复合索引。

对 confirmed `BDCR-INDEX-001` 必须同时输出 `offer_index_governance` 动作和非空 `indexProposals`，每个 proposal 包含对应代码位置、collection、候选 key pattern、理由以及 `consentScope: dry-run-only`。第一次用户同意只表示可以进入治理流程并生成 dry-run：classic 走 `index-governance`，Volc 走 `mongo-ops`。必须展示预览并再次获得 live 确认，才能提交工单或创建索引。

只有 `BDCR-QUERY-001`、`BDCR-MAXTIME-001` 或索引仍未知时，不得输出 `offer_index_governance` 或 `indexProposals`。索引未知仍使用 `request_metadata_consent`，不得以治理邀请代替证据授权。

## BDCR-WRITE-001 业务 DML 安全

**默认级别：High；空 filter 批量更新/删除或跨租户写入为 Blocker。**

业务应用正常调用 `insertOne/updateOne/deleteOne/bulkWrite` 不需要 bytedcli dry-run，也不需要逐请求人工确认。审查的是：

- filter 是否包含租户/分片和稳定业务键，是否会因空对象、可选参数或 builder 分支退化为空/低选择性条件。
- `updateMany/deleteMany/bulkWrite` 是否有明确业务上限、分批策略、审计和可恢复性。
- upsert 是否有唯一约束，retry 是否会重复插入或重复产生副作用。
- 状态迁移是否幂等，是否检查 matched/modified/deleted count，乐观锁/version 条件是否正确。
- 多文档一致性是否真的需要事务；已有事务时检查 session 传播、超时和重试，不机械要求所有写入加事务。
- retryable writes、超时后的未知提交状态和业务重试是否可能重复执行。

如果 Agent 后续要通过 bytedcli 执行 live 写入，那是执行协议而非代码 finding；转到 `../mongo-ops/GUIDE.md` 做 CLI dry-run 和用户确认。

## BDCR-DDL-001 索引和结构变更位置

**默认级别：Blocker（请求/消费/循环热路径）；受控迁移根据缺口为 High/Medium。**

报告条件：

- 请求 handler、消息消费函数、每次定时任务迭代或 DAO 查询路径调用 `createIndex/createIndexes/ensureIndex/dropIndex/createCollection/drop`。
- 多实例启动会并发执行无锁 DDL，失败被吞掉，或 DDL 与业务流量同时运行且没有治理/回滚方案。
- classic 业务代码或脚本通过 DMS shell 绕过 ByteDoc 索引工单治理。

避免误报：

- 初始化、迁移或运维代码中的 DDL 不是一律禁止。确认它有单次执行入口、幂等、并发串行化、审批/治理、观测、失败恢复和回滚说明。
- 仅存在 index model/声明不等于运行时每请求建索引；沿调用路径确认执行位置。
- review 只指出问题和治理入口。classic 转 `index-governance`，Volc 转 `mongo-ops`；不要在 review 中自动创建索引。

## BDCR-SECRET-001 凭证和敏感数据

**默认级别：Blocker（真实凭证/URI 泄漏）或 High（可触发的日志泄漏）。**

- 不把完整 Mongo URI、用户名密码、token、`SEC_TOKEN_STRING`、临时凭证或包含这些值的 client options 写入日志、异常、metrics、trace、panic/core dump。
- 错误对象可能包含 endpoint/URI 时先结构化提取安全字段；不要直接 `%v`、string interpolation 或序列化整个配置。
- 测试 fixture 也使用 `example.*`/`demo-*` 占位符，不提交真实服务、PSM、库名、IP 或个人信息。
- collection 业务字段是否敏感需结合 schema；经授权读取样本文档后，finding 只保留字段形态并脱敏字段值。

## BDCR-LIVE-001 线上证据最小权限

**类型：流程规则；违规时停止证据采集，不作为业务代码 finding。**

- 发现业务查询后主动列出库和集合信息，合并请求目标确认与 metadata-only 授权；用户同意后读取真实线上信息。无需先搜索仓库索引声明。metadata-only 与 sample-document 必须分别获得用户同意。
- 元数据授权不包含样本文档、slow-query、写入、权限申请或建索引。
- 样本文档只在会改变结论时使用最小 filter/projection/limit，且输出脱敏。
- `site` 由用户确认；backend/vregion 先交给 resolver，只有 `BYTEDOC_AMBIGUOUS` 或 `ASK_USER` 时让用户选择。
- classic `index list` 不得套用到 cloud-native/Volc；没有已验证 backend 路由时报告 unavailable，不切 backend 猜测。
- 用户拒绝、权限不足或 STOP 类错误后继续静态 review，明确 evidence gap，不绕路。

## 规则组合

同一代码片段可以组合规则，但避免重复 finding：

- 每请求新建 client + 1 秒 maxTime + 立即重试：以 `BDCR-CONN-001` 为主；独立超时预算问题用 `BDCR-TIMEOUT-001`，仅确认 mongos 早于 `4.0.13-286-4` 时才追加 `BDCR-MAXTIME-001`。
- 每请求创建 client 且 cursor/client 均未关闭：在一个 finding 中同时引用 `BDCR-CONN-001` 和 `BDCR-CURSOR-001`，说明 client pool、服务端 cursor 和连接占用的累积链路。
- 无租户 filter 的全量 sort 且无索引证据：先报 `BDCR-QUERY-001` 的确定性边界问题；`BDCR-INDEX-001` 只有拿到索引证据后再确认。
- 查询 shape 合理但 cursor 未关闭或 `Next` 循环吞掉终止错误：报 `BDCR-CURSOR-001`；查询有 limit 或匹配索引也不能消除资源和部分结果风险。
- 已确认索引缺失/不匹配：报 `BDCR-INDEX-001`，同时给出候选索引和 `offer_index_governance`；不把第一次同意当成 live 执行确认。
- 热路径 `createIndex`：报 `BDCR-DDL-001`；不要再用 `BDCR-WRITE-001` 重复描述同一结构变更。
- 正常受限 `UpdateOne`：即使没有 CLI dry-run，也不构成 finding；只有 filter/幂等/retry 等语义问题才使用 `BDCR-WRITE-001`。

## 参考资料

- ByteDoc Cloud Docs：连接池与 timeout 参数设置最佳实践，文档标识 `67d8feaab943e4054170e3f3`。
- Lark Wiki：ByteDoc 4.x 短 MaxTime 事故说明，文档标识 `CFIrwX8p4iPbhFks5xqcRni1nsg`。
- ByteDoc Cloud Docs：2026-3 Stable `v4.0.13-286-4` 发布说明，文档标识 `6a856e27b59ed0056a8a9ca8`；其中记录本连接池问题的修复（MR 1091）。适用版本以该修复边界为准。

参考资料用于理解风险前提；最终 finding 仍须以当前代码、当前依赖和经授权的目标环境证据为准。
