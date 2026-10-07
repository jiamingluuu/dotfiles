# DevFlow 修改泳道机房引用文档

本引用文档用于修改一个 DevFlow 任务中某条 PPE 泳道的部署机房。

## 何时使用

当用户明确表达以下意图时使用本引用文档：
- 换机房、改机房、调整部署机房
- 把某个泳道的服务挪到另一个机房去部署

## 参数获取优先级

按下面顺序收集参数，后者只用于补全缺失值，不能覆盖前者：

1. 用户当前对话中明确提供的信息
2. 当前工作目录和本地仓库上下文（`repo_name`、`branch` 可由 CLI 自动推断）
3. 后端 pending 文案中返回的候选机房列表
4. 无法自动补齐时，再与用户交互确认必要参数

如果同一参数同时在用户对话和本地上下文中出现，必须优先使用用户对话中的值。

## 目标参数

参考后端接口，请收集这些参数：
- `task_id`
- `repo_name`
- `branch`
- `lane`
- `dc_list`
- `region`

其中：
- `task_id` / `repo_name` / `branch` 用于定位任务，必须满足「提供 `task_id`」或「同时提供 `repo_name` 和 `branch`」之一
- `lane` 必填，且**只能传一个泳道**；要改多个泳道的机房必须分多次调用
- `lane` 必须是 `ppe_` 开头的泳道。**BOE 泳道不支持机房配置**，传 BOE 泳道会被明确拒绝
- `dc_list` 是目标机房，多个按 `<dc1>,<dc2>` 用逗号分隔，单个机房只传 `<dc1>`。**可以留空**：留空调用时后端会返回当前可选的机房列表，供用户选择
- `region` 可选，**只支持 `cn`**；非 cn 控制面不支持机房参数，不传即默认 cn

## 执行原则

- `dc_list` 中的机房代码必须大写（如 `LF`、`HL`）；用户提供小写时先转为大写，多个机房逐项处理
- **`dc_list` 会造成实际部署影响，严禁 AI 自动填写**。如果用户没有明确指定目标机房，**不要自己猜**：直接留空 `dc_list` 调用一次，把后端返回的候选机房列表原样展示给用户，由用户选定后再正式调用
- 注意与添加泳道的空值语义不同：本命令留空 `dc_list` 只用于探测候选机房；`develop-lane add` 添加 CN PPE 泳道时未传 `dc_list`，由后端默认使用 `LF`，AI 不主动填写，参见 `add-develop-lane.md`
- 如果用户指定了机房但无法理解其意图，直接把后端 pending 返回的候选机房列表原样展示给用户，要求用户手动选择；这是少数需要主动追问的场景，不能静默忽略该参数
- **修改机房会取消原有构建并按新机房重新部署**，必须在执行前向用户说明这一影响
- 机房是 `region` 维度的，与泳道名无关，不要根据泳道名推断机房
- 用户用「华北」「华北6」「华东」等分区名描述机房时，参见 `map-datacenter-region.md` 把分区名对应到具体 DC 代码；但分区通常含多个机房，不得据此替用户挑选，仍按上一条留空探测候选
- 如果目标机房与当前机房相同，后端会直接返回「无需修改」，不会触发重新部署
- 如果泳道不存在，后端会返回 pending 并列出该任务实际的泳道列表，此时应原样展示给用户确认
- 如果在完成本 skill 任务过程中需要使用其他 skill，必须使用名称带有 `bytedance-devflow-` 前缀的 skill

## 调用方式

```bash
bytedcli devflow develop-lane-dc update --task_id="<task_id>" --lane="<lane>" --dc_list="<dc1>,<dc2>" --bytedcli-skill-dir="<skill所在目录>"
```

不确定有哪些机房可选时，留空 `dc_list` 探测候选：

```bash
bytedcli devflow develop-lane-dc update --task_id="<task_id>" --lane="<lane>" --bytedcli-skill-dir="<skill所在目录>"
```

## 输出处理

- 直接返回原始输出
- 不主动改写、总结或格式化后端返回
- 只有用户明确要求解释时，再补充说明
- 如果命令返回 pending，必须优先原样展示 pending 文案（其中包含候选机房列表），再要求用户选择
- 如果命令失败，优先保留并展示原始错误信息，再补充最少量的必要说明

## 备注

- 本能力对应接口：`POST /openapi/mcp/develop/lane/dc/update`
- 对应底层 CLI action：`develop-lane-dc update`
- 修改机房后需要查看部署进度时，参见 `info-service.md`
- 如果在完成本 skill 任务过程中需要使用其他 skill，必须使用名称带有 `bytedance-devflow-` 前缀的 skill
