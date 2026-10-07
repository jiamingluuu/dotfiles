# 查看 DevFlow 任务信息

当用户需要查看、确认、检查某个 DevFlow task 的当前信息时，使用本能力。

本能力只处理未指向任何具体资源的泛化任务信息查询；如果用户已经明确提到某个资源，则应优先路由到该资源对应的信息查询文档，而不是继续使用本能力。

## 何时调用

- 用户明确说要查看 DevFlow task 详情、任务信息、任务状态、任务内容
- 用户提供了 `task_id`，希望确认该任务当前信息
- 用户没有 `task_id`，但当前仓库和分支可以定位到唯一的 DevFlow task，需要据此查询

以下场景不应优先使用本能力：

- 用户要查询服务的 DevFlow 任务信息、服务部署信息、泳道信息、scm 编译情况，应优先使用 `references/info-service.md`
- 用户要查询当前 DevFlow 任务下某个 TCC 资源的信息，应优先使用对应的 `references/*-tcc.md`

## 参数获取优先级

按下面顺序收集参数，后者只用于补全缺失值，不能覆盖前者：

1. 用户当前对话中明确提供的信息
2. 当前工作目录和本地仓库上下文

如果同一参数同时在用户对话和本地上下文中出现，必须优先使用用户对话中的值。

## 目标参数

以下参数在 skill 层都视为非必要参数；如果用户对话中没有明确指出，则可以不传：

- `task_id`：DevFlow 任务 ID；如果用户对话中没有明确指出，则可以不传，优先让 CLI 基于当前环境自动推断
- `repo_name`：仓库名称，例如 `iesarch/devflow_admin`；如果用户对话中没有明确指出，则可以不传，优先让 CLI 自动推断
- `branch`：目标分支名称；如果用户对话中没有明确指出，则可以不传，优先让 CLI 自动推断

补充说明：

- skill 层不要为了补齐这些参数频繁追问用户；用户未明确给出的参数，优先省略
- 若同时存在 `task_id` 与 `repo_name`/`branch`，以 `task_id` 为准定位任务

## 执行原则

- 不要为了补齐非必需参数频繁追问用户
- 能从当前对话、仓库上下文，直接使用
- 不需要执行任何 git 命令来获取参数
- 如果用户未明确指定 `task_id`、`repo_name`、`branch`，可以不传，这些都是非必须参数

## 调用命令

```bash
bytedcli devflow task info --task_id="<task_id>" --bytedcli-skill-dir="<skill所在目录>"
```

或：

```bash
bytedcli devflow task info --repo_name="<repo_name>" --branch="<branch>" --bytedcli-skill-dir="<skill所在目录>"
```

也可以同时传入三者；若存在 `task_id`，优先用它定位任务。

如果用户没有提供任何参数，也可以不使用任何参数，让 `bytedcli devflow` 基于当前环境自动透传到底层 CLI 进行推断。

## 输出处理

- 直接返回 `bytedcli devflow` 的原始输出
- 不主动改写、总结或格式化后端返回
- 只有用户明确要求解释时，再补充说明

## 备注

- 本能力对应接口：`GET /openapi/mcp/task/info`
- 如果在完成本 skill 任务过程中需要使用其他 skill，必须使用名称带有 `bytedance-devflow-` 前缀的 skill
