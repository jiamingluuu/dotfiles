---
name: bytedance-aidap
description: "Operate ByteDance internal AIDAP Serverless PostgreSQL resources via bytedcli: Workspaces, Branches, computes, database accounts, databases, connection endpoints, read-only SQL execution, and asynchronous operations. Use when tasks mention AIDAP, ServerlessPG, Serverless PostgreSQL, Workspace/Branch/Compute lifecycle, PostgreSQL data branches, AIDAP SQL queries, or the byteaidap OpenAPI."
---

# bytedcli AIDAP Serverless PostgreSQL

## Capability scope

本 skill 覆盖 AIDAP Serverless PostgreSQL Workspace、Branch、Compute、数据库账号、数据库、连接 endpoint、只读 SQL 查询与异步操作记录。Workspace 创建固定使用 PostgreSQL 17；Supabase、Pages、AI 等旁支接口不属于这一命令域。

## Authentication and routing

- 使用 ByteCloud 用户登录态动态获取 `x-jwt-token`，不要保存或传入浏览器 Cookie/JWT。
- ROW 内场服务使用全局参数 `--site i18n-tt`。
- AIDAP 资源/OpenAPI 命令显式传 `--project-name`，再按层级传 `--workspace-id`、`--branch-id` 或 `--compute-id`；`sql execute` 直接使用 Workspace、Branch 和数据库标识，不接收 `--project-name`。
- 写命令必须先用 `--dry-run` 检查 payload，再由用户确认后改用 `--yes`。

## Quick start

```bash
# 资源发现
bytedcli --site i18n-tt aidap workspace list --project-name demo-project
bytedcli --site i18n-tt aidap workspace get --project-name demo-project --workspace-id demo-workspace
bytedcli --site i18n-tt aidap branch list --project-name demo-project --workspace-id demo-workspace
bytedcli --site i18n-tt aidap compute list --project-name demo-project --workspace-id demo-workspace --branch-id br-demo-main

# 从指定父分支创建子分支：先预览，再提交
bytedcli --site i18n-tt aidap branch create --project-name demo-project --workspace-id demo-workspace --parent-id br-demo-main --name demo-child --dry-run
bytedcli --site i18n-tt aidap branch create --project-name demo-project --workspace-id demo-workspace --parent-id br-demo-main --name demo-child --yes

# 分支内资源与 endpoint
bytedcli --site i18n-tt aidap account list --project-name demo-project --workspace-id demo-workspace --branch-id br-demo-child
bytedcli --site i18n-tt aidap database list --project-name demo-project --workspace-id demo-workspace --branch-id br-demo-child
bytedcli --site i18n-tt aidap endpoint list --project-name demo-project --workspace-id demo-workspace --compute-id cp-demo

# 异步操作记录
bytedcli --site i18n-tt aidap operation list --project-name demo-project --workspace-id demo-workspace --action-name CreateBranch

# 执行单条只读 SQL；CLI 自动创建 DAIR DBW session/connection 并轮询结果
bytedcli --site i18n-tt aidap sql execute --workspace-id demo-workspace --branch-id br-demo-main --db-name demo-db --sql 'SELECT 1'
bytedcli --json --site i18n-tt aidap sql execute --workspace-id demo-workspace --branch-id br-demo-main --db-name demo-db --sql-file ./query.sql

# 多行 SQL 必须使用 shell 的 ANSI-C quoting，或优先使用 --sql-file
bytedcli --site i18n-tt aidap sql execute --workspace-id demo-workspace --branch-id br-demo-main --db-name demo-db --sql $'SELECT id, name\nFROM demo_table\nLIMIT 10'
```

## 多行 SQL 换行（必读）

- 正确：使用 `$'SELECT ...\nFROM ...'`，bash/zsh 会把 `\n` 解释为真实换行。
- 正确：把 SQL 写入文件并传 `--sql-file ./query.sql`。
- 错误：不要写 `--sql "SELECT ...\nFROM ..."`；双引号会把 `\n` 原样传给 CLI。

## Command map

| Resource  | Commands                                                                                          |
| --------- | ------------------------------------------------------------------------------------------------- |
| Workspace | `list`, `get`, `create`, `update`, `settings update`, `compute update`, `start`, `stop`, `delete` |
| Branch    | `list`, `get`, `create`, `update`, `execute --operation reset`, `delete`                          |
| Compute   | `list`, `get`, `create`, `name update`, `spec update`, `delete`                                   |
| Account   | `list`, `create`, `password update`, `delete`                                                     |
| Database  | `list`, `create`, `delete`                                                                        |
| Endpoint  | `list`                                                                                            |
| SQL       | `execute`                                                                                         |
| Operation | `list`                                                                                            |

## Agent guidance

- AIDAP 的资源层级是 `Workspace -> Branch -> Compute -> Endpoint`；先解析上层 ID，再调用下层命令。
- `branch create` 不传 `--parent-id` 时会从 Workspace 默认分支派生。涉及重要 Workspace 时显式传父分支 ID，避免选错来源。
- `branch create` 是异步请求。创建后用 `branch get` 或 `operation list --action-name CreateBranch` 轮询，不要连续重复创建。
- 支持服务端分页的列表命令使用 `--page`、`--page-size` 与 `--keyword`；JSON 输出包含 `page`、`page_size`、`total` 和 `has_more`。`compute list` 与 `endpoint list` 由后端一次返回当前资源集合，不提供分页参数。
- 默认分支、受保护分支、有子分支的分支可能禁止 reset/delete。不要为了绕过限制自动关闭保护或改默认分支。
- `workspace create` 固定创建 `PostgreSQL_17`，不会创建 Supabase 或 veDB MySQL Workspace。
- 数据库账号密码优先通过 `AIDAP_DB_PASSWORD` 传入；dry-run 和输出只展示 `<redacted>`。
- 文本模式展示完整资源 ID；脚本和 agent 使用全局 `--json`（放在 `aidap` 前）。
- AIDAP 写请求不会自动重试，收到 RequestId 后先查询操作记录，不要盲目重复提交。
- `sql execute` 当前只在 `--site i18n-tt` 验证，必须同时提供 `--workspace-id`、`--branch-id` 与 `--db-name`；CLI 使用用户 JWT，自动执行 `CreateSession -> CreateConnection -> ExecuteCommandSet -> DescribeCommandSet -> DescribeCommand`，不要手工传浏览器里的 SessionId、ConnectionId、Cookie 或 JWT。
- `sql execute` 只接受一条 PostgreSQL `SELECT` 或 `EXPLAIN SELECT`，并在同一 DBW command set 的 `READ ONLY` 事务内执行；DDL、DML、多语句和数据库写副作用会失败。
- SQL 命令只在 DBW 返回明确成功终态后输出结果。`columns` 是结果表头，`rows` 是数据行；默认和最大 `--limit` 均为 3000，达到上限时 `truncated=true`。文本表格的单元格最多展示 100 个字符，完整单元格值使用全局 `--json`。当前没有完整结果下载接口，需要用 WHERE、LIMIT/OFFSET 等方式缩小或分片查询。
