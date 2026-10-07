---
name: bytedance-tokadb
description: "Operate TokaDB via bytedcli: owner reports, metadata, read-only probes, and route CF-creation or table-disable ticket workflows. Use for TokaDB assets, tables, probes, or CF/disable-table tickets."
---

# bytedcli TokaDB

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

## When to use

- 列出当前账号在指定 TokaDB region 下可见的 cluster
- 查看 TokaDB cluster 详情、负责人、服务等级、共享集群标记与拓扑信息
- 按 cluster/database/table 维度列出 TokaDB table
- 查看 TokaDB table 的 schema、列族、TTL、表类型、多 AZ 拓扑等元信息
- 盘点当前账号作为 Owner 的全部 table 及其关联 cluster
- 将 Owner 资产盘点生成本地 Markdown 或飞书文档
- 查询 USTTP / EUTTP 等 TTP 区域的 TokaDB cluster/table 元信息
- 按显式 row-key 做只读 lookup 数据探查
- 按 row-key prefix 做只读 scan 数据探查
- 需要跨 region 只读盘点 TokaDB cluster 或 table 元数据
- 在已存在的 TokaDB 表上提交新建 CF 工单，或提交禁用表工单时，读取 `references/ticket.md`

## Do not use

- 执行 SQL、分析 Hive 表或离线数据任务：使用 `bytedance-tqs`、`bytedance-hive`、`bytedance-dorado` 等对应 skill
- 查询 RDS、ByteDoc、ABase、Redis、MemoryBase 等非 TokaDB 平台资源
- 直接写入、建表、删表、迁移或绕过 BPM 的 TokaDB 变更操作；创建 CF 只能通过 `tokadb ticket cf create`、禁用表只能通过 `tokadb ticket table disable` 的工单路径，字段规则见 `references/ticket.md`。当前仅开放这两类工单，不要提交其他类型工单。

## 前置条件

- 使用通用调用方式：`../../invocation.md`
- 需要可用的 ByteCloud 认证；若失败先执行 `bytedcli auth login`
- TokaDB Web 会话可能按站点隔离；跨 region 查询失败时按提示登录对应站点

> 执行前缀见 `../../invocation.md`；下面示例直接写 `bytedcli`。

## Quick start

```bash
# Owner 资产盘点（默认跨 Region）
bytedcli tokadb report
bytedcli tokadb report --output ./tokadb-owner-inventory.md
bytedcli tokadb report --feishu-doc

# cluster 元信息
bytedcli tokadb cluster list --region cn --page-size 20
bytedcli tokadb cluster list --all-regions --keyword "sample-cluster"
bytedcli tokadb cluster list --region cn --scope owner-or-common
bytedcli tokadb cluster list --region usttp --page-size 20
bytedcli tokadb cluster list --region euttp --page-size 20
bytedcli tokadb cluster get --region cn "sample-cluster"

# table 元信息
bytedcli tokadb table list --region cn --cluster "sample-cluster" --page-size 20
bytedcli tokadb table list --all-regions --keyword "sample_table"
bytedcli tokadb table list --region cn --scope owner
bytedcli tokadb table list --region usttp --page 1 --page-size 20
bytedcli tokadb table list --region euttp --page 1 --page-size 20
bytedcli tokadb table describe --region cn 12345

# 数据探查（只读）
bytedcli --json tokadb table lookup --region boe --cluster "sample-cluster" --database "sample_db" --table-name "sample_table" --cf "cf1" --row-key "sample-rowkey"
bytedcli --json tokadb table scan --region boe --cluster "sample-cluster" --database "sample_db" --table-name "sample_table" --cf "cf1" --prefix "sample-prefix" --limit 20

# 创建 CF 工单（默认 dry-run；完整流程见 references/ticket.md）
bytedcli tokadb ticket cf create --region cn --cluster "sample-cluster" --database "sample_db" --table-name "sample_table" --cf "cf1:1" --dry-run

# 禁用表工单（默认 dry-run；完整流程见 references/ticket.md）
bytedcli tokadb ticket table disable --region cn --cluster "sample-cluster" --database "sample_db" --table-name "sample_table" --dry-run

# 结构化输出
bytedcli --json tokadb cluster list --region cn --page-size 20
bytedcli --json tokadb table describe --region cn 12345
```

## Notes

- 用户要求“我的全部 TokaDB 表/集群”“Owner 资产盘点”“生成 Markdown/飞书文档”时，必须优先使用 `tokadb report`，不要分别调用 list 命令后手工拼接文档。
- `tokadb report` 的 Owner 口径来自 `tables?is_owner=true`；Cluster 只包含这些 Owner 表实际关联的集群，不等同于 `cluster list --scope owner-or-common`。
- `--feishu-doc` 直接使用命令内置模板创建飞书文档；不要让 Agent 重新编排 Markdown。未传 `--doc-title` 时使用标准标题 `TokaDB Owner 资产盘点 · YYYY-MM-DD`。
- 报告固定使用精简表格布局：核心概览 → Region 覆盖 → 全局 Cluster 清单 → 按 Region 分组的 Table 清单 → 数据限制。正文表格保持 5-7 列，不输出每个 Region 的重复 KPI，也不展示 ID、更新时间和原始错误等低频字段。
- Cluster 和 DB.Table 名称优先承载监控链接；完整字段保留在 `--json` 输出，不要为了“全面”把所有字段塞回飞书正文。
- `--exclude-regions <region,...>` 在查询前排除 Region，并同步影响统计、正文、失败详情与登录提示。它是显式配置，不改变默认全 Region 语义。
- 元信息 list/get 命令的 `--region` 默认是 `cn`；`tokadb report` 未显式传 `--region` 时默认跨全部支持 Region。
- 需要让元信息 list 命令跨站点查询时使用 `--all-regions`（与 `--region` 互斥，不存在 `--region all` 这种写法）。
- 支持的 region 为 `cn`、`boe`、`boei18n`、`i18ntt`、`i18nbd`、`usttp`、`euttp`；不要传旧别名或站点域名。
- `usttp` / `euttp` 是正式支持的控制面元信息和 Owner report Region，缺凭证时分别运行 `bytedcli --site us-ttp auth login` / `bytedcli --site eu-ttp auth login`；不要默认通过 `--exclude-regions` 跳过 TTP 区域。
- `cn_test` 是独立 CN 测试后端，只在显式传 `--region cn_test` 时使用，不纳入默认 `--all-regions` / report。
- TTP 控制面请求应发送 `x-og-common-path-mode: true`，但不发送 `x-bcgw-tenant-id`；若 `usttp` / `euttp` 已登录仍出现 `HTTP 403` 且包含 `invalid tagging: header` / `X-Bcgw-Tenant-Id`，优先检查 `src/api/tokadb/site.ts` 路由 header 配置，不要让用户重复登录。
- 元信息列表命令通过 `--keyword` 做模糊搜索、`--name` 做精确匹配，用 `--page` / `--page-size` 翻页（不存在 `--limit`）。
- 可见性范围统一用 `--scope` 枚举：cluster 支持 `all`（默认）/ `owner` / `owner-or-common`，table 支持 `all`（默认）/ `owner` / `admin-or-owner`；不存在 `--owner` / `--owner-or-common` / `--admin-or-owner` 这些布尔 flag。
- `table list` 额外支持 `--cluster`（按集群名/ID 过滤）与 `--has-data-query-permission`；不存在 `--database` / `--table` flag。
- `cluster get <id_or_name>` 与 `table describe <id>` 的标识都是位置参数，不要写成 `--cluster` / `--database` / `--table`。
- `table lookup` / `table scan` 是只读数据探查；必须显式传 `--cluster`、`--database`、`--table-name`。数据探查当前只支持 `--region cn` / `boe`。
- `table lookup` 用标准 flag `--row-key` 精确读取一行；`table scan` 用 `--prefix` 扫描 row-key prefix，`--limit` 默认 20、最大 200。`--limit` 只属于 data probe scan，不属于元信息 list。
- 列族过滤只使用 `--cf`。不要把 column qualifier 当成 CF，也不要自行添加 `--cq`；结果展示里会显示返回 cell 的 `CQ`。
- 数据探查底层走 cncp BFF `data_query` 只读接口（Lookup / Scan），后端会按服务配置遍历 VDC，命令只需 region、cluster、database 与 table 入参。
- `tokadb ticket cf create` 是受控工单创建命令，不直接创建 CF。它默认只 dry-run，必须显式 `--yes` 才会 POST `/tickets/create_column_family` 创建 BPM 工单。字段收集规则见 `references/ticket.md`。
- 创建 CF 工单必须收集 `--cluster`、`--database`、`--table-name`、至少一个 `--cf <name:max_version>`，并明确确认每个 CF 的 `attributes` 与 `storage_attributes`；没有高级属性时也要确认为空数组，不要猜测。
- `tokadb ticket table disable` 是受控禁用表工单命令，不直接禁用表。它默认 dry-run，必须显式 `--yes` 才会 POST `/tickets/disable_table` 创建 BPM 工单，只需 `--cluster`、`--database`、`--table-name` 三个字段。当前 tokadb 只开放创建 CF 与禁用表两类工单。
- `-j/--json` 是全局选项，放在 `tokadb` 之前；JSON 模式只输出结构化 JSON，适合脚本消费。
- `--all-regions` 会逐 region 查询并汇总；部分 region 鉴权失败时，文本模式会提示对应登录站点，JSON 模式会在错误列表中保留 region 维度。

## References

- `references/report.md` — Owner 资产盘点、飞书文档调用、固定版式与验收标准
- `references/cluster.md` — TokaDB cluster 概念、常用字段与 cluster 命令说明
- `references/table.md` — TokaDB table 概念、常用字段与 table 命令说明
- `references/ticket.md` — 创建 CF、禁用表两类受控 BPM 工单的字段清单、dry-run/`--yes` 流程与红线
- `../../troubleshooting.md` — 常见失败、权限 / 登录、站点选择和命令报错的处理步骤
