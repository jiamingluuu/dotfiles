# 生成与对话

生成、BITS 回传、模板对话使用独立后端，不会携带 UI OpenAPI 的 `TestIDE-Token`、`Platform` 或 Web BFF session，也不会继承全局自定义 HTTP headers。生成接口文档注明暂时无需鉴权；对话示例没有提供 UI token。当前用户应显式提供请求中的创建人或用户字段。

所有写命令默认校验并预览请求，`--yes` 才提交；`--dry-run` 与 `--yes` 互斥。请求只提交一次，网络异常后应先检查平台状态。

## 生成用例

```bash
bytedcli smartq generation create --username demo-user --user-email demo-user@example.com --space-id 1000 --prd-url https://docs.example.com/demo-prd --intent-content '生成回归用例'

# 完整字段也可由 JSON 文件提供；显式 option 覆盖同名字段
bytedcli smartq generation create --body-file ./demo-generation.json --env cn --yes

# 保存创建结果中的 taskId 和 caseSetId
bytedcli --json smartq generation get --id 2000 --env cn
bytedcli --json smartq generation wait --id 2000 --env cn --timeout-ms 1800000 --poll-interval-ms 5000

# 生成成功后，使用 UI OpenAPI 认证读取用例内容
bytedcli --json smartq case-set get --space-id 1000 --case-set-id 3000
```

`--env` 支持 `cn`、`boe`，默认 `cn`。创建请求的 `user_intent` 固定为 `prd2case_v3`；调用方说明放在 `intent_content`。

除常用 option 外，`--body-json` 或 `--body-file` 可提供 `dir_id`、`aid`、`additional_doc_urls`、`os_type`、`app_name`、`caseset_name`、`callback_url`、`callback_ext`、`meego_ids`、`meego_project_name`。`os_type` 为 `android`、`ios` 或 `web`；不指定用例集名称时由后端使用需求标题。两种 body 输入互斥。

生成状态包括 `running`、`succeeded`、`failed`、`paused`、`cancelled`、`unknown`。`wait` 默认最多等待 30 分钟，每 5 秒查询一次；成功、失败、取消时结束，暂停时返回 `terminal:false`，未知状态继续等待。超时错误保留最后状态和恢复命令，重复执行同一 ID 的 `wait` 不会创建新任务。

## BITS 回传

上游文档将以下两个接口标为“不维护”。调用前应确认业务仍使用这条转换链路。它们与 `smartq case-set import` 的 BITS → SmartQ 导入方向相反。

```bash
# 从 TestIDE 用例集创建 BITS 用例集
bytedcli smartq generation bits create --space-id 1000 --case-set-id 3000 --bits-project-id 4000 --bits-dir-id 5000 --operator demo-user

# 将 TestIDE 脑图作为一级节点追加到 BITS 用例集
bytedcli smartq generation bits update --space-id 1000 --case-set-id 3000 --bits-project-id 4000 --bits-dir-id 5000 --bits-case-set-id 6000 --name demo-case-set --operator demo-user
```

创建时 `--name` 可选，默认使用 TestIDE 名称；追加时需要 `--name`，目标 `--bits-case-set-id` 可选。请求也可通过互斥的 `--body-json`、`--body-file` 提供，支持 `--env cn|boe`。

## 模板对话

```bash
bytedcli smartq conversation execute --template-id demo-template --user-id demo-user --user-email demo-user@example.com --end-type web --context-json '{"requirement":"demo"}'
bytedcli --json smartq conversation execute --body-file ./demo-conversation.json --timeout-ms 1800000 --yes
```

`--context-json`、`--context-file` 接收 JSON 对象，提交时序列化为接口要求的字符串；二者互斥。在 body 文件中，`context` 可以是对象、序列化后的对象字符串，或文档示例中的空字符串。body 的 JSON 与文件输入同样互斥。

文档定义 SSE 响应但没有事件 schema。结果保留事件的 `event`、`data`、`id` 等字段，也兼容 JSON 响应。客户端最多收集 8 MiB，并受 `--timeout-ms` 限制。`receipt: response_received` 只表示收到了响应，不能据此判定模板触发的业务任务已经完成。超时或读流失败可能发生在提交之后，先到平台核对，再决定是否重试。
