---
name: bytedance-aiden
description: "Use Aiden through bytedcli aiden when asked to delegate work to Aiden, create or inspect its tasks, follow runs, conversations and artifacts, or manage its Agent configuration. Match Aiden task/run links and follow-up requests about an Aiden task already in context. Generic development requests or tasks without an identified platform do not trigger this skill. D2C and DeepWiki use their own domain skills."
---

# bytedcli aiden

使用 `bytedcli aiden` 管理 Aiden Cloud 的任务、运行、产物与 Agent。需要 Node.js >= 20、可用的 `node` / `npm`、公司网络和 Aiden 访问权限。

需要执行具体 Aiden 工作流时，先运行 `bytedcli aiden self skill install` 安装或刷新官方 Aiden skill，并重新加载；本 skill 只补充 bytedcli 入口和差异说明。

## 首次使用与认证

以下说明首次使用的授权流程；已有安装可用 `bytedcli aiden --version` 核对版本，旧版本按下方更新命令升级。

直接执行目标命令。没有有效首次检查标记时，命令会在首次平台请求前检查授权，通过后保存标记供后续调用复用。只有 ByteCloud 授权必需；Codebase、飞书、Meego 和 bytedcli SSO 的状态用于诊断。

```bash
# 单独建立本地登录态，不检查云端平台授权
bytedcli aiden auth login
# 复用现有身份或完成登录，再刷新平台授权状态
bytedcli aiden setup
# 检查现有凭证并刷新平台授权状态，不发起登录
bytedcli aiden auth status --json
# 仅检查本地凭证，不访问 Aiden API
bytedcli aiden auth status --local --json
```

- 认证缺失或检查异常时，按[常见问题](../../troubleshooting.md)中的恢复步骤处理。
- 登录链接和 Code 可能通过 stderr 展示，JSON 模式同样如此；将登录指引交给用户完成，再等待命令最终结果。
- `auth status --local` 成功仅证明本地凭证可用；完整检查的 `ready` 和 `setup` 的 `verified` 仅证明当前身份与必需授权通过，空间和具体业务权限仍由目标操作检查。业务写入失败或结果不确定时，先读回目标状态，不自动重放写入。

## 发现命令

以当前版本的帮助和 Schema 为准，不猜测业务参数。收到 task / run 链接时，先识别目标，再按帮助或 Schema 确认所需参数。

```bash
bytedcli aiden --help
bytedcli aiden task --help
bytedcli aiden task create --help
bytedcli aiden schema task create --json
bytedcli aiden task list --json
# 查看 Aiden Skill 的安装参数
bytedcli aiden self skill install --help
```

- `task` 管理任务；`run` 查看进展、会话和产物；`agent` / `team` 管理 Agent；`space` / `context` 选择空间和执行主体。其他能力按 `--help` 发现。
- 需要结构化结果时传 `--json`，支持 `bytedcli --json aiden ...` 和 `bytedcli aiden ... --json`；短参数 `-j` 仅在 `aiden` 前启用 JSON 模式。业务结果保留 Aiden JSON 结构，帮助与版本文本在 JSON 模式下包装为 bytedcli JSON。
- `aiden` 后的 `-j` / `-json` 不作为 JSON 开关处理，例如 `--prompt -j` 保留字符串值；`--` 之后所有参数均保持原样。在 `--` 前同时启用 JSON 模式并使用 `--json=false` / `--no-json` 关闭 JSON 时，命令执行前返回结构化参数错误。
- 支持 Unix 管道：用 JSON/JSONL 输出接下游处理；需要从 stdin 读取 Prompt、manifest 或配置时，按命令 Schema 将对应文件参数设为 `-`，每次命令只消费一次 stdin。Shell 管道启用 `set -o pipefail` 或逐进程检查退出码。

## 更新 Aiden 命令

```bash
bytedcli aiden +update
bytedcli aiden +update <version>
```

省略版本时更新到 `latest`。`bytedcli aiden update [version]` 是兼容入口，同样更新 bytedcli 托管的 Aiden 依赖；仅接受可选版本或 dist-tag，不使用上游要求 npm 全局安装的自更新流程。
