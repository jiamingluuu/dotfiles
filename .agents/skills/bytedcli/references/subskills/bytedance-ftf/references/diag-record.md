# 自查：录制/采集不到流量（L1）

## 适用现象

- Tesla-X 用例管理里查不到采集流量，或采集流量条数为 0。
- outbound 未采集到流量：inbound 有，但下游调用完全没采到。

本文件完整负责录制/采集侧输入门禁、ByteCopy/SDK 分流、故障树、证据链和输出。首次症状分诊时，
若用户提供任务 ID/链接并反馈“回放没有流量”或任务 `status=7`，应改读 `diag-replay.md`；若已由
`diag-replay.md` 的实时链路委派回来，则不要再次改读，直接使用任务中的 PSM、时间窗和已知采集源
执行本文件对应分支。流量已采到但回放失败见 `diag-replay-failure.md`，采到了但覆盖面少见
`diag-coverage.md`。

参考资料：

- 《FTF2.0 ByteCopy 无流量排查手册》（内部文档；脱敏锚点：ByteCopy 无流量）
- 《FTF2.0 流量回放 One Page》（内部知识库；脱敏锚点：采集问题）

手册只提供排查线索。当前 CLI 帮助、源码、Schema、日志、请求/响应、部署和配置证据与手册
冲突时，以直接证据为准并说明冲突。

## 目录

- [输入门禁与采集源分流](#输入门禁与采集源分流)
- [ByteCopy 采不到流量](#bytecopy-采不到流量)
- [SDK 采不到流量](#sdk-采不到流量故障树)
- [outbound 采集不全](#outbound-采集不全sdk)
- [连续证据与结论规则](#连续证据与结论规则)
- [输出](#输出)

## 输入门禁与采集源分流

录制不到流量诊断至少需要 **PSM**。缺少 PSM 时先索取，不做无目标查询；一次性提示用户可
补充环境/泳道、Cluster、IDC、Method/接口、LogID、时间窗和预期采集源。拿到 PSM 后先固定
观察时间窗和已知环境维度，并确认目标实例在该窗口内是否真的收到业务请求。

用户只说“录制不到流量”或“采集不到流量”，没有明确 ByteCopy 或 SDK 时，必须同时建立
**ByteCopy 和 SDK 两条并行诊断分支**。两条分支可并行取证，但要分别输出结果；一条正常不能
证明另一条正常。用户明确了采集源时，只进入对应分支。ByteCopy 收包、consumer 解析、限流
等专属指标只能证明 ByteCopy 链路；SDK 分支只接受 SDK 初始化、插桩、发送日志及其自身部署、
配置和业务请求证据，禁止复用 ByteCopy 指标补齐 SDK 证据链。

采集源决定了"该采到什么"和"去哪看",不先分清会白排查。判据见
`domain-model.md#采集源与证据可见性边界`,`flow_source` 取值见 `enums.md#flow_source`。

| 采集源     | 采集时机             | 流量内容                       | 典型场景                             |
| ---------- | -------------------- | ------------------------------ | ------------------------------------ |
| `bytecopy` | 任务运行期间实时采集 | 只含入流量(inbound)请求 / 响应 | 一般用于 PPE 读接口回放              |
| `sdk`      | 合码上线后一直采集   | 完整数据,含下游 outbound       | 一般用于 BOE 写接口回放,也可用于 PPE |

- `bytecopy` **本就不含完整 outbound**;这种源下"outbound 采不到"不是 bug,别按 sdk 排查。
- `sdk` 才适合下钻 outbound。sdk 采不到,按下面的故障树逐项核实。

若存在关联回放任务，任务的 `case_filter_mode` 反映流量来源类别（见
`enums.md#case_filter_mode`），单条 Flow 的 `flow_source` 在 `flow get` / `flow diff get`
概要字段里；没有关联任务或完全没有 Flow 时该字段不可见，不能据此猜测采集源。

```bash
bytedcli --json --site cn ftf task get --id 1234567 | jq '.data | {case_filter_mode, run_psm, env}'
bytedcli --json --site cn ftf task flow get --task-id 1234567 --pid sample-pid | jq '.data.diff.flow_source'
```

以上是 cn 的裸 ID 示例；zg 裸 ID 必须把全局路由改为 `--site cn --vregion China-Pay`。裸 ID
不携带站点，未明确站点时先索取；不得依赖默认配置猜测。若来自 URL，先按 `SKILL.md` 解析并
冻结站点，后续 ID-only 命令复用该显式路由；与用户显式配置冲突时停止。

## ByteCopy 采不到流量

ByteCopy 的采集不属于 FTF SDK 插桩链路，CLI 也看不到完整采集管线。按以下顺序建立连续
证据，不要因为用例管理中为零就直接判定 ByteCopy 故障：

1. 用目标实例访问日志、业务 QPS 或已知 LogID 证明目标 PSM、环境/泳道、Cluster、IDC、
   Method 在采集窗口内确有真实入流量。
2. 核对流量是否经过支持 ByteCopy 的 Mesh/协议链路，以及 ByteCopy 采集配置、目标范围、采样
   和限流是否覆盖该请求。
3. 在同一 PSM、Method 和时间窗内核对 ByteCopy 收包、解析错误及
   `ftf.nova.flow_consumer.bytecopy_flow_parse_ok`，区分没收到、收到但解析失败。
4. 继续核对 `ftf.nova.flow_consumer.flow_bytecopy_rate_limit`、`flow_format_check` 和
   `save_nova_flow`，定位限流、格式转换或保存断点。

具体平台操作参考 **FTF2.0 ByteCopy 无流量排查手册**和 FTF One Page 的“采集问题 →
【ByteCopy】采集不到流量原因”。当前可用观测能力取不到某段证据时，明确记录待核实的指标、
日志、维度和时间窗；无果后携带已收集证据发起 FTF oncall。

## SDK 采不到流量：故障树

sdk 采不到的根因几乎都在 CLI 之外(编译产物 / 启动脚本 / 服务日志 / tcc)。下面每个
节点给**稳定判据 + 核实动作**;操作细节以 FTF onepage「采集问题 →【sdk】采集不到流量
原因」为准。按从易到难顺序核实:

### 1. 服务是否真的起了 record 产物

稳定判据(以下关键字来自 FTF SDK,属固定契约,可直接搜):

- 服务启动日志搜 `[FTF-INFO] start rinnegan success!`——**这是 FTF SDK 成功初始化的
  标志**。没有它,基本可判定当前实例没跑起录制能力。
- 线上按小流量机器采集:登录机器 webshell,`ps aux | grep <p.s.m>` 看启动的 bin 是否
  带 `.record` 或 `-ftf` 后缀;`ls bin` 看有没有对应产物。无后缀 = 启动产物不对 / SCM
  没接 FTF。
- PPE / BOE 若在 SCM 打开了"FTF 录制 Mock 插桩",录制 bin 与业务 bin 同名,无需查后缀。

核实动作:让用户去对应实例拉启动日志搜该关键字;线上再补 `ps aux` / `ls bin`。这些
CLI 都取不到,列为外部待验证项。

### 2. 编译有没有真的插桩 FTF

稳定判据:

- 看 SCM 编译的 `pre-build-ftf-sdk` 和 `building` 两个阶段日志。
- `building` 日志里搜 FTF SDK module replacement marker（例如脱敏模块锚点 `rinnegan`）——有,
  说明改过 go.mod 接了 FTF；完全没有绿色 INFO 日志则说明没编译 FTF 过程。
- 编译告警 `unsupported kitex version ...` / `unsupported hertz ...`:组件版本未支持,
  **不阻塞编译但会漏采**,需发起 oncall 支持。
- atum 编译需在 lidar 平台待优化里打开 ftf,或 SCM 环境变量配
  `CUSTOM_ATUM_COMPILE_FEATURES=enable_ftf`。
- 编译脚本里若有 `go_coverage_annotate.sh ... -clean`,`-clean` 会清除 FTF 插桩,需删掉。

核实动作:引导用户翻编译流水线这两个阶段日志;CLI 不可见,列外部待验证项。

### 3. 启动条件 / 环境变量把录制挡住了

稳定判据(以下 env / 脚本条件是 FTF 固定契约):

- `bootstrap.sh`(`script/bootstrap.sh`)里有启动 record 产物的条件判断,例如:
  `(TCE_STAGE==canary && TCE_INTERNAL_IDC==HL && TCE_CLUSTER==default) || TCE_HOST_ENV==ppe
|| TCE_HOST_ENV==boe || RECORDER_ON!="" ) && FTF_FORBIDDEN==""`。条件不满足就不会起
  record 产物,需按实际部署改条件。
- PPE / BOE 采集必须设 TCE 环境变量 `RECORDER_ON=1`(全量录制用 `FTF_SAMPLED_ALL=1`,慎用)。
- TCE 集群若配了 `FTF_FORBIDDEN=true`,会禁掉采集,需找配置人确认背景。
- 压测流量默认不采,除非设 `FTF_STRESS_OPEN=1`。

核实动作:引导用户核对 `bootstrap.sh` 启动条件与 TCE 环境变量;CLI 不可见。

### 4. 采样 / 限流 / 特殊接入把流量过滤了

稳定判据:

- 默认均匀随机采样,约 10s 采一条。采样率 tcc 配置 namespace `pdiqa.ftf.rinnegan`,
  key `psm_sample_ratio`(单实例录制比例 [0.01,1],最高不超过 1qps)。流量本身少时用
  **定向采集**。
- 部分接口采不到:FTF 默认只采 canary 的 `default` 集群;打到别的集群要在
  `bootstrap.sh` 加对应采集集群条件。
- 老框架(如 kite)不支持;只支持 Kitex / Hertz / Ginex。
- 电商接了 TSF 托管采集（代码里有 TSF module import + `EnableSimulator: true`）时,
  FTF 默认录制会被关,需配 TSF 的 tcc 才录制。
- 序列化报错也会导致采不到:业务日志搜 `FTF-ERROR` 有 `json: unsupported type`,在
  tcc `pdiqa.ftf.rinnegan` 的 `psm_marshal_config` 把该 psm 的 `use_json_iterator` 配
  `true`,BOE 和线上都配。

核实动作:采样率 / 定向采集 / TSF / 序列化都在 tcc 或业务代码,CLI 不可见,给用户对应
key 与代码搜索关键词。

### 5. 服务端录制日志与监控(需要用户在 Argos 查)

稳定判据(FTF 固定日志关键字):

- `[FTF-INFO] send inbound req message success`:录制成功并已发 MQ 消息。
- `[FTF-WARN] resource circuitbreaker triggered`:机器资源紧张触发系统熔断,5 分钟后
  才会再判断是否允许采集。
- `[FTF-ERROR]`:录制过程 error,可带日志链接发起 oncall。
- 录制失败监控打点 `ftf.nova.recorder.flow_record_failure`(按 psm / method 查);
  `ftf.nova.recorder` 日志按 `_level=Warn/Error` 过滤。

核实动作:这些是 Argos / 监控侧证据,CLI 不覆盖。可配合 `bytedance-log` skill 按 psm +
关键字查 FTF 日志,但结论仍需用户确认。

这些 SDK 证据不得替换成 `bytecopy_flow_parse_ok`、`flow_bytecopy_rate_limit` 等 ByteCopy 专属
指标。若 SDK 日志、插桩或部署证据不可取得，SDK 分支必须标为证据缺失，而不是借用 ByteCopy
链路的正常指标判定 SDK 正常。

## outbound 采集不全(sdk)

inbound 采到了,但 outbound 很少或没有:

- 先确认采集源是 `sdk`(`bytecopy` 本就不含完整 outbound,见上文)。
- 看编译日志有没有 `unsupported` 组件,或需要支持但无相关日志的组件 → 发起 oncall。
- **用了协程池但没透传 context**:协程池里的 outbound 无法录制,必须透传 context 才行。
  这是原理性限制(见 `domain-model.md` 录制回放模型),属需业务改造的外部待验证项。

## 连续证据与结论规则

对每条采集源分支按“真实请求 → 采集组件启用 → 请求被采集 → 消息发送 → 消费解析 → 保存
可见”建立时间线，记录最远通过点和紧邻的首个失败点。低 QPS 时还要核对采样概率、观察窗和
任务运行时长；观察窗内没有样本不足以证明采集组件故障，应延长观察、定向采集，或用已知
LogID 核对一条真实请求。

“未发现日志”“指标为零”和“当前工具不可见”分别表示未观察到、观测值为零和证据缺失，
不能混为同一结论。无法闭环时输出“根因未定位”，列出已排除节点、首个证据缺口和一个最小
下一步，不以“未知”“采集异常”或笼统的平台问题结案。

## 输出

按 `replay-diagnosis.md#报告口径` 输出，并额外包含：

- PSM 是否齐全，以及环境/泳道、Cluster、IDC、Method、LogID、时间窗等已知范围；
- ByteCopy 与 SDK 分支结果；未指定采集源时两条都必须输出；
- 每条分支的最远通过点、首个失败点和时间线证据；
- 日志、编译产物、TCC、`bootstrap.sh` 等外部待验证项及具体核实动作；
- 已确认根因、待验证项、证据冲突和一个带验证成功标准的最小下一步。
