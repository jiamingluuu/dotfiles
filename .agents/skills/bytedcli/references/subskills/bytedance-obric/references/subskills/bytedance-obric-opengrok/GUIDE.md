---
name: bytedance-obric-opengrok
description: "Obric 内部研发工具集中的 OpenGrok 命令行工具。支持索引项目列表、代码符号/文本搜索和 raw 文件读取。用户提到 Obric OpenGrok、OpenGrok、代码索引、符号定义/引用或从 OpenGrok 读取源码时使用。"
---

# bytedcli obric opengrok

Obric 内部研发工具集中的 OpenGrok CLI 工具，用于查询代码索引和读取源码。

## 命令概览

| 命令 | 说明 |
| --- | --- |
| `bytedcli obric opengrok project list` | 列出索引项目 |
| `bytedcli obric opengrok search` | 搜索符号或文本 |
| `bytedcli obric opengrok get` | 读取 raw 文件 |

## Commands

```bash
# List indexed projects
bytedcli obric opengrok project list
bytedcli obric opengrok project list --page 1 --page-size 20
bytedcli --json obric opengrok project list

# Search code
bytedcli obric opengrok search --keyword SomeSymbol --kind defs
bytedcli obric opengrok search --keyword "error message" --project demo-project
bytedcli --json obric opengrok search --keyword SomeSymbol --kind refs --page-size 20

# Read raw file content
bytedcli obric opengrok get --path demo-project/src/index.ts
bytedcli --json obric opengrok get --path demo-project/src/index.ts
```

## Authentication

- OpenGrok auth reuses the browser SSO session saved by `bytedcli auth login --session`.
- If requests fail with `OPENGROK_AUTH_ERROR`, run `bytedcli auth login --session`, then retry.

## Agent Guidance

- Prefer `obric opengrok search` for code symbol or text search, not `insearch query`.
- Use `--kind defs` for definitions, `--kind refs` for references, `--kind full` for full-text search, and `--kind path` for path search.
- Use `--json` when another tool or agent needs structured paths, line numbers, URLs, or file content.
- Current scope is read-only: project list, search, and raw file read.

## References

- Read [references/opengrok-invocation.md](references/opengrok-invocation.md) for global option placement and invocation rules.
- Read [references/opengrok-troubleshooting.md](references/opengrok-troubleshooting.md) when authentication or command discovery fails.
