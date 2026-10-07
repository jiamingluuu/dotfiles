---
name: spark-ui-diagnose
description: |
  诊断单个 Spark 应用的运行状态、定位真实根因并给出可执行方案：失败任务找失败原因（OOM / FetchFailed / 数据问题），成功但慢的任务找慢因（数据倾斜 / 资源不足 / 数据量），健康任务评估资源是否过度/不足配置。这是一套**假设驱动的诊断方法论**，在 `bytedcli megatron spark-ui` 原子命令之上，由你按任务的具体情况选择该取哪些证据、何时下钻、一个数据源拿不到时换哪个。当用户问「这个 spark 任务为什么失败 / 为什么慢 / 资源是否合理 / 帮我诊断 application_xxx / 这个任务跑了好久」时使用，即使没明说「诊断」也应触发。
---

# Spark 应用诊断方法论

诊断不是固定流水线，而是**假设 → 取针对性证据 → 确认或推翻 → 换假设**的循环。不同任务（失败 / 慢 / 体检）需要的证据完全不同，**该取什么由当前假设决定**——所以这里给的是判断框架，不是一键脚本。

职责分层（别混淆）：

- **CLI（`megatron spark-ui`）** 只做原子取数，返回原始 Spark UI JSON。
- **你（agent）** 做动态编排：选证据、下钻、交叉验证、换证据源。
- **`scripts/compute_metrics.py`** 只做确定性计算（从已取的 JSON 算 wall 时长 / CPU 利用率 / 峰值内存比 / GC 占比 / executor 退出分类）——这部分机械且每次一样，交给脚本，省得每次手算。它**不替你做判断**。

## 前置

- `bytedcli megatron spark-ui` 可用；鉴权问题见主技能 / `bytedcli auth login`。

```bash
bytedcli megatron spark-ui --help &>/dev/null || \
  NPM_CONFIG_REGISTRY=http://bnpm.byted.org npx -y @bytedance-dev/bytedcli@latest megatron spark-ui --help
```

- 默认 region `sg` / site `i18n-tt`（BDEE 主路），其他按实际传 `-r` / `--site`。
- **解析一次 root，后续复用**：第一条命令（如 `jobs list -j`）的输出里 `context.spark_history_root` 是解析出的 History Server REST root。后续命令带 `--spark-history-url <root>/history/<appId>/jobs/` 复用它，**避免每条命令都经偶发不稳定的 app-info 鉴权网关**重新解析。
- **冷启动延迟**：History Server 对已结束任务首次访问要回放 event log。轻量端点（jobs/sql/environment）数秒；`executors`、`stages` 对大任务（数千 executor、数万 task）可达数分钟。统一带较大 `--timeout-ms`（如 180000+）。**取数顺序上先取轻的、能定方向的**。

## Step 0 — 分诊：先定方向，再决定深挖什么

起手取一个轻量全局画像（二选一）：

```bash
bytedcli megatron spark-ui jobs list --app-id <id> -r sg          # 最轻：状态 + 每个 job 时长 → 立刻看出 失败/慢/正常
bytedcli megatron spark-ui summary get --app-id <id> -r sg       # 聚合：失败数 + OOM-killed 数 + dead executor + shuffle 量
```

据此分流（任务可能同时命中多条线，按用户诉求和严重度排序处理）：

| 观察 | 走哪条线 |
|---|---|
| 有 `FAILED` job / 有失败 stage | **A. 失败线** |
| 全 `SUCCEEDED` 但 wall 远超预期 / 用户嫌慢 | **B. 慢成功线** |
| 成功且不慢，想看是否省资源 / 配置是否合理 | **C. 资源体检线** |

> **强力技巧——孪生对比**：很多任务是周期调度（同一 Dorado 任务不同日期）。若手上有同任务一个正常实例，**拿它和异常实例对比**（时长、配置、shuffle 量、executor 死亡数），差异点往往直指根因。

## A. 失败线 — 找失败的真实原因

失败几乎总是**级联**的：表层报错（如 FetchFailed）往往是症状，真因在更上游（executor 为何丢失）。所以要顺着链条往回追。

1. **取失败 stage 的报错**：

   ```bash
   bytedcli megatron spark-ui stages list --app-id <id> --spark-history-url <root>.../jobs/ -r sg
   ```

   找 `status=FAILED` 的 stage，读其 `failureReason`。按错误类型分诊：

   | failureReason / 现象 | 真因方向 | 下一步证据 |
   |---|---|---|
   | `FetchFailedException` | **上游 executor 丢失**导致 shuffle 数据拉不到（症状，非根因） | 追 executor 为何死 → 下一步 2 |
   | `OutOfMemoryError` / task errorMessage 含 OOM / `Container killed ... memory` | executor/driver 内存不足 | `executors list --all` 看 `removeReason` 确认 |
   | 业务异常栈（`FileNotFoundException` / schema / SparkException 业务类） | **数据或代码问题，不是资源** | 读 errorMessage 全文；非资源问题不要去调内存 |
   | stage 列表没有 failureReason | 信息不足 | 下钻 `stages get --stage-id <failed>` 看 task 级 `errorMessage` |

2. **追 executor 死亡原因**（FetchFailed / 怀疑 OOM 时）：

   ```bash
   bytedcli megatron spark-ui executors list --all --app-id <id> --spark-history-url <root>.../jobs/ -r sg
   ```

   文本模式直接给 `removeReason` 分类（OOM / 驱逐抢占 / 正常缩容）；JSON 模式每个 executor 带 `removeReason` 原文。**OOM 在这里即可确认**（"Cgroup memory overhead" 等），无需翻 container log。典型链：executor OOM → shuffle 输出丢 → 下游 FetchFailed → stage 重试耗尽 → job 失败。

3. **替代证据（关键——拿不到不等于断线）**：`executors` 超时/拿不到时，**换角度而不是放弃**：

   | 想确认 | 主证据 | 拿不到时的替代 |
   |---|---|---|
   | executor 是否 OOM | `executors list --all` 的 removeReason | ① `dorado get-container-log --application-id <id> --file stderr` 抓某个 dead executor 看异常（最直接）；② 孪生成功实例对比内存峰值；③ `environment` 看 executor.memory 是否本就偏紧 |
   | 失败 stage 报错 | `stages` 的 failureReason | `stages get --stage-id <X>` 的 task errorMessage（更慢但更细） |
   | 是否资源问题 | executors + environment | 对比孪生成功实例的配置/资源 |

   > ⚠️ **`summary` 的 `oomKilled` 派生自 executors**——`summary` 内部就是 fan-out 到 `executors` 再统计的。所以当 `executors` 不可用时，`summary` 要么一起失败，要么 `oomKilled` 退化为 `0`。**此时 `oomKilled=0` 是「没数据」，不是「没 OOM」，绝不能据此排除 OOM。** 要确认/排除 OOM，必须走上表的 container-log 或孪生对比，而不是看 summary。同理，任何「派生指标」（summary 的聚合、compute_metrics 的计算）在其底层原始数据缺失时都只是 0/空，不构成反向证据。

4. **给结论**：根因（区分症状与真因）+ 方案。常见方案：
   - OOM → 提 `spark.executor.memory` / `spark.executor.memoryOverhead`。
   - FetchFailed（shuffle 压力大）→ 调高 `spark.sql.shuffle.partitions`（减小单 block）；开/确认 external shuffle service 或 shuffle tracking（executor 死后 shuffle 不丢）；根本上降 shuffle 量。
   - 数据/代码问题 → 指出具体异常，不要乱调资源。
   - **重启判断**：单次偶发节点丢失可重启；**同一 stage 多次 attempt 全挂 = 系统性问题，先改配置/数据再重跑**，否则白跑几小时。

## B. 慢成功线 — 找慢在哪、为什么慢

「慢」必须落到**具体的 stage**，再判类型。不要停在 job 层说一句"慢"。

1. **定位长尾**：从 Step 0 的 `jobs` 找耗时最长的 job（submissionTime→completionTime 跨度），拿它的 `stageIds`。
2. **找占时间的 stage**：`stages` 看这些 stage 的耗时 / shuffle / input。
3. **下钻该 stage 看 task 分布**（最关键的一步）：

   ```bash
   bytedcli megatron spark-ui stages get --app-id <id> --stage-id <X> --spark-history-url <root>.../jobs/ -r sg
   ```

   看 task 级指标，判断慢的**类型**：

   | 现象 | 慢因类型 | 方向 |
   |---|---|---|
   | 少数 task 耗时 >> 中位数（max 远大于 median） | **数据倾斜** | 加盐 / 调分区 / 改 join 策略 / 修复热点 key |
   | task 普遍慢、量大但均匀 | **数据量大 / 分区过少** | 提分区数 / 资源 |
   | task 有大量 spill（落盘）、GC 高 | **内存不足** | 提 executor 内存 |
   | task 时间花在 input/scan | **外部 IO / 上游慢** | 看数据源、扫描裁剪 |
   | Hudi commit（`BaseSparkCommitActionExecutor` / `Hoodie*`）独占大量时间 | **Hudi 写入瓶颈** | bulk_insert vs upsert、文件大小、bucket index、并行度 |

4. **辅助看资源**：`executors list --all` 的 GC 占比、shuffle 量、是否有 spill，佐证上面的判断。
5. **给结论**：哪个 stage、为什么慢、调优方向。

## C. 资源体检线 — 是否过度/不足配置

```bash
bytedcli megatron spark-ui executors list --all --app-id <id> --spark-history-url <root>.../jobs/ -r sg
bytedcli megatron spark-ui environment get --app-id <id> --spark-history-url <root>.../jobs/ -r sg
```

- **峰值内存 vs 配置**：executor `peakMemoryMetrics.JVMHeapMemory` 对比 `spark.executor.memory`。峰值 < 配置 40% → **过度配置**，可下调省集群资源；峰值 > 85% 或有 OOM → **不足**，应上调。
- **CPU 利用率**：task 计算时间 / (wall × cores)。**注意：动态分配（dynamicAllocation）下这是下界**——大量 executor 只存活很短时间，wall×峰值核数会高估 slot，从而低估利用率。所以低利用率别急着下结论，要结合 executor 生命周期看，或只作量级参考。
- **GC 占比** > 10% → 内存压力或对象分配过多。

## 用 compute_metrics.py 算派生指标（可选）

取完数（用 `-j` 存成 JSON 文件）后，把它们喂给计算脚本，一次性拿到 wall 时长 / per-job 排序 / CPU 利用率 / 峰值内存比 / GC 占比 / executor 退出分类，省得手算：

```bash
bytedcli -j megatron spark-ui jobs list        --app-id <id> -r sg > /tmp/jobs.json
bytedcli -j megatron spark-ui executors list   --app-id <id> --all --spark-history-url <root>.../jobs/ -r sg > /tmp/exec.json
bytedcli -j megatron spark-ui environment get --app-id <id> --spark-history-url <root>.../jobs/ -r sg > /tmp/env.json
python3 scripts/compute_metrics.py --jobs /tmp/jobs.json --executors /tmp/exec.json --env /tmp/env.json
```

脚本只输出**数字**（含 `--json`），verdict 和建议由你结合方法论给出。缺某个文件时它跳过对应指标而不报错——和「替代证据」原则一致。

## 输出结构

诊断结论建议包含三段，让 human / agent 都能直接行动：

```
判定：<成功/失败> · <一句话结论>
证据链：<观察到的关键信号，区分「症状」与「真因」，标明数据来源>
建议：<可执行项，标注 [human] / [agent]，给出具体参数或命令>
```

## 局限

- CPU 利用率是粗算下界（见 C 线说明），精确需按 executor 生命周期加权。
- 最深的失败细节（具体分配点、GC 曲线、完整异常栈）仍可能要 `bytedcli dorado get-container-log` 抓容器日志。
- 大任务的 `executors` / `stages get --stage-id` 冷回放慢（数分钟），按需取、设大 timeout、优先复用 root。
