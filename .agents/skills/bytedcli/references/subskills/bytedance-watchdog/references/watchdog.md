# Watchdog Diag commands

BDEE 无法直接调用 US-TTP / EU-TTP 内的 RPC。Diag 在合规区内执行 RPC/DB 并对结果断言。当前命令覆盖 RPC 与 RDS。CLI 按 `--site` / `--region` 自动选择 execute 控制面，不要手写 host。

```bash
bytedcli watchdog region list

# ROW：可读回包，用来对照写 --assert
bytedcli --json --site i18n-tt watchdog rpc execute \
  --psm example.service.api \
  --method DemoMethod \
  --region sg1 \
  --body-file ./demo-request.json

# PPE 泳道
bytedcli --json --site i18n-tt watchdog rpc execute \
  --psm example.service.api \
  --method DemoMethod \
  --region sg1 \
  --env ppe_demo \
  --body-file ./demo-request.json

# 合规区（US-TTP / EU-TTP）：只能断言，不回业务明文；按已知业务预期写断言
bytedcli --site us-ttp watchdog rpc execute \
  --psm example.service.api \
  --method DemoMethod \
  --region useast5 \
  --body-file ./demo-request.json \
  --assert 'VideoDetails.demo-id.EpisodeNum = 1' \
  --assert 'VideoDetails.demo-id.Title = demo-title'
bytedcli --site eu-ttp watchdog rpc execute \
  --psm example.service.api \
  --method DemoMethod \
  --region USEASTRED \
  --vdc useast2b \
  --body-file ./demo-request.json \
  --assert 'VideoDetails.demo-id.IsPreview = true'

# RDS ROW：可读行
bytedcli --json --site i18n-tt watchdog db execute \
  --db-name example_db \
  --region Singapore-Central/alisg \
  --sql 'SELECT id, extra FROM demo_table WHERE id=1'
# RDS 合规区：只允许 Diag 控制台列出的 vregion/dc
bytedcli --site us-ttp watchdog db execute \
  --db-name example_db \
  --region US-TTP2/useast8 \
  --sql 'SELECT id, extra FROM demo_table WHERE id=1' \
  --assert 'id = 1' \
  --assert 'extra.multi_language.contract_language = zh'
bytedcli --site eu-ttp watchdog db execute \
  --db-name example_db \
  --region US-EastRed/us_east_gcp \
  --sql-file ./demo.sql \
  --assert 'extra.multi_language.contract_language = zh'
bytedcli --site eu-ttp watchdog db execute \
  --db-name example_db \
  --region EU-TTP2/no1a \
  --sql 'SELECT id FROM demo_table WHERE id=1' \
  --assert 'id = 1'
```

`--site i18n-tt --region sg1` 走 ROW execute，可返回 `data` 与 `data_outline`。`--site us-ttp` / `--site eu-ttp` 按 region 打对应合规区 execute 平面，JWT 分别用 `us-ttp` / `eu-ttp`，每个 `--assert` 一次 `where` + `fetch`，只回是否命中。断言未命中时命令以 `WATCHDOG_ASSERT_FAILED` 非零退出。`USEASTRED` RPC 必须带 `--vdc useast2b`。`--env ppe_demo` 写入 `Base.TrafficEnv` 和 `x-tt-env` / `x-use-ppe`。请求体用 `api-test gen-request` 生成，不要手写 schema。`--assert` 语法是 `<path> = <value>`，snowflake key 写成 `Map.demo-id.Field` 或 `Map["demo-id"].Field`。`--body` 与 `--body-file` 互斥；`--body-file` 原样编码进 Diag `j`+Base64 request，snowflake ID 保持 JSON number。`--body` 必须是 JSON 对象，不能是数组、null 或标量。

RDS `--region` 是 `vregion/dc`：`Singapore-Central/alisg`；`US-BOE/boei18n`、`US-Compliance/useast11a`、`US-East/awsvagm`、`US-East/maliva`、`US-East/maliva_sensitive`、`US-East/useastdt`、`US-EastRed/us_east_gcp`、`US-TTP/ova`、`US-TTP2/useast8`；`EU-TTP/ie`、`EU-TTP/iedt`、`EU-TTP2/no1a`。RDS 行是扁平列；带点的 `--assert 'extra.foo = zh'` 表示 `extra` 是 JSON 字符串列，CLI 发 `getFirst` + `getJSON` + `where`。`watchdog db execute` 命中 DB SQL 禁入清单时以 `DB_SQL_BLOCKED` 拒绝。SQL 只允许单条 SELECT / SHOW TABLES / SHOW CREATE TABLE / EXPLAIN SELECT，DML/DDL 以 `RDS_SQL_NOT_READ_ONLY` 拒绝。RPC `--vdc` 只接受该 region 的 VDC 令牌（`useast2b` / `us_east_gcp`），不要把 `USEASTRED` 这类 region 名传给 `--vdc`；`--region us_east_gcp --vdc USEASTRED` 会报错。

## EU RPC 地区与调用方式

RPC 支持 `--region ie2`（`EU-Compliance2`）、`--region ie`（`EU-TTP` / `EUTTP`）、`--region de`（`EU-Compliance`）。CLI 自动发送对应 VDC，并使用 EU execute 服务与 `eu-ttp` 认证；仍只返回断言结果。

`--use-direct-rpc` 是可选的 Watchdog RPC 调用方式开关，对应后端 `useDirectRPC=true`，默认不发送。后端返回 watchman 权限错误且提示 `useDirectRPC=true` 时可尝试启用；它不改变权限要求。若报 `peek instance error: psm instance not found`，检查目标 PSM 在该 region / cluster 是否有部署，不要把 ie、ie2、de 当作可互换别名。预期的业务状态可直接用 `BaseResp.StatusCode` 断言；Diag 执行失败仍然报错。

```bash
bytedcli --json --site eu-ttp watchdog rpc execute \
  --psm example.service.api --method DemoMethod \
  --region ie2 --env prod --cluster default \
  --body-file ./demo-request.json \
  --assert 'BaseResp.StatusCode = 110005'
```
