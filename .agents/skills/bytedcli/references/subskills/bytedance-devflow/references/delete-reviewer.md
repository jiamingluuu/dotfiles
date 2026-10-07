# DevFlow 删除评审人引用文档

本引用文档用于从一个 DevFlow 任务中删除代码评审人。

## 何时使用

当用户明确表达以下意图时使用本引用文档：
- 删评审人、移除 reviewer、把某人从评审名单里去掉

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
- `psm`
- `reviewers`

其中：
- `task_id` / `repo_name` / `branch` 用于定位任务，必须满足「提供 `task_id`」或「同时提供 `repo_name` 和 `branch`」之一
- `repo_name` 与 `psm` 二选一确定作用范围：
  - 传 `repo_name`：只修改该仓库（可由当前仓库自动推断），本方式不支持一次修改任务下全部仓库
  - 传 `psm`：作用于该 `psm` 关联的全部仓库；若该 `psm` 同时有 IDL（API 设计）仓库和开发调试仓库，则两个仓库都会被删除，后端返回时会分别列出各仓库结果。此时无需再传 `repo_name`
- `reviewers` 必填，多个按 `<reviewer1>,<reviewer2>` 用逗号分隔，单个评审人只传 `<reviewer1>`；**支持用户名或完整邮箱**：只传用户名（如 `zhangsan`）时后端会自动补齐 `@bytedance.com` 后再校验

## 执行原则

- `reviewers` 支持用户名或完整邮箱：优先使用用户明确给出的形式，只给用户名时可直接透传，由后端补齐后缀并校验；无需自己拼接完整邮箱
- 需要一次作用于某个 `psm` 的 API 设计仓库和开发调试仓库时，传 `psm` 而不是 `repo_name`；后端会分别返回每个仓库（含阶段/PSM 标题）的删除结果
- 后端会按每个相关 MR 校验待删除人员，并保证删除后仍至少保留 1 名审批人
- MR 创建者、默认评审人和已通过审批的评审人不可删除；这些失败项不会阻止其他符合条件的评审人继续删除
- 删除只需解析 ReviewerId，不要求被删除用户当前仍有仓库写权限，避免权限变化或离职状态阻塞名单清理
- 如果某人已不在部分 MR 的评审名单中，后端会按幂等 no-op 处理，继续删除其他 MR
- 一次删多个评审人时用逗号一次性传入；后端会尽力完成所有合法删除，并分别返回 `删除成功`、`删除失败` 和幂等跳过明细
- 任一评审人或 MR 删除失败时接口整体返回 error，但已成功的删除不会回滚；只根据 `删除失败` 列表重试
- 未传 `psm` 时每次调用只处理一个 `repo_name`；需要修改多个仓库时传 `psm` 或分别调用
- 如果既没传 `repo_name` 也没传 `psm`，后端会返回包含 API 设计、开发调试和依赖仓库类型以及当前全量 reviewer 的候选列表，并将不可删除的 MR 创建者明确标注出来
- 如果在完成本 skill 任务过程中需要使用其他 skill，必须使用名称带有 `bytedance-devflow-` 前缀的 skill

## 调用方式

删除单个评审人：

```bash
bytedcli devflow reviewer delete --task_id="<task_id>" --repo_name="<repo_name>" --reviewers="<reviewer1>" --bytedcli-skill-dir="<skill所在目录>"
```

一次删除多个评审人（用户名与邮箱可混用）：

```bash
bytedcli devflow reviewer delete --task_id="<task_id>" --repo_name="<repo_name>" --reviewers="<reviewer1>,<reviewer2>" --bytedcli-skill-dir="<skill所在目录>"
```

按 `psm` 删除（同时作用于该 psm 的 IDL 仓库和开发调试仓库）：

```bash
bytedcli devflow reviewer delete --task_id="<task_id>" --psm="<psm>" --reviewers="<reviewer1>,<reviewer2>" --bytedcli-skill-dir="<skill所在目录>"
```

## 输出处理

- 直接返回原始输出
- 不主动改写、总结或格式化后端返回
- 只有用户明确要求解释时，再补充说明
- 如果命令返回 pending，必须优先原样展示 pending 文案
- 如果命令失败，优先保留并展示原始错误信息，再补充最少量的必要说明

## 备注

- 本能力对应接口：`POST /openapi/mcp/reviewer/delete`
- 对应底层 CLI action：`reviewer delete`
- 查询现有评审人参见 `list-reviewer.md`
- 如果在完成本 skill 任务过程中需要使用其他 skill，必须使用名称带有 `bytedance-devflow-` 前缀的 skill
