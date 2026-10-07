# 用例与断言

本页命令使用 SmartQ OpenAPI 认证。写操作默认返回请求预览，确认目标和内容后加 `--yes` 提交；`--dry-run` 与 `--yes` 互斥。写请求失败后先核对服务端状态，再决定是否重新提交。

## 节点、复制和历史

```bash
# 修改指定节点；未传字段保持原值
bytedcli smartq case-set node update --space-id 1000 --case-set-id 2000 --body-json '{"case_nodes":{"demo-node":{"text":"示例步骤","tags":[]}}}'

# 从一个用例集复制指定自动化用例
bytedcli smartq case-set case copy --space-id 1000 --case-set-id 2000 --source-case-set-id 3000 --source-auto-node-id demo-auto-node

# 复制多个来源用例集的用例
bytedcli smartq case-set case copy --space-id 1000 --case-set-id 2000 --body-json '{"cases":[{"caseset_id":3000,"node_id":"demo-auto-node"}]}'

# 将源子树粘贴到目标脑图节点；可重复传源节点
bytedcli smartq case-set node copy --space-id 1000 --case-set-id 2000 --node-id demo-target --source-case-set-id 3000 --source-node-id demo-source

# 编辑历史每页最多 100 条，默认 10 条
bytedcli --json smartq case-set history list --space-id 1000 --case-set-id 2000 --page 2 --page-size 20

# 用例执行历史；支持 android、ios、web，limit 默认 10，最多 100
bytedcli --json smartq case-set run list --space-id 1000 --case-set-id 2000 --node-id demo-case --device-platform web --limit 20

# 查询 Meego 需求关联的用例集、任务和计划
bytedcli --json smartq case-set related list --meego-id 1000

# 抢占编辑权限：先核对预览中的目标与接管用户，再加 --yes
bytedcli smartq case-set edit-lock execute --space-id 1000 --case-set-id 2000 --username demo-user

# 旧 Xmind 接口仅在部分空间可用；通常使用 case-set get
bytedcli --json smartq case-set xmind get --case-set-id 2000
bytedcli --json smartq case-set get --space-id 1000 --case-set-id 2000
```

`node update` 的 `case_nodes` 是节点 ID 到变更对象的映射。可更新 `node_type`、`text`、`tags`、`priority`、`plugins`、`platform_auto_status`；空数组、`false` 等显式值会保留。复杂内容也可通过互斥的 `--body-file` 提供。

`case copy` 使用参数指定来源时，`--source-case-set-id` 与至少一个非空的 `--source-auto-node-id` 必须同时提供；也可用互斥的 `--body-json` 或 `--body-file` 指定完整 `cases` 数组。

`node copy` 的 `--source-node-id` 选择源子树，`--source-auto-node-id` 进一步筛选含指定自动化节点的子树。目标 `--node-id` 是粘贴位置，需与源节点参数同时提供，两者不要互换。

`history list` 默认每页 10 条，返回 `page`、`page_size` 和后端总数。`run list` 按时间倒序返回最近 N 条执行记录，不提供页码或游标参数。输出中的 `limit` 是记录数量上限；`truncated` 表示已达到上限，可能还有更早的记录。需要更多记录时可增加 `--limit`，最多 100 条。执行历史要求有空间权限的 operator，默认从当前登录身份取得，也可显式传 `--operator`。

## Webdiff 断言

规则绑定到自动化步骤的 AutoID。这里的 `--auto-node-id` 对应接口 `node_id`，应使用步骤 AutoID，不要替换为用例节点 ID。

```bash
bytedcli --json smartq assert-rule get --case-set-id 2000 --auto-node-id demo-auto-step

# check_rule 必须是字符串；规则结构由对应断言类型决定
bytedcli smartq assert-rule create --case-set-id 2000 --auto-node-id demo-auto-step --rule-type ui --body-file ./demo-rule.json
bytedcli smartq assert-rule update --assert-rule-id 3000 --case-set-id 2000 --auto-node-id demo-auto-step --rule-type ui --body-file ./demo-rule.json

# 指定用例范围，或显式选择整个任务；两者互斥
bytedcli smartq assert-rule benchmark update --task-id 4000 --case-node-id demo-case
bytedcli smartq assert-rule benchmark update --task-id 4000 --all-cases
```

`--source` 当前支持 `mnt`，`--device-platform` 当前支持 `web`，两者都有默认值。`--rule-type` 支持 `ui`、`video`、`ui-stamp`、`stamp-check`。JSON 文件中的 `check_rule` 是序列化后的规则字符串；可选字段包括 `step`、`max_step`、`base_screen_shot`、`base_control_tree`。`--body-json` 与 `--body-file` 互斥。

基准更新会用指定任务的当前运行截图与控件树更新关联规则。`--all-cases` 对应省略 `case_node_id_list`；`--case-node-id` 可重复或用逗号分隔。预览会说明更新范围。
