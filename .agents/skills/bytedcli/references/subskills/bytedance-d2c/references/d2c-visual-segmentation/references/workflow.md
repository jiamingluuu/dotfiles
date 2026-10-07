# 完整工作流：从 Figma 到 figma2code 整页代码

本文档描述拿到切分产物后如何组装整页 browser / Lynx 代码。命令只负责「发起任务 → 拿状态 → 拿 downloadUrl」，下载、解压、组装由本工作流完成（`d2c segment create --wait --output-dir` 可以把下载与解压一并做掉）。

## Step 1: 上下文分析

调任何命令前：

1. 识别 `transformType`（`lynx` / `h5` / `web`；`h5` 与 `web` 都走 browser 链路）和 `packageName`（可选）。
2. 明确 `<userOutputDir>`。如果用户没给，先暂停向用户索取，不要默认写到 `.aiden_d2c/` 内。
3. 取 `figmaUrl` 后六位作为 `<prefix>`，并先清理上次可能残留的 `.aiden_d2c/<prefix>/` 与 `.aiden_d2c/<prefix>.tar.gz`，确保从干净状态开始。
4. 递归读取 `<projectRoot>/d2c_context/`，组装完整的 segmentation config；当前将合同 `target.unit` 映射到 `config.unit`，并保留其他配置字段。目录不存在时按目标平台补默认 `unit`。
5. 确认 Figma token 的来源（显式 flag / 环境变量 / 后端按 `creator` 查询），不需要落盘任何配置文件。

### Figma token 解析（bytedcli 行为）

不需要、也不要创建任何 `settings.json`。`bytedcli d2c segment create` 在内部按以下优先级解析 Figma token：

1. 显式 flag：`--figma-token` 或 `--figma-auth-token`
2. 环境变量：`FIGMA_ACCESS_TOKEN` / `FIGMA_PAT` / `FIGMA_TOKEN` / `FIGMA_AUTH_TOKEN`
3. 后端按 `--creator` 查询该用户已登记的 token

token **只在内存中使用**——不写入磁盘、不打日志、不出现在命令输出里。

规则：

- 不要把 token 写进任何配置文件或产物；本链路没有 `settings.json`，也没有「写入失败即终止」这一步。
- `repo_name`、`transformType`、`creator` 必须由调用方从上下文显式提供，命令不做 git 推断。
- 不要在聊天回复或普通日志中打印明文 token，展示时必须脱敏。

## Step 2: 发起 + 轮询

1. `bytedcli --json d2c segment create --config '<segmentationConfigJson>' ...` 发起任务，拿到 `taskId`。
2. 加 `--wait`（`--poll-interval-ms 60000 --timeout-ms 1200000`，总时限至少 20 分钟）轮询直到 `completed`；或用 `bytedcli --json d2c task get --task-id <taskId> --kind visual-segmentation` 自行查询。
3. `failed` / `cancelled` 立即终止并透传 message；接口失败时透传 `error`。

## Step 3: 下载并解压

`completed` 返回里取 `downloadUrl`，下载无需 cookie / 鉴权头：

```bash
mkdir -p .aiden_d2c/<prefix>
curl -L "<downloadUrl>" -o .aiden_d2c/<prefix>.tar.gz
tar -xzf .aiden_d2c/<prefix>.tar.gz -C .aiden_d2c/<prefix> --strip-components 1
```

定位 `figma2code/` 目录（记为 `<figma2codeDir>`）。

## Step 4: 读取产物清单

以 `<figma2codeDir>/regions-visual/region-artifacts.json` 为权威输入：

- 任何 region `status !== 'success'` 都终止，并提示用户重跑切分任务。
- 只读取必要的 region 文件，避免批量打开所有产物。

## Step 5: 运行 interaction-recognition

组装前必须运行 `interaction-recognition`，生成页面级 interaction inventory：

`<figma2codeDir>/run-artifacts/interaction-inventory.json`

执行顺序：
1. 调用 `interaction-recognition`，用整页截图、skeleton、region manifest、region crops 和 region Figma JSON 生成该文件。
2. 如果识别失败或证据不可读，由 `interaction-recognition` 写入空清单文件，并在最终报告记录失败原因。
3. 后续 target skill 必须读取该文件。不要把缺失 inventory 当作静态页面的理由。

识别规则、schema、置信度含义和目标端映射都以 `interaction-recognition` skill 为准。后续 target skill 只消费该清单，不在本 workflow 中重复维护识别策略。

## Step 6: 选择目标 skill

- `transformType=lynx`：继续使用 `lynx-design-to-code`，选择 `global-assembly` mode
- `transformType=h5` 或 `transformType=web`：都继续使用 `browser-design-to-code`，选择 `global-assembly` mode
- `packageName` 非空：按需补充业务组件知识
- 切分产物后的整页生成不得使用 `full-page-generation`。该模式只用于没有 region pipeline 的 one-shot 生成。

## Step 7: 组装计划与生成代码

基于整页截图、region crop、RFC 和 region tree，生成 `<figma2codeDir>/composition-plan.json`，然后输出：

- `<userOutputDir>/figma2code.tsx`
- `<userOutputDir>/figma2code.css`
- `<figma2codeDir>/composition-plan.json`
- `<figma2codeDir>/figma2code.json`

强制要求：

- 样式 / 尺寸 / 布局遵循 `d2c_context/d2c.contract.json` 的 `target.unit`：`px` 读取 `origin.json` 原始 px 值，`rpx` 才优先 `origin.rpx.json`；未指定时沿用目标平台默认。
- 单位严格按 `rootInfo.unitConversion`
- 不要保留对 region tsx/css 的相对 import
- 最终产物需可独立编译
- composition plan 必须记录由 `interaction-inventory.json` 驱动的组件选择，以及不能满足的目标端限制。
- 如果 visible evidence 或 interaction inventory 指向 tabs/paged/list/input/action/overlay 结构，必须用真实可见的目标组件或目标原生交互结构满足；不要用静态 `view/text` 外观替代。
- 不要添加隐藏、透明、不可达、视觉无关的组件或文字来满足 deterministic validation。

## Step 8: 自检

- 检查 import 集、wrapper 定位、单位、composition plan、最终视觉顺序是否合理。
- 把最终产物回填到 `<figma2codeDir>/figma2code.json`。

## Step 9: 清理

确认 `<userOutputDir>` 下的 `figma2code.tsx` / `figma2code.css` 已正确产出后，删除本次本地切分产物，避免影响下次任务：

- 删除 `.aiden_d2c/<prefix>/` 与 `.aiden_d2c/<prefix>.tar.gz`。
- 仅删本次 `<prefix>` 对应内容，不要误删 `.aiden_d2c/` 下其他任务目录。
- 若产物校验失败或用户要求保留以便排查，则跳过清理并在报告中说明残留路径。

## Failure Modes

| 故障 | 处置 |
|:-----|:-----|
| `d2c segment create` 报错 | 透传 error / message 给用户；终止 |
| 状态查询返回 `failed` / `cancelled` | 透传 message；终止 |
| 状态轮询超时 | 终止；提示用户重试 |
| `downloadUrl` 下载失败 / 包损坏 | 终止；提示用户重跑切分任务 |
| `region-artifacts.json` 缺失 | 终止；提示产物不完整 |
| 任意 region 非 success | 终止；提示重跑切分任务 |
| 目标 skill 缺失 | 使用保守 fallback，并在最终报告里明确说明 |
