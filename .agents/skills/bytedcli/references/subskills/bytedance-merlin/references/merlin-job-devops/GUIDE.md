---
name: merlin-job-devops
description: 对运行中的 merlin, seed 任务执行运维操作：查看日志与训练进度、查询时间线与 Pod 退出信息、在 Pod 内执行命令、获取 Grafana 监控链接、停止任务、审计热更新历史。当用户说"查看任务日志/任务进度/查询时间线/Pod 退出码/在任务里执行命令/获取 Grafana/停止任务/终止任务/任务运维/热更新审计/hot update"时使用。
---

# Job 运行态操作

对运行中的 Merlin 任务执行运维操作。根据用户需求阅读对应的 reference 文件获取详细步骤。

## 前置条件

- `bytedcli merlin` 可用
- 知道 `job_run_id`（部分操作还需 `trial_id`）

```bash
bytedcli merlin --help &>/dev/null || \
  NPM_CONFIG_REGISTRY=http://bnpm.byted.org npx -y @bytedance-dev/bytedcli@latest merlin --help
```

如果出现认证错误（401/403），运行 `bytedcli auth login`。

## 操作分类

| 操作 | 详细文档 | 关键命令 |
|------|----------|----------|
| 查看日志、分析训练进度 | `references/logs.md` | `job list-trial-logs` + 压缩脚本 |
| 查询时间线、Pod 退出信息 | `references/timeline.md` | `job get-timeline` + `job list-trial-exit-info` |
| 在 Pod 内执行命令 | `references/execute.md` | `job execute-script` |
| 获取 Grafana 监控链接 | `references/grafana.md` | `job get-grafana` |
| 停止任务 | `references/stop.md` | `job stop-run` |
| 热更新历史审计 | `references/hot-update-audit.md` | `job get-timeline` + `job hot-update` + `checkpoint get-step` |

## 获取任务 SSH 指令

```bash
# 只读输出一条可复制命令，不建立 SSH 连接
bytedcli --site i18n-tt merlin job ssh-command get --job demo-job
# JSON 同时返回 command、args（不含 ssh 可执行文件名）、实例及网关信息
bytedcli --site i18n-tt --json merlin job ssh-command get --job demo-job --trial-id 123 --instance-id 456
```

- `--job` 接受任务 ID 或完整任务 URL，由 URL 解析目标站点。当前只支持已验证的 ROW（i18n-tt），即使传入 ROW URL 也需配置 `--site i18n-tt`，确保任务和当前用户使用同站点认证；站点冲突明确报错，不回退 CN。
- trial 优先级为显式 `--trial-id` > URL 的 `trialId` > 任务当前 trial；历史 trial 需通过任务的 trial 列表校验归属，最多读取 100 页，达到上限时报 `MERLIN_SSH_TRIAL_LOOKUP_LIMIT`，不判定为不属于该任务。`--vdc` 不受支持，传入任务 URL 时也会明确报错。
- 未传 `--instance-id` 时，仅在 trial 恰有一个实例时自动选择；多实例返回候选信息并要求选择。URL 的 `instanceId` 也可用于选择，显式参数优先。
- 命令按前端规则由任务 ID、`natural_id` 的最后一个 `__` 段、编码后的当前用户名和实时 `job-ssh-host` 配置生成，不使用表格 Host IP。网关附加参数当前只接受空值或 `-p <port>`（1–65535，不接受前导零）；配置缺失、主机名超过 253 字符、实例列表不完整、超过 500 个实例或实例未运行时拒绝生成。
- 文本模式输出经过 shell 引号处理的单条命令；生成成功不代表已获 SSH 权限或可连接。公钥管理使用 `merlin cpu-devbox ssh-keys get/upload/delete`；本命令不会修改公钥、申请授权或调用远程执行接口。

## 脚本

| 脚本 | 路径 | 作用 |
|------|------|------|
| 日志下载与压缩 | `scripts/download_and_compress_logs.py` | 下载日志 + 压缩片段 + 增量模式 |
| 批量日志抓取 | `scripts/batch-get-jobs.sh` | 兜底快速抓取最后 N 行日志 |

---

## 关联技能

- `merlin-job-debug`：任务失败与 hang 诊断
- `merlin-job-launch`：创建并启动任务
