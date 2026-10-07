# 自查:outbound mock 未命中 / 外调异常(L1)

目录：[适用现象](#适用现象) · [前置判断](#前置确认该不该有-outbound) · [取证命令](#取证命令) · [故障树](#故障树) · [输出](#输出)

## 适用现象

- 回放日志有 `not match recorded outbound`。
- Tesla-X 回放 case 的 outbound 页右侧没有 mock 数据,或 mock 结果不符合预期。
- 外调报错、mock 后类型断言失败(如 `i.(int64)` 失败)。

本文件解决"mock 这一步为什么没成";采集侧根本没采到 outbound 见 `diag-record.md`
的 "outbound 采集不全";mock 命中但值不同导致的 inbound diff 归因见
`flow-diff-root-cause.md`；判断依据的因果链与深链要求见 `diff-analysis.md` 的“归因证据规范”。

## 前置:确认该不该有 outbound

不是所有任务都期待 outbound mock。先按 `domain-model.md#任务形态判定` 与
`#采集源与证据可见性边界` 判断:

- **系统级任务**:outbound 走真实下游,不注入 mock,本就不期待 outbound mock,别按
  "未命中"排查。
- **采集源 `bytecopy`**:通常不含完整 outbound,拿不到 outbound 不代表有问题。
- 只有 **沙箱 / 混合形态 + `sdk` 采集** 才应重点查 mock 未命中。

## mock 两步原理(判据基础)

outbound mock 分匹配 + mock 两步,完整模型见 `flow-diff-root-cause.md#核心模型`。要点:

1. 匹配:在录制数据里找相同 protocol、method 的 outbound;多个候选按请求 diff 最小 /
   时间顺序匹配;已用过的默认不重复匹配。
2. mock:把匹配到的录制 response 反序列化进回放服务的 response 结构体。

匹配不到 → 返回 error,走业务 error 分支,日志出现 `not match recorded outbound`。

## 取证命令

```bash
# 单条流量 outbound 上下文:mock 是否命中、请求 diff、未使用的录制 outbound
bytedcli --json ftf flow diff get --url "<ftf-flow-diff-url>" --with-outbound \
  | jq '{outbound: .outbound.summary, outboundCount, newOutboundCount}'

# 无 URL 时用 psm_task_id + method + log_id
bytedcli --json --site cn ftf flow diff get --psm-task-id 123456701001 --method GetDemo --log-id sample-logid --with-outbound
```

outbound 查询结果解读(见 `diff-query-reference.md` 的 outbound 说明):

- `request diff`:回放 outbound 请求参数和录制的不同,需判断是否符合本分支预期。
- `not match recorded outbound`:录制侧没采到对应 outbound,或录制调用次数少于回放调用
  次数。
- 同 protocol/method 多候选按请求 diff + 时间顺序匹配,已匹配的默认不重复用。

## 故障树

### A. outbound 页右侧完全没有 mock 数据

稳定判据:被测环境根本没跑起 FTF 产物,或没启动正确 bin。核实:

- 参考 `diag-record.md` 的"服务是否真的起了 record 产物":确认被测包编译了 FTF、
  启动了正确 bin;看 `bootstrap.sh` 启动条件。
- 确认服务启动日志有 `[FTF-INFO] start rinnegan success!`。
- 覆盖率启动条件可能顶掉 FTF 产物启动(BOE 无法 mock),按 onepage「FTF BOE 录制与
  覆盖率兼容」处理。
- 也可能是业务逻辑报错没走到外调:点回放 logID 看日志,用 diff 调试定位。

这些都是产物 / 启动 / 业务日志层面,CLI 看不到,列外部待验证项。

### B. `not match recorded outbound`(有 outbound 但没匹配上)

稳定判据(来自 onepage「mock 失败的情况」),原因通常是录制侧没采到对应 outbound,
或录制调用次数 < 回放调用次数,可在左侧线上 outbound 搜索确认。三类根因:

1. **业务变更 / 两侧代码版本不一致**:采集与回放环境代码逻辑不同 → 属正常业务变更,
   可标注。
2. **录制 / 回放环境差异**导致执行逻辑不同 → 需回放日志 + 调试定位,参考降噪改造。
3. **不支持的组件 / 本地缓存等特殊逻辑** → 见下方 C / D。

判据边界:原因 1 是业务变更可标注;原因 2、3 需借回放日志 + 调试功能坐实,不能只凭
"未匹配"就判代码问题。这与 `flow-diff-root-cause.md#常见根因模式` 的 "mock 未命中"
一致。

### C. 请求外状态无法 mock(需业务改造,外部待验证)

以下都是原理性限制——数据不和单次请求绑定,FTF 默认采不到 / mock 不了,需业务方法级
mock 或改造。CLI 无法证明其接入状态,一律列外部待验证项:

- **协程池未透传 context**:上下文传不过去,子协程外调无法 mock。必须透传 context。
- **tcc 异步获取**:`tcc.AddListener` / 自实现异步写全局变量的配置,默认不 mock;需方法级
  mock 或临时全量同步 tcc 到回放泳道。`tcc.Get` / `NewGetter` 是支持的。
- **localcache 本地缓存**:本地 map 缓存的数据无法录制回放,回放查不到造成噪音;需方法级
  mock 或走"两侧均不命中 localcache"方案。
- **singleflight**:并发复用一个响应,会出现"rpc 漏录制的假象";需幂等或对相关函数完整
  包装采集 mock。

### D. mock 反序列化 / 类型断言失败

稳定判据:FTF mock 对 interface 类型 mock 会丢原始类型,反序列化成 `json.Number`;业务
若 `i.(int64)` 断言会失败(典型:dolphin `BasicJudge` 返回 `map[string]interface{}`)。
动作:业务侧做类型兼容(先判 `int64`,再判 `json.Number` 调 `.Int64()`)。这是 mock
反序列化边界,通常需业务兼容或方法级 mock。

## 输出

按 `replay-diagnosis.md#报告口径` 输出。mock 类务必:

- 先说清任务形态 / 采集源,排除"本就不该有 outbound"的误判;
- 用 `flow diff get --with-outbound` 的 `not match recorded outbound` / `request diff` 作为
  CLI 可见证据;
- 已定位根因时，给出业务代码 / 配置机制与日志 / Trace 直达链接，再用 outbound 请求、回放
  响应和最多一个代表性 Flow 说明结果；仅有 FTF 详情页时必须降为低置信并列证据边界；
- 请求外状态(协程池 / tcc / localcache / singleflight)一律列外部待验证项 + 改造方向,
  不要直接判成代码 bug;
- 单条根因的完整下钻转 `flow-diff-root-cause.md`;无果带 logid 证据发起 FTF oncall。
