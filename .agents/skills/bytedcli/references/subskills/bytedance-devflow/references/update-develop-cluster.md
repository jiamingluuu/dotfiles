# DevFlow 修改服务集群引用文档

本引用文档用于修改一个 DevFlow 任务中某个服务在指定泳道下的部署集群。

## 何时使用

当用户明确表达以下意图时使用本引用文档：
- 换集群、改集群、调整部署集群
- 某个服务要部署到别的集群上

## 参数获取优先级

按下面顺序收集参数，后者只用于补全缺失值，不能覆盖前者：

1. 用户当前对话中明确提供的信息
2. 当前工作目录和本地仓库上下文（`repo_name`、`branch` 可由 CLI 自动推断）
3. 后端 pending 文案中返回的候选集群列表
4. 无法自动补齐时，再与用户交互确认必要参数

如果同一参数同时在用户对话和本地上下文中出现，必须优先使用用户对话中的值。

## 目标参数

参考后端接口，请收集这些参数：
- `task_id`
- `repo_name`
- `branch`
- `psm`
- `lane`
- `clusters`

其中：
- `task_id` / `repo_name` / `branch` 用于定位任务，必须满足「提供 `task_id`」或「同时提供 `repo_name` 和 `branch`」之一
- `psm` 必填且只能传一个。**集群是「服务维度」的**，不同服务在同一泳道下可以用不同集群，所以必须指定 psm
- `lane` 必填且只能传一个。后端要靠 `task_id` + `psm` + `lane` 定位唯一的服务环境记录，缺 `lane` 会改错泳道
- `clusters` 是目标集群，多个按 `<cluster1>,<cluster2>` 用逗号分隔，单个集群只传 `<cluster1>`。**可以留空**：留空调用时后端会返回该服务当前可选的集群列表，供用户选择

## 执行原则

- **`clusters` 会造成实际部署影响，严禁 AI 自动填写**。如果用户没有明确指定目标集群，**不要自己猜**：直接留空 `clusters` 调用一次，把后端返回的候选集群列表原样展示给用户，由用户选定后再正式调用
- 如果目标集群不在候选列表内，后端会返回 pending 并列出当前可选集群，此时必须把候选列表原样展示给用户，由用户选择
- **不要擅自补充或猜测 `psm`**；如果任务下有多个服务而用户没说改哪个，必须先澄清
- **修改集群后端会自动触发目标服务、目标泳道的重新部署**，成功响应会返回新的 `build_id`；不要再调用 `develop start` 或 `service redeploy`，避免重复部署
- **不支持 Gecko-Ufra 项目**：这类项目的集群名与 app_sides、pids 联动，后端会返回 pending 引导用户走前端操作，不要尝试绕过
- TCC 等资源类服务没有集群概念，后端会明确拒绝
- 如果要改多个服务或多个泳道的集群，必须分多次调用
- 如果在完成本 skill 任务过程中需要使用其他 skill，必须使用名称带有 `bytedance-devflow-` 前缀的 skill

## 调用方式

```bash
bytedcli devflow develop-cluster update --task_id="<task_id>" --psm="<psm>" --lane="<lane>" --clusters="<cluster1>,<cluster2>" --bytedcli-skill-dir="<skill所在目录>"
```

不确定有哪些集群可选时，留空 `clusters` 探测候选：

```bash
bytedcli devflow develop-cluster update --task_id="<task_id>" --psm="<psm>" --lane="<lane>" --bytedcli-skill-dir="<skill所在目录>"
```

## 输出处理

- 直接返回原始输出
- 成功后通过返回的 `build_id` 确认重新部署已触发；如需查看进度，再调用 `service info`
- 不主动改写、总结或格式化后端返回
- 只有用户明确要求解释时，再补充说明
- 如果命令返回 pending，必须优先原样展示 pending 文案（其中包含候选集群列表），再要求用户选择
- 如果命令失败，优先保留并展示原始错误信息，再补充最少量的必要说明

## 备注

- 本能力对应接口：`POST /openapi/mcp/develop/cluster/update`
- 对应底层 CLI action：`develop-cluster update`
- 修改集群成功后会自动触发重新部署，无需额外调用其他部署命令
- 如果在完成本 skill 任务过程中需要使用其他 skill，必须使用名称带有 `bytedance-devflow-` 前缀的 skill
