# 诊断状态机与证据模型

## 目录

- 最小事实包
- 状态路由
- 证据模型
- 因果收敛
- 置信度
- 停止与验证
- 最终输出

## 最小事实包

根因结论前尽量固定：

| 字段 | 获取方式 | 缺失风险 |
|---|---|---|
| task ID、任务名、owner | 用户输入 + Dorado | 查错同名任务 |
| application ID、attempt | Dorado operation log / Megatron | 把旧实例错误套到当前实例 |
| job ID、Flink URL | `flink job list` | 查错 JobGraph；不要硬编码全零 job ID |
| site、region、cluster、queue | Dorado/Megatron/Dashboard | 把错误路由的空数据当 0 |
| YARN/Kubernetes | 任务元数据/runtime provider | 错用 K8s 或遗漏容器事件 |
| Flink 完整版本/fork | build、配置、JM log | 使用不存在的 endpoint/metric/default |
| stream/batch、source/sink、CP mode | 配置和 plan | 套错语义 |
| 故障起止、时区、正常基线 | 告警、用户时间、operation log | 不能建立先后关系 |
| 症状、SLA、最近变更 | 监控、发布/操作记录 | 把正常 backlog 当故障或漏掉变更 |

Agent 应自行查询可取得的事实。只有身份、时间或业务 SLA 无法从环境取得时再向用户补问。

## 状态路由

同时保存 `platform_status` 与 `flink_job_status`；两者不是同一状态机。

1. 身份无法解析：`FACTS_INCOMPLETE`。
2. 当前 application 不存在：
   - 从未创建或提交中：`STARTUP_OR_SUBMISSION`；
   - 存在历史/终态 attempt：`HISTORICAL_TERMINATION`；
   - 历史也无法解析：`FACTS_INCOMPLETE`。
3. `FAILED/FAILING/RESTARTING`、明确 TM/JM lost、container termination 或 restart/attempt 同窗上升：`FAILOVER`，最高优先级。若只有不确定 TM lost/heartbeat、`Pod deleted` 或 `Pod Terminated`，保留 `FAILOVER` 路由并强制输出 `FAILOVER_TM_IDENTITY_EVIDENCE_REQUIRED`，不直接命名根因。
4. 平台状态与 Flink 状态冲突，或 attempt、JM URL、host 映射不唯一：`PLATFORM_RECONCILIATION`，先检查身份和新鲜度。
5. application 存在但 JM 不可达：
   - 终态 application：`HISTORICAL_TERMINATION`；
   - 已稳定运行，且 [failover.md 的 JM 静默强制守卫](failover.md#jm-静默或宿主机不可用无-failover) 闭合：`JM_SILENT_OR_HOST_UNAVAILABLE`；
   - 从未稳定进入 RUNNING：`JM_STARTUP_OR_PLATFORM_AVAILABILITY`；
   - attempt/restart 历史、故障时间窗或 URL 身份不足：保留 `JM_STARTUP_OR_PLATFORM_AVAILABILITY` 并输出 `PARTIAL/UNKNOWN`，不能用数据缺失证明守卫成立。
6. `CANCELLING`：与用户操作一致且 task 正收敛时为预期过渡，否则 `CANCELLATION_STUCK`。
7. `CANCELED/FINISHED/STOPPED`：与有界作业或用户操作一致则正常结束，否则意外终止。
8. `SUSPENDED/RECONCILING`：`DEPLOYMENT_CONTROL_PLANE`。
9. `INITIALIZING/CREATED` 或 task 卡在调度/部署：`STARTUP_OR_SCHEDULING`。
10. `RUNNING` 时收集全部症状，再选主分支：
    - checkpoint 与 restart/TM lost 重合：`FAILOVER`，CP 是后果；
    - Lag/source 断流、平台仍保留 RUNNING、incident attempt/restart 未变化，且绑定该 attempt 的 JM REST 或 uptime 断点：`JM_SILENT_OR_HOST_UNAVAILABLE`；该分支优先于普通性能诊断；
    - 含明确 reason/diagnostics 的容器终止：`RESOURCE_OR_PLATFORM_TERMINATION`；只有 deleted/terminated 状态时转 `FAILOVER_TM_IDENTITY_EVIDENCE_REQUIRED`；
    - 正确性：独立高优先级 `CORRECTNESS`；
    - 无 failover 的 CP 异常：`CHECKPOINT_PHASE`；
    - lag/吞吐/反压：`RUNNING_PERFORMANCE`；
    - 无 lag 但 e2e 高：`WATERMARK_BATCHING_OR_COMMIT`。

保留次分支，不要把多个并存症状压成一个标签。

## 证据模型

证据优先级：

- **E0 直接因果**：带实体和时间的 root exception、termination reason、scheduler rejection、远端明确错误响应。
- **E1 同窗跨层**：两个独立证据面以相同实体和正确先后顺序闭合。
- **E2 症状指标**：lag、busy/idle/BP、CP duration、GC、CPU、memory；用于量化与选路。
- **E3 假设**：文本相似或未经验证的经验，只能进入待验证列表。

每条证据使用以下结构：

```json
{
  "evidenceId": "ev-001",
  "level": "E0",
  "source": "flink-rest",
  "entity": "task|application|application-attempt|job|jm|vertex|subtask|tm|allocation|container|pod|host",
  "entityId": "...",
  "observedAt": "RFC3339 with timezone",
  "window": ["from", "to"],
  "fetchedAt": "RFC3339",
  "freshness": "live|historical|stale|unknown",
  "fact": "不含推断的原始事实摘要",
  "artifactRef": "endpoint/query/log offset/trace id",
  "supports": ["hypothesis-id"],
  "contradicts": ["hypothesis-id"]
}
```

使用事件自身时间排序，不使用 API 返回顺序或抓取时间代替事件时间。

## 因果收敛

按以下结构组织：

```text
[触发事件 E0]
  -> [失败机制 E0/E1]
  -> [Flink 状态、反压、checkpoint 或 failover E1]
  -> [业务症状 E2]
```

把根因与促成条件分开。根因是移除后能阻断事件链的具体条件；checkpoint interval、恢复策略、资源余量等可能只放大影响。

结论前至少处理最接近的替代解释：

- 流量突增：生产率是否先升，而不是消费率先降？
- 数据倾斜：是否集中在少数 subtask，records/state/partition 是否支持？
- Java heap OOM：是否有 heap OOM，而不是只有 exit 137？
- CP storage：是否集中在 async/upload，而不是 start delay/alignment？
- 外部依赖：远端错误/延迟是否早于 Flink timeout/反压？
- watermark：哪个 input/subtask 最小，是否确有 idle partition？

## 置信度

| 状态 | 最低条件 | 输出边界 |
|---|---|---|
| `CONFIRMED` | E0 与正确实体/时间匹配，且有独立佐证或完整复现链；关键替代解释已证伪 | 可写具体 root cause |
| `HIGH` | 至少两个独立 E1 构成正确先后顺序，无强冲突 | 写高置信原因/机制并列未证实部分 |
| `MEDIUM` | 一个有区分力的 E1 + E2，替代解释未全排除 | 写候选和下一证据 |
| `LOW` | 只有 E2 或文本相似 | 不给根因动作，只给分支和取证建议 |
| `PARTIAL` | 部分数据源成功，关键数据源因权限/网络/retention 失败 | 保存部分证据，不解释为空或健康 |
| `UNKNOWN` | 身份、attempt、时间、版本或区分性证据缺失 | 写停止原因、最后可证实层级和补证 owner |

## 停止与验证

满足以下条件后停止扩大取证：

1. task/application/job/vertex/subtask/runtime placement 的实体链闭合，时间窗一致；Kelemetry Pod 与 Vela host 仅在有可信 bridge 时作为分段旁证，不能承担反查。
2. 触发事件、机制和业务症状存在可复核因果边。
3. 最相近的替代假设已处理。
4. 置信度、影响、owner、缓解与根因修复边界清楚。
5. 修复验证条件可观测。

`RUNNING_PERFORMANCE` 还必须满足 [performance.md 的强制性能分支完成条件](performance.md#完成条件)：high busy 与上游反压或 lag 同窗出现后，不得停在 E2 症状层。只有完成 current-attempt subtask/TM 绑定，只对 2–3 台代表 TM 查询 Kelemetry Pod lifecycle、Vela host 指标、TM 有界证据与两轮 thread dump 分类，或被 capability、权限、预算明确阻断，才允许停止；阻断时输出 `PARTIAL`/`UNKNOWN` 并记录失败的实体、命令边界和所需 owner。

`JM_SILENT_OR_HOST_UNAVAILABLE` 还必须满足 [failover.md 的 JM 静默分支完成条件](failover.md#完成与停止条件)：固定 incident attempt，以 containerId 查询 Kelemetry Pod/node、只对 Kelemetry 唯一绑定的 node 查询 Vela host，完成有界 ByteTSD、Megatron attempt 与最多两个显式 peer 的相同分段取证，或记录明确 capability、权限、retention 缺口；不得因 Kelemetry/Vela 空数据、Vela 负载高或 `agent.alive` 断点升格为宿主机不可用。

`FAILOVER_TM_IDENTITY_EVIDENCE_REQUIRED` 还必须满足 [failover.md 的日志优先完成条件](failover.md#输出与停止边界)：固定 incident application 和 `W`，结构化 `tmResourceId/exactPod/hostHint`，并只选最多 3 个实体。AM attempt 仅由显式元数据或 exact incident TM Pod 绑定；application ID 不等价于 AM attempt，opaque TM ID 缺 attempt 时仍先查日志但保持 `PARTIAL`。对每个实体先完成有界 TM 日志 list/get；只有日志不可得、截断或无决定性信号才进入 Kelemetry/Vela。Kelemetry 仅查 exact Pod，其同窗唯一 node 才是 verified Vela target；未经 Kelemetry 验证、仅由 host hint 驱动的 Vela 结果保持 candidate。泛化文本、身份冲突、旧 attempt、日志/Kelemetry/Vela 空结果或预算阻断均保持 `PARTIAL/UNKNOWN`，不扫描全部 TM。

以下情况停止猜测并输出 `UNKNOWN`：异常史截断且日志不可得；版本/attempt/时间窗不明；关键 metric 因权限或 retention 缺失；需要外部 owner 提供 termination/scheduler/remote evidence；继续采集只能重复症状指标。

修复后不要用一次 RUNNING 或一次 CP success 宣告解决。验证 restart/attempt 稳定、lag 斜率回落、subtask 分布恢复、连续跨越多个实际 CP interval 成功、无新 root exception/dirty/writeFailed，并确认直接异常同步消失。

## 最终输出

内部保留完整 `IncidentEnvelope`、时间线、证据等级、反证、缺口和替代假设，最终默认按上层 `SKILL.md` 的“三项紧凑报告契约”只输出 `根因 / 证据 / 解决方案`。任务事实只在防止实体混淆时进入证据；置信度折叠进根因句；关键反证或停止边界最多占一条证据；owner、风险、回滚和验证条件只在影响行动安全时折叠进对应解决方案。

只有用户明确要求展开证据或详细报告时，才从内部账本补充任务事实、完整时间线、替代假设、验证条件和升级路径；不要把采集器 JSON、完整日志、堆栈或原始 metric series 直接倾倒给用户。
