# Ocean Assistant Admin Reference

Ocean Assistant is an admin console whose CLI command group is
`bytedcli obric oassistant-zeus`. Omni Viewer and Session Viewer are read-only investigation pages
within that console.

## Command Matrix

| User input              | Command                                      | Selector / default       |
| ----------------------- | -------------------------------------------- | ------------------------ |
| Omni Viewer URL         | `bytedcli obric oassistant-zeus trace list`  | `--url`                  |
| Trace log ID            | `bytedcli obric oassistant-zeus trace list`  | `--log-id`               |
| Single trace by log ID  | `bytedcli obric oassistant-zeus trace get`   | `--log-id` or `--url`    |
| Ocean Assistant user ID | `bytedcli obric oassistant-zeus trace list`  | `--user-id`              |
| Session Viewer URL      | `bytedcli obric oassistant-zeus session get` | `--url`                  |
| Session ID              | `bytedcli obric oassistant-zeus session get` | `--session-id`           |
| Annotation enum         | `bytedcli obric oassistant-zeus config list` | `--type` (`issue_label`) |

Explicit `--log-id`, `--user-id`, and `--session-id` values take precedence over values extracted
from a supplied URL.

## Request Semantics

### Trace

`trace list` calls the OAssistant Zeus trace endpoint with:

```json
{
  "log_id": "<log_id-or-empty>",
  "user_id": "<user_id-or-empty>",
  "limit": 20
}
```

`trace get --log-id <log_id>` or `trace get --url <omni-viewer-url>` uses the same endpoint with
the maximum bounded page size and requires exactly one returned trace. A missing trace returns
`OASSISTANT_ZEUS_TRACE_NOT_FOUND`; multiple records return `OASSISTANT_ZEUS_TRACE_AMBIGUOUS`.
Use `trace list` for `user_id` selectors.

`--page-size` accepts integers from 1 through 100. The command defaults to 20 rows and maps that
value to the backend's `limit` field. The backend does not expose an offset or cursor, so JSON
reports `page: 1`, `page_size`, `current_count`, and `truncated`.

### Session

`session get` calls the Session Viewer debug endpoint with `session_id` and
`use_pseudo_session_id=1`. The response may encode `assistant_history`, `assistant_meta`, and
individual step `viewer_result` values as JSON strings; the CLI decodes them while retaining raw
representations with credential fields and signed URL queries redacted.

### Config

`config list` sends `config_type` and a status code. The CLI exposes `active|inactive` and maps them
to backend codes `1|0`; defaults are `issue_label` and `active`.

## Authentication Recovery

Run:

```bash
bytedcli auth login --session
```

Then retry the original command. The CLI reuses the saved ByteDance browser session and follows the
OAssistant Zeus OIDC redirect chain. It never accepts a cookie or token flag.

## Error Guide

| Error code                        | Meaning                                         | Action                                    |
| --------------------------------- | ----------------------------------------------- | ----------------------------------------- |
| `CLI_ARGS_INVALID`                | Missing selector or invalid command option      | Use the command hint and `--help`         |
| `OASSISTANT_ZEUS_INPUT_ERROR`     | Invalid Viewer URL or domain-level input        | Use the command hint and `--help`         |
| `OASSISTANT_ZEUS_AUTH_ERROR`      | Missing or expired browser SSO session          | Run `bytedcli auth login --session`       |
| `OASSISTANT_ZEUS_FORBIDDEN`       | Account lacks Viewer access                     | Request access; do not retry unchanged    |
| `OASSISTANT_ZEUS_PARSE_ERROR`     | Response is HTML or has an unexpected schema    | Refresh auth, then inspect HTTP trace     |
| `OASSISTANT_ZEUS_API_ERROR`       | Platform returned another explicit failure code | Inspect the returned message and endpoint |
| `OASSISTANT_ZEUS_TRACE_NOT_FOUND` | No trace matched the selector                   | Verify the log ID and access              |
| `OASSISTANT_ZEUS_TRACE_AMBIGUOUS` | Selector matched multiple traces                | Use `trace list` or narrow the selector   |

For request diagnostics:

```bash
bytedcli --http-debug obric oassistant-zeus session get --session-id <session_id>
bytedcli --http-trace-file /tmp/oassistantZeus.http.log \
  --http-body-limit 4096 \
  obric oassistant-zeus trace list --log-id <log_id>
```

HTTP traces can contain sensitive response data. Keep trace files local and remove them after the
investigation.
