---
name: bytedance-devflow
description: 面向 DevFlow 任务创建/查看/关闭、构建或清理本地工作区、空间项目列表查询、Meego/需求列表查询、Meego 绑定、资源查询、启动开发、泳道和集群管理、代码评审人管理、服务部署/发布/重试部署/删除部署/开启 debug、任务提测、任务发布前检查/合码上线/发布状态查询、发布流水线信息查询、服务热部署开关、RDS 工单创建、API Design（查看 IDL API 设计流水线 / 查看本地 IDL diff / IDL 拉取 / 创建 API / 新增接口 / 更新本地依赖 / 修改 IDL / 提交 IDL 变更 / 本地接口定义定位）、添加服务到 DevFlow 任务，以及 TCC key 查询/创建/修改/删除、仓库评论查询的统一入口。当用户提到 DevFlow、服务信息、项目信息、部署情况、发布单、发布流水线、发布流水线详情、任务提测、能否提测、任务能否合码发布、任务或服务合码上线、当前发布状态或执行原子、泳道信息、服务 MR 信息、TCC 部署信息、RDS 工单、服务部署、服务发布、服务重试部署、开启/关闭服务热部署、设置是否支持 hot deploy、在 DevFlow 上开启或重启 debug、启动开发（开始开发）、添加/删除 BOE/PPE 泳道、修改机房/服务集群、添加/删除/查询代码评审人（reviewer）、催审、查看空间项目列表、查看我的 Meego 列表、查询某个 Meego、Meego 关联任务查询、将 Meego 绑定到 DevFlow task、获取 IDL 文件、查看 IDL API 设计流水线、查看本地 IDL diff、创建 API、新增接口、修改 IDL、更新本地依赖、查找某个接口在哪个 IDL 文件、查询 DevFlow 任务下仓库的代码 review 评论，或发起代码评审时使用。对 API/IDL 场景默认按 DevFlow 流程处理；仅当用户明确指定不使用 DevFlow，或当前场景明确不属于 DevFlow skill 的能力范围时，不触发本 skill 的 API Design 流程。
---
# DevFlow 技能

本技能是 DevFlow 相关能力的统一入口，覆盖以下场景：

- DevFlow 任务创建、查询、关闭
- 构建本地工作区
- 扫描和清理本地 DevFlow 任务工作区构建产物
- 查询某个业务空间下的项目列表
- 查询与当前用户或关键词相关的 Meego 列表
- DevFlow 服务与资源信息查询, 包括服务信息、项目信息、TCC 部署信息、部署情况、泳道信息、服务MR信息
- DevFlow 资源查询，尤其是根据 `meego_id` 查询关联任务和资源
- 将指定 Meego issue 绑定到某个 DevFlow task
- 发起 DevFlow 任务代码评审，支持基于当前 task 或当前仓库分支发起，并在提交前展示默认 reviewer 供用户确认
- DevFlow 服务部署、重试部署、删除部署、开启或重启 debug
- DevFlow 任务 RD 提测
- DevFlow 服务发布单创建、任务发布前检查、任务或服务合码发布、发布状态与流水线查询
- DevFlow 启动开发，以及泳道添加、泳道删除、泳道机房修改、服务集群修改
- DevFlow 代码评审人添加、删除、查询与催审
- DevFlow 服务热部署开关设置
- DevFlow RDS 工单创建
- 当前 DevFlow 任务里的 TCC key 查询、创建、修改、删除
- 更新当前 DevFlow 任务相关的 IDL / codegen 依赖
- API Design：查看 IDL API 设计流水线、查看本地 IDL diff、拉取目标服务 IDL、创建 API、更新本地依赖、提交本地 IDL 变更、按接口名/RpcMethod/path/Req/Resp 定位本地 IDL 文件
- 查询 DevFlow 任务下某个仓库 MR 的评论明细

使用该工具时，非必要信息尽量不要与用户进行交互，尽可能快速完成相关操作。

## Scripts

- `bytedcli devflow ...`：DevFlow 工作流命令入口，运行时由 bytedcli 自动准备。AI 按 skill 调用时应显式追加 `--bytedcli-skill-dir="<skill所在目录>"`，把当前 skill 安装目录透传进去做 agent 推断。

## 何时使用

当用户明确表达以下意图时使用本技能：

- 创建新的 DevFlow 任务
- 查看或关闭现有 DevFlow 任务
- 构建本地工作区、初始化本地工作区、拉取 DevFlow 任务工作区
- 扫描本地 DevFlow 工作区占用，或清理已完成/全部变更已合入任务的本地构建产物
- 查看空间项目列表或 Biz 下项目列表
- 查看一下我的 meego 列表，或按 meego 链接 / meego id / meego 名称查询 meego
- 将某个 Meego issue 绑定到指定 DevFlow task
- 查询服务部署信息、服务信息、项目信息、TCC 部署信息、部署情况、泳道信息、服务MR信息
- 发起服务部署、重试部署或删除某个服务部署
- 对已有 DevFlow 任务发起 RD 提测
- 创建服务发布单，检查任务是否可合码发布，发起任务或单服务合码发布，或查询任务、服务、发布单的发布状态
- 启动开发、开始开发，让任务下已绑定的服务与泳道跑起来
- 给任务加泳道、删泳道，添加或移除 BOE / PPE 环境
- 修改某条 PPE 泳道的部署机房，或修改某个服务在指定泳道下的部署集群
- 添加、删除、查询代码评审人，或催促评审人尽快评审
- 开启或关闭某个服务的热部署能力，或设置服务是否支持 hot deploy
- 创建某个 RDS 资源的 DDL / DML / CLEAR 工单
- 添加服务到 DevFlow 任务
- 在当前项目对应的 DevFlow 服务上开启 debug 或重启 debug
- 查询、创建、修改或删除当前 DevFlow 任务里的 TCC key
- 查询当前 DevFlow 任务下某个仓库的代码 review 评论
- 提到 DevFlow/TCC 配置管理，且需要先识别具体动作再继续处理
- 提到“更新当前任务相关 IDL 依赖 / codegen 依赖 / 一键更新全部 IDL 依赖”，且目标是直接在当前 Go 仓库内执行依赖更新
- 提到“获取 IDL 文件”“拉取 IDL”“查看 IDL API 设计流水线”“查看 API 流水线”“查看本地 IDL diff”“修改 IDL”“提交 IDL 变更”“创建 API”“新增接口”“更新本地依赖”“更新 codegen 依赖”“idl info”“idl diff”“idl pull”“idl save”“idl new_interface”“codegen update”，且用户未明确排除 DevFlow 流程
- 提到“查找 xxx 接口在哪个 IDL 文件”“定位接口定义位置”“这个 rpc/method/path 是哪个 proto/thrift 定义的”“idl search_api”，且目标是在当前项目已经 `idl pull` 下来的本地 IDL 中反查接口所在文件

## References

- [query-tcc.md](references/query-tcc.md): 当用户要查询、查看、确认某个 `tcc_psm + tcc_key` 当前配置内容时，加载并阅读该文档。
- [create-tcc.md](references/create-tcc.md): 当用户要在当前任务中为某个服务新增 `tcc key`，并写入初始值、描述或类型信息时，加载并阅读该文档。
- [edit-tcc.md](references/edit-tcc.md): 当用户要修改、更新、覆盖某个 `tcc_psm + tcc_key` 的配置值时，加载并阅读该文档。
- [delete-tcc.md](references/delete-tcc.md): 当用户要删除、移除某个 `tcc_psm + tcc_key` 配置时，加载并阅读该文档。
- [info-task.md](references/info-task.md): 当用户要查看、确认、检查某个 DevFlow task 的当前信息时，加载并阅读该文档。
- [build-workspace.md](references/build-workspace.md): 当用户要构建本地工作区、初始化本地工作区或拉取 DevFlow 任务工作区时，加载并阅读该文档。
- [cleanup-workspace.md](references/cleanup-workspace.md): 当用户要扫描或清理本地 DevFlow 任务工作区时，加载并阅读该文档。
- [query-develop-comments.md](references/query-develop-comments.md): 当用户要查看、确认、整理某个 DevFlow task 下指定仓库的 code review 评论时，加载并阅读该文档。
- [list-project.md](references/list-project.md): 当用户要查看某个 `biz_id` 下的空间项目列表时，加载并阅读该文档。
- [list-work-item.md](references/list-work-item.md): 当用户要查看自己的 meego/需求 列表，或按 meego 链接、meego id、meego 名称/描述查询 meego 候选列表时，加载并阅读该文档；对应命令入口为 `work_item list`。
- [info-service.md](references/info-service.md): 当用户要查询服务部署信息、服务信息、项目信息、TCC 部署信息、部署情况、泳道信息、服务MR信息或 scm 编译情况时，加载并阅读该文档。
- [deploy-service.md](references/deploy-service.md): 当用户要创建新的 DevFlow 任务并发起服务部署或泳道部署，或在当前仓库/分支上发起一次服务部署或泳道部署，添加服务到 DevFlow 任务时，加载并阅读该文档。如果用户在使用该文档创建任务的同时提供`meego_id`,则再执行`add_meego-task.md`将`meego_id`绑定到新创建的任务。
- [submit-quality.md](references/submit-quality.md): 当用户明确要求对已有 DevFlow 任务执行提测、提交测试或发起 RD 提测时，加载并阅读该文档。
- [publish-task.md](references/publish-task.md): 当用户要检查 DevFlow 任务能否合码发布、对已有任务执行整体或单服务合码发布，或查询任务、服务、发布单的完整发布状态、当前流水线、当前执行原子及错误信息时，加载并阅读该文档。
- [publish-service.md](references/publish-service.md): 当用户要基于发布参数创建服务发布单、发起服务发布，或要求调用 MCP 服务发布接口时，加载并阅读该文档。
- [query-publish_pipeline.md](references/query-publish_pipeline.md): 当用户只需要根据 `task_id + psm` 查询发布流水线 ID 时，加载并阅读该文档。
- [debug-service.md](references/debug-service.md): 当用户要在 DevFlow 上为当前项目开启 debug、重启 debug，或指定 `repo_name/branch/ide_type/env/cluster/idc` 发起一次 debug 时，加载并阅读该文档；其中 `ide_type` 支持 `DEBUG_IDE_TYPE_GOLAND`、`DEBUG_IDE_TYPE_VSCODE`、`DEBUG_IDE_TYPE_WEBIDE`。
- [create-rds-ticket.md](references/create-rds-ticket.md): 当用户要在 DevFlow 里为某个 RDS 资源创建 DDL / DML / CLEAR 工单，或用户明确提到“发 RDS 工单”“创建数据库工单”“提交 SQL 变更单”时，加载并阅读该文档。
- [retry-deploy-service.md](references/retry-deploy-service.md): 当用户要重试当前 DevFlow 任务里某个服务已有的部署流水线，或按 `task_id/repo_name/branch/psm/lane/region` 触发一次服务重试部署，并且用户当前动作不涉及提交或git push的时候，加载并阅读该文档。
- [set-hot-deploy-service.md](references/set-hot-deploy-service.md): 当用户要开启/关闭某个服务的热部署能力，或按 `task_id/psm/lane/region/repo_name/branch` 设置 `support_hot_deploy` 时，加载并阅读该文档。
- [search-resource.md](references/search-resource.md): 当用户要按 `meego_id` / meego 链接查询 DevFlow 关联任务，按任务标题关键词或创建者搜索任务，搜索可部署资源或可添加到 DevFlow 任务的资源，或表达“先帮我搜索下 xxx，再加到 DevFlow 任务里”这类先搜再继续处理的意图时，加载并阅读该文档。
- [add\_meego-task.md](references/add_meego-task.md): 当用户要把某个 Meego issue 绑定到指定 DevFlow task，或把当前仓库/分支对应任务和某个 `meego_id` 关联起来时，加载并阅读该文档。
- [create-develop-review.md](references/create-develop-review.md): 当用户要为某个 DevFlow task 或当前仓库分支发起代码评审、补 reviewer、确认后提交代码评审时，加载并阅读该文档。
- [delete-service.md](references/delete-service.md): 当用户要删除某个 DevFlow 任务里的服务部署，或移除指定 `psm` 的部署时，加载并阅读该文档。
- [close-task.md](references/close-task.md): 当用户要关闭、结束、终止某个 DevFlow task 时，加载并阅读该文档。
- [design-api.md](references/design-api.md): 当用户要查看 IDL API 设计流水线、查看本地 IDL diff、获取 IDL 文件、创建 API、修改 IDL、更新本地依赖或提交本地 IDL 变更时，默认加载并阅读该文档；只有用户明确指定不使用 DevFlow，或场景明确不属于 DevFlow skill 时不加载。
- [start-develop.md](references/start-develop.md): 当用户要启动开发、开始开发，或在手工添加泳道后要让服务跑起来时，加载并阅读该文档。注意「新建任务并部署」应走 `deploy-service.md`，不要重复调用本能力。
- [add-develop-lane.md](references/add-develop-lane.md): 当用户要给 DevFlow 任务添加泳道、添加 BOE / PPE 环境，或要为任务补一个指定机房的 PPE 泳道时，加载并阅读该文档。
- [delete-develop-lane.md](references/delete-develop-lane.md): 当用户要删除某个泳道、移除某个 BOE / PPE 环境，或清理不再使用的调试泳道时，加载并阅读该文档；这是破坏性操作，执行前须与用户确认。
- [update-develop-lane-dc.md](references/update-develop-lane-dc.md): 当用户要换机房、改机房、调整某条 PPE 泳道的部署机房时，加载并阅读该文档。
- [map-datacenter-region.md](references/map-datacenter-region.md): 当用户用「华北」「华北6」「华东」等分区名描述机房，需要把它对应到具体 DC 代码（如 LF、XH、HJ）时，加载并阅读该文档；这是翻译辅助，不改变「严禁 AI 自动填写机房」的约束。
- [update-develop-cluster.md](references/update-develop-cluster.md): 当用户要换集群、改集群、调整某个服务在指定泳道下的部署集群时，加载并阅读该文档。
- [add-reviewer.md](references/add-reviewer.md): 当用户要给 DevFlow 任务加评审人、加 reviewer 时，加载并阅读该文档；这只调整名单，发起评审仍走 `create-develop-review.md`。
- [delete-reviewer.md](references/delete-reviewer.md): 当用户要删除评审人、移除 reviewer、把某人从评审名单里去掉时，加载并阅读该文档。
- [list-reviewer.md](references/list-reviewer.md): 当用户要查看评审人列表、确认谁在 review、查看谁还没通过评审时，加载并阅读该文档。
- [notify-reviewer.md](references/notify-reviewer.md): 当用户**显式要求**催审、催评审、提醒 reviewer 看代码时，加载并阅读该文档；这是唯一会向真人发飞书消息的能力，禁止自主催审。

## 使用原则

- 本文档作为 DevFlow 总入口，负责先识别任务、部署、TCC 等大类场景
- 如果用户提到的是“DevFlow 任务信息”，不要直接默认走 `references/info-task.md`；应先判断用户描述里是否已经指向某个资源
- 一旦用户提到 DevFlow 任务下的某个资源，优先路由到该资源对应的信息查询路径，而不是泛化路由到 `references/info-task.md`
- 例如：查询服务的 DevFlow 任务信息，或查询 TCC 的部署信息，应优先加载并阅读 `references/info-service.md`
- 例如：查询当前 DevFlow 任务下某个 TCC 资源的信息，应优先加载并阅读对应的 `references/*-tcc.md`
- 当需求落在服务部署或泳道部署上时，加载并阅读 `references/deploy-service.md`
- 当用户明确要求对已有 DevFlow 任务执行提测时，加载并阅读 `references/submit-quality.md`
- 当需求落在任务发布前检查、已有任务整体或单服务合码发布，或发布状态、当前流水线、当前执行原子及错误信息查询时，加载并阅读 `references/publish-task.md`
- 当需求落在 TCE 服务发布单创建、TCE 服务发布，或用户要求调用 MCP TCE 服务发布接口时，加载并阅读 `references/publish-service.md`
- 当需求只要求根据 `task_id + psm` 返回发布流水线 ID 时，加载并阅读 `references/query-publish_pipeline.md`
- 当需求落在服务重试部署、重跑部署流水线、重试当前部署流程，并且用户当前动作不涉及提交或git push的时候，加载并阅读 `references/retry-deploy-service.md`
- 当需求落在开启/关闭服务热部署能力，或设置某个服务是否支持 hot deploy 时，加载并阅读 `references/set-hot-deploy-service.md`
- 当需求落在在 DevFlow 上开启 debug 或重启 debug 时，加载并阅读 `references/debug-service.md`
- 当需求落在 RDS 工单创建、数据库 DDL / DML / CLEAR 发单，或涉及重命名表、truncate table、清空表、drop table、删除表等清表类需求时，加载并阅读 `references/create-rds-ticket.md`
- 涉及 DevFlow CLI / OpenAPI 返回 `pending` 的场景时，必须优先把返回文案原样展示给用户，再继续追问、补参或请求确认；不能只做摘要式转述
- 当需求落在服务部署信息、服务信息、项目信息、TCC 部署信息、部署情况、泳道信息、服务MR信息查询上时，加载并阅读 `references/info-service.md`
- 当需求是泛化的 DevFlow task 信息查看，且未提及任何具体资源时，加载并阅读 `references/info-task.md`
- 当需求落在构建本地工作区、初始化本地工作区或拉取 DevFlow 任务工作区时，加载并阅读 `references/build-workspace.md`
- 当需求落在扫描磁盘中的 DevFlow 工作区、查看可清理任务或清理工作区构建产物时，加载并阅读 `references/cleanup-workspace.md`
- 当需求落在某个 DevFlow task 下仓库评论、未解决评论、MR 评论线程查询时，加载并阅读 `references/query-develop-comments.md`
- 当需求落在空间项目列表查询，或用户提供 `biz_id` 要查看项目列表时，加载并阅读 `references/list-project.md`
- 当需求落在 Meego/需求 列表查询、Meego 候选查询，或用户说“查看一下我的 meego/需求 列表”“帮我查询 xxx meego/需求”时，加载并阅读 `references/list-work-item.md`
- 当需求落在 DevFlow 资源搜索、按 `meego_id` / meego 链接查询关联任务、按任务标题关键词或创建者搜索任务、搜索可部署资源或可添加到 DevFlow 任务的资源、，或表达“先帮我搜索下 xxx，再加到 DevFlow 任务里”这类先搜再继续处理的意图时，加载并阅读 `references/search-resource.md`；若同时要求任务搜索和可部署资源搜索，应提示拆成两次调用
- 当需求落在把某个 Meego issue 绑定到 DevFlow task 上时，加载并阅读 `references/add_meego-task.md`
- 当需求落在发起任务代码评审、补 reviewer、确认提交代码评审时，加载并阅读 `references/create-develop-review.md`
- 当需求落在服务部署、添加服务到 DevFlow 任务上时，加载并阅读 `references/deploy-service.md`
- 当需求落在启动开发、开始开发时，加载并阅读 `references/start-develop.md`。**注意与 `service deploy` 的边界**：「新建任务并部署」只需 `deploy-service.md`，它创建任务后已自动启动开发；`start-develop.md` 用于启动已有任务，或在手工添加泳道后启动开发，避免重复触发流水线
- 当需求落在给任务加泳道、添加 BOE / PPE 环境时，加载并阅读 `references/add-develop-lane.md`
- 当需求落在删除泳道、移除 BOE / PPE 环境时，加载并阅读 `references/delete-develop-lane.md`；这是破坏性操作，执行前必须与用户确认具体泳道名
- 当需求落在换机房、改机房、调整部署机房时，加载并阅读 `references/update-develop-lane-dc.md`；机房只对 `ppe_` 泳道生效，BOE 泳道不要追问机房
- 当需求落在换集群、改集群、调整部署集群时，加载并阅读 `references/update-develop-cluster.md`；集群是「服务维度」的，必须同时指定 `psm` 与 `lane`
- **机房代码统一使用大写**：传入 `dc`、`dc_list`、`idc` 时，具体机房代码必须大写（如 `LF`、`HL`、`XH`）；用户输入小写时先转为大写，多个机房逐项处理。该规则只调整已明确机房代码的大小写，不用于推断或自动选择机房；`region`、`env`、泳道名和集群名沿用各自格式
- **机房与集群是两件事，不要混淆**：机房（`dc_list`）是泳道维度的，集群（`clusters`）是服务维度的。用户说「换机房」走 `update-develop-lane-dc.md`，说「换集群」走 `update-develop-cluster.md`；语义不清时必须先追问
- 当用户用「华北」「华北6」「华东」等分区名指代机房时，加载并阅读 `references/map-datacenter-region.md` 把分区名对应到具体 DC 代码；但分区通常含多个机房，AI 不得据此替用户挑选并自动填 `dc_list`，仍需按下面「修改部署机房 / 添加泳道」原则处理
- 当需求落在加评审人、删评审人、查看评审人列表时，加载并阅读对应的 `references/*-reviewer.md`
- `reviewer list` 的评审人标注、仓库分组和排序均由后端完成；必须原样返回 CLI 输出，不得自行补充 `MR 创建者` 标记、调整仓库顺序或重新排版
- **「调整评审人名单」与「发起代码评审」是两件事**：前者走 `references/add-reviewer.md` / `references/delete-reviewer.md`，后者走 `references/create-develop-review.md`。正确顺序是先调整名单，再发起评审
- 当需求落在催审、催评审、提醒 reviewer 时，加载并阅读 `references/notify-reviewer.md`。**催审必须由用户显式要求**：禁止自主催审、禁止把它作为「评审未通过」的自动补救动作、禁止在同一轮对话中重复催审；如果用户只是问「谁还没通过评审」，那是查询意图，应走 `references/list-reviewer.md`
- **修改部署集群**：`clusters` 为空时不要在本地拦截，直接调用后端，并将 pending 返回的候选集群列表原样展示给用户选择；选定集群并修改成功后，后端会自动触发目标服务、目标泳道的重新部署，不要额外调用 `develop start` 或 `service redeploy`；严禁 AI 自动填写
- **修改部署机房**：`dc_list` 为空时不要在本地拦截，直接调用后端，并将 pending 返回的候选机房列表原样展示给用户选择；严禁 AI 自动填写
- **添加泳道**：CN 控制面添加 `ppe_` 泳道且 `dc_list` 为空时，后端默认使用 `LF`，无需向用户追问机房；BOE 泳道不配置机房
- 当需求落在删除服务部署上时，加载并阅读 `references/delete-service.md`
- 当需求落在关闭 DevFlow task 上时，加载并阅读 `references/close-task.md`
- 当需求落在 TCC 资源上时，先判断具体 action，再加载并阅读匹配的引用文档
- 当需求落在“更新当前 DevFlow 任务相关 IDL / codegen 依赖”时，不要回退到 task/service/tcc 查询路径；应先完成 API Design 目录预检，再在目标业务仓库根目录走 direct 模式执行 `bytedcli devflow --caller direct codegen update --bytedcli-skill-dir="<skill所在目录>"`，并仅在用户显式提供 `task_id` / `psm` / `repo_name` / `branch` 时补充对应参数
- 当需求落在 API Design（查看 IDL API 设计流水线 / 查看本地 IDL diff / 获取 IDL 文件 / 创建 API / 修改 IDL / 更新本地依赖 / 提交 IDL 变更）时，默认进入 DevFlow API Design 流程；不要回退到 task/service/tcc 查询路径，应加载 `references/design-api.md`，再按文档执行 `idl info` / `idl diff` / `idl pull` / `idl new_interface` / `codegen update` / `idl save`。
- 只有在以下两类情况下不进入本流程：
  - 用户明确指定不使用 DevFlow，例如“不走 DevFlow”“不要用 bytedance-devflow skill”“只直接修改本地 IDL 仓库”。
  - 当前需求明确不是 DevFlow skill 场景，即操作对象、工具或流程已明确属于其他系统，与 DevFlow 无关。不得仅因为用户未主动提到 DevFlow，就判定为非 DevFlow 场景。
- 不进入 DevFlow 流程时，不加载 `references/design-api.md`，也不对其 IDL 编辑、校验、codegen 或 Git 提交方式施加约束。
- 执行 API Design 的本地相关动作前，必须先按 `references/design-api.md` 完成执行目录预检：
  - 当前位于 Git 仓库时，统一在 Git 仓库根目录执行。
  - 当前位于 devflow 工作区时，先根据 `.devflow-workspace.json`、`AGENTS.md` 以及用户或上下文中的 PSM/完整仓库名确定目标仓库，再进入该仓库根目录执行。
  - 已确认在工作区但无法唯一确定目标 PSM/仓库时，必须向用户展示候选并确认；确认前禁止执行本地 IDL 命令或修改文件。
  - 当前目录既不是 Git 仓库也不是可验证的 DevFlow 工作区时，禁止直接执行本地相关动作，避免在错误目录生成 `.devflow` 或 `idl_*`。
- **进入 DevFlow API Design 流程后，新增接口 / 创建 API 必须执行 `idl new_interface`，禁止用 Edit/Write 手改 DevFlow 拉取的本地 `.proto` / IDL 工作区实现新接口。** 只有命中上述排除条件时该约束才不生效，详见 `references/design-api.md`。
- 对 direct 模式参数优先级保持如下顺序：显式 `task_id` > 显式 `psm` > 显式 `repo_name + branch` > 由 CLI 根据当前仓库自动补全 `repo_name/branch`
- 查询任务、服务或发布单的发布状态、当前流水线、当前执行原子或报错时，优先使用 `publish info`，不要误用 `service info` 或仅返回流水线 ID 的 `publish_pipeline query`
- 没有 DevFlow 任务或仅创建 TCE 服务发布单的场景使用 `service publish`；对已有 DevFlow 任务执行合码或启动发布使用 `publish start`
- 对已有多服务任务执行发布时，发布范围必须明确：只有用户明确提供目标 PSM 才能发起服务级动作；只有用户明确表达“整个任务”“全部服务”“整体发布”等任务级范围时，才能发起任务整体合码上线；用户未明确 PSM 或任务级范围时必须先澄清，禁止默认整体发布，也禁止根据 `qualitycheck` 的“可发服务”自动选择部分服务发布
- 如果用户同时出现“发布”和“部署”，或无法判断是创建 TCE 发布单还是对已有任务执行合码发布，必须先追问确认，不能默认选择写操作。
- 主文档不再重复展开 task、service、TCC action 的参数和命令细节，避免与引用文档重复维护
- 如果用户意图同时涉及多个 TCC 动作，例如先查后改，可以依次阅读多个引用文档
- 后续如新增新的 DevFlow action 文档，也应继续维护在当前 skill 目录下的 `references/` 中，并同步更新本文件里的触发场景说明
- 完成当前 skill 的任务时，若还需要使用其他 skill，必须优先使用名称带有 `bytedance-devflow-` 前缀的技能。

## 场景分流

以下能力已拆分为独立引用文档，命中对应场景时应先加载并阅读相应文档，再执行命令：

- DevFlow 任务创建 / 服务部署 / 泳道部署 / 添加服务到 DevFlow 任务：`references/deploy-service.md`
- DevFlow 任务 RD 提测：`references/submit-quality.md`
- DevFlow 任务发布前检查 / 任务或单服务合码发布 / 发布状态、流水线、当前原子查询：`references/publish-task.md`
- DevFlow 启动开发 / 开始开发（任务已存在，非新建任务场景）：`references/start-develop.md`
- 给任务添加泳道 / 添加 BOE、PPE 环境：`references/add-develop-lane.md`
- 删除泳道 / 移除 BOE、PPE 环境：`references/delete-develop-lane.md`
- 换机房 / 改机房 / 调整 PPE 泳道的部署机房：`references/update-develop-lane-dc.md`
- 换集群 / 改集群 / 调整服务的部署集群：`references/update-develop-cluster.md`
- 添加代码评审人 / 加 reviewer：`references/add-reviewer.md`
- 删除代码评审人 / 移除 reviewer：`references/delete-reviewer.md`
- 查看评审人列表 / 查看谁还没通过评审：`references/list-reviewer.md`
- 催审 / 催评审 / 提醒 reviewer（须用户显式要求）：`references/notify-reviewer.md`
- DevFlow TCE 服务发布单创建 / TCE 服务发布 / 上线单 / 上线发布 / 创建服务发布单：`references/publish-service.md`
- DevFlow 发布流水线 ID 查询：`references/query-publish_pipeline.md`
- DevFlow 服务重试部署 / 重跑已有部署流水线, 并且用户当前动作不涉及提交或git push：`references/retry-deploy-service.md`
- DevFlow 服务热部署开关设置：`references/set-hot-deploy-service.md`
- 在 DevFlow 上开启 debug / 重启 debug：`references/debug-service.md`
- 创建 RDS 工单：`references/create-rds-ticket.md`
- 查看服务相关的 DevFlow 任务信息 / 服务部署信息 / 项目信息 / TCC 部署信息 / 泳道信息 / 服务MR信息 / scm 编译情况：`references/info-service.md`
- 删除 DevFlow 服务部署：`references/delete-service.md`
- 关闭 DevFlow 任务：`references/close-task.md`
- 查看泛化的 DevFlow 任务信息（未指向任何具体资源）：`references/info-task.md`
- 构建本地工作区 / 初始化本地工作区：`references/build-workspace.md`
- 扫描 / 清理本地 DevFlow 任务工作区：`references/cleanup-workspace.md`
- 查看 DevFlow 任务下某个仓库的 MR 评论 / 未解决评论：`references/query-develop-comments.md`
- 查看空间项目列表：`references/list-project.md`
- 查看我的 Meego/需求 列表 / 按 Meego 链接、Meego ID、Meego 描述查询候选：`references/list-work-item.md`
- 按 `meego_id` / meego 链接查询 DevFlow 关联任务、按任务标题关键词或创建者搜索任务、搜索可部署资源或可添加到 DevFlow 任务的资源、先搜索再继续添加到任务：`references/search-resource.md`
- 将 Meego 绑定到 DevFlow task：`references/add_meego-task.md`
- 发起 DevFlow 任务代码评审：`references/create-develop-review.md`
- TCC 查询 / 创建 / 修改 / 删除：加载对应 `references/*-tcc.md`
- 更新当前任务相关 IDL / codegen 依赖：直接执行 `bytedcli devflow --caller direct codegen update [--task_id <task_id>] [--psm <psm>] [--repo_name <repo_name>] [--branch <branch>] --bytedcli-skill-dir="<skill所在目录>"`
- DevFlow API Design（查看 IDL API 设计流水线 / 查看本地 IDL diff / IDL 拉取 / 创建 API / 修改 IDL / 更新本地依赖 / 提交 IDL 变更）：默认加载 `references/design-api.md`，只有用户明确指定不使用 DevFlow，或场景明确不属于 DevFlow skill 时不加载。流程内的“新增接口 / 创建 API”必须走 `idl new_interface`。
