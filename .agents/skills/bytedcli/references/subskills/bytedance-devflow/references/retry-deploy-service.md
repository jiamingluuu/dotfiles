# DevFlow 服务重试部署引用文档

本引用文档用于重试当前 DevFlow 任务里某个服务已有的部署流水线，不会创建新的 DevFlow 任务。

## 何时使用

当用户明确表达以下意图时使用本引用文档：

- 重试部署某个服务
- 重跑当前服务的部署流水线
- 在 DevFlow 上重试某个服务已有的部署流程

## 目标参数

- `task_id`：目标 DevFlow 任务 ID。若用户已明确给出，优先直接使用
- `repo_name`：仓库名称；若用户未明确给出，可不传。如果传入了，必须是类似 "iesarch/client_codegen" 这种两级形式
- `branch`：仓库分支；若用户未明确给出，可不传。
- `psm`：目标服务 PSM；如果用户明确指定了服务，则直接透传
- `lane`：目标泳道；如果用户明确指定了泳道，则直接透传
- `region`：目标 region；如果用户明确指定了 region，则直接透传
- `build_ctx_envs`：构建上下文环境变量字符串；如果用户明确指定了，则直接透传

补充说明：

- 所有的参数都不是必传。
- 这里的 `lane` 指 DevFlow 泳道，不是通用环境变量
- `build_ctx_envs` 作为字符串原样透传，不要在 skill 层改写成数组或对象参数列表
- 如果同一参数同时在用户对话和本地上下文中出现，必须优先使用用户对话中的值。

## 执行原则

- 不要为了补齐非必需参数频繁追问用户
- 能从当前对话、仓库上下文直接使用的参数直接使用
- 不需要执行任何 git 命令来获取参数
- 如果 CLI / OpenAPI 已返回 pending 候选项，优先按返回文案继续补参，不自行重写规则
- 如果在完成本 skill 任务过程中需要使用其他 skill，必须使用名称带有 `bytedance-devflow-` 前缀的 skill

## 调用方式

优先调用 `bytedcli devflow` 新增命令：

```bash
bytedcli devflow service retry_deploy --bytedcli-skill-dir="<skill所在目录>"
```

根据上下文补充参数，例如：

```bash
bytedcli devflow service retry_deploy --psm="<psm>" --lane="<lane>" --region="<region>" --build_ctx_envs='<build_ctx_envs>' --bytedcli-skill-dir="<skill所在目录>"
```

或者：

```bash
bytedcli devflow service retry_deploy --task_id="<task_id>" --psm="<psm>" --bytedcli-skill-dir="<skill所在目录>"
```

## 输出处理

- 尽量原样展示 `bytedcli devflow` 的原始输出
- 不主动对输出做总结、概要、改写、提炼或格式化
- 只有用户明确要求解释时，才补充说明
- 如果命令失败，优先保留原始错误信息，只补充最少量必要说明
