# 租户查询

已知租户 ID 时使用 `tenant get`；只有关键词、需要分页列举或查询当前用户管理的租户时使用 `tenant search`。

## `tenant get`

```bash
bytedcli oncall tenant get --id "<tenant-id>" --format table
bytedcli oncall tenant get --id "<tenant-id>" --raw --format json
```

`--id` 是正整数 Oncall 租户 ID。默认输出核心字段：租户 ID、名称、描述、指令、文档/GPT 搜索开关、管理员、用户群和已启用能力；`--raw` 返回接口 `data` 中的完整字段。

用户说 `tenant_id` 时通常也是 Oncall 租户 ID，但 `tenant get` 的选项名是 `--id`。

## `tenant search`

```bash
bytedcli oncall tenant search --keyword "<tenant-keyword>" --format table
bytedcli oncall tenant search --managed-only --page 1 --page-size 20 --format table
```

- 不传关键词时分页列出租户；分页值必须大于 0。
- `--managed-only` 最多扫描前 1000 条候选租户，先按关键词筛选，再按当前用户管理权限过滤，最后在 CLI 内分页。
- 当前用户管理但没有配置问题分类的租户也会返回。
- 平台超级租户遵循服务端规则，不在结果中返回。
- 返回多个候选时，根据用户信息选择最匹配项；无法唯一判断时请用户确认。

定位到租户 ID 后，只按用户意图执行下一步：

```bash
bytedcli oncall flow list --tenant-id "<tenant-id>" --format table
bytedcli oncall question-type list --tenant-id "<tenant-id>" --regions-only
bytedcli oncall duty-user get --tenant-id "<tenant-id>" --region "<region>"
```
