---
name: aiden-d2c-skills
description: 使用 Aiden D2C 视觉切分命令把 Figma 设计稿转换为生产级 browser / Lynx 代码，负责拉取切分产物、组装最终页面代码，并按用户指定目录输出 figma2code.tsx 与 figma2code.css。
allowed-tools: Bash, Read, Write, Edit, Grep
---

# aiden-d2c-skills

Use this skill when you need to turn a Figma design into production-oriented browser (H5 / desktop web) or Lynx code with the Aiden D2C workflow.

You are an **Aiden Figma-to-Code Expert**. Use the `d2c-visual-segmentation` capability's commands to fetch segmentation artifacts, inspect the generated regions, and assemble the final page code under the user-provided output directory.

## D2C 切分命令

通过 `bytedcli d2c` 命令调用 D2C 视觉切分服务，不再走 MCP 工具。

| 命令 | Purpose |
|:-----|:--------|
| `bytedcli d2c segment create` | 发起 D2C 切分任务。入参（CLI flag）：`--figma-url` / `--transform-type` / `--figma-token`(或 `--figma-auth-token`) / `--repo-name` / `--creator` / `--config`。返回 `{ taskId }`；带 `--wait --output-dir` 时直接落盘产物。 |
| `bytedcli d2c task get --kind visual-segmentation` | 用 `--task-id` 查询任务状态。返回 `{ taskId, status }`；`status === 'completed'` 时会带 `downloadUrl`。 |

详细参数见该 capability 的 `references/scripts.md`。

## Figma token 解析（bytedcli 行为）

不需要、也不要创建任何 `settings.json`。`bytedcli d2c segment create` 在内部按以下优先级解析 Figma token：

1. 显式 flag：`--figma-token` 或 `--figma-auth-token`
2. 环境变量：`FIGMA_ACCESS_TOKEN` / `FIGMA_PAT` / `FIGMA_TOKEN` / `FIGMA_AUTH_TOKEN`
3. 后端按 `--creator` 查询该用户已登记的 token

token **只在内存中使用**——不写入磁盘、不打日志、不出现在命令输出里。

强制规则：

1. 不要把 token 写进任何配置文件或产物；本链路没有配置落盘这一步，也没有「写入失败即终止」的前置条件。
2. 不要在聊天回复、普通日志或报错中打印明文 token；如需展示配置，只能脱敏。
3. `repo_name`、`transformType`、`creator` 必须由调用方从上下文显式提供，命令不做 git 推断。

## Artifact Persistence

整体流程：**发起任务 → 轮询状态 → 拿到 downloadUrl → 下载 tar.gz → 解压**。

**轮询**：1 分钟一次；总时限至少 20 分钟。`failed` / `cancelled` 立即终止并透传错误；`completed` 后读取 `downloadUrl`。

**落盘四步**：

1. 取 `<prefix>` = `figmaUrl` 后六位 + `-` + `node-id`（从 figmaUrl 的 `node-id` query 解析，把 `:` / `%3A` 等非字母数字字符统一规整为 `-`）。这样同一设计稿不同 node 的产物目录不会互相覆盖/误删。
2. 用 `curl -L` 或等价方式下载 `downloadUrl`，无需额外 cookie / 鉴权头。
3. 把压缩包落盘到 `.aiden_d2c/<prefix>.tar.gz`。
4. 解压到 `.aiden_d2c/<prefix>/`，再定位其中的 `figma2code/` 目录，下文记为 `<figma2codeDir>`。

## Execution Workflow

Follow this order exactly for D2C runs:

`visual-segmentation -> interaction-recognition -> target global-assembly -> deterministic validation -> build/capture -> unified evaluation -> refine loop`

Do not skip `interaction-recognition` because no inventory file exists yet. The entry workflow owns this ordering and must create the interaction inventory before target assembly.

### Step 1: Context Analysis

调任何工具前先：
1. 识别 `transformType`（`lynx` / `h5` / `web`；`h5` 与 `web` 都走 browser 链路）和 `packageName`（可选）。
2. 明确 `<userOutputDir>`。如果用户没给，就先暂停并向用户索取，不要默认写到 `.aiden_d2c/` 内。
3. 取 `<prefix>` = `figmaUrl` 后六位 + `-` + `node-id`（从 figmaUrl 的 `node-id` query 解析，`:` / `%3A` 等非字母数字字符统一规整为 `-`），并先清理上次可能残留的 `.aiden_d2c/<prefix>/` 与 `.aiden_d2c/<prefix>.tar.gz`，确保从干净状态开始，避免上次任务产物干扰本次。同一设计稿不同 node-id 因此互不影响。（只清理本 `<prefix>` 对应的产物，不要动 `d2c_context/` 目录等业务上下文文件。）
4. 加载业务定制上下文（运行时）：递归读取 `<projectRoot>/d2c_context/` 下的文件，并据此组装本次请求的完整 segmentation config。当前合同字段 `target.unit` 映射为 `config.unit`；目录不存在时使用平台默认值（Lynx=`rpx`、browser=`px`），合同存在但该字段缺失或非法时停止。保留 config 中的其他字段，具体映射与校验见 `d2c-visual-segmentation/references/scripts.md`。
5. 按上方 **Figma token 解析** 确认 token 来源（显式 flag / 环境变量 / 后端按 `creator` 查询）；不需要落盘任何配置文件。

### Step 2: Fetch via Scripts

1. 调 `bytedcli --json d2c segment create`，用 CLI flag 传入 `--figma-url`、`--transform-type`、`--figma-token`(或 `--figma-auth-token`)、`--repo-name`、`--creator` 和完整的 `--config '<segmentationConfigJson>'`（这些值都从上下文显式提供，命令不做 git 推断）。
2. 加 `--wait --output-dir` 轮询直到 `completed`，或用 `bytedcli --json d2c task get --task-id <taskId> --kind visual-segmentation` 自行查询。
3. 从返回拿到 `downloadUrl`，用 `curl -L` 下载、解压，并定位 `<figma2codeDir>`。
4. 优先读取 `<figma2codeDir>/regions-visual/region-artifacts.json` 验证产物完整，并确认 `<figma2codeDir>/run-artifacts/figma-facts.json` 与 `section-contracts.json` 存在。

任一接口 HTTP 非 2xx 时响应是 JSON `{ error, ... }`，直接把 `error` 透传给用户并终止。

### Step 3: Read Manifest

以 `region-artifacts.json` 为权威输入。

强制要求：
- 任何 region `status !== 'success'` 都终止，并提示用户重跑切分任务。
- 只读取必要的 region 文件，避免批量打开所有产物。

### Step 4: Recognize Interaction & Component Inventories

在组装前必须运行 `interaction-recognition` 产出交互清单；组件清单已由视觉切分上游产出。两份页面级清单：

- `<figma2codeDir>/run-artifacts/interaction-inventory.json`（行为轴：页面有什么交互，本 skill 产）
- `<figma2codeDir>/run-artifacts/component-inventory.json`（形态轴：每个 region 归属的**目标无关组件类型**，由视觉切分上游产出，随切分产物解压即得——不由本 skill 生产）

执行顺序：
1. 调用 `interaction-recognition`，用整页截图、skeleton、region manifest、region crops 和 region Figma JSON 生成 interaction-inventory.json。component-inventory.json 已随切分产物在 run-artifacts 下，无需在此生成。
2. 如果识别失败或证据不可读，由 `interaction-recognition` 写入空清单文件，并在最终报告记录失败原因；缺失清单时下游行为退化为现状，不阻塞。
3. 后续 target skill 必须读取两份文件。不要把缺失 inventory 当作静态页面的理由。

interaction-inventory 的识别规则、schema、置信度含义以 `interaction-recognition` skill 为准；component-inventory 由视觉切分上游产出（目标无关组件类型），其消费与「类型→库组件」映射以目标 skill 的 `references/component-inventory-consumption.md` 为准。这里不要重复维护识别策略。

### Step 5: Invoke Target Skill

- `transformType=lynx`：继续使用 `lynx-design-to-code`, 选择 `global-assembly` mode
- `transformType=h5` 或 `transformType=web`：都继续使用 `browser-design-to-code`, 选择 `global-assembly` mode（`h5` = 移动端网页，`web` = 桌面端网页，共用同一套 browser 生成链路）
- 调用目标 skill 时传入或明确读取 `<figma2codeDir>/run-artifacts/interaction-inventory.json` 与 `<figma2codeDir>/run-artifacts/component-inventory.json`。
- **组件选型策略路由（三选一，强制）**：组件类型来自 component-inventory（视觉切分产），但「类型→具体库组件」用哪条策略解析，按 `browser-design-to-code/references/component-selection-routing.md` 路由，首个命中生效：
  1. **业务自建组件识别接入**——若 Step 1 加载的 `d2c_context/` 声明了业务自建识别能力，按其说明调用并消费其映射结果（接口未标准化，是文档化 hook；调不通/无可用结果则下沉到 2 并在 composition plan 记录）。
  2. **DeepWiki 动态查**（browser 业务库默认）——`packageName`/业务上下文给了库、且无自建识别时，Decide 阶段**运行时从 DeepWiki 查**具体库组件与用法（`references/component-inventory-consumption.md` 定协议：按类型语义查、蒸馏成 import+props+JSX 记入 composition plan、allowlist 刹车）。skill 侧不写死任何路由表/用法卡，换库/新组件零改动。
  3. **lynx-ui 固定映射 + componentSelection 门控**（Lynx 单库）——无业务库诉求的 Lynx 走 `lynx-design-to-code` 的 interaction→lynx-ui 固定映射 + 确定性门控，不需 DeepWiki；若 Lynx 也点名了 lynx-ui 以外的包，则对这些组件复用第 2 条动态路径。
- 组件选型不替代 interaction inventory 的行为约束（选型层定用哪个组件、行为层定组件怎么表现，两层都要满足；无论走哪条策略，行为层契约都不被削弱）。
- 切分产物后的整页生成不得使用 `full-page-generation`。该模式只用于没有 region pipeline 的 one-shot 生成。

### Step 6: Composition Plan

基于整页截图、region crop、RFC 和 region tree，生成 `<figma2codeDir>/composition-plan.json`。

### Step 7: Generate Final Code

输出到：
- `<userOutputDir>/figma2code.tsx`
- `<userOutputDir>/figma2code.css`
- `<figma2codeDir>/composition-plan.json`
- `<figma2codeDir>/figma2code.json`

强制要求：
- 样式 / 尺寸 / 布局的单位以 `d2c_context/d2c.contract.json` 的 `target.unit` 为最高优先级：`px` 必须读取 `origin.json` 的原始 px 值，即使存在 `origin.rpx.json`；`rpx` 才优先读取 `origin.rpx.json`。Contract 未指定时，lynx 保持 rpx、browser 保持 px 的平台默认。
- 单位严格按 `rootInfo.unitConversion`
- 不要保留对 region tsx/css 的相对 import
- 最终产物需可独立编译
- composition plan 必须记录由 `interaction-inventory.json` 驱动的组件选择，以及不能满足的目标端限制。
- 如果 visible evidence 或 interaction inventory 指向 tabs/paged/list/input/action/overlay 结构，必须用真实可见的目标组件或目标原生交互结构满足；不要用静态 `view/text` 外观替代。
- **组件消费以 `component-inventory.json` 为准绳**（目标无关类型→库组件映射见目标 skill `references/component-inventory-consumption.md`）：high 置信类型必须映射到真实库组件（或缺件替代）落地并在 composition plan 引用对应条目；**allowlist 刹车**——某库组件对应的类型没被任何 region 归属，import 前必须在 composition plan 写明截图证据，严禁把 `Image`/`List` 当默认容器无差别外推（R4 实证的 precision 崩盘主因）。
- 不要添加隐藏、透明、不可达、视觉无关的组件或文字来满足 deterministic validation。

### Step 8: Deterministic Validation and Self-Check

- 检查 import 集、wrapper 定位、单位、composition plan、最终视觉顺序是否合理。
- `transformType=lynx` 时，运行 `bytedcli --json d2c lynx-page validate --figma2code-dir "<figma2codeDir>" --project-root "<projectRoot>"`。validator 必须从 `<projectRoot>/d2c_context/d2c.contract.json` 读取目标单位：`px` 合同允许 Lynx CSS 使用 `px`，`rpx` 合同才禁止 raw `px`。如果 `passed=false`（即存在 `workflowBlocking=true` 的 issue），直接读 `<figma2codeDir>/validation-report.json`——修复所需信息都在其中（每条 issue 带 `workflowBlocking` / `repairable` / `category`，报告顶层还有 `repairTargets` 与 `guidance`），不需要另外生成 repair context 文件；只修复 `workflowBlocking && repairable` 的 issue 后重跑 validator。
- 对 `workflowBlocking && repairable` 的 issue，最多重试 2 次；组件类问题（high-confidence 组件选择不匹配、render-blocking 组件用法）优先修复。2 次后仍存在任一 `workflowBlocking=true` 的 issue 时，停止后续 build/capture/evaluation/refine，并报告残留 blocking issue（组件门控不再持久化到 report，需要时按 `category=component && workflowBlocking=true` 从 issues 现算，判断一律以 `workflowBlocking` 为准）。
- `workflowBlocking=false` 的 issue（如 low-confidence 组件选择不匹配、quality 级组件用法问题、视觉分/覆盖度提示）不阻塞后续 build/capture/evaluation/refine；保留 `<figma2codeDir>/validation-report.json`，并在最终回复中列出残留 issue code。
- 如果出现 `category=infrastructure && repairable=false` 的 issue（如 validator/远端服务自身失败），停止当前流程并交给外层重试，不要让代码 repair 去改 TSX/CSS。
- 如果 validation 报告显示 interaction inventory missing/invalid/empty 或 component-selection skipped，不要把 `passed=true` 表述为组件选择正确；只说明 deterministic validation 没有 render-blocking issue。
- 最后把最终产物回填到 `<figma2codeDir>/figma2code.json`。

## Post-Generation Evaluation and Refine

Step 8 是 workflow gate 与 best-effort 自检的边界：只要存在 `workflowBlocking=true` 的 issue 就必须先处理，不能进入后续链路。其中 `repairable=true` 的 blocking issue（含组件选择/用法、artifact、syntax）按上面的 2 次限制修复，仍失败则停止后续链路；`repairable=false` 的 blocking issue（`category=infrastructure`，如远端服务/ validator 自身失败）直接停止并交给外层重试，不做代码 repair。只有当没有 `workflowBlocking=true` 的 issue 时才继续；`workflowBlocking=false` 的 issue 不阻塞。自检完成后，按 `transformType` 分别走对应的 build/capture 链路，再进入统一的 `d2c-evaluation-workflow`。
统一使用 `<figma2codeDir>/input_image.png` 作为后续 evaluation/refine 视觉参考：

- Lynx 渲染截图交给 `lynx-build-and-capture`；命令会按显式参数或参考图确定 capture 尺寸，并默认请求 UI Tree。只有 `lynx-ui-tree-status.json` 的 `usable=true` 才能声称抓树成功。
- H5/web 调用 `d2c-evaluation-workflow` 时只做图片评测：`--reference-image` + `--candidate-image` + `--output-dir`。geometry 为 `not-applicable` 是正常状态（Lynx 专属，H5 根本不跑）。
- Lynx 调用 `d2c-evaluation-workflow` 时，先用 `--reference-image` + `--capture-output-dir` + `--output-dir` 跑图片评测，再用 `d2c geometry evaluate --figma-json <figma2codeDir>/origin.json --runtime-tree <captureOutputDir>/lynx-ui-tree.json` 跑几何评测。UI Tree 不可用时几何记为 `insufficient-evidence`，但不影响图片 diff。
- 调用 `d2c-refine-workflow` 时，把 `evaluation-result.json` 传为 `sourceEvidencePaths.evaluationResultPath`，Lynx 再补 `geometry/geometry-report.json` 作为 `geometryReportPath`。

不要使用 `screenshot.raw.png` 作为视觉参考。

### Lynx (`transformType=lynx`)

```
Skill(skill_name="lynx-build-and-capture")       // screenshot + raw/normalized UI Tree + status
Skill(skill_name="d2c-evaluation-workflow")      // pixel diff + 条件 UI-tree geometry + geometry-report.json
Skill(skill_name="d2c-refine-workflow")          // 消费 evaluation-result + geometry-report
```

### Browser (`transformType=h5` 或 `transformType=web`)

```
Skill(skill_name="d2c-render-screenshot")     // 云端 build + 无头浏览器渲染，产出 .aiden_d2c/shot/screenshot.png
Skill(skill_name="d2c-evaluation-workflow")    // align + diff + 打分
Skill(skill_name="d2c-refine-workflow")        // 基于评测报告精修 figma2code.tsx / figma2code.css
```

evaluation 未发现可修复差异时跳过 refine。否则进入有界循环：

1. 每轮都以当前代码依次执行 Step 8 validation、build/capture、evaluation。Lynx 在图片评测后按 UI Tree 可用性追加 geometry 评测；H5 的 geometry 正常为 `not-applicable`。
2. 第 2 轮起把上一轮 `geometry/geometry-report.json` 传给 `d2c geometry evaluate --previous-report`，以固定 Figma ID + runtime path 的配对趋势判断改善。
3. 调用 `d2c-refine-workflow` 的 preflight guard。`decision=continue` 时完成本轮精修后必须回到步骤 1 重新截图和评测；不得在只写完代码、尚未复评时结束。
4. `decision=stop`、图片 evaluation 已无可修复差异、达到 guard 上限或连续停滞时才结束循环。geometry 为 `insufficient-evidence` 时只按图片证据 refine；`not-applicable` 是 H5 正常状态。
5. 每轮报告原始参考图、该轮 rendered/diff、pixel score、geometry evidence status，以及 stable-pair trend。若 pixel 与可信 stable-pair geometry 指标方向冲突，标为 mixed，不能宣称整体修复成功。

refine 完成且循环终止后再继续 Step 9 Cleanup。两种目标都走同一个 `d2c-evaluation-workflow` capability；Lynx 的几何评测是其中的附加一步，不是独立 SKILL。

### Step 9: Cleanup

确认 `<userOutputDir>/figma2code.tsx` 与 `figma2code.css` 已正确产出后，清理本次的本地切分产物，避免影响下次任务：

- 删除解压目录 `.aiden_d2c/<prefix>/` 与压缩包 `.aiden_d2c/<prefix>.tar.gz`。
- 仅删除本次 `<prefix>` 对应的产物，不要误删 `.aiden_d2c/` 下其他任务的目录。
- 如最终产物校验失败或用户要求保留以便排查，则跳过清理并在报告中说明残留路径。

## Failure Modes

| 故障 | 处置 |
|:-----|:-----|
| `d2c segment create` 报错 | 透传 error 给用户；终止 |
| 状态查询返回 `failed` / `cancelled` | 透传错误；终止 |
| 状态轮询超时 | 终止；提示用户重试 |
| `downloadUrl` 下载失败 / 包损坏 | 终止；提示用户重跑切分任务 |
| `region-artifacts.json` 缺失 | 终止；提示产物不完整 |
| 任意 region 非 success | 终止；提示重跑切分任务 |
| 目标 skill 缺失 | 使用保守 fallback，并在最终报告里明确说明 |
