# MaaS Perf

## Perf 任务

模型 Perf Task 的状态流转：

```text
CREATE -> MODEL_READY -> INPUT_READY -> FIRST_PROFILING  ------> STOPPED
                                       |               ^
                                       V               |
                                  DAILY_PROFILING ------
                                       |  ^
                                       V  |
                                  DAILY_PROFILING_START
```

## 状态解释

**CREATE**：模型的 Perf 任务完成创建，等待模型产图。

- 如果长时间卡在 `create`，请先检查模型分发产图。

**MODEL_READY**：模型产图成功完成，等待足够的 Perf 样本输入。

- 如果长时间卡在 `model_ready` 状态，请先通过小流量实验保证 MaaS 能收集到模型输入。

**INPUT_READY**：模型收集足够的 Perf 样本，等待第一次发起 Perf Job 进行压测。

- 如果长时间卡在 `input_ready`（超 10 分钟），表示 Perf 的状态机调度存在异常，请联系 MaaS oncall 跟进排查。

**FIRST_PROFILING**：首次 Perf Job 执行中，等待任务完成。

- 如果长时间（超过 2 小时）卡在 `first_profiling`，表示首次发起的压测任务还在运行中，可以先到 MaaS 控制台对应 BU 的 Perf Job 页面查看压测进展，确认是否存在异常任务。

**DAILY_PROFILING**：进入常态的 Perf 状态，等待新的 Perf 需求。

- MaaS 会持续检查线上的 bs 分布，如发现存在新的 bs 需要触发压测，则持续下发新的压测任务。

**DAILY_PROFILING_START**：常态的 Perf Job 执行中，等待任务完成。

- 如果长时间（超过 2 小时）卡在 `daily_profiling_start`，可以先到 MaaS 控制台对应 BU 的 Perf Job 页面查看压测进展，确认是否存在异常任务。

**STOPPED**：模型的 Perf 任务停止，不再发起任何新的压测任务。

## Perf 性能与 HPA 的容量水位

模型水位（capacity water level，公式里简称 `l`）计算公式如下：

```text
l = (bs * qps) / sum(package_i * packageNum_i * packagePerfBs_i * packagePerfQps_i)
```
