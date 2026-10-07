# HDFS 目录统计（path search）

`hdfs path search` 返回一个 HDFS 目录的聚合统计，加上它的直接子目录（按含副本容量降序）。
反复对最大的子目录再跑一次，就能逐层下钻定位容量大头。

```bash
# 顶层目录（Singapore）
bytedcli --site i18n-tt hdfs path search --path /home/example-rgroup/warehouse

# US-East
bytedcli --site i18n-tt --vregion US-East hdfs path search --path /home/example-rgroup/warehouse

# US-EastRed-compass：US-EastRed 兼容别名默认选择 Compass
bytedcli --site eu-ttp --vregion US-EastRed hdfs path search --path /home/example-rgroup/warehouse

# US-EastRed-gcp
bytedcli --site eu-ttp --vregion US-EastRed-gcp hdfs path search --path /home/example-rgroup/warehouse

# 下钻到日期分区
bytedcli --site i18n-tt hdfs path search --path /home/example-rgroup/warehouse/date=20240131

# 再下钻到小时分区
bytedcli --site i18n-tt hdfs path search --path /home/example-rgroup/warehouse/date=20240131/hour=13

# 子目录多时翻页
bytedcli --site i18n-tt hdfs path search --path /home/example-rgroup/warehouse --page 2 --page-size 50

# 指定历史快照
bytedcli --site i18n-tt hdfs path search --path /home/example-rgroup/warehouse --date 20240101
```

## 选项

| 选项                | 默认 | 说明                                       |
| ------------------- | ---- | ------------------------------------------ |
| `--path <path>`     | 必填 | 绝对路径，结尾不能带 `/`                   |
| `--date <YYYYMMDD>` | 自动 | 快照日期；省略时自动选最近一个已产出的快照 |
| `--page <n>`        | `1`  | 子目录页码                                 |
| `--page-size <n>`   | `20` | 每页子目录数                               |

## 字段

汇总（`summary`）：

| 字段                              | 含义                                                           |
| --------------------------------- | -------------------------------------------------------------- |
| `usedSize` / `usedSizeReadable`   | **含副本**的实际磁盘占用                                       |
| `size`                            | 逻辑大小（不含副本）                                           |
| `fileNum` / `dirNum` / `blockNum` | 文件数 / 目录数 / block 数                                     |
| `accessTime`                      | 最近访问时间                                                   |
| `replicaDist`                     | 按存储策略拆分的容量分布，例如 `2` / `3` 副本与 `COOL@V2` 冷存 |

子目录（`children`）字段与 summary 相同，按 `usedSize` 降序。`childrenCount` 是子目录
总数，`inEachRgroup` 说明该路径计费到哪些资源组。

## 快照日期语义（重要）

HDFS 目录统计是按天产出的快照，**第 D 天的快照要到第 D+1 天中途才可查**。

- 不传 `--date`：bytedcli 从最近一天往前依次探最多 3 天，用第一个能返回的快照。文本模式
  会打印 `Snapshot <date> is not published yet; showing <date> instead.`，JSON 模式对应
  `date`（实际使用）、`snapshot_fell_back`、`attempted_dates`。
  **不要自己算"昨天"再传进去** —— 不同时区算出来的日期不一样，容易撞上还没产出的快照。
- 传了 `--date`：不做任何回退，那天没有就直接报错。
- 历史快照有保留期，实测约一年内可查，更早的日期同样查不到。

## 常见报错

| 现象                                           | 原因与处理                                                                                                                                                            |
| ---------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `HDFS path must be absolute`                   | `--path` 不是以 `/` 开头；按提示里的命令改                                                                                                                            |
| `HDFS path must not end with a trailing slash` | 去掉结尾的 `/`                                                                                                                                                        |
| `HDFS snapshot date must be YYYYMMDD`          | 日期写成了 `2024-01-31` 之类；改成 `20240131`                                                                                                                         |
| `HDFS_SNAPSHOT_NOT_FOUND`                      | 路径不存在 / 快照未产出 / 日期过保留期。先去掉 `--date` 重试，再用 `hdfs rgroup path list` 确认路径存在                                                               |
| `HDFS does not serve site cn`                  | 该站点不提供此模块；改用 `--site i18n-tt` / `us-ttp` / `eu-ttp`                                                                                                       |
| `HDFS does not serve vregion ...`              | `i18n-tt` 支持 Singapore（默认）和 `--vregion US-East`；`--site eu-ttp --vregion US-EastRed` 是默认 Compass 的兼容别名，GCP 使用 `--vregion US-EastRed-gcp`           |
| `HDFS API error: ...Domain和URL`               | 网关路由失败，通常是站点或 vregion 用错；US-East 使用 `--site i18n-tt --vregion US-East`，EU-TTP2 默认 Compass 使用 `--vregion US-EastRed`，GCP 使用 `US-EastRed-gcp` |
| `Please follow OG instructions...`             | US/EU 网关缺 `x-og-common-path-mode`；bytedcli 会自动带上，出现这条说明是自己拼的请求                                                                                 |

## 容量口径

同一个目录会同时出现两个容量数：`usedSize`（含副本，磁盘实际占用）和 `size`（逻辑大小）。
两者可能差 2~3 倍。汇报"这个目录多大"时先说清用的是哪个口径，也不要拿它和
`hdfs rgroup path list` 的 `size` 直接相减 —— 那是第三个口径。

PB 级数值超过 IEEE754 安全整数范围，只能当近似值用。
