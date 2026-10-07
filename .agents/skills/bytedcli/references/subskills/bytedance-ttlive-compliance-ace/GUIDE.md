---
name: bytedance-ttlive-compliance-ace
description: "Operate TikTok LIVE DECC/DES compliance data tickets through bytedcli: list owned tickets, inspect a ticket by session ID, read the embedded Agent chat history, and safely continue that Agent conversation. Make sure to use this skill whenever the user mentions TikTok LIVE DECC 合规工单、DECC/DES session_id、我的 TTLIVE 合规任务、Agent 对话历史，或继续跟该工单 Agent 对话. This skill is only for TikTok LIVE compliance workflows. Chat send is dry-run by default; add --yes only when the user explicitly confirms the exact target session and message."
---

# bytedcli TikTok LIVE Compliance Data Tickets

Use `bytedcli ttlive-compliance-ace` only for TikTok LIVE DECC/DES compliance tickets and their embedded Agent conversations. Prefer these commands over opening the ticket web UI or constructing HTTP/WebSocket requests by hand.

## Scope

- `ttlive-compliance-ace task list`: list TikTok LIVE DECC/DES compliance tickets owned by the current authenticated user.
- `ttlive-compliance-ace task get --session-id <id>`: inspect one owned TikTok LIVE DECC/DES ticket and its regional ticket state.
- `ttlive-compliance-ace chat history --session-id <id>`: replay the embedded Agent session for an owned ticket without sending anything.
- `ttlive-compliance-ace chat send --session-id <id> --message <text>`: preview a reply; add `--yes` only for an explicitly approved live send.
- Supported ticket entity types are currently limited to `MQ-Storage` and `RPC-callee`; `MQ-Event` is not supported yet.

Do not use this skill for non-TikTok-LIVE compliance work. Do not route this work to AIME, Coco, TMates, or XPA; those are different Agent platforms.

## Prerequisites

- Follow the shared invocation guidance in [`../../invocation.md`](../../invocation.md).
- The command resolves the current owner through the active bytedcli identity. If identity lookup fails, run `bytedcli auth login` and retry.
- `--json` is a global option and must appear before `ttlive-compliance-ace`, for example `bytedcli --json ttlive-compliance-ace task list`.

## Read my tasks

```bash
bytedcli --json ttlive-compliance-ace task list
bytedcli --json ttlive-compliance-ace task list --page 2 --page-size 20
bytedcli --json ttlive-compliance-ace task get --session-id demo-session-123
```

`task list` applies an exact owner check even though the upstream owner filter is fuzzy, and only returns TikTok LIVE DECC/DES compliance tickets. `task get` also rejects a session that is out of scope or is not owned by the current user.

When reporting results, include the full `session_id`, task/entity name, task status, and each ticket's region, status, and URL. Do not shorten identifiers.

## Read Agent history

```bash
bytedcli --json ttlive-compliance-ace chat history --session-id demo-session-123
bytedcli --json ttlive-compliance-ace chat history --session-id demo-session-123 --timeout-ms 15000
```

History is read-only. Summarize the user and assistant turns in order. Avoid dumping raw ToolOutput, internal tool payloads, or repetitive Status frames unless the user explicitly asks for raw JSON.

`--timeout-ms` is in milliseconds. A busy session may need several minutes.

The Agent Gateway has no dedicated end-of-replay frame and may emit `enable_input: true` after each historical turn. Bytedcli therefore uses 3000 ms as both the default and safety floor for the quiet window after the latest ready frame. If replay frames arrive in slower chunks, increase `--history-settle-ms`; the same option applies to a live `chat send` before its message is transmitted.

## Continue the conversation safely

1. Read `task get` and `chat history` first so the target session and current context are clear.
2. Preview the exact message without `--yes`:

```bash
bytedcli --json ttlive-compliance-ace chat send \
  --session-id demo-session-123 \
  --message "Please re-check the evidence and give me the next action."
```

3. Verify that the preview contains the intended session ID and exact message. Add `--yes` only when the user explicitly asked to send that message to that session:

```bash
bytedcli --json ttlive-compliance-ace chat send \
  --session-id demo-session-123 \
  --message "Please re-check the evidence and give me the next action." \
  --yes
```

For long or multiline input, use `--message-file <path>` instead of shell-escaping a large message.

The no-`--yes` path performs no network request, so it does not verify ownership. The live path verifies the ticket scope and ownership before connecting, then returns the Agent reply plus the trace URL when available.

If a live send times out or has an uncertain result, run `chat history` before retrying. Do not blindly resend: the Agent may have accepted the first message even if the client did not receive the final status.

## Output guidance

- Task list/detail: report owner-scoped TikTok LIVE DECC/DES records and ticket state; distinguish task status from per-region ticket status.
- History: summarize meaningful User and ChatModel turns; use the structured JSON only when raw events are needed.
- Send preview: clearly label `dry_run: true` and state that nothing was sent.
- Live send: report the assistant response and trace URL. Never claim delivery if the command timed out or returned an error.

## References

- [`../../invocation.md`](../../invocation.md) — shared bytedcli invocation and site conventions
- [`../../troubleshooting.md`](../../troubleshooting.md) — auth, network, and structured-error troubleshooting
