# DevFlow 添加泳道引用文档

本引用文档用于为一个已有的 DevFlow 任务添加泳道（开发调试环境）。

## 何时使用

当用户明确表达以下意图时使用本引用文档：
- 给任务加一个泳道、加一个 BOE / PPE 环境
- 需要在新的泳道上部署调试
- 需要为任务补一个指定机房的 PPE 泳道

## 参数获取优先级

按下面顺序收集参数，后者只用于补全缺失值，不能覆盖前者：

1. 用户当前对话中明确提供的信息
2. 当前工作目录和本地仓库上下文（`repo_name`、`branch` 可由 CLI 自动推断）
3. 后端 pending 文案提示中要求补齐的字段
4. 无法自动补齐时，再与用户交互确认必要参数

如果同一参数同时在用户对话和本地上下文中出现，必须优先使用用户对话中的值。

## 目标参数

参考后端接口，请收集这些参数：
- `task_id`
- `repo_name`
- `branch`
- `lane`
- `region`
- `env`
- `dc_list`

其中：
- `task_id` / `repo_name` / `branch` 用于定位任务，必须满足「提供 `task_id`」或「同时提供 `repo_name` 和 `branch`」之一
- `lane` 必填，须以 `boe_` 或 `ppe_` 开头；多个泳道按 `<lane1>,<lane2>` 用逗号分隔，一次性传入，单个泳道只传 `<lane1>`
- `region` 可选，取值 `cn` 或 `i18n`，不传默认 `cn`
- `env` 可选，取值 `boe` 或 `ppe`，不传时由 `lane` 前缀推导；传了但与 `lane` 前缀矛盾会被拒绝
- `dc_list` 可选，部署机房列表，多个按 `<dc1>,<dc2>` 用逗号分隔，单个机房只传 `<dc1>`。**机房只对 `ppe_` 泳道生效**，BOE 泳道的 `dc_list` 会被后端忽略；CN 控制面添加 PPE 泳道时未传 `dc_list`，由后端默认使用 `LF`，AI 不主动填写 `LF`

## 执行原则

- `dc_list` 中的机房代码必须大写（如 `LF`、`HL`）；用户提供小写时先转为大写，多个机房逐项处理
- 一次要加多个泳道时，必须用逗号一次性传入，不要拆成多次调用；拆开调用会放大与「删泳道」并发时的竞态风险
- 机房是 `region` 维度的，与泳道名无关，不要根据泳道名去推断机房
- 用户用「华北」「华北6」「华东」等分区名描述机房时，参见 `map-datacenter-region.md` 把分区名对应到具体 DC 代码；但分区通常含多个机房，不得据此替用户挑选并自动填 `dc_list`
- BOE 泳道不需要询问机房；对 BOE 泳道反复追问 `dc_list` 是错误行为
- `dc_list` 会造成实际部署影响；用户明确指定时按用户输入传递，未指定时 CN PPE 泳道由后端使用默认机房 `LF`。后端在机房不合法时会返回 pending 并列出候选机房，此时应把候选列表原样展示给用户，由用户选择
- 注意与修改泳道机房的空值语义不同：本命令未传 `dc_list` 时由后端使用默认机房；`develop-lane-dc update` 留空 `dc_list` 只用于探测候选机房，严禁 AI 自动填写，参见 `update-develop-lane-dc.md`
- 已存在的泳道不会重复添加，后端会在返回文案中说明哪些泳道已存在
- 如果在完成本 skill 任务过程中需要使用其他 skill，必须使用名称带有 `bytedance-devflow-` 前缀的 skill

## 调用方式

添加单个泳道：

```bash
bytedcli devflow develop-lane add --task_id="<task_id>" --lane="<lane1>" --bytedcli-skill-dir="<skill所在目录>"
```

添加带指定机房的 PPE 泳道：

```bash
bytedcli devflow develop-lane add --task_id="<task_id>" --lane="<lane1>" --dc_list="<dc1>,<dc2>" --bytedcli-skill-dir="<skill所在目录>"
```

一次添加多个泳道：

```bash
bytedcli devflow develop-lane add --task_id="<task_id>" --lane="<lane1>,<lane2>" --bytedcli-skill-dir="<skill所在目录>"
```

## 输出处理

- 直接返回原始输出
- 成功响应的 `data` 会返回最终生效的 `region` 与 `dc_list`；以该结构化结果为准
- 不主动改写、总结或格式化后端返回
- 只有用户明确要求解释时，再补充说明
- 如果命令返回 pending，必须优先原样展示 pending 文案（其中包含候选机房等信息），再根据提示补参
- 如果命令失败，优先保留并展示原始错误信息，再补充最少量的必要说明

## 备注

- 本能力对应接口：`POST /openapi/mcp/develop/lane/add`
- 对应底层 CLI action：`develop-lane add`
- 添加泳道后如果需要让服务在新泳道上运行，参见 `start-develop.md`
- 如果在完成本 skill 任务过程中需要使用其他 skill，必须使用名称带有 `bytedance-devflow-` 前缀的 skill
