# Lego 命令参考索引

本文档保留为路由层兼容入口，不承载完整正文。按任务加载下列文件，路径以本文档所在 `references/` 目录为基准。

- 选择 site / region、处理认证：`sites-and-auth.md`
- plugin get / register / compile / version / compile-detail / commit / branch：`plugin-actions.md`
- pipeline / scope / order / confirm / step-info：`release-actions.md`
- 判断编译、工单或步骤状态；处理错误码：`statuses-and-errors.md`

加载规则：

- 单个 plugin 查询或编译任务只加载 `plugin-actions.md`，需要判断状态时再加载 `statuses-and-errors.md`。
- 发布信息收集、创单和跟踪加载 `release-actions.md`，需要判断状态时再加载 `statuses-and-errors.md`。
- site、region 或认证已经确认时，不重复加载 `sites-and-auth.md`。
- 端到端编译发布按阶段加载资料，不要一次读取全部 reference。
