---
name: bytedance-coco
description: "Coco AI Code Agent。覆盖旧 Codebase Copilot task/chat/sandbox/env，以及 OpenAPI Next Managed Agent 的 workspace、device、agent、session 创建、消息、多模态、SSE 订阅、中断和清理。当用户提到 Coco、coco、AI 编程任务、Codebase Copilot、Managed Agent、OpenAPI Next、coco task、coco workspace、coco agent、coco session、创建或中断 agent session 时使用。"
---

# Coco AI Code Agent

Coco 目前有两套并行入口，先按用户意图选对模型：

- **Copilot（旧入口）**：一次性或多轮编程任务，使用 `coco task/chat/sandbox/env`。
- **Managed Agent（OpenAPI Next）**：先创建长期 Agent 配置，再按任务创建 Session，使用 `coco workspace/device/agent/session`。

## 前置条件

- 与 Codebase 共用认证：先执行 `bytedcli auth login`。
- 通用调用方式见 `../../invocation.md`。
- 需要稳定机器输出时把全局 `--json` 放在 `coco` 前：`bytedcli --json coco ...`。

## Managed Agent：完整创建闭环

Agent 创建必须显式使用 Workspace 中的 Device。不要猜或自动选择 Device ID。

```bash
# 1. 创建 Workspace；创建后平台会注册系统 Device
bytedcli coco workspace create \
  --name "demo-managed-agent" \
  --slug demo-managed-agent

# 2. 查询 Device，选择 Kind=system，记录其 Device ID 和 Runtimes
bytedcli coco device list --workspace-id <workspace-id>

# 3. 创建长期 Agent 配置
bytedcli coco agent create \
  --workspace-id <workspace-id> \
  --name "demo-agent" \
  --device-id <system-device-id> \
  --runtime traex \
  --instruction "Reply concisely." \
  --permission-mode dont-ask

# 4. 每次任务创建 Session
bytedcli coco session create \
  --workspace-id <workspace-id> \
  --agent-id <agent-id> \
  --idempotency-key demo-session-1

# 5. 发送消息；记录返回的 Event ID
bytedcli coco session send \
  --workspace-id <workspace-id> \
  --session-id <session-id> \
  --message "Reply with READY"

# 6. 从用户消息之后订阅，收到 Idle/Terminated 后退出
bytedcli coco session subscribe \
  --workspace-id <workspace-id> \
  --session-id <session-id> \
  --after-event-id <event-id> \
  --until-idle \
  --timeout-ms 300000
```

`--after-event-id` 是事件游标，不是 Run ID。断线后用最后一个 `last_event_id` 续订：

```bash
bytedcli coco session subscribe \
  --workspace-id <workspace-id> \
  --session-id <session-id> \
  --after-event-id <last-event-id>
```

订阅默认持续运行。Text 模式将 `AgentMessage` 流式写到 stdout，将 thinking、tool、queued/running/idle/terminated 摘要写到 stderr；JSON 模式每行输出完整事件 envelope，并在正常结束时输出带 `last_event_id` 的 success 总结。`SessionStatusIdle.StopReason.RequiresAction.EventIds` 会完整保留，但当前版本没有确认回复命令。

## Managed Agent：多模态消息

快捷模式固定按“文本 → 本地媒体 → URL 媒体 → Workspace FileId”组装。参数可重复：

```bash
bytedcli coco session send \
  --workspace-id <workspace-id> \
  --session-id <session-id> \
  --message "Compare these inputs" \
  --media-file ./sample-image.png \
  --media-file ./sample-report.pdf \
  --media-url https://example.com/sample.png \
  --file-id <workspace-file-id>
```

本地媒体读取后以内联 Base64 发送；已知扩展名会推断 MIME，未知扩展名使用 `application/octet-stream`。

需要保留 block 顺序或完整 wire shape 时，用精确模式，且不要与快捷参数混用：

```bash
bytedcli coco session send \
  --workspace-id <workspace-id> \
  --session-id <session-id> \
  --content-json '[{"Text":{"Text":"Inspect this"}},{"Media":{"SourceKind":"url","Url":"https://example.com/sample.png"}}]'

bytedcli coco session send \
  --workspace-id <workspace-id> \
  --session-id <session-id> \
  --content-file ./content-blocks.json
```

Media 分支规则：

- `base64`：必须有 `Data` 和 `MediaType`，不能有 `Url` / `FileId`。
- `url`：必须有 `Url`，不能有 `Data` / `FileId`。
- `file`：必须有 `FileId`，不能有 `Data` / `Url` / `MediaType`。

## Managed Agent：中断与清理

`interrupt` 直接发送，不需要 `--yes`。删除 Workspace/Agent、归档 Session 必须显式确认：

```bash
bytedcli coco session interrupt \
  --workspace-id <workspace-id> \
  --session-id <session-id> \
  --idempotency-key demo-interrupt-1

bytedcli coco session archive \
  --workspace-id <workspace-id> \
  --session-id <session-id> \
  --yes

bytedcli coco agent delete \
  --workspace-id <workspace-id> \
  --agent-id <agent-id> \
  --yes

bytedcli coco workspace delete \
  --workspace-id <workspace-id> \
  --yes
```

推荐按 Session → Agent → Workspace 的顺序清理。

## Markdown 多行换行（必读）

传多行 instruction 或 message 时使用 shell 的 `$'...'`，不要在普通双引号中写字面量 `\n`：

```bash
# 正确：shell 会传入真实换行
bytedcli coco agent create \
  --workspace-id <workspace-id> \
  --name demo-agent \
  --device-id <device-id> \
  --runtime traex \
  --instruction $'First line\nSecond line'

bytedcli coco session send \
  --workspace-id <workspace-id> \
  --session-id <session-id> \
  --message $'Check these items:\n- item one\n- item two'

# 错误：普通双引号不会把 \n 解释成换行
bytedcli coco session send ... --message "line one\nline two"
```

长文本优先使用 `--instruction-file` 或 `--message-file`。

## Copilot（旧入口）

旧能力保持不变，适合直接发任务，不需要先维护 Workspace/Agent/Session：

```bash
# 发任务并订阅结果
bytedcli coco task send --message "Fix the login bug" --repo-id 12345
bytedcli coco task subscribe --task-id <task-id>

# 多轮继续
bytedcli coco task send --task-id <task-id> --message "Add unit tests"

# Sandbox 模式
bytedcli coco task send \
  --agent-name sandbox \
  --message "Run the tests" \
  --repo-id 12345

# Sandbox / Environment 管理
bytedcli coco sandbox create --environment-id <env-id>
bytedcli coco env list --repo-id 12345

# 模型、Prompt、Chat、飞书授权
bytedcli coco model list
bytedcli coco prompt list --repo-id 12345
bytedcli coco chat --message "Explain this function" --repo-id 12345
bytedcli coco auth check-lark
```

## 命令索引

### Managed Agent / OpenAPI Next

| Resource  | Commands                                          |
| --------- | ------------------------------------------------- |
| Workspace | `workspace create/list/delete`                    |
| Device    | `device list`                                     |
| Agent     | `agent create/list/delete`                        |
| Session   | `session create/send/interrupt/subscribe/archive` |

支持的 permission mode：`default`、`accept-edits`、`plan`、`bypass-permissions`、`dont-ask`。

### Copilot

| Resource       | Commands                                           |
| -------------- | -------------------------------------------------- |
| Task           | `task send/get/list/delete/share/events/subscribe` |
| Chat           | `chat`                                             |
| Model / Prompt | `model list`、`prompt list/get`                    |
| Sandbox        | `sandbox create/delete`                            |
| Environment    | `env create/get/list/update/delete/search`         |
| Auth           | `auth check-lark`                                  |

## Notes

- 当前 Managed Agent 第一版不包含 `session execute`、Run API、Environment、Skill、Memory、Vault。
- 遇到认证或调用问题参考 `../../troubleshooting.md`。
