---
name: bytedance-bfc
description: "Operate BFC (ByteDance Flow Control) via bytedcli: query plans, analyze plan metadata and operation schemas, union plans, products, product directories, operation execution history, tenants, and broadcast flow records/issues. Use when tasks mention BFC, ByteDance Flow Control, 预案, 操作元数据, operation schema, 联合预案, 产品线, 产品目录, 执行历史, 租户信息, 容灾演练, or broadcast flows."
---

# BFC

## 如何调用 bytedcli

推荐：先全局安装一次，后续所有命令直接调用 `bytedcli`。

```bash
# 推荐方式：先全局安装，后续直接调用 bytedcli
NPM_CONFIG_REGISTRY=http://bnpm.byted.org npm install -g @bytedance-dev/bytedcli@latest
bytedcli <command> [options]
```

```bash
# Fallback：仅在无法全局安装时使用 npx 临时执行
NPM_CONFIG_REGISTRY=http://bnpm.byted.org npx -y @bytedance-dev/bytedcli@latest <command> [options]
```

BFC 平台的 CLI 操作工具。

## Capabilities

- 预案管理：查询预案详情与列表
- 预案分析元数据：查询操作类型、参数 schema、预案结构骨架与状态列表
- 联合预案：查询详情与列表
- 产品：列表（v3）、详情与产品线目录
- 预案操作执行：查询执行记录
- 租户：查询详情与列表
- 容灾演练：查询流程列表、流程详情与流程问题

## Agent Guidance

- 解释或分析 BFC 预案时，优先用 `bfc plan get` 获取预案详情；当需要理解 `operation_type`、操作参数含义、分级参数结构或预案返回结构时，再查询 `bfc meta get`。
- `bfc meta get` 默认返回 Agent 分析视图：`operations_v3`、`plan_status_list`、`empty_plan` 和语义说明。它不是控制台初始化数据大全。
- `operations_v3` 是操作 schema 的主要来源；涉及具体产品线时传 `--product-id`，这样返回的 `hide` 状态更贴近当前上下文。
- `hide=true` 表示该操作在当前元数据上下文中隐藏或不推荐新增；它不等于不支持或非法。已有预案中出现 hidden 操作时仍应保留并解释。
- `empty_plan` 只用于理解 `plan get` 返回结构骨架，不是 `/plan/create` 或 `/plan/update` 的请求模板。创建或更新操作参数应以 `operations_v3` 中对应 operation 的 `params` 和 `phase_params` 为准。
- `--section raw` 会返回完整后端 `/meta` 原始数据，其中可能包含废弃或仅为控制台兼容保留的字段，例如 `app_map`、`biz_panel_meta` 等。Agent 默认不要基于这些字段推理当前能力。

## Usage

```bash
# 查询预案详情
bytedcli bfc plan get --plan-key <key>

# 查询预案列表（分页+筛选）
bytedcli bfc plan list --product-id 123 --page 1 --page-size 20 --keyword <keyword>

# 查询预案分析元数据（操作 schema + 状态 + 结构骨架）
bytedcli bfc meta get --product-id 123

# 查询单个操作类型的参数 schema
bytedcli bfc meta get --operation-type 316 --product-id 123

# 只查询预案状态列表
bytedcli bfc meta get --section statuses

# 查询完整后端 /meta 原始响应（包含历史控制台字段）
bytedcli bfc meta get --section raw

# 查询联合预案详情
bytedcli bfc union get --union-key <key>

# 查询联合预案列表（分页+筛选）
bytedcli bfc union list --product-id 123 --page 1 --page-size 20 --status 1

# 查询产品列表（v3）
bytedcli bfc product list --version v3 --tenant-id 1001 --page 1 --page-size 20

# 查询产品详情
bytedcli bfc product get --product-id 123

# 查询产品线目录
bytedcli bfc product dirs --product-id 123 --ids 1001,1002

# 查询预案操作执行记录
bytedcli bfc op-exec list --plan-key <key> --start-time-gte <ts> --start-time-lte <ts>

# 查询租户详情
bytedcli bfc tenant get --tenant-id 1001

# 查询租户列表（分页+筛选）
bytedcli bfc tenant list --name-like <name> --page 1 --page-size 20

# 查询容灾演练流程列表
bytedcli bfc broadcast flows list --query page=1 page_size=20

# 查询容灾演练流程详情
bytedcli bfc broadcast flows get --id 123456

# 查询容灾演练问题列表
bytedcli bfc broadcast flows issues --id 123456

# Agent 调用必须加上 --json
bytedcli --json bfc plan get --plan-key <key>
```
