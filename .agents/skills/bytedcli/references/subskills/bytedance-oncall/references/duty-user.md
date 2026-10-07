# 值班人查询

使用 `duty-user get` 查询租户、区域和可选问题分类对应的值班人：

```bash
bytedcli oncall duty-user get \
  --tenant-id "<tenant-id>" \
  --region "<region>"
```

- `--tenant-id` 和 `--region` 必填；租户 ID 必须是整数。
- 区域未知时，先用 `question-type list --regions-only` 获取可用值，不要根据展示名猜测。
- 用户指定问题分类时，先用 `question-type list --tenant-id "<tenant-id>"` 确认该分类返回的 `region`，再同时传 `--question-type-id` 和完全一致的 `--region`。
- `cn` 与 `cn_all` 是不同区域，不能根据“所有区域”的展示名互换。分类和区域不匹配时，后端会回退到租户默认值班；命令输出中的 `已回退默认值班` 和 `回退说明` 会明确标记这一情况。
- 用户明确要求联合值班时传 `--union-duty=true`。
- 租户未知时，先按 [租户查询](tenant.md) 定位。

如果用户还要查询该租户近期工单，再执行 `flow list --tenant-id "<tenant-id>"`。
