# AgentGate 策略逃逸安全提交

使用仓库内置 `scripts/submit-agentgate-approval.mjs` 自动提交 AgentGate 逃逸工单。不要直接构造 HTTP 请求，也不要用 `curl` 替代 helper。

## RecoveryURL 校验

必须用标准 URL 解析器读取服务端返回的原始 `RecoveryURL`，并逐项验证：

- `protocol === "https:"`
- `hostname === "cloud.bytedance.net"`
- `pathname === "/open/explorer/ai-policy/apply"`
- `strategy_id` 匹配正整数字符串，转为整数后仍大于 0
- `account_id` 和 `api_id` 均为非空字符串

不要接受子域名、用户名密码段、非默认端口、相似域名、重定向 URL 或其它 path。不要用字符串前缀判断代替 URL 解析。

校验失败时不得打开、请求或回显完整 URL。只报告错误码、错误类型和脱敏后的策略名称，并建议联系策略管理员。

## 私有输入文件

使用 Agent 的结构化文件写入能力创建权限为 `0600` 的临时 JSON 文件。禁止通过 shell heredoc、`echo`、字符串模板或命令替换写入用户值。

时长逃逸：

```json
{
  "RecoveryURL": "<validated-original-recovery-url>",
  "Username": "<current-username>",
  "EscapeType": "escape_duration",
  "EscapeTime": 60,
  "Reason": "<confirmed-reason>"
}
```

次数逃逸：

```json
{
  "RecoveryURL": "<validated-original-recovery-url>",
  "Username": "<current-username>",
  "EscapeType": "escape_count",
  "EscapeCount": 2,
  "Reason": "<confirmed-reason>"
}
```

- `RecoveryURL` 必须使用错误响应原值；helper 从中提取 `StrategyID`、`AccountID` 和 `APIID`，输入文件不得重复提供这些字段。
- `Username` 从当前 CLI 的认证状态取得，只接受用户名字符。
- `EscapeTime` 使用分钟，允许 `-1`（永久）或 `1..525600`。
- `EscapeCount` 只接受 `1..1000000`。
- `Reason` 必须非空且不超过 2000 字符。
- 时长和次数字段互斥。

## 执行

将当前 `ai-approval-ai-auth` Skill 目录解析为绝对路径，先执行只校验、不联网的预检：

```bash
node "<ai-auth-skill-dir>/scripts/submit-agentgate-approval.mjs" \
  --input "<private-input-json>" \
  --validate-only
```

确认预检输出的 `status` 为 `validated`，再执行真实提交：

```bash
set -o pipefail
bytedcli --site cn auth get-bytecloud-jwt-token |
  node "<ai-auth-skill-dir>/scripts/submit-agentgate-approval.mjs" \
    --input "<private-input-json>"
```

helper 只从 stdin 读取 JWT。它固定请求到 AgentGate submit 端点，设置 20 秒总时限、socket 空闲超时和 1 MiB 响应上限，不跟随重定向，并严格检查 `Code === 0`、Result 对象和有界字符串 TicketID。`--validate-only` 保留输入文件；真实提交在联网前安全消费并删除输入文件，后续成功或失败都不会遗留该文件。

成功输出：

```json
{
  "status": "ok",
  "ticket_id": "<ticket-id>",
  "ticket_url": "https://cloud.bytedance.net/open/explorer/ai-policy/ticket/<ticket-id>",
  "escape_type": "escape_duration",
  "escape_time": 60
}
```

非零退出表示输入、认证、网络或上游业务失败。网络结果不明确时不要自动重放；先通过可信平台入口回查。

## 禁止事项

- 不运行或生成 `curl`、`fetch`、`httpie` 等直连写请求。
- 不把 JWT 放入 argv、环境变量、临时 JSON、日志或输出。
- 不把错误响应或用户输入插值进 shell 命令、HTTP header、URL 或 JSON。
- 不绕过 helper 的 URL、字段、权限、超时、响应大小和错误脱敏校验。
