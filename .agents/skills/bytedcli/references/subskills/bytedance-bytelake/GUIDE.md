---
name: bytedance-bytelake
description: "Create, validate, and update ByteLake Hive tables via bytedcli using DataLeap CoralNG Hive bridge. Use when tasks mention ByteLake/Bytelake, DataLeap, Coral, creating Hive tables stored as ByteLake, setting recordkey/precombine, partitioning, clustering/buckets, TTL, updating table Chinese display name, description, business metadata, project binding, or when you need a repeatable CLI workflow for table creation or metadata updates across Hive-supported regions such as cn, sg, gcp, va, mycis, mybd, us-ttp, eu-ttp2, eu-compliance2, and eu-ttp."
---

# bytedcli ByteLake (DataLeap CoralNG Hive bridge)

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

- 创建 ByteLake 表（`STORED AS ByteLake`）
- 在创建前通过 `bridge/hive/explain` 校验 DDL
- 对已有 `CREATE TABLE ... STORED AS ByteLake` DDL 做 explain / create
- 用结构化参数生成标准 ByteLake DDL（字段/分区/聚簇/桶/recordkey/precombine）
- 更新已有 ByteLake 表的中文展示名、描述、业务元数据、项目绑定或 TTL
- 在 Hive 支持的多个机房之间切换创建（cn、sg、gcp、va、mycis、mybd、us-ttp、eu-ttp2、eu-compliance2、eu-ttp）

## 前置条件

- 已登录对应站点：`bytedcli auth status` / `bytedcli auth login`

> 执行前缀见 `../../invocation.md`；下面示例直接写 `bytedcli`。

## Supported Regions

| Hive region (`--region`) | 建议站点 (`--site`) |
| ------------------------ | ------------------- |
| `cn`                     | `cn`                |
| `sg`                     | `i18n-tt`           |
| `gcp`                    | `i18n-tt`           |
| `va`                     | `i18n-tt`           |
| `mycis`                  | `i18n-bd`           |
| `mybd`                   | `i18n-bd`           |
| `us-ttp`                 | `i18n-tt`           |
| `eu-ttp2`                | `i18n-tt`           |
| `eu-compliance2`         | `i18n-tt`           |
| `eu-ttp`                 | `i18n-tt`           |

## --site 与 --region 的搭配（必看）

- `--region cn`：建议 `--site cn`
- `--region sg|gcp|va|us-ttp|eu-ttp2|eu-compliance2|eu-ttp`：建议 `--site i18n-tt`
- `--region mycis|mybd`：建议 `--site i18n-bd`

## Quick start

### 1) 先校验 DDL（不创建）

```bash
bytedcli --site cn bytelake table create \
  --region cn \
  --db demo_db \
  --table demo_tbl \
  --comment "demo bytelake table" \
  --column "id:bigint:pk" \
  --column "name:string:name" \
  --partition-column "pdate:string:ds" \
  --record-key "id" \
  --precombine "id" \
  --username your.name \
  --explain-only
```

### 2) 创建表

```bash
bytedcli --site cn bytelake table create \
  --region cn \
  --db demo_db \
  --table demo_tbl \
  --comment "demo bytelake table" \
  --column "id:bigint:pk" \
  --column "name:string:name" \
  --partition-column "pdate:string:ds" \
  --cluster-by "id" --buckets 32 \
  --record-key "id" \
  --precombine "id" \
  --ttl 7 --ttl-column pdate --ttl-pattern yyyyMMdd \
  --username your.name
```

### 3) 更新表属性

```bash
bytedcli --site i18n-bd bytelake table update \
  --region mycis \
  --guid 12345678-1234-1234-1234-123456789abc \
  --alias "demo table name" \
  --description "demo table description" \
  --business-line "demo-line" \
  --data-layer "demo-layer" \
  --data-category "demo-category" \
  --storage-strategy "demo-strategy" \
  --project "demo_project" \
  --ttl 7 --ttl-column pdate --ttl-pattern yyyyMMdd
```

也可以用库表名定位：

```bash
bytedcli --site i18n-bd bytelake table update \
  --region mycis \
  --database demo_db \
  --table demo_tbl \
  --description "demo table description"
```

### 4) 直接提交 DDL

默认只做 explain：

```bash
bytedcli --site cn bytelake ddl apply \
  --region cn \
  --sql "CREATE TABLE \`demo_db\`.\`demo_tbl\` (\`id\` bigint) STORED AS ByteLake" \
  --username your.name
```

显式创建时，追加 `--no-explain-only`：

```bash
bytedcli --site cn bytelake ddl apply \
  --region cn \
  --sql "CREATE TABLE \`demo_db\`.\`demo_tbl\` (\`id\` bigint) STORED AS ByteLake" \
  --username your.name \
  --no-explain-only
```

## Notes

- `--column` / `--partition-column` 是可重复参数，格式为 `name:type[:comment]`
- `--cluster-by` 与 `--buckets` 必须同时提供
- `--record-key` / `--precombine` 会写入 `TBLPROPERTIES`，用于 ByteLake MERGE_ON_READ
- `--explain-only` 只跑校验，不会触发创建请求
- `bytelake ddl apply` 默认也是 explain-only；需要创建时显式传 `--no-explain-only`
- `bytelake table update` 对齐 Hive 表属性更新：`--alias` 写入 CoralNG `attributes.alias`，`--description` 写入 `attributes.description`，`--business-line` / `--data-layer` / `--data-category` / `--storage-strategy` / `--project` 写入对应业务属性，`--ttl` 走 `data-stores/ttl`

## References

- `references/bytelake.md`
- `../../invocation.md`
- `../../troubleshooting.md`
