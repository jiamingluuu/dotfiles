# Paimon 建表（bytedcli）

本技能对应命令：

- `bytedcli paimon table create`
- `bytedcli paimon table update`

## 支持机房

- `cn` -> `--site cn`
- `sglark` -> `--site cn`
- `sg` / `gcp` / `va` / `us-ttp` / `eu-ttp2` / `eu-compliance2` / `eu-ttp` -> `--site i18n-tt`
- `mycis` / `jplark` / `uspipo` / `mybd` -> `--site i18n-bd`

## 输入信息清单（建议按这个顺序收集）

- 站点与区域：`--site`、`--region`
- 库表名：`--database`、`--table`
- 表描述：`--comment`
- 字段：多次 `--column "name:type:comment"`
- 分区字段（可选但常用）：多次 `--partition-column "pdate:string:日期分区"`
- 主键与分桶（必填）：`--primary-key "pdate,id"`、`--bucket 8`、`--bucket-key "id"`
- Paimon 行为（可选）：`--merge-engine`、`--changelog-producer`、`--sequence-field`
- 存储（可选，有默认值）：`--file-format parquet`、`--file-compression zstd`
- Owner：多次 `--username your.name`
- TTL（可选）：`--ttl 7 --ttl-column pdate --ttl-pattern yyyyMMdd`
- 业务元数据（可选）：`--business-line`、`--data-layer`、`--data-category`（可重复）、`--project`

补充说明：

- `paimon table update` 里的 `--alias` / `--description` / `--business-line` / `--data-layer` / `--data-category` / `--storage-strategy` / `--project` 传空串或纯空白值时会被省略，不作为清空语义。
- `--advanced-parameter <key=value>` 可重复传入；key 仅支持字母、数字、点、下划线和连字符。命令先读取现有 DDL 与 `advancedExtParameters`，依次执行编辑态 schema explain、候选 DDL 校验、`notifyDownstream:true` 物理下发和资产属性同步，最后回读物理 DDL；传入的键覆盖旧值，未传入的键保持不变。
- 高级参数写入后的物理 DDL 回读窗口在 `mycis` 默认为 60000ms，其他 region 默认为 5000ms；可用 `--ddl-readback-timeout-ms <ms>` 显式覆盖，最大 600000ms。
- `--data-category` 可重复；混入空串或纯空白值时，这些项会被静默丢弃。

## 典型模式

### 最小可用（推荐先 explain）

```bash
bytedcli --site cn paimon table create \
  --region cn \
  --database demo_db \
  --table demo_tbl \
  --comment "demo" \
  --column "id:bigint:pk" \
  --partition-column "pdate:string:ds" \
  --bucket 8 \
  --bucket-key "id" \
  --primary-key "pdate,id" \
  --username your.name \
  --explain-only
```

### 带业务元数据创建

```bash
bytedcli --site cn paimon table create \
  --region cn \
  --database demo_db \
  --table demo_tbl \
  --comment "demo" \
  --column "id:bigint:pk" \
  --column "name:string:name" \
  --partition-column "pdate:string:ds" \
  --bucket 8 \
  --bucket-key "id" \
  --primary-key "pdate,id" \
  --merge-engine deduplicate \
  --changelog-producer none \
  --file-format parquet \
  --file-compression zstd \
  --business-line demo_business \
  --data-layer DWD \
  --data-category demo_category \
  --project demo_project \
  --username your.name
```

### 增量更新高级参数

```bash
bytedcli --site i18n-bd paimon table update \
  --region mycis \
  --database demo_db \
  --table demo_tbl \
  --advanced-parameter amoro.expire-snapshots.enabled=true \
  --advanced-parameter amoro.clean-orphans.enabled=true \
  --advanced-parameter amoro.compact.enabled=true
```

## 输出与验证

- `--explain-only` 时，成功输出包含：`DDL validation succeeded` 和 `Skipped create`
- 实际创建时，成功输出包含：`DDL validation succeeded` 和 `Table created`
- 创建后可以用 Hive 域名查询元数据（示例）：

```bash
bytedcli --site cn hive detail demo_db demo_tbl --region cn
```
