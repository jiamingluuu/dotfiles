---
name: bytedance-mira
description: "Chat with Mira through bytedcli: sign in with Feishu, send a prompt, continue an existing conversation, list sessions, and read message history. Use when the user asks to talk to Mira or inspect a Mira conversation."
---

# Mira

Use `bytedcli mira` to talk to Mira and read your conversations. Run `bytedcli mira --help` for the command overview.

## Login

Run `bytedcli mira login`. It reuses a valid saved Mira or Feishu login; otherwise, scan and approve the Feishu QR code. The CLI saves the Mira session for subsequent commands. Fresh QR login must run in a terminal before using Mira through MCP; MCP login can reuse saved authentication and returns terminal-login instructions when a scan is needed.

`--no-terminal-qr` saves a QR image instead of printing a terminal QR code. `--qr-image [path]` chooses an image path, with a temporary path when omitted. JSON and non-TTY login automatically use a QR image. JSON login emits a `qr_image_ready` event containing `qr_image` on stderr, followed by the final success or error result on stdout.

## Chat and history

```bash
bytedcli mira login

# Send immediately; a new conversation uses Auto and quick mode
bytedcli mira chat --message "Explain how a hash table works"

# Continue a conversation using the session ID from the previous result
bytedcli mira chat --session-id demo-session --message "Show a small example"

# Wait for the complete answer before printing it
bytedcli mira chat --message "Explain caching" --no-stream --timeout-ms 300000

# Machine-readable result
bytedcli --json mira chat --message "Summarize this sample error"

# Browse conversations and read their user/assistant messages
bytedcli mira session list --page 1 --page-size 20
bytedcli --json mira session get --id demo-session
```

`chat` sends immediately and does not require `--yes`. Text mode streams the answer to stdout and prints the session ID and browser URL to stderr. `--no-stream` prints the completed answer once. JSON mode emits one result with `sessionId`, `messageId` when available, `answer`, `model`, and `url`.

New sessions use Auto. Continuation uses the model saved when the session was created and keeps its project; later model choices in the browser do not change the CLI's selection. `model` reports that stored setting, so Auto is reported as `auto`. Chat uses quick mode and Mira's default tools. Model selection, attachments, and project creation are not exposed by these commands.

The default chat timeout is 300000 milliseconds. A timeout or interrupted response returns an error with the session ID, message ID when available, and partial answer in its details. Read `session get` before deciding whether to send again: Mira may still be generating the answer. The CLI does not resend an interrupted prompt.

`session list` returns `page`, `pageSize`, `total`, and `hasMore`. `session get` returns the complete available message history in conversation order, excluding reasoning messages; it has no pagination flags.

## Markdown 多行换行（必读）

Use `$'...'` for actual newlines in Bash or Zsh. Double-quoted `"...\n..."` passes literal backslash characters.

```bash
# Correct: two lines
bytedcli mira chat --message $'Explain this sample error:\nConnection timed out'

# Incorrect: a literal \n, not a newline
bytedcli mira chat --message "Explain this sample error:\nConnection timed out"
```

## Agent guidance

- On `MIRA_AUTH_REQUIRED`, run `bytedcli mira login` in a terminal and complete the Feishu login before retrying CLI or MCP commands.
- Keep the returned session ID when continuing; omitting `--session-id` creates a new conversation.
- Treat chat errors as errors even when their details contain a partial answer.
- Use the returned `url` when the user wants to inspect the conversation in a browser.
