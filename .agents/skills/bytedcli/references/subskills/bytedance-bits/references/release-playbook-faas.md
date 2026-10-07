# BITS 发布单 FaaS 上线 Playbook（demo-faas 实战沉淀 2026-08-04）

> 本文档来自 example.faas.demo-service 空 post 重试修复（MR #50）上线实战，覆盖 BITS 发布单跑 FaaS 升级流水线（`create_faas_upgrade_ticket`）的完整链路：从解锁 can-run 到 FaaS 工单模板变量物化、人工卡点放行、发布后日志验证。**核心结论：FaaS 发布流水线的 `faas_deploy_config` 系统变量只在发布确认表单提交时物化，直接调 `cd/pipeline/run` 会因模板变量不解析而失败。**

本文目录：
0. 发布链路总览
1. 解锁 can-run 固定顺序
2. FaaS 升级工单模板变量物化（最高频坑）
3. 发布单维度门禁与 QCSS 处理
4. 125536 阶段流转失败
5. 本地直调 BITS API
6. 发布后验证
7. 飞书战报/直播卡

## 0. 发布链路总览（开发任务 → 发布单）

FaaS 服务（如 demo-faas）上线**必须走 BITS 开发任务 → 发布单**，禁止 FaaS 平台直发。链路：

```text
dev task（MR 合入 master）→ 建发布单（r2）→ 解锁 can-run → 前端发布确认流提交 run
→ 人工卡点放行 → Canary→Single DC→All DCs → stage operation → RELEASED (status=6)
```

## 1. 解锁 can-run 的固定顺序（canRun=false reason 2 时照做）

```bash
# 发布单维度推进（r2 门禁全绿 + canRun=true 后，直接走发布单，不再碰 dev pass-stage）
bytedcli bits release complete-integration --ticket-id <rtId> --operator <operator>   # status 3→4
bytedcli bits release start-integration --ticket-id <rtId>                          # stageStatus 0→1
bytedcli bits release stage check --ticket-id <rtId> --stage-id <stageId> --operator <operator>
# ★ 真正的解锁键：release 维度 QCSS 人工项（先 dry-run 解析 report/check id）
bytedcli bytestable qcss manual pass --space-id <space_id> --dev-id <rtId> --stage <stageId> \
  --check-name "确认本次上线依赖的TCC配置完成" --remark "<TCC 证据或无变更说明>" --dry-run
# 去掉 --dry-run 正式通过
bytedcli bits release pipeline can-run --ticket-id <rtId> --stage-id <stageId>      # → true
```

- `--dev-id` 在 release 维度传**发布单 id**（不是 dev task id），`--stage` 传**数字 stageId**（`bits release stages` 拿）。
- `qcss manual pass` 返回 13001「报告完结态不可改」= 解析到旧报告，以 `final-result` 为准。

## 2. FaaS 升级工单模板变量物化（最高频踩坑，务必先读）

**症状**：发布流水线「创建FaaS升级工单」节点失败，job 详情报：

```text
faasmodel.CreateFAASTicketStreamCtx.ClusterInfo: []*v2.ReleaseClusters:
decode slice: expect [ or n, but found ", error found in #10 byte of ...|cluster_info":"{{sys.release_ticket.faas_deploy_config['cluster_i|...
```

**根因**：流水线模板 `create_faas_upgrade_ticket` 的 inputs 引用 `{{sys.release_ticket.faas_deploy_config['cluster_info']}}` / `['rolling_percentage']`。`sys.release_ticket.faas_deploy_config` 是 **needLoadWhenRender 系统变量**，只在发布确认表单渲染/提交时物化。直接/CLI 调 `cd/pipeline/run` 缺 `params` → 模板变量不解析 → 报错。

**正解 = 前端发布确认流（4 步序列）**，前端「Run deployment pipeline」按钮会依次发：

```text
1) POST /api/v1/cd/pipeline/run_vars
   {"stageId":"<stageId>","releaseTicketId":"<rtId>","selectedControlPlane":1,
    "selectedProjects":[{"projectUniqueId":"<psm>","projectType":2,"projectName":"<psm>"}]}
2) POST /api/v1/cd/pipeline/run_pre_check        ← body 带完整 params（关键）
   {"checkItemId":"<rtId>","username":"<operator>",
    "params":{"selectedProjects":[{"controlPlane":1,
      "deployTarget":{...},
      "artifact":{...,"scmArtifacts":[{"scmName":"<scm>","revision":"master","targetCommitHash":"<sha>"}]},
      "strategy":{...,"faasStrategy":{
        "publishMode":1,"volumeStrategy":2,"grayPercentage":10,"rollingPercentage":10,"envName":"prod",
        "clusters":[{"region":"cn-beijing","cluster":"cluster-a","dc":"dc-a","functionId":"<fn>"},
                    {"region":"cn-north","cluster":"cluster-b","dc":"dc-b","functionId":"<fn>"}],
        "selectedClusterUniqueKeys":["cn-beijing_cluster-a","cn-north_cluster-b"]},
        "deployResource":{...}}],...},"workflowType":1}
3) POST /api/v1/cd/pipeline/pre_set_batch_stage_pipeline_run_key
   {"stageId":<数字>,"releaseTicketId":"<rtId>","controlPlanes":[1],"runTimestamp":<ms>}
4) POST /api/v1/cd/pipeline/run                   ← params 与 run_pre_check 相同
   {"stageId":"<stageId>","releaseTicketId":"<rtId>","username":"<operator>",
    "params":{...与 2 相同...},"runTimestamp":<ms>}
```

要点：
- **`cd/pipeline/run` 的 `params` 必须带 `strategy.faasStrategy`（双集群）+ `deployResource`（scm master@commit）**，否则模板变量空转。
- `pre_set_batch_stage_pipeline_run_key` 的 `stageId` 是**数字**，`run`/`run_vars`/`run_pre_check` 是**字符串**。
- `change-item deploy-strategy update`（`POST .../change_item/deploy_strategy`）只改存储、**不**触发模板物化——别指望它修复。
- 本地复刻该序列：逐条直调上述 HTTP 接口即可；第 2 步 body 可从 `deploy-strategy get` 的返回组装 faasStrategy。

## 3. 发布单维度门禁与 QCSS 处理

- 发布阶段门禁是**发布单维度**：`bits develop gatekeeper list --release-ticket-id <rtId> --stage <数字stageId>`。
- 「质量门禁」QCSS 项 skippable=true，可直接 `gatekeeper skip --check-id <id> --reason "..."`（会生成 BPM 审批单，approver 收到后通过即转 Success）。
- 项目流水线人工卡点（`user_confirm`，审批人=操作者自己）：放行

```bash
bytedcli bits job-run continue-release --job-run-id <jobRunId> --pipeline-run-id <runId>
```

## 4. 125536 阶段流转失败（dev 指针钉已取消发布单）

**症状**：`bits develop publish` / `pass-stage` 报 `125536 阶段流转失败: 请重试`，hint 永远说 "QCSS check items are pending"。

**根因**：dev 任务 `releaseTicketAssociatedOneDevTask` 指针钉在**已取消的旧发布单**（r1），pass-stage 按关联单解析 QCSS 报告 → 报告不存在 → 125536。**QCSS 全绿也照样报**（它查的不是当前单）。

**解法**：**不要**试图解绑 dev（`bind-release` 在合入阶段报 125006「合入阶段无法解绑」）。r2 门禁全绿 + canRun=true 后，**直接走发布单维度**（§1 的 complete-integration → start-integration → stage check → pipeline run），完全绕开 dev pass-stage。

## 5. 本地直调 BITS API（免浏览器）

> 说明：以下端点可直接以 HTTP 方式直调（如 `curl` / 脚本）；无需浏览器。鉴权头见上。

鉴权：`X-Jwt-Token`（`bytedcli auth get-bytecloud-jwt-token`）+ `X-Accept-Format: bytecycle/v1`，无需浏览器/登录态。

高频端点（反编译前端 JS 全量入库 1398 端点，缓存 `/tmp/bits-api-catalog.json`）：

| 用途 | 端点 |
|---|---|
| can-run 预检 | `GET /api/v1/cd/release_ticket/<rt>/stage/<sid>/pipeline_runnable` |
| 阶段流水线概览 | `GET /api/v1/cd/release_ticket/<rt>/stage/<sid>/pipeline` |
| 流水线 run 列表/详情 | `GET /api/v1/pipelines/runs?pipelineId=<pid>&pageSize=5&pageNum=1` |
| job 操作枚举 | `POST /api/v1/p/pipelines/group_job_run_operation/batch` body `{"pipelineRunIds":["<rid>"],"spaceId":<sid>}` |
| 阶段状态 | `GET /api/v1/cd/release_ticket/<rt>/execution/latest_status` |
| 部署策略 | `GET /api/v1/cd/release_ticket/<rt>/change_item/deploy_strategy?controlPlane=1&projectUniqueId=<psm>&projectType=2` |
| 系统变量 | `GET /api/v1/cd/release_ticket/vars?workspaceId=<ws>&releaseTicketId=<rt>&includeSysVars=true` |

## 6. 发布后验证（日志回捞 + 错误率对比）

```bash
# 修复生效验证：回捞新签名，应命中 retry_count_source=s:retry
bytedcli log search-psm-log --psm example.faas.demo-service \
  --keyword "skip article commit wake-up event" --start <RFC3339> --end <RFC3339> --output console
# 错误率对比（同一错误签名）
bytedcli log search-psm-log --psm example.faas.demo-service \
  --keyword "article commit post data is empty" --start <pre> --end <pre> --output console
```

判定标准：
- 回捞 `skip ... wake-up` 出现 `retry_count_source=s:retry` → 修复生效（EventBus header 重投计数读取成功）。
- 新实例（cold-start pod）错误率 vs 发布前基线：风暴 32/min → 稳态 ~1/min 且 ack 数远大于 retry 数 → 收敛。
- 发布后短窗口内错误含**旧实例滚动下线残留**，要按 `_podname` 过滤（`<old-pod-prefix>-*` 旧 vs `cold-start-instance-*` 新）。

## 7. 飞书战报/直播卡

- 直播卡：`.agents/skills/release-lark-card`（发布开始发卡 Pin → 原地刷新 → 成功绿卡自动取消 Pin）。
- 战报卡：schema 2.0 green template，column_set 大数字 + stage_table 对比行；table rows 必须 5 字段 dict（stage/status/start/time/note），数组行会 200914。
