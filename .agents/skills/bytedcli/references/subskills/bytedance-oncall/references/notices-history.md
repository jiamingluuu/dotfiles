# 公告与历史工单

## 查询公告

`notice list` 同时返回指定租户的 P0 公告和产品公告：

```bash
bytedcli oncall notice list --tenant-id "<tenant-id>" --format table
```

输出分为 `p0_notice` 和 `product_notices`，不包含接口包装和公告辅助字段。

## 搜索历史工单

`flow search` 按问题描述做相关性搜索；`flow list` 按工单字段做结构化筛选，两者不要混用。

```bash
bytedcli oncall flow search \
  --keyword "如何接入值班流程" \
  --mine \
  --last-days 90 \
  --limit 10 \
  --format table
```

关键词必填，并且必须通过 `--tenant-id` 或 `--mine` 限定搜索范围。`--mine` 只查当前认证用户的历史工单；两者可以同时使用，以便在指定租户内搜索当前用户的工单。`--limit` 和 `--last-days` 必须大于 0。

结果包含标题、链接、工单 ID、租户名称和创建时间；需要按租户、人员、分类、状态或时间精确筛选时改用 `flow list`。
