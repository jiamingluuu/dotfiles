---
name: bytedance-ark
description: "Operate the internal Volc ARK (方舟) console at ark.bytedance.net via bytedcli: list projects, foundation models, inference endpoints, and masked API keys within an ARK account. Use when tasks mention 方舟 / ARK console, ark.bytedance.net, ARK projects, doubao foundation models, inference endpoints, ep- endpoint ids, or ARK API keys for internal ByteDance accounts."
---

# bytedcli ARK（内部方舟控制台）

内部方舟控制台（https://ark.bytedance.net）只读命令：在指定 ARK 账号下列出项目、基础模型、推理接入点与 API Key（密钥始终脱敏）。

## 如何调用 bytedcli

```bash
# 推荐方式：先全局安装，后续直接调用 bytedcli
NPM_CONFIG_REGISTRY=http://bnpm.byted.org npm install -g @bytedance-dev/bytedcli@latest
bytedcli <command> [options]
```

## 前置条件

- 已通过 `bytedcli auth login` 完成 SSO 登录；命令使用 ByteCloud CN JWT（与 TCE/Keel 同一套办公网登录态）。
- 知道 **ARK 账号 ID（数字）**：打开 https://ark.bytedance.net 任意页面，URL 中 `arkAccountId=<id>` 即账号 ID。
  - 可通过 `--account-id <id>` 传入，或设置环境变量 `BYTEDCLI_ARK_ACCOUNT_ID` 后省略。

## Quick start

```bash
# 列出账号下的项目（project 名称是其他命令的入参）
bytedcli ark project list --account-id 2100000000
bytedcli ark project list --account-id 2100000000 --keyword demo

# 查看单个项目详情（服务树路径/部门/Owner/告警 PSM）
bytedcli ark project get --account-id 2100000000 --project-name demo-project

# 列出项目已开通的基础模型
bytedcli ark foundation-model list --account-id 2100000000 --project-name demo-project
bytedcli ark foundation-model list --account-id 2100000000 --project-name demo-project \
  --names doubao-seed-1-8,doubao-seed-code --page 1 --page-size 50

# 列出项目的推理接入点（普通 / agentic）
bytedcli ark endpoint list --account-id 2100000000 --project-name demo-project
bytedcli ark endpoint list --account-id 2100000000 --project-name demo-project --agentic

# 查询推理 token 用量（按 Day/Hour 聚合；start/end 为 YYYY-MM-DD 闭区间）
bytedcli ark inference-usage list --account-id 2100000000 --project-name demo-project \
  --start 2026-08-13 --end 2026-08-26
bytedcli ark inference-usage list --account-id 2100000000 --project-name demo-project \
  --start 2026-08-26 --end 2026-08-26 --interval Hour --endpoint-like ep-20

# 列出项目的 API Key（默认仅 Active；Key 字段由后端脱敏，不会泄露明文）
bytedcli ark api-key list --account-id 2100000000 --project-name demo-project
bytedcli ark api-key list --account-id 2100000000 --project-name demo-project --all-statuses
```

## 输出约定

- 所有命令默认表格文本输出；`-j/--json` 输出 JSON。普通资源列表包含 `items`、`total`、`page`、`page_size`、`has_more`。
- `inference-usage list` 是按区间聚合的用量查询（非分页），JSON 输出 `fields`（列名顺序）、`rows`（对齐字段的用量行：InputTokens/CacheTokensHit/OutputTokens/TotalTokens/ReqCnt 等）、`current_count` 与后端的 `data_count`。
- API Key 的 `key` 字段由控制台返回星号脱敏值；本平台没有任何命令可以读取明文密钥。

## Agent Guidance

- 账号 ID 与 project name 是两层不同入参：先用 `ark project list` 拿 `projectName`，再调用其余三个命令；不要把账号 ID 当 project name。
- 这些命令只覆盖内部办公网 `ark.bytedance.net` 控制台（CN）；火山公有云（volcengine.com）控制台不在范围内。
