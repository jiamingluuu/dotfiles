# 问题分类与文档搜索

这两个命令都需要 Oncall 租户 ID。租户未知时，先按 [租户查询](tenant.md) 定位。

## `question-type list`

区域未知时，先查服务端可用值；已知区域时，再查该区域的问题分类：

```bash
bytedcli oncall question-type list \
  --tenant-id "<tenant-id>" \
  --regions-only \
  --format table

bytedcli oncall question-type list \
  --tenant-id "<tenant-id>" \
  --region "<region>" \
  --format table
```

不传 `--region` 时返回该租户全部区域及分类。分类结果还可能包含分类动作、目标租户、目标群聊和跳转链接。必须使用接口返回的区域值，不要根据展示名或自然语言猜测。

## `document search`

```bash
bytedcli oncall document search \
  --tenant-id "<tenant-id>" \
  --keyword "<search-text>" \
  --limit 5 \
  --format table
```

需要同时搜索 Wiki 时加 `--include-wiki`。关键词不能为空，`--limit` 必须大于 0。结果包含文档标题、类型、链接、相关度、高亮摘要、关键词、标签和时间。

用户要查相似历史工单时改用 `flow search`，不要用文档搜索代替。
