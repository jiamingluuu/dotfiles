---
name: bytedance-abase
description: "Operate ABase2 via bytedcli: list namespaces, search by PSM, get namespace detail, list/get tables, list supported online-query commands, run online query, inspect ABase regions/locations, list/get ABase classic (1.0) clusters, query/grant/delete/reconcile ACP permissions (SDK runtime auth for PSM or user, with BPM approval tickets), track/approve/reject/cancel/retry ABase BPM tickets, create ABase logical tables on DataLeap (CoralNG ABaseLogicalTable), and list ABase logical tables the current user owns on DataLeap. Use when tasks mention ABase, ABase2, ABase namespace, ABase table, ABase PSM search, ABase online query, ABase ACP permission/authorization, ABase ticket/workflow approval, or creating/searching ABase logical tables on DataLeap. Do not use for Redis/Cache service operations; use bytedance-cache for Redis cache services."
---

# bytedcli ABase

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

- ABase2 namespace 列表、收藏、我的 namespace
- 按 PSM 或 namespace 关键词搜索 ABase2 namespace
- 查看 ABase2 namespace 详情、table 列表、table 详情
- 查看 table 支持的在线查询命令
- 通过 ABase2 online query 执行只读或后端允许的命令
- 查询 ABase region / location 元数据
- 查询 ABase classic（1.0）服务（集群）列表与单集群详情/概要
- 查询 / 新增 / 删除 namespace 的 ACP 鉴权（SDK 运行态授权，PSM 服务账号或用户；删除用 `acp delete`）
- 对账修复某个 namespace 的 ACP 授权（`acp sync`，对应控制台的「一键修复 ACP 授权」）
- 跟进 ABase BPM 工单：列表、详情、查看审批人、审批 / 驳回 / 取消 / 失败重试
- 在 DataLeap 上创建 ABase 逻辑表（CoralNG `management/data-store`，`typeName=ABaseLogicalTable`）
- 在 DataLeap 上按当前登录用户的权限（biowner）搜索 ABase 逻辑表，支持按逻辑表名和物理表名（parentName）模糊过滤

## Do not use

- Redis / Cache 服务搜索、Redis 命令、慢日志、大 Key、热 Key：使用 `bytedance-cache`
- ABase Classic 或非 ABase2 控制台能力
- 无需 bytedcli 的通用 NoSQL 概念解释

## 前置条件

- 使用通用调用方式：`../../invocation.md`
- 需要可用的 ByteCloud 认证；若失败先执行 `bytedcli auth login`

> 执行前缀见 `../../invocation.md`；下面示例直接写 `bytedcli`。

## Quick start

```bash
# namespace 列表与搜索
bytedcli abase list --scope all --keyword "demo.namespace" --limit 20
bytedcli abase search --psm "demo.namespace"
bytedcli abase search --psm "bytedance.abase2.demo_namespace"
bytedcli abase get --psm "demo.namespace"

# 共享控制面：用 --site 选控制面，--region 选具体 deployment
bytedcli --site us-ttp abase get --psm "demo.namespace" --region US-TTP2
bytedcli --site eu-ttp abase get --psm "demo.namespace" --region EU-TTP2
bytedcli --site eu-ttp abase get --psm "demo.namespace" --region US-EastRed
bytedcli --site eu-ttp abase get --psm "demo.namespace" --region EU-Compliance
bytedcli --site eu-ttp abase get --psm "demo.namespace" --region EU-Compliance2
bytedcli --site i18n-tt abase get --psm "demo.namespace" --region Singapore-Central
bytedcli --site i18n-tt abase get --psm "demo.namespace" --region US-East

# table
bytedcli abase table list --psm "demo.namespace"
bytedcli abase table get --psm "demo.namespace" --table "sample_table"

# online query
bytedcli abase command list --psm "demo.namespace" --table "sample_table"
bytedcli abase command list
bytedcli abase command run --psm "demo.namespace" --table "sample_table" --command "GET" --inputs "sample-key"
bytedcli abase command run --cluster "sample-cluster" --namespace "demo_namespace" --table "sample_table" --payload-json '{"command":"GET","inputs":"sample-key"}'

# region / location
bytedcli abase region list
bytedcli abase location list

# classic (1.0) 集群（只读，走网关；--psm 用集群 PSM 而非短名）
bytedcli abase cluster list --keyword demo --limit 20
bytedcli abase cluster get --psm abase_demo_service

# ACP 鉴权：查询已授权列表；新增/删除授权先 --dry-run 预览再 --yes 提交（生成审批工单）
bytedcli abase acp list --namespace "demo_namespace"
bytedcli abase acp add --namespace "demo_namespace" --perm-region "ChinaSinf-North" --psm "demo.service.psm" --perm r --dry-run
bytedcli abase acp add --namespace "demo_namespace" --perm-region "ChinaSinf-North" --psm "demo.service.psm" --perm r --yes
bytedcli abase acp delete --namespace "demo_namespace" --perm-region "ChinaSinf-North" --user "demo-user" --dry-run

# 对账修复该 namespace 的 ACP 授权（对应控制台「一键修复 ACP 授权」）
bytedcli abase acp sync --namespace "demo_namespace" --dry-run

# 工单跟进与审批（approve/reject/cancel 为写操作，同样需要 --dry-run 或 --yes）
bytedcli abase ticket list --namespace "demo_namespace" --creator "demo-user"
bytedcli abase ticket get --id 108000001
bytedcli abase ticket approvers --id 108000001
bytedcli abase ticket approve --id 108000001 --comment "lgtm" --yes
bytedcli abase ticket retry --id 108000001

# 在 DataLeap 上创建 ABase 逻辑表（CoralNG ABaseLogicalTable）
bytedcli abase logic-table create \
  --namespace "demo_namespace" \
  --database "demo_db" \
  --table "demo_table" \
  --column "author_id:BIGINT:author" \
  --column "data_col_type:INT" \
  --column "date:VARCHAR:date" \
  --primary-key "author_id,data_col_type" \
  --key-format 'demo_table:${author_id}:${data_col_type}' \
  -r cn

# 在 DataLeap 上按当前用户权限搜索 ABase 逻辑表（biowner）
bytedcli abase logic-table list --name "demo_tbl" --parent-name "demo_db" -r cn
bytedcli abase logic-table list --page 2 --page-size 10 -r cn
```

## Notes

- 需要结构化输出加 `--json`（全局选项，放在子命令之前，如 `bytedcli --json abase search --psm ...`）。
- 国内生产默认使用 `--site cn`（可省略）；跨站点时用全局 `--site boe|i18n-bd|i18n-tt|us-ttp|eu-ttp`，再用 `--region` 选择共享控制面上的 deployment。
- `us-ttp` 站点由 `US-TTP` 与 `US-TTP2` deployment 共享控制面，`eu-ttp` 站点由 `EU-TTP`、`EU-TTP2`、`US-EastRed`、`EU-Compliance` 与 `EU-Compliance2` deployment 共享控制面。`i18n-tt` 用 `--region Singapore-Central` 或 `--region US-East` 选择 ROW 成员。使用 `--psm` 解析 namespace 时，CLI 会先聚合完整 PSM 与 suffix 的全部精确同名候选，再读取候选详情，并按 `--region` 指定的 deployment 精确筛选。
- `--region US-TTP`、`--region US-TTP2`、`--region EU-TTP`、`--region EU-TTP2`、`--region US-EastRed`、`--region EU-Compliance`、`--region EU-Compliance2`、`--region Singapore-Central` 和 `--region US-East` 是 deployment 选择条件，不是同名 namespace 的跨区域回退条件。指定 deployment 中没有候选时返回 `ABASE_NOT_FOUND`；筛选后仍有多个候选时返回 `ABASE_AMBIGUOUS`，不会接受 ROW/SG 或其他 deployment 的同名 namespace。旧 overlay 简写（如 `us`、`gcp`、`i18n`）不会进入这张表，只回落到当前 `--site` 的 default host，不要用它们选 deployment。
- namespace 详情接口需要 namespace numeric ID；`--psm` 会先搜索并自动解析 ID 与 cluster。
- table 详情接口需要 table numeric ID；`--table` 会先从 table list 中按精确表名解析 ID。
- `query` 默认按 ABase2 前端形态发送 `command` 与 `inputs`；`--payload-json` 会把 JSON object 原样发送到 ABase2 online-query endpoint，适合后端新增命令参数形态时兜底。
- 在 `i18n-tt`（默认/sg）站点，ABase2 的 namespace、table、command、region、location 和 ACP 请求统一通过 ByteCloud gateway；CLI 会自动补齐所需 routing header，用户无需手工传 header。Classic cluster 与 BPM ticket 继续使用各自的 gateway path，DataLeap logic-table 保持独立。
- `abase search --psm` 支持完整 PSM（例如 `bytedance.abase2.demo_namespace`）；首查无结果时会自动按 suffix（例如 `demo_namespace`）重试，短 namespace 也可直接搜索。
- `abase logic-table create` 走 DataLeap CoralNG（不是 ABase2 控制台），用 `-r <region>` 选择 DataLeap 站点（cn / sg / gcp / va / mycis / sglark / jplark / uspipo / mybd / us-ttp / eu-ttp2 / eu-compliance2 / eu-ttp），并要求 `--namespace / --database / --table / --column / --primary-key / --key-format` 全部提供；`--primary-key` 中的列必须先出现在 `--column` 里，`--value-type` 未传时默认为 `general`。
- `abase logic-table create --column` 里的类型是 **ByteSchema 大写枚举**：`INT / BIGINT / VARCHAR / DOUBLE / FLOAT / BOOLEAN / DATE / TIMESTAMP / BINARY`。不要传 Hive/Paimon 风格的小写 `bigint / int / string`——CoralNG 会返回 `校验Schema错误: not find the byteSchemaType, the typeName = bigint`。CLI 端已在 handler 里做归一化与拒识，命中未知类型会返回带 hint 的结构化错误。
- `abase logic-table list` 只列出当前登录用户有权限（`filterMode=biowner`）的 ABase 逻辑表，`--name` / `--parent-name` 为模糊过滤（`parentName` 对应 web 端“物理表名”），`--page` / `--page-size` 走客户端 offset 换算，JSON 返回体保留 `page`、`page_size`、`total`。
- `abase acp add/delete/sync` 与 `abase ticket approve/reject/cancel` 是写操作，必须带 `--dry-run`（仅预览请求）或 `--yes`（执行）之一。授权目标二选一：`--psm`（服务账号）或 `--user`（个人）；`--perm` 取 `r`（只读，默认）或 `rw`（读写）。
- `abase acp sync` 的请求体只有 `{namespace}`（与控制台前端一致，CLI 只发送这一个字段）；与 `acp add/delete` 不同，它不返回工单 id，执行后用 `abase acp list --namespace <ns>` 回读确认实际授权。
- `abase acp add/delete` 用 `--perm-region` 指定授权所属的 ABase 可读 region 名（如 `ChinaSinf-North`），`abase acp list --perm-region` 则按回读到的短名（如 `sinf`）过滤。旧的 `--region` 保留为隐藏兼容别名，新脚本请用 `--perm-region`；其他 abase 命令的 `--region` 是 deployment 选择条件（如 `US-TTP`、`Singapore-Central`），语义不同。
- `abase acp add/delete` 提交成功返回 BPM 工单 id，审批通过后授权才生效，用 `abase ticket get --id <id>` 跟进。
- `abase cluster *` 是 ABase classic（1.0）只读查询，使用其独立的 ByteCloud gateway path；`cluster get --psm` 用集群 **PSM**（如 `abase_demo_service`），不是 `cluster list` 里显示的短名，`--no-summary` 可只取详情跳过概要。
- `abase ticket approvers --id <id>` 展示每个审批阶段的可审批人列表（来自工单 config 的 `assignees_map`），当前阶段列出的任何人都可以审批，不止页面显示的默认处理人。

## References

- `references/abase.md` — ABase2 命令示例与参数说明
- `../../troubleshooting.md` — 常见失败、权限 / 登录、站点选择和命令报错的处理步骤
