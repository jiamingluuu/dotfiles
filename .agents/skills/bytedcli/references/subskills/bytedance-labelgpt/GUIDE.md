---
name: bytedance-labelgpt
description: LabelGPT 助手：通过 `bytedcli labelgpt` 使用 LabelGPT 平台的完整业务能力，并复用 bytedcli 的认证与站点。在明确的 LabelGPT 上下文中涉及 Space、Plugin、Agent、Dataset、Model、Metrics、schema 或命令发现时使用。
---

# bytedcli LabelGPT

`bytedcli labelgpt` 承载 LabelGPT 平台的完整命令面。业务能力、参数、Schema 和操作规则由 [LabelGPT 命令参考](references/upstream/GUIDE.md) 维护；处理具体任务前，先读取该文件及其指向的对应 reference。

## 宿主差异

读取命令参考时只应用以下宿主映射，其他业务语义保持不变：

- 所有命令统一通过 `bytedcli labelgpt <args...>` 调用，参数与退出码原样透传；参考文档中出现的命令均已写作 bytedcli 形态。
- 认证命令：使用 `bytedcli auth login|status|logout`。宿主模式不开放 `bytedcli labelgpt auth ...`。
- Shell completion：宿主不开放上游 `completion` 命令；使用 bytedcli 自身的补全能力。
- 运行时安装：无需任何手动安装；bytedcli 会在首次运行时自动准备兼容运行时，也不要执行任何外部安装脚本。
- 运行时更新：`bytedcli labelgpt update ...` 只更新平台运行时，不同步上游 Skill。
- Skill 更新：默认全局安装时，`bytedcli labelgpt update skill ...` 对应 `bytedcli self skill update -s bytedance-labelgpt -g`；若明确安装在当前项目，则省略 `-g`。
- 站点与身份：由 bytedcli 注入；不要向子命令传 `--byted-jwt-token` 或 `--endpoint`。不开放 `config set endpoint|custom-region` 持久化覆盖；请使用 `bytedcli --site`，或为单次调用传官方 `--custom-region`。
- bytedcli 全局参数必须放在 `labelgpt` 前（如 `bytedcli --site cn --debug labelgpt ...`）；`labelgpt` 后、首个 `--` 前的参数属于官方 CLI，并按原样透传。
- 机器可读输出：优先把全局 `--json` 放在命令域前，例如 `bytedcli --json labelgpt commands`。不要与下游 `-o/--output` 或 `--format pretty` 同时使用。
- `--input -` 依赖真实 stdin，只能直接从 shell 执行，不能通过捕获式或 MCP 调用执行。

## 快速入口

```bash
bytedcli auth status
bytedcli auth login
bytedcli labelgpt version
bytedcli --json labelgpt commands
bytedcli --json labelgpt schema <command-path>
```

不要根据 bytedcli 的静态命令清单猜测 LabelGPT 能力；以当前官方 CLI 的 `commands`、`schema` 和上游 Skill 为准。
