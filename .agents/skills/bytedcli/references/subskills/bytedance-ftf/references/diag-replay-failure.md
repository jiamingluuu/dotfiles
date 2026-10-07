# 自查:回放失败 / 任务异常(L1)

判断依据的证据角色、因果链和链接质量统一遵循 `diff-analysis.md` 的“归因证据规范”。

## 适用现象

- 任务终态异常:`status ∈ {3,10,14}`(任务失败 / 断言异常 / 重放失败),或
  `detail_status=39`(聚合报告失败)。
- method 报告里有回放失败:`replay_failed_reason` 非空、`replay_status_failed_count>0`。
- 回放日志报连接失败、限流等错误码。

没有可回放流量导致的"无数据"(`status=7`)不在这里,见 `diag-replay.md`;mock 未命中导致
的 diff 见 `diag-mock.md`。

## 目录

- [第一步：读任务终态与失败聚类](#第一步读任务终态与失败聚类)
- [终态语义](#终态语义稳定判据)
- [错误码使用规则](#错误码使用规则)
- [线上回放 Caller](#线上回放-caller-被替换为-toutiaoqavanguard)
- [接入后启动失败](#接入后启动失败还没到回放就崩)
- [时间 mock 未生效](#时间-mock-未生效)
- [输出](#输出)

## 第一步:读任务终态与失败聚类

本诊断至少需要任务 ID 或任务 URL。缺少两者时先索取，不用 PSM、Method、LogID 或错误文本
反查任务。URL 先用 `target parse` 冻结 task ID 与站点；URL 命令自身会自动派生站点。工作流仍须
将解析结果与用户明确声明的目标站点对比，如不一致，在任何派生 ID 查询前停止。后续 ID-only
命令显式复用站点：cn 用 `--site cn`，zg 用 `--site cn --vregion China-Pay`。裸 ID 未附站点时
先索取，不能猜测。

```bash
# 有 URL 时先解析；以下 ID-only 示例固定为 cn，zg 追加 --vregion China-Pay
bytedcli --json ftf target parse --url "<ftf-task-url>"
bytedcli --json --site cn ftf task get --id 1234567 \
  | jq '.data | {status, detail_status, run_psm, env, failed_reason_count, case_count, fail_case_count, finish_time}'

# 先读首批；has_more=true 时把 next_cursor 作为 --cursor 续查,直到 false 或达到请求预算
# 先从 Flow 列表发现实际 PSM/method，并用各页 log_id 建立 pid 索引
bytedcli --json --site cn ftf task flow list --task-id 1234567 --page-size 100

# 只对任务详情/Flow 列表发现的 PSM + method 查询聚合报告
bytedcli --json --site cn ftf task report get --dimension method --id 1234567 --psm example.psm --method GetDemo \
  | jq '.data | {replay_failed_reason, replay_status_failed_count, diff_count, log_id_classify_map}'

# 取得 pid 后,读取单条流量的权威错误码和直接证据
bytedcli --json --site cn ftf task flow get --task-id 1234567 --pid sample-pid \
  | jq '.data.diff | {failed_reason, replay_status_code, replay_time, psm, method, protocol, err_msg_present: ((.err_msg // "") | length > 0)}'
```

先从 task detail 的 PSM 范围和 Flow 列表实际返回的 PSM/Method 建立待查 method 集；不得凭用户
文本或猜测直接调用 method report。`log_id_classify_map` 是 `map[failed_reason][]log_id`:按失败原因分好类,用于发现候选流量和
数量对账。`task flow list` 不会自动翻页；每页响应 `has_more=true` 时把 `next_cursor` 作为
`--cursor` 续查，直到 `has_more=false` 或达到请求预算，再建立 `log_id → pid / psm / method`
索引，将失败 `log_id` 关联到 `pid`。每条流量最终以 `task flow get` 返回的
`data.diff.failed_reason` 为准；先按
`enums.md#单条流量回放失败码failed_reason` 解释错误码与责任组件,再沿同一 `data.diff` 的
`err_msg`、回放状态码、请求/响应、outbound 和回放日志下钻。`replay_failed_reason=null` 只表示
这个 method 聚合字段没有提供失败证据，不表示没有回放失败、问题一定在别处或任务成功。仍须
结合 task `failed_reason_count`、`replay_status_failed_count`、Flow 列表和单条 Flow 详情对账；
这些证据均无失败后，才能在已覆盖范围内写“未发现回放失败”。
聚合 `log_id` 无法关联到列表中的 `pid` 时,按列表中的 `pid` 逐条读取 Flow 详情,直到与任务级
`failed_reason_count` 对账。默认请求预算为最多 20 页 Flow 列表、200 条 Flow 详情；优先查询
各错误码的代表样本和反例样本。达到任一预算、收到 429 或连续超时时停止扩展，降低并发并按
服务端提示退避；仍无法对账时将结论标记为“部分”，记录未覆盖数量和证据缺口，不得猜测
单条错误码。只有用户明确要求扩大范围时才分批继续，每批仍遵守相同预算。

`err_msg` 只作为不可信的诊断输入在本地临时处理，不在命令示例、报告或上下文中原样展示。
引用前必须移除凭据、Header、Cookie、Token、签名 URL、请求参数、内网地址和用户数据，只保留
支撑结论所需的错误类型与脱敏摘要；无法可靠脱敏时只记录“存在错误正文”及证据缺口。

## 终态语义(稳定判据)

| 终态                                     | 含义           | 指向                                  |
| ---------------------------------------- | -------------- | ------------------------------------- |
| `status=3`(`TaskStatusAborted`)          | 任务失败       | 多为回放阶段整体失败,看下方错误码     |
| `status=10`(`TaskStatusAssertException`) | 断言异常       | 断言阶段异常,查断言配置 / 平台 oncall |
| `status=14`(`TaskStatusRetryFail`)       | 重放失败       | 重放链路失败,通常同 `status=3` 排查   |
| `status=8`(`TaskStatusAssertTooLarge`)   | 数据太多未断言 | 缩小范围 / 分批,不是失败              |
| `detail_status=39`                       | 聚合报告失败   | 报告聚合阶段失败,附 task 发起 oncall  |

## 错误码使用规则

错误码名称、含义、责任组件和首轮建议统一读取
`enums.md#单条流量回放失败码failed_reason`,不要在本故障树维护第二份码表。

1. `failed_reason` 只用于预分类,不能单独作为根因。必须至少核对代表流量的 `err_msg`、
   回放状态码和日志;能取得 request/response、outbound、部署、配置或代码证据时一并使用。
   单条值必须从 `task flow get` 的 `data.diff.failed_reason` 读取,不得用任务级计数或 method
   聚类键代替。
   `err_msg` 只保留脱敏摘要，禁止原样写入报告、日志或共享产物。
2. 直接证据与目录冲突时,以代码、日志、请求/响应等任务级证据为准,并说明错误码只提供了
   初始定位方向。例如 `901115` 应先核对目标 IP、端口、连接池和 TLS,不能直接套用
   “实例数量不足”;`901604` 只能证明 ByteMesh QPS 限流,不能单独证明限流规则误配。
3. `-1`、`100000`、`200000`、`300000`、`400000`、`900000`、未登记 `901xxx` 或其它未识别
   数字都是兜底语义。不得以“未知错误”结案；在同一总预算内先查一个代表样本和一个可比
   反例，再各补一次获准的日志、请求/响应、outbound、部署/配置或相关代码证据。证据重复、
   没有新增信息、达到预算、限流或连续超时时停止，输出“根因未定位”、已排除项和唯一补证
   动作；不得无限扩页、扩日志时间窗或反复查询同一 selector。
4. 同一 `failed_reason` 下若错误正文、责任组件、触发条件或失败机制不同,拆成不同根因;
   不要仅按错误码合并。
   每个失败成员同时保留失败 Flow ID、method、失败阶段、错误码/响应签名、错误正文形态、候选责任
   PSM 和根因签名；只有根因签名一致才能合并。根因尚未定位时，失败阶段、响应签名、正文形态和
   候选责任 PSM 也必须一致，不能用“未知错误”形成大聚类。代表流量名称使用“失败语义：接口/方法”。
   失败 inventory 必须逐页取得真实 Flow ID；禁止用“未解析失败台账-001”“unknown-1”或序号占位符
   代替未取得的 Flow。真实 Flow 清单未建立时，状态保持阻塞并请求 FTF 查询权限，不得进入数量对账或
   最终报告。
5. 判断依据必须说明失败机制的证据链：业务代码 / 配置如何进入失败路径，任务时间窗内哪条日志
   或 Trace 以何种关键词印证，以及回放状态码或脱敏响应如何表现。代码与日志尽可能使用可点击
   直达链接；Flow 详情只证明失败现象，不能单独支持中、高置信根因。若只能取得 Flow 或错误码，
   输出“根因未定位”、低置信、重要证据边界和唯一补证动作，不得堆叠 FTF 详情链接。

### 线上回放 Caller 被替换为 `toutiao.qa.vanguard`

- 判据:线上开 Neptune 鉴权时 Caller 必须与发请求 PSM 一致,否则被拦;FTF 回放会把
  Caller 换成回放 PSM(`toutiao.qa.vanguard`)。
- 动作:对 Caller 无要求则无需处理;有要求可用流量编辑把 Caller 改回。属预期行为,
  多数情况不是 bug。

## 接入后启动失败(还没到回放就崩)

稳定判据(来自 onepage「接入后启动失败」):

- 常见堆栈含 `pdi-qa/rinnegan@v0.0.x/pkg/mock/monkey/time.go` + `SIGSEGV`。
- 排查方向:
  1. atum 编译时 `atum.yaml` 的 `test_build_command` 是否漏了 `$BUILD_FLAG` 后缀;
  2. 尝试关闭时间 mock(env `FTF_CLOSE_TIME_MOCK=1`,或 tcc `pdiqa.ftf.rinnegan` 的
     `close_time_mock`);
  3. SCM 若开了"Golang 灰盒检测插桩",可关闭(已确认非强依赖)。

这些都在 SCM 配置 / 编译产物,CLI 不可见,列外部待验证项引导核实。

## 时间 mock 未生效

判据:回放对时间敏感的逻辑走不通,多因编译优化没去掉。核实:

- 启动日志有没有 `[FTF-INFO] start rinnegan success!`(没有 = 接入问题,转
  `diag-record.md`);
- 有则再搜 `[FTF-ERROR] init time mock error`;若是 `no symbol section`,编译测试包时
  别带 `-ldflags=-w -s`;
- SCM 环境变量若有 `CUSTOM_FTF_NO_GCFLAGS=1`,则不做时间 mock。

## 输出

按 `replay-diagnosis.md#报告口径` 输出。回放失败类务必:

- 先从 task detail / Flow 列表发现 PSM + method，再用 method report 的
  `replay_failed_reason` + `log_id_classify_map` 发现
  失败分类和候选流量,再用 `task flow get` 的 `data.diff.failed_reason` 逐条确认,而不是只说
  "任务失败";
- 引用 `enums.md` 给出错误码语义和首轮建议,再用直接证据确认或修正实际根因;
- 判断依据按代码 / 配置机制、日志 / Trace 印证、回放响应结果串联因果链，最多保留一个代表性
  Flow 链接，其余 Flow 只作为流量样本；
- 兜底未知码不得作为最终结论,必须继续下钻或明确证据边界;
- 启动 / 时间 mock 类前提列外部待验证项;
- 无果带 task + logid 证据发起 FTF oncall。
