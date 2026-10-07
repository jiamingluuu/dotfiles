---
name: bytedance-merlin
description: |
  Merlin 平台 用于训练、部署LLM模型。使用 bytedcli merlin 原生命令完成：（训练）Job 管理、Devbox 开发机、Tracking 实验跟踪、Arena 评估、Insight 分析、Checkpoint/Model/Data 卡片管理、模型部署，以及在线服务治理：批量 HPA 弹性配置读写、推理服务压测（loadtest）全生命周期与 Rhino 性能报告、GPU 推荐与容量/部署拓扑查询。

  触发词：Merlin、Seed、ml.bytedance.net、seed.bytedance.net、ml.tiktok-row.net、训练任务、开发机、工作台 SSH 公钥、上传公钥、删除公钥、评估、Arena、Tracking、Checkpoint、模型/checkpoint部署、模型卡片、数据卡片、GPU、401/403 认证失败、HPA、弹性伸缩、扩缩容配置、目标利用率、压测、性能压测、loadtest、压测预检、压测报告、Rhino、性能报告、扩容建议、GPU 推荐、GPU 数量、PD 分离部署、seed 压测数据集、压测配置复现。
---

# Merlin 平台 All-in-One Guide

Merlin 是字节跳动的机器学习训练与评估平台。本 skill 整合了所有 Merlin 相关操作的子技能。

## 快速导航

| 场景                            | 推荐子技能                                                                                   |
| ------------------------------- | -------------------------------------------------------------------------------------------- |
| 认证失败 / 401/403              | [bytedcli Merlin 兜底](references/merlin-cli/GUIDE.md)                                       |
| 创建/启动训练任务               | [merlin-job-launch](references/merlin-job-launch/GUIDE.md)                                   |
| 任务失败排查                    | [merlin-job-debug](references/merlin-job-debug/GUIDE.md)                                     |
| 运行态运维（日志/Grafana/停止） | [merlin-job-devops](references/merlin-job-devops/GUIDE.md)                                   |
| 资源配额查询                    | [merlin-job-resource](references/merlin-job-resource/GUIDE.md)                               |
| 任务模板管理                    | [merlin-job-template](references/merlin-job-template/GUIDE.md)                               |
| 开发机管理                      | [merlin-devbox](references/merlin-devbox/GUIDE.md)                                           |
| 开发机故障排查                  | [merlin-devbox-troubleshoot](references/merlin-devbox-troubleshoot/GUIDE.md)                 |
| 启动 GPU Worker                 | [merlin-devbox-worker](references/merlin-devbox-worker/GUIDE.md)                             |
| Arena 评估数据拉取              | [merlin-arena](references/merlin-arena/GUIDE.md)                                             |
| Arena 失败分析                  | [merlin-arena-task-failure-analysis](references/merlin-arena-task-failure-analysis/GUIDE.md) |
| Arena 慢任务分析                | [merlin-arena-task-slow-analysis](references/merlin-arena-task-slow-analysis/GUIDE.md)       |
| Arena 得分对比                  | [merlin-arena-diff](references/merlin-arena-diff/GUIDE.md)                                   |
| Arena Trajectory 拉取           | [merlin-arena-trajectory](references/merlin-arena-trajectory/GUIDE.md)                       |
| 评估结果导出                    | [merlin-eval-result-export](references/merlin-eval-result-export/GUIDE.md)                   |
| 获取评估指标                    | [merlin-eval-get-result](references/merlin-eval-get-result/GUIDE.md)                         |
| 查询 Exercise/Collection        | [merlin-eval-query](references/merlin-eval-query/GUIDE.md)                                   |
| 上传评估数据                    | [merlin-eval-data-upload](references/merlin-eval-data-upload/GUIDE.md)                       |
| 创建 Exercise                   | [merlin-recipe-eval-exercise-setup](references/merlin-recipe-eval-exercise-setup/GUIDE.md)   |
| 创建 Collection                 | [merlin-recipe-eval-collection](references/merlin-recipe-eval-collection/GUIDE.md)           |
| 运行评估                        | [merlin-recipe-eval-run](references/merlin-recipe-eval-run/GUIDE.md)                         |
| Evals-to-Exercise 验证          | [merlin-recipe-e2e-eval-verify](references/merlin-recipe-e2e-eval-verify/GUIDE.md)           |
| 伴生评估管理                    | [merlin-companion-eval](references/merlin-companion-eval/GUIDE.md)                           |
| Tracking 实验分析               | [merlin-tracking-experiment](references/merlin-tracking-experiment/GUIDE.md)                 |
| Insight 分析                    | [merlin-insight](references/merlin-insight/GUIDE.md)                                         |
| Checkpoint 管理                 | [merlin-checkpoints](references/merlin-checkpoints/GUIDE.md)                                 |
| 模型卡片                        | [merlin-model-card](references/merlin-model-card/GUIDE.md)                                   |
| 数据卡片                        | [merlin-data-card](references/merlin-data-card/GUIDE.md)                                     |
| Profiling 资产                  | [merlin-profiling](references/merlin-profiling/GUIDE.md)                                     |
| 线上服务管理与部署              | [merlin-service](references/merlin-service/GUIDE.md)                                         |
| HDFS 跨洋传输                   | [merlin-hdfs-migration](references/merlin-hdfs-migration/GUIDE.md)                           |
| Grafana 监控                    | [merlin-grafana-observation](references/merlin-grafana-observation/GUIDE.md)                 |
| 知识问答                        | [merlin-knowledge-qa](references/merlin-knowledge-qa/GUIDE.md)                               |

---

## 核心工具：bytedcli merlin

工作台「SSH 公钥」使用原生 REST 命令 `merlin cpu-devbox ssh-keys get/upload/delete`，不依赖 MCP 工具可用性。上传／删除默认预览，`--yes` 才提交；支持 `--key-file` 或 `--public-key`，删除还支持 `--fingerprint`。ROW 使用 `--site i18n-tt`。详细行为、并发限制与示例见 [开发机管理](references/merlin-devbox/GUIDE.md#工作台-ssh-公钥)。

bytedcli merlin 是仓库内原生命令入口，复用 bytedcli 认证并通过 schema-derived options 调用 Merlin MCP。

### 安装

```bash
NPM_CONFIG_REGISTRY=http://bnpm.byted.org npx -y @bytedance-dev/bytedcli@latest merlin --help
```

### 认证与站点选择

```bash
# 先检查当前站点的全局认证与 ZTI 状态
bytedcli auth status

# 办公网、无 ZTI 或 ZTI 交换失败时再登录
bytedcli auth login

# 运行 Merlin 命令时用全局 site/vregion 选择控制面
bytedcli --site cn merlin job get-run --job-run-id <job-run-id>
bytedcli --site cn --vregion seed merlin job get-run --job-run-id <job-run-id>
# v4 拆分开发机：CPU 走 cpu-devbox，GPU 走 gpu-devbox，均带 instances 子资源
bytedcli --site i18n-tt merlin cpu-devbox instances list
bytedcli --site i18n-bd merlin cpu-devbox instances list
```

在生产网环境（`BYTEDCLI_NETWORK_PROFILE=prod`）中，若运行环境提供 `SEC_TOKEN_STRING` 或 `SEC_TOKEN_PATH`，`bytedcli merlin` 会按所选站点自动把 ZTI 换成个人 ByteCloud JWT，通常无需先执行 `bytedcli auth login`。当前支持 `cn`、`i18n`、`i18n-tt`、`i18n-bd`；显式 JWT override 优先于 ZTI，ZTI 不可用或交换失败时自动回退到现有 ByteCloud Auth。`bytedcli auth status` 的 `zti_jwt` 段可查看是否启用、是否已有缓存及过期时间，且不会输出原始 ZTI/JWT。

### 控制面

| bytedcli 选择              | Merlin 控制面 | 域名                     |
| -------------------------- | ------------- | ------------------------ |
| `--site cn`                | `cn`          | `ml.bytedance.net`       |
| `--site cn --vregion seed` | `cn-seed`     | `seed.bytedance.net`     |
| `--site i18n-tt`           | `i18n-tt`     | `ml.tiktok-row.net`      |
| `--site i18n-bd`           | `i18n-bd`     | `ml-i18nbd.byteintl.net` |

### 常用命令

```bash
# 发现工具
bytedcli merlin --help

# 查看 Schema
bytedcli merlin <group> <command> --schema

# option-first 调用
bytedcli merlin <group> <command> [schema-derived options]

# 预览请求
bytedcli merlin <group> <command> --dry-run [schema-derived options]
```

### 手写命令（非 MCP 生成）

任务页「SSH → 复制指令」对应 `bytedcli --site i18n-tt merlin job ssh-command get --job <job-id-or-url>`。只读输出连接命令，不执行 SSH、不更改公钥或授权；多实例必须指定 `--instance-id`。当前仅支持 ROW，详细规则见 [运行态操作](references/merlin-job-devops/GUIDE.md#获取任务-ssh-指令)。

以下命令是手写实现，flag 形态与 MCP 生成命令不同，不在下方「Generated command 快速索引」内：

| 命令                 | 关键 flag                                                                                                                                                        | 说明                                                                                                                                                                           |
| -------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `job get-timeline`   | `--job <job-run-id>`                                                                                                                                             | 获取任务时间线事件（仅需 `--job`，不接受 `--trial-id`）                                                                                                                        |
| `job hot-update`     | `--trial <trial-id> --update-reason <reason> [--update-mode <failover\|restart-now>] [--env-vars <json>] [--git-repo <json>] [--entrypoint-full-script <value>]` | 对运行中的 Merlin trial 应用 robust 热更新（按 trial id，非 job run id）                                                                                                       |
| `job metrics`        | `--job` `--window` `--allow-partial`                                                                                                                             | per-node/per-GPU trailing window; incomplete → exit 4 unless `--allow-partial`; branch on `coverage.complete`.                                                                 |
| `trial watch poll`   | `--job <job-run-id-or-url> [--trial-id <id>] [--mode startup\|until-terminal]`                                                                                   | 一次平台 API 观测（robust-run / Xray alerts / job status）。按 `outcome`（`healthy` / `needs_intervention` / `no_claim`）分支，不按 event kind；**notify_only**，不 stop trial |
| `trial watch follow` | `--job <job-run-id-or-url> [--mode startup\|until-terminal] [--interval <s>] [--max-watch-seconds <n>] [--min-stable-seconds <n>]`                               | 轮询直到 STABLE / TERMINAL / STOP_LOSS_TRIGGERED / WATCH_TIMEOUT。全局 `--json` 时 stdout 为 JSONL（每事件一行，无最终 envelope）；同样 **notify_only**，不 stop trial         |

### Generated command 快速索引

| Group        | 常用命令                                                                                      |
| ------------ | --------------------------------------------------------------------------------------------- |
| `arena`      | `get-evaluation`, `list-case`, `create-evaluation`, `create-eval-result-export-job`           |
| `training`   | `checkpoint-dirs list`, `checkpoints list`, `companion-configs update`, `companion-jobs list` |
| `collection` | `list`, `get`, `create`, `create-version`                                                     |
| `data`       | `list`, `get`, `get-data-preview`, `get-field-stat`                                           |
| `cpu-devbox` | `instances list`, `instances get`, `instances exec`, `instances start`, `instances stop`      |
| `exercise`   | `list`, `get`, `create`, `create-version`                                                     |
| `insight`    | `get`, `create`, `get-ability`, `get-significance`                                            |
| `job`        | `get-run`, `create-run`, `fork-run`, `get-grafana`                                            |
| `model`      | `list`, `get`, `get-v2`, `list-v2`, `create-idc-sync-job`                                     |
| `pipeline`   | `list-def`, `get-def`, `list-run`, `get-run`, `retry-run`                                     |
| `profiling`  | `list`, `get`, `get-tos-link`                                                                 |
| `service`    | `list`, `get`, `get-seed-template`, `create-instant-deployment`                               |
| `tracking`   | `projects list`, `runs list`, `runs get`, `run-entities list`, `get-timeseries`               |
| `trigger`    | `list-def`, `get-def`, `list-run`, `reset-status`                                             |

v4 已将 checkpoint 与伴生评估统一到 `training` 组（`checkpoint-dirs` / `checkpoints` / `companion-configs` / `companion-jobs`）；原 `eval` 组的 SequenceJob 命令已在 v4 移除，周期性伴生评估改用 `training companion-configs` / `training companion-jobs`。

MCP-backed generated commands currently support `--site cn`, `--site cn --vregion seed`, `--site i18n-tt`, `--site i18n-bd`, and `--site i18n-bd --vregion seed`. Unsupported Merlin sites fail fast instead of falling back to CN.

For generated commands, `--arg key=value` parses `true`, `false`, `null`, numbers, quoted JSON strings, objects, and arrays before sending raw MCP arguments.

详细用法见 [bytedcli Merlin 兜底](references/merlin-cli/GUIDE.md)。

---

## 子技能分类索引

### Job 任务管理

| 子技能                                                         | 说明                                   |
| -------------------------------------------------------------- | -------------------------------------- |
| [merlin-job-launch](references/merlin-job-launch/GUIDE.md)     | 创建并启动训练任务（按模板/fork/重试） |
| [merlin-job-debug](references/merlin-job-debug/GUIDE.md)       | 任务失败排查与诊断                     |
| [merlin-job-devops](references/merlin-job-devops/GUIDE.md)     | 运行态运维（日志/Grafana/停止/热更新） |
| [merlin-job-resource](references/merlin-job-resource/GUIDE.md) | 资源配额查询与队列选择                 |
| [merlin-job-template](references/merlin-job-template/GUIDE.md) | 任务模板（JobDef）管理                 |

### Devbox 开发机

| 子技能                                                                       | 说明                              |
| ---------------------------------------------------------------------------- | --------------------------------- |
| [merlin-devbox](references/merlin-devbox/GUIDE.md)                           | 开发机管理（查询/启动/停止/执行） |
| [merlin-devbox-troubleshoot](references/merlin-devbox-troubleshoot/GUIDE.md) | 开发机故障排查（SSH/启动/连接）   |
| [merlin-devbox-worker](references/merlin-devbox-worker/GUIDE.md)             | GPU/CPU Worker 节点管理           |

### Arena 评估

| 子技能                                                                                       | 说明                                |
| -------------------------------------------------------------------------------------------- | ----------------------------------- |
| [merlin-arena](references/merlin-arena/GUIDE.md)                                             | 评估数据拉取（概览/case 明细）      |
| [merlin-arena-task-failure-analysis](references/merlin-arena-task-failure-analysis/GUIDE.md) | 评估任务失败分析                    |
| [merlin-arena-task-slow-analysis](references/merlin-arena-task-slow-analysis/GUIDE.md)       | 评估任务慢任务分析                  |
| [merlin-arena-diff](references/merlin-arena-diff/GUIDE.md)                                   | 两个评估任务得分对比                |
| [merlin-arena-trajectory](references/merlin-arena-trajectory/GUIDE.md)                       | Trajectory（Trace）数据拉取与可视化 |
| [merlin-eval-result-export](references/merlin-eval-result-export/GUIDE.md)                   | 评估明细后台导出任务                |

### Exercise/Collection 评估

| 子技能                                                                                     | 说明                                |
| ------------------------------------------------------------------------------------------ | ----------------------------------- |
| [merlin-eval-query](references/merlin-eval-query/GUIDE.md)                                 | 查询 Exercise/Collection 配置与版本 |
| [merlin-eval-get-result](references/merlin-eval-get-result/GUIDE.md)                       | 获取评估实例指标结果                |
| [merlin-eval-data-upload](references/merlin-eval-data-upload/GUIDE.md)                     | 上传评估数据集到 Seed 平台          |
| [merlin-recipe-eval-exercise-setup](references/merlin-recipe-eval-exercise-setup/GUIDE.md) | 从 DataCard 创建 Exercise           |
| [merlin-recipe-eval-collection](references/merlin-recipe-eval-collection/GUIDE.md)         | 从 Exercise Version 创建 Collection |
| [merlin-recipe-eval-run](references/merlin-recipe-eval-run/GUIDE.md)                       | 运行 Exercise 评估                  |
| [merlin-recipe-e2e-eval-verify](references/merlin-recipe-e2e-eval-verify/GUIDE.md)         | Evals 代码到 Exercise 端到端验证    |
| [merlin-companion-eval](references/merlin-companion-eval/GUIDE.md)                         | 伴生评估（companion）管理           |

### Tracking & Insight

| 子技能                                                                       | 说明                   |
| ---------------------------------------------------------------------------- | ---------------------- |
| [merlin-tracking-experiment](references/merlin-tracking-experiment/GUIDE.md) | 实验跟踪与指标分析     |
| [merlin-insight](references/merlin-insight/GUIDE.md)                         | Insight 分析与案例查询 |

### 资源管理

| 子技能                                                       | 说明                                    |
| ------------------------------------------------------------ | --------------------------------------- |
| [merlin-checkpoints](references/merlin-checkpoints/GUIDE.md) | Checkpoint 目录与条目管理               |
| [merlin-model-card](references/merlin-model-card/GUIDE.md)   | 模型卡片（Model Card）管理              |
| [merlin-data-card](references/merlin-data-card/GUIDE.md)     | 数据卡片（DataCard/Iceberg 表）管理     |
| [merlin-profiling](references/merlin-profiling/GUIDE.md)     | Profiling 资产管理                      |
| [merlin-service](references/merlin-service/GUIDE.md)         | 线上服务管理（创建/部署/日志/API 验证） |

### 其他

| 子技能                                                                       | 说明                       |
| ---------------------------------------------------------------------------- | -------------------------- |
| [bytedcli Merlin 兜底](references/merlin-cli/GUIDE.md)                       | 命令发现、schema、认证排障 |
| [merlin-hdfs-migration](references/merlin-hdfs-migration/GUIDE.md)           | HDFS 跨洋传输与数据搬迁    |
| [merlin-grafana-observation](references/merlin-grafana-observation/GUIDE.md) | Grafana 监控观测           |
| [merlin-knowledge-qa](references/merlin-knowledge-qa/GUIDE.md)               | 平台知识问答               |

---

## 使用建议

1. **认证问题**：遇到 401/403 时先运行 `bytedcli auth status`；生产网的 `zti_jwt` 不可用或交换失败、且 ByteCloud Auth 未登录时，再运行 `bytedcli auth login`
2. **任务创建**：使用 `merlin-job-launch` 按模板或 fork 创建
3. **任务失败**：使用 `merlin-job-debug` 进行诊断
4. **评估相关**：根据具体场景选择对应的 Arena/Exercise 子技能
5. **服务部署**：storm 多角色（`storm_service` / `storm_service_pool`）走 `deploy roleset create`，不是 `deploy create`；pool 模式用 `--is-pool` 且每角色给 `num_pods`。优先用 `deploy roleset gen-config --service-id <id> --region <r> --role-gpu <role>=<gpu>` 自动生成 `roleset_deployment_config`（会按服务配置带出 role/is_socket/num_pods，并为 `cfs_enabled` 的 role 自动回填 `cfs_cluster`/`cfs_protocol`，来源 `deploy meta cfs-clusters`）。缺 `cfs_cluster` 时后端只回隐晦的 `error_code 384`，`deploy roleset create` 已在创建前预检。详见 [merlin-service](references/merlin-service/GUIDE.md)。
6. **兜底工具**：当其他子技能不适用时，使用 `bytedcli merlin` 直接调用 API

## Batch HPA configuration

`bytedcli merlin hpa-config get|update` uses the published CN OpenAPI gateway (`/api/v1/merlin/hpa-configs/get|update`), independently of the direct Merlin and Bernard API routes. Currently supports `--site cn` without `--vregion`; other sites fail explicitly. Authentication uses shared ByteCloud JWT login. Quota submissions require explicit `--as user` with your own login and a person-account JWT; the CLI checks the selected identity before preflight and the backend validates the JWT. Operator permission is checked by the server.

```bash
bytedcli --site cn --json merlin hpa-config get --service-selectors '[{"service_id":"demo-service","gpu_type":"h20"}]' --platform merlin-hpa
bytedcli --site cn --json merlin hpa-config get --service-selectors-file ./selectors.json
bytedcli --site cn --as user --json merlin hpa-config update --platform merlin-hpa --configs-file ./targets.json
bytedcli --site cn --as user --json merlin hpa-config update --platform merlin-hpa --configs-file ./targets.json --yes
```

Both files contain arrays, not whole request envelopes. `selectors.json` contains objects with `service_id` and `gpu_type`. `targets.json` example:

```json
[
  {
    "service_id": "demo-service",
    "gpu_type": "h20",
    "targets": [
      { "strategy": "gpu_utilization", "target_value": 28 },
      { "strategy": "min_instance_ratio", "target_value": 20 }
    ]
  }
]
```

`--configs` accepts the same array inline. Exactly one inline or file input is required; files are bounded regular JSON files (maximum 1 MiB), not stdin. Updates do not prompt: default is a read-only preview, `--yes` submits, and `--dry-run` always prevents writes. Save and inspect the preview first. It is a snapshot, not server-side dry-run; deployment membership and authorization may change before submission.

Choose GPU or SMA plus `min_instance_ratio`. Targets are percentages: Merlin accepts integers 0–100; Quota accepts 1–100, with integer GPU targets and fractional SMA/minimum-instance targets. Up to 50 distinct selectors, with a server limit of 500 expanded deployments. No automatic splitting or write retries. Merlin writes enable HPA. Quota submits asynchronous rule-change tickets and does not enable switches; acceptance does not mean the change is effective. Partial success is not rolled back; after an uncertain write, read back (and check Quota tickets) before retrying.

Query `--platform all` (default) reports failures from both platforms. `--platform merlin-hpa|quota` filters rows and computes status for that platform; resolution failures always fail. A service outside a Quota elastic group can therefore succeed with `--platform merlin-hpa` while `all` returns a partial failure. JSON preserves row details, recommendations, timestamps, warnings and resolve failures; partial failures return exit code 1.

Use exact GPU SKUs when targets differ. A family selector such as `a100` can expand to multiple memory SKUs; `t4` can include `t4-half`. One config applies the same targets to every matched deployment. `910B` covers the 910B/910B2 family, not 910B4; select the returned SKU or the correct family and inspect `resolve_failures`. Missing recommendation fields remain absent and are never filled with zero; SMA recommendations are NVIDIA-only.

HPA update output always includes `rows`, `resolve_failures`, and `warnings`. Preview and blocked submissions have empty `rows`; inspect `before.rows` for current configuration and `request.body.configs` for proposed targets. Submitted responses place write outcomes in `rows`. `warnings` contains backend messages; `notices` contains CLI guidance about expansion and preview limitations. Text mode renders a configuration table and explicit errors. CLI platform `merlin-hpa` maps to wire/output value `merlin_hpa`.

## Load testing and Rhino reports

`merlin loadtest` uses shared ByteCloud JWT authentication on default `--site cn` and `--site i18n-tt`. Other sites and vregions are rejected. This richer native workflow complements the low-level `rhino` commands.

```bash
bytedcli merlin loadtest precheck --service-id demo-service
bytedcli merlin loadtest create --service-ids demo-a,demo-b --task-duration 5m --latency-threshold 100ms
bytedcli merlin loadtest create --service-ids-file ./services.json --yes
bytedcli merlin loadtest create --from-task lt-demo
bytedcli merlin loadtest config get --task-id lt-demo
bytedcli merlin loadtest config export --task-id lt-demo --output ./loadtest-config.json
bytedcli merlin loadtest governance get --service-id demo-service
bytedcli merlin loadtest governance get --service-id demo-service --start 1767225600 --end 1767312000
bytedcli merlin loadtest dataset list
bytedcli merlin loadtest list --service-ids demo-service --all-users --status success
bytedcli merlin loadtest get --task-id lt-demo
bytedcli merlin loadtest follow --task-id lt-demo --interval 10 --timeout 300
bytedcli merlin loadtest cancel --task-id lt-demo
```

Creation, cancellation and cloning default to preview. `--yes` submits; `--dry-run` takes precedence even with `--yes`. Creation runs all Merlin prechecks before submission, including in preview. Batch creation accepts 1–50 distinct service IDs, submits sequentially and stops after the first uncertain result. Inspect `rows`, `unsubmitted_service_ids`, `precheck` and `failed`; already submitted tasks are not rolled back. Writes never retry automatically. Inspect existing tasks before retrying an uncertain submission.

Creation supports latency threshold, duration, error rate (`5%` or `0.05`), starting/target QPS multipliers, pressure mode (`qps`/`concurrency`), latency percentile/aggregation and a metrics latency threshold. Bare durations are seconds; explicit `us`, `ms`, `s`, `m`, `h` are accepted. `--force-record` explicitly requests traffic recording. Submission generates real load and recording can affect a live service. `--freeform-config` is an escape hatch accepting a JSON array of objects whose values are strings; it cannot be combined with tuning flags and is rejected before any request.

`config get` normalizes the source task's service and freeform tuning into a versioned JSON object; the `create` block always carries the one-shot submission trigger type, while the source task's own trigger type stays under `source` for reference. `config export` writes the same object to an owner-only file. `create --from-task` reuses that service and tuning, always submits as a fresh one-shot submission instead of inheriting a cronjob or batch trigger, runs prechecks, and remains preview-only unless `--yes` is present; it cannot be mixed with service selectors or tuning flags.

`governance get` aggregates the latest successful result, GPU recommendation, prefill/decode topology, and current GPU count for one service. Optional `--start`/`--end` values are Unix seconds and only scope the latest-result lookup. Independent sections survive partial failures; inspect `errors` and the nonzero exit status. `dataset list` reads the available Seed datasets. These commands are read-only.

Get the actual Rhino report and supporting data:

```bash
bytedcli --json merlin loadtest report list --service-id demo-service
bytedcli --json merlin loadtest report get --task-id lt-demo
bytedcli --json merlin loadtest report get --task-id lt-demo --service-id demo-service
bytedcli --json merlin loadtest report get --service-id demo-service
bytedcli --json merlin loadtest report get --result-id 456
```

`report list` returns the latest report summaries by service/SKU, preserving report URLs, observed utilization/QPS and recommendations when present. `report get --service-id` chooses the newest Merlin task by creation time; it does not skip running tasks to find an older successful report. Specify `--task-id` for reproducibility. A native Rhino result ID can be queried directly and cannot be mixed with Merlin selectors; the Rhino task ID remains null when its association has not been resolved.

Report detail includes `info`, `report_url`, full `report` metadata, `execution_detail` data, `scaling_suggestion` and `deployment_info` when available. The full `report`/`execution_detail` sections are verified on the default CN control plane only; on other sites they are reported as failed sections with an explicit unsupported-host error while summaries and suggestions still return. Missing result IDs return `available: false` with an explanation, without inventing metrics. If one report section fails, successful sections remain in the response and `errors` identifies the failed sections; exit status is nonzero. Report URLs are metadata only; the CLI calls fixed authenticated Rhino APIs, not arbitrary report links. Use global `--json` to save the complete structured response. Waiting exits nonzero for failed/stopped/abnormal terminal states or timeout; each HTTP poll is bounded by the remaining deadline.

```bash
bytedcli merlin loadtest clone create --service-id demo-service --exec-id 123 --instances 1
bytedcli merlin loadtest clone get --clone-service-id demo-clone
bytedcli merlin loadtest profiling list --task-id lt-demo
bytedcli merlin loadtest profiling list --clone-service-id demo-clone
bytedcli merlin loadtest profiling get --job-id demo-job
```

Cloning creates resources only with `--yes`. Profiling commands inspect existing jobs; they do not start profiling. Spreadsheet retry/refresh workflows from gpucenter/agent are not part of this command surface.
