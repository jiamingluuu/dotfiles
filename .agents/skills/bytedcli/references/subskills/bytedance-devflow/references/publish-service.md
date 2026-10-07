# DevFlow TCE 服务发布引用文档

本引用文档用于通过本仓库 CLI 调用 MCP 服务发布接口，为 TCE 服务创建 DevFlow 发布单。

## 何时使用

当用户明确表达以下意图时使用本引用文档：

- 创建 TCE 服务发布单、发起 TCE 服务发布或上线
- 基于发布参数、`deploy_info` 返回值或前端发布参数创建 TCE 发布单
- 用户明确要求调用 `/openapi/mcp/service/publish` 或 MCP 服务发布接口，且目标 provider 是 `TCE`

RDS 工单使用 `references/create-rds-ticket.md`，不要走本引用文档。

对已有 DevFlow 任务执行整体或单服务合码发布，以及查询任务、服务、发布单的发布状态时，使用 `references/publish-task.md`，不要走本引用文档。

## 参数获取优先级

按下面顺序收集参数

1. 用户当前对话中明确提供的发布参数
2. 用户指定了 `psm` 那么通过 `psm` 返回字段候选
3. 用户指定了 `repo_name` / `repo_path` 那么通过仓库路径返回字段候选
4. 用户未指定仓库和分支时，CLI 会从当前执行目录对应的 git 仓库自动推断 `repo_name` 和 `branch`，并写入 `repo_info.repo_path` / `repo_info.source_branch`
5. 后端 `pending` 文案提示中会返回字段候选，尽量不要通过其他 cli 命令去查
6. 不要使用 `service info` 去查，仅发布无法查询到


## 目标参数

基础定位参数：

- `psm`：可选，服务 PSM；可以先传递 `repo_path` 来查询候选服务
- `repo_path`：可选，服务仓库路径；不传是根据 `psm` 返回候选

发布参数：

- `provider`：固定使用 `TCE`
- `region`：发布区域、仅支持 `cn`
- `source_type`：可选，不传时后端默认按 `branch`；当前仅支持 `branch`
- `repo_id`：可选，不传是根据 `psm` 返回候选
- `repo_default_branch`：可选，不传是根据 `psm` 返回候选
- `repo_latest_commit_id`：可选，不传是根据 `psm` 返回候选
- `repo_latest_commit_msg`：可选，不传是根据 `psm` 返回候选
- `repo_source_branch`：可选，不传是根据 `psm` 返回候选
- `scm_id`：可选，不传是根据 `psm` 返回候选
- `scm_name`：可选，不传是根据 `psm` 返回候选
- `scm_repo_name`：可选，不传是根据 `psm` 返回候选
- `version_list`：依赖 SCM 版本列表，按 `ServicePublishScmVersionInfo` 结构严格解析。传 JSON 对象时可重复传多次；也可以一次传完整 JSON 数组
- `cluster_info_list`：发布集群列表，按 `ServicePublishClusterInfo` 结构严格解析。传 JSON 对象时可重复传多次；也可以一次传完整 JSON 数组
- `work_items`：关联 Meego / WorkItem 列表，按 `WorkItem` 结构严格解析。传 JSON 对象时可重复传多次；也可以一次传完整 JSON 数组
- `ppe_name`：测试泳道名称，可不填；不填时不要主动追问用户
- `emergency_publish`
- `user_confirm`

## 列表 JSON 字段

`version_list` 的每个对象按 `ServicePublishScmVersionInfo` 解析：

- 必填：`base_info`
- `base_info` 必填：`id`、`version`
- `base_info` 可选：`desc`、`scm_name`、`scm_id`
- 可选：`git_url`、`repos`、`branch_name`

`cluster_info_list` 的每个对象按 `ServicePublishClusterInfo` 解析：

- 必填：`id`、`name`、`is_standalone_release`
- 可选：`zone`、`physical_cluster`、`logical_cluster`、`region`、`is_locked`、`pre_merge_region`、`surge_num`、`surge_percent`、`canary_surge_percent`、`faas_function_id`
- 可选：`depend_scm`，其数组元素按 IDL 中的 `ServiceDeployScmVersionInfo` 解析

`work_items` 的每个对象按 `WorkItem` 解析：

- 必填：`id`、`name`、`work_item_type_key`、`project_key`、`simple_name`
- 可选：`link`、`source`、`str_id`、`project_name`、`work_item_no_bind_info`

## 执行原则

- 不要让用户直接输入完整请求 JSON；按上面的 flags 传参
- 如果仅知道服务的 psm 或者仓库，那么可以先传入这些参数，以获得其他参数的候选数据。可以通过多轮对话来获取全发布参数。
- `version_list`、`cluster_info_list`、`work_items` 是列表字段，不要拆成 `cluster_id` / `cluster_name` / `work_item_id` 这类单项参数
- 对列表字段，优先直接使用后端 `pending` 或服务信息返回的 JSON 对象 / JSON 数组；多个对象可以重复传同名 flag
- `ppe_name` 是测试泳道，可不填；用户未明确提供时不要为了补 `ppe_name` 中断流程
- 没有 DevFlow 任务或用户仅要求创建 TCE 服务发布单时，使用 `service publish`
- 只支持 TCE 分支发布；不要传 `scm`、`sql`、`command` 等 `source_type`
- 不要把 RDS、Redis、TCC、Repo、Lego、Gecko-Ufra 等资源转成 `service publish`
- 不要使用 `service publish` 代替已有 DevFlow 任务的 `publish qualitycheck`、`publish start` 或 `publish info`
- 如果后端返回的是参数缺失、参数不一致或任意校验未通过的 `pending`，禁止使用 `--user_confirm=true`；必须先修正参数，并且下次请求仍不能带 `--user_confirm=true`
- 只有后端校验全部通过并返回“请确认发布”这类确认提示时，需须将本次所有发布参数格式化后完整展示给用户，包括 `service`、`source_type`、`repo_info`、`scm_info`、`version_list`、`cluster_info_list`、`work_items`、`ppe_name`、`emergency_publish` 等已传入或后端补齐的字段，并询问用户是否确定以当前参数发布，必须需待用户手动确认后，才可继续
- 格式化展示优先使用缩进 JSON 或清晰的字段分组；不能只展示摘要、不能只转述“参数已校验通过”
- 用户看不到命令执行输出；因此当后端返回确认提示时，最终回复中也必须完整粘贴后端确认文案和完整发布配置，不能只在工具输出中展示，不能用摘要替代
- 如果在完成本 skill 任务过程中需要使用其他 skill，必须使用名称带有 `bytedance-devflow-` 前缀的 skill

## 调用方式

首次校验发布参数：

```bash
bytedcli devflow service publish --psm="<psm>" --provider="TCE" --region="<region>" --source_type="branch" --repo_id="<repo_id>" --repo_name="<repo_name>" --branch="<branch>" --repo_default_branch="<default_branch>" --repo_latest_commit_id="<commit_id>" --repo_latest_commit_msg="<commit_msg>" --scm_id="<scm_id>" --scm_name="<scm_name>" --scm_repo_name="<scm_repo_name>" --cluster_info_list='<cluster_info_json_object_or_array>' --bytedcli-skill-dir="<skill所在目录>"
```

多个列表项可以重复传同名 flag：

```bash
bytedcli devflow service publish --psm="<psm>" --provider="TCE" --region="<region>" --version_list='<version_json_object_1>' --version_list='<version_json_object_2>' --cluster_info_list='<cluster_json_object_1>' --cluster_info_list='<cluster_json_object_2>' --work_items='<work_item_json_object_1>' --work_items='<work_item_json_object_2>' --bytedcli-skill-dir="<skill所在目录>"
```

## 待用户确认时展示参数示例

每次待用户确认都需要完整展示全部参数。展示规则：

- 后端确认文案必须原样粘贴在最前面
- 无值字段写 `未传`，空列表写 `无`
- `version_list[].base_info.desc` 必须展示，且把描述中的换行压成空格
- 本轮等待用户确认时 `user_confirm` 必须展示为 `false`；用户确认后下一轮才可传 `true`

模板：
```text
后端确认提示：
<原样粘贴后端确认文案>

发布配置：
服务：
- 服务名：<service_name>
- Provider：TCE
- Region：cn
- SourceType：DEPLOY_SOURCE_TYPE_BRANCH

仓库：
- 仓库 ID：<repo_id>
- 仓库路径：<repo_path>
- 默认分支：<default_branch>
- 最新 Commit：<commit_id>

SCM 信息：
- SCM ID：<scm_id>
- SCM 名称：<scm_name>
- SCM 仓库：<scm_repo_name>

依赖版本：
- [1] Version ID：<base_info.id>，SCM ID：<base_info.scm_id>，SCM 名称：<base_info.scm_name>，版本：<base_info.version>，当前版本描述："<base_info.desc 去除换行>"
- [2] Version ID：<base_info.id>，SCM ID：<base_info.scm_id>，SCM 名称：<base_info.scm_name>，版本：<base_info.version>，当前版本描述："<base_info.desc 去除换行>"

发布集群：
- [1] ID：<id>，名称：<name>，Region：<region>，Zone：<zone>，物理集群：<physical_cluster>，逻辑集群：<logical_cluster>，独立发布：<is_standalone_release>
- [2] ID：<id>，名称：<name>，Region：<region>，Zone：<zone>，物理集群：<physical_cluster>，逻辑集群：<logical_cluster>，独立发布：<is_standalone_release>

Meego 绑定：
- [1] ID：<id>，名称：<name>，空间：<project_key>，类型：<work_item_type_key>，链接：<link>

发布选项：
- PPE 测试泳道：<ppe_name>
- 紧急发布：false
- 用户确认：false
```

## 输出处理

- 尽量原样展示 `bytedcli devflow` 的原始输出
- `pending` 时必须先把后端返回的提示原样展示给用户，再继续补参或发起确认
- 校验通过等待确认时，除了原样展示后端提示，还必须追加格式化后的完整发布参数，供用户逐项确认
- 如果校验通过后本轮即将结束，最终回复必须保留完整发布参数；不得因为最终回复要简洁而省略 `repo_info`、`scm_info`、`version_list`、`cluster_info_list`、`work_items`、`ppe_name`、`emergency_publish`
- 成功时保留后端返回的 `publish_url` 和下一步提示
- 失败时优先保留原始错误信息，只补充最少量必要说明
