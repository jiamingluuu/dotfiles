# FTF Diff 查询与聚类标注参考

目录：[用途](#用途) · [JSON 输出](#json-输出约定) · [查询命令](#查询命令) · [参数](#参数) · [字段口径](#字段口径) · [API 形态](#api-形态) · [验证](#验证方法)

## 用途

新增 FTF diff 查询只能通过 TeslaX v1 gateway `/ftf/...` 获取证据。当前文档中的 assert `/nova/...` 深度 value/diff 明细属于仓库基线存量能力，仅为兼容已有命令保留并等待迁移；禁止新增命令复用或扩展这些接口，也不得在 v1 请求失败后自动回退。gateway 默认使用办公网 host，`BYTEDCLI_NETWORK_PROFILE=prod` 时按 FTF 分区切换到生产网 host；输出中的 Tesla-X task/flow 页面链接仍使用对应页面域名。
当需要读取 task 上下文、diff cluster、flow diff、字段值、标注状态或相似 case，或对显式选中的 diff cluster 做人工标注时，可以使用这些命令。

task/flow URL 查询命令会把 Tesla-X URL 解析成稳定 selector，再串联 task 上下文、diff cluster、record value、相似 case 和 outbound diff。`diff attribute get/list` 是精查某条 inbound record 的直接入口。
解析后冻结 `site` 和 selector。URL 命令自身会自动派生站点；工作流仍须将解析结果与用户明确
声明的目标站点对比，如不一致，在任何派生 ID 查询前停止。继续传 URL 的命令保留 URL 路由；
后续若只传派生 ID，必须显式携带全局路由：cn 用 `--site cn`，zg 用
`--site cn --vregion China-Pay`。只有裸 ID 且站点未知时先索取，不从 ID 或默认配置猜测。

本文件覆盖 diff 分析取数以及显式聚类标注，不覆盖 FTF task 创建、plan execute、retry、stop 等其他写操作。

查询输出的语义背景（录制回放模型、outbound 采集源差异、证据可见性边界）见 `domain-model.md`；本文件只覆盖命令、参数与 JSON/字段形态。

## JSON 输出约定

task/flow harness 命令在 JSON 顶层输出 Agent 归因需要的稳定字段，同时保留完整来源数据：

- `task diff-cluster list/get` 和 `task analyze` 的 `cluster.raw` 保留单个后端聚类对象，
  `full_result` 保留完整编排结果，`full_result.sources[].data` 保留各查询的原始业务响应。
- `task evidence get` 输出统一证据包，包含 task meta、psm_task_id 映射、任务/PSM/接口汇总统计、top method、top diff 聚类、代表样本和原始来源 endpoint/参数，适合多个 agent 对同一 task 做同题分析时共用。传 task URL 时 CLI 会自动应用 URL 里的 `diffReasons` 筛选；没有 URL 筛选时默认只取未处理 diff 聚类；需要看全部时显式传 `--annotation-op-type all`。后端 similar diff 列表接口当前不支持服务端分页，CLI 会拉全量后按 URL 或显式参数过滤，再按 `--page` / `--page-size` 返回本页证据。JSON 字段名可能仍叫 `aggregates`，用户报告里统一写“汇总统计”。
- `task diff-cluster list` / `task analyze` 输出 `clusterSelection`：`total` 是当前筛选口径下、未应用 `--top` / `--top-n` 截断前的 diff 聚类数；`returned` 是本次返回或详细分析的聚类数；`remaining` 是剩余未展开聚类数；`truncated=true` 表示报告需要输出“剩余未分析聚类表”。
- `task diff-cluster list/get` / `task analyze` 的每个 `cluster` 都会尽量输出 `displayPath` 和 `flowDiffUrl`。报告正文优先使用 `displayPath` 作为 path；优先使用 `flowDiffUrl` 作为代表流量详情链接。缺字段时不要编造链接。
- `diff path-profile get` 按 task + psm + method + diff path 聚合 base/replay value 分布，输出 distinct count、top values、样本 log_id 和随机值置信度依据；它只提供依据，不直接定性。
- `diff array-check get` 对一个 diff path 或 similarDiffId 拉 base/replay array，尝试按显式或推断候选主键排序后比较；输出候选主键、排序后是否一致、`failedSamples` 失败样本，并标注需要业务语义确认。若 FTF 将同一数组 path 拆成 base-only / replay-only 两类元素级 diff 聚类，命令会额外输出 `pairedElementAlignment`，用于说明两侧元素能否按业务键一一对齐、对齐后是否仍有字段差异。
- `flow diff get --with-values` 顶层保留 `base` / `replay` 和 origin/deepParse 的存在性、数量摘要，
  完整 record value 位于 `recordValue.raw` / `full_result.recordValue`。value 抽取以未回填的
  `*Origin` 为准（详见「取值以 origin 为准」一节），因此单侧缺失能被如实标注，而不是被
  对齐视图掩盖成“两边相同”。
- `flow diff get --with-outbound` 和 task 类命令的 `--with-outbound` 顶层输出
  `outbound.summary`、`outboundCount/newOutboundCount`、`baseOutboundPreview/replayOutboundPreview`
  和摘要 `outboundDiff`；完整 outbound 对象位于 `outbound.raw` / `full_result.outbound`。
- `flow diff get --diff-id/--similar-case-id/--diff-number` 会选中一条 value diff，并按 diff path 从 record value 中抽取 base/replay 值。每侧输出 `present`（后端是否认为该侧存在此 key）、`found`（是否真的抽到值）、`value` 与可选 `reason`：`present:false` + `reason`（如 `DIFF_LOST(回放组缺失)`）表示后端确认该侧缺失，不要当成噪音；`present:true` 但 `found:false` 表示“本该有却没抽到”，属于取值异常而非确认缺失。
- `task analyze` 会把 task 上下文、diff cluster、value diff、record value 和 similar cases 串起来，适合从 task URL 直接产出可分析 JSON；默认 `--direction inbound`。传 task URL 时 CLI 会自动应用 URL 里的 `diffReasons` 筛选；没有 URL 筛选时只分析页面“标注原因”未处理过的聚类。
- `task diff-cluster get --with-values` 未显式传 `--direction` 时会自动按 inbound 聚类查询；显式传 `--direction all/outbound` 同时带 value 相关参数会报错。优先读取 JSON 的 `inbound.samples`。`valueSource=record_value` 表示值来自 record value + diff path 抽取；`valueSource=similar_case_list` 表示 value diff 明细没有命中该聚类，样本来自聚类代表 case。样本里的 `basePresent/replayPresent` 用于区分“该侧值存在”与“未抽到/不存在”，不要只凭字段缺省过度解释。
- 页面“标注原因”列对应聚类对象的 `opType` 字段；`opType=0` 或缺失表示“未处理过”。`--annotation-op-type unannotated` 等价于 `0`，`--annotation-op-type all` 表示不按人工标注原因过滤。不要为了“保险”固定传 `--annotation-op-type unannotated` 覆盖用户当前 URL；只有明确要覆盖 URL 筛选时才传该参数。JSON 里的 `annotationOpTypeSource` 会说明筛选来自 `url`、`explicit`、`default` 还是 `none`。`opType` 数字↔语义值的权威映射见 [enums.md](./enums.md) 的「diff 聚类标注原因（`opType`）」表；不要凭数字大小或历史印象臆测（例如 `opType=8` 是「系统噪音（模板识别）」而非「系统BUG」）。
- `task diff-cluster list/get` 的每个 `cluster` 会输出 `operateUser`（标注者/标注来源）与 `operateTime`（标注时间字符串）。`operateUser` 需要结合 `opType` 一起读：`opType` 说明“标成了什么原因”，`operateUser` 说明“谁标的、来自哪条链路”。`operateUser=null` 表示尚无标注者（常见于 `opType=0` 未处理，此时可能仍有 `aiOpType` 的 AI 建议）；`from_formwork` / `from_history*` / `from_strategy` / `ecom_life_ai_denoise` / `order_avalon` 等是平台哨兵值而非真人。哨兵值与真实用户名的完整区分见 [enums.md](./enums.md) 的「similar diff 标注来源（`operateUser`）」表；不要把哨兵值当成人工标注的证据。

解释 outbound 查询结果时注意：

- `request diff` 表示回放 outbound 请求参数和录制 outbound 请求参数不同，需要判断是否符合本分支预期。
- `not match recorded outbound` 通常表示录制侧没有采集到对应 outbound，或录制调用次数少于回放调用次数。
- 同 protocol/method 有多个候选时，平台会基于请求 diff 和时间顺序匹配；已匹配的 outbound 默认不会重复使用。

## 取值以 origin 为准

`record getValue` 每一侧返回两种形态：`base`/`replay` 是后端为“对齐式展示”生成的 `*WithHidden` 视图，会把只在对侧出现的 key **回填**到本侧占位；`baseOrigin`/`replayOrigin` 才是未回填的真实响应。`--with-values` 的取值以 `*Origin` 为准（`*Origin` 为空时才回退到对齐视图）。

- 判断“某侧是否缺失”看的是 diff 结构信号，而不是对齐视图里 key 是否存在：某侧 `pathStr` 为空且 `hiddenPath` 非空，即该侧被回填、真实缺失，输出 `present:false` + `reason`。
- 因此“归一化 `base`/`replay` 两边逐字节相同”不能证明无差异；单侧缺失（DIFF_LOST / DIFF_ADD 族，含数组元素级 5/6/11/12）只有对比 `*Origin` 或读 `present/reason` 才能看出。

## 鉴权

这些 API 通过 `X-Jwt-Token` header 使用 ByteCloud JWT 鉴权，不使用 Tesla RM token。
请先执行 `bytedcli auth login`，或通过环境变量提供 JWT：推荐使用通用变量 `BYTEDCLI_USER_CLOUD_JWT`。

## 查询命令

```bash
bytedcli --json ftf target parse --url "<ftf-url>"

bytedcli --json ftf task evidence get --url "<ftf-task-url>" --page 1 --page-size 20

bytedcli --json --site cn ftf task get --id 1234567

bytedcli --json ftf task evidence get \
  --url "<ftf-task-url>" \
  --page 1 \
  --page-size 20 \
  --top-n 10 \
  --sample-size 3

bytedcli --json ftf diff path-profile get \
  --url "<ftf-task-url>" \
  --psm example.psm \
  --method GetDemo \
  --sample-size 20

bytedcli --json ftf diff array-check get \
  --url "<ftf-task-url>" \
  --similar-diff-id sample-similar-diff \
  --key sample_id \
  --sample-size 5

bytedcli --json ftf task diff-cluster list \
  --url "<ftf-task-url>" \
  --direction all \
  --method GetDemo \
  --sort diff-count-desc \
  --top 20

bytedcli --json ftf task analyze \
  --url "<ftf-task-url>" \
  --direction inbound \
  --method GetDemo \
  --with-values \
  --sample-values 3 \
  --with-similar-cases \
  --top-n 10

bytedcli --json ftf task diff-cluster get \
  --url "<ftf-task-url>" \
  --similar-diff-id sample-similar-diff \
  --with-values \
  --sample-values 3 \
  --with-similar-cases \
  --with-outbound

bytedcli --json --site cn ftf task diff-cluster mark \
  --task-id <task_id> \
  --direction inbound \
  --similar-diff-ids <similar_diff_id_1>,<similar_diff_id_2> \
  --annotation-op-type system-bug

bytedcli --json ftf task diff-cluster mark \
  --url "<ftf-task-url>" \
  --direction outbound \
  --similar-diff-ids <similar_diff_id> \
  --annotation-op-type stability \
  --remark <remark> \
  --yes

bytedcli --json ftf flow diff get \
  --url "<ftf-flow-diff-url>" \
  --with-values \
  --with-outbound

bytedcli --site cn ftf diff similar \
  --psm-task-id 123456701001 \
  --method GetDemo

bytedcli --site cn ftf diff attribute get \
  --record-id 1234567_sample_record

bytedcli --site cn ftf diff attribute list \
  --record-id 1234567_sample_record \
  --similar-case-id sample-similar-case \
  --diff-id sample-diff \
  --page 1 \
  --page-size 5

bytedcli --site cn ftf diff attribute list \
  --record-id 1234567_sample_record \
  --similar-case-id sample-similar-case \
  --diff-id sample-diff \
  --all

bytedcli --site cn ftf diff attribute list \
  --record-id 1234567_sample_record \
  --similar-case-id sample-similar-case \
  --diff-id sample-diff \
  --task-id 1234567
```

使用 `get` / `list` 作为稳定入口。

## 聚类标注

`task diff-cluster mark` 只接受一个顶层 task selector、一个方向和 1 至 100 个显式 `similarDiffId`。公开写枚举只允许 `system-bug`、`biz-change`、`recognition-error`、`exception`、`confirming`、`stability`；不要传数字、查询专用枚举或 `direction=all`。

- 默认仅实时查询并展示预检结果，不提交写请求。确认顶层 task ID、唯一 PSM task ID、方向、目标 ID、当前 `opType`、新标注和 remark 后，才可在同一命令后增加 `--yes`。
- 预检会忽略 task URL 上的 `diffReasons` 筛选，确保每个显式 ID 都按所选方向完整核对；任一 ID 缺失、方向不符、匹配不唯一，或 task 映射到零个/多个 PSM 时整批失败且不写入。
- `--yes` 最多提交一次方向对应的批量写请求，不拆批、不自动重试。请求超时、断连、权限拒绝、非 `200` 业务码或响应格式异常均为 `unknown`；不要直接重试，先用只读 `list/get` 查看当前状态，但回查不能证明本次写入结果。
- `accepted` 仅表示服务返回明确的 `code=200` 且空 `data`，不表示每个 ID 都已修改，也不证明跨任务传播、异步刷新或 callback 已完成。

`ftf diff similar --psm-task-id <id> --method <method>` 查询**单个 method** 下的 similar diff group（后端 `GET /nova/task/getMethodSimilarDiffs/?taskId=&method=`）。它与 `task diff-cluster list/get` 的分工是：

- `diff similar` 按 `method` 过滤，只回该 method 的 similar diff，适合已知具体 method、想快速看这一个接口的 similar diff 概览；当前命令原样透传后端响应，不做精简或字段裁剪。
- `task diff-cluster list/get`（底层 `GET /nova/task/getSimilarDiffListByTaskId?taskId=&type=`）
  覆盖整个 task 的全部 method，并输出稳定结构化字段；后端完整聚类对象和查询响应分别位于
  `cluster.raw`、`full_result.sources[].data`。

`diff similar` 返回的每条 similar diff 对象与 `task diff-cluster` 共享同一套字段口径：`similarDiffId` / `diffPath` / `method` / `protocol` / `diffCount` / `logCount` / `diffRate` / `opType` / `analyseResult` / `operateUser` 等。字段的用户可读译法与维度归属见 [domain-model.md](./domain-model.md) 的「术语与表达规范」；`opType`（标注原因编码）见 [enums.md](./enums.md) 的「diff 聚类标注原因（`opType`）」表；`operateUser`（标注者/标注来源，含 `from_history*` / `from_strategy` / `ecom_life_ai_denoise` / `order_avalon` 等哨兵值与真实用户名的区分）见 [enums.md](./enums.md) 的「similar diff 标注来源（`operateUser`）」表。

`diff attribute list` 传入 `--task-id`（顶层 FTF task id）后进入 replay logid attribution 模式：CLI 会自动拉取该 diff 聚类的全部相似 case，再拉取该 method 的 flow list，用「录制原始 log_id」把每条 diff 明细 join 到对应回放流量，输出被测侧回放 logid（`logid_comparison`）与基线侧回放 logid（`logid_benchmark`）。输出里 `replay_logids` 是去重后的回放 logid 列表（含 `detailCount`），`items` 保留每条明细的 `recordingLogId` / `replayLogId` / `baseLogId`。注意：一条回放流量可能因数组内多个字段缺失产生多条 diff 明细，因此 `total_details`（明细行数）通常大于 `replay_logids` 的去重条数。`psm` / `method` 默认从 record info 自动解析，仅在需要覆盖时显式传 `--psm`。

如果需要机器可读输出，使用全局 JSON 模式：

```bash
bytedcli --json --site cn ftf diff attribute get \
  --record-id 1234567_sample_record
```

## 参数

| 参数                        | 是否必填     | 说明                                                                                                                     |
| --------------------------- | ------------ | ------------------------------------------------------------------------------------------------------------------------ |
| `--record-id`               | 是           | 复合 inbound record id。case id 从第一个 `_` 之前的前缀派生。                                                            |
| `--similar-case-id`         | `list` 必填  | 相似 case 标识。                                                                                                         |
| `--diff-id`                 | `list` 必填  | diff 标识。                                                                                                              |
| `--page`                    | 否           | 页码，默认 `1`。                                                                                                         |
| `--page-size`               | 否           | 分页大小，默认 `5`。                                                                                                     |
| `--all`                     | 否           | 自动翻页获取全部相似 case，最多拉取 50 页。                                                                              |
| `--task-id`                 | 否           | 顶层 FTF task id。传入后 `list` 进入 replay logid attribution 模式，为每条 diff 明细解析被测/基线回放 logid。            |
| `--psm`                     | 否           | 仅在 replay logid attribution 模式下用于覆盖自动解析的 PSM；缺省时从 record info 自动解析。                              |
| `--business`                | 否           | 可选业务标识。为空时不会带入 API 请求。                                                                                  |
| 全局 `--site` / `--vregion` | ID-only 必填 | cn：`--site cn`；zg：`--site cn --vregion China-Pay`。URL 自动派生站点；工作流对比明确目标，冲突时在派生 ID 查询前停止。 |

URL harness 常用参数：

| 参数                   | 适用命令                                                     | 说明                                                                                         |
| ---------------------- | ------------------------------------------------------------ | -------------------------------------------------------------------------------------------- |
| `--url`                | `target parse` / `task *` / `flow diff get`                  | Tesla-X FTF task 或 flow diff URL。                                                          |
| `--direction`          | `task analyze` / `task diff-cluster list/get`                | `inbound`、`outbound` 或 `all`；`mark` 只允许单一 `inbound` 或 `outbound`。                  |
| `--annotation-op-type` | `task evidence get` / `task analyze` / `task diff-cluster *` | 查询命令接受 `unannotated`、`all`、语义值或多值；`mark` 只接受六个公开写枚举，且不接受数字。 |
| `--similar-diff-ids`   | `task diff-cluster mark`                                     | 必填，逗号分隔的显式 ID；去重后必须为 1 至 100 个。                                          |
| `--remark`             | `task diff-cluster mark`                                     | 可选；空白值不发送。                                                                         |
| `--yes`                | `task diff-cluster mark`                                     | 缺省只预览；传入后才提交一次批量标注请求。                                                   |
| `--with-values`        | `task analyze` / `task diff-cluster get` / `flow diff get`   | 拉取 base/replay value 摘要。                                                                |
| `--sample-values`      | `task analyze` / `task diff-cluster get`                     | 每个 cluster 的代表性 value diff 样本数。                                                    |
| `--with-similar-cases` | `task analyze` / `task diff-cluster get`                     | 拉取并汇总 inbound 相似 case。                                                               |
| `--with-outbound`      | `task analyze` / `task diff-cluster get` / `flow diff get`   | 拉取 outbound diff 上下文。                                                                  |

`task diff-cluster get` 的 value 相关输出：

- `inbound.samples`：面向 agent 的稳定样本入口，包含 `source`、`path`、`recordId`、`logId`、`baseValue`、`replayValue`。
- `inbound.valueSource=record_value`：通过 `getValueDiffDetail` 匹配到聚类，再从 `getRecordValue` 按 path 抽值。
- `inbound.valueSource=similar_case_list`：`getValueDiffDetail` 没有返回能匹配该聚类的 value diff，CLI 改用 `getSimilarCaseListByDiffId` 的代表样本。
- `representativeValueDiffs`、`representativeSamples` 是兼容字段；新报告优先读 `samples`，并在结论里说明取值来源。

P0 diff 分析取证命令常用参数：

| 参数                     | 适用命令                                                               | 说明                                                                                                      |
| ------------------------ | ---------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------- |
| `--url` / `--task-id`    | `task evidence get` / `diff path-profile get` / `diff array-check get` | 二选一。task URL 会先解析 Tesla-X 上下文，并自动带入 URL 上的 `diffReasons` 筛选；task id 直接查询 task。 |
| `--psm`                  | 三个命令                                                               | 只分析某个 replay PSM。                                                                                   |
| `--method`               | 三个命令                                                               | 只分析某个 method。                                                                                       |
| `--top-n`                | `task evidence get` / `diff path-profile get`                          | 控制 top method / cluster 或聚合后返回的 top path profile。                                               |
| `--page` / `--page-size` | `task evidence get`                                                    | 对本地过滤后的 top diff 聚类分页；用于避免一次 evidence 输出过大。                                        |
| `--sample-size`          | 三个命令                                                               | 每个 cluster 或检查项拉取的代表样本数。样本量只作为置信度参考。                                           |
| `--diff-path`            | `diff path-profile get` / `diff array-check get`                       | 精确 diff path 过滤或数组检查 selector。                                                                  |
| `--similar-diff-id`      | `diff path-profile get` / `diff array-check get`                       | 精确 similarDiffId 过滤或数组检查 selector。它是内部定位 ID，用户报告正文优先用 method + diff path 表达。 |
| `--key`                  | `diff array-check get`                                                 | 显式排序主键；支持逗号分隔的组合键。未传时由命令基于元素字段推断候选键。                                  |

## 字段口径

`diffCount` / `logCount` / `aggregate` / `similarDiffId` 等字段的用户可读译法、维度归属，以及"累计 diff 明细条数 ≠ 流量数"的辨析，统一见 `domain-model.md` 的"术语与表达规范"，本文件不重复定义。命令层面：`--similar-diff-id` 是内部定位 ID，复现 / 精确过滤时需要它，报告正文不用它做主语（用法见上方参数表）。

## Flow diff 链接拼接

生成 task 级分析报告时，如果某个 diff 聚类或代表样本具备完整流量上下文，应在正文附一个可点击的代表流量详情链接，方便用户直接打开 Tesla-X 复核。不要用 `similarDiffId` 代替用户可打开的链接。

优先读取 `task diff-cluster list/get` 或 `task analyze` JSON 里的 `cluster.flowDiffUrl`。只有旧版本 CLI 或特殊输出缺少该字段时，才按下面规则手工拼接。

链接格式（host 跟随任务所在 Tesla-X 部署：cn 用 `tesla-x.bytedance.net`，zg 用 `tesla-x-zg.bytedance.net`）：

```text
https://tesla-x.bytedance.net/space/<space_id>/f_app/task/new/diff/<task_id>/<psm_task_id>/<method_base64>/<protocol>/<log_id>
```

字段来源：

| URL 片段          | 来源字段                               | 说明                                                                                   |
| ----------------- | -------------------------------------- | -------------------------------------------------------------------------------------- |
| `<space_id>`      | task URL / target parse 的 `spaceId`   | 没有 spaceId 时不要编造链接。                                                          |
| `<task_id>`       | task id                                | 例如 `1234567`。                                                                       |
| `<psm_task_id>`   | PSM task id                            | 例如 `123456701001`。                                                                  |
| `<method_base64>` | `method` 做 UTF-8 base64 后 URL encode | 例如 `/aftersale/apply_page_dynamic` -> `L2FmdGVyc2FsZS9hcHBseV9wYWdlX2R5bmFtaWM%3D`。 |
| `<protocol>`      | cluster / flow 的 protocol             | 常见为 `http`；没有证据时不要猜。                                                      |
| `<log_id>`        | 代表流量原始 log_id                    | 使用不带 method 后缀的原始 log_id，并 URL encode。                                     |

Node.js 拼接示例：

```js
function buildFlowDiffUrl({ spaceId, taskId, psmTaskId, method, protocol, logId }) {
  const methodBase64 = Buffer.from(method, "utf8").toString("base64");
  return `https://tesla-x.bytedance.net/space/${encodeURIComponent(spaceId)}/f_app/task/new/diff/${encodeURIComponent(
    String(taskId),
  )}/${encodeURIComponent(String(psmTaskId))}/${encodeURIComponent(methodBase64)}/${encodeURIComponent(
    protocol,
  )}/${encodeURIComponent(logId)}`;
}
```

报告正文推荐写法：

```text
`/aftersale/apply_page_dynamic` 的 `data->...` 覆盖 1 条流量，累计记录 4 条 diff 明细。代表流量详情：<flow-diff-url>。
```

注意：

- 这是“代表流量详情链接”，不是 diff 聚类永久链接；同一个 diff 聚类覆盖多条流量时，选择最能说明问题的一条代表流量。
- 只生成 `/f_app/task/new/diff/` 新版路由；历史 `/f_app/task/diff/` 链接仅作为输入兼容，不得用于报告或示例。
- `method_base64` 一定要 URL encode。base64 可能包含 `/`、`+`、`=`，直接拼进 path 可能导致路径被拆坏。
- 如果只有 `recordId`，优先用 CLI 已解析出来的 `method/logId`；不要靠字符串猜测。必须从 `recordId` 反推时，确认 `recordId` 形如 `<psm_task_id>_<log_id>_<method-without-leading-slash>`，只去掉 method 的开头 `/`，内部 `/` 保留。
- 缺少 `spaceId`、`protocol` 或原始 `logId` 时，不生成链接；改为给 task URL + method + path + 代表 log_id。
- 回放失败聚类（按 `method × failed_reason` 从 `log_id_classify_map` 聚合）没有 `similarDiffId`，同样用上面这个**不带 `similarDiffId` 后缀**的 flow-diff 链接格式，代表 `log_id` 从该聚类的 `log_id_classify_map` 取；硬性约束见 `task-diff-triage.md` 的“聚类必须附「查看 diff 明细」链接”。

## API 形态

- TeslaX v1，task 上下文：`GET /ftf/query/task?taskId={taskId}`
- TeslaX v1，task aggregate：`POST /ftf/task/aggregate/report/task`，payload 带 `task_id` 和 `no_re_aggregate=true`
- TeslaX v1，PSM aggregate：`POST /ftf/task/aggregate/report/psm`
- TeslaX v1，method aggregate：`POST /ftf/task/aggregate/report/method`
- 存量待迁移，task diff cluster：`GET /nova/task/getSimilarDiffListByTaskId?taskId={psmTaskId}&type=inbound|outbound`
- 存量待迁移，cluster 代表样本：`GET /nova/valuediff/getSimilarCaseListByDiffId/{psmTaskId}?type={direction}&similarDiffId={similarDiffId}&page={page}&size={size}`
- 存量待迁移，record value：`GET /nova/record/getValue/{psmTaskId}`
- 存量待迁移，outbound diff：`GET /nova/valuediff/getOutbound`
- 存量待迁移，相似 case：`GET /nova/valuediff/getSimilarCaseList/{caseId}`
- 存量待迁移，Inbound diff 详情：`GET /nova/valuediff/getValueDiffDetail/{caseId}`

两个接口都会通过 query 参数接收 `recordId`，并从同一个复合 record id 中派生 `{caseId}`。

## 验证方法

### 本地验证

文档或命令实现变更后，先跑基础校验：

```bash
npm run validate:skills
git diff --check
```

如果涉及 `diff attribute` 命令、参数或 API 拼装逻辑，再跑聚焦单测：

```bash
node --test -r ts-node/register -r tsconfig-paths/register \
  test/api/ftf/client.test.ts \
  test/cli/handlers/ftf/diff_attribution.test.ts \
  test/cli/commands/ftf/ftf.test.ts
```

这些测试能验证：

- `recordId` 会从第一个 `_` 前派生 `{caseId}`。
- `get` 和 `list` 会转发正确参数。
- `page`、`page-size`、`business` 的默认值和空值处理符合预期。
- `--all` 会按页拉取相似 case，并在达到安全页数上限时标记 `truncated=true`。
- 请求会带 `X-Jwt-Token`、Tesla-X `origin` 和 `referer`。

### 真实只读 smoke

真实验证需要一条已经存在 value diff 的复合 inbound `record-id`。格式通常是：

```text
<psm_task_id>_<log_id>_<method-with-slashes-removed>
```

示例占位：

```text
1234567_sample_log_id:sample_call_id:50_SampleMethod
```

先查 diff 详情：

```bash
bytedcli --json --site cn ftf diff attribute get \
  --record-id '1234567_sample_log_id:sample_call_id:50_SampleMethod'
```

期望结果：

- 返回 `code=200`、`message=OK`。
- `data.valueDiffList` 非空。
- 每条 diff 中包含真实的 `diffId` 和 `similarCaseId`。

然后用上一步返回的真实 `similarCaseId` 和 `diffId` 查相似 case：

```bash
bytedcli --json --site cn ftf diff attribute list \
  --record-id '1234567_sample_log_id:sample_call_id:50_SampleMethod' \
  --similar-case-id 'sample-similar-case-id' \
  --diff-id 'sample-diff-id' \
  --page 1 \
  --page-size 5
```

如果需要一次性拉全量相似 case，可以加 `--all`：

```bash
bytedcli --json --site cn ftf diff attribute list \
  --record-id '1234567_sample_log_id:sample_call_id:50_SampleMethod' \
  --similar-case-id 'sample-similar-case-id' \
  --diff-id 'sample-diff-id' \
  --all
```

期望结果：

- 返回 `code=200`、`message=OK`。
- `data.similarCaseList` 非空，或至少返回 `similarCount` / `similarRecordCount`。

不要用占位的 `sample-similar-case` / `sample-diff` 做真实 smoke；平台可能返回 500。必须先通过 `get` 取真实 id，再调用 `list`。
