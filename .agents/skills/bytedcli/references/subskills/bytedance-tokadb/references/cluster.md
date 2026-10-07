# TokaDB Cluster

TokaDB cluster 是 TokaDB 资源管理与访问路由的基础单元，用来承载一组 table，并关联所属 region、负责人、服务等级、共享集群标记和多 AZ 拓扑等元信息。Agent 需要回答“我有哪些 TokaDB 集群”“这个集群属于哪个 region”“这个 cluster 是否是共享集群”“集群详情里有哪些拓扑信息”时，优先使用 `bytedcli tokadb cluster`。

## 常用命令

```bash
# 列出指定 region 下可见 cluster
bytedcli tokadb cluster list --region cn --page-size 20

# 跨 region 汇总查询（--all-regions 与 --region 互斥）
bytedcli tokadb cluster list --all-regions --keyword "sample-cluster"

# 仅看自己是 Owner / Owner 或共享的集群
bytedcli tokadb cluster list --region cn --scope owner-or-common

# 查看 USTTP / EUTTP 集群（需要独立 TTP 站点授权）
bytedcli tokadb cluster list --region usttp --page-size 20
bytedcli tokadb cluster list --region euttp --page-size 20

# 查看单个 cluster 详情（<id_or_name> 是位置参数）
bytedcli tokadb cluster get --region cn "sample-cluster"

# 输出 JSON 供脚本处理
bytedcli --json tokadb cluster get --region cn "sample-cluster"
```

## 参数说明

- `--region` 默认是 `cn`，支持 `cn`、`boe`、`boei18n`、`i18ntt`、`i18nbd`、`usttp`、`euttp`。
- `usttp` / `euttp` 是正式支持的控制面元信息 Region，但使用独立 ByteCloud Auth 凭证；缺凭证时分别运行 `bytedcli --site us-ttp auth login` / `bytedcli --site eu-ttp auth login`。
- `--all-regions` 一次性并行查询所有受支持 region；与 `--region` 互斥，没有 `--region all` 的写法。
- `--keyword` 用于列表结果模糊搜索，适合不知道完整 cluster 名时先搜索；`--name` 做精确匹配。
- `--scope` 控制可见性范围：`all`（默认）/ `owner` / `owner-or-common`，取代旧的 `--owner` / `--owner-or-common` 布尔 flag。
- `--page` / `--page-size` 控制分页（不存在 `--limit`）。
- `cluster get` 的集群标识是位置参数 `<id_or_name>`，直接传 ID 或名称，不要写成 `--cluster`。

## 字段理解

- `name` / `id`：cluster 名称与 ID，是后续 table list 或 table describe 的上游定位条件。
- `region`：cluster 所属 TokaDB region，决定请求路由、登录站点与权限边界。
- `isCommon`：是否为共享集群；共享集群通常承载多个业务方的 table。
- `state`：集群当前状态。
- `grafana`：集群监控面板链接（详情中返回）。

## 使用建议

先用 `cluster list` 缩小 region 与 cluster 范围，再用 `cluster get <id_or_name>` 查看详情。需要继续查看表信息时，把 cluster 名传给 `tokadb table list --cluster`。如果 `--all-regions` 只有部分 region 失败，优先保留成功结果，再根据输出中的登录提示补齐对应站点认证。

需要交付“我作为 Owner 的全部 table 及其关联 cluster”清单、Markdown 或飞书文档时，不要用 `cluster list` 手工拼接；直接使用 `bytedcli tokadb report [--output <path>] [--feishu-doc]`，标准版式见 `references/report.md`。
