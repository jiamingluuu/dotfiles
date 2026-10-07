# DataQ

## DataQ RDS 查询

```bash
# 执行 DataQ RDS 查询 (US)
bytedcli --site i18n-tt dataq rds-query --geo "US" --dbname "my_database" --query "select * from users limit 10"

# 执行 DataQ RDS 查询 (EU)
bytedcli --site i18n-tt dataq rds-query --geo "EU" --dbname "my_database" --query "select * from users limit 10"
```

## 参数映射说明

- `--geo "US"` 会自动映射 region 为 `ova`，并使用专门的鉴权网关 `https://cloud-ttp-us.bytedance.net`。
- `--geo "EU"` 会自动映射 region 为 `us_east_gcp`，并使用默认的鉴权网关。

## DataQ ByteDoc 查询

DataQ ByteDoc 查询是一个明确的只读查询通道。一般 ByteDoc database/collection 查询、权限申请或写入操作使用 `bytedcli bytedoc ...`；只有用户明确要求通过 DataQ 查询时才使用这里的命令。

```bash
# inline 查询
bytedcli --site i18n-tt dataq bytedoc-query --geo "US" --region "US-TTP" --db-name "demo_database" --collection "demo_items" --query 'find({"status":"active"}).limit(10)'

# 文件查询和结构化输出
bytedcli --json --site i18n-tt dataq bytedoc-query --geo "EU" --region "EU-TTP2-No1a" --db-name "demo_database" --collection "demo_items" --query-file ./query.mongo
```

参数：

- `--geo`：必填，仅支持 `US` / `EU`，用于认证分支。
- `--region`：必填，原样传给 DataQ。region 不是 geo 的一对一映射；EU 已知至少包括 `EU-TTP2-No1a` 和 `US-EastRed`，CLI 不提供推测性默认值。
- `--db-name`：必填，ByteDoc database 名称。
- `--collection`：必填，ByteDoc collection 名称。
- `--query` / `-F, --query-file`：二选一。CLI 会 trim 输入并要求查询以 `find(` 开始。

成功结果包含 `amount`、`col_name` 和 `data`；可能包含 `result_id`、`blocked_columns`、`data_fetch_plan`。文本模式显示表格和 `Rows: <amount>`，JSON 模式返回相同的结构化结果。
