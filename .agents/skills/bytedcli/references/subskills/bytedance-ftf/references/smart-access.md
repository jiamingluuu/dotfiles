# FTF v3 智能接入工作流

## 导航

- [用途](#用途)
- [纯 PSM 输入的最短决策路径](#纯-psm-输入的最短决策路径)
- [SCM 生效前标准预览（强制）](#scm-生效前标准预览强制)
- [正式命令入口](#正式命令入口)
- [安全职责边界](#安全职责边界)
- [标准工作流](#标准工作流)
- [低打扰交互策略](#低打扰交互策略)
- [上传、发布与回滚安全](#上传发布与回滚安全)
- [人工恢复证据包](#人工恢复证据包)

## 用途

本文件定义 FTF v3 SDK Agent 智能接入的 Agent 编排流程。核心边界是：

- 正式入口统一使用 `bytedcli ftf access create`、`access admission execute`、`access artifact create/publish/deploy`、`access compile execute/status`、`access record open/close/status` 与 `access status`。
- `bytedcli ftf psm access --type sdk_agent` 仅保留兼容，不作为新流程推荐入口；确认使用旧版 SDK 接入时统一使用 `bytedcli ftf access legacy create --psm <psm>`。
- 用户只说“帮我给 `<psm>` 接入 FTF”时，默认表示新版 SDK 智能接入；只有明确指定 ByteCopy 才走 ByteCopy。若准入检查返回 `atum_detected=true`，新版流程必须停止，并询问用户是否切换旧版 SDK 接入。
- Skill 在受控的业务工作副本中执行和评测脚本；普通 CLI 与 Manager 只处理安全文件快照、结构化 attempt 和流程状态，不执行 `script_content`。
- 默认低打扰推进。仅在缺少必要输入、需要申请权限、需要确认高风险操作或进入人工恢复时打断用户。

接入完成后的线上 `source_hash_mismatch` 后台闭环与追踪方式见 `online-source-refresh.md`；不要把它与本文件的接入期 Agent 调优流程混用。

## 纯 PSM 输入的最短决策路径

用户只提供 PSM 并要求“接入 FTF 录制/mock”时，严格按以下顺序推进，不先执行通用 `auth status`，也不要求用户补充仓库、工单或 SCM 上下文：

1. 以当前登录用户身份读取实时状态。用户未指定面板时，串行执行 `bytedcli --json --site cn ftf access record status --psm <psm> --region cn` 和 `bytedcli --json --site cn --vregion China-Pay ftf access record status --psm <psm> --region china-pay`；用户明确指定面板时只查询目标面板。`--region` 选择业务面板，请求网关则由 `ftf` 前的全局 `--site/--vregion` 决定，两者必须按以上映射保持一致。CN 查询保持 TeslaX v1 gateway，China-Pay 查询路由到追光 Manager，禁止用 CN Manager 响应代替。每个结果记录 `data.is_register_sdk_agent`、`data.is_register_sdk`、`data.is_register_sdk_prebuild`、`data.is_register_smartq_advanced` 和 `data.record_detail.record_status`，不得用一个面板替代另一个面板。`is_register_sdk_agent` 用于标识新版智能接入来源，核心用户结论仍由 `is_register_sdk` 与 `record_status` 分别表达接入和录制状态。历史工单只能作为参考，不能替代实时状态。
2. 未指定面板时先展示 CN、China-Pay 的分面板证据，再给综合结论；综合状态优先级为录制中/采样录制（`2|4`）→ 熔断（`5`）→ 关闭（`1`）→ 未部署（`3`）→ 未知。任一目标面板已录制时不创建新工单；仅当目标面板的 SDK、prebuild、深度录制标记均有效且 `record_status=1` 时，先按目标面板执行不带 `--yes` 的 `access record open --psm <psm> --region <region>` 预览，其中 CN 使用全局 `--site cn`，China-Pay 使用全局 `--site cn --vregion China-Pay`。预览一致且用户已明确要求开启该面板时追加 `--yes` 写入，不重复询问；否则只询问这一项。后续写操作与回读始终复用同一组全局站点参数和面板参数。`record_status=3` 只表示未部署或无心跳：已有 order id 或 session id 时先执行 `access status`，按 `next action` 恢复已有流程；纯 PSM 没有 selector 时只报告“确认重建接入或恢复部署/心跳”这一项决策，不仅凭状态 3 自动创建。`record_status=5` 或未知状态时停止并报告恢复动作，不盲目 create。
3. 仅在实时接入标记缺失，或用户已明确确认对 `record_status=3` 执行重建时，先执行不带 `--yes` 的 `access create --psm <psm>`，核对自动发现的 PSM、仓库、SCM 和创建人。只透传用户明确提供的运行范围参数；用户未显式指定时不要传 `--canary-name`，不得把接口查询到的小流量机房自动转换为接入限制。结果一致且用户已明确要求执行接入或重建时，直接追加 `--yes` 创建，不重复询问。保存响应中实际存在的 selector；存在 order id 时优先复用，缺少 session id 时使用 `access status --order-id <id>` 获取。若响应不含 order id 或 session id，按不确定写结果停止并报告恢复动作，禁止因此重复 create。
4. 若 readiness 结构化结果明确包含 `sdk_record_mq_permission=need_permission`，自动追加 `--apply-mq-permission` 重试一次，不再要求用户手动申请或单独确认；旧后端没有结构化结果时，仅把精确错误 `sdk record mq permission is required` 作为兼容识别。返回 `permission_submitted` 或有效工单链接时，表示工单创建成功后继续准入，`mq_permission_ready` 仍保持真实权限状态；如需确认权限已生效，可约 20 秒后自动复查一次，但不得因此打断用户。申请失败、其他权限错误、模糊报错或重试后仍为 `need_permission` 时停止，并报告唯一所需动作。
5. 创建成功后按 `access admission execute` → `access artifact create` → `access compile execute/status` → `access artifact publish` 推进。每一步先读取当前状态与 `next action`，已经完成的阶段直接跳过，不回退重做。若 admission 返回 `atum_detected=true`、`atum_evidence.detected=true` 或 `next_action=confirm_legacy_strategy` 且证据指向 Atum，明确说明“Atum 编译暂不支持新版 Agent 接入”，只询问是否切换旧版。用户同意后先执行 `access legacy create --psm <psm>` 预览；确认预览后追加 `--yes`，成功后把 order、access branch、Codebase MR 和 BPM 工单交给用户推进，不再进入 AI draft。若 admission 返回 `FTF_ACCESS_FILE_CONFIRMATION_REQUIRED`，优先读取 `details.files[].summary`：`recovery_action=restore_codebase_read` 时先提示检查 Codebase 权限或分支文件状态；`candidates` 为空且 `oncall_recommended=true` 表示所有已读取文件均不具备可识别的 FTF 改造入口，向用户原样概括阻塞原因并只询问是否发起 FTF oncall，不要求用户重复输入同一配置路径；存在多个候选时才展示候选并请用户确认具体路径。
6. 验证编译必须同时具备 `verification_path=v3_online` 与 `verification_path=legacy_test` 两条成功证据：前者验证 prebuild + AI draft，后者复用同一份 AI draft、换用旧接入编译环境验证开启 prebuild 后普通测试/线下版本仍可编译通过。Manager 会并行发起两条构建，只完成一条时继续等待另一条，不发布 artifact。两条均成功后 Manager 才会把 session 推进到 `awaiting_confirmation`，`next_action` 变为 `publish_artifact`；Agent 以 `access status` 返回的 `stage` 与 `next_action` 判断是否具备发布条件，不自行解释 `changePreview.tracks` 的完整性。随后先预览 `access artifact publish --version <version>`，按“SCM 镜像 → 环境变量 → Pre-Build → v3_online diff/风险 → legacy_test 验证结论”的顺序向用户展示。用户消费并确认后追加 `--yes`。该命令连续完成首次正式发布、SCM FTF 配置及回读、PSM 注册、`is_register_sdk_agent/is_register_sdk/is_register_sdk_prebuild/is_register_smartq_advanced` 持久化和工单完成。结果进入 `registered` 才能描述为“平台侧接入已完成”。同一工单已处于 `awaiting_confirmation` 时可直接确认发布，不重新走编译验证。
7. 注册完成后，按目标面板和对应全局站点参数预览 `access record open --psm <psm> --region <region>`，确认后追加 `--yes`；随后用相同路由执行 `access record status`，分别回读注册状态和录制状态。`is_register_sdk=true` 表示接入已完成，`record_status=3` 表示仍等待业务重新编译、部署或心跳，不得把它改写成接入失败，也不得把已注册描述为正在录制。最后明确提示业务执行新的编译上线。

面向用户的阶段输出固定为三项：当前结论、关键证据、唯一下一步。正常推进不展开脚本迭代、内部状态图、完整 JSON 或重复命令；只有出现阻塞时才补充必要原因和恢复动作。SCM 生效前的高风险确认必须按下方专用模板展开关键证据。

### SCM 生效前标准预览（强制）

首次执行 `access artifact publish` 属于高风险写入。Agent 必须先运行不带 `--yes` 的预览，并将最新响应按以下固定结构呈现给用户；不得只回复“验证已通过”“即将发布”或仅给出命令。预览内容必须来自 CLI 返回的 `changePreview`，不得根据历史 attempt、旧消息或本地文件自行拼接。

1. **当前结论**：展示“可确认/不可确认”、目标版本和缺失证据。
2. **关键证据**：依次展示以下三个子段，不得调换或省略。
   - **SCM 配置变更**：按镜像、环境变量、Pre-Build 顺序展示。镜像使用“当前值 → 目标值”；环境变量只展示 `env_updates` 中发生变化的键和值并保持脱敏；Pre-Build 必须同时展示当前步骤、目标步骤和新增/移除项。
   - **AI Draft 代码变更**：展示 `v3_online` 的受控文件改造前后对比、验证状态和已上报风险。改造后代码由编译验证构建上报，Manager 在预览里按文件回传改造前后内容，CLI 据此渲染成 unified diff；Agent 原样展示 CLI 输出的 diff，不推测、补写或重新解释，也不自行拼接或重排 diff 正文。`legacy_test` 复用同一份 AI draft、不产出独立脚本改动，只展示其验证状态，不展示 diff，也不把同一份 diff 复述成两份证据。
   - **影响与边界**：明确说明即将执行“发布已验证 draft、应用并回读 SCM 配置、注册 PSM、完成接入工单”；同时说明不会自动执行“业务代码合入、业务重新编译、线上部署、开启流量录制”。
3. **唯一下一步**：`confirmation_ready=true` 时给出确认动作；为 `false` 时展示 `missing_evidence` 并停在预览阶段。

确认条件只看验证状态：`v3_online` 与 `legacy_test` 均存在且 `validation_status=verified`。任一轨道缺失或未 verified 时，必须展示 `missing_evidence`，停止在预览阶段，且不得输出或执行带 `--yes` 的发布命令。

#### 受控文件 diff 的呈现约束

改造前后内容由 Manager 在 `changePreview.tracks.v3_online` 下按文件回传，CLI 负责渲染；Agent 只做呈现，不参与解码、比对或改写。

- **`evidence_status` 决定这段证据能不能用**：仅 `rendered` 表示改造前后内容都已读到、`file_changes` 完整；其余任何取值一律按证据不可用处理，原因看 `evidence_reason`，此时不存在可展示的 diff。
- **空 diff 与读不到证据必须分开表述。** CLI 已按文件给出 `state`：`changed`（有改动，`diff` 为 unified diff 正文）、`unchanged`（前后内容一致，确实没改）、`undecodable`（内容不是合法 Base64）、`render_failed`（超出渲染预算）。Agent 照实转述对应结论，**不得把任何一种读取失败说成「该文件没有改动」**——用户正是据此确认发布。新增文件的改造前一侧本就不存在，会渲染成整份内容的新增行，不是读取失败。
- **证据不完整不阻断发布。** 编译验证本身是否成功由 Manager 状态机判定，与能否读到快照无关；CLI 会把不完整的证据记入 `evidence_advisories`，在预览里以「提示」行展示。Agent 照实说明证据缺失原因即可，不得把它描述为用户可修复的输入问题，也不得据此拒绝发布或反复重试。
- **JSON 模式消费 `rendered_diff`。** 该字段只包含产出独立 draft 的轨道（当前仅 `v3_online`）；`legacy_test` 复用同一份 draft，不出现在其中。每个轨道给出 `evidence_status`、`evidence_reason`、`files[]`、`omitted_files`，每个文件带 `file`、`state`、`diff`、`note`、`truncated`。`truncated=true` 表示 diff 过长已截断、`omitted_files` 大于 0 表示受控文件数超出展示上限，两者转述时都要说明。无预览时该字段为 `null`，不会整键消失。原始 Base64 快照不会出现在任何输出里（diff 正文本身即改动处的文件内容）。
- 风险数组为空只能表述为“未发现已上报风险”，不得表述为“无风险”。

**发布前置条件与用户授权是两件独立的事，不可互相替代：**

- **技术前置条件由 Manager 状态机把关，任何情况下都不得跳过或代为判断。** 双路径编译验证均成功后 Manager 才会置 `stage=awaiting_confirmation`、`next_action=publish_artifact`，publish 接口本身也会重新校验编译验证 attempt 与 artifact 的 version、source_hash、manifest_path、script_hash 是否一致。Agent 判断“能不能发布”一律依据 `access status` 的 `stage` 与 `next_action`，不把 `changePreview.tracks` 的字段完整性当作独立判据。
- **用户前置授权只减少交互往返，不降低前置条件。** 用户在本会话中明确表达过“改造和注册自动通过”“需要确认的直接通过”“一路做到底”时，Agent 在 `awaiting_confirmation` 阶段仍按上述结构展示 SCM 变更与 v3_online 受控文件 diff，随后直接执行 `--yes` 并简要通报，不再停下来等待逐项回复。未获此类授权时，展示预览后等待用户明确确认。
- **两种情形下前置条件完全相同。** 编译验证未全部成功、session 未进入 `awaiting_confirmation`、或 `confirmation_ready=false` 时，即使用户已前置授权也不得发布；此时只报告阻塞原因与恢复动作。

标准呈现示例（下列内容即 CLI 文本模式的真实输出形态：`当前结论` 与各轨道均为「项目 / 内容」两列表格，不带 `键：值` 前缀；轨道说明行是表格之后的缩进正文，不是表格里的字段。复述时不要臆造 `说明` 之类不存在的字段名）：

```text
FTF 智能接入生效前确认

当前结论
 项目       内容
 确认状态   可确认
 工单 ID    1234
 会话 ID    sample-session-id
 目标版本   sample-artifact-version
 缺失证据   无

关键证据

SCM 配置变更
 配置项                 当前值       目标值      变化
 镜像                   demo-old     demo-new    更新
 环境变量 FTF_EXAMPLE   接口未返回   <UPDATED>   新增或覆盖
 Pre-Build              [8,23]       [8,17,23]   新增 17

AI Draft 代码变更：v3_online
 项目       内容
 验证状态   verified
 风险       未发现已上报风险
build.sh diff
  --- a/build.sh
  +++ b/build.sh
  @@ -1,2 +1,3 @@
   set -e
  +source ./ftf_nova_build.sh
   make build
script/bootstrap.sh diff
  --- a/script/bootstrap.sh
  +++ b/script/bootstrap.sh
  @@ -1,2 +1,3 @@
   #!/usr/bin/env bash
  +export TCE_STAGE=canary
   exec ./bin/demo-service

编译验证轨道：legacy_test
 项目       内容
 验证状态   verified
 风险       未发现已上报风险
  该轨道复用 v3_online 的 AI draft，仅验证旧接入编译路径，不产生独立改动。

影响与边界
即将执行：发布已验证 draft；应用并回读 SCM 配置；注册 PSM；完成接入工单。
不会自动执行：业务代码合入；业务重新编译；线上部署；开启流量录制。

唯一下一步
等待用户明确确认后，重新执行同一命令并增加 --yes。
```

## 正式命令入口

`--json` 与 `--site` 是全局参数，需要放在 `ftf` 前面。下列 ID-only 示例固定为 cn；zg 使用
`--site cn --vregion China-Pay`。裸 order id 或 session id 未附站点时先索取，不得猜测。普通
access 命令的 order id 与 session id 至少提供一个；同时提供时必须指向同一会话。验证编译命令必须二选一，只传 `--order-id` 或 `--session-id`。

```bash
# 创建：普通用户只需要 PSM；CLI 自动发现仓库、SCM 和原始镜像，分支默认 master。
# 默认只预览；确认请求后增加 --yes。
bytedcli ftf access create \
  --psm example.psm

bytedcli ftf access create \
  --psm example.psm \
  --yes

# Atum 仓库经用户确认后切换旧版 SDK 接入；先预览，再创建 MR 与 BPM 工单。
bytedcli ftf access legacy create --psm example.psm
bytedcli ftf access legacy create --psm example.psm --yes

# 非默认仓库布局必须显式覆盖，并确认预览中的最终路径。
bytedcli ftf access legacy create \
  --psm example.psm \
  --source-branch develop \
  --build-file build/service.sh \
  --boot-file script/start.sh

# 准入检查：先预览受控文件范围，再提交
bytedcli --site cn ftf access admission execute \
  --order-id 10001

bytedcli --site cn ftf access admission execute \
  --order-id 10001 \
  --yes

# 生成：attempt 使用文件输入，CLI 不执行其中的脚本
bytedcli --site cn ftf access artifact create \
  --session-id sample-session \
  --common-attempt-json ./sample-common-attempt.json \
  --previous-attempts-json ./sample-previous-attempts.json \
  --compile-knowledge-file ./sample-compile-knowledge.json \
  --max-iterations 3

# 消费预览中的 compile_knowledge_hash 后，再使用同一份知识文件确认执行。
bytedcli --site cn ftf access artifact create \
  --session-id sample-session \
  --common-attempt-json ./sample-common-attempt.json \
  --previous-attempts-json ./sample-previous-attempts.json \
  --compile-knowledge-file ./sample-compile-knowledge.json \
  --max-iterations 3 \
  --compile-knowledge-hash <preview-sha256> \
  --yes

# 验证编译：先预览真实四文件范围，再触发；默认请求携带受控 file_snapshot
bytedcli --site cn ftf access compile execute \
  --session-id sample-session \
  --artifact-version sample-artifact-version \
  --source-hash sample-source-hash

bytedcli --site cn ftf access compile execute \
  --session-id sample-session \
  --artifact-version sample-artifact-version \
  --source-hash sample-source-hash \
  --yes

# 验证编译状态：默认单次查询；仅按需有限轮询
bytedcli --site cn ftf access compile status --session-id sample-session
bytedcli --json --site cn ftf access compile status \
  --session-id sample-session \
  --wait \
  --poll-interval-ms 3000 \
  --timeout-ms 600000

# 首次正式发布并完成平台侧收尾：先预览确认变更，再增加 --yes 执行
bytedcli --site cn ftf access artifact publish \
  --session-id sample-session \
  --version sample-artifact-version

bytedcli --site cn ftf access artifact publish \
  --session-id sample-session \
  --version sample-artifact-version \
  --yes

# SDK 线上录制开关：以下为 CN；默认预览，确认后增加 --yes
bytedcli --site cn ftf access record open --psm example.psm --region cn
bytedcli --site cn ftf access record open --psm example.psm --region cn --yes
bytedcli --site cn ftf access record close --psm example.psm --region cn
bytedcli --site cn ftf access record close --psm example.psm --region cn --yes

# China-Pay 同时切换网关和业务面板，不能只传 --region china-pay
bytedcli --site cn --vregion China-Pay ftf access record open --psm example.psm --region china-pay

# 单独查询 SDK 接入与线上录制状态；不会查询录制流量
bytedcli --site cn ftf access record status --psm example.psm --region cn
bytedcli --site cn --vregion China-Pay ftf access record status --psm example.psm --region china-pay

# 状态与固定进度图
bytedcli --json --site cn ftf access status --session-id sample-session --with-versions
bytedcli --site cn ftf access status --session-id sample-session --format graph
bytedcli --site cn ftf access status --session-id sample-session --format mermaid

# 回滚：先预览，用户明确确认后增加 --yes
bytedcli --site cn ftf access artifact deploy \
  --session-id sample-session \
  --version sample-verified-version

bytedcli --site cn ftf access artifact deploy \
  --session-id sample-session \
  --version sample-verified-version \
  --yes
```

复杂 JSON 和多行 Markdown 不要内联到命令参数。优先写入受控临时文件，再通过 `--request-json`、`--common-attempt-json` 或 `--previous-attempts-json` 传入；任务结束后删除临时文件或交由临时目录回收。

## 安全职责边界

| 层级          | 可以做                                                                                                                                      | 不可以做                                                                                                                                                                    |
| ------------- | ------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Skill / Agent | 在业务工作副本安全读取四文件；审查、执行通用或 Fornax 专用脚本；采集真实 diff；执行构建和启动评测；生成 attempt 文件                        | 在未审查时执行脚本；把凭证注入脚本；在业务工作副本之外写入；自动执行高风险发布或恢复                                                                                        |
| bytedcli      | 安全读取四文件并生成快照；校验 attempt；触发验证编译；首次发布后编排平台收尾；有限轮询状态；预览并调用 SDK 录制开关；渲染状态、图和回滚预览 | 执行 `script_content`；除 artifact create JSON 中供 Agent 受控执行的 `generation.script_content` 外，输出其他完整脚本、base64 文件内容、`file_snapshot`、用户环境变量或凭证 |
| Manager       | 执行准入、状态机、Fornax 生成、artifact 校验、受门禁保护的发布、SCM 配置回读、PSM 注册和工单完成；从 JWT 审计操作人                         | 在 Manager 主机或普通 CLI 进程中执行业务仓库脚本；发布危险、failed 或 blocked 产物                                                                                          |

任何脚本候选在执行前都视为不可信。发现远程下载并执行、提权、凭证读取或外传、破坏性删除、工作副本外写入、修改宿主机服务、绕过安全检查等行为时，停止执行并记录 `blocked` issue。脚本还必须能在 SCM prebuild 环境独立运行，不得依赖 `apply_patch` 等 Agent/Worker 专用命令；本地存在该命令不能作为 SCM 可用性的证据。不要尝试通过改写命令绕过门禁。

## 标准工作流

### 1. 获取或创建会话

1. 已有 order id 或 session id 时，先用 `access status` 获取当前阶段、阻塞原因和下一步。
2. 没有会话时，使用 `access create --psm <psm>`。CLI 使用当前登录用户，并自动发现仓库、SCM、原始镜像和运行范围；源码分支默认 `master`。只有自动发现失败或用户明确要求覆盖时才补充高级参数。`--cluster` 与 `--canary-name` 都只透传用户显式输入；特别是用户未显式指定时不要传 `--canary-name`，默认机房策略交由 Manager 处理。先检查预览中的 PSM、仓库、SCM 和创建人；请求本身没有新增风险且用户已要求执行接入时，可以继续使用 `--yes`，不重复询问。
3. 不再为新流程生成 `psm access --type sdk_agent` 命令。Atum 强卡点经用户确认后使用 `access legacy create --psm <psm>`；旧命令只用于维护既有自动化。

### 2. 确认代码基线与文件路径

准入、AI draft 和验证编译默认不要求把业务仓库 clone 到本地。CLI 使用当前登录用户的 Codebase 身份，按工单仓库与 `source_branch` 远程遍历目录并读取 raw 文件；分支未指定时使用 `master`。

必须记录以下事实：

- 远程 Codebase 仓库和目标 branch；用户未覆盖时为 `master`。
- build、boot、main、go.mod 四文件的仓库内相对路径。

默认先检查 `build.sh`、`script/bootstrap.sh`、`main.go`、`go.mod`。默认文件不存在或内容明显不承担对应职责时，CLI 会有界遍历仓库目录，查找 build/compile、bootstrap/start、Go main 和 go.mod 候选。只有一个合理候选时自动采用；存在多个合理候选时返回 `FTF_ACCESS_FILE_CONFIRMATION_REQUIRED`，向用户展示候选及判断依据，再使用 `--build-file`、`--boot-file`、`--main-file`、`--go-mod-file` 重试。若配置文件可读但缺少 `go build`、`atum`、`ftf_nova_build.sh` 等当前支持的改造入口，且其它候选也均不适合，保持阻塞是正确行为；面向用户必须说明“找到了哪些文件、为什么不适合”，然后只询问是否发起 FTF oncall。

只有用户明确提供 `--repo-dir`，或需要在调用方控制的本地工作副本采集脚本执行证据时，才走本地读取。此时必须使用独立、可复核的工作副本，不得在含用户改动的目录中自动 reset、clean、stash、覆盖文件或切换分支。

### 3. 安全读取四文件并执行准入检查

四文件是：

| 类型   | 默认来源                                                    | 约束                                               |
| ------ | ----------------------------------------------------------- | -------------------------------------------------- |
| build  | 工单 `build_file`、`--build-file`，否则 `build.sh`          | 远程文件非空、可读且不超限；不适合时扫描候选并确认 |
| boot   | 工单 `boot_file`、`--boot-file`，否则 `script/bootstrap.sh` | 同上                                               |
| main   | 工单 `main_file`、`--main-file`，否则 `main.go`             | 同上                                               |
| go.mod | 工单 `go_mod_file`、`--go-mod-file`，否则 `go.mod`          | 同上                                               |

远程读取时拒绝绝对路径和 `..` 穿越，限制目录深度、文件数量、候选数量和单文件大小。文件内容只在请求内转换为 base64；不写入项目文件，不在日志或报告中展示原文或 base64。本地 `--repo-dir` 模式额外拒绝符号链接逃逸、非普通文件和读取期间发生变化的文件。

先运行不带 `--yes` 的 `access admission execute` 检查选择器、文件范围和权限/警告开关。明确缺少 MQ 权限时自动追加 `--apply-mq-permission`，工单创建成功后继续准入，不要求用户手动申请；仅当 warning 已被业务确认可接受时使用 `--confirm-warnings`。申请失败、warning 业务语义不明确或检查要求高风险动作时暂停；普通通过项和已提交的 MQ 权限工单不打断。

### 4. 执行通用脚本并采集真实证据

通用脚本必须在同一个受控业务工作副本中按以下顺序执行：

1. 记录 branch、HEAD commit、执行前工作区状态和既有 diff 摘要。
2. 使用项目允许的相同命令执行 build/boot 基线评测，记录退出状态和脱敏摘要为 `build_before`、`boot_before`。
3. 对脚本做安全审查。危险或无法可靠判断的脚本不执行，直接形成 `blocked` attempt。
4. 以业务工作副本根目录为 cwd，使用受限超时和最小环境执行脚本；不注入凭证，不提权，不访问工作副本外路径。
5. 记录执行后的工作区状态，并生成相对于执行前快照的真实 diff。`dry_run_diff` 字段保存真实变更摘要，不得用脚本计划、猜测或测试桩替代。
6. 使用与基线一致的命令重新执行 build/boot 评测，记录 `build_after`、`boot_after`。
7. 根据真实 diff、脚本退出状态和前后评测形成 `common_attempt`。

build/boot 评测可能启动进程或访问外部环境时，使用项目已有的安全 smoke 方式和有界超时。若只能通过生产写入、长期驻留进程或新增权限完成评测，将该项记为 blocked/manual recovery，不自行扩大权限。

### 5. 生成 common attempt

attempt 文件只保存结构化证据，不在对话或命令输出中展示真实脚本内容。示例：

```json
{
  "mode": "generic",
  "script_content": "sample-script-content",
  "dry_run_diff": "sample-build.sh: sample-diff-summary",
  "build_before": "sample-build-before: exit=0",
  "build_after": "sample-build-after: exit=1",
  "boot_before": "sample-boot-before: exit=0",
  "boot_after": "sample-boot-after: not-run",
  "evaluation": {
    "status": "failed",
    "summary": "sample-evaluation-summary",
    "issues": [
      {
        "field": "sample-main.go",
        "severity": "error",
        "message": "sample-build-failure",
        "suggestion": "sample-fix-suggestion"
      }
    ]
  }
}
```

状态判定：

| 状态      | 使用条件                                                                  | issues                     |
| --------- | ------------------------------------------------------------------------- | -------------------------- |
| `passed`  | 脚本安全执行，真实 diff 符合目标，必需 build/boot 评测通过                | 可为空                     |
| `failed`  | 脚本已安全执行，但退出、diff、build 或 boot 评测未达到目标                | 至少一条可执行问题         |
| `blocked` | 脚本危险、必要输入/权限缺失、文件不安全，或评测只能依赖未获准的高风险动作 | 至少一条阻塞原因和恢复建议 |

failed/blocked 不能只写笼统摘要。每个 issue 至少包含 `message`，并尽量提供 `field`、`severity` 和 `suggestion`，使 Fornax 能基于真实失败继续生成。

### 6. passed 直通与 Fornax 专用迭代

1. `common_attempt.evaluation.status=passed`：直接调用 `access artifact create`。Manager 应基于 common attempt 创建草稿，不再请求专用脚本。
2. common attempt 为 `failed` 或可恢复的 `blocked`：携带 issues 调用 `access artifact create`，请求 Fornax 专用脚本。
3. 使用 `bytedcli --json ftf access artifact create ... --yes` 读取 `generation.script_content`。该字段是唯一允许返回的完整脚本字段；文本输出和其他 access 命令不展示脚本，其他脚本字段、base64 快照与凭证继续脱敏。
4. Agent 必须先审查专用脚本，再在受控业务工作副本中重复“安全执行 → 真实 diff → build/boot 前后评测”。不要在 CLI 或 Manager 中执行脚本。
5. 每次专用评测形成 `mode=specific` 的 attempt，并按发生顺序追加到 `previous_attempts`。不得改写、排序或删除历史失败 attempt。
6. 某次专用 attempt 为 `passed` 时立即停止迭代并提交最终生成结果。
7. 某次为 `failed` 时，将最新 issues 与全部 previous attempts 交给下一轮 Fornax。
8. 某次为 `blocked` 且无法通过安全的自动恢复动作解除时，停止自动迭代，进入 manual recovery。
9. `previous_attempts` 达到 `max_iterations` 仍未通过时，停止生成，不再请求下一份脚本。状态保持 blocked，并把 order/session、branch、commit、四文件路径、attempt 摘要和 issues 交给 FTF oncall。

previous attempts 文件使用 JSON 数组，示例不包含真实脚本：

```json
[
  {
    "mode": "specific",
    "script_content": "sample-specific-script-content",
    "dry_run_diff": "sample-bootstrap.sh: sample-specific-diff-summary",
    "build_before": "sample-build-before: exit=1",
    "build_after": "sample-build-after: exit=0",
    "boot_before": "sample-boot-before: not-run",
    "boot_after": "sample-boot-after: exit=0",
    "evaluation": {
      "status": "passed",
      "summary": "sample-specific-evaluation-passed",
      "issues": []
    }
  }
]
```

`max_iterations` 使用 Manager 支持的正整数边界。Agent 不通过增大上限掩盖重复失败；同一问题连续出现时应优先停止并进入人工恢复。

### 7. 跟踪状态与进度

- `access status` 用于读取 stage、status、block reason、recovery actions 和 next action；需要版本信息时增加 `--with-versions`。
- `access status` 的文本输出使用中文阶段、处理状态和下一步语义；JSON 同时保留原始枚举和 `stageLabel`、`statusLabel`、`nextActionLabel`，Agent 面向用户时优先使用中文标签。
- `access status --format graph|mermaid` 只渲染 Manager 返回的固定 nodes/edges。文本、Mermaid 和 JSON 必须表达同一组阶段，不临时增加“看起来合理”的节点。
- `access compile execute` 从同一受控业务工作副本读取真实 build、boot、main、go.mod 快照。四文件 override 规则与 `access admission execute` / `access artifact create` 一致；预览确认后增加 `--yes`，不要通过 JSON 手工注入 `file_snapshot`。
- `access compile status` 默认只查询一次。自动化需要等待时增加 `--wait`；轮询仅在 `compile_status=pending|running` 或 `auto_retrying=true` 时继续，其他状态立即停止。`--poll-interval-ms` 范围为 1000～60000，默认 3000；`--timeout-ms` 范围为 1000～1800000，默认 600000。
- 验证编译失败时，不能把 SCM commit 描述当作真实错误。历史 attempt 未返回或返回空白 `verification_path` 时按 `v3_online` 兼容解释。若 current attempt 同时提供 `scm_repo_id` 与 `scm_version`，继续执行 `bytedcli scm repo build-log --repo-id <scm_repo_id> <scm_version> --status failed`；历史响应缺少 `scm_repo_id` 时，只允许从可信 `compile_url` 的 `/scm/detail/<id>/` 路径提取一次，不猜仓库。FTF 返回的 `build_id` 是 SCM version id，不得直接作为 ByteBuild `--record-id` 使用。
- SCM 下钻时先获取真实失败 step、exit code 和最小脱敏错误摘要，不向用户展示完整 `detail`、`user_envs`、`scm_envs` 或整段日志。出现 v3 script、patch、hash、注入命令缺失等证据时归为脚本补丁问题；业务 Go 编译错误归为业务基线；权限错误归为权限；无明确证据才保留基础设施分类。下钻只用于诊断，不改变 Manager 的 `next_action`，不自动重试或切换 builder。匹配《FTF 编译问题汇总》后，将命中项整理为 `signature/category/cause/remediation/source` JSON 数组，通过 `--compile-knowledge-file` 传给下一轮 artifact create；只传已确认知识，不附完整日志，不把未知原因补写成确定结论。
- 对 hash mismatch、权限、基础设施等平台策略之外的编译问题，参考 [FTF 编译问题汇总](https://bytedance.larkoffice.com/wiki/VRm1wE6kIiytzKkTyOUcggQQnQh) 查找同类错误。命中已知问题后，把“错误、原因、对策”整理为结构化条目写入当前 attempt 的 `evaluation.issues`，与真实 SCM 失败证据、历史 attempts 和四文件快照一起作为下一轮 AI draft 的输入；未命中时也要把已确认的真实错误和可执行建议写入 issues，不用猜测补足原因。最终 AI draft 只允许修改 build 和 bootstrap；main.go、go.mod 与其它业务源码只能作为分析输入，不得写入改造结果。
- Manager 会并行发起 `verification_path=v3_online` 与 `verification_path=legacy_test` 两条构建，两者复用同一份 AI draft（相同 artifact version、source hash、manifest 路径与 script hash），legacy_test 不额外生成脚本。第二条构建不携带 `CUSTOM_FTF_SMART_ACCESS_V3_VERIFY` 及 manifest/artifact/hash 等验证变量，只保留未来真实 SCM 配置，确保命中普通 test/offline 的旧接入路径；任一路径失败都保持对应 attempt 和恢复动作，legacy_test 失败不触发重新生成 draft。
- 两条验证均通过后执行 `access artifact publish`，不得使用 `artifact deploy` 代替首次发布。首次发布成功后继续完成 SCM 配置、PSM 注册和工单收尾；中途失败时先重新执行不带 `--yes` 的 publish 预览，消费最新 SCM 状态后再确认恢复，由 current 指针和后端回读幂等续跑，不改选其它版本。
- `access record open|close` 只要求 `--psm example.psm`；`--env`、`--region` 可选，未显式传入时由 Manager 使用 `prod/cn`。显式选择面板时必须同步选择请求网关：CN 使用全局 `--site cn` 配合 `--region cn`，China-Pay 使用全局 `--site cn --vregion China-Pay` 配合 `--region china-pay`，不得只改业务 `--region`。命令默认预览并要求 `--yes`，预览必须明确只修改 `is_open_record`，保留采样策略且不创建、关闭或切换 ByteCopy。操作人由 JWT 解析，不提供 `--trigger-user`。
- `access record status --psm example.psm` 查询 SDK Agent、SDK、prebuild、ByteCopy、普通/深度录制接入标记及线上录制状态。`is_register_sdk_agent` 是接入来源的规范性标记；核心用户结论仍优先展示 `is_register_sdk` 和 `record_status`。它不查询 recorded flow；用户说“有没有录制流量”时仍使用 `ftf flow ...`。
- 文本输出先看 compile status、last error category、recovery action 和 next action，再看 attempt 表与 current attempt 详情。JSON 保留后端扩展字段和完整 attempt 证据，但删除所有 `file_snapshot` 与 `failure_evidence.user_envs`，并继续脱敏脚本、base64、凭证和 URL userinfo；唯一例外是 artifact create 成功结果中的 `generation.script_content`，用于 Agent 审查和受控执行。
- 正常推进时不向用户逐轮展开脚本调优细节，只报告关键阶段变化。只有需要用户动作时才展示阻塞原因、影响和建议动作。

## 低打扰交互策略

| 场景                                                                                         | 是否打断用户 | 处理                                                                                       |
| -------------------------------------------------------------------------------------------- | ------------ | ------------------------------------------------------------------------------------------ |
| 已有完整 selector、工作副本、branch/commit 和四文件                                          | 否           | 自动完成只读检查、脚本评测和状态查询                                                       |
| 缺少目标 branch/commit、关键文件路径或必要业务参数                                           | 是           | 只询问缺失且无法安全推断的输入                                                             |
| 需要申请权限或确认 warning 的业务语义                                                        | 是           | 展示具体检查项、影响和拟执行动作                                                           |
| 普通 draft 生成与静态验证通过后的 immutable 自动上传                                         | 否           | 由一次 `artifact create --yes` 连续完成，不等同正式发布                                    |
| 首次 `artifact publish`、显式 `--upload-to-tos`、历史版本 `artifact deploy` 或其它高风险写入 | 是           | 先展示预览，获得明确确认后执行；用户已前置授权自动推进时仍展示变更，随后直接执行并简要通报 |
| 危险脚本、不可恢复 blocked、达到 max iterations                                              | 是           | 停止自动化，提供 manual recovery 和 FTF oncall 证据包                                      |

## 上传、发布与回滚安全

- 静态验证通过的 draft 由 Manager 自动上传 immutable manifest/script，并在回读校验成功后返回 `compile_ready=true`；上传失败不得写入可编译状态。
- dangerous script、`evaluation.status=failed`、`evaluation.status=blocked` 时不得进入 compile-ready，更不能发布。
- 不把“生成了脚本候选”描述为“业务改造完成”；只有真实执行、真实 diff 和评测通过后才能标记 passed。
- 首次发布必须使用 `access artifact publish`。它只接受等待首次发布的 compile-verified draft；成功后必须同时确认 current 指针、SCM 配置回读、`is_register_sdk_agent` 及关联 SDK 状态、工单完成和 `registered` 阶段。
- 历史版本回滚通过 `access artifact deploy` 执行，只允许显式选择历史 `verified` artifact version。目标不存在、blocked、failed 或验证状态不明确时拒绝。
- `artifact deploy` 未传 `--yes` 时只展示 current、目标版本和影响；用户明确确认后才能重新发布。目标已经是 current 时按幂等结果返回，不重复发布。
- 发布后必须读回 current version；读回与目标不一致时报告不确定写结果，不能宣称成功。
- Phase 5 的 `artifact deploy` 仅重新发布历史已验证 artifact，不关闭 prebuild。关闭 prebuild 延后到 Phase 6，不在本工作流中通过其它命令替代。

## 人工恢复证据包

进入 manual recovery 或转交 FTF oncall 时，提供最小脱敏证据：

- order id、session id、PSM。
- 业务工作副本标识、目标 branch、基线 commit 和当前 HEAD commit。
- 四文件的仓库内相对路径和大小，不包含文件原文或 base64。
- common attempt 与 previous attempts 的顺序、状态、diff 摘要、build/boot 结果摘要和 issues。
- 当前 stage/status、block reason、recovery actions、next action。
- 验证编译的 compile status、current attempt、attempt 顺序、last error category、recovery message、next action 和脱敏 compile URL；不包含 `file_snapshot` 或 `failure_evidence.user_envs`。
- 是否曾请求上传或回滚，以及最终 current version 读回结果。

不得附带真实脚本全文、仓库凭证、Cookie、JWT、环境变量值或其它敏感信息。
