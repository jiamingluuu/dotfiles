---
name: bytedance-tae
description: "TAE / AI PaaS workflow: sandbox sessions, Bash/PTY, processes, files and ports through native controlplane/sandboxd commands; Connector access-policy domain whitelist (tae connector domain/release/ticket); search MCP server_id by name/keyword, use first-class bytedcli commands for Agent/Sandbox search/list/get and MCP Server/Tool operations, import BAM RPC methods, generate tool_input_schema from Thrift IDL, publish revisions, and verify live config. Use when users mention TAE, AI PaaS, /tae URLs, /ai/agent, /ai/sandbox, /ai/mcp_server URLs, MCP name/keyword lookup, MCP tool 录入/发布, BAM 接口导入, RPC tool creation, fixing MCP Input Schema, or Sandbox 域名加白 / connector 访问策略 / access-policy whitelist on ByteCloud."
---

# bytedcli TAE / AI PaaS

This skill covers TAE / AI PaaS operations. Prefer first-class bytedcli commands for Agent/Sandbox list/get and MCP Server management; unresolved Memory/Skill surfaces are documented as discovered API areas and should be verified before write operations.

## 前置条件

- 使用通用调用方式：`../../invocation.md`
- 需要排错时看：`../../troubleshooting.md`
- Sandbox 会话、执行、文件与端口：`references/sandbox-runtime.md`
- 具体 TAE / AI PaaS API 工作流：`references/tae.md`

## When to use

- 用户提到 TAE、AI PaaS、MCP Server、MCP Tool、AI Agent、AI Sandbox、AI Memory、AI Skill。
- 用户给出 `cloud.tiktok-row.net/tae/...`、`/tae/...`、`/ai/...` 页面，尤其是 `/ai/mcp_server`、`/ai/agent`、`/ai/sandbox`、`/ai/memory`、`/ai/skill`。
- 用户只有 MCP 名称 / 关键词，需要查找 `server_id`，不想先提供 URL。
- 用户要查询、新建、更新、发布 MCP Server，或排查 server settings / revision。
- 用户要录入、查询、删除、更新或发布 MCP tools，包括 RPC MCP tool。
- 用户反馈 MCP tool 的 `tool_input_schema` / Input Schema 为空、不正确、缺 description，或模型 structured output 报 schema / `format` 问题。
- 用户要从 Thrift IDL / Kitex RPC method 生成或回写 MCP tool input schema。
- 用户要搜索、查询 TAE Agent / Sandbox 列表或详情。
- 用户要给 Sandbox Connector 加内网/公网访问白名单域名（access-policy），或查询/预览/提交 Connector 发布工单：`/tae/connector/.../access-policy` 页面、「域名加白」「访问策略」「connector 白名单」。
- 用户要调研 Memory、Skill、A2A Registry、Keys、Security Policy 等 TAE 平台页面/API。
- 用户遇到 TAE 鉴权、401/403、site、region/env 参数相关问题。

## Markdown 多行换行（必读）

传递 Markdown、多行命令或 stdin 文本时，使用 `$'line1\nline2'`。不要使用 `"line1\nline2"`，后者会传入字面量反斜杠和 n。

## Supported capabilities

- 原生 `bytedcli tae sandbox session/bash/exec/process/fs/port/request/region list`：详见 `references/sandbox-runtime.md`；`list/search/get` 仍是平台资源查询。
- 解析 TAE MCP Server URL，提取 `server_id`、`env`、region。
- 使用 bytedcli 内置认证调用 TAE 命令和已确认的 raw API 路径。
- 列出现有 MCP tools，识别 tool 类型、重复项、空 Input Schema。
- 新建 MCP Server，并在成功后进入 server tools/settings 流程。
- 创建 RPC MCP tools。
- 默认 dry-run 预览 BAM RPC 导入 payload，显式 `--yes` 后逐项创建，并可在全部成功后发布 revision。
- PATCH 更新已有 tools，保留原配置并替换 `tool_input_schema`。
- 从 Thrift IDL 解析 Request struct，生成 JSON Schema。
- 从 IDL 注释补充 schema `description`，解析 enum、nested struct、list/map/set。
- 避免生成空 `format` 字段，兼容 GPT 5.5 structured output。
- 发布 MCP server revision，并重新拉取线上配置做验证。
- 输出批量操作报告，便于超时后定位成功/失败项。
- 使用一等 CLI：`bytedcli tae agent search/list/get` / `bytedcli tae sandbox search/list/get` 查询 Agent/Sandbox，`bytedcli tae mcp server ...` / `bytedcli tae mcp tool ...` 管理 MCP Server 和 Tool，`schema generate/update` 生成并回写 input schema。
- Connector 访问策略（域名白名单）：`bytedcli tae connector domain list/add`、`release preview/create`、`ticket get`；写操作默认 dry-run，`--yes` 才改草稿，草稿须经 BPM 审批的 release 工单才生效，详见 `references/tae.md`。
- 调研并定位 TAE Memory、Skill、A2A Registry、Keys、Security Policy 等页面对应的前端 API；写操作前需先确认 payload 和权限。

## Quick start

1. 先读 `references/tae.md`。
2. 从 TAE URL 提取 `server_id`、`env`、`x-bc-region-id`。
3. 优先使用 `bytedcli tae agent --help`、`bytedcli tae sandbox --help`、`bytedcli tae mcp server --help` 和 `bytedcli tae mcp tool --help`。
4. 如果 CLI 未覆盖目标能力，再用 `bytedcli tae api ...` 调已确认的 TAE API 路径。
5. 对 RPC tools，用 `bytedcli tae mcp schema generate/update` 从 Thrift IDL 生成真实 `tool_input_schema`，不要输出空 `format`。
6. 从 BAM 导入时先运行 `tae mcp tool import-bam` 查看 dry-run payload；确认后用 `--descriptions-json` 为每个方法补齐模型可读描述并加 `--yes`，需要发布时同时加 `--release`。
7. 手工创建 RPC tools 时，不要指定 `tool_config.rpc.idl`。
8. 批量操作成功后重新 list 验证。

## References

- `references/sandbox-runtime.md` — Sandbox 运行时命令、参数、认证与 taecli 迁移表

- `references/tae.md` — TAE / AI PaaS API 操作指南
- `../../invocation.md` — bytedcli 通用调用方式
- `../../troubleshooting.md` — 通用排障
