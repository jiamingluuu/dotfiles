---
name: bytedance-cronjob
description: "Operate ByteDance cronjob via bytedcli: list/get jobs, list records, list/get deploy & upgrade tickets, list US-TTP SRE candidates and choose NoC or a named SRE, create clusters, deploy jobs, rerun jobs, debug jobs, kill running task instances, find logs, view cluster resource/Argos info, and enable/disable a cronjob's scheduling (suspend/resume) or delete a cluster. Use when tasks mention cronjob, 定时任务, 任务调度, 发布, 升级版本, 补数, 重跑, 调试, 杀任务, kill, 停止实例, 工单, 发布单, 查日志, 集群, 新建集群, 创建集群, 开启定时任务, 关闭定时任务, 启用任务, 停用任务, 暂停调度, 恢复调度, 删除集群. 注意：开启/关闭（启用/停用）定时任务调度走 `cronjob cluster resume` / `cronjob cluster suspend`（开关在 cluster 的 suspend 字段上，cronjob 没有 job 级一键开关）。重要：当涉及查找日志时，必须优先确认任务所在的控制面 (Site) 环境，请务必参考 references/workflow-find-logs.md 流程。"
---

# Cronjob (bytedcli)

## 如何调用 bytedcli

推荐：先全局安装一次，后续所有命令直接调用 `bytedcli`。

```bash
# 推荐方式：先全局安装，后续直接调用 bytedcli
NPM_CONFIG_REGISTRY=http://bnpm.byted.org npm install -g @bytedance-dev/bytedcli@latest
bytedcli <command> [options]
```

```bash
# Fallback：仅在无法全局安装时使用 npx 临时执行
NPM_CONFIG_REGISTRY=http://bnpm.byted.org npx -y @bytedance-dev/bytedcli@latest <command> [options]
```

## When to use

- 列出 Cronjob 任务列表 (my 或 all)
- 获取 Cronjob 任务详情
- 列出 Cronjob 执行记录 (支持按 cluster-id / job-id / psm 筛选)
- 获取 Cronjob 实例详情
- 发布 Cronjob 任务到指定集群，升级 SCM 版本
- 列出某个任务的工单 (tickets / deploy_tickets)
- 获取单个工单详情
- 对工单执行发布动作：deploy / cancel / retry-safety-check / approve (默认 dry-run，--yes 才真正提交)
- 查询 US-TTP 候选 SRE，或在 USTS 审批步骤选择 NoC / 指定 SRE（选择审批方不等于审批通过）
- 查看工单回滚信息 (rollback-info：能否回滚、目标版本/区域/集群)
- 查看集群资源用量 (cluster resource：usage_cpu/usage_mem) 与 Argos 监控信息 (cluster argos)
- 新建集群 (cluster create：提交 createCluster ticket，默认 dry-run、--yes 才提交)
- 开启/关闭定时任务调度：`cluster suspend` 关闭（停用），`cluster resume` 开启（启用）；以及删除集群 (cluster delete)。默认 dry-run、--yes 才提交
- 查询 Cronjob 发布单状态
- 查找 Cronjob 任务日志 (含跨区域/I18n)
  - **重要**：必须优先执行 `references/workflow-find-logs.md` 中定义的站点确认流程。
- 重跑 Cronjob 任务 (支持依赖)
- 启动 Cronjob 调试容器 (空跑 sleep)
- 杀死正在运行的 Cronjob 任务实例 (含 rerun/debug 实例)
- 列出支持的挂载目录和可用区域

## 核心流程：查找日志 (Find Logs)

当用户请求查找 Cronjob 日志时，**严禁**直接在默认环境搜索。请务必遵循以下步骤：

1.  **阅读工作流**：立即阅读 `references/workflow-find-logs.md`。
2.  **确认站点 (Site)**：根据用户提供的关键词（如 I18n, TikTok, SG, US, Prod 等）确定 `--site` 参数。若不确定，**必须询问用户**。
3.  **获取 Cluster ID**：使用 `cronjob list-zones` 或 `cronjob list-jobs` 获取数字 ID，不能直接使用名称（如 `sg1`）。
4.  **提取链接**：通过 `cronjob get-instance` 获取 `argos_stdout_view_log` 等链接。

## 前置条件

- 按通用调用方式执行命令（含内网 registry）：`../../invocation.md`
- 需要鉴权的命令先登录：`bytedcli auth login`

## 常用命令

```bash
# 列出 Cronjob 任务
# 支持按关键词搜索，--type 默认为 my
bytedcli cronjob list-jobs \
  --type "my" --search "keyword" --page 1 --page-size 20

# 获取 Cronjob 任务详情
bytedcli cronjob get-job \
  --job-id 12345

# 列出 Cronjob 执行记录
# 必须指定 --cluster-id 或 --job-id 或 --psm 其中之一
# 支持按 --status (Running/Succeeded/Failed) 和 --task-type (cron/rerun/debug) 筛选
bytedcli cronjob list-job-records \
  --cluster-id 12345 --status "Succeeded" --page 1 --page-size 20

# 获取 Cronjob 实例详情
# instance-name 可以是完整的 task_name 或 rerun/debug 的前缀
bytedcli cronjob get-instance \
  --cluster-id 12345 --instance-name "job-instance-name"

# 重跑 Cronjob 任务
# --command 为必填，--run-deps 可选（是否跑依赖）
bytedcli cronjob rerun-job \
  --cluster-id 12345 --command "echo hello" --run-deps

# 杀死正在运行的任务实例
# --instance-name 为运行中实例名（task_name），可从 list-job-records / get-instance 获取
# rerun/debug 产生的实例同样适用
bytedcli cronjob task kill \
  --cluster-id 12345 --instance-name "rerun-1-abcd"

# 发布 Cronjob 任务
# deploy-job 是一个命令组，实际执行发布使用 deploy 子命令
bytedcli cronjob deploy-job \
  deploy --job-id 12345 --psm "cronjob.demo" --cluster-ids "85243,85244" \
  --scm-repo-id 123456 --scm-repo-name "demo/repo" --scm-repo-version "1.0.0.1"

# 查询发布单状态
# 发布单状态查询使用 deploy-job status 子命令
bytedcli cronjob deploy-job status \
  --ticket-id 30253713

# 列出某个任务的工单
# 默认读 job/{id}/tickets/；加 --deploy 读 job/{id}/deploy_tickets/
bytedcli cronjob ticket list \
  --job-id 12345 --deploy --page 1 --page-size 20

# 获取单个工单详情
# 取基础工单 (ticket/{id}/)；发布流水线实时视图用 deploy-job status
bytedcli cronjob ticket get \
  --ticket-id 30253713

# 对工单执行发布动作（危险写，默认 dry-run）
# deploy / cancel / retry-safety-check / approve 都是默认只打印将发送的请求
# 必须显式加 --yes 才真正提交
bytedcli cronjob ticket deploy --ticket-id 30253713          # dry-run，仅预览
bytedcli cronjob ticket cancel --ticket-id 30253713 --yes    # 真正取消
bytedcli cronjob ticket retry-safety-check --ticket-id 30253713 --yes
bytedcli cronjob ticket approve --ticket-id 30253713 --yes   # 通过 TTOPS 审批

# US-TTP：查询页面使用的候选 SRE 列表；--job-id 与 --ticket-id 二选一
bytedcli --site us-ttp cronjob ticket list-usts-approvers --ticket-id 123
bytedcli --site us-ttp cronjob ticket list-usts-approvers --job-id 234 --keyword demo

# 选择 USTS 审批方：父发布单与审批步骤是不同的 ID，默认只读校验并预览
bytedcli --site us-ttp cronjob ticket choose-usts-approver \
  --ticket-id 123 --step-id 456 --approver-type noc
bytedcli --site us-ttp cronjob ticket choose-usts-approver \
  --ticket-id 123 --step-id 456 --approver-type sre --approver demo.user --yes

# 查看工单回滚信息（只读）
bytedcli cronjob ticket rollback-info --ticket-id 30253713

# 查看集群资源用量与 Argos 监控信息（只读）
bytedcli cronjob cluster resource --cluster-id 12345   # usage_cpu / usage_mem
bytedcli cronjob cluster argos --cluster-id 12345      # Argos 监控/看板链接

# 新建集群（危险写，默认 dry-run，--yes 才提交）
# 默认创建为 suspend=true，并补 ENABLE_STREAM_LOG / SEC_TOKEN_PATH；如需关闭自动补齐可加 --no-default-envs
bytedcli cronjob cluster create \
  --job-id 12345 --name default --zone Example-Zone \
  --physical-cluster demo-physical --business-cluster demo-business \
  --cpu 4 --mem 8192 --max-exec-time 300 \
  --env CONF_ENV=prod-demo \
  --repos-json '[{"id":123456,"name":"demo/repo","version":"1.0.0.1","description":"demo"}]'

# 开启/关闭定时任务调度、删除集群（危险写，默认 dry-run，--yes 才提交）
# 关闭/停用定时任务 = suspend；开启/启用定时任务 = resume（开关在 cluster 上）
bytedcli cronjob cluster suspend --cluster-id 12345 --yes   # 关闭/停用定时任务调度
bytedcli cronjob cluster resume --cluster-id 12345 --yes    # 开启/启用定时任务调度
bytedcli cronjob cluster delete --cluster-id 12345 --yes    # 删除集群

# 启动 Cronjob 调试容器
# 默认执行 sleep 命令，--duration-sec 控制存活时长（默认 300s）
bytedcli cronjob debug-job \
  --cluster-id 12345 --duration-sec 300 --run-deps

# 列出支持的挂载目录
bytedcli cronjob list-mounts

# 列出可用区域和集群
bytedcli cronjob list-zones
```

## Notes

- `ticket list-usts-approvers` 读取 Job 的 `ttops_approver_list/`，传 `--ticket-id` 时先解析父单的 Job。`--keyword` 在完整结果中按用户名/姓名本地过滤，`total` 是过滤前数量，`count` 是返回数量，`keyword` 回显过滤关键词；`selectable_as_sre` 表示个人账号且非 NoC 组。该列表是可选人员，不代表已选审批人。
- `ticket choose-usts-approver` 支持 `us-ttp`、`us-ttp-bdee`、`us-ttp-usts`，复用个人 ByteCloud JWT。`noc` 固定选择 NoC 组织账号且禁止 `--approver`；`sre` 必须传候选列表中的唯一个人用户名。
- 选择命令默认只做实时只读校验和完整请求预览，`--yes` 才提交；显式 `--dry-run` 优先于 `--yes`。父发布单必须包含指定的、正在运行且明确允许 `choose_ttops_approver` 的 `ConfirmStep`；请求 URL 中使用 `--step-id`，不是父单 ID。写请求禁止自动重试与重定向。
- 选择成功只表示请求已提交。JSON 分别报告 `submitted`、`selection_verified` 和 `preflight` / `readback` 中的工单、阶段、步骤状态。当前工单 API 不暴露已选账号，因此 `selection_verified` 保持 `false`；`approval_users` 是可审批人员，`reviewers` 是已执行审核的人，两者都不是已选审批方的证据。**不要仅因 `selection_verified=false` 再次传 `--yes`，重复提交可能再次通知审批方。**
- 提交响应不明时返回 `CRONJOB_SUBMISSION_UNKNOWN`、`submitted=null`，并尝试回读状态；确认提交但回读失败时返回 `CRONJOB_READBACK_FAILED`、`submitted=true`。先检查发布单和审批通知再决定是否重试。选择命令不执行 `confirm` / `approve`，也不代表发布完成。
- 新流水线使用 `POST ticket/{step_id}/actions`；旧界面的 `ticket/{ticket_id}/notify_approver/` 是另一条协议。本命令只支持带审批步骤的新流水线，不会自动降级到旧接口。

- 需要结构化输出加 `--json`（全局选项，放在子命令之前，如 `bytedcli --json cronjob list-jobs`）
- `rerun-job` 支持 `--extra-args` 传递额外参数
- `task kill` 用于停止正在运行的实例；`--instance-name` 传实例名（task_name），先用 `list-job-records` / `get-instance` 拿到实例名再 kill
- `deploy-job` 通过 Cronjob `upgrade` 接口提交发布单，需要显式传 `job-id`、`psm`、`cluster-ids` 和目标 SCM 版本信息；CLI 会读取任务当前 SCM 仓库列表，替换目标仓库后提交完整 `scm_repos`
- `deploy-job` 是一级命令组，常用子命令是 `deploy` 和 `status`
- `ticket` 是一级命令组，`ticket list --job-id` 列出任务工单（`--deploy` 切到 deploy_tickets），`ticket get --ticket-id` 取基础工单详情；需要发布流水线的实时轮询视图时用 `deploy-job status`
- `ticket deploy/cancel/retry-safety-check/approve` 是危险写操作，**默认 dry-run**（只打印将发送的 `POST ticket/{id}/...` 请求，不实际调用）；确认无误后加 `--yes` 才真正提交，`--json` 下 `mode` 字段为 `dry_run` / `submitted`
- `ticket rollback-info` 是只读命令（GET `ticket/{id}/rollback_info/`），返回 `can_rollback`、不可回滚原因、目标 SCM 版本/区域/集群
- `cluster` 是一级命令组，`cluster resource --cluster-id` 看 CPU/MEM 用量（GET `cluster/{id}/resource/`），`cluster argos --cluster-id` 看 Argos 监控信息（GET `cluster/{id}/argos_info/`），均为只读
- `cluster create` 是危险写：提交 `POST job/{job_id}/cluster/` 的 createCluster ticket。默认 dry-run（打印 site+URL+method+body），加 `--yes` 才真正提交；默认 `suspend=true`，并按前端创建页补 `ENABLE_STREAM_LOG=true` 与 `SEC_TOKEN_PATH=/etc/tce_dynamic/identity.token`，可用 `--no-default-envs` 关闭自动补齐
- `cluster suspend/resume/delete` 是危险写：`suspend` = **关闭/停用定时任务在该集群上的调度**（PUT `cluster/{id}/` `{suspend:true}`），`resume` = **开启/启用调度**（`{suspend:false}`），`delete` 删除集群（DELETE `cluster/{id}/`）。均默认 dry-run（打印 site+URL+method+body），加 `--yes` 才真正提交
- **开启/关闭（启用/停用）一个定时任务**：cronjob 没有 job 级一键开关，开关在 cluster 的 `suspend` 字段上——用 `cronjob cluster resume`（开）/ `cronjob cluster suspend`（关）。一个任务跑在多个 cluster 上时，逐个 cluster 操作；先用 `get-job` 拿到 cluster id

## References

- `../../invocation.md`
- `references/workflow-find-logs.md`
