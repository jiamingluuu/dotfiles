# bytedcli 只读取证与 Metric 命令

## 目录

- 调用与鉴权
- 安全允许列表
- 身份与 application
- Flink runtime
- Failover TM 身份证据原生补证
- 性能 TM 证据原生补证
- TM 日志与 Kelemetry/Vela 公共边界
- 历史 metric 与 Dashboard
- JM 静默历史证据
- 平台、消息源和宿主机
- 发现优先原则
- 时间、区域与失败语义

## 调用与鉴权

执行前先确认实际版本和登录态：

```bash
bytedcli --version
bytedcli -j auth status
```

海外任务要区分平台登录态与 compliance Flink 自己的 Django session，而不是只看顶层 `authenticated`。`flink.tiktok-eu.org` / `flink.tiktok-us.org` 或 UI-shell 中的 `clover` / `us-ttp` 任务出现鉴权失败时，交互登录必须传 Dorado 返回的原始 `flink-proxy.tiktok-row.net` UI-shell URL：`bytedcli --site "$SITE" auth flink-session login --url "$FLINK_UI_SHELL_URL"`。浏览器已有登录态时会直接捕获，否则按提示完成飞书 SSO。`auth flink-session status|logout` 省略 `--url` 时按全局 `--site` 选择缓存（`us-ttp` 为 US，其余保持 EU 默认）；显式 `--url` 优先。若只有直接 REST URL，先从 Dorado `yarnAppUrl` 取得 UI-shell URL；直接 REST URL 只适用于恢复现有浏览器 cookie，或配合显式 `--cookie` 写入缓存。其他海外平台鉴权失败时再请用户完成目标 SSO environment 的 device-code 登录。不要索要或回显凭据。

结构化调用加 `-j`/`--json`；JM/TM 日志内容使用非 JSON 的原生 `log get`，并由调用方施加输出上限。Flink REST 的瞬时 `fetch failed`、timeout、connection reset 和网关 `502/503/504` 最多重试三次；`401/403`、`404`、鉴权与身份错误不重试，也不算 JM 静默。

## 安全允许列表

允许自动执行：

- Dorado：`task get/code/diff/advanced-search`、`flink monitor get`、`flink operation-log list/get`。`advanced-search` 只在已知 project/owner 范围内使用，`--limit` 不超过 20；`code/diff` 只对已固定的 task 读取最近变更。
- Megatron：`app search/get`、`queue usage`、`flink log-link list`、`log list/get`。
- Flink：`diagnose`、`job list/get/exception get/plan get/checkpoint list/get/checkpoint-config get/metric list`、`vertex backpressure get/metric list/watermark get/taskmanager list`、`taskmanager list/log list/log get/metric list`、`jobmanager log list/log get/metric list`。`raw get` 只允许按下文 3 类精确 GET 模板构造，拒绝调用方提供的任意 path/query。
- APM/Grafana：search、metadata、describe、info、variable get、query。
- BMQ/RMQ、Kelemetry、SIP、Vela、HDFS：只读 list/get/search/query/stats/clients/allocation。
- Cache：控制面只允许只读 `get-cluster`；`execute-command` 只允许 `LLEN`、`LRANGE`、`ZREVRANGE`，且必须由已审计的调用逻辑构造 key/范围。

不允许自动执行任何未列出的叶子命令。TCE webshell 不在自动允许列表；明确确认后仍限制为已说明的只读命令。profiling 会创建采样任务，不属于本 skill 的只读执行范围，只能建议另行授权的人工/独立流程。

## 全局有界执行

- 每条外部命令默认 20 秒超时，自动上限 60 秒；只有网络/网关瞬时错误最多重试 3 次，鉴权与参数错误不重试。
- 性能 TM 分支中的 subtask detail、subtask metric 和 TM metric 等普通结构化响应单次最多 256 KiB；性能 metric 的整个分支累计最多 1 MiB。达到字节上限时立即终止子进程、标记截断并输出 `PARTIAL`，不能继续扩大实体范围。
- JM/TM 日志先用 `log list` 验证源文件 size 不超过 64 MiB；size 缺失或超限时跳过内容读取并记录缺口。内容读取使用非 JSON `log get`，`--tail` 不超过 50，禁止 `-j`/`--json`、`--full` 和 `--out`；每台 TM 的 stdout+stderr 合计硬上限为 64 KiB，超限立即终止并标记截断。Megatron 离线日志 `--tail-bytes` 不超过 65536。
- 列表单页不超过 100 条，metric 名每批不超过 100 个；先按实体和时间窗缩小，再翻页，不做无限分页。
- 历史查询默认 2 小时，围绕已发现事件自动扩窗最多 24 小时。更长窗口必须让用户明确指定，并仍保持聚合和输出上限。
- JM 静默分支只按 incident application/job、固定指标名和故障窗口查询；当前任务加最多两个调用方已知的同机 peer。禁止 job/vertex metric catalog discovery、host → applications 全量枚举或 cluster-wide application 扫描。
- JM 静默补证的每条结构化命令 stdout+stderr 合计最多 256 KiB、20 秒；Kelemetry 整个分支累计最多 1 MiB，ByteTSD 累计最多 1 MiB，Vela 累计最多 256 KiB，自动窗口最多 24 小时。达到预算立即终止/跳过后续调用并输出 `PARTIAL`，不得通过加 peer、metric 或扩窗绕过。
- Failover TM 身份补证的每条结构化命令 stdout+stderr 合计最多 256 KiB、20 秒；单台 TM 日志内容最多 64 KiB，Kelemetry 总计最多 1 MiB，Vela 总计最多 256 KiB。主诊断最多选 3 个 incident TM 实体；任一实体达到预算即停止其后续查询并记为 `PARTIAL`，不新增替代 TM。
- Kelemetry/Vela 专用命令固定 `--no-auto-upgrade --http-timeout-ms 15000 --http-retry-count 0`，外层仍以 20 秒和 stdout+stderr 256 KiB 硬截断兜底。性能 TM 分支只对最终 2–3 台代表 TM 查询：Kelemetry 累计最多 1.5 MiB，Vela 累计最多 768 KiB；不得对 12 个候选 subtask 或全部 TM 扇出。
- 通用 `flink raw get` 保持禁用。只有 current-attempt subtask detail、固定白名单 subtask metrics 和 current-placement TM thread dump 这 3 类精确 GET 模板可由诊断逻辑构造；拒绝用户提供的 path/query。subtask/detail/metric 单次响应最多 256 KiB，性能 metric 累计最多 1 MiB；thread dump 每份 20 秒、1 MiB，最多 3 台 TM × 2 轮，总上限 6 MiB。其他 raw path 都记为 capability 缺口。
- 原始输出只在内存中解析；报告只保留脱敏后的最短事实、引用和有限样本。

## 身份与 application

优先链：

```bash
bytedcli -j dorado flink monitor get --task-id "$TASK_ID" -r "$DORADO_REGION"
bytedcli -j dorado flink operation-log list \
  --task-id "$TASK_ID" -r "$DORADO_REGION" --page 1 --page-size 20
bytedcli -j dorado task get "$TASK_ID" -r "$DORADO_REGION"
```

只有 task ID 缺失且已有明确 project/owner 范围时，才做有界搜索；候选必须再用 task metadata、名称和归属闭合，不能靠模糊命中直接进入诊断：

```bash
bytedcli -j dorado task advanced-search \
  --project-id "$PROJECT_ID" --keyword "$KEYWORD" \
  --search-scope owner,name,uid --owner "$OWNER" --limit 20 \
  -r "$DORADO_REGION"
```

最近发布或 SQL 变更只作为时间相关候选。固定 task 后，可读取当前代码和指定版本 diff；只有变更时间、失败路径与运行 artifact 能闭合时才确认归因：

```bash
bytedcli -j dorado task code --task-id "$TASK_ID" -r "$DORADO_REGION"
bytedcli -j dorado task diff "$TASK_ID" \
  --from "$FROM_VERSION" --to "$TO_VERSION" -r "$DORADO_REGION"
```

`monitor get` 返回可用 Flink URL 时直接验证。没有 URL 或需要历史 attempt 时：

```bash
bytedcli -j megatron app search \
  --app-name "$JOB_NAME" --application-type Flink -r "$MEGATRON_REGION"
bytedcli -j megatron app get --app-ids "$APPLICATION_ID" -r "$MEGATRON_REGION"
bytedcli -j megatron queue usage --queue-name "$QUEUE" -r "$MEGATRON_REGION"
```

同名 application 必须核对 task tag、application type、state、attempt 和 `_stage` 影子任务。当前 app 不存在时不要只查 `state=RUNNING` 后结束；回看 operation log 和终态 attempt。

Flink Web 已失效时使用离线日志：

```bash
bytedcli -j megatron flink log-link list --app-id "$APPLICATION_ID" -r "$MEGATRON_REGION"
bytedcli -j megatron log list --app-id "$APPLICATION_ID" --attempt "$INCIDENT_ATTEMPT" -r "$MEGATRON_REGION"
bytedcli megatron log get --app-id "$APPLICATION_ID" --attempt "$INCIDENT_ATTEMPT" \
  --file jobmanager.log --tail-bytes 65536 -r "$MEGATRON_REGION"
```

从 `megatron app get` 的 `am_attempts_container_info` 等实际字段固定故障时刻的 attempt、container、start/end、node address 和 exit code。只有已证明 `latest == INCIDENT_ATTEMPT` 时才可用 `latest`；人工重启后的新 attempt 不能替代故障实体。Godel Explainer 需要精确 cluster、namespace 和 workload 坐标，并会创建或读取诊断 artifact，因此不在自动允许列表；缺少精确坐标或授权时记录 capability gap，不把空事件解释成没有 failover 或节点异常。

YARN application ID 形态的 `log-link` 不要直接用于 K8s/Godel；后者先取得实际 proxy URL、pod 或 host。

## Flink runtime

先发现 job、DAG、TM，再查专项证据：

```bash
bytedcli -j --site "$SITE" flink job list --url "$FLINK_URL"
bytedcli -j --site "$SITE" flink job get --url "$FLINK_URL" --job-id "$JOB_ID"
bytedcli -j --site "$SITE" flink job plan get --url "$FLINK_URL" --job-id "$JOB_ID"
bytedcli -j --site "$SITE" flink job exception get --url "$FLINK_URL" --job-id "$JOB_ID"
bytedcli -j --site "$SITE" flink taskmanager list --url "$FLINK_URL"
```

不要硬编码全零 job ID。TM 重建后 ID 会变化，每次从 list 现取。

Checkpoint：

```bash
bytedcli -j --site "$SITE" flink job checkpoint-config get --url "$FLINK_URL" --job-id "$JOB_ID"
bytedcli -j --site "$SITE" flink job checkpoint list --url "$FLINK_URL" --job-id "$JOB_ID"
bytedcli -j --site "$SITE" flink job checkpoint get \
  --url "$FLINK_URL" --job-id "$JOB_ID" --checkpoint-id "$CHECKPOINT_ID"
```

普通规模实体可先列名，再按实际名称取值：

```bash
bytedcli -j --site "$SITE" flink vertex metric list \
  --url "$FLINK_URL" --job-id "$JOB_ID" --vertex-id "$VERTEX_ID"
bytedcli -j --site "$SITE" flink vertex metric list \
  --url "$FLINK_URL" --job-id "$JOB_ID" --vertex-id "$VERTEX_ID" --names '<actual-names>'
bytedcli -j --site "$SITE" flink taskmanager metric list --url "$FLINK_URL" --tm-id "$TM_ID"
bytedcli -j --site "$SITE" flink jobmanager metric list --url "$FLINK_URL"
```

不带 `--names` 时 value 可能全是 null，因为结果只是目录。不要把 null 当无流量。`vertex backpressure get` 返回 deprecated 时改用实际存在的 busy/idle/backpressured metric；两者都不可用时记录缺口。

高并行度 vertex 由 `flink diagnose` 直接从有界 DAG 候选中最多检查 6 个 vertex、12 个代表 subtask；守卫未闭合时，`PERFORMANCE_HIGH_BUSY_EVIDENCE_REQUIRED.argumentMap` 给出固定 metric 白名单。尤其对 7000 并行度 vertex，禁止执行不带 `--names` 的 vertex-wide metric catalog，也禁止代表 subtask catalog discovery。每批最多 100 个名字；单次结构化响应保持 256 KiB，整个性能 metric 分支保持 1 MiB；白名单不匹配或触顶时记录缺口，不能改为 catalog discovery。

## Failover TM 身份证据原生补证

当 `TM lost`、heartbeat timeout、`Pod deleted`/`Pod Terminated`（兼容误拼 `Termated`）等 failover 信号未说明 TM 消失原因时，`flink diagnose` 输出 `FAILOVER_TM_IDENTITY_EVIDENCE_REQUIRED`。只处理其中绑定 incident application 与事件窗口的最多 3 个去重 TM 实体；至少需要 exact `tm-id` 或 `pod-name`，`host-hint` 不能单独通过身份守卫。事件窗口必须不超过 2 小时；恢复后 current TM、泛化文本或字符串猜测不得作为 incident 实体。

执行顺序固定为：

1. 按 [TM 日志公共边界](#tm-日志公共边界) 用原生 `flink taskmanager log list/get` 查 incident TM；
2. 日志在 event 前后 5 分钟内只有明确 OOM/OOMKilled、JVM crash、SIGSEGV 或 `hs_err` 才允许停止 fallback；`Full GC`/`FullGC` 字样不是决定性信号；
3. 日志不可得、截断或无决定性信号时，才按 [Kelemetry/Vela 公共旁证边界](#kelemetryvela-公共旁证边界) 继续；
4. Kelemetry 仅接收 exact Pod；其同窗 allowlisted 唯一 node 才是 verified Vela target。Kelemetry 未唯一绑定且没有 identity conflict 时，显式 `host-hint` 驱动的 Vela 结果只标为 candidate。

整个补证最多使用 1 MiB Kelemetry 和 256 KiB Vela；每条结构化命令仍受 20 秒/256 KiB 上限约束。有 exact Pod 但 Kelemetry 身份冲突，或其唯一 node 与 `host-hint` 冲突时，停止 Vela 并输出 `PLATFORM_RECONCILIATION/PARTIAL`。Kelemetry/Vela 空结果不是健康证据。完整选择与停止规则见 [failover.md](failover.md#不确定-tm-failover日志优先的身份取证)。

## 性能 TM 证据原生补证

high busy 与上游反压或用户报告 lag 同窗出现后，`flink diagnose` 自动对有界 DAG 候选完成 current-attempt placement 校验，选择一个 hottest、一个 control 和必要的 hot subtask；总样本不超过 12 个，最终 TM 不超过 3 台。原生 service 直接复用 Flink/Kelemetry/Vela API，并只构造下面列出的精确 `raw get` 模板。每个 assessment 都分别记录 CPU、锁竞争、同步外部 I/O、线程池等待、network buffer 的支持、反证、缺口与置信度；缺独立旁证时只保留 `LOW/UNKNOWN`。

只允许构造以下 GET path 模板：

```text
/jobs/{job-id}/vertices/{vertex-id}/subtasks/{subtask-index}
/jobs/{job-id}/vertices/{vertex-id}/subtasks/{subtask-index}/metrics?get={allowlisted-names}
/taskmanagers/{tm-id}/thread-dump
```

严格校验 job/vertex/TM ID 与非负 subtask index；从诊断模块常量取得 `{allowlisted-names}` 并编码 query。TM CPU/GC/内存/网络指标同样只用固定白名单调用 `taskmanager metric list --names`。每批不超过 100 个 metric 名；拒绝用户自定义 path、query、metric 名和 catalog 请求。除上述三类模板外不得执行 `flink raw get`。

## TM 日志公共边界

性能代表 TM 与不确定 failover TM 都必须先列文件并检查 size，再以非 JSON 模式读取：

```bash
bytedcli -j --site "$SITE" flink taskmanager log list \
  --url "$FLINK_URL" --tm-id "$TM_ID"
bytedcli --site "$SITE" flink taskmanager log get \
  --url "$FLINK_URL" --tm-id "$TM_ID" --name "$LOG_NAME" --tail 50
```

第二条命令必须由调用方施加每台 stdout+stderr 64 KiB 硬上限。`log list` 返回的源文件 size 必须存在且不超过 64 MiB；否则跳过 `log get` 并记录缺口。相同边界适用于 `jobmanager log list/get`；`taskmanager log get -j --tail` 可能返回完整日志，因此日志内容不得使用 `-j`/`--json`。输出被截断、文件轮转或旧 TM 不可达均表示日志缺口，不表示没有异常。

性能分支在最多 3 台代表 TM 上继续取两轮 thread dump。Failover TM 身份分支则先裁决日志：只有日志不可得、被截断或没有与 event 前后 5 分钟对齐的明确 OOM/OOMKilled、JVM crash、SIGSEGV/`hs_err` 时，才继续 Kelemetry/Vela fallback。

### 性能分支 thread dump

thread dump 只允许以下精确模板：

```bash
bytedcli -j --site "$SITE" flink raw get \
  --url "$FLINK_URL" \
  --path "/taskmanagers/$TM_ID/thread-dump"
```

调用前必须证明 `$TM_ID` 来自 current job/subtask attempt placement，并拒绝含 `/`、`?`、`#` 或路径转义的 ID。每台代表 TM 取两轮，每份执行 20 秒且响应最多 1 MiB；超时或超限时终止命令。只汇总线程状态、重复栈签名、锁 owner 与必要帧，不把原始 dump 写入报告。

## Kelemetry/Vela 公共旁证边界

性能分支对最终代表 TM，使用 current placement 给出的 TM ID 作为已知 Godel Pod 候选、runtime host 作为机器候选。Failover TM 身份分支只在日志 fallback gate 打开后进入：Kelemetry 仅查已绑定 incident attempt 的 exact Pod；Vela 查 Kelemetry 同窗唯一 node，或在 Kelemetry 未唯一绑定且没有 identity conflict 时查显式 `hostHint` 候选。两个分支均使用以下有界命令形状：

```bash
bytedcli -j --no-auto-upgrade --site "$SITE" \
  --http-timeout-ms 15000 --http-retry-count 0 \
  kelemetry search --resource pods --name "$TM_POD" \
  --start "$WINDOW_START_RFC3339" --end "$WINDOW_END_RFC3339" --limit 3

bytedcli -j --no-auto-upgrade --site "$SITE" \
  --http-timeout-ms 15000 --http-retry-count 0 \
  vela one-machine query --selected-name "$RUNTIME_HOST_HINT" \
  --metric agent.alive --metric sys.uptime --metric cpu.busy \
  --metric load.1min --metric cpu.iowait --metric mem.memused.percent \
  --metric sys.proc.blocked --metric disk.io.await \
  --time "$START_MS-$END_MS" --step "$BOUNDED_STEP" --timeout-ms 15000
```

Kelemetry 只能查询已知 Pod 名的 lifecycle trace，不能从 application/JM/TM ID 发现 Pod；只有 namespace 已由平台元数据确认时才附加 `--namespace`。`--cluster` 映射 Jaeger operation，不是 physical/Godel cluster filter，因此不得把 `physicalCluster` 填进去。Vela 的 `selectedName` 也是输入 host/IP，不能从 Pod 反查机器。Failover 分支只把 Kelemetry 同窗 allowlisted 唯一 node 作为 verified Vela target；未经 Kelemetry 验证、仅由 `hostHint` 驱动的 Vela 输出必须标记 candidate。两条命令只能旁证 placement bridge；Kelemetry loose tags/logs 与 `raw` 不进入报告，Vela 必须存在有效 points 且 response `query.selectedName` 与请求一致。Kelemetry 0 trace、Vela 空 points 或查询失败都是缺口，不是 Pod/host 健康证据。

## 历史 metric 与 Dashboard

历史单指标优先 APM，复杂 panel 优先 Grafana：

```bash
bytedcli -j --site "$SITE" apm grafana search 'flink.job.' \
  --tenant "$METRICS_TENANT" --limit 50
bytedcli -j --site "$SITE" apm metric tagk-list \
  --metric flink.job.uptime --tenant "$METRICS_TENANT"
bytedcli -j --site "$SITE" apm grafana query \
  "flink.job.numRestarts{jobname=$JOB_NAME}" \
  --duration 6h --tenant "$METRICS_TENANT" \
  --aggregator max --downsample 5m-max
```

Gauge/ratio 不要使用隐式 `sum + 5m-sum`；显式选择 aggregator/downsample。Metric/tag/operator 路径随版本变化，先 search、tagk-list 或从 Dashboard target 复制实际名字。

```bash
bytedcli -j --site "$SITE" grafana info "$DASHBOARD_URL"
bytedcli -j --site "$SITE" grafana dashboard describe --url "$DASHBOARD_URL"
bytedcli -j --site "$SITE" grafana query "$DASHBOARD_URL" \
  --panel "$PANEL_ID" --from "$FROM" --to "$TO"
```

Dashboard 是可变配置。`grafana query` 返回 datasource target，不执行浏览器 transformation；Used/Total、throttled/period 等 ratio 要按相同 tag/time 重算。实例化示例盘中嵌入的 topic/operator 不可套给其他作业。

常见诊断意图：

| 意图         | 先发现的指标/面板                                                  |
| ------------ | ------------------------------------------------------------------ |
| restart      | job `numRestarts/fullRestarts` 历史 max                            |
| throughput   | operator records in/out rate                                       |
| backpressure | busy/idle/backPressured + buffer pool，按 subtask                  |
| JVM          | heap max/used、GC count/time、direct/metaspace/network memory      |
| checkpoint   | failure、duration、size、start/alignment/sync/upload phases        |
| correctness  | late/dirty/dropped/writeFailed                                     |
| Pod          | CPU/memory limit/request/usage、status/reason、exit code、I/O wait |

## JM 静默历史证据

按 [failover.md 的 JM 静默分支](failover.md#jm-静默或宿主机不可用无-failover) 固定 application、incident attempt、job、site/physical cluster 和窗口。ByteTSD/APM 只查询以下固定意图，不执行 job/vertex metric catalog discovery：

- 诊断 allowlist 中的 job tag schema：`flink.job.uptime`、`flink.job.numRestarts`、`flink.job.fullRestarts`；
- 同一 allowlist 中的 schema：`flink.job.consumerRecordsRate`、`flink.job.numberOfFailedCheckpoints`、`flink.job.numberOfContinuousCheckpointFailure`；
- completed checkpoint 只在已从当前 Dashboard/版本取得准确名字后用 `--checkpoint-completed-metric` 显式传入；不猜名字、不 discovery。

收到 `JM_SILENT_EVIDENCE_REQUIRED` 后，先固定事故 attempt 的唯一 JobManager Pod、namespace 与 cluster，再按 handoff 的窗口执行原生只读查询：

```bash
bytedcli -j --site "$SITE" kelemetry search \
  --resource pods --name "$JM_POD" --namespace "$NAMESPACE" \
  --cluster "$CLUSTER" --start "$WINDOW_START" --end "$WINDOW_END" --limit 3
```

指标 tenant 必须来自当前运行环境或 Dashboard datasource，不得把线上 tenant 固化进 Skill。Megatron 返回的 `app_name` 必须与 ByteTSD `jobName` 精确一致，权威 `physical_cluster/cluster_name` 也必须与 `physicalCluster` 精确一致，冲突立即停止；字段缺失时只有主 application 可继承已验证 join。同机 peer 必须逐个闭合自己的 app name 与 cluster，不能继承主 application 的身份或仅相信参数映射。

按当前 `megatron app get --help` 暴露的路由处理 region：CN/US-TTP 不传 `-r`；需要 vregion 的 i18n/EU site 必须显式给出 allowlist 内的 `--megatron-region`，不得让错误 region 静默回退。

`--restart-unchanged-at-incident` 只能在独立、已规范化且绑定 incident 的正向事实存在时传给 `flink diagnose`；只有 incident 前平坦、随后断流的 ByteTSD counter 不得转换成该 flag。`--platform-running-at-incident` 同样只接受正向证据；缺失表示该守卫未闭合。业务影响按真实证据区分 lag 与 source silence，不得互相改写。跨作业最多检查两个显式已知 peer，不得反查全量应用。

故障后出现新 attempt 时，只有 operation log、人工 restart 记录等独立 artifact 已给出恢复时间，才传可选 `--recovery-time "$RECOVERY_TIME"`；命令只允许 `incident < recovery <= window end`，并把早于该时刻的 replacement 当作反证。不得看到“后来恢复”就猜一个恢复时间。

只有强制守卫闭合时才进入 `JM_SILENT_OR_HOST_UNAVAILABLE`。仍缺守卫证据时输出普通 `UNKNOWN`，不能把“尚未确认静默”写成“静默原因未知”。守卫闭合但 host/peer/node-event 等根因证据缺失时为 `PARTIAL`；只有完整宿主机闭环才可输出高置信度 `JM_HOST_UNAVAILABLE`。

固定查询 6 个已知 ByteTSD 指标（加最多 1 个显式 completed 指标）以及以下 8 个 Vela counter：`agent.alive`、`sys.uptime`、`cpu.busy`、`load.1min`、`cpu.iowait`、`mem.memused.percent`、`sys.proc.blocked`、`disk.io.await`。每个指标只保留有界 first/last/min/max 与点数；任一固定 Vela 指标缺失都会把采集降为 `PARTIAL`，不能让 7/8 等部分响应冒充完整 host 旁证。uptime/source 的派生结果另保留 last-good、first-bad、恢复点和实际采样周期，区分 0、reset、无样本与不对齐 incident 的晚发断点。当前 1 分钟序列要求最近 cadence 不超过 2 分钟，且断点 onset 必须落在 incident 后 2 分钟内；恰从该容差边界或更晚开始的尾断记为 `misaligned`。固定指标在实际 fork/tag 下不可查询时记录 capability gap；不能改为拉取大并行度 vertex catalog。跨作业逐个核对 job/app/physicalCluster、incident attempt、AM/JM container 与 host 绑定；只有 peer JM uptime 同窗断点可参与 host 闭环，peer source 断流不能替代。

## 平台、消息源和宿主机

Godel/Kubernetes 已知 Pod 生命周期：

```bash
bytedcli -j --no-auto-upgrade --site "$SITE" \
  --http-timeout-ms 15000 --http-retry-count 0 \
  kelemetry search --resource pods --name "$POD" \
  --start "$START_RFC3339" --end "$END_RFC3339" --limit 3
bytedcli -j --no-auto-upgrade --site "$SITE" \
  --http-timeout-ms 15000 --http-retry-count 0 \
  kelemetry get --trace-id "$TRACE_ID"
```

Godel Pod 与 Kubernetes Pod 均可查询，classic YARN container 不使用该命令。Pod 名必须先来自 Megatron/Flink/runtime placement；Kelemetry 不是 Pod discovery。只有已验证 namespace 时才加过滤；`--cluster` 是 Jaeger operation，不是 physical/Godel cluster tag。

消息源：

```bash
bytedcli -j bmq consumer list -s "$GROUP" --cluster-name "$CLUSTER" -v "$VREGION" -a
bytedcli -j bmq topic metrics get --topic-name "$TOPIC" --cluster-name "$CLUSTER" -v "$VREGION"
bytedcli -j rmq consumer stats --topic "$TOPIC" --group "$GROUP" \
  --cluster "$CLUSTER" --top-lag-queue 20 -v "$VREGION"
```

BMQ 命令可能只返回元数据和监控 URL，不要假设 consumer list 自带 lag。RMQ stats 可给 TPS、总 lag 和 queue 明细。

宿主机旁证使用以下固定指标命令：

```bash
bytedcli -j --no-auto-upgrade --site "$SITE" \
  --http-timeout-ms 15000 --http-retry-count 0 \
  vela one-machine query \
  --selected-name "$HOST" \
  --metric agent.alive --metric sys.uptime --metric cpu.busy \
  --metric load.1min --metric cpu.iowait --metric mem.memused.percent \
  --metric sys.proc.blocked --metric disk.io.await \
  --time "$START_MS-$END_MS" --step "$BOUNDED_STEP" --timeout-ms 15000
```

`BOUNDED_STEP` 按窗口自适应，最小 60 秒，并把每个 Vela metric 的理论点数限制在约 200 个；24 小时窗口不得仍固定 60 秒采样。输出只保留每个固定 metric 的有界 first/last/min/max、点数和最大断点，不回显全量 series。

placement bridge 必须来自对应时刻的权威 runtime/platform 元数据。JM 使用 incident Megatron AM/JM attempt 的 containerId 定位已知 Godel Pod，由 Kelemetry trace 中严格 allowlist、唯一且同窗的 node 绑定决定 Vela `selectedName`；Megatron `nodeHttpAddress` 只作分域交叉验证。性能 TM 分支使用 current RUNNING subtask attempt 的 TM ID 与 runtime host hint；不确定 failover 分支先固定 incident attempt 的 `tmResourceId/exactPod/hostHint` 并查有界 TM 日志，只在 fallback gate 打开后查 Pod lifecycle 和 host 指标。Kelemetry/Vela 都不是从 application/JM/TM 开始的通用反查接口；缺失、空结果或冲突时输出 `PARTIAL/UNKNOWN`。没有已验证的 host → applications 过滤能力时，禁止为找同机作业扫描全量 application。

当前 Vela 只有 `vela one-machine query`，没有 node lifecycle/availability event 叶子。Vela host 负载高、`agent.alive` 断点、无数据或查询失败都不能证明节点不可用；它们也不能证明 JVM OOM、算子反压或 connector 根因。缺直接节点事件时，JM 静默分支只能输出 `JM_SILENT_CAUSE_UNKNOWN`，不能升格为 `JM_HOST_UNAVAILABLE`。

SIP 默认 biz/filter 可能很窄，空结果前先确认已覆盖目标业务。HDFS 只在异常已出现具体 path/rgroup 且站点支持时查询元数据。

## 发现优先原则

1. 当前 runtime metric：Flink REST。
2. 单一历史指标：APM/ByteTSD。
3. 复杂表达式/多 target：复用当前 Grafana panel。
4. 已知 Godel/Kubernetes Pod lifecycle：Kelemetry；Pod/container placement 仍来自 runtime/platform 元数据。
5. 已定位 host：Vela 旁证。

先发现 endpoint、metric、tag、operator、Dashboard target，再查询。不要把文档示例固化为运行时事实。

## 时间、区域与失败语义

- APM `--start-time/--end-time` 使用 epoch 秒；Grafana 可用 `now-1h` 或明确时间；Vela `--time` 使用毫秒。
- 全局 `--site/--vregion/--vdc`、Dorado/Megatron `-r`、BMQ/RMQ `-v`、APM `--region` 是不同维度。
- 不同指标 tenant 不可互换；消息 lag 可能是独立 datasource。
- 同名作业跨 cluster/site 时同时过滤 job 与 physical cluster。
- 每次执行都以当前 `bytedcli --version`、`--help`、实际 JSON 和 capability discovery 为准；不要把编写本 Skill 时的 CLI 快照当成运行时保证。
