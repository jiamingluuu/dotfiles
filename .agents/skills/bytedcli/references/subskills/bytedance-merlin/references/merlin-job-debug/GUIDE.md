---
name: merlin-job-debug
description: |
  排查 Merlin / Seed 训练任务失败、hang、Robust Training 多 run 重启与在线观测；输出结构化结论与可执行修复方案。覆盖：时间线与 Pod 退出信息、事后静态分析（含 analyze_failure 脚本）、在线排查、Mega/Xray hang（NCCL / pyspy）、Karl / Grafana。当用户问「任务为什么失败 / hang / NCCL / robust 重启 / 训练卡住 / 分析 exit code / 代码定位报错行」时使用。
---

# 任务诊断与排障

本技能合并了历史 **`merlin-job-troubleshoot-failure`** 与 seed **`job-debug`** 的流程：在 Merlin 官方「状态分流 + failure/hang 参考」之上，补充 **时间线 → 静态事后分析 → 在线排查** 分层策略与脚本化入口。

## 前置条件

- `bytedcli merlin` 可用；认证问题执行 `bytedcli auth login`（详见 `bytedcli merlin` 技能）。
- 知道任务 URL 或 `job_run_id`；事后/多 run 分析需要 `trial_id`。
- **代码定位**：静态分析阶段如需把日志栈映射到仓库行号，可调用 **`code-repo`**（seed `rd-skills` 技能包名仍为 `code-repo`）克隆任务对应 commit 并阅读源码。
- Bash / `curl` / `rg` 等用于拉取日志；可选使用本目录 `scripts/analyze_failure.py`。

```bash
bytedcli merlin --help &>/dev/null || \
  NPM_CONFIG_REGISTRY=http://bnpm.byted.org npx -y @bytedance-dev/bytedcli@latest merlin --help
```

## 分层策略（与历史 `job-debug` 对齐）

| 阶段 | 适用 | 做什么 |
|------|------|--------|
| 时间线 / Pod 退出 | 任意需上下文 | `job list-trial-exit-info`、Robust 事件边界 |
| **模式 A — 事后分析** | `FAILED` / `TERMINATED` / `FAILED_TO_LAUNCH` | 退出码 + 日志 + 代码定位；见 `references/post-mortem.md` |
| **模式 B — 在线排查** | 静态证据不足，或任务 `RUNNING` 需容器内观测 | 见 `references/live-debug.md` |

**选择建议**：终态优先模式 A；模式 A 无法高置信定位 → 升级模式 B；任务 `RUNNING` 但疑似假活 → 结合 `references/hang-diagnosis.md` 与模式 B。

## 诊断分流（Merlin 平台）

先取任务状态：

```bash
bytedcli merlin job get-run --job-run-id '<id>'
```

| 任务状态 | 诊断路径 |
|----------|----------|
| `FAILED` / `FAILED_TO_LAUNCH` | `references/failure-diagnosis.md`（平台失败路径）+ **必要时** `references/post-mortem.md`（多 run / 脚本化） |
| `RUNNING` 但无进展（hang） | `references/hang-diagnosis.md` |
| `RUNNING` 正常 | 用 `merlin-job-devops` 看日志与进度 |
| `PENDING` | 排队中，稍后再查 |
| `SUCCEEDED` / `TERMINATED` | 一般无需排障；若需复盘仍可用模式 A |

## Pod 退出信息与 Robust 边界

```bash
bytedcli merlin job list-trial-exit-info \
  --job-run-id <id> \
  --trial-id <trial_id> \
  --filter '{"robust_run_index":<0-N>}'
```

- 返回状态、退出码、错误摘要；作为事后分析输入。
- **Robust Training**：时间线里 `RobustHotUpdate` 等事件标识 run 边界，便于逐 run 分析。

## 模式 A — 事后分析（脚本入口）

详见 **`references/post-mortem.md`**。快速命令：

```bash
python3 scripts/analyze_failure.py "<job_run_id_or_url>" --trial-id "<trial_id>"
python3 scripts/analyze_failure.py "<job_run_id>" --trial-id "<trial_id>" --all-runs --out /tmp/post_mortem.md
```

## 模式 B — 在线排查

详见 **`references/live-debug.md`**（容器内观测、分层检查）。

## 通用工具

```bash
bytedcli merlin job get-run --job-run-id '<id>'
bytedcli merlin job list-trial-exit-info --job-run-id '<id>' --trial-id '<trial_id>'
bytedcli merlin job list-trial-logs --job-run-id '<id>' --trial-id '<trial_id>'
bytedcli merlin job get-grafana --job-run-id '<id>'
bytedcli --site i18n-tt --json merlin trial watch poll --job '<id>'
bytedcli --site i18n-tt --json merlin trial watch follow --job '<id>' --mode until-terminal
bytedcli --site i18n-tt merlin job metrics --job '<id>' --window 15m
bytedcli --site i18n-tt merlin job list --status running --perf-metrics
bytedcli merlin knowledge search --user-query '<error_keyword>'
```

`trial watch` is handwritten. Branch on `outcome` (`healthy` / `needs_intervention` / `no_claim`), never on event kind. It does **not** stop the trial; stop-loss is notify_only. `trial diagnose` is Arnold scheduling/quota — a different API.

`job metrics` is handwritten (not MCP): Grafana OpenAPI `only_data` (viewport height 6000px) for per-GPU SM/mem/tensor plus Byteplot host mem. Branch on `coverage.complete`; incomplete reports exit 4 unless `--allow-partial`. `job list --perf-metrics` is a different number — a whole-run blend from `POST /api/v1/job_run/get_gpu_usage`.

### 在 trial pod 上执行命令（webshell exec）

`RUNNING` 任务需要进容器观测时，用 `merlin webshell exec` 直接在某个 pod（Ray head / worker）上跑命令并取回 stdout + exit code，无需开浏览器。`--trial-id` 与 `--merlin-job-id` 都来自任务 URL `…/jobs/<merlin-job-id>?trialId=<trial-id>`。

```bash
# 默认连第一个实例；--pod head|worker|worker-N|<pod_name> 指定节点，或 --instance-id <id>
bytedcli --site cn --vregion seed merlin webshell exec \
  --trial-id '<trial_id>' --merlin-job-id '<job_run_id>' --pod head --command 'nvidia-smi'
# JSON 模式返回 {output, exit_code}，便于 agent 消费
bytedcli --json --site cn --vregion seed merlin webshell exec \
  --trial-id '<trial_id>' --merlin-job-id '<job_run_id>' --command 'hostname'
# 仅当上一步返回 MERLIN_WEBSHELL_OTP_REQUIRED 时：以 stdin pipe 注入一行 Seal/飞连 OTP
bytedcli --site cn --vregion seed merlin webshell exec \
  --trial-id '<trial_id>' --merlin-job-id '<job_run_id>' --command 'hostname' --otp-stdin
# Agent 应以管道子进程方式启动上行命令，将 secret input 获得的一行 OTP 写入 stdin 后关闭
```

需先 `bytedcli auth login --session`（webshell relay 走 SSO cookie）。若返回 `MERLIN_WEBSHELL_PERMISSION_REQUIRED`，先在 Merlin/Seed UI 的 Webshell 页授权（可能需 BPM 工单）。

WebShell OTP 门禁（与 `tce webshell exec` 同一 relay）：

- 首次调用不要预先索要 OTP；目标无需 OTP 时命令直接执行。
- 提示文案可能是 `please input otp code`、`please input seal/feilian OTP code` 或 `请输入Google Authenticator OTP码（输入q退出）`，CLI 均能识别。
- 返回 `MERLIN_WEBSHELL_OTP_REQUIRED` 时，保留原参数，通过模型对话之外的 secret input 获取当前 OTP，再以 stdin pipe 启动同一命令并加 `--otp-stdin`，写入一行后关闭 stdin。不要通过 argv、环境变量、文件、日志或普通对话传递 OTP。
- `MERLIN_WEBSHELL_OTP_INVALID`：丢弃该 OTP 并重新请求，禁止自动重放；`MERLIN_WEBSHELL_OTP_TIMEOUT`：用当前 OTP 重新连接重试。认证失败时业务命令不会发出。

## 输出

- 结构化诊断：失败类别、最可能原因、关键日志/退出信息、（如有）代码位置
- 可执行修复：资源 / 镜像 / 入口 / 依赖 / Robust 策略
- **非中国区 TOS**：日志下载若遇 `tosv.byted.org` 不可用，可替换为 `cdn-tos-cn.bytedance.net`（全球可达）。参考：[说明文档](https://bytedance.us.larkoffice.com/docx/U6vLdvE1RoLB4lx1RNhubX2NsRf)

---

## 关联技能

- `merlin-job-devops`：日志、时间线、Pod
- `merlin-job-resource`：配额与队列
- `merlin-job-launch`：创建 / fork / 重试
- `job-monitor`（`seed/rd-skills`）：周期性监控与异常自愈（含 Cron 方案，见 `skills/job-monitor/references/`）
- `code-repo`：代码级定位与修改（与 Merlin 任务 commit 对齐）
