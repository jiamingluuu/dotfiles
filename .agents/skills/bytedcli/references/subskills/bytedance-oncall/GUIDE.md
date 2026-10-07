---
name: bytedance-oncall
version: 1.4.0
description: "通过 bytedcli 查询和操作 Oncall，并对明确需要 Oncall 支持的产品故障执行完整排查和升级。用于查询工单及其关键事件时间线、修改工单标签、绑定 Meego Story 或 Issue、查询租户标签、召回工单 Artifact 知识、查看群聊、执行智能问答与总结，以及查询租户、问题区域与分类、值班人、值班配置、租户文档、公告和历史工单；还支持关闭自己创建且未关联群聊的工单，以及创建 Oncall、提单、P0 提单、发起 Oncall 或创建 Oncall 群。普通问题排查应先使用对应领域能力；仅在用户明确表达 Oncall 意图时进入升级流程。"
---

# oncall

## 使用边界

1. 执行任何 `bytedcli` 命令前，必须先读取公共技能 `bytedcli`，按其规则处理安装、认证、路由、通用参数和排障。
2. 本技能负责工单与时间线查询、智能问答、工单知识召回、租户标签查询、工单标签修改、Meego 工作项绑定、受限关单，以及具有明确 Oncall 意图的故障排查与升级。
3. 仅当用户明确要求“用 Oncall 排查”、创建 Oncall、提单、P0 提单、发起 Oncall 或创建 Oncall 群时，进入 [故障排查与升级](references/escalation.md)。普通的“看下问题”“排查/解决问题”、报错、异常、失败操作或业务阻碍本身不足以进入 Oncall 升级流程，应交给对应领域能力先处理。
4. `flow create` 和 `chat create` 只能按故障排查与升级流程调用：前者创建内部追踪工单，不代表已发起 Oncall；后者必须满足流程中的分类条件并经过用户最终确认。

## 快速路由

| 用户意图 | 命令 | 读取 |
|---|---|---|
| 用 Oncall 排查故障、创建 Oncall、提单、P0 提单、发起 Oncall、创建 Oncall 群 | `tenant search` → `question-type list` → `flow create` → 自助排查 → 按需 `chat create` | [故障排查与升级](references/escalation.md) |
| 查工单列表、我发起的工单、分配给我的工单 | `flow list` | [工单查询、更新与关单](references/flow.md) |
| 已知工单 ID 查详情 | `flow get` | [工单查询、更新与关单](references/flow.md) |
| 查工单创建、拉群、响应、升级、换处理人和解决等关键事件 | `flow timeline` | [工单查询、更新与关单](references/flow.md) |
| 全量替换工单标签 | `flow update` | [工单查询、更新与关单](references/flow.md) |
| 将已有 Meego Story 或 Issue 增量绑定到工单 | `flow meego-bind` | [工单查询、更新与关单](references/flow.md) |
| 关闭自己创建且未关联群聊的工单 | `flow close` | [工单查询、更新与关单](references/flow.md) |
| 查工单群聊 | `chat get` | [群聊信息](references/chat.md) |
| 执行智能问答 | `agent execute` | [智能问答与记录](references/gpt.md) |
| 查前置拦截、GPT/智能体问答记录 | `agent log-list` | [智能问答与记录](references/gpt.md) |
| 查工单或群聊总结 | `agent summary-get` | [智能问答与记录](references/gpt.md) |
| 查租户详情、搜租户、查我管理的租户 | `tenant get` / `tenant search` | [租户查询](references/tenant.md) |
| 查租户可用区域或问题分类 | `question-type list` | [问题分类与文档搜索](references/discovery.md) |
| 查租户标签 ID、中文名和层级信息 | `tag list` | [租户标签查询](references/tag.md) |
| 搜索租户文档 | `document search` | [问题分类与文档搜索](references/discovery.md) |
| 查值班人 | `duty-user get` | [值班人查询](references/duty-user.md) |
| 查租户默认值班、SLA、等级策略、L1/L2/L3 流程、值班假期和标准角色 | `duty-config get` | [值班配置查询](references/duty-config.md) |
| 查 P0/产品公告 | `notice list` | [公告与历史工单](references/notices-history.md) |
| 按问题描述搜相似历史工单 | `flow search` | [公告与历史工单](references/notices-history.md) |
| 按问题和租户线索召回工单 Artifact 知识 | `llms get` → `artifact get` | [工单知识召回](references/ticket-knowledge.md) |

## 执行规则

1. 优先使用已封装的 `bytedcli oncall ...` 命令，并在执行前读取上表对应的功能说明；选项、默认值和当前可用命令以 `bytedcli oncall <resource> <action> --help` 为准。
2. 用户说“工单 ID”时，按 `oncall_flow_id` / `flow_id` 处理；不要把它当成群 ID。
3. `flow timeline`、`chat get`、`agent log-list` 和 `agent summary-get` 需要工单 ID。缺少 ID 但已有人员、租户、区域、分类、状态、关键词或时间范围时，先用 `flow list` 定位；候选不唯一时请用户确认。
4. 查相似历史问题用 `flow search`；按工单字段精确筛选用 `flow list`。
5. 执行 `flow update` 前必须确认用户明确要求修改目标工单的标签，并携带 `--confirm`；`--tag-id` 是更新后的完整标签集合，不是增量追加。
6. 执行 `flow meego-bind` 前必须确认用户明确要求绑定目标工单与 Meego 工作项，并携带 `--confirm`；该操作会通知工单发起人，不支持 `--dry-run`。
7. 执行 `flow close` 前必须确认用户明确要求关闭目标工单，并携带 `--confirm`；不得绕过命令内的创建人和群聊关联校验。
8. 执行 `agent execute` 时，按 [智能问答与记录](references/gpt.md) 的实时转发规则处理流式输出。
9. 现有 Oncall 命令确实无法满足需求时，再按 [未封装能力处理](references/oncall-service.md) 逐级降级；不要猜测资源名、方法或参数。
10. 进入故障排查与升级时，先完整读取 [故障排查与升级](references/escalation.md)，然后按其停止条件、确认门禁和状态维护要求执行，不要只凭快速路由直接拼接写命令。

## 多步与排障

- 术语和同义词：[常用概念](references/glossary.md)
- 组合查询：[常见多步流程](references/workflows.md)
- 明确 Oncall 意图下的完整排查和升级：[故障排查与升级](references/escalation.md)
- 组件特有错误：[Oncall 排障](references/oncall-troubleshooting.md)
- 通用安装、认证、路由、schema 和网络问题：返回 `bytedcli`
