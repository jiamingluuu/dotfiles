# Coral search and metadata

Use this when the user asks to find a table or inspect Coral Hive metadata.

## Search choice

```bash
# Free-form search across Coral entities
bytedcli --json coral search --region sg --query "example_table" --type-name HiveTable --limit 10

# Better when DB is known
bytedcli --json coral hive table list --region sg --db-name example_db --query "example_table" --limit 10
```

I tested both patterns locally against Coral; `HiveTable` is accepted by `coral search`, and DB-scoped `table list` is the cleaner path when the database is known.

## Inspect a table

```bash
bytedcli --json coral hive table get --region sg --db-name example_db --table-name example_table
bytedcli --json coral hive table ddl --region sg --db-name example_db --table-name example_table
bytedcli --json coral hive table latest-partition --region sg --db-name example_db --table-name example_table
bytedcli --json coral hive table partitions --region sg --db-name example_db --table-name example_table --limit 20
bytedcli --json coral hive table preview --region sg --db-name example_db --table-name example_table --limit 10
bytedcli --json coral hive table replicas --region sg --db-name example_db --table-name example_table
bytedcli --json coral hive table lineage --region sg --db-name example_db --table-name example_table --direction BOTH
bytedcli --json coral hive table quality --region sg --db-name example_db --table-name example_table
bytedcli --json coral hive table dorado-tasks --region sg --db-name example_db --table-name example_table
```

## 更新普通 Hive 列说明

```bash
# 读取完整 schema 并预览，未指定 --yes 时不会写入
bytedcli --json coral hive table update --region cn --db-name example_db --table-name example_table \
  --column-comments '{"sample_col":"业务主体标识","sample_count":"资源数量"}'
# 获得用户写入授权后提交，空字符串用于清空说明
bytedcli --json coral hive table update --region cn --db-name example_db --table-name example_table \
  --column-comments '{"sample_col":"业务主体标识","sample_count":""}' --yes
```

- 仅接受普通 Hive 表的非分区列，字段名必须与读取结果完全一致。分区说明没有经过验证的安全写入接口，不能将分区列塞进完整字段列表。
- CLI 从当前完整 schema 构造字段列表，保留列顺序、类型、GUID 和已有安全元数据。只有安全标签缺失或 NULL 的 CID 使用表所在地域的 CID 补齐，已有数值 CID 保持不变，不新增安全标签。
- 提交前再次读取 schema，有变化则停止。后端没有 CAS/锁，操作期间仍须避免其他客户端同时修改同一表结构。
- 读取、写入和回读固定使用 Hive 配置的首选网关及 CID（US-TTP 遵循 BDEE 优先规则），不在写入失败后切换地域或重试 PUT。
- `state=preview` 表示只读预览，`unchanged` 表示无需写入，`verified` 表示回读的 Coral 列元数据与预期一致。它不证明 Hive 引擎、已有分区或下游系统完成同步。
- `submission=unconfirmed` 与 `state=verified` 可以同时出现：写入响应失败，但回读确认了所需元数据。`HIVE_COMMENTS_UPDATE_INDETERMINATE` 表示已尝试提交却无法核验，应按错误中的只读查询指引检查，不能自动重发。

## Agent guidance

- To quickly check table freshness or latest available partition (e.g. before scheduling downstream tasks or queries), prefer `coral hive table latest-partition`; it returns the max partition and creation timestamp in sub-second time without scanning all partitions.
- Use `coral hive table partitions` only when you need to enumerate multiple partition paths with `--limit`.
- Prefer explicit `--region`; omitted regions follow the active `--site`, so explicit region keeps repeated calls stable.
- Use `--json` when the result will be parsed or used to drive another step.
- If output is huge, query only the command needed rather than dumping every metadata endpoint.
- `search` and `hive table list` return `{ entities, total, offset, limit, truncated }`. When `truncated` is `true`, more rows exist beyond the current window — raise `--limit` or advance `--offset` before treating the result as complete.
