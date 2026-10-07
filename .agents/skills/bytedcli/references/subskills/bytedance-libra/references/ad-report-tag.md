# 广告报告辅助标签

使用 `libra ad-report tag` 管理广告报告里的独立标签配置。它使用 Libra Page/BFF 的现有登录身份及 `--site` 路由，不要求提供 Cookie 或 Token。实验详情的普通 `tags`、关注指标组 `metrics` 与这里的辅助标签是不同配置。

```bash
bytedcli --json --site <site> libra ad-report tag list --keyword demo-business
bytedcli --json --site <site> libra ad-report tag get --flight-id <flight_id>
# 预览要保存的合并配置；完整路径或 ID 均来自 tag list。
bytedcli --json --site <site> libra ad-report tag update --flight-id <flight_id> --tag-path 'demo-business/demo-tag'
# 明确提交，支持重复 --tag-path / --tag-id。
bytedcli --json --site <site> libra ad-report tag update --flight-id <flight_id> --tag-id <tag_id> --yes
```

- `list` 返回叶子标签的完整路径、ID、是否可选择、是否需要原因表单。`--keyword` 是本地路径子串过滤。目录一次读取，不分页或截断；JSON 以 `pagination: none`、`page: 1`、`page_size/current_count` 记录当前返回条数。
- `get` 返回已保存的辅助标签、决策标签、停用标签、绑定 ID、原因及核对时间。新建实验尚未配置时返回空标签列表、null 绑定 ID；可直接用 `update --yes` 完成首次配置。目录中已不存在的 ID 仍保留，路径可能为 null。
- `update` 只合并指定叶子标签，不做替换或删除。不接受模糊名称、父分类、停用标签；重复路径存在歧义时用 ID。添加需要新原因表单的标签时提示先在网页处理。
- 默认 `dry_run: true`，展示完整合并 payload，`persisted: false`；只有 `--yes` 才允许写。新增标签时启用报告的标签选择 (`clearEffectiveScenes: true`)；请求的标签均已存在时不改变该开关。
- 保存时保留已有辅助/停用标签、决策标签、原因和用户侧标签，之后 GET 校验。停用 ID 随请求保留，但不计入 `added_tag_ids`，回读允许其单独出现在停用列表。`--yes` 下已满足时返回 `changed: false`、`persisted: true`，不发 POST。业务流程应检查 `persisted`，不能仅判断进程成功或 dry-run 成功。
- 保存前重查并发修改；平台没有原子条件更新接口，仍需避免同时操作同一实验的报告编辑器。鉴权、参数或业务明确拒绝时直接报原错误。写入超时、网络故障或响应不确定时只回读，不自动重发，并保留 `write_error` 诊断；未核实成功时返回明确错误。重试同一命令会重新读取并合并当前状态。
- 新建实验推荐顺序：创建草稿 → 配置标签并核验 → 提交 Review → 审核后开启。标签影响数据产出与展示；运行后才添加只影响后续产数，历史回补需在平台单独处理。
- 具体业务默认标签由调用者/workflow 提供，CLI 不内置任何业务的默认名单，也不修改实验参数、流量或有效期。
