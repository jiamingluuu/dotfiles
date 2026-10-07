# Oncall 租户标签查询

使用 `tag list` 查询指定租户的完整标签树；命令会按树的顺序展开为列表，方便查看标签 ID 并用于 `flow update --tag-id`。

```bash
bytedcli oncall tag list --tenant-id 2 --format table
bytedcli oncall tag list --tenant-id 2 --only-used --format json
```

- `--tenant-id` 是必填的正整数租户 ID。
- 默认返回租户下全部标签；`--only-used` 仅返回已启用标签。
- 表格包含标签 ID、中文名、英文名、启用状态、叶子节点、层级、父标签 ID、别名和中文路径。
- JSON 额外保留父节点 ID 列表、排序 ID、英文路径、租户 ID、创建和修改信息等后端元数据。
- 输出保持标签树的遍历顺序，但以平铺列表呈现，不返回嵌套的 `children` 字段。
