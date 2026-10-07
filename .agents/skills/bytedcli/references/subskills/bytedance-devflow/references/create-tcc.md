# DevFlow TCC 创建引用文档

本引用文档用于在当前 DevFlow 任务中，为某个服务新增一个 `tcc key`，并写入初始化配置。

## 何时使用

当用户明确表达以下意图时使用本引用文档：
- 在 DevFlow 任务上为某个服务创建一个 TCC key
- 为某个 `tcc_psm` 新增一条 TCC 配置
- 初始化某个 `tcc_key` 的值、描述、目录或值类型

## 参数获取优先级

按下面顺序收集参数，后者只用于补全缺失值，不能覆盖前者：

1. 用户当前对话中明确提供的信息
2. 当前工作目录和本地仓库上下文
3. `bytedcli devflow` 的自动推断能力

如果同一参数同时在用户对话和本地上下文中出现，必须优先使用用户对话中的值。

## 目标参数

参考后端接口，请尽量收集这些参数：
- `task_id`
- `repo_name`
- `branch`
- `tcc_psm`
- `tcc_key`
- `tcc_value`
- `description`
- `dir_name`
- `value_type`

其中：
- `tcc_psm`、`tcc_key` 通常应优先从用户请求中提取
- `tcc_value`、`description`、`dir_name` 如果用户提供了就直接透传；没提供时不必强制追问
- `value_type` 可选，仅支持以下 4 个小写值：

  | 取值 | 含义 |
  | --- | --- |
  | `string` | 普通字符串配置 |
  | `json` | JSON 配置 |
  | `yaml` | YAML 配置 |
  | `xml` | XML 配置 |

- 用户明确指定 `value_type` 时，按上述小写值原样传入，不要改写为大写或其他别名
- 用户未提供 `value_type` 时不必追问，也不要主动补传：合法的 JSON 对象或数组会自动识别为 `json`，其余内容自动识别为 `string`
- 自动识别只把 JSON 对象和数组归为 `json`；JSON 字符串、数字、布尔值等其他内容仍按 `string` 处理
- `task_id` 如果用户没有明确给出，可以留空，不必为了补齐它而打断流程
- `repo_name`、`branch` 如果用户没有给出，优先允许 `bytedcli devflow` 从当前工作目录自动透传到底层 CLI 进行推断

## 执行原则

- 不要为了补齐非必需参数频繁追问用户
- 能从当前对话确定的参数，直接使用
- `repo_name` 和 `branch` 若无用户明确输入，优先不传，让 CLI 基于当前目录推断
- 如果 `task_id`、`repo_name`、`branch` 都没有，也可以继续创建，让后端按空参数处理
- 如果用户没有提供 `tcc_psm` 或 `tcc_key`，且无法从当前对话唯一确定，再发起一次简短澄清
- 如果在完成本技能任务过程中需要使用其他技能，必须优先使用名称带有 `bytedance-devflow-` 前缀的技能

## 调用方式

优先调用 `bytedcli devflow` 新增命令：

```bash
bytedcli devflow tcc create --tcc_psm="<tcc_psm>" --tcc_key="<tcc_key>" --bytedcli-skill-dir="<skill所在目录>"
```

在以下情况下追加参数：

- 用户明确给出初始化值时：

```bash
bytedcli devflow tcc create --tcc_psm="<tcc_psm>" --tcc_key="<tcc_key>" --tcc_value="<tcc_value>" --bytedcli-skill-dir="<skill所在目录>"
```

- 用户明确给出任务或仓库上下文时：

```bash
bytedcli devflow tcc create --task_id="<task_id>" --repo_name="<repo_name>" --branch="<branch>" --tcc_psm="<tcc_psm>" --tcc_key="<tcc_key>" --bytedcli-skill-dir="<skill所在目录>"
```

- 用户同时给出描述、目录和值类型时：

```bash
bytedcli devflow tcc create --tcc_psm="<tcc_psm>" --tcc_key="<tcc_key>" --tcc_value="<tcc_value>" --description="<description>" --dir_name="<dir_name>" --value_type="<string|json|yaml|xml>" --bytedcli-skill-dir="<skill所在目录>"
```

- 用户同时给出全部参数时：

```bash
bytedcli devflow tcc create --task_id="<task_id>" --repo_name="<repo_name>" --branch="<branch>" --tcc_psm="<tcc_psm>" --tcc_key="<tcc_key>" --tcc_value="<tcc_value>" --description="<description>" --dir_name="<dir_name>" --value_type="<string|json|yaml|xml>" --bytedcli-skill-dir="<skill所在目录>"
```

## 输出处理

- 尽量将 `bytedcli devflow` 的原始输出原文展示
- 不要主动对输出做总结、概要、改写、提炼或格式化
- 除非用户明确要求解释结果，否则直接返回命令输出即可
- 如果命令失败，优先保留并展示原始错误信息，再补充最少量的必要说明
