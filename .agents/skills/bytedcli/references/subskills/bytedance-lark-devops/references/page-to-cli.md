# lark-devops 平台页面操作 → CLI 命令映射

> 本文件记录 lark-devops 发布平台（工单详情页）上的可视化操作，分别对应 bytedcli 的哪个命令。
> 示例环境：发布版 v0.79.0，simple flow 工单 process_id=12347 / space_id=67。
> 命令前缀统一为 `bytedcli lark-devops release ...`。
> 约定：所有写操作默认 dry-run（只回显 endpoint+payload），真正写入须追加 `--execute --yes-i-know-this-is-live`。

---

## 一、工单创建 / 总览

| 页面操作                                 | CLI 命令                                                   | 说明                                                 |
| ---------------------------------------- | ---------------------------------------------------------- | ---------------------------------------------------- |
| 新建发布单（提单：填名称/类型）          | `release create --space-id <id> --name <名> --flow simple` | 只建工单骨架，不含 app。`--flow dev` 走 BOE 开发流。 |
| 查看工单原始详情                         | `release get --process-id <id>`                            | 纯读，返回平台原始 detail。                          |
| 工单整体审批视图（各 stage 的 app 列表） | `release audit inspect --process-id <id>`                  | 读 PRE/GRAY/ONLINE 各阶段 app 分布。                 |

## 二、审批流程页（普通发布 simple flow）

工单详情页顶部 4 步：①应用确认 → ②发布时间确认 → ③需求/缺陷确认 → ④审批提交&审批结果。

### ① 应用确认阶段

| 页面操作                                              | CLI 命令                                                                                                                            | 说明                                                                                                                                                                                                                                                                                                                           |
| ----------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| 「新增/更新应用」按钮（把 app 加入工单）              | `release audit add-app --process-id <id> --space-id <id> --app-id <id> --app-name <psm>`                                            | 平台默认把 app 铺到所有 stage、勾选所有 unit 的所有集群。                                                                                                                                                                                                                                                                      |
| 「编辑」按钮内：选 unit / 区域                        | `release audit apply-stage ... --file <plan.json>`，plan 内 `units.<UNIT>.is_deploy`                                                | `is_deploy:false` = 取消勾选该 unit（即「移除」app 也靠全 unit 关闭）。                                                                                                                                                                                                                                                        |
| 「编辑」按钮内：单独勾选/取消某个 unit（不改版本）    | `release audit unit add\|remove --process-id <id> --app-id <id> --app-name <psm> --stage <stage> --unit <UNIT>`                     | 版本与集群对象无损精细编辑，底层走 set-apps、只改目标 unit、其余逐字透传、不重新 pin 版本；灰度等 cluster 元数据完整保留。`unit add` 不带 `--clusters` 默认选全部候选 cluster。适合 repoVersion 推迟场景；apply-stage 会重写版本，二者择一。                                                                                   |
| 「编辑」按钮内：单独勾选/取消某个 cluster（不改版本） | `release audit cluster add\|remove --process-id <id> --app-id <id> --app-name <psm> --stage <stage> --unit <UNIT> --clusters <csv>` | 版本与集群对象无损精细编辑，只动目标 unit 的 cluster 集合、不重新 pin 版本；已有和候选 cluster 的完整对象都会回写。`--clusters` 必填；未知 cluster 报错带候选 hint；cluster remove 移到 0 会 warn 该 unit 无法 confirm/submit。                                                                                                |
| 「编辑」按钮内：选集群（机房）                        | 同上，plan 内 `units.<UNIT>.cluster_ids: [...]` 或 `units.<UNIT>.all_clusters: true`                                                | `cluster_ids` 只保留列出的 cluster id（不传则维持现状）；`all_clusters:true` 一键勾选该 unit 候选全集（`cluster_ids` 优先）。                                                                                                                                                                                                  |
| 「移除应用」（把 app 从工单撤下）                     | `release audit remove-app --process-id <id> --space-id <id> --app-id <id> --app-name <psm>`                                         | 平台无物理删除；该命令把 app 在所有非空 stage 的所有 unit `is_deploy` 一键关掉（内部复用 apply-stage）。                                                                                                                                                                                                                       |
| 「编辑」按钮内：选仓库目标版本                        | 同上，plan 内 `repo_versions.<repo>: "<version>" \| "latest" \| {branch?,type?,version?}`，或 plan 顶层 `auto_versions:true`        | 可精确 pin 版本号，也可让 CLI 自动推理：`"latest"`/`{}` = 最新 online+build_ok；`{branch}` = 主仓某分支最新 build_ok；`{type}` = 按类型筛。`auto_versions:true` 兜底未列出的 repo。自动推理跳过 build_failed，显式 pin build_failed 放行带 warning。结果见 `validation.selected_repo_versions` / `version_warnings`。          |
| 查看某阶段某 unit 的候选集群/仓库/版本                | `release audit inspect-unit --process-id <id> --app-id <id> --stage <stage> --unit <UNIT> --repo-limit 30`                          | 读候选。取「最新可用版本」务必拉大 `--repo-limit`，否则漏更新版本。                                                                                                                                                                                                                                                            |
| 生成某阶段的可编辑草稿（候选全集）                    | `release audit build-stage --process-id <id> --app-id <id> --stage <stage>`                                                         | 取 stage 级候选，含各 repo 的 candidates（带 type/status）。                                                                                                                                                                                                                                                                   |
| 物化某阶段计划（预览 materialized payload）           | `release audit materialize-stage ...`                                                                                               | 把 plan 物化成最终 payload，dry-run 预览用。                                                                                                                                                                                                                                                                                   |
| （批量设置阶段 app 列表，逃生口）                     | `release audit set-apps ...`                                                                                                        | 直接覆盖某阶段 app 选择集，少用。                                                                                                                                                                                                                                                                                              |
| **「确认」按钮 / 「全部确认状态」**                   | **`release audit confirm-apps --process-id <id> --confirm true`**                                                                   | **应用确认，强制规则1+2：规则1 = PRE+ONLINE 合计至少一个 `is_deploy=true` unit（只发线上合法）；规则2 = 每个 `is_deploy=true` unit 必须有集群（`clusters` 非空）且 repo 有版本（`version_iterms` 非空）。不过返回 `confirm_blocked_by_stage_validation` + `guard.issues`。`--confirm false` 取消确认（跳过 guard，复位用）。** |

### ② 发布时间确认阶段

| 页面操作           | CLI 命令                                                                   | 说明                                                                                                                                                                                                                                                                                              |
| ------------------ | -------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 查看当前发布时间窗 | `release audit get-window --process-id <id>`                               | 读 pre/gray/online 时间窗。                                                                                                                                                                                                                                                                       |
| 设置发布时间窗     | `release audit set-window --process-id <id> ...`                           | 写 pre/gray/online 发布时间。`--from-platform` 拉平台已有时间窗回写；默认透传平台 `status`（常为 `Init`，只存时间不算确认）。                                                                                                                                                                     |
| **「确认」按钮**   | **`release audit set-window --process-id <id> --from-platform --confirm`** | **与设置时间同一端点**（`/deploy/cd/audit/publish/update`），`--confirm` 强制 payload `status:"Done"` 标记发布时间已确认；可与 `--from-platform` 组合（拉平台时间 + 确认）。`--execute` 成功后会回读 `get-window`，结果挂在 `window_readback`（time/desc 以此为准，update 响应偶发不回显 desc）。 |

### ③ 需求/缺陷确认阶段

> 对应 Meego work item 绑定。接口走 `ci/project_management` 前缀（注意是 `ci` 不是 `cd`）。
> `project_key` / `business_id` 由 CLI 从 process 的 space 自动解析（`get_team_pm_config`），用户无需手填 Meego 内部 id。
> 绑定是**全量覆盖式**：add/remove 内部都先 list 已绑项，在内存合并/剔除后整组提交；需求与缺陷共用同一端点，靠 `work_item_type`（story=1，bug=2）区分。

| 页面操作                            | CLI 命令                                                                                | 说明                                                                                                                  |
| ----------------------------------- | --------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------- |
| 查看已绑定的需求/缺陷               | `release audit list-work-items --process-id <id>`                                       | 读。`project_key`/`business_id` 自动解析。                                                                            |
| 点「添加需求」/「添加缺陷」弹出候选 | `release audit search-work-items --process-id <id> --type story\|bug`                   | 读候选。story=需求（带固定 template_id `[22747,9318]`），bug=缺陷（无 template_id）。                                 |
| 弹窗选中候选后「确定添加」          | `release audit add-work-item --process-id <id> --type story\|bug --work-item-key <key>` | `--work-item-key` 可重复。内部 list 已绑 + 合并目标候选后整组提交；目标从 search 候选解析，template_id 取候选自身值。 |
| 删除某条已绑需求/缺陷               | `release audit remove-work-item --process-id <id> --work-item-key <key>`                | `--work-item-key` 可重复。内部 list 已绑 - 目标后整组提交（删空传空数组）。                                           |

### ④ 审批提交 & 审批结果

| 页面操作                                                             | CLI 命令                                     | 说明                                                                                                                                                                                                                                                                                                                                                                                                                      |
| -------------------------------------------------------------------- | -------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 提交审批                                                             | `release audit submit --process-id <id>`     | 只校验两个前置标志：「应用已确认」（`integrators[].viewed` 全 true，由 confirm-apps 设置）与「窗口已确认」（`audit_publish.status==="Done"`，由 `set-window --confirm` 设置）。任一缺失返回 `submit_requires_confirm_apps` / `submit_requires_window_confirm`，先补对应命令。提交后回查 `audit/process/list` 验证是否进入 PENDING。                                                                                       |
| 撤回审批（撤回已提交的审批，回到可编辑）                             | `release audit withdraw --process-id <id>`   | 与提交同端点（`/deploy/cd/audit/process/update/id`），发 `action:"cancel"`（无 `skipped`）。撤回后该轮 audit_id 不变，可再次 submit。默认 dry-run，须 `--execute --yes-i-know-this-is-live`。                                                                                                                                                                                                                             |
| 强制跳过（红色按钮，**仅 紧急发布（应急）/deploy_type:4 工单可见**） | `release audit force-skip --process-id <id>` | 跳过审批节点强行推进发布。与提交同端点，发 `action:"submit"` + `skipped:true`。先读 `deploy_type`，非 4 拒绝（`LARK_DEVOPS_FORCE_SKIP_NOT_ALLOWED`）并提示改用 submit；仍要求应用+窗口已确认。跳过成功后流程**直接推进到预发阶段**（AUDIT 变 `AuditOnApproved`、`current_phase_index` 前移），不是停在审批节点；execute 后按阶段推进回读判定 `verified`。高风险，默认 dry-run，须 `--execute --yes-i-know-this-is-live`。 |

## 三、BOE 开发流（dev flow，仅 BOE，与生产隔离）

| 页面操作                    | CLI 命令                                                    | 说明                          |
| --------------------------- | ----------------------------------------------------------- | ----------------------------- |
| 加入 app（dev flow）        | `release dev add-app ...`                                   | dev flow 专属，带 preflight。 |
| 更新 app（逃生口）          | `release dev update-app ...`                                |                               |
| 跑 DEV / INTEGRATION 流水线 | `release dev execute-pipeline --phase dev\|integration ...` |                               |
| 集成（DEV→INTEGRATION）     | `release dev integrate ...`                                 |                               |
| 完成 dev flow               | `release dev finish ...`                                    |                               |
| 列 BOE 特性                 | `release dev list-boe-features ...`                         | 读。                          |

---

## 备注

- stage 数字映射：1=DEV、2=INTEGRATION、3=PRE_RELEASE、4=GRAY_RELEASE、5=ONLINE、6=AUDIT。
- 「应用确认」阶段的本质：编辑完 app / stage / unit / 集群 / 版本后，用 `confirm-apps --confirm true` 把该阶段确认锁住。示例流程中 process 12347 可走通：编辑 → confirm-apps execute → 后端返回 integrators + upgrade_policy，页面「全部确认状态」置为已确认。
- **「确认」按钮出现的前置 = 工单顶层 `audit_user_status.integrators` 非空**：该列表**只由 `release audit add-app`（`/deploy/cd/audit/cd/app/add`）种入当前操作者**；`apply-stage` / `set-apps`（走 `app/update`）只配置版本/集群，**不**登记 integrators。预填或克隆进工单的 app 没走过 `app/add` → 顶层 integrators 空 → 按钮不出现、`confirm-apps` 报 not-in-integrators。标准 simple 流程顺序是先 `add-app` 再 `apply-stage`；`apply-release`（exclusive）已内置：工单 integrators 为空时先自动 `app/add` 种入、再配版本（`app/add` 会重置 app 清空版本，故必须先 seed 后配版本），结果里 `seed.performed` / `seed.reason` 透出。
- 「移除某 app」：用 `release audit remove-app`（内部把该 app 在所有 stage 的所有 unit `is_deploy:false`，复用 apply-stage 链路）。平台无物理删除。
