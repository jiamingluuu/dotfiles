# 查询 DevFlow 任务仓库评论

当用户需要查看、确认、整理某个 DevFlow task 下指定仓库的 code review 评论、未解决评论、MR 评论组时，使用本能力。

## 何时调用

- 用户明确说要查看某个 DevFlow task 下某个仓库的评论
- 用户要看未解决评论、review comment、MR 评论组
- 用户提供了 `task_id`，希望确认某个仓库当前还有哪些 review 评论未处理

## 参数获取优先级

按下面顺序收集参数，后者只用于补全缺失值，不能覆盖前者：

1. 用户当前对话中明确提供的信息
2. 当前工作目录和本地仓库上下文

## 目标参数

- `task_id`：可选；若未提供，则使用 `repo_name + branch` 推断任务
- `repo_name`：可选；若未提供，优先让底层 CLI 从当前仓库目录自动推断
- `branch`：可选；若未提供，优先让底层 CLI 从当前仓库目录自动推断
- `psm`：可选；当已提供 `task_id` 但未提供 `repo_name` 时，可通过 `task_id + psm` 推断任务内对应仓库
- `service_name`：可选；当已提供 `task_id` 但未提供 `repo_name` 时，可通过 `task_id + service_name` 推断任务内对应仓库，适合前端/Goofy 场景
- `status`：可选，支持 `unresolved` 或 `all`；默认 `unresolved`
- `limit`：可选；未提供时不截断评论组数量

## 执行原则

- 不要把评论内容改写成摘要后再返回；优先原样返回 CLI 输出
- CLI 返回 `pending` 时，优先把返回文案原样展示给用户
- 用户未明确给出 `repo_name` 或 `branch` 时，不要先追问，优先省略让 CLI 自动推断
- 当用户已提供 `task_id` 且表达的是某个服务 / 前端项目，而不是仓库时，优先使用 `psm` 或 `service_name`，不要强行追问 `repo_name`
- 本能力首期不支持按文件路径过滤评论

## 调用命令

```bash
bytedcli devflow develop-comments query --task_id="<task_id>" --repo_name="<repo_name>" --bytedcli-skill-dir="<skill所在目录>"
```

按需补充可选参数：

```bash
bytedcli devflow develop-comments query --task_id="<task_id>" --repo_name="<repo_name>" --status="all" --limit="20" --bytedcli-skill-dir="<skill所在目录>"
```

如果用户没有提供 `task_id`，可以改用 `repo_name + branch`：

```bash
bytedcli devflow develop-comments query --repo_name="<repo_name>" --branch="<branch>" --bytedcli-skill-dir="<skill所在目录>"
```

如果用户已经提供 `task_id`，但手里只有服务标识，可以直接传 `psm` 或 `service_name`：

```bash
bytedcli devflow develop-comments query --task_id="<task_id>" --psm="<psm>" --bytedcli-skill-dir="<skill所在目录>"
```

```bash
bytedcli devflow develop-comments query --task_id="<task_id>" --service_name="<service_name>" --bytedcli-skill-dir="<skill所在目录>"
```

如果用户没有提供 `repo_name` 或 `branch`，可以一起省略，让 CLI 从当前仓库目录自动推断：

```bash
bytedcli devflow develop-comments query --bytedcli-skill-dir="<skill所在目录>"
```

## 输出处理

- 直接返回 `bytedcli devflow` 的原始输出
- 不主动改写、总结或重新排版后端返回的 Markdown 评论明细
- 只有用户明确要求解释时，再补充说明

## 备注

- 本能力对应接口：`GET /openapi/mcp/task/develop/review/repo_comments/get`
- 如果在完成本 skill 任务过程中需要使用其他 skill，必须使用名称带有 `bytedance-devflow-` 前缀的 skill
