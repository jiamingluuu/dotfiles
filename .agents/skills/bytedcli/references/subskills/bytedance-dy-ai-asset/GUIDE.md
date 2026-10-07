---
name: bytedance-dy-ai-asset
description: 抖音AI资产平台 AI 资源（Skill / MCP Tool）查询与调用。当用户提到 dy-ai-asset、抖音 AI 资源、AI 资产、查询 Skill/MCP 资源、获取 MCP 工具详情、调用 MCP 工具，或需要按 resource_id / out_resource_id / 名称 / 平台 / 业务线检索 AI 资源时使用。
---

# DY AI Asset — AI 资源查询与 MCP 工具调用

通过 `bytedcli dy-ai-asset` 在 DY AI Asset 平台检索 AI 资源（Skill / MCP Tool / Knowledge / Memory）、获取指定 MCP Tool 的详情，并对 MCP Tool 发起调用。

## Authentication

依赖 ByteCloud JWT，登录共享 `bytedcli auth` 体系：

```bash
bytedcli auth login --begin
bytedcli auth status
```

如果 ByteCloud JWT 拿不到，CLI 会按下列顺序回退到环境变量：

1. `BYTEDCLI_USER_CLOUD_JWT`
2. `AIME_USER_CLOUD_JWT`
3. `BYTEDCLI_USER_CODE_JWT`
4. `AIME_USER_CODE_JWT`

可选环境变量 `DOUYIN_AI_ASSET_CLIENT_TOKEN` 用于在请求头补充 `ClientToken`。

## Commands

### search — 搜索 AI 资源

```bash
# 按 resource id 精确查询（多个用逗号分隔）
bytedcli dy-ai-asset search --resource-ids asset-123,asset-456

# 按 out resource id 查询
bytedcli dy-ai-asset search --out-resource-ids out-id-1,out-id-2

# 名称模糊搜索（多个关键词用逗号分隔）
bytedcli dy-ai-asset search --names-like "my-skill,my-tool"

# 按类型过滤（语义化值：skill / mcp / knowledge / memory，逗号分隔）
bytedcli dy-ai-asset search --names-like demo --types skill,mcp

# 按平台 / 业务线过滤
bytedcli dy-ai-asset search --names-like demo --platform example-platform --biz-line example-biz

# 显式 JSON 输出
bytedcli --json dy-ai-asset search --resource-ids asset-123
```

### get-tool — 获取指定 MCP Tool 详情

```bash
# 通过 resource id + tool name
bytedcli dy-ai-asset get-tool --resource-id asset-123 --tool-name my-tool

# 通过 resource id + tool key
bytedcli dy-ai-asset get-tool --resource-id asset-123 --tool-key my-tool-key

# 通过 out resource id 查找
bytedcli dy-ai-asset get-tool --out-resource-id out-id-1 --tool-name my-tool

# 显式 JSON 输出
bytedcli --json dy-ai-asset get-tool --resource-id asset-123 --tool-key my-tool-key
```

### call — 调用 MCP Tool

```bash
# 通过 tool name 调用
bytedcli dy-ai-asset call \
  --resource-id asset-123 \
  --tool-name my-tool \
  --tool-arguments '{"param1": "value1"}'

# 通过 tool key 调用
bytedcli dy-ai-asset call \
  --resource-id asset-123 \
  --tool-key my-tool-key \
  --tool-arguments '{"param1": "value1"}'

# 显式 JSON 输出
bytedcli --json dy-ai-asset call \
  --resource-id asset-123 \
  --tool-name my-tool \
  --tool-arguments '{}'
```

## Options

### search

| Option                       | 必填 | 说明                                                               |
| ---------------------------- | ---- | ------------------------------------------------------------------ |
| `--resource-ids <ids>`       | 否   | 逗号分隔的 resource id 列表                                        |
| `--out-resource-ids <ids>`   | 否   | 逗号分隔的 out resource id 列表                                    |
| `--names-like <names>`       | 否   | 逗号分隔的名称关键词，做模糊搜索                                   |
| `--types <types>`            | 否   | 资源类型过滤，逗号分隔的语义化值：`skill`、`mcp`、`knowledge`、`memory` |
| `--platform <platform>`      | 否   | 资源所属平台过滤                                                   |
| `--biz-line <bizLine>`       | 否   | 资源所属业务线过滤                                                 |

> 至少传 `--resource-ids`、`--out-resource-ids`、`--names-like` 中的一个；`--types`、`--platform`、`--biz-line` 通常作为附加过滤项使用。

### get-tool

| Option                     | 必填   | 说明                                       |
| -------------------------- | ------ | ------------------------------------------ |
| `--resource-id <id>`       | 二选一 | resource id（与 `--out-resource-id` 互斥） |
| `--out-resource-id <id>`   | 二选一 | out resource id                            |
| `--tool-name <name>`       | 二选一 | tool name（与 `--tool-key` 二选一）        |
| `--tool-key <key>`         | 二选一 | tool key                                   |

### call

| Option                          | 必填 | 说明                                               |
| ------------------------------- | ---- | -------------------------------------------------- |
| `--resource-id <id>`            | 是   | resource id                                        |
| `--tool-name <name>`            | 二选一 | tool name（与 `--tool-key` 二选一）              |
| `--tool-key <key>`              | 二选一 | tool key                                           |
| `--tool-arguments <json>`       | 是   | 工具入参 JSON 字符串，例如 `'{"param1":"v1"}'`     |

## Output Modes

- **默认文本**：
  - `search`：按资源逐条渲染，包含 Resource ID、Out Resource ID、Type、Description；MCP 资源会展开 Tools（name/key/description/input_schema/output_schema），Skill 资源会展开 Skill 信息，并列出依赖资源。
  - `get-tool`：渲染单个 MCP Tool 详情（name/key/description/input_schema/output_schema）；若资源不是 MCP 或未命中目标 tool，会列出该资源下可用工具供参考。
  - `call`：成功时输出 `Call success!` 与 data 字段；失败时输出错误消息。
- **显式 JSON (`--json`)**：在 `data` 字段返回结构化结果，适合 Agent / 脚本消费。

## Common Patterns

**按名称模糊检索 MCP 工具，再获取某个工具的详情：**

```bash
bytedcli dy-ai-asset search --names-like demo --types mcp
bytedcli dy-ai-asset get-tool --resource-id <resource-id> --tool-name <tool-name>
```

**直接通过工具 key 调用：**

```bash
bytedcli dy-ai-asset call \
  --resource-id <resource-id> \
  --tool-key <tool-key> \
  --tool-arguments '{"foo":"bar"}'
```

**JSON 模式驱动 Agent 流程：**

```bash
bytedcli --json dy-ai-asset search --names-like demo --types mcp
bytedcli --json dy-ai-asset get-tool --resource-id <resource-id> --tool-key <tool-key>
bytedcli --json dy-ai-asset call \
  --resource-id <resource-id> \
  --tool-key <tool-key> \
  --tool-arguments '{}'
```

## References

- [invocation.md](../../invocation.md) — bytedcli 通用调用方式
- [dy-ai-asset.md](references/dy-ai-asset.md) — 命令与 API 映射、资源 / 工具字段说明
- [troubleshooting.md](../../troubleshooting.md) — 常见问题与处理
