# HDFS 资源组（rgroup）

HDFS 资源组是 HDFS 的配额与计费单元。一个资源组关联一组 HDFS 路径，容量、INode 数与
成本都按资源组汇总；成员关系挂在 Galaxy 服务树节点上。

上游没有资源组列表接口，所有命令都必须显式传 `--rgroup`；资源组是 per-region 的，同名组在 Singapore、US-East、US-EastRed-compass、US-EastRed-gcp、US-TTP、EU-TTP2 下内容可能不同。`i18n-tt` 默认查询 Singapore，
US-East 使用全局参数 `--vregion US-East`；`--site eu-ttp --vregion US-EastRed` 是 US-EastRed-compass 的兼容别名，默认选择 Compass（也可显式使用 `US-EastRed-compass`），US-EastRed-gcp 使用 `--site eu-ttp --vregion US-EastRed-gcp`。资源组名可以从 HDFS 控制台 URL、Galaxy 节点名，或 `hdfs path search` 输出末尾的 "Charged to resource group(s)" 拿到。

## `hdfs rgroup get`

查看资源组的归属信息。

```bash
bytedcli --site i18n-tt hdfs rgroup get --rgroup example_rgroup
bytedcli --site i18n-tt --vregion US-East hdfs rgroup get --rgroup example_rgroup
bytedcli --site eu-ttp --vregion US-EastRed hdfs rgroup get --rgroup example_rgroup
bytedcli --site eu-ttp --vregion US-EastRed-gcp hdfs rgroup get --rgroup example_rgroup
bytedcli --json --site i18n-tt hdfs rgroup get --rgroup example_rgroup
```

| 字段                      | 含义                                   |
| ------------------------- | -------------------------------------- |
| `owner`                   | 资源组负责人                           |
| `members`                 | 有权限的成员列表                       |
| `galaxyId` / `galaxyPath` | 对应的 Galaxy 服务树节点 ID 与完整路径 |
| `desc`                    | 资源组描述，常为空                     |

## `hdfs rgroup path list`

查看配额水位，并列出计费到该资源组的路径。

```bash
bytedcli --site i18n-tt hdfs rgroup path list --rgroup example_rgroup
bytedcli --site i18n-tt --vregion US-East hdfs rgroup path list --rgroup example_rgroup
bytedcli --site eu-ttp --vregion US-EastRed hdfs rgroup path list --rgroup example_rgroup
bytedcli --site eu-ttp --vregion US-EastRed-gcp hdfs rgroup path list --rgroup example_rgroup
bytedcli --site i18n-tt hdfs rgroup path list --rgroup example_rgroup --sort inodes --page-size 50
bytedcli --site i18n-tt hdfs rgroup path list --rgroup example_rgroup --sort access
```

选项：

| 选项              | 默认   | 说明                                                            |
| ----------------- | ------ | --------------------------------------------------------------- |
| `--rgroup <name>` | 必填   | 资源组名                                                        |
| `--page <n>`      | `1`    | 页码                                                            |
| `--page-size <n>` | `20`   | 每页路径数；上游一次返回全部路径，分页在客户端按排序结果切片    |
| `--sort <key>`    | `size` | `size`（容量）/ `inodes`（INode 数）/ `access`（近 7 天访问量） |

组级字段：

| 字段                                  | 含义                                                |
| ------------------------------------- | --------------------------------------------------- |
| `size` / `sizeCapacity`               | 已用容量 / 配额容量，文本模式会渲染成百分比水位     |
| `inodes` / `inodesCapacity`           | INode 已用 / 配额；`inodesCapacity` 为 0 表示未设限 |
| `ssdSize` / `ssdSizeCapacity`         | SSD 部分的已用 / 配额                               |
| `accessSizeWeek` / `accessInodesWeek` | 近 7 天被访问的数据量 / INode 数，可用来判断冷热    |
| `costDay`                             | 组级日成本，与控制台一致                            |
| `canAdmin`                            | 当前账号是否有该组的管理权限                        |

路径级字段：

| 字段                        | 含义                                |
| --------------------------- | ----------------------------------- |
| `path`                      | HDFS 绝对路径                       |
| `size`                      | 原始字节数口径的容量                |
| `inodes`                    | INode 数                            |
| `accessSizeWeek`            | 近 7 天访问量                       |
| `storPolicy` / `replicaNum` | 存储策略与副本数，例如 `hotstor x3` |
| `nameNodeCluster`           | 所属 NameNode 集群                  |
| `isAdmin`                   | 当前账号对该路径是否有管理权限      |

## 注意事项

- 路径级 `costDay` 只出现在 `--json` 输出里。上游把它算成原始字节数的固定倍数，既不是
  金额，各路径求和也对不上组级 `costDay`（差约 6e8 倍），因此不渲染成列、也没有
  `--sort cost`。做成本归因请用组级 `costDay`。
- 上游每条路径还带 `Security`（owner、鉴权失败计数）和 `StorHealthy`（SLA、坏块数）两个
  块，但同一资源组下每条路径的值完全相同，是占位数据。bytedcli 不透出这两块。
- `size` 是原始字节数口径，和 `hdfs path search` 的 `Used Size`（含副本）不是同一个数，
  不要跨命令直接相减。
- PB 级数值超过 IEEE754 安全整数范围，属于近似值。
