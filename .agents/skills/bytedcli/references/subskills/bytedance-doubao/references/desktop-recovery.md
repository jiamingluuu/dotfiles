# 豆包桌面端错误恢复

这里只处理本机豆包及其当前 Profile。不要使用 `bytedcli auth login`、站点切换或 HTTP 代理修复豆包用户登录。

| 错误码 | 处理 |
| --- | --- |
| `DOUBAO_CDP_UNAVAILABLE` | 豆包可能未启动、未开启 CDP，或端口填写错误。先查看豆包窗口和启动参数，再运行 `bytedcli doubao status --cdp-port <port>`。只凭连接失败不能断言是哪一种情况。 |
| `DOUBAO_CDP_TIMEOUT` | 调试端点没有按时回复。检查应用是否无响应；只有只读检查可重试。发送已开始时先对账。 |
| `DOUBAO_CDP_UNSUPPORTED` | 当前调试端不支持所需方法。使用已验证兼容的豆包桌面版本及 bytedcli，不能通过匿名模式或私有发送 API 绕过。 |
| `DOUBAO_CDP_PROTOCOL_ERROR` / `DOUBAO_CDP_SCHEMA_ERROR` | 可能连到其他本地服务，或协议响应已变化。核对端口；保留不含凭据的错误码，更新适配器。 |
| `DOUBAO_CHAT_NOT_FOUND` | 当前只有启动页、登录页或其他浏览器页面。打开真正的聊天窗口，不能把任意页面当成豆包聊天页。 |
| `DOUBAO_TARGET_AMBIGUOUS` / `DOUBAO_TARGET_NOT_FOUND` | 从提示中的候选选择 `--target-id`；更多候选用 `--json` 查看。重启后旧 ID 可能失效。 |
| `DOUBAO_LOGIN_REQUIRED` | 在当前豆包 Profile 手动登录；匿名页面能发送不代表具备用户身份。若更换 `--user-data-dir` 后未登录，新目录是另一个桌面 Profile，不会继承原登录态；已有独立 Profile 可继续使用原路径，不自动迁移或复制凭据。 |
| `DOUBAO_ACCOUNT_UNVERIFIED` | 登录探活缺失、失败或与当前 Profile 不一致。完成登录/账号切换后再检查，不把它简单认定为已退出登录。 |
| `DOUBAO_PAGE_SCHEMA_ERROR` / `DOUBAO_PAGE_UNSUPPORTED` | 页面字段或输入组件不符合合同。等待页面加载完成；仍失败时停止操作并更新适配器。 |
| `DOUBAO_DRAFT_EXISTS` / `DOUBAO_NOT_READY` | 保留原草稿/附件，或等待生成结束；权限和登录弹窗由用户处理。用户明确选择发送保留草稿时，先对账，再按 skill 的 `--resume-draft` 路径重新预览和确认；不能用它绕过未完成回复或附件。 |
| `DOUBAO_DRAFT_MISMATCH` | `--resume-draft` 的文本与当前非空草稿不完全一致，包括空白差异。保留草稿，核对 `--text-file` 原文，不自动改写草稿或改用普通发送。 |
| `DOUBAO_DRAFT_RESUME_UNSAFE` | 最近用户消息不可读、历史角色不明，或最近用户消息与草稿疑似重复。保持停止，人工对账；不换令牌绕过。用于拒绝疑似重复的比较会忽略排版空白，不代表发送时会更改原文。 |
| `DOUBAO_PERMISSION_MODE_UNSUPPORTED` | 保留或手动选择“始终询问”/“按需确认”；不使用“全部允许”，不引导降低已有保护。 |
| `DOUBAO_STATE_CHANGED` | 页面、账号、会话、可见选项或历史发生变化。准备完成后仅容忍最旧历史移出页面且保留最新消息；恢复草稿时还必须保留最近用户消息及最新回复的校验证据，角色、最近用户正文或回复完成状态变化均停止发送。新消息、重排、末尾/中间丢失或全部历史消失仍拒绝。错误可能发生在文本已插入之后；提交阶段会包装为 `DOUBAO_SEND_UNCERTAIN`，令牌仍被消耗。检查草稿，不自动清空或重发。 |
| `DOUBAO_SEND_UNCERTAIN` | 根据 `details.conversationId`、`userMessageId` 和 `targetId` 查看页面及 `message list`；`state` 与兼容别名 `observedState` 一致，缺失标识或原因使用 `null`。`unknown` 表示提交未确认，`submitted` 表示已观察到用户消息但最终回复未确认。状态不明不是发送失败，不自动重试。 |
| `DOUBAO_PREVIEW_UNAVAILABLE` | 本地预览签发记录无法保存，未发送消息。检查 bytedcli 数据目录的权限后重新预览，不手工创建记录。 |
| `DOUBAO_CONFIRMATION_MISMATCH` | 目标、账号、选项或用于恢复草稿的历史证据已变，或令牌不是当前本地 bytedcli 数据目录签发的完整令牌。`--profile` 不隔离豆包确认记录。不要修改令牌；先确认没有未对账的发送，再重新人工预览。 |
| `DOUBAO_SEND_LOCKED` | 另一进程正在发送，或前次崩溃留下锁。先确认没有活动发送并人工对账，再处理明确属于该次操作的残留锁。 |
| `DOUBAO_SEND_ALREADY_ATTEMPTED` | 这个令牌已使用。成功操作后的独立新任务重新人工预览；结果不明时禁止自动换令牌绕过。 |

## 排查命令

```bash
bytedcli --json doubao status --cdp-port 19222
bytedcli --json doubao message list --cdp-port 19222 --page 1 --page-size 20
bytedcli doubao message send --help
```

CLI 不会自动退出/重启应用、切换账号、开启 CDP 或改变系统权限。桌面 Profile 和 bytedcli 企业身份、`--profile`、`--as`、`--site` 是不同的配置来源。

本地预览签发和尝试记录目前没有自动过期/清理策略。不要只删除尝试记录或手工构造预览记录来绕过单次使用保护；状态变化或断线后的令牌仍不可重用。锁文件的关闭/删除会分别尽力执行，清理失败不覆盖原发送结果；后续遇到残留锁时按 `DOUBAO_SEND_LOCKED` 处理。
