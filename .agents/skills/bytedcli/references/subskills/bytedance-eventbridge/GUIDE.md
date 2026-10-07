---
name: bytedance-eventbridge
description: "Query EventBridge projects, rules, rule event samples, event sources, event types, Auth Events, and JWT Events through bytedcli eventbridge for these operations. Trigger when users mention EventBridge、事件桥、项目、规则、事件样例、事件源、事件类型、Auth Event、JWT Event, or need to inspect these resources."
---

# EventBridge

Use `bytedcli eventbridge` for EventBridge operations. Query commands call the EventBridge HTTP API through the selected ByteCloud gateway under `/api/v1/eventbridge`.

## Scope

- Control-plane reads cover EventBridge projects, rules, rule event samples, event sources, event types, auth events, and JWT events.
- The CLI must use ByteCloud CLI routing, authentication, error handling, and JSON envelope behavior. Do not invent endpoint paths, credentials, request fields, or response fields.
- Only read-only commands with real API behavior are exposed; deferred write commands remain excluded.

## Commands

- `bytedcli eventbridge project list --page 1 --page-size 20`: List EventBridge projects.

- `bytedcli eventbridge project get --uid <project-uid>`: Get one EventBridge project. Use `--id` only for the deprecated numeric ID.

- `bytedcli eventbridge rule list --project-uid <project-uid>`: List EventBridge rules. Use `--pid` only for the deprecated numeric project ID.

- `bytedcli eventbridge rule get --uid <rule-uid>`: Get one EventBridge rule. Use `--id` only for the deprecated numeric ID.

- `bytedcli eventbridge rule event-sample get --source <source-id> --type <event-type-id>`: Get a sample event for an EventBridge rule.

- `bytedcli eventbridge source list --pid <project-id> --category bytecloud`: List EventBridge event sources.

- `bytedcli eventbridge source get --event-bus-id <bus-id> --event-source-id <source-id>`: Get one EventBridge event source.

- `bytedcli eventbridge type list --event-source <source-id>`: List EventBridge event types.

- `bytedcli eventbridge event auth-event list --start <unix-time> --end <unix-time>`: List EventBridge auth events.

- `bytedcli eventbridge event jwt-event list --access-key <ak>`: List EventBridge JWT events.

## Safety

- Query commands are read-only.
- Never print JWTs, Authorization headers, Gateway tokens, or raw credential material.

## References

- [Command guide](references/eventbridge.md)
- [Invocation](../../invocation.md)
- [Troubleshooting](../../troubleshooting.md)
