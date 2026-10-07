# ByteDoc 集群水位巡检指南

当任务涉及 ByteDoc **classic** 集群的拓扑查询、水位巡检 / 资源体检时使用本指南，覆盖
CPU、config server CPU/连接数、QPS、mongos 连接数、IO、mongod cache 带宽、
磁盘、文档大小。既可以只查其中一项，也可以一次性做整体水位巡检。

## 适用范围

- **仅支持 classic 后端。** cloud-native / volc 集群不支持本命令。
- 目标可用 `--cluster <数值集群 id>`（如 `240085`）或 `--service <classic PSM>`
  指定；给 `--service` 时 CLI 会解析出 classic 集群 id。
- 数据来自 ByteTSD（同 Grafana 集群监控大盘），按 **节点 / 分片** 展开。
- 时间窗默认 `1h`，取每个节点窗口内的 `max`（可用 `--agg avg` 改成均值）。

## 命令

`bytedoc inspect cluster get` 从监控指标解析副本集成员、primary、复制延迟和
config server 拓扑：

```bash
bytedcli --json --site cn bytedoc inspect cluster get --cluster 240085
bytedcli --json --site cn bytedoc inspect cluster get --service "example.bytedoc.demo_orders" --backend classic --window 20m
```

统一入口是 `bytedoc inspect cluster check`；用 `--metric` 选择巡检目标
（单项 metric，或 `all` 整体，默认 `all`）。

```bash
# 单项：CPU（按 mongod 节点展开：used %（100%=1核）、分配用量 %）
bytedcli --json --site cn bytedoc inspect cluster check --cluster 240085 --metric cpu

# 单项：config server CPU（按 config 节点展开）
bytedcli --json --site cn bytedoc inspect cluster check --cluster 240085 --metric config-cpu

# 单项：config server 当前连接数
bytedcli --json --site cn bytedoc inspect cluster check --cluster 240085 --metric config-connections

# 单项：QPS（mongod operations，按节点 ops/s）
bytedcli --json --site cn bytedoc inspect cluster check --cluster 240085 --metric qps

# 单项：mongos 当前连接数
bytedcli --json --site cn bytedoc inspect cluster check --cluster 240085 --metric mongos-connections

# 单项：IO（WiredTiger 读写盘 / 写 log 带宽、可用读写并发 tickets）
bytedcli --json --site cn bytedoc inspect cluster check --cluster 240085 --metric io

# 单项：mongod WiredTiger cache read/write 带宽
bytedcli --json --site cn bytedoc inspect cluster check --cluster 240085 --metric cache-bandwidth

# 单项：磁盘（按 shard 使用率 %、剩余可用小时数）
bytedcli --json --site cn bytedoc inspect cluster check --cluster 240085 --metric disk

# 单项：文档大小（按 database 存储大小 / 文档数 / 平均文档大小）
bytedcli --json --site cn bytedoc inspect cluster check --cluster 240085 --metric doc-size

# 整体水位巡检：逐项跑上面五项并给出 overallLevel（--metric all 为默认，可省略）
bytedcli --json --site cn bytedoc inspect cluster check --cluster 240085

# 用 service（PSM）代替 cluster id：CLI 解析出 classic 集群
bytedcli --json --site cn bytedoc inspect cluster check --service "example.bytedoc.demo_orders" --backend classic

# 自定义时间窗与聚合方式
bytedcli --json --site cn bytedoc inspect cluster check --cluster 240085 --metric cpu --window 2h --agg avg

# 覆盖该项阈值（应用到所选 metric 的所有子指标）
bytedcli --json --site cn bytedoc inspect cluster check --cluster 240085 --metric disk --warn 75 --crit 90

# 手动指定 ByteTSD region（默认自动探测；跨 region 或探测失败时使用）
bytedcli --json --site cn bytedoc inspect cluster check --cluster 240085 --metric cpu --region China-East
```

## 参数说明

- `--metric <metric>`：巡检目标，支持 `cpu` / `config-cpu` /
  `config-connections` / `qps` / `mongos-connections` / `io` /
  `cache-bandwidth` / `disk` / `doc-size` 单项，或 `all` 整体，默认 `all`。
- `--cluster <id>`：数值 classic 集群 id（与监控大盘 `var-Cluster` 一致）。
- `--service <psm>`：classic 服务 PSM；与 `--cluster` 二选一。
- `--backend <backend>`：解析 `--service` 时消歧，固定 classic。
- `--region <region>`：ByteTSD region 覆盖，默认按集群自动探测（CN 候选含
  `China-East`、`China-North`、`China-Aggregation`、`Aliyun_NC2`）。
- `--window <duration>`：回看窗口，如 `1h`、`30m`、`2h`、`900s`，默认 `1h`。
- `--agg <max|avg>`：分级采用的代表值，默认 `max`（看峰值）。
- `--warn <value>` / `--crit <value>`：覆盖所选 metric 的默认阈值。

`cluster get` 使用相同的目标和 region 参数，`--window` 默认 `10m`；JSON 输出
包含 `replicaSets[]`、`shards[]`、`configServer` 和 `warnings[]`。只有最新指标
中恰好存在一个 primary 时才返回该副本集的 `primary`，否则为 `null` 并附 warning。

## 内置默认阈值（可被 --warn/--crit 覆盖）

阈值对齐 ByteDoc 长稳沟通文档的建议水位。

| 子指标                                                       | 默认 warn | 默认 crit | 方向       |
| ------------------------------------------------------------ | --------- | --------- | ---------- |
| CPU 分配用量 %（allocated_cpu_percent）                      | 30        | 50        | 越高越危险 |
| config server CPU 分配用量 %（config_allocated_cpu_percent） | 30        | 50        | 越高越危险 |
| 磁盘使用率 %（cluster_used_percent）                         | 60        | 80        | 越高越危险 |
| cache 盘读写带宽（block_manager_bytes）                      | 300MB/s   | —         | 越高越危险 |
| log 盘写带宽（log_bytes）                                    | 15MB/s    | —         | 越高越危险 |
| 分片剩余可用小时（shard_remain_hours）                       | 720       | 168       | 越低越危险 |
| WiredTiger 可用 tickets（available_tickets）                 | 64        | 12        | 越低越危险 |

> `allocated_cpu_percent` 上游返回 0~1 的占用比例，CLI 已 ×100 归一为百分数，
> 与文档「CPU 使用率建议 < 30%」同口径。

其余子指标（CPU used %、operations QPS、文档大小/数量）默认为纯观测，
`level` 返回 `unknown`，仅展示原始 max/avg/last。

新增观测项说明：

- `config-cpu` 复用 CPU 指标并按 `role=config` 过滤。
- `config-connections` 查询 config server 当前连接数。
- `mongos-connections` 查询 mongos 当前连接数。
- `cache-bandwidth` 查询 mongod WiredTiger cache read/write bytes rate；它是 cache
  层读写带宽，不等同于上面 `io` 中的物理 cache/log 盘 IO 阈值。

## 输出结构（JSON）

- 单项：`{ item, clusterId, region, service?, window, subMetrics[], level }`。
  - 每个 `subMetric`：`{ key, label, unit, metric, threshold, nodes[], level }`。
  - 每个 `node`：`{ name, tags, max, avg, last, points, level }`。
- 聚合 `all`：`{ clusterId, region, window, items[], overallLevel }`；`overallLevel`
  取所有项里最严重的分级（critical > warning > healthy > unknown）。

## Agent Guidance

- 只查某一项时用 `--metric cpu|config-cpu|config-connections|qps|mongos-connections|io|cache-bandwidth|disk|doc-size`；要整体水位体检就用默认的 `--metric all`（或省略 `--metric`）。
- 若返回 `BYTEDOC_METRICS_REGION_NOT_FOUND`，说明按集群 id 没在 CN 候选 region
  里探到数据：确认 cluster id 是否正确，或用 `--region` 显式指定 ByteTSD region。
- 若返回 `BYTEDOC_INSPECT_NOT_CLASSIC` / `BYTEDOC_METRICS_UNSUPPORTED_SITE`，
  说明目标不是 classic 或站点非 cn；本命令只支持 `--site cn` 的 classic 集群。
- 水位关注单机峰值，默认 `--agg max` 已按节点展开；需要看均值再切 `--agg avg`。
