# SCM WebShell 直接操作与生命周期

本 reference 适用于已准备好的 opaque `session_id`, 以及 WebShell state、archive、audit、recovery 和 accountable resolution。候选抽取、`prepare` 和默认 `pwd` probe 见 `scm-webshell-prepare.md`。

## 授权边界

- `prepare` 是唯一 create-or-reuse operation。`execute`、`stream`、`upload` 和 `diff apply` 只接收 `--session-id`, 不会隐式创建或替换 session。
- Minimal WebShell Probe 之外的额外 `execute`、interactive stream、upload、diff apply、delete、recover、`prune-expired` 和 manual resolution 只在用户明确授权的目标与范围内执行。建议、错误 hint、diagnosis recommendation、过期 session 或待处理资源都不构成授权。
- 只执行用户已经要求的诊断。不要因获得 session 而扩大到其他命令、文件、目录、归档、清理或恢复。
- 所有命令使用 `bytedcli --site cn`; 认证由 bytedcli 在操作内部获取和使用。

## 有限命令与 interactive stream

```bash
# 一次有限命令; inline command 和 command file 二选一
bytedcli --site cn --json scm webshell execute --session-id <session_id> --command '<command>'
bytedcli --site cn --json scm webshell execute --session-id <session_id> --command-file ./diagnose.sh

# 直接终端交互; 只用于用户明确授权的 direct CLI 会话
bytedcli --site cn scm webshell stream --session-id <session_id>

# 非 TTY 调用方显式使用 JSONL protocol
bytedcli --site cn scm webshell stream --session-id <session_id> --protocol jsonl
```

`execute` 结果以 `command_completed`、`exit_code`、`timed_out`、`output_truncated`、`archive_truncated` 和 `clean_output` 为准。连接关闭、timeout、truncation 或 protocol error 不能解释为成功。命令完成后, bytedcli process exit code 等于 remote `exit_code`; 这个契约也适用于 `--json`, 此时 JSON envelope 的 `status` 仍为 `success`, 表示编排完成且结构化结果已经成功输出。外层 shell automation 应先读取 JSON payload, 再用 process exit code 判断远端命令是否成功。不要自动重试有可能已经派发的命令。

`stream` 是直接 CLI 操作, 不通过 JSON result、captured execution 或 MCP 启动。它持有 session writer lease; 结束或异常后按 CLI 返回事实处理, 不自行接管 lease。

## Remote Verification Change

```bash
bytedcli --site cn --json scm webshell upload --session-id <session_id> --local ./fix.txt --remote /tmp/fix.txt --backup
bytedcli --site cn --json scm webshell diff apply --session-id <session_id> --diff ./fix.diff --cwd /workspace/example-repo
```

`upload` 接收最大 64 MiB 的本地 regular non-symlink file, 分块传输并校验 SHA-256。`diff apply` 接收相同边界的本地 diff, 先运行 `git apply --check`, 通过后才 apply。两者都必须由用户明确授权目标 session 与远端位置。

Remote Verification Change 是临时验证。把验证结论带回 local repository, 在本地实现最终修复、运行测试并提交。不要推荐 remote commit, 也不要把远端 checkout 当作最终修复来源。

## 只读检查与证据

以下命令可在用户请求的排障范围内读取安全的本地摘要或显式远端状态：

```bash
bytedcli --site cn --json scm webshell session list
bytedcli --site cn --json scm webshell session get --session-id <session_id>
bytedcli --site cn --json scm webshell session status --session-id <session_id>
bytedcli --site cn --json scm webshell attempt list
bytedcli --site cn --json scm webshell attempt get --attempt-id <attempt_id>
bytedcli --site cn --json scm webshell claim list
bytedcli --site cn --json scm webshell claim get --claim-id <claim_id>
bytedcli --site cn --json scm webshell conflict list
bytedcli --site cn --json scm webshell conflict get --conflict-id <conflict_id>
bytedcli --site cn --json scm webshell archive list
bytedcli --site cn --json scm webshell archive get --archive-id <archive_id> --page-size 20
bytedcli --site cn --json scm webshell audit list
bytedcli --site cn --json scm webshell audit get --audit-id <audit_id>
bytedcli --site cn --json scm webshell diagnose
```

List 命令可使用 `--page-size` 和上次结果返回的 opaque `--page-token`。`archive get` 返回单个 archive 的元数据和其中一页 events; 它的 `--page-size`、`--page-token` 及分页元数据都描述 events, 而不是 archives。JSON 输出中的 `current_count` 是当前页实际返回的条数; opaque cursor 分页不提供数字 `page` 或全量 `total`。Archive content 只能通过显式 `archive get` 读取; 普通 session、audit 和 diagnose 输出只含安全摘要。Archive export 是显式本地写入, 目标必须不存在：

```bash
bytedcli --site cn --json scm webshell archive export --archive-id <archive_id> --destination ./webshell-events.jsonl
```

## 显式生命周期操作

以下操作会改变远端或本地 authority, 逐次取得用户明确授权：

```bash
# 单次 no-retry 远端 cancellation
bytedcli --site cn --json scm webshell session delete --session-id <session_id>

# 只恢复满足 CLI eligibility 的 unfinished local work
bytedcli --site cn --json scm webshell session recover --session-id <session_id>
bytedcli --site cn --json scm webshell session recover --all-expired

# 只在本地标记已到期的 ready sessions
bytedcli --site cn --json scm webshell session prune-expired
```

TTL 到期只表示本地 direct-use/reuse window 结束, 不是远端终止证据。只有用户明确要求的新 `prepare` 可以换代; 被 retire 的 session 保留供检查和显式清理, 不再用于 `execute`、`stream`、`upload` 或 `diff apply`。换代结果中的 cleanup hint 不授权自动 delete。

`delete` 结果不确定或失败时保留现状并报告, 不自动重试。`recover` 只处理 CLI 判定合格的 unfinished local operation; 它不创建 generation、不制造远端事实、不清除活动 owner, 也不解决 conflict。

## Accountable manual resolution

Manual resolution 只处理一个明确资源, 需要非敏感、单行的 `--confirmed-by` 和 `--reason`：

```bash
bytedcli --site cn --json scm webshell attempt reconcile --attempt-id <attempt_id> --webshell-record-id <webshell_record_id> --confirmed-by <actor> --reason '<reason>'
bytedcli --site cn --json scm webshell attempt resolve --attempt-id <attempt_id> --confirmed-by <actor> --reason '<reason>'
bytedcli --site cn --json scm webshell session resolve --session-id <session_id> --status destroyed --confirmed-by <actor> --reason '<reason>'
bytedcli --site cn --json scm webshell conflict resolve --resource-id <resource_id> --confirmed-by <actor> --reason '<reason>'
```

只在用户明确要求且提供可问责事实时执行。不要根据推测确认 attempt absent、session destroyed/lost 或 conflict disposition, 不要把 token、credential、URL 或远端输出放进 actor/reason。

## 错误恢复

- Source ambiguity、architecture choice 或 conflicting identity: 展示安全候选并等待用户消歧。
- Pending/uncertain create: 保留 attempt、claim 和 occupancy。可先读 `attempt get` 与 `diagnose`; reconcile/resolve 需要用户授权和独立证据。
- Writer lease 或 unfinished operation: 停止远端操作并读 `diagnose`; 只有用户授权后才运行符合 eligibility 的 `session recover`。
- Lifecycle conflict: 读取单个 conflict/resource; 只有用户授权并提供 accountable evidence 后才 resolve。
- Timeout、connection/protocol failure、truncation、delete uncertainty 或 lease release 未确认: 保留失败事实并停止自动重试。
- 任意 direct operation 返回 `SCM_WEBSHELL_NOT_DISPATCHED`: 报告安全证据并停止。只有准备工作流中经过严格校验的默认 `pwd` 可以使用 `scm-webshell-prepare.md` 的一次 platform retry 例外。

错误中的可复制 hint 是建议, 不自动授权执行。保持 opaque identities 和 state 证据, 让用户决定下一步。
