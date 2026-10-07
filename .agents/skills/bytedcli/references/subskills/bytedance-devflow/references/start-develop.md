# DevFlow 启动开发引用文档

本引用文档用于为一个已有的 DevFlow 任务启动开发，触发其下已绑定服务与泳道的部署流水线。

## 何时使用

当用户明确表达以下意图时使用本引用文档：
- 启动开发、开始开发、跑起来、部署一下当前任务
- 手工添加了泳道之后，需要让服务在新泳道上跑起来

**不要在下面这种情况下使用本引用文档**：用户是「新建任务并部署」，这条路径应使用 `service deploy`。`service deploy` 创建任务成功后已经会自动启动开发，此时再调用本命令会导致流水线被触发两次。本命令用于启动已有任务，或在手工添加泳道后启动开发。

## 参数获取优先级

按下面顺序收集参数，后者只用于补全缺失值，不能覆盖前者：

1. 用户当前对话中明确提供的信息
2. 当前工作目录和本地仓库上下文（`repo_name`、`branch` 可由 CLI 自动推断）
3. 无法自动补齐时，再与用户交互确认必要参数

如果同一参数同时在用户对话和本地上下文中出现，必须优先使用用户对话中的值。

## 目标参数

参考后端接口，请收集这些参数：
- `task_id`
- `repo_name`
- `branch`

其中：
- 三个参数都不是必填，但必须满足「提供 `task_id`」或「同时提供 `repo_name` 和 `branch`」之一
- `repo_name` 和 `branch` 在当前仓库内执行时可以由 CLI 自动推断，通常不需要显式传入
- `repo_name` 与 `branch` 必须配对出现，只给其中一个无法反查任务

## 执行原则

- 本命令是异步操作，返回成功只代表流水线已触发，不代表服务已就绪
- 启动成功后应引导用户通过 `service info` 查询部署进度，不要直接告知用户服务已可用
- 如果后端返回 pending 提示任务未绑定服务或泳道，必须原样展示该提示，并按提示先调用 `service deploy` 或 `develop-lane add`
- 不要因为担心没启动成功而反复调用本命令；请先通过 `service info` 确认部署进度
- 如果在完成本 skill 任务过程中需要使用其他 skill，必须使用名称带有 `bytedance-devflow-` 前缀的 skill

## 调用方式

```bash
bytedcli devflow develop start --task_id="<task_id>" --bytedcli-skill-dir="<skill所在目录>"
```

在目标仓库目录内执行时，可以省略全部参数，由 CLI 自动推断仓库与分支：

```bash
bytedcli devflow develop start --bytedcli-skill-dir="<skill所在目录>"
```

## 输出处理

- 直接返回原始输出
- 不主动改写、总结或格式化后端返回
- 只有用户明确要求解释时，再补充说明
- 如果命令返回 pending，必须优先原样展示 pending 文案，再根据提示补参或执行前置命令
- 如果命令失败，优先保留并展示原始错误信息，再补充最少量的必要说明

## 备注

- 本能力对应接口：`POST /openapi/mcp/develop/start`
- 对应底层 CLI action：`develop start`
- 如果在完成本 skill 任务过程中需要使用其他 skill，必须使用名称带有 `bytedance-devflow-` 前缀的 skill
