# DevFlow 删除泳道引用文档

本引用文档用于删除一个 DevFlow 任务下的泳道。**这是破坏性操作**，会连带回收该泳道下的服务资源。

## 何时使用

当用户明确表达以下意图时使用本引用文档：
- 删除某个泳道、移除某个 BOE / PPE 环境
- 清理不再使用的调试泳道

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
- `lane`
- `region`

其中：
- `task_id` / `repo_name` / `branch` 用于定位任务，必须满足「提供 `task_id`」或「同时提供 `repo_name` 和 `branch`」之一
- `lane` 必填，是要删除的泳道名；多个泳道按 `<lane1>,<lane2>` 用逗号分隔，单个泳道只传 `<lane1>`
- `region` 可选，取值 `cn` 或 `i18n`，不传默认 `cn`；后端按 `lane` + `region` 唯一确定泳道
- 删除泳道不需要 `env` 与 `dc_list`，本命令也不提供这两个参数

## 执行原则

- **删除泳道是破坏性操作**，会回收该泳道下的服务资源。执行前必须先向用户确认要删除的具体泳道名，不要在目标泳道不明确时直接执行
- 不要把「删除泳道」和「修改泳道机房」混淆；如果用户只想换机房，应使用 `update-develop-lane-dc.md`
- 不允许删除任务下的所有泳道，后端会拒绝并返回提示
- 如果要删的泳道不存在，后端会返回 pending 并列出该任务当前实际的泳道列表，此时应把列表原样展示给用户确认
- 一次删多个泳道时用逗号一次性传入，不要拆成多次调用
- 如果在完成本 skill 任务过程中需要使用其他 skill，必须使用名称带有 `bytedance-devflow-` 前缀的 skill

## 调用方式

删除单个泳道：

```bash
bytedcli devflow develop-lane delete --task_id="<task_id>" --lane="<lane1>" --bytedcli-skill-dir="<skill所在目录>"
```

一次删除多个泳道：

```bash
bytedcli devflow develop-lane delete --task_id="<task_id>" --lane="<lane1>,<lane2>" --bytedcli-skill-dir="<skill所在目录>"
```

## 输出处理

- 直接返回原始输出
- 不主动改写、总结或格式化后端返回
- 只有用户明确要求解释时，再补充说明
- 如果命令返回 pending，必须优先原样展示 pending 文案（其中包含该任务实际的泳道列表），再与用户确认
- 如果命令失败，优先保留并展示原始错误信息，再补充最少量的必要说明

## 备注

- 本能力对应接口：`POST /openapi/mcp/develop/lane/delete`
- 对应底层 CLI action：`develop-lane delete`
- 如果在完成本 skill 任务过程中需要使用其他 skill，必须使用名称带有 `bytedance-devflow-` 前缀的 skill
