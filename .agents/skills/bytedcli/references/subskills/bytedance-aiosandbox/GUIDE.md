---
name: bytedance-aiosandbox
description: "Manage AIO Sandbox environments via bytedcli: manage Sandbox Templates, inspect deployed Sandbox instances, manage sessions, execute shell commands, manage files, automate browsers, run code with Jupyter/Node.js, record screens, manage skills and hooks, and discover or call sandbox MCP tools."
---

# AIO Sandbox

AIO Sandbox is an All-in-One Agent Sandbox Environment providing containerized Browser, Shell, File System, Code Execution, Jupyter, Node.js, and more.

## How to invoke bytedcli

```bash
npx @bytedance-dev/bytedcli aiosandbox <subcommand> [options]
```

## Access Modes

| Mode             | When to Use                        | Options                           | Auth                |
| ---------------- | ---------------------------------- | --------------------------------- | ------------------- |
| AIPAAS (managed) | Standard workflow                  | `--session-id <id> --site <site>` | SSO JWT (automatic) |
| Direct           | Dev/debug, pre-existing containers | `--url <url> --api-key <key>`     | API Key             |

## Quick Start

### 1. Create a session (AIPAAS)

```bash
bytedcli aiosandbox session create --psm example.sandbox.psm --ttl 3600
```

### 2. Execute shell commands

```bash
bytedcli aiosandbox shell exec --command "echo hello" --session-id <id>
```

### 3. File operations

```bash
bytedcli aiosandbox file read --path /workspace/main.py --session-id <id>
bytedcli aiosandbox file write --path /workspace/main.py --content "print('hello')" --session-id <id>
bytedcli aiosandbox file upload --local-path ./data.csv --remote-path /workspace/data.csv --session-id <id>
bytedcli aiosandbox file download --remote-path /workspace/output.csv --local-path ./output.csv --session-id <id>
```

### 4. Execute code

```bash
bytedcli aiosandbox code exec --language python --code "print('hello')" --session-id <id>
bytedcli aiosandbox nodejs exec --code "console.log('hello')" --session-id <id>
```

### 5. Browser automation

```bash
bytedcli aiosandbox browser page navigate --page-url "https://example.com" --session-id <id>
bytedcli aiosandbox browser page screenshot --output ./screenshot.png --session-id <id>
bytedcli aiosandbox browser page click --selector "#submit" --session-id <id>
```

### 6. Manage Sandbox Templates

```bash
bytedcli --site i18n-tt --vregion Singapore-Central aiosandbox template list --scope mine
bytedcli --site i18n-tt --vregion Singapore-Central aiosandbox template get --template-id demo-template-id

# Writes are dry-run by default. Review the payload, then add --yes.
bytedcli --site i18n-tt --vregion Singapore-Central aiosandbox template create \
  --name demo_template \
  --description "Demo template" \
  --admins '["demo.user"]' \
  --tags '["demo"]' \
  --config '{"base_template":"demo-base","envs":{"MODE":"demo"}}'
```

### 7. Inspect Sandbox instances

```bash
bytedcli aiosandbox instance list --scope all --search example.sandbox.demo
bytedcli aiosandbox instance get --sandbox-id demo-sandbox-id
bytedcli aiosandbox instance ticket list --sandbox-id demo-sandbox-id
bytedcli aiosandbox instance runtime-session list --sandbox-id demo-sandbox-id
bytedcli aiosandbox instance quota --sandbox-id demo-sandbox-id

# 升级 sandbox 使用的 template 版本；默认 dry-run，确认 payload 后再加 --yes
bytedcli aiosandbox instance update-template \
  --sandbox-id demo-sandbox-id \
  --template-version 1.0.0.3
```

### 8. Direct mode

```bash
bytedcli aiosandbox shell exec --command "whoami" --url http://localhost:8080 --api-key demo-key
```

### 9. Discover and call MCP tools

```bash
bytedcli aiosandbox mcp server list --session-id <id>
bytedcli aiosandbox mcp tool list --server-name demo-server --session-id <id>

# Calls are dry-run by default. Review the encoded endpoint and payload first.
bytedcli aiosandbox mcp tool call \
  --server-name demo-server \
  --tool-name demo-tool \
  --arguments '{"query":"demo"}' \
  --session-id <id>

# Add --yes only after reviewing the preview.
bytedcli aiosandbox mcp tool call \
  --server-name demo-server \
  --tool-name demo-tool \
  --arguments '{"query":"demo"}' \
  --url http://localhost:8080 \
  --api-key demo-key \
  --yes
```

## Command Reference

### Session Management (AIPAAS)

- `session create --psm <psm> [--ttl <s>] [--site <site>]`
- `session list [--psm <psm>] [--site <site>]`
- `session get --session-id <id> [--site <site>]`
- `session update --session-id <id> [--ttl <s>] [--site <site>]`
- `session delete --session-id <id> [--site <site>]`

### Sandbox Template

- `template list [--scope mine|subscribed|all] [--name <name>] [--search <keyword>] [--tags <json>] [--include-disabled] [--page <n>] [--page-size <n>]`
- `template get --template-id <id> [--version <version>]`
- `template create --name <name> --description <text> --admins <json> --tags <json> --config <json> [--yes] [--wait] [--timeout-ms <ms>]`
- `template update --template-id <id> [--description <text>] [--admins <json>] [--tags <json>] [--config <json> --changelog <text>] [--force-rebuild] [--yes] [--wait] [--timeout-ms <ms>]`
- `template enable|disable|delete --template-id <id> [--yes]`
- `template version list --template-id <id> [--status <status>] [--version-prefix <prefix>] [--page <n>] [--page-size <n>]`
- `template version diff --template-id <id> --version <version>` — compares the selected version with its predecessor
- `template version rebuild --template-id <id> --version-id <id> [--yes] [--wait] [--timeout-ms <ms>]`
- `template usage list --template-id <id> [--name <prefix>] [--sort-desc] [--page <n>] [--page-size <n>]`

模板名称只允许字母、数字和下划线，例如 `demo_template_01`。

`template list` 的 JSON 输出仅包含模板与版本摘要，不返回 `envs` 等完整配置；需要查看完整配置时显式使用 `template get --template-id <id>`，并注意其输出可能包含敏感环境变量。

`template version rebuild` 对应后端 retry，只能用于 `failed`、`error`、`cancelled` 或 `canceled` 状态的版本；成功或仍在构建的版本不能重试。

Template commands use the global `--site` and `--vregion` options. The `--config` value is strict JSON and must contain `base_template`. On update, `--config` replaces the complete config; omitted top-level fields are preserved. Create, update, enable, disable, delete, and rebuild are dry-run by default and only submit with `--yes`.

`--wait` 默认最多等待 20 分钟；平台镜像构建常超过 10 分钟，可按实际需要用 `--timeout-ms` 覆盖。

### Sandbox Instance

`instance` 命令查询 AI PaaS 控制面上已部署的 Sandbox 实例本身（`session` 管理的是运行期会话，`template` 管理的是镜像模板）。除 `update-template` 与 `ticket confirm` 两个写命令外，其余均为只读命令。

- `instance list [--scope mine|subscribed|all] [--search <keyword>] [--search-fields psm|name|sandbox_id] [--env-type <env>] [--sort-by <field>] [--page <n>] [--page-size <n>]`
- `instance get --sandbox-id <id>`
- `instance ticket list --sandbox-id <id> [--page <n>] [--page-size <n>]` — 发布/运维工单记录，含 `ticket_type`、`status` 与 revision
- `instance runtime-session list --sandbox-id <id> [--query-usage] [--history] [--page <n>] [--page-size <n>]` — 当前运行中的 runtime session，`--query-usage` 附带 CPU/内存用量
- `instance quota --sandbox-id <id>` — 按 IDC 拆分的配额与可创建会话数
- `instance acl --sandbox-id <id>` — 管理员、授权人与 allowed PSM
- `instance policy list --sandbox-id <id> [--policy-type <type>]` — 网络策略组
- `instance kata-state --sandbox-id <id>` — Kata 运行时就绪条件；`missing_conditions` 指出阻塞项
- `instance env list --psm <psm>` — 按 PSM 查询 Sandbox 环境
- `instance update-template --sandbox-id <id> --template-version <version> [--template-id <id>] [--runtime-arch <arch>] [--run-cmd <cmd>] [--gray --traffic <1-100>] [--description <text>] [--yes]`
- `instance ticket get --sandbox-id <id> [--region <region>] [--cluster <cluster>]` — 查看进行中的发布工单及其 pipeline step ID
- `instance ticket confirm --sandbox-id <id> --ticket-id <id> --step-ids <id>[,<id>] [--yes]`
- `instance abort --sandbox-id <id> [--ticket-id <id>] [--region <region>] [--cluster <cluster>] [--yes]`

Instance 命令同样使用全局 `--site` 与 `--vregion`，与 Sandbox Template 共用同一套 AI PaaS 网关与鉴权。

`instance update-template` 用于把某个 Sandbox 切到该 template 的另一个版本。`--template-id` 与 `--runtime-arch` 省略时自动沿用该 Sandbox 当前值；默认整量发布（`traffic_value=100`），加 `--gray --traffic 10` 表示 10% 灰度。该命令默认 dry-run，只打印将要提交的 payload，必须显式 `--yes` 才真正提交。

后端 PATCH 是**整体替换**语义，因此该命令实现为 read-modify-write：先读取 Sandbox，继承 `run_cmd` / `source` / `source_type` 等未显式覆盖的字段。dry-run payload 里的 `source` 是**当前已部署版本**的镜像 digest，切到别的版本时会和 `template_version` 对不上；后端以 `template_version` 为准并在落库时重算 digest，属于预期现象（dry-run 输出的 `notes` 里也会提示）。

### 发布流程与卡住时的退出方式

升级是**异步**的：`--yes` 提交后后端会开一张发布工单。

```bash
# 1. 查看工单整体状态
bytedcli aiosandbox instance ticket list --sandbox-id demo-sandbox-id

# 2. 灰度会停在人工闸门；ticket get 才能拿到 step ID 与 allowed_actions
bytedcli aiosandbox instance ticket get --sandbox-id demo-sandbox-id

# 3. 用上一步的 step ID 放行，推进到 100%
bytedcli aiosandbox instance ticket confirm \
  --sandbox-id demo-sandbox-id --ticket-id demo-ticket-id --step-ids demo-step-id --yes
```

`ticket list` 只返回 ticket ID，**不返回 step ID**；`--step-ids` 必须从 `instance ticket get` 的 Pipeline Steps 表里取。

`ticket confirm` 只支持 `confirm`：实测该 step 的 `allowed_actions` 只有 `update` 和 `confirm`，后端对 `reject` 返回 HTTP 500 `not supported step action`，因此 `--action` 只接受 `confirm`。

**灰度未终结前无法再次升级**：该 Sandbox 上任何 `update-template` 都会返回 HTTP 409 `has ongoing ticket`，想回滚也回滚不了。而 `confirm` 是往前推到 100%，不是取消。此时用 `instance abort` 中止流水线：

```bash
bytedcli aiosandbox instance abort --sandbox-id demo-sandbox-id --yes
```

注意 `abort` 只停流水线、**不回退 spec**：abort 完 `template_version` 仍停在灰度那个版本，需要再跑一次 `update-template` 切回原版本。

同一批工单也可以用 `bytedcli faas release status --service-id <sandbox-id>` 查看（Sandbox 的发布工单就是 FaaS 发布工单，`sandbox_id` 即 FaaS `service_id`）。

可用的目标版本用 `template version list --template-id <id> --status success` 查询。

`instance list` 的 `--search` 默认按 `psm` 匹配；要按名称或 ID 检索时显式加 `--search-fields name` 或 `--search-fields sandbox_id`。

`instance kata-state` 的 `conditions.*.ready` 为 `false` 时，`reason_code` 与 `message` 说明具体原因，可据此判断实例为何未切换到目标运行时。

### Shell (Bash Pipe)

- `shell exec --command <cmd> [--shell-session-id <id>] [--async] [--timeout <s>]`
- `shell output --shell-session-id <id> [--offset <n>] [--wait]`
- `shell write --shell-session-id <id> --input <text>`
- `shell kill --shell-session-id <id> [--signal <sig>]`
- `shell session list | create | close`

### PTY (tmux)

- `pty exec --command <cmd> [--pty-session-id <id>] [--timeout <s>]`
- `pty show --pty-session-id <id>`
- `pty wait --pty-session-id <id> [--timeout <s>]`
- `pty write --pty-session-id <id> --input <text> [--press-enter]`
- `pty kill --pty-session-id <id>`
- `pty session list | create | delete | clear`

### File Operations

- `file read --path <path> [--start-line <n>] [--end-line <n>]`
- `file write --path <path> --content <text> [--file <local>] [--append]`
- `file replace --path <path> --old <text> --new <text>`
- `file search --path <path> --regex <pattern>`
- `file locate --glob <pattern> [--path <dir>]`
- `file grep --pattern <regex> [--path <dir>] [--include <glob>]`
- `file glob --pattern <glob> [--path <dir>]`
- `file list --path <dir> [--recursive] [--show-hidden]`
- `file upload --local-path <path> --remote-path <path>`
- `file download --remote-path <path> --local-path <path>`
- `file watch create | list | delete | poll`

### Browser

- `browser info`
- `browser screenshot [--output <path>]`
- `browser action --type <CLICK|TYPE|SCROLL|...> [--x <n>] [--y <n>] [--text <t>]`
- `browser config [--set <json>]`
- `browser page navigate --page-url <url>`
- `browser page click --selector <sel>`
- `browser page fill --selector <sel> --value <text>`
- `browser page screenshot [--output <path>]`
- `browser page html | text | markdown | elements | wait | tabs | cookies`

### Code Execution

- `code exec --language <python|javascript> --code <code> [--file <path>]`
- `code info`
- `jupyter exec --code <code> [--kernel <name>] [--jupyter-session-id <id>]`
- `jupyter info | session list | create | delete | clear`
- `nodejs exec --code <code> [--version <ver>] [--node-session-id <id>]`
- `nodejs info | session list | create | get | update | delete`

### MCP

- `mcp server list`
- `mcp tool list --server-name <name>`
- `mcp tool call --server-name <name> --tool-name <name> [--arguments <json>] [--yes]`

All three commands support AIPAAS mode with `--session-id` and direct mode with `--url [--api-key]`. `--arguments` must be a JSON object; omit it to send an empty object. `mcp tool call` may invoke a side-effecting tool, so it only prints the encoded endpoint and payload by default and sends the request only with explicit `--yes`.

### Other

- `recording start [--fps <n>] | stop | status`
- `skill register --name <n> --file <path> | list | get | delete | clear`
- `info` — Sandbox environment info
- `packages python | nodejs`
- `hook create --name <n> --event <e> --command <c> | list | delete`
- `convert --uri <uri>` — Convert file/URL to markdown

## Sites

| Site        | Alias    | Description              |
| ----------- | -------- | ------------------------ |
| cn-north    | cn, prod | China North (default)    |
| cn-east     | cn-e     | China East               |
| boe         | test     | BOE test environment     |
| i18n-office | i18n     | International office     |
| i18n-prod   | —        | International production |

## Notes

- Data-plane requests require `--session-id` or `--url`; `mcp tool call` dry-run can preview
  the endpoint and payload without either option
- Use `--json` for structured output
- For async shell commands, use `--async` then poll with `shell output --wait`
