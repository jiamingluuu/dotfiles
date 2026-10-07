# BITS Dev Task 官方 Skill 路由

BITS Dev Task 的创建/新建流程由 BITS 官方 skill `bits-devops-dev-task` 维护。本仓不复制它的 create 流程，避免模板、项目推断、确认 UI 和 `bitscli` 参数随上游演进后产生两份不一致的说明。

Source of truth:
https://skills.bytedance.net/skill/skills:skills.byted.org/default/public/bits-devops-dev-task

## 路由规则

- 用户要创建或新建 Dev Task 时，加载官方 `bits-devops-dev-task`，按其 `prepare -> confirm -> submit` 流程执行。
- 官方 skill 的 submit 负责创建；本文件的“代码评审就绪检查”负责创建前补充信息与创建后回读。分别报告任务创建结果和评审状态，不因评审异步初始化或 Codebase 查询不可用而否认已成功创建的 Dev Task。
- `bytedcli bits develop ...` 保留用于用户明确要求 bytedcli、官方 skill/`bitscli` 暂时不可用，或需要本仓特有的底层排障命令时；不要把它作为创建 Dev Task 的默认入口。
- 不要把官方 skill 的正文复制回本仓。上游行为变化时，以 Source of truth 的最新版本为准。

## 代码评审就绪检查

创建包含代码变更的 Dev Task 时，拿到 Dev Task ID 代表任务记录已创建，但不代表代码评审已经可用。该检查用于防止误报评审就绪，不把只读查询或异步 MR 初始化升级为创建流程的额外硬依赖。

机器可读契约：

```json
{
  "contract": "bits-dev-task-review-readiness-v1",
  "precheck": {
    "prepare_selected_mr": "validate_selected_mr",
    "selected_mr_validation_unavailable": "continue_submit_without_reuse_field",
    "no_existing_mr": "continue_submit",
    "multiple_mrs_without_selection": "continue_submit_without_guessing",
    "precheck_unavailable": "continue_submit"
  },
  "result_states": ["ready", "pending", "attention_required", "not_applicable"],
  "bind_order": [
    "dry_run_with_revalidation",
    "confirm_if_needed",
    "live_with_revalidation",
    "readback"
  ],
  "bind_requires_confirmation": true
}
```

### prepare 后、confirm 前

1. 从 prepare 结果记录预期的代码变更集合，每项使用 `repo + source + target` 标识。prepare 明确没有代码项目时，后续评审状态为 `not_applicable`。
2. 源分支与目标分支都应出现在确认摘要中。用户未指定目标分支时，优先使用 prepare 返回值；缺失时可用 `bytedcli --json codebase repo get -R <repo>` 读取 `data.Repository.DefaultBranch`。若 best-effort 查询后仍无法确定，确认摘要标记目标分支未知、跳过已有 MR 匹配并继续官方 submit；不要猜成 `master`，也不要把本路由层的预查变成创建前置条件。只有官方 prepare 自身明确要求该输入时，才按官方流程向用户补充。
3. 若用户或官方 prepare 已选定 MR IID，不重复搜索或要求用户再次选择，但仍要 best-effort 读取该 MR，校验仓库、IID、open 状态和双分支。校验通过才把该 IID 写入尚未包含 MR 复用信息的 prepare 快照；校验失败、查询不可用或坐标不完整时继续官方 submit，但不由本路由层新增未经验证的 MR 复用字段，并将后续评审状态记为 `pending` 或 `attention_required`。没有已选 IID 时，可按精确的 `repo + source + target` best-effort 查询 open MR：

```bash
bytedcli --json codebase mr list \
  -R "example-org/example-repo" \
  --state open \
  --head feature/demo \
  --base master \
  -L 20
```

- 唯一命中一个 open MR：把该 MR IID 与“创建后绑定到 Change Card”的动作写进确认摘要。若官方 prepare 支持 MR 复用字段，直接写入 prepare 快照；否则 submit 后按下文绑定。
- 没有命中：继续官方流程，由 BITS 创建 MR；这不是错误，也不要求用户先手工创建 MR。
- 命中多条且官方 prepare 未选定 IID：不猜 MR。若官方流程需要选择则请用户选择；否则继续创建，并在提交后按实际回读结果报告状态。
- Codebase 查询因鉴权、权限、网络或仓库可见性失败：记录 `precheck_unavailable` 后继续官方流程。不要把查询失败解释成 0 个 MR，也不要让它阻塞 BITS 创建。

### submit 后强制回读

官方 submit 返回 `<dev-id>` 后，立即运行：

```bash
bytedcli --json bits develop inspect-changes --dev-id <dev-id>
```

将回读结果与 prepare 记录的预期集合逐项对账。等待预算内，预期有代码项目但 `change_count=0`、缺少对应卡片或出现重复卡片时先记为 `pending` 并继续回读；等待预算耗尽后仍不一致才转为 `attention_required`。只有 prepare 明确没有代码项目时，空 Change Card 才是 `not_applicable`。

对后端异步创建 MR 的情况，在不重复 submit 的前提下做有界轮询，总等待不超过 60 秒（例如立即、5 秒、15 秒、30 秒、60 秒）。每个代码型 Change Card 的评审就绪条件是：

- `target_branch` 非空，并与确认摘要中的目标分支一致；
- `iid > 0`；
- `binding_state=BOUND`。

轮询期间 Change Card 尚未出现，或 `iid=0` / `binding_state=UNBOUND` 且已有字段不存在矛盾时，都属于 `pending`，不是创建失败。超过等待预算仍未完成时返回稍后可重跑的 `inspect-changes` 命令，不自动重建任务，也不自动重复 submit。

### 绑定唯一匹配的已有 MR

若回读结果已经是 `BOUND`，但 `target_branch` 为空，先读取该 MR 并核对仓库、IID、open 状态和双分支；全部匹配时直接将评审状态判为 `ready`，使用 MR 的目标分支作为展示信息，不重复执行 `bind-mr`。

若回读结果为 `UNBOUND`，且 confirm 前已经找到并披露唯一匹配 MR，使用 canonical `change bind-mr` 入口。即使 Change Card 回读的目标分支为空，也必须把已验证的目标分支显式传给 `--target-branch`，不能依赖兼容入口的隐式 `master`。无需在两次绑定命令外重复运行 `codebase mr get`；每次 `change bind-mr` invocation 都会读取 Codebase MR，并要求其仍为 open，且仓库、IID、源分支和目标分支与已确认的 `repo + source + target` 完全一致：

1. 运行 `change bind-mr --dry-run`；该调用先重校验 MR，再展示将写入的完整绑定坐标。
2. 若这次绑定动作尚未包含在用户确认过的 prepare 摘要中，单独请求用户授权。
3. 用户授权后运行 `change bind-mr --yes`；该调用在提交前再次读取并重校验 MR，失败或查询不可用时停止 live 写入。
4. 再次运行 `inspect-changes`，以最终读回结果判定 `ready` 或 `attention_required`。

```bash
bytedcli --json bits develop change bind-mr \
  --dev-id <dev-id> \
  --change-id <change-id> \
  --mr <iid> \
  --target-branch <target-branch> \
  --dry-run

bytedcli --json bits develop change bind-mr \
  --dev-id <dev-id> \
  --change-id <change-id> \
  --mr <iid> \
  --target-branch <target-branch> \
  --yes
```

不要把原始创建确认扩张为未披露的 MR 绑定授权。

### 结果状态

输出中分别提供 `task_creation` 与 `code_review_readiness`，避免把“创建成功”和“评审已经可用”混成一个结论：

| 场景                                                                                                   | `task_creation` | `code_review_readiness` | 处理                                               |
| ------------------------------------------------------------------------------------------------------ | --------------- | ----------------------- | -------------------------------------------------- |
| prepare 明确没有代码项目                                                                               | `success`       | `not_applicable`        | 正常报告创建成功，不要求 MR                        |
| 预期 Change Card 全部存在且满足就绪条件；或已绑定历史卡片经 Codebase 回读确认实际目标分支              | `success`       | `ready`                 | 报告任务和 MR 链接                                 |
| 等待预算内预期卡片尚未出现/缺失/重复，或卡片坐标完整但 BITS 仍在异步创建或补全 MR                      | `success`       | `pending`               | 报告创建成功和稍后复查命令，不阻塞后续使用         |
| 等待预算耗尽后预期卡片仍缺失/重复；或已出现坐标矛盾、目标分支为空或不一致、回读失败、MR 漂移或绑定失败 | `success`       | `attention_required`    | 报告部分成功、证据与可执行修复步骤，不宣称评审就绪 |

`inspect-changes` 报错与返回 `change_count=0` 是两种不同状态，不能把回读错误当成没有代码变更。不要自动重建第二个 Dev Task；保留已创建任务供用户检查，避免同一分支出现多张重复工单或多个 MR。

## 为什么使用官方入口

官方 skill 把以下高风险步骤收口在同一流程中：

- prepare 阶段从当前仓库识别项目与分支，并返回工作区状态和确认路径；
- 多项目或多仓变更合并为一个 Dev Task，避免拆成多次 submit；
- submit 只消费当前会话生成并经用户确认的 prepare 快照；
- 创建结果回显实际项目和部署环境，便于创建后立即核对；
- 本路由层在 submit 后回读 Change Card，并把任务创建结果与代码评审就绪状态分别报告。

这些约束直接影响 Dev Task 后续流水线是否命中正确项目、分支、模板与环境，因此不在 bytedcli skill 中维护第二套创建编排。
