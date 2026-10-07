# series_diagnosis.md — TensorBoard / Wandb 统一诊断流程

当用户明确反馈 Forge 任务的 **TensorBoard 或 Wandb** 数据无点、缺点、稀疏、畸形，或者 `stage_id` / `instance_time` 缺失时，使用本流程。

- Series 路径发现、查询参数和产物格式见 [series.md](series.md)。
- Job 元信息、stage、event、log、metrics、Primus CRD 与热更命令见 [job.md](job.md)。
- 通用 Metrics、DeepInsight 或训练任务生命周期问题不属于本流程，应切换到对应 reference。
- 本文件统一包含公共流程、TensorBoard/Wandb 专用知识和分框架附录，不再读取其他 Series diagnosis reference。
- 每种症状的前序步骤一旦已经得到能解释用户问题的最终结论，应立即停止；不要继续排查或向用户罗列其他未经必要验证的可能原因。

## 强制诊断顺序

凡是 Forge CLI TensorBoard/Wandb 打点异常或相关咨询，必须严格按以下顺序执行；不要跳过症状验证后直接凭经验猜测原因，也不要在已有最终结论后随意扩展排查：

1. **验证症状，匹配症状**：先执行 Step 0 的现场查询，并按“确认症状”表验证用户描述对应的症状；特征不成立时先修正问题描述。
2. **逐步查询任务数据并匹配原因**：只执行该症状规定的步骤，结合对应时间窗、目标 stage、实际生效的 Norbert/Model Code 和附录知识，形成可验证的原因链。
3. **输出最终结论和下一步建议**：仅在证据能解释症状时定性，并给出与该结论直接对应的修复或下一步。不要将未验证的可能性并列为最终原因。

## 目录

1. [确认症状](#确认症状)
2. [Step 0：确认问题现场](#step-0确认问题现场)
3. [症状 1：整个 Job 无点](#症状-1整个-job-无点)
4. [症状 2：整个 Job 打点慢](#症状-2整个-job-打点慢)
5. [症状 3：部分 Path 无点](#症状-3部分-path-无点)
6. [症状 4：部分 step/event_time 无点或打点稀疏](#症状-4部分-stepevent_time-无点或打点稀疏)
7. [症状 5：部分数据类型无点](#症状-5部分数据类型无点)
8. [症状 6：畸形数据](#症状-6畸形数据)
9. [症状 7：stage_id / instance_time 缺失](#症状-7stage_id--instance_time-缺失)
10. [附录 A：各框架须知](#附录-a各框架须知)
11. [附录 B：常见打点日志错误 pattern](#附录-b常见打点日志错误-pattern)
12. [附录 C：Model Code 常见编码问题索引](#附录-cmodel-code-常见编码问题索引)
13. [附录 D：Series 系统后端 SLA 指标](#附录-dseries-系统后端-sla-指标)

## 确认症状

根据用户描述和 Series 查询结果确定需要诊断的症状。

- 用户已给出症状时，先用“确认特征”验证。特征不成立时，引导用户修正问题描述。
- 用户只说“打点异常”“没数”等宽泛描述时，按下表顺序识别所有存在的症状。

| 症状 | 确认特征 | 必要追问 |
|---|---|---|
| 整个 Job 无点 | 对预期 source 执行 Series `get-meta`，查不到任何 path | 无 |
| 整个 Job 打点慢 | 用户此前声称“无点”，或直接反馈打点慢 / 曲线很久才更新；`get-meta` 已有大量 path，且任意已有 path 的 `event_time` 普遍相隔超过 10 分钟，可能达到小时级 | 无 |
| 部分 Path 无点 | `get-meta` 非空，但缺少用户指定的 path 或 path pattern | 用户未提供具体 path 时追问 |
| 部分 `step/event_time` 无点 | 查询指定 path、框架代表 path，或任意 path 后，用户指定的 step/时间范围无点 | 用户未提供缺失范围时追问 |
| 部分数据类型无点 | 已存在部分 `scalar` / `histogram` / `image` path，但缺少其中一种或多种 | 无 |
| 数据畸形 | `get-meta/query` 均正常，但数据表现与常见情况不同 | 排除以上异常后，让用户明确描述畸形现象 |
| `stage_id` / `instance_time` 缺失 | 返回点中的对应字段全部为 `0` | 无 |
| 其他咨询 | 以上均不符合 | 结合用户问题、Model Code 和附录现场判断 |

## Step 0：确认问题现场

1. 通过用户文本或 URL 确认 `site` 和 `job_id`。site 不清晰或存在冲突时先追问。
2. 查询 Job 元信息：

   ```bash
   forge job meta get --job-id <job-id> --site <site>
   ```

3. 确认 `framework`，并直接推断预期 source：
   - `sail` / `sail_dev` → TensorBoard
   - `lite` → TensorBoard
   - `torch` → Wandb
4. 确认用户询问的是 TensorBoard/Wandb，而不是 DeepInsight 或通用训练 Metrics；否则切换到对应 reference。
5. 用预期 source 的 `get-meta/query` 验证症状。命令语法见 [series.md](series.md)。
   - `get-meta` 非空、但用户反馈“无点/很久才出现点”时，**必须**选择一个当前可见的代表性 scalar path，以目标 stage 的 `start_time/end_time` 作为 `--event-time-min/--event-time-max` 查询窗口。
   - 计算相邻 points 的 `event_time` 间隔；若多数间隔超过 10 分钟，优先归类为“症状 2：整个 Job 打点慢”，不要继续按“症状 1：整个 Job 无点”诊断。

### Stage 与时间窗口边界

- TensorBoard/Wandb 数据按 `job_id` 聚合，不强依赖 `stage_id`。**禁止**根据某一个 stage（尤其 latest stage）尚未进入 training、已结束或无日志，推断整个 Job 没有/缺少打点。
- Series `get-meta` / `query` 不绑定 `stage_id`：`get-meta` 无范围参数；`query` 必须用 `--step-min` / `--step-max` 或 `--event-time-min` / `--event-time-max` 将结果限制在用户症状所在的时间段。症状、查询结果与最终结论必须处于同一时间窗。
- `meta get`、`event get-meta/query`、`log get-meta/query`、`metrics get-meta/query` 会按 `stage_id` 查询；省略 `--stage-id` 时通常落到 latest stage。凡是用这些结果解释指定历史阶段的 Series，必须显式传入目标 `--stage-id`，而不是使用默认结果。
- `forge job log get-meta --stage-id <stage-id>` 会把日志类型与可选 Primus role 发现限制到显式选择的 stage；省略 `--stage-id` 时选择 latest stage。显式 stage 必须唯一报告所请求的 stage identity，并且归属于所请求的 job；身份缺失、冲突或跨 job 时命令会拒绝结果。
- 显式 stage 被拒绝时，先运行 `forge job stage list --job-id <job-id> --site <site>`，从返回结果中选择确属该 job 的 `stage_id` 后重试。若 job/stage 配对正确时仍返回身份缺失或冲突，停止使用该 stage 响应作为诊断证据，不要改用 latest stage 或盲目重试；向 Forge Oncall 提供 `site`、`job_id`、`stage_id` 和完整错误信息。
- 日志内容仍应使用同一 `--stage-id` 的 `forge job log query` 或该 stage 的实际 Primus/Flink 日志确认。
- Norbert/Model Code 通过 `forge code commit get --commit-id <commit-id>` 读取，命令本身不绑定 stage；用于诊断时，`commit-id` 必须来自目标 stage。

向用户输出当前现场：

```text
当前排查的是 {site} 站点的 Job {job_id}
- Job 状态：{status}
- 启动时间：{job_start_time}
- 结束时间：{job_end_time / 仍在运行}
- framework：{framework}
- Series source：{tensorboard / wandb}
- 已确认的症状：{症状列表}
现在开始诊断：{当前症状}
```

## 症状 1：整个 Job 无点

按 Step 1.1 → 1.2 → 1.3 → 2 → 3 → 4 检查。形成确定结论后即可停止，不需要强行执行后续步骤。

### Step 1.1：旧 Job 检查

查询 Job 的开始/结束时间，并在需要时查询 Norbert 与 Primus CRD 更新历史：

```bash
forge job meta get --job-id <job-id> --site <site>
forge job norbert-commit list --job-id <job-id> --site <site>
forge job primus-crd list --job-id <job-id> --site <site>
```

诊断规则：

- **TTL**：当前 Forge Series 系统使用三个月数据 TTL。终止 Job 的 `job_end_time` 距今达到三个月时，结论为“打点数据已过期”。
- **旧式任务**：运行中的 Job 早于对应 source 的“有点最小值”，并且在该时间之后没有 Norbert/Primus CRD 更新时，可判断旧式任务不支持当前 Series 链路。
  - TensorBoard：最小 `job_id=1578410`；最小 `start_time=2022-02-23 00:25:36 +08:00`
  - Wandb：最小 `job_id=12477057`；最小 `start_time=2025-10-29 19:36:43 +08:00`
- Job 为 `success` / `failed` / `killed` 不代表数据不可查询；只要未过 TTL，已写数据仍可存在。

中间结论至少包含：

```text
任务启动时间：{job_start_time}
任务结束时间：{job_end_time / 仍在运行}
最近一次 Norbert/Primus 更新：{last_update_time / 无}
{如已确定} 结论：数据已过期 / 旧式任务不支持当前打点链路
```

### Step 1.2：样本消费、GlobalStep 与 steps_interval 等效配置

#### 1. 查询样本吞吐

优先按 framework 使用 [job.md](job.md) 中的映射：

```bash
forge job metrics query \
  --job-id <job-id> \
  --stage-id <stage-id> \
  --metric-name <framework 对应吞吐指标> \
  --site <site>
```

- Sail/Sail Dev/Torch 通常使用 `metrics/sailor/read_instance`。
- Lite 使用 `metrics/lite/read_instance`。
- framework 未知或指标不可用时，先用 `metrics get-meta` 找可用路径。

若目标时间范围内样本吞吐完全为空，结论为“任务尚未进行样本消费”；后续调度、错误事件和训练生命周期问题交给 Job 诊断流程。

#### 2. 查询 current global_step 与 checkpoint offset

先按[附录 A](#附录-a各框架须知)中的 `series role_name`、`series log file` 和 `current global_step 日志 pattern` 查询目标 stage 的训练日志：

```bash
forge job log get-meta \
  --job-id <job-id> \
  --stage-id <stage-id> \
  --with-roles \
  --site <site>

forge job log query \
  --job-id <job-id> \
  --stage-id <stage-id> \
  --log-type primus \
  --role <series-role-name> \
  --log-file <series-log-file> \
  --keyword "<稳定日志关键词>" \
  --seek tail \
  --limit 1000 \
  --site <site>
```

- Flink 任务在 worker-0 所在 TaskExecutor 日志中使用对应 pattern。
- Torch/Wandb 的 `trainer-runner` 日志文件名必须精确匹配，不能将附录中的 `<...>` 视为通配符。优先针对 `globalrank_0` 依次尝试以下两种实际文件名形态，使用目标 runtime 实际的 `<period>` / `<failover>` / `<YYYYmmddHHMMSS>` 值：
  - `runner_ver_<period>_<failover>_globalrank_0_localrank_0_createtime_<YYYYmmddHHMMSS>.log`
  - `runner_ver_<period>_<failover>_globalrank_0_localrank_0.log`
  哪一种能够查询到目标日志，就使用该文件继续搜索 `forge_wandb`、缺失 path 和异常 pattern。
- 取最新一条匹配日志中的 `<N>`，作为该日志时刻已经确认的精确 global_step。
- 日志查询成功且命中可持续打印的 pattern 时，以日志证据为准。
- 日志不可查、超时、返回 40x、没有命中，或者附录明确说明 pattern 只覆盖启动/前若干步时，改用下方 Metrics 粗略查询；不要把旧的有界日志值当成任务当前进度。

Metrics 查询更快，常见 framework 通常也更容易取得：

```bash
forge job metrics query \
  --job-id <job-id> \
  --stage-id <stage-id> \
  --metric-name metrics/model/global_step \
  --site <site>
```

- 该指标用于粗略估算当前进度，以及判断 `current_global_step - checkpoint_offset` 是否明显小于 `steps_interval 等效配置`。
- Lite 暂无可靠的 Metrics current global_step 查询方式。优先使用附录中的 Lite 日志 pattern；日志也无法确认时，明确向用户说明当前累计 global_step 无法可靠取得，不要把 Lite step-rate、Series `step` 或原始 `x_value` 解释成当前累计 global_step。
- checkpoint offset 的日志查询方法见[附录 A](#附录-a各框架须知)。附录未提供时，明确提示无法可靠取得 offset。

#### 3. 定位生效的 steps_interval 等效配置

1. 根据无点时间范围找到对应 stage。
2. 根据 stage 的 `train_mode`、`is_catchup` 等信息定位实际生效的 Norbert 配置。
3. 读取提交到该 Job 的 Norbert Code，而不是只读当前 checkout 或用户 Model Code。
4. 不要只做全局字符串搜索；必须确认命中的配置确实赋给目标 stage 和负责打点的 role。
5. `steps_interval 等效配置` 的 gflag 不一定名为 `steps_interval`，以附录中的实际 gflag 和默认值为准。例如部分 Sail 任务的 `sailor_args` 不控制 `base-runner`，真正生效的打点 role 配置可能在 `pilot_args`；该例不能泛化为所有 Sail framework。

各框架 flag、默认值和生效逻辑见[附录 A](#附录-a各框架须知)。

诊断规则：

- 只有确认具体框架的最终生效 interval 为 `0` 后，才能结论为“任务手动关闭了 TensorBoard / Wandb 打点”。
  - 如果预期 source 的 scalar / histogram / image `get-meta` 均为空，且目标无点时间窗中负责发送的 role 实际使用该值 `0`，此结论为最终结论：停止后续并发、日志、Model Code 和 SLA 排查。
  - 之后的 Primus CRD 热更历史只能补充说明“配置曾被更新”；除非同一时间窗有 Series 或日志直接证明新配置已生效，不要推测进程是否重启、是否重载 gflag 或 EventWriter/Databus 是否仍失败。
- interval 很大，且 `current_global_step - checkpoint_offset` 尚未明显超过该等效配置，启动不足 12 小时时，可结论为“任务尚未运行到第一个打点间隔”。
- 用户明确配置了远超默认值的 interval 时，应说明这很可能是有意降低频率，而不是平台异常。

#### 4. 检查影响打点的其他 gflags

- `job_id=<other_job_id>` 或 `forge_job_id=<other_job_id>`
  - 所有打点类型与框架均可能受影响。
  - 该值会覆盖当前 Job/Stage 的打点归属，导致当前 Job 查询不到点，而点被写归到指定的 Job ID。
  - 必须以目标 stage 实际生效的 Norbert gflags 为准；命中后，在同一时间窗查询被指定 Job ID 的预期 source/data type，确认是否出现当前任务的点。
  - 建议删除该调试用覆盖 flag，防止其继续传播到后续任务。
- `use_databus_save_tfevent=false`
  - TensorBoard；常见于 Sailor、`dandelion_v2`、`sailor_primus`、`sailor_flink`。
  - tfevent 改走旧 HDFS/本地文件链路，当前 Forge TensorBoard `get-meta/query` 可能为空。
  - 建议删除或设为 `true`；已按旧链路运行的任务通常需要新启。
- `databus_topic=<topic>`
  - TensorBoard；适用于所有使用 TensorBoard 的框架，包括 Sail / Lite。以目标 stage 实际生效值为准。
  - 当前 Forge Series 预期 `tfboard_event_v2`；`tfboard_event`、`tfboard_event_sandbox` 或其他非当前消费 topic 会使 Event 写入 Databus 但不进入当前 Forge Series，`get-meta/query` 可能为空。
  - `tensorboard.event_write status=ok` 或日志 `to databus OK` 只证明发送到该 topic 成功，不能证明当前 Forge Series 已消费。
  - 若实际生效值为 `tfboard_event_v2`，或目标 runtime 的默认值已解析为该值，不要将此 flag 作为无点原因；否则建议显式设置 `databus_topic=tfboard_event_v2` 并新启任务。
- `enable_summary=false`
  - TensorBoard；主要影响 Jaguar 编译链路。
  - 跳过 summary 收集与 merge；旧版本仍可能生效。
- `summary_output_bus=""` 或非 `tfboard_event`
  - TensorBoard；影响 Dandelion V3、Lagrange TF Async/Sync、Jaguar。
  - 空值会记录 `status=no_databus` 并跳过发送；错误 channel 可能发送到非 Forge 消费链路。
- `wandb_log_all_ranks=true`
  - Wandb；默认仅 rank 0 写。
  - 开启后 path 变成 `<path>/rank_<rank_id>`，增加 path/payload 数量；查询原 path 可能误判缺失。

向用户输出：

```text
样本吞吐：{存在 / 不存在}
current global_step：{value / 无法可靠查询}
checkpoint global_step offset：{value / 无法可靠查询}
steps_interval 等效配置：{flag_name}={effective_value}（默认 {default_value}）
{如已确定} 结论：尚未消费样本 / 已关闭打点 / 尚未到首个打点间隔 / 特殊 gflag 改变了打点链路
```

当确认“已关闭打点”时，优先简明输出：

```text
任务确实完全没有 {TensorBoard/Wandb} 打点。
根因：负责发送的 {role_name} 在目标无点时间窗使用 {flag_name}=0，等效关闭打点。
建议：后续新任务启动时将该配置设为正值；已结束任务无法回填历史打点。
```

### Step 1.3：并发程度

先定位用户询问的 stage，再根据 `stage.task_type` 判断 Primus 或 Flink。

- Primus：
  1. 从 `job meta get --stage-id` 获取 `primus_history_url`。
  2. 结合 `forge job primus-crd get` 确认 training_framework 对应的实际 CRD role。
  3. 在 Primus History 中统计该 role 下 `state=RUNNING` 的具体 executor attempts 数量，作为有效并发 pod 数。
- Flink：
  1. 从元信息获取 `dorado_url`。
  2. 在 Flink Dashboard 或 REST `/taskmanagers` 统计已注册 TaskManager 数量。

仅当同时满足以下条件时，才可结论为“任务并发过大，在当前框架打点体系中导致 TensorBoard 打点 role 很难见到 `steps_interval` 等效配置对应位置的样本”：

- 并发 worker 超过 `20`；
- [附录 A](#附录-a各框架须知)标记该 framework 的打点可能受并发数量抽样影响；且
- 任务尚未运行很久：目标 stage 的样本消费与 current global_step 进展仍不大，尚未明显超过该框架的首个/正常打点等待范围。

用户建议：减少 Primus/Flink 作业中发送 role 的 replica 数量，或接受打点频率被稀释并维持现状。

若任务已有较长时间、且样本消费与 current global_step 指标均持续且数值较大，并发过多不能解释“整个 Job 完全无点”；继续按后续日志、配置和 Model Code 步骤诊断，禁止将根因归为并发抽样。

### Step 2：打点日志异常

1. 按无点时间定位 stage，并按[附录 A](#附录-a各框架须知)选择 `series role_name` 和日志文件。
2. 先查询任务元信息中的实际运行 DC。对于 Wandb，若 DC 为 `my`、`useast5`、`useast8` 或 `usttp`，优先怀疑旧版 Wandb SDK 无法路由/连接后端：
   - 继续按[附录 B](#附录-b常见打点日志错误-pattern)查询 IDC/Region 错配或连接异常，取得日志证据后直接定性。
   - 若日志查询受阻，仍应向用户保留该高优先级怀疑，并建议按附录升级覆盖当前 DC 的 Torch/bytedance.wandb；不要改为无依据地优先猜测其他 AdHoc 原因。
3. 对其余场景或上述假设未证实时，按[附录 B](#附录-b常见打点日志错误-pattern)匹配日志 pattern。
4. 命中后直接输出问题类型、异常说明和下一步建议。
5. 不在表内的错误只能作为辅助证据，除非日志足以直接证明根因。

用户输出：

```text
已检查打点日志：
- training_framework：{value}
- stage_id：{value}
- role：{role_name}
- log_file：{log_file}
- 关键异常：{pattern / 未发现}
{如命中} 结论：{异常说明}
建议：{下一步建议}
```

### Step 3：框架版本与 Model Code

1. 取得该 Job 实际使用的 Model commit，并按顶层 Skill 的 exact-commit source guard 获取代码；不要用当前/default framework checkout 替代。
2. 按 framework/source 和[附录 C](#附录-cmodel-code-常见编码问题索引)逐条匹配 Model Code pattern。
3. 使用“补充特征”确认匹配，不要只凭一个字符串就下结论。只有 pattern 与对应“补充特征”均得到确凿验证后，才能将该编码问题作为最终结论；否则仅作为待排查线索，继续诊断。
4. 未命中已知 pattern 且仍无固定结论时，必须基于该 Job 的 exact Model Code 进行 AdHoc 诊断，不能以“索引未命中”结束排查。
   - 先检查用户是否手动改写 `wandb_data_manager.is_recording_scalar` 或同类记录状态/控制属性。用户不熟悉框架控制逻辑时容易将其改坏，导致 Wandb 打点被整体或局部关闭；必须结合赋值点、外层条件和缺失 path 验证影响范围。
   - 未发现上述高优先级控制属性问题时，再检查其他用户代码 bug、错误控制开关或错误分支条件；深入分析打点调用所在的实际执行路径，定位可能有问题的代码位置，说明其影响机制，并提出具体修改建议。

用户输出：

```text
已检查任务 Model Code
{如命中} 已知 pattern：{pattern}
问题说明：{说明}
建议：{对用户建议}
```

### Step 4：SLA

只有任务状态、配置、指标、日志和代码问题均排除后，才检查任务所在 site 的 Series 后端 SLA。

- 指标见[附录 D](#附录-dseries-系统后端-sla-指标)。
- 查询环境必须支持目标 site 的 Metrics。
- 若过去若干小时对应 source/data_type 的 job count 骤降至接近 `0`，指引用户对 Forge 平台发起 oncall。

## 症状 2：整个 Job 打点慢

进入本症状前，必须确认：

- 用户此前声称“无点”，或直接反馈打点慢 / 曲线很久才更新；`get-meta` 已有大量 path；且
- 查询任意已有 path 后，`event_time` 间隔普遍超过 10 分钟，可能达到小时级。

**必须先向用户说明**：任务实际上有打点；在目标 stage 时间窗内，代表性 path 的相邻点间隔约为 `{gap_summary}`，因此任务启动后短时间内可能看不到新点。

沿用症状 1 的部分流程，但按以下顺序缩小范围：

1. 读取该 Job 的实际 Norbert Code，定位负责打点 role 的 `steps_interval 等效配置`。
2. 与[附录 A](#附录-a各框架须知)中该 framework 的默认值比较：
   - 如果实际值没有显著小于默认值，结论为“任务实际配置的 `{flag_name}={effective_value}` 仍会导致打点间隔较长”。
   - 说明当前频率可能符合任务预期；如果需要更密集打点，建议用户调小该 gflag。
3. 若多个代表性 path 的间隔均较长且分布大致一致，以上结论已解释用户现象，**到此停止**。
4. 只有满足任一条件时，才继续执行症状 1 的 Step 1.3（并发程度）和 Step 2（打点日志异常）：
   - 若干 path 的 `event_time` 间隔明显不均匀，或不同 path 之间存在显著差异；或
   - 用户明确反馈问题仅限于部分 path。

不要为本症状重复执行旧 Job、样本吞吐、current global_step/checkpoint offset、Model Code 或 SLA 检查。也不要因无法关联到用户指定 path 与同一时间窗口的单条训练日志异常继续展开排查。

## 症状 3：部分 Path 无点

沿用症状 1 的部分流程，但：

- 跳过 Step 1.1、1.2、1.3、4。已有其他 path 能产出，说明任务不属于旧任务、已达到打点位置，并且没有整站 SLA 故障。
- 如果其他 path 的打点量已很大，不要仅因任务提前结束、训练只完成一部分或后续 step 未运行，就把缺失 path 归因于训练未完全执行。只有读取 exact Model Code 后，取得与该缺失 path 的训练进度 / step / 运行分支直接相关的证据，才能作此结论。
- 对 Sail/Lite 的 TensorFlow 静态图训练，先搜索 `<代码 path>_<N>`（如 `loss_1`、`loss_2`）：TensorFlow 会在同名节点或 summary 建图时自动追加 `_N` 以保证唯一名称。若后缀 path 存在，应向用户说明实际 path 名称并检查是否有同名计算节点或同名 summary；Torch/Wandb 不适用此规则。
- 对 Torch/Wandb，若用户指定 path 缺失，先搜索 `<path>/rank_<rank_id>`，并确认目标 stage 的 `wandb_log_all_ranks`：
  - 默认或 `false` 时仅 rank 0 写入，Model Code 指定的 path 不会被改写。
  - `true` 时所有 rank 都写入，path 改为 `<path>/rank_<rank_id>`，查询原始未带 rank 后缀的 path 可能查不到。
  - 命中时向用户说明该机制；若并非有意配置，建议去掉该 gflag。
- 执行 Step 2 时，带入缺失 path 或 path family 搜索日志。
- 执行 Step 3 时，重点检查缺失 path 的打点代码、构图和运行分支；与正常用户打点的 Model Code 对比，归纳缺失 path 共同的代码 pattern 或外层控制条件。

## 症状 4：部分 step/event_time 无点或打点稀疏

沿用症状 1 的流程，并使用缺失时间范围约束所有 stage-scoped 查询。

- Series query 主要使用 `--step-min` / `--step-max` 或 `--event-time-min` / `--event-time-max` 成对缩小范围。
- Job metrics/log/event 若存在 latest-stage 默认逻辑，应显式指定缺失时段对应的 `stage_id`。

### 双层降采样

TensorBoard 与 Wandb 均适用：

1. 写入侧按时间桶保留数据：
   - Scalar：30 秒一个桶
   - Histogram：5 分钟一个桶
   - Image：60 秒一个桶
2. 查询侧会对宽范围结果继续抽样；长期任务尤其容易显得稀疏。
3. 缩小 `step/event_time` 范围，比较窄范围结果是否更密。

只有实测窄范围能够返回更多局部点时，才把稀疏归因于查询抽样；缩小范围不能恢复训练侧未发送或写入侧已经合并的点。

```text
经宽/窄范围对照，原查询的部分稀疏由查询抽样造成；
限制到 {new_range} 后可以返回更多局部点。
```

其他检查：

- 跳过 Step 1.1 和 Step 3：同一路径其他 step/time 有点，通常不属于旧任务或静态构图问题。
- 最新一段无点时，检查 interval 是否远大于默认值。
- 对受并发影响的框架，检查缺失窗口内并发是否过大。
- 执行 Step 2，重点匹配 NaN/Inf、payload oversize 和发送中断。
- 缺失的是最新时间段且其他问题均排除后，再检查 Step 4。

## 症状 5：部分数据类型无点

例如 scalar 正常但 histogram/image 缺失。

- 跳过 Step 1.1、1.3、4：已有其他数据类型，说明 Job 不旧、训练有进展，并且不是整站 SLA 故障。
- 对 Torch/Wandb，按需执行 Step 1.2 的相关部分：
  - 不同 data type 可能使用不同 `steps_interval` 等效配置；以附录 A 的 data-type 默认值和目标 stage 实际生效的 Norbert 配置为准。
  - 查询样本吞吐和 current global_step。若不同 data type 的实际有效 interval 有区别，且当前进展尚未明显超过相应 interval，可怀疑不同 interval 导致首个打点时机不同。
- 执行 Step 2：按缺失数据类型查 payload oversize、NaN/Inf、发送失败。
- 执行 Step 3：对比正常与异常数据类型的 Model Code、构图和运行分支。

## 症状 6：畸形数据

无需执行症状 1 全流程，按下表处理。

| 畸形现象 | 适用范围 | 确认方法 | 说明与建议 |
|---|---|---|---|
| 大量 points 堆积在少数 step | TensorBoard Scalar | 查询代表性 scalar path，同时比较 `step` 与 `event_time`；`event_time` 连续但 `step` 大量重复/压缩时，确认是 step 轴畸形 | 常见方向是很大的 `global_step` 叠加 bf16/混合精度造成精度损失。当前任务优先使用时间轴；后续任务检查 bf16 配置，必要时清理或重新设计 `global_step` |
| 首个可见 step 很大或不从 0 开始 | TensorBoard/Wandb Scalar | 检查 checkpoint/resume 上下文，并比较首点后的 `event_time` 与相邻 path 是否连续 | checkpoint 可能自带 `global_step` offset；后续曲线连续时，不应单独判断为数据畸形或丢点 |
| Image 数据缺失或不完整 | TensorBoard Image | 确认 image path，并查询 exact path 检查实际 frames | 检查单张 PNG 是否超过 100 KB、`max_outputs` 是否过大、image interval 是否过稀、UI sample count 是否过小；相应减少尺寸/数量/频率或提高 UI sample count |
| Scalar 的 mean 等统计值不符合预期 | TensorBoard/Wandb Scalar | 从原查询的 `step/event_time` 范围抽取多个更小窗口重新查询；只有窄窗口结果明显更密或统计结果改善时，才确认查询侧抽样是原因 | 宽范围查询会再次抽样，可能隐藏中间点并影响基于返回点计算的统计值。建议缩小范围复核；若窄窗口没有改善，继续排查训练数据或其他业务原因 |
| 打点间隔过长/过短，或修改 interval 后未生效 | TensorBoard/Wandb 所有数据类型 | 按 Step 1.2 定位目标 stage、打点 role 和实际 Norbert 配置，确认 `steps_interval 等效配置` 的具体 gflag、最终值及是否偏离默认值 | 向用户指出实际生效的代码位置、变量名和值，建议调整到框架默认值附近；不要只根据同名变量或未赋给目标 stage/role 的配置下结论 |

## 症状 7：stage_id / instance_time 缺失

- 该症状通常来自旧框架版本对新字段支持不足，无需执行症状 1 全流程。
- 建议用户升级所使用的 Sail/Torch/Lite 框架；2026 H2 之后版本可作为优先选择方向。
- 该字段缺失不等同于所有 Series 数据缺失。

## 附录 A：各框架须知

空单元格表示当前没有稳定、可复用的查询方法，诊断时不要自行猜测。

| framework / training_framework | source | 代表性 path | series role_name | 受并发影响 | series log file | 打点发送 metric | steps_interval 与默认值 | current global_step metric（参考） | current global_step 日志 pattern | checkpoint global_step 日志 pattern | 备注 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| sail / lagrange_tensorflow_sync | tensorboard | `sparse_bias_lr_scaling`<br>`sparse_vec_lr_scaling` | base-runner | 否 | `runner_0.log` | `data.jaguar.worker.tensorboard.databus.send`；过滤 `model={model_name}`、`job_id`；`status=success` 成功，其他有 `no_databus/dbus_send_err/exception` | `tf_summary_interval` = `2000` | `data.jaguar.worker.batch.global_step`；`model_name={model_name}` 或 `global_worker_idx=0` | `runner_0.log`；取最新 `start current step: <N>` / `current step: <N>, run target: ...` / `finish current step: <N>`。前 100 step 逐步打印，之后按 step 数量级周期打印 | 见本表后的“Base-runner checkpoint pattern” | 当前 SummaryPlugin 链路 |
| sail / lagrange_tensorflow_async | tensorboard |  | base-runner | 是 | `runner_0.log` | `data.dandelion.worker.tensorboard.databus.send`；`status=success`；生成侧可辅查 `data.dandelion.worker.tensor_event_throughput` | `summary_interval` = `1000` | `data.dandelion.{model_name}.dandelion.session_run.step.max`；`worker_id=0` | 参考以上 base-runner 框架 | 参考 Base-runner | 仅 chief/worker 0 发送 |
| sail / jaguar | tensorboard | `sparse_bias_lr_scaling`<br>`sparse_vec_lr_scaling` | jaguar-worker | 否 | `jaguar_worker_0.log` | `data.jaguar.worker.tensorboard.databus.send`；`status=success` | `tf_summary_interval` = `2000` | `data.jaguar.worker.batch.global_step`；`model_name={model_name}` 或 `global_worker_idx=0` | 持续进度取最新 `Recent <seconds> s: throughput ... total <N> steps`；前 `display_step`（默认 100）步也可匹配 `Step <N> finished. (log only for first <limit> steps)` |  | 仅 `global_worker_idx=0` 发送 |
| sail / dandelion_v2 | tensorboard |  | sailor | 是 | `stderr.log` | `data.oracle.{model_name}.tensorboard.event_write`；`type=event,status=ok` 成功，`status=err` 失败；生成侧可辅查 `data.oracle.{model_name}.tensor_event_throughput` | `summary_sample_rate` = `10` | `data.oracle.{model_name}.tensor_event_value.step` | 默认无持续 current global_step 日志，使用 `metrics/model/global_step`。仅非默认配置 `startup_delay_factor` 时可匹配 `waiting for startup delay, current step: <N>, expected: ...` / `startup_delay_by_step success, current step: <N>, expected: ...`；只覆盖启动延迟阶段 |  | Sailor EventWriter |
| sail / dandelion_v3 | tensorboard |  | base-runner | 是 | `runner_0.log` | `data.dandelion.worker.tensorboard.databus.send`；`status=success`；生成侧可辅查 `data.dandelion.worker.tensor_event_throughput` | `summary_interval` = `1000` | `data.dandelion.{model_name}.dandelion.session_run.step.max`；`worker_id=0` | 参考以上 base-runner 框架 | 参考 Base-runner | 仅 chief/worker 0 发送 |
| sail / sailor_flink | tensorboard |  | taskmanager | 是 | worker-0 所在 TaskExecutor 日志；常见 `flink-*-taskexecutor-*.log` | `data.oracle.{model_name}.tensorboard.event_write`；`type=event,status=ok`；生成侧可辅查 `data.oracle.{model_name}.tensor_event_throughput` | `summary_sample_rate` = `10` | `data.oracle.{model_name}.tensor_event_value.step` | 参考以上 Sailor 框架；在 worker-0 所在 TaskExecutor 日志中查询 |  | Sailor EventWriter |
| sail / sailor_primus | tensorboard |  | sailor | 是 | `stderr.log` | `data.oracle.{model_name}.tensorboard.event_write`；`type=event,status=ok`；生成侧可辅查 `data.oracle.{model_name}.tensor_event_throughput` | `summary_sample_rate` = `10` | `data.oracle.{model_name}.tensor_event_value.step` | 参考以上 Sailor 框架 |  | Summary node 为 worker 0/1 的 thread 0 |
| torch / lagrange_torch_sync | wandb | `framework/clip_norm/dense_clip_norm` | trainer-runner | 否 | 依次尝试 `runner_ver_<period>_<failover>_globalrank_0_localrank_0_createtime_<YYYYmmddHHMMSS>.log` 或 `runner_ver_<period>_<failover>_globalrank_0_localrank_0.log`；`--log-file` 不支持通配符，使用实际可查询的 `globalrank_0` 文件 | `data.reckon.forge_wandb.sdk.user.log.count` 可按 `job_id / stage_id / path / log_type` 证明 SDK 收到输入；`data.reckon.forge_wandb.api.send.count` / `data.reckon.forge_wandb.api.fail.count` 是服务级指标，不能单独证明单 Job 成功 | Scalar=`max(wandb_log_interval_steps, wandb_log_scalar_interval_steps)`，默认 `max(100,0)`；Histogram=`max(wandb_log_interval_steps, wandb_log_histogram_interval_steps)`，默认 `max(100,1000)` | `data.oracle.worker.{model_name}.batch.global_step`；`worker_index=0` | rank 0 日志匹配 `Step <N> finished`。默认只打印前 `print_step_limits=100` 个本地 step；超过限制后回退 `metrics/model/global_step` | 见本表后的“Trainer-runner checkpoint pattern” | 默认仅 rank 0；过滤可查 `data.reckon.forge_wandb.sdk.user.log.check.filtered.count` |
| torch / lagrange_torch_async | wandb | `framework/clip_norm/dense_clip_norm` | trainer-runner | 否 | 同上 | 同上 | 同上 | 同上 | 参考以上 trainer-runner 框架 | 参考 Trainer-runner | 默认仅 rank 0 |
| torch / nova_sync | wandb | `framework/clip_norm/dense_clip_norm` | trainer-runner | 否 | 同上 | 同上 | 同上 | 同上 | 参考以上 trainer-runner 框架 | 参考 Trainer-runner | 默认仅 rank 0 |
| torch / nova_async | wandb | `framework/clip_norm/dense_clip_norm` | trainer-runner | 否 | 同上 | 同上 | 同上 | 同上 | 参考以上 trainer-runner 框架 | 参考 Trainer-runner | 默认仅 rank 0 |
| torch / nova_omni | wandb | `framework/clip_norm/dense_clip_norm` | trainer-runner | 否 | 同上 | 同上 | 同上 | 同上 | 参考以上 trainer-runner 框架 | 参考 Trainer-runner | 默认仅 rank 0 |
| lite | tensorboard |  | chief | 是 |  | `data.aml.lagrange_lite.tfb.send`；过滤 `model={model_name}`、`task=chief-0`、`databus=tfboard_event`；`send_succ/send_fail/except` | `RunConfig.save_summary_steps` = `100` |  | chief 日志匹配 `[tracing] global_step=<N>, step_elapsed=<seconds>, step_loss=<value>`，取最新一条；`StepInfoTracingHook` 默认每 50 step 打印一次，由 Lite TensorFlow AOP 自动加入训练 hooks |  | Estimator `SummarySaverHook` 在 chief 发送；并发会稀释 chief 看到的 step。成功日志 `send message succeed with size <N> event_size <M>`；失败 `send message to databus failed <error>`；异常 `import tfboard event failed <error>` |

### Base-runner checkpoint pattern

- 日志优先使用 `base-runner/runner_0.log`；若实际文件是 `runner_ver_*_globalrank_0_localrank_0*.log`，使用 rank 0 文件。
- Jaguar/Lagrange TF Sync：
  1. `Try to load checkpoint from <path> with data time ...`
  2. `Load args: {...'load_global_step': ...}`
  3. `Successfully loaded checkpoint from <path>`
  4. 用后续 `start current step: <N>` / `current step: <N>` 或同窗口 `metrics/model/global_step` 确认 runtime offset。
  5. 检查 `load_path`、`load_dense_path`、`load_incr_path`、`load_global_step`（默认 `True`）。
- Dandelion/Lagrange TF Async/Dandelion V3：
  1. `Loading Checkpoint: <path>` → `Loaded Checkpoint: <path>`
  2. runtime offset：`set global_step: [array([<N>], dtype=float32)]`
  3. 与 `start current step: <N>` 配对。
  4. 检查 `load_checkpoint`；PS/failover 恢复时可为空，可辅查 `save_input = {'dandelion/ckp_from_ps/checkpoint_filename:0': '...'}`。
- 共同检查 `load_global_step` 和 `clear_global_step`；`load_global_step=False` 或 `clear_global_step=True` 会丢弃 checkpoint step offset。

### Trainer-runner checkpoint pattern

- 使用 `trainer-runner/runner_ver_<period>_<failover>_globalrank_0_localrank_0*.log`。
- 公共 pattern：`[Checkpointer] Worker <rank> load done, global step: <N>`；仅在 `enable_coordinator=True` 时保证打印。
- Sync/Hybrid 可辅查 `Loaded global_step: {'_global_step': tensor([<N>])}`；Async、Dense-only、Omni 不保证出现。
- 检查 `ckp_path`、`dense_ckp_path`、`load_global_step`（默认 `True`）、`skip_load_ckpt`，以及 Norbert/PS 的 `clear_global_step`。
- Async 另查 `torch_async_load_legacy`。
- Omni 可能使用 Dense 或 Jaguar checkpointer，但最终以公共 `load done, global step` 为准。
- 用首个 Wandb step 复核，允许与 `wandb_log_interval_steps` 同量级的间隔。

## 附录 B：常见打点日志错误 pattern

| 问题类型 | 日志 pattern | framework / role / log file | 异常说明 | 下一步建议 |
|---|---|---|---|---|
| Wandb：SDK 无法识别当前 IDC / Region 错配 | `forge_wandb: No region found for current IDC: <IDC>, wandb data will be ignored`；或 `forge_wandb: API failed: <traceback containing reckon-tracing and ReadTimeout\|ConnectTimeout\|ConnectionError>`；或 `forge_wandb: error: <ReadTimeout\|ConnectTimeout\|ConnectionError to reckon-tracing>` | 所有表内 Torch framework；trainer-runner；globalrank 0 文件 | SDK/bytedenv 未正确路由当前 IDC，数据被忽略；`my/useast5/useast8` 是历史高频事故 DC | 升级覆盖当前 IDC 的 Torch/bytedance.wandb；优先 Torch >= LTS 1.7 |
| Wandb：Scalar 为 NaN/Inf | `forge_wandb: nan value in <path> at step <N> found, this value will be ignored`；`forge_wandb: inf value in <path> at step <N> found, this value will be ignored` | 所有表内 Torch framework；trainer-runner；globalrank 0 文件 | SDK 在持久化前丢弃当前 path/step，可造成局部缺点或整个 path 缺失 | 修复上游数值稳定性；写入前使用 `isfinite`、`nan_to_num` 或等价清洗 |
| Wandb：Histogram batch 上传失败 / Payload 过大 | `forge_wandb: API failed: <traceback>`；`forge_wandb: Failed Batch of Histograms Paths: dict_keys([<paths>])`；`forge_wandb: Current Batch of Histograms Skipped...` | 所有表内 Torch framework；trainer-runner；globalrank 0 文件 | 大概率为 Histogram payload 过大 | 优先升级 Torch/SDK（建议 >= LTS 1.7）；仍失败时减少 Histogram path 数量 |
| Wandb：Histogram 非法或不可序列化 | `forge_wandb: error or non-serializable histogram <path> <value> at step <N> found, histogram will be ignored` | 所有表内 Torch framework；trainer-runner；globalrank 0 文件 | SDK 在发送前拒绝该 Histogram，是 path 级确定性证据；详细原因看 traceback | 按具体异常修改 Model Code 或样本；检查传入 Histogram 的异常值 |
| TensorBoard：Histogram 含 NaN/Inf | `NaN in summary histogram`；`SESSION_RUN_ERROR`；`Invalid argument` | 表内 Sail framework；使用对应 role/log file | 以 `NaN in summary histogram` 为准；Jaguar 默认 `replace_nan_before_summary=True`，通常先替换无效值 | 从错误栈定位 path，清洗 NaN/Inf 并修复上游计算 |
| TensorBoard：Sailor EventWriter 发送失败 / Payload 过大 | `send job[<job_id>] stage [<stage_id>] model[<model>] type[event] size[<bytes>] to databus ERROR:<ret>` | `dandelion_v2/sailor_flink/sailor_primus`；对应 Sailor/TaskManager 日志 | 包含 job/stage/model/type/bytes/返回码；EU/US-TTP 上限 4 MB，其他地区 10 MB | 按 bytes 核对上限，减少 Histogram/Image 数量、尺寸、频率；或升级到支持自动拆包的新框架 |
| TensorBoard：TensorBoardClient Databus 发送失败 | `send message to databus error: <error_msg>` | Lagrange TF Sync/Async、Jaguar、Dandelion V3；对应 role/log file | 序列化完成，但 `collect_with_response` 非 0；metric `status=dbus_send_err`；单日志不能区分 payload、网络或 Databus | 保留完整 `error_msg`；对照同窗口成功日志 `write databus succeed with tfb size <N> event size <M>` 与发送 metric；先核对地区 payload 上限，必要时升级框架 |
| TensorBoard：Sailor 仅发送 graph metadata | `send job[<job_id>] stage [<stage_id>] model[<model>] type[graph] size[<bytes>] to databus OK` | `dandelion_v2/sailor_flink/sailor_primus` | 只证明 graph metadata 成功，不会生成用户可见 scalar/histogram/image | 继续检查 summary 是否生成、发送 worker 是否有样本，以及 `type[event]` OK/ERROR |

TensorBoard Scalar 的 NaN/Inf 通常会原样写入，不产生通用错误日志；Jaguar 部分 `add_tensor_summary` 路径会替换为 `1e-5`，并记录：

```text
Found NaN/Inf in summaries count <N> values in <step> step's summary
```

## 附录 C：Model Code 常见编码问题索引

先按 source + training_framework 路由，再匹配代码结构，并使用“补充特征”确认。历史 DC/版本经验不能单独作为根因。

| Pattern | 补充特征 | 说明 | 对用户建议 |
|---|---|---|---|
| Wandb；LagrangeTorch/Nova/Omni；`torch.compile(...)` 或 `@torch.compile` 内出现 `LG.wandb_data.update(...)`、`LG.wandb_data.log(...)`、`CONTEXT.wandb_data.update_scalar(...)`、`update_histogram(...)` 或 `wandb.log(...)` | 旧 Torch runtime；`disable_wandb_step_compile=False` 或未配置；`Graph Break Reason: Tensor.item` 只能证明部分 eager fallback | Dynamo/Inductor 捕获 Python 副作用后，后续 step 可能跳过打点，造成全部或部分 path 缺失 | 优先设置 `trainer.enable_external_flags(trainer_runner={"disable_wandb_step_compile": True})`；更稳妥地让 compiled forward 返回 metrics，再由外层 `@LG.train` runstep 打点 |
| TensorBoard；Sail/Sailor/Jaguar/Dandelion/Lite 静态图；代码 path 与实际查询 path 同名但未命中 | 搜索 `<path>_<N>` 可见 `loss_1`、`loss_2` 等后缀 path；代码中同名计算节点（如 `tf.reduce_sum(..., name="loss")`）或重复 `tf.summary.scalar("loss", ...)` | TensorFlow 建图会给同名节点/summary 自动追加 `_N`，代码中的 path 名称不一定等于 TensorBoard 实际 path；Torch/Wandb 不适用 | 先使用实际后缀 path 查询；将计算节点名与展示 path 分开，并改用带业务前缀的稳定名称，例如 `name="cross_entropy_loss"` + `tf.summary.scalar("train/loss", loss)` |
| TensorBoard；Sailor/Dandelion 多 RunStep；已创建 `M.RunStep(...)` / `run_train`，但业务指标使用裸 `tf.summary.scalar(...)` / `tf.summary.histogram(...)`，未使用 `run_train.summary.scalar(...)` / `run_train.summary.histogram(...)` | 其他 TensorBoard path 正常，目标 loss/业务 metric 缺失；存在多个 RunStep；裸 summary 依赖的 placeholder 超出实际执行的 TRAIN RunStep feed，因而被过滤。只有同时符合这些特征的 path 才可归因于此；该问题通常不导致整个 Job 所有 path 均缺失 | 裸 summary 未绑定实际 RunStep，或依赖 feed 超出当前 RunStep，被过滤/不执行 | 改用 `run_train.summary.scalar(name, tensor)` / `run_train.summary.histogram(name, tensor)` |
| TensorBoard；Sail/Sailor/Lgtf；框架要求 `from sail import tf`，但代码使用 `import tensorflow as tf` / `tensorflow.compat.v1`，或反向混用 | 源码存在 `tf.summary.*`，但目标 path 缺失 | API/import 风格与框架版本不匹配，没有进入预期 summary 收集/编译路径 | 按实际 framework/TensorFlow 版本使用匹配 API；不能仅凭源码存在 summary 调用认定会打点 |
| TensorBoard；Sail/Sailor/Lgtf；源码有目标 summary，但 `graph.readable` 中 path 不存在，或 op 为 `Const` 而非 `ScalarSummary/HistogramSummary` | Model Code 字符串命中，但编译图没有正确 summary op | summary 未附着到实际训练图 | 确认输入 tensor 属于实际 graph/RunStep；代码无误仍缺 op 时交给框架/Sail owner |
| TensorBoard；Sail/Sailor/Jaguar/Dandelion/Lgtf；summary 位于未命中的 `mode/run_type/feature flag/step/graph branch` | 同区域 sibling summary 存在，只有一个 family 缺失 | summary 定义存在，但当前任务未执行该分支 | 核对 Job 条件，修正 logging condition，或移动到实际执行的 RunStep/graph |
| TensorBoard Image；`tf.summary.image(..., max_outputs=N)` 的 `N` 较大或原图过大 | 单张 PNG 编码后超过 100 KB；Scalar/Histogram 正常，Image 缺失或不完整；Series 原始值可能显示 `TOO+LARGE` | Image 超过 consumer 限制，被拒绝或缺帧 | 降低尺寸、`max_outputs` 和频率；需要查看更多帧时提高 UI sample count |
| TensorBoard Scalar；启用 `dense_fc_bf16`、`multislice_bf16`、bf16 autocast、`enable_alltoall_bf16` / `enable_allreduce_bf16` | 大量 points 堆积在少数 step，但 `event_time` 连续；global_step 很大 | bf16/混合精度造成 global_step 表示精度损失，是 step 轴压缩而非 emission 丢失 | 当前任务使用时间轴；未来任务评估关闭相关 bf16 配置或重新设计 global_step |

## 附录 D：Series 系统后端 SLA 指标

| site | metric | tags |
|---|---|---|
| cn | `data.reckon.one_forge_cn.info.series.job.count` | `source=tensorboard/wandb`；`data_type=scalar/histogram/image` |
| i18n | `data.reckon.one_forge_i18n.info.series.job.count` | 同上 |
| euttp | `data.reckon.one_forge_euttp.info.series.job.count` | 同上 |
| usttp | `data.reckon.one_forge_usttp.info.series.job.count` | 同上 |
