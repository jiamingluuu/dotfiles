# DevFlow 服务热部署开关引用文档

本引用文档用于设置某个 DevFlow 服务是否支持热部署，对应 `bytedcli devflow service set_hot_deploy` action。

## 何时使用

当用户明确表达以下意图时使用本引用文档：

- 开启或关闭某个服务的热部署能力
- 设置某个服务是否支持 hot deploy / hot deployment
- 基于 `task_id`、`psm`、`lane`、`region` 调用服务热部署开关 OpenAPI

## 参数获取优先级

按下面顺序收集参数，后者只用于补全缺失值，不能覆盖前者：

1. 用户当前对话中明确提供的信息
2. 当前工作目录和本地仓库上下文
3. CLI 内部自动推断逻辑

如果同一参数同时在用户对话和本地上下文中出现，必须优先使用用户对话中的值。

## 目标参数

- `support_hot_deploy`：是否支持热部署。该字段在 IDL 中为 required，必须由用户明确给出，传 `true` 表示开启/支持，传 `false` 表示关闭/不支持。不能在用户未明确确认时自行默认成 `false`
- `task_id`：目标 DevFlow 任务 ID。若用户已明确给出，优先直接使用
- `psm`：目标服务 PSM。若用户已明确给出，优先直接使用
- `lane`：目标泳道。若用户已明确给出，优先直接使用
- `region`：目标 region，例如 `cn`
- `repo_name`：仓库名称；若用户未明确给出，可不传，由 CLI 尝试从当前仓库自动推断
- `branch`：仓库分支；若用户未明确给出，可不传，由 CLI 尝试从当前仓库自动推断
- `devflow-openapi-env`：OpenAPI 环境。若用户明确要求 PPE，例如 `ppe_support_stop_hot_deploy`，通过全局参数 `--devflow-openapi-env="<env>"` 传入

## 执行原则

- `support_hot_deploy` 是必需的显式参数；如果用户没有明确要开启还是关闭，先询问确认
- 不要手动传入 JWT token；底层 CLI 会使用本地登录态自动注入认证 header
- 如果用户给出 PPE 环境，使用 `--devflow-openapi-env="<env>"`，底层 CLI 会自动注入 `x-tt-env` 和 `x-use-ppe`
- 不需要执行任何 git 命令来获取参数
- 如果在完成本 skill 任务过程中需要使用其他 skill，必须使用名称带有 `bytedance-devflow-` 前缀的 skill

## 调用方式

优先调用 `bytedcli devflow` 新增命令：

```bash
bytedcli devflow --devflow-openapi-env="<env>" service set_hot_deploy --task_id="<task_id>" --psm="<psm>" --lane="<lane>" --support_hot_deploy="<true|false>" --region="<region>" --repo_name="<repo_name>" --branch="<branch>" --bytedcli-skill-dir="<skill所在目录>"
```

如果不需要指定 PPE 环境，可以省略 `--devflow-openapi-env`：

```bash
bytedcli devflow service set_hot_deploy --task_id="<task_id>" --psm="<psm>" --lane="<lane>" --support_hot_deploy="<true|false>" --region="<region>" --bytedcli-skill-dir="<skill所在目录>"
```

示例：

```bash
bytedcli devflow --devflow-openapi-env="ppe_support_stop_hot_deploy" service set_hot_deploy --task_id="<task_id>" --psm="<psm>" --lane="<lane>" --support_hot_deploy="false" --region="<region>" --bytedcli-skill-dir="<skill所在目录>"
```

## 输出处理

- 尽量原样展示 `bytedcli devflow` 的原始输出
- 不主动对输出做总结、概要、改写、提炼或格式化
- 只有用户明确要求解释时，才补充说明
- 如果命令失败，优先保留原始错误信息，只补充最少量必要说明
