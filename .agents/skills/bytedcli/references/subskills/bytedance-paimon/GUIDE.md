---
name: bytedance-paimon
description: "Create, validate, and update Paimon tables via bytedcli using the DataLeap CoralNG Hive bridge. Use when tasks mention Paimon/paimon tables, DataLeap, Coral, creating a Hive-engine Paimon table, setting or incrementally merging advancedExtParameters, primary key / bucket / bucket-key, merge-engine (deduplicate/partial-update/aggregation/first-row), changelog-producer, sequence.field, file format/compression, TTL, alias/description, business metadata (business line / data layer / data category / project), or when you need a repeatable CLI workflow for Paimon tables across Hive-supported regions such as cn, sg, gcp, va, mycis, sglark, jplark, uspipo, mybd, us-ttp, eu-ttp2, eu-compliance2, and eu-ttp."
---

# bytedcli Paimon (DataLeap CoralNG Hive bridge)

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

- 在 DataLeap 上创建 Paimon 表（CoralNG `management/data-store`，engine 为 `paimon`）
- 在创建前通过 explain 校验 DDL（`--explain-only`）
- 用结构化参数生成标准 Paimon DDL（字段/分区/主键/bucket/merge-engine/changelog-producer/file format）
- 为已存在的表补填/更新展示名、描述、业务元数据（业务线 / 数据分层 / 数据分类 / 项目绑定 / 存储策略）与 TTL（`paimon table update`）
- 查询 Coral 项目列表并按项目名绑定到表（`paimon project list` / `paimon table update --project`）
- 在 Hive 支持的多个机房之间切换创建（cn、sg、gcp、va、mycis、sglark、jplark、uspipo、mybd、us-ttp、eu-ttp2、eu-compliance2、eu-ttp）

## 属性更新约定

- Paimon 的表级属性更新统一走聚合命令 `bytedcli paimon table update`，对外收口别名、描述、业务元数据、项目绑定和 TTL，不再拆成多条 `modify` 子命令。
- 命令形态与 Hive 的聚合 `hive table update` 相近。普通属性和 TTL 复用 CoralNG helper；高级参数按 `schema explain → DDL check → fields commit → attributes update → physical DDL readback` 完整链路执行。
- 常用属性字段与 Hive / ClickHouse 保持覆盖范围对齐：`alias`、`description`、`businessLine`、`dataLayer`、`dataCategories`、`storageStrategy`、`ttl`；差异除了命令入口和后端契约，还包括空值语义。
- Paimon 当前不把空串当清空：`--alias`、`--description`、`--business-line`、`--data-layer`、`--data-category`、`--storage-strategy`、`--project` 里的空串或纯空白值会被直接省略，不会写成 null 或空数组。
- 使用可重复的 `--advanced-parameter <key=value>` 增量更新 Paimon 参数；命令按页面顺序执行编辑态 schema explain、候选 DDL 校验、`data-stores/fields` 下发和 Coral `advancedExtParameters` 同步，并以物理 DDL 回读为成功标准。
- 高级参数写入后的物理 DDL 回读窗口在 `mycis` 默认为 60000ms，其他 region 默认为 5000ms；可用 `--ddl-readback-timeout-ms <ms>` 显式覆盖，最大 600000ms。

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
| `sglark`                 | `cn`                |
| `jplark`                 | `i18n-bd`           |
| `uspipo`                 | `i18n-bd`           |
| `mybd`                   | `i18n-bd`           |
| `us-ttp`                 | `i18n-tt`           |
| `eu-ttp2`                | `i18n-tt`           |
| `eu-compliance2`         | `i18n-tt`           |
| `eu-ttp`                 | `i18n-tt`           |

## --site 与 --region 的搭配（必看）

- `--region cn`：建议 `--site cn`
- `--region sg|gcp|va|us-ttp|eu-ttp2|eu-compliance2|eu-ttp`：建议 `--site i18n-tt`
- `--region mycis|jplark|uspipo|mybd`：建议 `--site i18n-bd`
- `--region sglark`：建议 `--site cn`

## Quick start

### 1) 先校验 DDL（不创建）

```bash
bytedcli --site cn paimon table create \
  --region cn \
  --database demo_db \
  --table demo_tbl \
  --comment "demo paimon table" \
  --column "id:bigint:pk" \
  --column "name:string:name" \
  --partition-column "pdate:string:ds" \
  --bucket 8 \
  --bucket-key "id" \
  --primary-key "pdate,id" \
  --username your.name \
  --explain-only
```

### 2) 创建表

```bash
bytedcli --site cn paimon table create \
  --region cn \
  --database demo_db \
  --table demo_tbl \
  --comment "demo paimon table" \
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
  --ttl 7 --ttl-column pdate --ttl-pattern yyyyMMdd \
  --username your.name
```

### 3) 为已存在的表补填业务元数据 / TTL

```bash
bytedcli --site i18n-bd paimon table update \
  --region mycis \
  --database demo_db \
  --table demo_tbl \
  --alias "demo alias" \
  --description "demo table description" \
  --business-line demo-line \
  --data-layer demo-layer \
  --data-category "demo-category" \
  --storage-strategy demo-strategy \
  --ttl 365 --ttl-column pdate --ttl-pattern yyyyMMdd
```

### 4) 查询可绑定项目

```bash
bytedcli --site i18n-bd paimon project list \
  --region mycis \
  --keyword demo
```

### 5) 增量更新高级参数

```bash
bytedcli --site i18n-bd paimon table update \
  --region mycis \
  --database demo_db \
  --table demo_tbl \
  --advanced-parameter amoro.expire-snapshots.enabled=true \
  --advanced-parameter amoro.clean-orphans.enabled=true \
  --advanced-parameter amoro.compact.enabled=true
```

### 6) 给已存在的表绑定项目

```bash
bytedcli --site i18n-bd paimon table update \
  --region mycis \
  --database demo_db \
  --table demo_tbl \
  --project demo_project
```

## Notes

- `--column` / `--partition-column` 是可重复参数，格式为 `name:type[:comment]`
- `--bucket`、`--bucket-key`、`--primary-key` 是必填项；后端走 `x-gw-exec-mode: async` 网关，缺字段时可能以 `code:0` 静默接收却不落元数据，务必补齐
- `--bucket-key` / `--primary-key` 接受逗号分隔的多列
- `--merge-engine` 默认 `deduplicate`，可选 `partial-update` / `aggregation` / `first-row`
- `--changelog-producer` 默认 `none`，可选 `input` / `lookup` / `full-compaction`
- `--file-format` 默认 `parquet`，`--file-compression` 默认 `zstd`
- `--ttl-column` 与 `--ttl-pattern` 必须同时提供
- 展示名、描述与业务元数据 `--alias` / `--description` / `--business-line` / `--data-layer` / `--data-category`（可重复）/ `--project` 全部可选，不传则从 payload 中省略；传空串或纯空白值也会被省略，不作为清空语义
- `--explain-only` 只跑校验，不会触发创建请求
- `paimon project list` 走 Coral `bridge/dorado/project`，用于列出当前 region/cid 下可绑定的项目；可用 `--keyword` 按项目名过滤。
- `paimon table update` 用于更新已存在的表：普通元数据调用 `data-stores/attributes`，TTL 调用 `data-stores/ttl`；高级参数先提交完整 schema 和合并后的属性，再以物理 DDL 回读确认生效。至少要传一个更新字段；`--ttl-column` 与 `--ttl-pattern` 必须同时提供。
- `--advanced-parameter` 可重复传入 `key=value`。命令会更新物理 DDL 的 `TBLPROPERTIES` 并同步 Coral 资产属性；完成后可用 `hive ddl <database> <table> --region <region>` 回读验证。不接受完整 CoralNG 属性对象透传。
- `--ddl-readback-timeout-ms` 只控制高级参数提交后的物理 DDL 验证窗口。`mycis` 默认 60000ms，其他 region 默认 5000ms；物理 DDL 更慢时可传不超过 600000 的正整数。
- `--project` 会先按项目名精确匹配 Coral 项目列表，再把完整 project 对象（`typeName/id/name/createUserName/departmentName/description`）写入 `data-stores/attributes`。若未命中或命中多个候选，会提示先运行 `paimon project list --keyword ...`。

## References

- `references/paimon.md`
- `../../invocation.md`
- `../../troubleshooting.md`
