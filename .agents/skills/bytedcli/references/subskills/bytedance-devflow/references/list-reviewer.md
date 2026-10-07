# DevFlow 查询评审人引用文档

本引用文档用于查询一个 DevFlow 任务的代码评审人列表及各仓库的评审通过状态。这是只读操作。

## 何时使用

当用户明确表达以下意图时使用本引用文档：
- 看一下有哪些评审人、谁在 review、评审名单是什么
- 谁还没通过评审、评审进度怎么样
- 在增删评审人或催审之前，需要先确认当前名单

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
- `repo_name` 与 `branch` 仅在 `task_id` 未提供时用于定位任务；无论用哪种方式定位，接口都返回任务下全部仓库的评审人
- `repo_name` 和 `branch` 在当前仓库内执行时可以由 CLI 自动推断

## 执行原则

- 这是只读操作，不需要向用户确认
- 后端已经完成评审人列表的分组、排序、状态标注和 Markdown 排版，Agent 不得再次处理这些内容
- 默认返回包含 MR 创建者的完整评审人列表，并由后端将对应 MR 的创建者标注为 `MR 创建者`
- 如果任务还没有评审记录，后端会返回 pending 并提示先发起代码评审，此时应原样展示提示
- 如果在完成本 skill 任务过程中需要使用其他 skill，必须使用名称带有 `bytedance-devflow-` 前缀的 skill

## 调用方式

```bash
bytedcli devflow reviewer list --task_id="<task_id>" --bytedcli-skill-dir="<skill所在目录>"
```

通过仓库和分支定位任务（返回结果仍包含任务下全部仓库）：

```bash
bytedcli devflow reviewer list --repo_name="<repo_name>" --branch="<branch>" --bytedcli-skill-dir="<skill所在目录>"
```

在目标仓库目录内执行时，可以省略全部参数：

```bash
bytedcli devflow reviewer list --bytedcli-skill-dir="<skill所在目录>"
```

## 输出处理

- 命令成功后，将后端返回的业务正文原样作为最终回答
- 严格保留原始 Markdown 的标题、换行、空行、缩进、列表符号、分组顺序和全部文案
- 不解析或重建 PSM、仓库、reviewer 及评审状态；包括 `### 未关联 PSM` 在内的内容均以后端原文为准
- 不重新排版，不包裹代码块，不添加引言、总结、解释、操作建议或其他前后缀
- 不因某个仓库没有 reviewer 而合并、删除或改写对应分组
- 如果命令返回 pending，直接原样返回 pending 文案
- 如果命令失败，直接返回原始错误信息；只有用户明确要求解释时，才另行补充说明

## 备注

- 本能力对应接口：`GET /openapi/mcp/reviewer/list`
- 对应底层 CLI action：`reviewer list`
- 增删评审人参见 `add-reviewer.md` 与 `delete-reviewer.md`；催审参见 `notify-reviewer.md`
- 如果在完成本 skill 任务过程中需要使用其他 skill，必须使用名称带有 `bytedance-devflow-` 前缀的 skill
