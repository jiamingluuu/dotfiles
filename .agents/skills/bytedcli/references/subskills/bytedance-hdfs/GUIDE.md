---
name: bytedance-hdfs
description: "Inspect HDFS storage via bytedcli: resource-group quota and ownership, and per-directory size / file-count statistics with day-granularity snapshots. Use when tasks mention HDFS resource groups (rgroup), HDFS quota or capacity, warehouse directory size, file counts, or which directories are consuming storage."
---

# bytedcli HDFS

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

- 查看某个 HDFS 资源组的配额水位（已用 / 容量、INode 数、周访问量）
- 查看资源组的 owner、成员列表与 Galaxy 归属
- 列出计费到某个资源组的所有 HDFS 路径，并按容量、INode 数或周访问量排序
- 查看单个 HDFS 目录的容量、文件数、目录数、副本分布
- 逐层下钻目录（例如按 `date=` / `hour=` 分区）定位容量大头
- 用历史快照对比某个目录的容量增长

## Do not use

- 读写 HDFS 文件内容、上传下载、删除目录：bytedcli 当前只提供只读元信息查询
- 查询 Hive / Paimon / ClickHouse 表的 schema 与血缘：使用 `bytedance-hive`、`bytedance-paimon`
- 查询对象存储 bucket / object：使用 `bytedance-tos`
- 申请扩容或提交工单：当前未接入相关写接口

## 前置条件

- 使用通用调用方式：`../../invocation.md`
- 需要可用的 ByteCloud 认证；若失败先执行 `bytedcli auth login`
- **必须显式指定 `--site`**。支持 `i18n-tt`、`us-ttp`、`eu-ttp`；`cn` / `i18n-bd` 等其余站点会直接报 `HDFS_SITE_UNSUPPORTED`
- `i18n-tt` 默认查询 Singapore；查询 US-East 时使用全局参数 `--vregion US-East`。`--site eu-ttp --vregion US-EastRed` 是兼容别名，默认查询 US-EastRed-compass（也可显式使用 `US-EastRed-compass`）；US-EastRed-gcp 使用 `--site eu-ttp --vregion US-EastRed-gcp`
- **每个站点要单独登录**：`bytedcli --site <site> auth login`。Singapore 与 US-East 同属 `i18n-tt`，两个 US-EastRed plane 都使用 `eu-ttp` 登录态
- 没有 HDFS 专属的 `--region` 参数；同一站点下的 region 用全局 `--vregion` 选择
- 上游没有资源组列表接口，所有资源组命令都必须显式传 `--rgroup`

> 执行前缀见 `../../invocation.md`；下面示例直接写 `bytedcli`。

## Quick start

```bash
# 资源组归属：owner、成员、Galaxy 路径
bytedcli --site i18n-tt hdfs rgroup get --rgroup example_rgroup

# 查询 US-East：与 Singapore 共用 i18n-tt host，但 HDFS 内部路由键不同
bytedcli --site i18n-tt --vregion US-East hdfs rgroup get --rgroup example_rgroup

# 查询 US-EastRed-compass：US-EastRed 兼容别名默认选择 Compass
bytedcli --site eu-ttp --vregion US-EastRed hdfs rgroup get --rgroup example_rgroup

# 查询 US-EastRed-gcp
bytedcli --site eu-ttp --vregion US-EastRed-gcp hdfs rgroup get --rgroup example_rgroup

# US-TTP / EU-TTP2 是另外的独立部署
bytedcli --site us-ttp hdfs rgroup get --rgroup example_rgroup
bytedcli --site eu-ttp hdfs rgroup get --rgroup example_rgroup

# 资源组配额水位 + 计费到该组的路径（默认按容量降序，取前 20 条）
bytedcli --site i18n-tt hdfs rgroup path list --rgroup example_rgroup
bytedcli --site i18n-tt hdfs rgroup path list --rgroup example_rgroup --sort inodes --page-size 50
bytedcli --site i18n-tt hdfs rgroup path list --rgroup example_rgroup --sort access

# 单个目录的统计信息 + 直接子目录（按容量降序）
bytedcli --site i18n-tt hdfs path search --path /home/example-rgroup/warehouse

# 下钻到分区
bytedcli --site i18n-tt hdfs path search --path /home/example-rgroup/warehouse/date=20240131

# 指定历史快照做容量对比
bytedcli --site i18n-tt hdfs path search --path /home/example-rgroup/warehouse --date 20240101

# 子目录很多时翻页
bytedcli --site i18n-tt hdfs path search --path /home/example-rgroup/warehouse --page 2 --page-size 50

# 结构化输出
bytedcli --json --site i18n-tt hdfs rgroup path list --rgroup example_rgroup
bytedcli --json --site i18n-tt hdfs path search --path /home/example-rgroup/warehouse
```

## Agent Guidance

### 快照日期（必读）

HDFS 目录统计是**按天的快照**，且第 D 天的快照要到第 D+1 天中途才可查。

- 不传 `--date` 时，bytedcli 会从最近一天往前探最多 3 天，用第一个已产出的快照，并在文本输出里明确提示实际用的是哪天（JSON 里对应 `date` / `snapshot_fell_back` / `attempted_dates`）。**不要自己算"昨天"再传进去**，不同时区算出来的结果不一样。
- 传了 `--date` 就不会回退。此时 `path not found` 有三种可能：路径不存在、当天快照还没产出、该日期已过保留期。排查顺序是先不带 `--date` 重试一次，再用 `hdfs rgroup path list` 确认路径确实存在。

### 机房是彼此独立的

Singapore、US-East、US-EastRed-compass、US-EastRed-gcp、US-TTP、EU-TTP2 是彼此独立的 HDFS
region。同名资源组在不同 region 下的成员、路径和容量都可能不同，**跨 region 的数字不要相加，也不要
拿一个 region 的结论推另一个**。`i18n-tt` 默认是 Singapore，US-East 必须显式带 `--vregion US-East`；
`--site eu-ttp --vregion US-EastRed` 是 US-EastRed-compass 的兼容别名；也可显式使用
`US-EastRed-compass`。US-EastRed-gcp 使用 `--site eu-ttp --vregion US-EastRed-gcp`。回答容量问题时先确认 region；没说清就分别查询并标注。

### 路径格式

`--path` 必须是绝对路径且结尾不能带 `/`，否则 bytedcli 在本地就会拦下并给出修正后的命令。

### 容量字段怎么读

- `path search` 的 `Used Size` 是**含副本**的实际占用，`Logical Size` 是逻辑大小；两者可能差 2~3 倍，讨论"这个目录多大"时先说清用的是哪个口径。
- `rgroup path list` 里的 `Size` 是原始字节数口径，和 `path search` 的 `Used Size` 不是同一个数，不要跨命令直接相减。
- PB 级数值超过 IEEE754 安全整数范围，只能当近似值用，不要做精确求和校验。

### 已知的上游数据问题

- 每条路径的 `Security`（owner、鉴权失败计数）和 `StorHealthy`（SLA、坏块数）在同一资源组下**每条路径都是同一份占位数据**，不是真实值。bytedcli 不透出这两块，也不要绕过 CLI 直接取来做告警。
- 路径级 `costDay` 只在 `--json` 里保留。它是按原始字节数线性缩放的 `size` 副本，既不是金额，各路径求和也对不上组级 `Cost / Day`；不要拿它做成本归因，也没有 `--sort cost`。

### 排查容量大头的推荐路径

1. `hdfs rgroup path list --rgroup <name>` 看配额水位，定位最大的几条路径。
2. 对最大的路径跑 `hdfs path search --path <path>`，看直接子目录排序。
3. 沿最大的子目录继续 `path search` 下钻，直到定位到具体分区。
4. 需要看增长时，对同一路径分别用两个 `--date` 各跑一次再比较。

## References

- `references/rgroup.md` — 资源组配额、成员与路径清单命令说明，以及字段含义
- `references/path.md` — 目录统计与下钻命令说明，快照日期语义与常见报错
