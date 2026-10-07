# DevFlow TCC 修改引用文档

本引用文档用于修改当前 DevFlow 任务中某个服务下指定 `tcc key` 的值。

## 何时使用

当用户明确表达以下意图时使用本引用文档：
- 修改 DevFlow 任务中的 TCC key 值
- 调整某个服务在当前任务里的 TCC 配置内容
- 将某个 `tcc_psm + tcc_key` 更新为新的 `tcc_value`

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

其中：
- `tcc_psm`、`tcc_key`、`tcc_value` 通常应优先从用户请求中提取
- `task_id` 如果用户没有明确给出，可以留空，不必为了补齐它而打断流程
- `repo_name`、`branch` 如果用户没有给出，优先允许 `bytedcli devflow` 从当前工作目录自动透传到底层 CLI 进行推断

## 执行原则

- 不要为了补齐非必需参数频繁追问用户
- 能从当前对话确定的参数，直接使用
- `repo_name` 和 `branch` 若无用户明确输入，优先不传，让 CLI 基于当前目录推断
- 如果 `task_id`、`repo_name`、`branch` 都没有，也可以继续修改，让后端按空参数处理
- 如果用户没有提供 `tcc_psm`、`tcc_key` 或 `tcc_value`，且无法从当前对话唯一确定，再发起一次简短澄清
- 如果用户是在“修改已有值”，尤其是 JSON、YAML、XML、脚本或其他多行文本，优先先查询当前值，再基于原文做最小改动，尽可能保留原有换行、缩进、字段顺序和首尾空白
- 不要为了“美化格式”主动重新排版 `tcc_value`，除非用户明确要求统一格式
- 对 JSON 值，禁止通过 `python -c`、`json.loads`、`json.dumps` 或其他“解析后整体重建文本”的方式生成最终写回内容；这类做法会改变原有格式
- 如果确实需要借助 JSON 解析能力，只能用于校验最终文本是否合法，不能把 `json.dumps` 的输出作为最终提交内容
- 如果用户要修改 JSON 中的局部字段，应优先在原文本上做最小替换，而不是把整个 JSON 反序列化后重新序列化
- 对于多行或需要严格保留格式的 `tcc_value`，优先把最终内容原样写入临时文件，再使用 `--tcc_value_file` 调用，避免命令行转义或首尾空白丢失
- 如果在完成本技能任务过程中需要使用其他技能，必须优先使用名称带有 `bytedance-devflow-` 前缀的技能

## 调用方式

优先调用 `bytedcli devflow` 新增命令：

```bash
bytedcli devflow tcc edit --tcc_psm="<tcc_psm>" --tcc_key="<tcc_key>" --tcc_value="<tcc_value>" --bytedcli-skill-dir="<skill所在目录>"
```

当 `tcc_value` 是多行文本或需要尽可能保留原格式时，优先使用文件参数：

```bash
bytedcli devflow tcc edit --tcc_psm="<tcc_psm>" --tcc_key="<tcc_key>" --tcc_value_file="<temp_file>" --bytedcli-skill-dir="<skill所在目录>"
```

在以下情况下追加参数：

- 用户明确给出 `task_id` 时：

```bash
bytedcli devflow tcc edit --task_id="<task_id>" --tcc_psm="<tcc_psm>" --tcc_key="<tcc_key>" --tcc_value="<tcc_value>" --bytedcli-skill-dir="<skill所在目录>"
```

- 用户明确给出 `repo_name`、`branch` 时：

```bash
bytedcli devflow tcc edit --repo_name="<repo_name>" --branch="<branch>" --tcc_psm="<tcc_psm>" --tcc_key="<tcc_key>" --tcc_value="<tcc_value>" --bytedcli-skill-dir="<skill所在目录>"
```

- 用户同时给出所有参数时：

```bash
bytedcli devflow tcc edit --task_id="<task_id>" --repo_name="<repo_name>" --branch="<branch>" --tcc_psm="<tcc_psm>" --tcc_key="<tcc_key>" --tcc_value="<tcc_value>" --bytedcli-skill-dir="<skill所在目录>"
```

## 格式保持

- 修改已有 TCC 值时，默认目标是“语义正确且格式最小变更”
- 如果当前值本身就是格式化后的 JSON，不要擅自压成单行，也不要重新按新的缩进风格整体格式化
- 如果只修改 JSON 中的局部字段，应尽量保持未修改部分的文本内容不变
- 禁止把原始 JSON 走一遍 `json.loads` -> `json.dumps` 后再提交，因为这会丢失原文格式信息
- 如需校验 JSON 合法性，应对“已完成最小改动后的最终文本”做校验，通过后直接提交该文本本身
- 当无法可靠地同时满足“局部改动”和“格式保持”时，先向用户说明风险，再继续执行

## 输出处理

- 尽量将 `bytedcli devflow` 的原始输出原文展示
- 不要主动对输出做总结、概要、改写、提炼或格式化
- 除非用户明确要求解释结果，否则直接返回命令输出即可
- 如果命令失败，优先保留并展示原始错误信息，再补充最少量的必要说明
