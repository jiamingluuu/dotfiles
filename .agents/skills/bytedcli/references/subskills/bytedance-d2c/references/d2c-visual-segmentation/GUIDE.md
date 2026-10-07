---
name: d2c-visual-segmentation
description: 通过 D2C 视觉切分 API 把 Figma 设计稿转换为生产级 browser / Lynx 代码切分产物。发起切分任务、轮询任务状态、拿到 downloadUrl 后下载并解压产物。当用户给出 Figma design 链接需要转代码、提到 D2C / 视觉切分 / figma2code / visualSegmentation，或需要拉取切分产物组装整页代码时使用。替代 aiden_d2c_create_visual_segmentation_task 与 aiden_d2c_get_visual_segmentation_status 两个 MCP 工具，直接走 HTTP 接口。
allowed-tools: Bash, Read, Write, Edit, Grep
---

# D2C 视觉切分

DeepWiki D2C 视觉切分服务的集成，用于把 Figma 设计稿转换为 browser / Lynx 代码切分产物。本 capability 用 `bytedcli d2c` 命令调用该服务，替代 `aiden_d2c_create_visual_segmentation_task` 和 `aiden_d2c_get_visual_segmentation_status` 两个 MCP 工具。

## 快速开始

整体流程：**发起任务 → 轮询状态 → 拿到 downloadUrl → 下载 tar.gz → 解压 → 定位 figma2code 产物**。

### Step 1: 发起切分任务

```bash
bytedcli --json d2c segment create \
  --figma-url "https://www.figma.com/design/demoFileKey/demo-page?node-id=123-456" \
  --transform-type "lynx" \
  --repo-name "example/demo-repo" \
  --creator "your.email.prefix" \
  --config '{"unit":"rpx"}'
```

返回 `{ success, taskId, message }`，记下 `taskId`。

`--figma-token` 与 `--figma-auth-token` 都是可选的覆盖项（见下方「Figma token 解析」）。`--creator` / `--figma-url` 为必填，`--repo-name` / `--transform-type` 建议显式传入——本命令**不会**自动从 git 推断，所有参数都由调用方（agent）从上下文中明确给出。

`--config` 必须传完整的 JSON 对象，命令会将它原样写入 visualSegmentation POST body（也可用 `--config-file <path>` 从文件读取）。调用方从业务上下文组装该对象；当前必需字段 `unit` 由 `<projectRoot>/d2c_context/d2c.contract.json` 的 `target.unit` 解析，其他配置字段不得丢弃。字段映射与默认值见 [references/scripts.md](references/scripts.md)。

#### Figma token 解析（bytedcli 行为）

不需要、也不要创建任何 `settings.json`。`bytedcli d2c segment create` 在内部按以下优先级解析 Figma token：

1. 显式 flag：`--figma-token` 或 `--figma-auth-token`
2. 环境变量：`FIGMA_ACCESS_TOKEN` / `FIGMA_PAT` / `FIGMA_TOKEN` / `FIGMA_AUTH_TOKEN`
3. 后端按 `--creator` 查询该用户已登记的 token

token **只在内存中使用**——不写入磁盘、不打日志、不出现在命令输出里。因此没有「配置落盘」这一步，也没有「写入失败就终止」的前置条件。

> The resolved Figma token is held **in memory only**: it is **never written to disk**, never logged, and never echoed in command output. There is no config file to persist and therefore no "stop if the write failed" precondition.

规则：

1. 不要把 token 写进任何配置文件或产物。
2. 不得在聊天回复或普通日志中打印明文 token；展示配置时必须脱敏。
3. `creator`、`repo_name`、`transformType` 仍必须由调用方显式提供，命令不做 git 推断。

> ⚠️ 不要绕过 bytedcli 去直连 D2C HTTP 接口：上游脚本 **send no credentials**（不带任何凭据），而本命令走你自己的 ByteCloud + Codebase SSO 会话。

### Step 2: 轮询任务状态

```bash
bytedcli --json d2c task get \
  --task-id "<taskId>" \
  --kind visual-segmentation
```

也可以在发起任务时直接等待终态并落盘产物：

```bash
bytedcli --json d2c segment create \
  --figma-url "https://www.figma.com/design/demoFileKey/demo-page?node-id=123-456" \
  --creator "your.email.prefix" \
  --config '{"unit":"rpx"}' \
  --wait \
  --output-dir ".aiden_d2c/<prefix>" \
  --poll-interval-ms 60000 \
  --timeout-ms 1200000
```

- `--wait`：命令内部按 `--poll-interval-ms`（毫秒，最小 `30000`，建议 `60000`）轮询，命中 `completed` / `failed` / `cancelled` 时返回；总时限由 `--timeout-ms` 控制（默认 `1200000`，即 20 分钟）。配合 `--output-dir` 时会自动下载并解压产物。
- 不传 `--wait`：只返回 `taskId`，之后用 `d2c task get --kind visual-segmentation` 自行查询。
- ⚠️ 用 `Bash` 调用 `--wait` 模式时**必须**把 timeout 设为略大于 `--timeout-ms`（默认至少 **20 分钟**）。

`status === 'completed'` 时返回会带 `downloadUrl`；`failed` / `cancelled` 立即终止并把 message 透传给用户。

### Step 3: 下载并解压产物

`completed` 后从返回里拿到 `downloadUrl`，下载落盘并解压（无需额外 cookie / 鉴权头）：

```bash
# <prefix> 取 figmaUrl 后六位
mkdir -p .aiden_d2c/<prefix>
curl -L "<downloadUrl>" -o .aiden_d2c/<prefix>.tar.gz
tar -xzf .aiden_d2c/<prefix>.tar.gz -C .aiden_d2c/<prefix> --strip-components 1
```

解压后定位其中的 `figma2code/` 目录（记为 `<figma2codeDir>`），并优先读取 `<figma2codeDir>/regions-visual/region-artifacts.json` 验证产物完整性。视觉切分产物还应包含 `<figma2codeDir>/run-artifacts/figma-facts.json`、`page-plan.json` 和 `section-contracts.json`，供后续组装和 deterministic validation 使用。

## 核心命令概览

每条都是 **✅ bytedcli command**（不是 plugin 脚本）。`d2c task get` 是 **read-only** 的状态查询，不消耗算力；`d2c segment create` 会创建服务端任务。

| 命令 | 功能 | 对应 MCP 工具 |
|------|------|--------------|
| `bytedcli d2c segment create` | 发起 D2C 视觉切分任务，返回 `taskId`；带 `--wait --output-dir` 时直接落盘产物 | `aiden_d2c_create_visual_segmentation_task` |
| `bytedcli d2c task get --kind visual-segmentation` | 查询任务状态，`completed` 时返回 `downloadUrl` | `aiden_d2c_get_visual_segmentation_status` |

状态查询的完整形态（read-only）：

```bash
bytedcli --json d2c task get --task-id "<taskId>" --kind visual-segmentation
```

同一条命令换 `--kind render-screenshot` 即可查 render 任务 —— 见
[d2c-render-screenshot](../d2c-render-screenshot/GUIDE.md)。

## 详细文档参考

- **命令参数与用法**：[references/scripts.md](references/scripts.md)
- **完整工作流（拿到产物后如何组装整页代码）**：[references/workflow.md](references/workflow.md)

## ⚠️ 重要注意事项

1. **执行环境**：所有命令调用**必须**用 `Bash` 工具执行，**切勿**通过重复调用 `Skill` 工具来运行命令。
2. **超时设置**：`d2c segment create --wait` 耗时长，`Bash` 超时必须 ≥ `--timeout-ms`（默认至少 20 分钟）。
3. **错误透传**：任一接口失败时，响应是 JSON `{ error, message, ... }`，把 `error` / `message` 直接透传给用户并终止，不要静默重试。
4. **任务失败**：状态为 `failed` / `cancelled` 时立即终止，提示用户检查 `repo_name`、`transformType`、`creator`、Figma token 后重试。
5. **不要落盘 token**：命令在内部解析 Figma token 并只在内存中使用；不要创建 `settings.json`，也不要把 token 写进任何文件。
6. **配置透传**：发起任务前解析完整 segmentation config，并通过 `--config`（或 `--config-file`）发送；不要只挑选 `unit` 或丢弃未知字段。
