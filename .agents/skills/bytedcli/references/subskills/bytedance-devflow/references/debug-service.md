# DevFlow 服务 Debug 引用文档

本引用文档用于通过本仓库 CLI 在 DevFlow 平台上为当前项目开启 debug，或对已有 debug 进行重启。

## 何时使用

当用户明确表达以下意图时使用本引用文档：

- 在 DevFlow 上开启 debug
- 在 DevFlow 上重启 debug
- 为当前仓库或指定仓库分支发起一次服务 debug

## 参数获取优先级

按下面顺序收集参数，后者只用于补全缺失值，不能覆盖前者：

1. 用户当前对话中明确提供的信息
2. 当前工作目录和本地仓库上下文
3. `bytedcli devflow` 的自动透传能力

如果同一参数同时在用户对话和本地上下文中出现，必须优先使用用户对话中的值。

## 目标参数

参考 `DebugRequest`，以下参数都允许按需传递：

- `repo_name`：仓库名称，例如 `iesarch/devflow_admin`；如果用户对话中没有明确指出，则可以不传，优先让 CLI 自动推断
- `branch`：目标分支名称；如果用户对话中没有明确指出，则可以不传，优先让 CLI 自动推断
- `ide_type`：debug 使用的 IDE 类型；支持 `0/1/2`，也支持 `DEBUG_IDE_TYPE_GOLAND`、`DEBUG_IDE_TYPE_VSCODE`、`DEBUG_IDE_TYPE_WEBIDE` 及简写 `goland`、`vscode`、`webide`。用户未提供时可以不传，优先让 CLI 基于 IDE 内置终端环境变量自动识别。
- `env`：debug 目标环境；如果用户明确提供则直接透传，未提供时可以省略
- `cluster`：debug 目标集群；如果用户明确提供则直接透传，未提供时可以省略
- `idc`：debug 目标机房或 IDC 标识；如果用户明确提供则直接透传，未提供时可以省略

补充说明：

- 这里的 `env` 是 debug 接口本身的业务参数，不是 CLI 顶层的 `--devflow-openapi-env`
- `ide_type` 的枚举映射如下：`0=DEBUG_IDE_TYPE_GOLAND`、`1=DEBUG_IDE_TYPE_VSCODE`、`2=DEBUG_IDE_TYPE_WEBIDE`
- 如果 CLI 自动识别不到 `ide_type`，会直接停止并提示用户显式通过 `--ide_type` 重新执行
- skill 层不要为了补齐非必需参数频繁追问用户；用户未明确给出的参数，优先省略

## 执行原则

- `idc` 中的机房代码必须大写（如 `LF`、`HL`）；用户提供小写时先转为大写，多个机房逐项处理
- 不要为了补齐非必需参数频繁追问用户
- 能从当前对话、仓库上下文直接使用的参数直接使用
- 不需要执行任何 git 命令来获取参数
- 如果用户未明确指定 `repo_name`、`branch`、`ide_type`、`env`、`cluster`、`idc`，可以不传；其中 `ide_type` 由 CLI 自动识别，识别失败时再按 CLI 提示让用户显式指定
- 如果在完成本 skill 任务过程中需要使用其他 skill，必须使用名称带有 `bytedance-devflow-` 前缀的 skill

## 调用方式

优先调用 `bytedcli devflow` 新增命令：

```bash
bytedcli devflow service debug --bytedcli-skill-dir="<skill所在目录>"
```

根据上下文补充参数，例如：

```bash
bytedcli devflow service debug --repo_name="<repo_name>" --branch="<branch>" --ide_type="DEBUG_IDE_TYPE_VSCODE" --env="<env>" --cluster="<cluster>" --idc="<idc>" --bytedcli-skill-dir="<skill所在目录>"
```

## 输出处理

- 尽量原样展示 `bytedcli devflow` 的原始输出
- 不主动对输出做总结、概要、改写、提炼或格式化
- 只有用户明确要求解释时，才补充说明
- 如果命令失败，优先保留原始错误信息，只补充最少量必要说明
