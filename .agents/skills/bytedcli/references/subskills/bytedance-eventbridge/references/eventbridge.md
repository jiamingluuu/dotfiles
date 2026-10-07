# EventBridge command guide

## Current state

The current branch implements read-only EventBridge API queries through the ByteCloud gateway under `/api/v1/eventbridge`.

Gateway routing:

| CLI selection | Gateway base |
| --- | --- |
| `--site cn` | `https://cloud.bytedance.net/api/v1/eventbridge` |
| `--site boe` | `https://cloud-boe.bytedance.net/api/v1/eventbridge` |
| `--vregion va` or `--vregion maliva` | `https://bc-maliva-gw.tiktok-row.net/api/v1/eventbridge` |
| `--vregion sg` | `https://bc-sg-gw.tiktok-row.net/api/v1/eventbridge` |

## Command surface

| Command | Behavior | Read/write |
| --- | --- | --- |
| `bytedcli eventbridge project list --page 1 --page-size 20` | List EventBridge projects visible to the current identity | Read |
| `bytedcli eventbridge project get --uid <project-uid>` | Get one EventBridge project | Read |
| `bytedcli eventbridge rule list --project-uid <project-uid>` | List EventBridge rules | Read |
| `bytedcli eventbridge rule get --uid <rule-uid>` | Get one EventBridge rule | Read |
| `bytedcli eventbridge rule event-sample get --source <source-id> --type <event-type-id>` | Get a sample event | Read |
| `bytedcli eventbridge source list --pid <project-id> --category bytecloud` | List EventBridge event sources | Read |
| `bytedcli eventbridge source get --event-bus-id <bus-id> --event-source-id <source-id>` | Get one EventBridge event source | Read |
| `bytedcli eventbridge type list --event-source <source-id>` | List EventBridge event types | Read |
| `bytedcli eventbridge event auth-event list --start <unix-time> --end <unix-time>` | List EventBridge auth events | Read |
| `bytedcli eventbridge event jwt-event list --access-key <ak>` | List EventBridge JWT events | Read |

## Implementation boundaries

- Control-plane reads use EventBridge APIs through the selected ByteCloud Site/VRegion route.
- Use explicit flags, not positional arguments. Required, one-of and exactly-one constraints must be expressed through `PluginContext.Commands`.
- Query commands return stable public DTOs and render human output through presenters.
- JSON output should be preferred for automation and Agent use.

## Deferred write contract

Event submission commands are intentionally not exposed until the write contract is ready. The following information is required before adding them:

- Gateway host mapping, CloudEvent fields, batching rules and any idempotency key support;
- required flags for event submission selectors;
- dry-run or confirmation behavior for writes;
- representative offline fixtures for success, business errors, auth/permission errors and malformed responses.
