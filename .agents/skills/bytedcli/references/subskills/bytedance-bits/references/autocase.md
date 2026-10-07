# AutoCase 运行与报告

使用 `bytedcli bits autocase` 查询 AutoCase / Verse / BITS scenario plan 的运行，或对既有 manualTask 中一条精确叶执行一次通过。

## 对象 ID

- `planDetail/{scenarioPlanId}` 标识 scenario plan。
- `manualTask/{runId}` 标识可执行的 BITS run；其 ID 是后端 `TestPlanId`。
- URL 查询参数 `devops_space_old_id` 是 BITS/OneSite 的路由项目 ID；ID 模式的 `--project-id` 也必须传这个路由 ID。
- `run get` 返回的 `projectId` 是服务端业务 `ProductId`，不能直接复制为 `run pass --project-id`。需要写入时优先复用同一个完整 URL，或从 URL 的 `devops_space_old_id` 取得路由 ID。
- `--case-id` 是 `LeafInfo` 中的源 `CaseId`，不是列表序号；它必须与同一叶的 `--minder-id` 成对使用。

请保持 scenario plan、manualTask、路由项目、业务 ProductId 和叶 ID 的语义独立。优先传入完整的 BITS `manualTask` URL，因为 URL 同时携带 scenario plan、路由项目与 OneSite space 上下文。

## 命令

```bash
# 推荐：URL 携带 scenario plan、run、space 与 project routing（devops_space_old_id）。
bytedcli bits autocase run get \
  --url "https://bits.bytedance.net/devops/<space-id>/quality/plan/scenarios/planDetail/<scenario-plan-id>/manualTask/<run-id>?devops_space_old_id=<routing-project-id>"

# 仅传 run ID 时，--project-id 必须是 URL 的路由项目 ID，不是 run get 返回的 ProductId。
bytedcli bits autocase run get --id <run-id> --project-id <routing-project-id> --space-id <space-id>

# 使用统一 deadline 轮询。
bytedcli bits autocase run get --wait \
  --url "https://bits.bytedance.net/devops/<space-id>/quality/plan/scenarios/planDetail/<scenario-plan-id>/manualTask/<run-id>?devops_space_old_id=<routing-project-id>" \
  --timeout-ms 1800000 --poll-interval-ms 15000

# 原子写入 report.json；路由仍来自 URL。
bytedcli bits autocase run report \
  --url "https://bits.bytedance.net/devops/<space-id>/quality/plan/scenarios/planDetail/<scenario-plan-id>/manualTask/<run-id>?devops_space_old_id=<routing-project-id>" \
  --out ./autocase-report

# 预览一条精确的源 CaseId + MinderId 叶（默认也是预览）。
bytedcli bits autocase run pass \
  --url "https://bits.bytedance.net/devops/<space-id>/quality/plan/scenarios/planDetail/<scenario-plan-id>/manualTask/<run-id>?devops_space_old_id=<routing-project-id>" \
  --case-id <source-case-id> --minder-id <minder-id> --dry-run

# 明确提交一次并回读同一叶确认 Status=1。
bytedcli bits autocase run pass \
  --id <run-id> --project-id <routing-project-id> --space-id <space-id> \
  --case-id <source-case-id> --minder-id <minder-id> --yes
```

## 字段复制与精确叶查找

`run get --json` 的 `data.projectId` 是业务 ProductId，不能用它替代写入路由。若使用 URL，直接把同一个 URL 传给 `run pass`；若使用 ID 模式，从原 URL 的 `devops_space_old_id` 复制路由项目值到 `--project-id`，不要从 `data.projectId` 猜测。

要取得精确的源 `CaseId` 与叶 `MinderId`，对同一 URL 使用只读 `test-plan get`，遍历实际返回的 `data.LeafInfo`，不要取第一条或把数组位置当作 `CaseId`。`LeafInfo` 外层 map key 是 `TestCaseId` 分组键，不能替代叶对象中的源 `CaseId`；以叶对象的 `CaseId + MinderId` 为准：

```bash
bytedcli --json test-plan get \
  --url "https://bits.bytedance.net/devops/<space-id>/quality/plan/scenarios/planDetail/<scenario-plan-id>/manualTask/<run-id>?devops_space_old_id=<routing-project-id>" > ./autocase-leaf.json
```

核对叶对象的 `CaseId` / `MinderId` 后，再把同一对值传给 `run pass`；外层 `TestCaseId` 只用于分组定位，不要把它当作 `CaseId`。`run report` 的旧 `projectId` 同样是报告侧业务项目字段，不是可供 `run pass` 猜测的路由来源。

## 单叶通过

`run pass` 先读取当前 manualTask 的 `LeafInfo[TestCaseId][MinderId]`，再按叶对象中的源 `CaseId` 精确匹配目标，只允许未执行、失败、阻塞或跳过叶目标通过；已经通过的叶返回 `noOp`，不会重复写入。默认与 `--dry-run` 都是预览，文本会明确显示 `Not executed`；JSON 中 `dryRun:true` 或 `noOp:true` 且 `write:"not-run"` 表示命令业务成功但没有执行平台写入。只有 `--yes` 才调用单 case/minder 的通过接口，`--dry-run` 与 `--yes` 不能同时使用。

提交后命令会重新读取同一 CaseId + MinderId，并仅在其状态确认为通过时报告 `verification: confirmed`。明确业务拒绝会失败；网络错误、响应无法解析或回读不一致会区分为未知/部分成功，命令不会自动重放。Operator 从当前登录身份取得，不接受手填凭据或认证头；该命令不批量执行、不修改备注、不改变其他叶或整个计划状态。

## 运行状态

`run get --wait` 将 BITS 平台状态映射为 `succeeded`、`failed`、`blocked`、`exception` 和 `canceled`。失败的 run 退出码为 `2`；blocked 或 exception run 退出码为 `3`；canceled run 与超时退出码为 `4`。

## Plan 执行限制

经验证，BITS `CreateTestPlan` 操作接收完整的创建模板，包括基础信息、测试配置、case 选择、路由上下文与操作人；它会创建 scenario plan，并通过 `GetTestPlanTaskList` 暴露生成的 `manualTask`。该操作不支持仅凭现有 `planDetail/{scenarioPlanId}` 发起执行。独立的 `ExecuteTestPlan` contract 只会更新现有 `manualTask` 内的 minder results。

请先在 BITS 中启动现有 scenario plan，再将生成的 `manualTask` URL 传给 run 命令。

## 报告与 Evidence

`run report` 通过同目录临时文件与原子 rename 写入 `report.json`。报告包含 run 摘要字段、业务项目字段、可用的聚合报告数据，以及稳定的 AI / report evidence URL。

经验证的 API 会返回 evidence link，但没有稳定的鉴权附件下载 contract。因此该命令只记录元数据，不跟随 redirect 或下载文件，避免不安全跳转、错误 MIME 处理和凭据泄漏。
