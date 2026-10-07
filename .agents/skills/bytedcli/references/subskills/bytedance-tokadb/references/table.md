# TokaDB Table

TokaDB table 是 TokaDB 中承载业务数据的宽表资源，通常归属于某个 cluster 和 database。table 元信息包含表名、database、表类型、schema、列族、TTL、多 AZ 拓扑和权限可见性等内容。Agent 需要回答“这个 cluster 里有哪些表”“某张表的 schema 是什么样”“列族和 TTL 怎么配置”“table 位于哪个 cluster/database”时，优先使用 `bytedcli tokadb table`。

## 常用命令

```bash
# 列出指定 cluster 下的 table
bytedcli tokadb table list --region cn --cluster "sample-cluster" --page-size 20

# 按关键词模糊搜索 table
bytedcli tokadb table list --region cn --keyword "sample_table"

# 跨 region 搜索 table（--all-regions 与 --region 互斥）
bytedcli tokadb table list --all-regions --keyword "sample_table"

# 仅看自己是 Owner / 管理员或 Owner 的表
bytedcli tokadb table list --region cn --scope owner

# 查看 USTTP / EUTTP 表元信息（需要独立 TTP 站点授权）
bytedcli tokadb table list --region usttp --page 1 --page-size 20
bytedcli tokadb table list --region euttp --page 1 --page-size 20

# 查看单表详情与 schema（<id> 是位置参数）
bytedcli tokadb table describe --region cn 12345

# 按 row-key 精确只读探查
bytedcli --json tokadb table lookup --region boe --cluster "sample-cluster" --database "sample_db" --table-name "sample_table" --cf "cf1" --row-key "sample-rowkey"

# 按 row-key prefix 只读扫描
bytedcli --json tokadb table scan --region boe --cluster "sample-cluster" --database "sample_db" --table-name "sample_table" --cf "cf1" --prefix "sample-prefix" --limit 20

# 输出 JSON 供脚本处理
bytedcli --json tokadb table describe --region cn 12345
```

## 参数说明

- `--region` 默认是 `cn`，支持 `cn`、`boe`、`boei18n`、`i18ntt`、`i18nbd`、`usttp`、`euttp`。
- `usttp` / `euttp` 是正式支持的控制面元信息 Region，但使用独立 ByteCloud Auth 凭证；缺凭证时分别运行 `bytedcli --site us-ttp auth login` / `bytedcli --site eu-ttp auth login`。
- `--all-regions` 一次性并行查询所有受支持 region；与 `--region` 互斥，没有 `--region all` 的写法。
- `--cluster` 用于限定 table 所属 cluster（传集群名或 ID）；已知 cluster 时建议显式传入。
- `--name` 对表名做精确匹配；`--keyword` 做模糊搜索，适合先搜索再确定表 ID。
- `--scope` 控制可见性范围：`all`（默认）/ `owner` / `admin-or-owner`，取代旧的 `--owner` / `--admin-or-owner` 布尔 flag。
- `--has-data-query-permission` 仅返回具备 data_query 权限的表。
- 元信息 `table list` 用 `--page` / `--page-size` 控制分页（不存在 `--limit`）。
- `table describe` 的表标识是位置参数 `<id>`，传表 ID，不要写成 `--cluster` / `--database` / `--table`。
- `table lookup` / `table scan` 是只读数据探查命令；必须显式传 `--cluster`、`--database`、`--table-name`。当前数据探查 region 只支持 `cn` 和 `boe`。
- `table lookup` 额外要求标准 flag `--row-key`；`table scan` 额外要求非空 `--prefix`。
- `table scan --limit` 默认 20、最大 200，只属于数据探查 scan，不用于元信息 list。
- `--cf` 指定 column family，例如 `cf1`。不要把 column qualifier 当作 CF，也不要添加 `--cq`；响应中返回的 qualifier 会在结果列 `CQ` 里展示。
- 数据探查底层使用 cncp BFF `data_query` 只读接口（Lookup / Scan）；后端会按服务配置遍历 VDC，命令只需 region、cluster、database 与 table 入参。

## 字段理解

- `cluster`：table 所在 cluster，后续详情查询与 region 一起匹配。
- `database`：table 所在 database，用于区分同一 cluster 内不同业务域。
- `name` / `id`：table 名称与 ID，`describe` 查询用 `<id>` 定位。
- `tableType`：表类型，反映后端存储或兼容模型。
- `state`：表当前状态。

## 使用建议

如果只知道表名，先用 `table list --keyword` 搜索并记录返回的 `region`、`cluster`、`id`。随后用 `table describe <id>` 精确查看 schema 和列族。脚本消费时使用 `bytedcli --json tokadb ...`，不要从文本表格中解析字段。

做数据探查前，建议先用 `table describe` 确认真实 column family；lookup/scan 只读，不支持也不应尝试 put/delete/mutate 等写操作。

需要交付 Owner table 全量盘点、关联 cluster、Markdown 或飞书文档时，不要逐页调用 `table list --scope owner` 后手工整理；直接使用 `bytedcli tokadb report [--output <path>] [--feishu-doc]`，标准版式见 `references/report.md`。默认 report 会尝试包含 USTTP / EUTTP，只有用户明确要求临时跳过时才使用 `--exclude-regions`。
