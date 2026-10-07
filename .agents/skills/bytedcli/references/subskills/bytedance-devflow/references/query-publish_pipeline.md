# DevFlow 发布流水线信息查询引用文档

本引用文档用于兼容旧场景，通过本仓库 CLI 查询某个 DevFlow 任务下指定服务的发布流水线 ID，对应 `bytedcli devflow publish_pipeline query`。

如果用户需要完整发布状态、流水线状态、当前执行原子、原子状态或错误信息，应改用 `references/publish-task.md` 中的 `publish info`。

## 何时使用

当用户明确表达以下意图时使用本引用文档：

- 只查询发布流水线 ID 或发布 pipeline ID
- 已经有 `task_id` 和服务 `psm`，需要定位对应发布流水线
- 用户明确提供 `task_id + psm`，只要求返回发布流水线 ID

## 参数获取优先级

按下面顺序收集参数，后者只用于补全缺失值，不能覆盖前者：

1. 用户当前对话中明确提供的 `task_id` 和 `psm`
2. 上一步创建发布单或查询任务信息时得到的 `task_id` 和服务 PSM
3. 后端 pending 文案提示中要求补齐的字段

## 目标参数

- `task_id`：DevFlow 任务 ID
- `psm`：服务 PSM

这两个参数都应显式传入。不要用当前本地仓库、分支或 provider 猜测 `psm`。

## 执行原则

- 查询接口只负责返回发布流水线 ID，不负责创建发布单
- 用户泛化询问“当前发布到哪一步”“当前执行原子是什么”“发布失败原因是什么”时，不使用本接口，改用 `publish info`
- 如果后端返回发布信息不存在或流水线不存在的 pending 文案，必须原样展示给用户
- 如果用户没有提供 `task_id` 或 `psm`，可以先调用命令让后端返回 pending，也可以直接要求用户补齐；不要自行猜测
- 如果在完成本 skill 任务过程中需要使用其他 skill，必须使用名称带有 `bytedance-devflow-` 前缀的 skill

## 调用方式

```bash
bytedcli devflow publish_pipeline query --task_id="<task_id>" --psm="<psm>" --bytedcli-skill-dir="<skill所在目录>"
```

## 输出处理

- 尽量原样展示 `bytedcli devflow` 的原始输出
- 成功时输出中会包含 `pipeline_id=<id>`
- `pending` 时必须先把后端返回的提示原样展示给用户，再继续补参或提示用户确认发布单是否已创建
- 失败时优先保留原始错误信息，只补充最少量必要说明
