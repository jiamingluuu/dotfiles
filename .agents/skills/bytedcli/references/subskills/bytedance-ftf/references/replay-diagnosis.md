# FTF 流量回放使用问题自查(编排层)

## 用途

当业务反馈"回放用不起来"——采集不到流量、任务失败/异常、mock 未命中、覆盖率
低——用本文件做**症状驱动的只读自查**。它区别于 diff 归因:diff 归因回答"有 diff
是不是代码引入"(task 驱动),本主题回答"回放这条链路为什么跑不通"(症状驱动,
可以没有具体 task)。

- 领域背景(录制回放原理、采集源、证据可见性)见 `domain-model.md`。
- 一次完整 diff 归因的编排见 `diff-analysis.md`,本文件不覆盖 diff 分析。
- 取数命令参数、JSON 字段口径见 `diff-query-reference.md`;任务字段与接口映射见
  `task-api.md`;任务状态和单条流量 `failed_reason` 错误码见 `enums.md`。

## 目录

- [只读与边界原则](#只读与边界原则)
- [症状分诊](#症状分诊)
- [通用第一步](#通用第一步有-task-id--url-时)
- [报告口径](#报告口径)

## 只读与边界原则

- **全程只读**。自查不触发、不重试、不停止任务,只取证 + 引导。需要写操作
  (`task retry` / `task stop` / `plan execute`)时,交回用户显式确认后再走 `SKILL.md`
  的 Guarded Writes。
- **外部待验证优先**。采集源、FTF 产物是否启动、组件是否支持、context 是否透传,
  这些前提只有在任务结果 / 日志 / 编译产物里明确出现才算已确认事实;否则一律列为
  "外部待验证项",给用户可执行的核实动作,不要写成结论。判据依据见
  `domain-model.md#采集源与证据可见性边界`。
- **CLI 能取的自动取,取不到的引导核实**。CLI 只覆盖任务终态、流量来源、配置回显、
  flow / method 报告一小部分信号;根因大多散落在编译日志、服务启动日志、tcc 配置、
  `bootstrap.sh` 启动条件、业务代码里,这些 CLI 看不到,由各 L1 故障树给判据 + 核实
  动作。
- FTF 平台事实优先由 bytedcli 查询；根因链可按故障树补充获准的日志、代码、部署和配置证据。
- 输出根因判断时遵循 `diff-analysis.md` 的“归因证据规范”：用代码 / 配置机制、运行时日志 / Trace
  和回放结果闭合因果链，FTF Flow 详情只作为现象证据。
  API 失败不得改用浏览器抓页面。

## 症状分诊

先用一句话把用户诉求归到某一症状,再打开对应 L1 故障树。多个症状叠加时,按
"采集 → 回放失败 → mock → 覆盖率"的顺序逐个排除(没采到流量就谈不上 mock)。

| 症状关键词                                                               | 打开                     |
| ------------------------------------------------------------------------ | ------------------------ |
| "录制不到""采集不到""流量没录到""用例管理查不到""outbound 采集不全"      | `diag-record.md`         |
| "回放没有流量""回放任务无数据""任务没流量""status=7"                     | `diag-replay.md`         |
| "回放失败""任务红了""任务异常""901115/1115""901604/1604""连接失败""限流" | `diag-replay-failure.md` |
| "mock 没命中""not match recorded outbound""外调报错""类型断言失败"       | `diag-mock.md`           |
| "覆盖率低""命中流量少""case 太少""link_calls 为空"                       | `diag-coverage.md`       |

不要只按“流量”二字路由。没有任务语境的“录制/采集”问题进入 `diag-record.md`；带“回放/任务/
status=7”语境的零流量问题进入 `diag-replay.md`。同时包含两类症状时先按录制分支确认上游采集，
再回到回放分支沿任务和下游执行链路继续，不能用任一入口替代另一入口的必填输入。

无法归类,或用户只给了一句"回放有问题"时,先跑下面的通用第一步拿任务终态,再据
`status` / `detail_status` 收敛到某个症状分支。

## 通用第一步(有 task id / url 时)

任何带 task 的自查都先拿终态,把问题收敛到某个症状,不要一上来就翻日志。

```bash
# 以下裸 ID 示例固定为 cn；zg 使用 --site cn --vregion China-Pay。
bytedcli --json --site cn ftf task get --id 1234567 \
  | jq '.data | {status, detail_status, case_filter_mode, run_psm, env, task_flow_count, case_count, diff_case_count, fail_case_count, finish_time}'
```

只有 Tesla-X URL 时先解析类型,再按 task id 入口查:

```bash
bytedcli --json ftf target parse --url "<ftf-url>"
bytedcli --json ftf task evidence get --url "<ftf-task-url>" --page 1 --page-size 20
```

URL 命令自身会自动派生站点；解析后冻结 `.data.target.site` 和所有 selector。工作流仍须将解析
结果与用户明确声明的目标站点对比，如不一致，在任何派生 ID 查询前停止。继续使用 URL 的命令
由 URL 维持路由；任何改用派生 ID 的后续命令都必须显式传冻结站点（cn：`--site cn`；zg：
`--site cn --vregion China-Pay`）。输入只有裸 ID 且未给站点时先索取，不从 ID、默认配置、任务
字段或凭据猜站点。

按终态收敛(枚举含义与终态判定见 `enums.md#任务状态`):

| 观察到                                                            | 收敛到                                                             |
| ----------------------------------------------------------------- | ------------------------------------------------------------------ |
| `status=7`(无流量,`TaskStatusAssertNodata`)                       | `diag-replay.md`:按流量模式定位来源、筛选、采集或下游回放断点      |
| `status ∈ {3,10,14}`(任务失败 / 断言异常 / 重放失败)              | `diag-replay-failure.md`                                           |
| `status=8`(数据太多未断言)                                        | `diag-coverage.md` 的反面:流量够但被限,通常非自查重点,提示缩小范围 |
| `status=6 && detail_status=40`(正常结束)但有大量 diff / mock 失败 | `diag-mock.md` 或转 diff 归因 `diff-analysis.md`                   |
| `task_flow_count` 很小 / `case_count` 远低于预期                  | `diag-coverage.md`                                                 |
| `detail_status=39`(聚合报告失败)                                  | `diag-replay-failure.md`:报告聚合阶段失败                          |

`task get --id` 只反映回放任务状态;它**不能**证明线上采集是否成功。独立的录制/采集问题
直接按 `diag-record.md` 的 PSM 门禁和 ByteCopy/SDK 分支排查。回放任务无流量先进入
`diag-replay.md` 判断来源模式；只有实时流量分支才按需引用 `diag-record.md` 核对编译、启动和
采集日志，并在采集后继续检查下游回放链路。

## 报告口径

每次自查产出以下结构,让用户能照着做下一步:

```text
症状与范围
- 症状:<采集不到 | 回放失败 | mock 未命中 | 覆盖率低>
- 输入:<task id / url / psm / method / env / 采集源>
- 任务终态:<status / detail_status 的可读判定;无 task 时写"无关联任务">

已取证据(CLI 可见)
- 逐条列出命令输出里的关键信号:status/detail_status、case_filter_mode、
  task_flow_count、replay_failed_reason、flow 的 success/outbound_success 等
- 每条注明来自哪个命令
- `replay_failed_reason=null` 只写“method 聚合字段无失败证据”，不得写成“无回放失败”；须与
  task 失败计数、Flow 列表和单条 `failed_reason` 对账

根因判断(分层)
- 已证明:CLI 结果或用户已确认的日志能直接支撑的
- 疑似:故障树指向、但依赖外部证据才能坐实的
- 外部待验证项:采集源 / 产物启动 / 组件支持 / context 透传等前提,附核实动作

下一步
- CLI 能继续查的:下一条命令
- 需要用户去平台 / 机器核实的:看哪个日志、哪个 tcc key、哪个编译阶段
- 无果后的兜底:发起 FTF oncall,并附上已收集的证据链接
```

术语的用户可读译法见 `domain-model.md#术语与表达规范`;正文优先用可读说法,内部
字段名放命令清单或括号说明。
