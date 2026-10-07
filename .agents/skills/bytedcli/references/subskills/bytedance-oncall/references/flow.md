# Oncall 工单查询、更新与关单

使用 `flow list` 做结构化筛选，使用 `flow get` 按 ID 查详情，使用 `flow timeline` 查关键事件；根据问题描述查相似历史工单时改用 [flow search](notices-history.md#搜索历史工单)。

## `flow list`

```bash
bytedcli oncall flow list --tenant-id "<tenant-id>" --format table

bytedcli oncall flow list \
  --assigned-to-me \
  --stage launch_oncall \
  --solved=false \
  --format table

bytedcli oncall flow list \
  --source-type cli \
  --cli-source bytedcli \
  --range 30d \
  --format table

# 最近 3 天有更新的工单；默认按更新时间倒序
bytedcli oncall flow list --updated-within 3d --format table

# 指定更新时间边界
bytedcli oncall flow list \
  --updated-after "2026-08-28 12:00:00" \
  --updated-before "2026-08-31 12:00:00" \
  --format table

# 最近 3 天收到过新消息的工单；默认按最后消息时间倒序
bytedcli oncall flow list --message-updated-within 3d --format table
```

### 筛选语义与限制

- 必须至少传一个业务筛选条件；仅分页或排序不算筛选。
- `--mine` 和 `--assigned-to-me` 自动读取当前认证用户，分别不能与 `--originator`、`--handler` 同时使用。
- `--originator`、`--handler`、`--related-user` 需要用户标识，不要凭姓名猜测。
- `--region`、`--question-type-id`、`--priority`、`--stage`、`--tag` 支持重复传入或逗号分隔。
- `--keyword` 搜问题描述，`--message-keyword` 搜聊天记录。
- `--source-type` 和 `--source-location` 支持重复传入或逗号分隔；前者按来源类型筛选，后者按完整来源位置筛选。
- `--cli-source` 按 CLI 调用入口筛选，可选值为 `oncall-cli`、`bytecloud-cli` 或 `bytedcli`；通常与 `--source-type cli` 一起使用。
- `--solved` 支持 `true/false/1/0`；人工 Oncall 阶段值为 `launch_oncall`，不要猜成 `processing`。
- `--range Nd` 从今天零点向前取 N 天并覆盖到今天结束；`--range Nh` 从当前分钟向前取 N 小时。单位必须是小写 `d/h`，且不能与 `--created-after/--created-before` 同时使用。
- `--updated-within Nd/Nh` 按工单 `update_time` 查询滚动时间窗口，例如 `3d` 表示当前时刻向前 72 小时；不能与 `--updated-after/--updated-before` 同时使用。未显式指定排序时默认按更新时间倒序。
- `--message-updated-within Nd/Nh` 按 `last_update_message_time` 查询最近收到过新消息的工单；不能与 `--message-updated-after/--message-updated-before` 同时使用。未显式指定排序时默认按最后消息时间倒序。
- `--sort-by` 支持 `create-time`、`update-time`、`message-time` 和 `priority`。
- `--sort-order` 不能脱离 `--sort-by` 使用；分页值必须大于 0。

输出保留分页、核心工单字段、更新时间和最后消息时间，并自动省略空值。目标工单唯一时，可取结果中的 `id` 继续查询：

```bash
bytedcli oncall chat get --flow-id "<flow-id>" --format text
bytedcli oncall agent log-list --flow-id "<flow-id>" --format table
bytedcli oncall agent summary-get --flow-id "<flow-id>"
```

## `flow get`

```bash
bytedcli oncall flow get --id "<flow-id>" --format text
```

`--id` 是正整数 Oncall 工单 ID。结果直接返回单个工单，包含比列表更完整的人员、分类、时间线、群聊、标签和解决信息，并省略接口包装与空字段。

缺少工单 ID 但已有租户、人员、区域、分类、状态、关键词或时间范围时，先用 `flow list` 定位；候选不唯一时请用户确认。

## `flow timeline`

按时间倒序查看指定工单的创建、拉群、响应、等级变化、处理人变化、值班升级和解决等关键事件：

```bash
bytedcli oncall flow timeline --id "<flow-id>" --format table

bytedcli oncall flow timeline \
  --id "<flow-id>" \
  --event-type change_oncall_level \
  --all \
  --format json
```

- `--id` 是必填的正整数 Oncall 工单 ID。
- 默认按事件 ID 倒序返回，即最新事件在前；`--page` 和 `--page-size` 必须大于 0，默认分别为 `1` 和 `20`。
- `--all` 忽略分页并返回全部事件，适合完整复盘；事件较多时优先使用分页。
- `--event-type` 接受后端事件类型原值。常见值包括 `create_oncall`、`create_oncall_chat`、`response_oncall`、`change_oncall_level`、`solve_oncall_flow`、`init_async_oncall`、`change_handler_user`、`invite_duty_process_l1`、`invite_duty_process_l2`、`invite_duty_process_l3`。
- 输出包含事件时间、原始事件类型、展示名称、描述、操作人、变更前后状态和来源；没有事件时返回空列表。

## `flow meego-bind`

将已有 Meego Story 或 Issue 增量绑定到 Oncall 工单：

```bash
bytedcli oncall flow meego-bind \
  --id "<flow-id>" \
  --story-id "<story-id>" \
  --confirm \
  --format table

bytedcli oncall flow meego-bind \
  --id "<flow-id>" \
  --issue-id "<issue-id-1>,<issue-id-2>" \
  --confirm \
  --format json
```

- `--story-id` 和 `--issue-id` 必须且只能选一种，都支持重复传入或逗号分隔。
- 命令会先读取工单已有的同类 Meego 关联，合并新 ID 后再提交，不会删除原有绑定；重复 ID 会自动去重。
- 指定的 ID 已全部绑定时不发起写请求。
- 写操作必须携带 `--confirm`；绑定成功后 Oncall 服务会通知工单发起人。
- 工单所属租户必须已开启 Meego 集成，当前认证必须能解析为真实用户，并通过服务端的租户权限校验。
- 命令不支持 `--dry-run`：安全的增量请求必须先读取现有关联，而 dry-run 不执行该前置读取。

成功时返回工单 ID、Meego 类型、完整绑定 ID 和本次新增 ID。需要查看关联名称与链接时，再用 `flow get` 查询 `story_links` 或 `issue_links`。

## `flow update`

仅在用户明确要求修改工单标签后执行：

```bash
bytedcli oncall flow update \
  --id "<flow-id>" \
  --tag-id 22590,22591 \
  --confirm \
  --format table
```

- `--id` 是正整数 Oncall 工单 ID。
- `--tag-id` 是更新后的完整标签 ID 集合，支持重复传入或逗号分隔；命令会自动去重。
- 更新采用全量替换语义：未包含在 `--tag-id` 中的原标签会被移除，不是向现有标签增量追加。
- 写操作必须携带 `--confirm`，包括使用 `--dry-run` 预览请求时。
- 目前至少需要一个标签 ID，不支持通过该命令清空全部标签。
- 标签 ID 必须为正整数且处于启用状态。命令会在更新前读取工单所属租户及其标签；标签不存在、不属于该租户或未启用时直接失败，不发送更新请求。
- 可先运行 `tag list --tenant-id "<tenant-id>" --only-used` 获取可关联标签。
- `--dry-run` 只预览最终写请求，不执行标签状态前置查询；实际更新时仍会强制校验。

成功时输出工单 ID、更新后的标签 ID 和结果消息。需要确认标签名称时，更新后使用 `flow get` 查询工单详情。

## `flow close`

仅在用户明确要求关单后执行：

```bash
bytedcli oncall flow close \
  --id "<flow-id>" \
  --confirm \
  --format table
```

命令会先读取工单并执行以下校验：

- 工单必须由当前认证用户创建；无法确认创建人或当前用户时拒绝关单。
- 工单不得已关联 `oncall_chat_id` 或 `chat_id`；已拉群时应在群聊中继续处理。
- 工单已解决时不重复更新。
- 必须携带 `--confirm`；不得使用 service 或 raw API 绕过校验。

成功或已解决时输出 `flow_id`、`is_solved` 和说明；校验失败时以非零状态退出并保留具体原因。
