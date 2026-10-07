---
name: bytedance-dataq
description: "Operate DataQ via bytedcli for RDS SQL queries and read-only ByteDoc collection find queries. Use when tasks mention DataQ, dataq rds, or querying a ByteDoc collection specifically through the DataQ channel."
---
# bytedcli DataQ

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

- 通过 DataQ 平台查询 RDS 数据库的数据
- 通过 DataQ 平台查询 ByteDoc 数据库的数据

## 前置条件

- 使用通用调用方式：`../../invocation.md`
- 需要鉴权时先登录：`bytedcli --site i18n-tt auth login`
- dataq平台主要供海外区域使用，需要获取i18n-tt站点授权

> 执行前缀见 `../../invocation.md`；下面示例直接写 `bytedcli`。

## Quick start

```bash
# 执行 DataQ RDS 查询 (US)
bytedcli --site i18n-tt dataq rds-query --geo "US" --dbname "my_database" --query "select * from users limit 10"

# 执行 DataQ RDS 查询 (EU)
bytedcli --site i18n-tt dataq rds-query --geo "EU" --dbname "my_database" --query "select * from users limit 10"

# 通过 DataQ 查询 ByteDoc collection；仅支持只读 find(...)
bytedcli --site i18n-tt dataq bytedoc-query --geo "US" --region "US-TTP" --db-name "demo_database" --collection "demo_items" --query 'find({"status":"active"}).limit(10)'

# 从文件读取较长的 ByteDoc 查询
bytedcli --json --site i18n-tt dataq bytedoc-query --geo "EU" --region "EU-TTP2-No1a" --db-name "demo_database" --collection "demo_items" --query-file ./query.mongo
```

## 参数说明

RDS query 参数：

- `--geo`: (必填) 地理位置，仅支持 "US" 或 "EU"。
  - 当 geo 为 "US" 时，底层自动使用 `https://cloud-ttp-us.bytedance.net` 获取 JWT，且请求的 region 对应 "ova"。
  - 当 geo 为 "EU" 时，底层自动使用默认的 ByteCloud 获取 JWT，且请求的 region 对应 "us_east_gcp"。
- `--dbname`: (必填) 数据库名。
- `--query`: (必填) SQL 查询语句。

ByteDoc query 参数：

- `--geo`：必填，仅支持 `US` / `EU`，用于认证分支。
- `--region`：必填，原样传给 DataQ。同一 geo 可能对应多个 region，例如 EU 已知包括 `EU-TTP2-No1a` 和 `US-EastRed`
- `--db-name`：必填，ByteDoc database 名称。
- `--collection`：必填，ByteDoc collection 名称。
- `--query` / `-F, --query-file`：二选一，Mongo 风格 `find` 查询，需以 `find(` 开头（例如 `find({}).limit(10)`）。

## Notes

- 需要结构化输出加 `--json`（全局选项，放在子命令之前，如 `bytedcli --json dataq rds-query ...`）

## References

- `references/dataq.md`
