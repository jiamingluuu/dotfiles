# bytedcli labelgpt space

查询当前用户已加入和可申请的 LabelGPT Space、按 ID 获取空间详情，并向指定审批人提交空间权限申请。三个叶子
都不要求全局 `--space-id`。

## space list

```bash
bytedcli labelgpt space list --format raw
bytedcli labelgpt space list -o ./out
```

- 查询当前用户已加入和可申请的空间。
- 已加入空间在前，`access=joined`；未加入空间在后，`access=available`。相同 ID 保留已加入项。
- `raw/json` 输出 `spaces`、`total`、`joined_count`、`available_count`。空间字段包括 `id`、
  `name`、`description`、`bytetree_id`、`bytetree_name`、`create_user_id`、`create_time`、
  `update_time`、`is_dola_space` 和 `access`。
- `-o <DIR>` 写入 `space_list_<timestamp>.json`。

## space get

```bash
bytedcli labelgpt space get --id <SPACE_ID> --format raw
bytedcli labelgpt space get --id <SPACE_ID> -o ./out
```

- `--id` 必填且必须是正 int64；它是查询目标，不使用也不修改全局 `--space-id`。
- 查询指定空间的详情。
- `raw/json` 输出 `id`、`name`、`description`、`bytetree_id`、`bytetree_name`、
  `create_user_id`、`create_time`、`update_time` 和 `is_dola_space`。
- `-o <DIR>` 写入 `space_get_<SPACE_ID>.json`。

## space apply

```bash
bytedcli labelgpt space apply --id <SPACE_ID> --role member \
  --approver owner@example.com --format raw

bytedcli labelgpt space apply --id <SPACE_ID> --role admin \
  --approver first@example.com,second@example.com \
  --remark "申请理由" --format raw
```

- `--id` 必填且必须是正 int64；它是申请目标，不使用也不修改全局 `--space-id`。
- `--role` 必须为 `member` 或 `admin`，分别表示“空间组员”和“空间管理员”。
- `--approver` 必填，可重复或逗号分隔；值必须为邮箱。CLI 会 trim、去空并去重。
- `--remark` 可选。
- 提交空间权限申请。成功只表示审批已提交，不表示权限已生效；服务端不返回可公开使用的审批单 ID。提交成功后，请前往飞书“审批中心”查看自己发起的空间申请。
- `raw/json` 输出 `space_id`、`role`、`approvers`、`remark`、`submitted`。
- `-o <DIR>` 写入 `space_apply_<SPACE_ID>.json`。

## Schema

```bash
bytedcli labelgpt schema space list --format raw
bytedcli labelgpt schema space get --format raw
bytedcli labelgpt schema space apply --format raw
```
