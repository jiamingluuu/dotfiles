---
name: bytedance-oassistant-zeus
description: "Inspect the Ocean Assistant admin console through bytedcli. Use for Ocean Assistant or OAssistant Zeus requests, Omni/Session Viewer URLs, or log_id, user_id, session_id, issue_label, and issue_side in that context."
---

# bytedcli Ocean Assistant Admin

Use this skill for read-only investigation of the Ocean Assistant admin console. The CLI command group is
`bytedcli obric oassistant-zeus`.

## Routing

- Omni Viewer URL, `log_id`, `user_id`, trace steps, tools, or annotations:
  `bytedcli obric oassistant-zeus trace list`.
- A single trace identified by `log_id`: `bytedcli obric oassistant-zeus trace get`.
- Session Viewer URL, `session_id`, app steps, assistant history, metadata, or viewer results:
  `bytedcli obric oassistant-zeus session get`.
- Annotation enums such as `issue_label` or `issue_side`:
  `bytedcli obric oassistant-zeus config list`.

Prefer the original Viewer URL when the user provides one. The CLI validates the host and path,
then extracts the selector without requiring the user to copy query parameters manually.

## Commands

```bash
bytedcli obric oassistant-zeus trace list \
  --url 'https://oassistant-zeus-api.bytedance.net/omni_viewer?log_id=<log_id>'

bytedcli obric oassistant-zeus trace list --log-id <log_id>
bytedcli obric oassistant-zeus trace get --log-id <log_id>
bytedcli obric oassistant-zeus trace get \
  --url 'https://oassistant-zeus-api.bytedance.net/omni_viewer?log_id=<log_id>'
bytedcli obric oassistant-zeus trace list --user-id <user_id> --page 1 --page-size 5

bytedcli obric oassistant-zeus session get \
  --url 'https://oassistant-zeus-api.bytedance.net/session_viewer?session_id=<session_id>'

bytedcli obric oassistant-zeus session get --session-id <session_id>

bytedcli obric oassistant-zeus config list --type issue_label
bytedcli obric oassistant-zeus config list --type issue_side --status active
```

For structured output, put the global option before the domain:

```bash
bytedcli --json obric oassistant-zeus trace list --log-id <log_id>
bytedcli --json obric oassistant-zeus session get --session-id <session_id>
bytedcli --json obric oassistant-zeus config list --type issue_label
```

## Authentication

OAssistant Zeus uses the browser SSO session saved by bytedcli. On an authentication error, refresh it
and retry the same read:

```bash
bytedcli auth login --session
bytedcli obric oassistant-zeus trace list --log-id <log_id>
```

The CLI enters the OAssistant Zeus OIDC flow and establishes the same-origin site cookie automatically.
Do not ask users to provide cookies or tokens.

## Output Contract

- Trace output decodes JSON strings in `sub_task_info`, `extra`, and `annotation_json`.
- Trace JSON reports `page`, `page_size`, `current_count`, and `truncated`; narrow the selector or
  increase `--page-size` when `truncated` is true. The backend exposes no offset or cursor, so
  `page` is always `1`.
- Session output decodes `assistant_history`, nested `assistant_meta` values, and step
  `viewer_result`.
- JSON output retains redacted raw wire records alongside normalized fields for investigation.
- Text output provides identifiers, counts, status, timing, detected tools/actions, and Viewer URLs.

## Boundaries

- All commands in this skill are read-only.
- Annotation save/update operations and arbitrary raw API calls are not supported.
- A `1016` response is an authentication failure; refresh the SSO session.
- A `1015` or `1001` response is a permission failure; do not retry without changed access.

Read [OAssistant Zeus reference](references/oassistant-zeus.md) when selector validation, response decoding,
or authentication troubleshooting is relevant.
