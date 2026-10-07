---
name: bytedance-obric
description: Obric 内部研发工具入口。用户提到 OBRIC CM ROM 构建、构建产物、自动挑单、Coverity、Jenkins、OpenGrok、Ocean Assistant/OAssistant Zeus、Omni Viewer、Session Viewer、Ocean Review 或 Quality Data 时使用。ROM 或 product/device/variant 走 obric pdm；仅明确 App Version 走 obric-pdm，不按 patch 数量或仓库路径路由。
---

# bytedcli obric

Obric 内部研发工具集命令聚合入口。根据具体任务加载对应 subskill，不在本文件重复展开各工具的命令和参数。

## PDM command routing

- 用户明确要求构建 ROM，或已提供 `product`、`device`、`variant` 这组 ROM
  参数时，加载 `bytedance-obric-pdm-rom`，使用 `bytedcli obric pdm version create`。
- 仅当用户明确要求 App Version，或明确提供 `repo-server`、`repo-name`、`branch`
  这组 App Version 参数时，才使用 `bytedcli obric-pdm app-version`。
- Gerrit patch 的数量和仓库路径都不是命令路由依据。同一仓库的 patch 可以用于完整 ROM
  构建，不能据此推断为 App Version。
- 用户只提供 patch、未说明目标产物且没有上述参数组合时，先确认要构建 ROM 还是 App
  Version；确认前不要执行创建命令或添加 `--yes`。
- 生成 ROM 创建命令时，每条 patch 分别使用一个 `--android-patch` 或
  `--gradle-patch`。不要用逗号拼接，不要把用户消息中的 Markdown 反引号写入参数。

## Subskills

- OBRIC CM 项目管理平台的 ROM 构建、构建产物和自动挑单候选 patch 查询：
  [bytedance-obric-pdm-rom](references/subskills/bytedance-obric-pdm-rom/GUIDE.md)
- Coverity 静态扫描 issue 查询、源码事件链和 triage 字段安全更新：
  [bytedance-obric-coverity](references/subskills/bytedance-obric-coverity/GUIDE.md)
- Obric Jenkins 构建状态、参数、变更、产物和控制台日志尾部查询：
  [bytedance-obric-jenkins](references/subskills/bytedance-obric-jenkins/GUIDE.md)
- Obric 内部研发工具集中的 OpenGrok 代码索引项目列表、代码搜索与 raw 文件读取：
  [bytedance-obric-opengrok](references/subskills/bytedance-obric-opengrok/GUIDE.md)
- Obric 内部研发工具集中的 Ocean Assistant 管理后台，支持 Omni Viewer、Session Viewer 和标注配置只读查询：
  [bytedance-oassistant-zeus](references/subskills/bytedance-oassistant-zeus/GUIDE.md)
- Obric 内部研发工具集中的 Ocean Review / Gerrit change 查询、文件与 diff 读取、评论读取和发布、review label 投票、topic 更新与 cherry-pick：
  [bytedance-ocean-review](references/subskills/bytedance-ocean-review/GUIDE.md)
- Obric 内部研发工具集中的 Quality Data 反馈列表、详情和搜索条件查询：
  [bytedance-quality-data](references/subskills/bytedance-quality-data/GUIDE.md)
