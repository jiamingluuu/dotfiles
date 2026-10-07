# DevFlow 任务提测

## 适用场景

当用户明确要求对一个已有 DevFlow 任务执行以下操作时，使用本能力：

- 帮我提测
- 提交测试
- 发起 RD 提测

对应命令：

```bash
bytedcli devflow quality submit --task_id="<task_id>" --bytedcli-skill-dir="<skill所在目录>"
```

对应接口：

```text
POST /openapi/mcp/task/quality/submit
```

## 参数

- `task_id`：必填，必须是明确且唯一的 DevFlow 任务 ID。

用户未提供 `task_id` 时，先使用 `task info` 根据当前仓库和分支查询任务。只有得到唯一任务后才能提测；匹配到多个任务时，向用户展示候选并要求明确选择。

## 执行规则

1. 本命令是写操作。只有用户明确要求执行提测时才能调用。
2. 用户询问“能否提测”“提测条件是什么”或“当前质量状态”时，不得直接调用本命令。
3. 不得绕过接口返回的权限、任务状态或质量状态限制。
4. 接口返回 `pending` 时，原样展示 `status_msg`，不得自动重试。
5. 请求超时时，提测结果属于未知状态。先向用户展示 CLI 的“提测结果待确认”提示，不得自动重试写操作。
6. 提测成功后必须展示返回的任务链接；存在提测审批链接时一并展示。
7. “提测成功”仅表示 RD 提测动作已经完成，不代表 QA 审批通过，也不代表任务可以合码上线。

## 返回说明

接口返回统一 MCP 响应。向用户回复时，以 `status_msg` 为准，不省略其中的 HTTPS 链接。

`data` 中可能包含以下字段：

- `task_id`：任务 ID。
- `quality_status`：提测后的质量状态枚举。
- `quality_status_text`：提测后的质量状态文案。
- `need_qa_approval`：是否需要 QA 审批。
- `task_url`：任务链接。
- `approval_url`：提测审批链接。
