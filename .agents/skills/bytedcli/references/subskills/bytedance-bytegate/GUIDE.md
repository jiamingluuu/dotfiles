---
name: bytedance-bytegate
description: "Operate ByteGate feature gates via bytedcli: discover and follow workspaces, maintain workspace and gatekeeper admins or members, inspect gatekeeper and TCC sync details, create or update gatekeepers, validate and update rules, manage User/Device whitelist and blacklist groups, list and inspect tickets, and approve or reject tickets with explicit confirmation. Use when tasks mention ByteGate, feature gate, gatekeeper, 灰度规则, 黑白名单, or ByteGate workspace/gate/rule/ticket links."
---

# ByteGate (bytedcli)

## Install

bytedcli distributes this skill with its npm package. Install it globally when it is not already installed:

```bash
NPM_CONFIG_REGISTRY=http://bnpm.byted.org npm install -g @bytedance-dev/bytedcli@latest
bytedcli self skill install -s bytedance-bytegate -g
```

For the command flow below, use the globally installed `bytedcli` executable. Use the `npx` fallback only when global installation is impossible.

## When to use

- Discover a ByteGate workspace or gatekeeper.
- List or follow ByteGate workspaces.
- Add or remove a ByteGate workspace admin or member.
- Add or remove a ByteGate gatekeeper admin.
- Read gatekeeper configuration or TCC sync status.
- Create a gatekeeper.
- Delete a gatekeeper by creating and approving a deletion ticket.
- Update gatekeeper admins, metadata, or switch status.
- Validate or update a gatekeeper rule.
- Add, remove, or clear User/Device whitelist or blacklist entries.
- List, inspect, or approve a ByteGate change ticket.
- Reject a ByteGate change ticket with a reason.

Do not use this skill for generic ByteCloud resource management, TCC configuration changes, or non-ByteGate approval workflows.

## Prerequisites

- Authenticate first with `bytedcli auth login`.
- ByteGate uses a CN ByteCloud user JWT. Do not copy browser cookies, raw JWTs, or manually reconstructed request headers.
- Resource-scoped commands require `--workspace-id`; cross-workspace discovery commands (`workspace list` and `workspace follow list`) do not. The CLI uses the workspace ID to scope requests, validate resource ownership, and preserve the workspace in output.
- For machine-readable output, put `--json` before the command domain:

```bash
bytedcli --json bytegate gatekeeper list --workspace-id <workspace-id>
```

## Discovery

```bash
bytedcli bytegate workspace list --keyword demo --page 1 --page-size 20
bytedcli bytegate workspace follow list --page 1 --page-size 20
bytedcli bytegate workspace follow add --workspace-id <workspace-id> --dry-run
bytedcli bytegate gatekeeper list --workspace-id <workspace-id> --gatekeeper-ids <gatekeeper-id>
bytedcli bytegate gatekeeper list --workspace-id <workspace-id> --keyword demo --creator demo-user --status full
bytedcli bytegate gatekeeper get --workspace-id <workspace-id> --gatekeeper-id <gatekeeper-id>
bytedcli bytegate gatekeeper sync-status --workspace-id <workspace-id> --gatekeeper-id <gatekeeper-id>
```

Use `gatekeeper list` to resolve a workspace ID and gatekeeper ID before running detail, rule, or ticket commands. `--keyword` filters by Feature Gate name, `--creator` filters by creator, and `--status` accepts `off`, `gray`, or `full`.

`workspace follow list` returns the current user's followed workspaces. `workspace follow add` requires `--workspace-id` and follows the same dry-run confirmation flow as other ByteGate write commands.

## Update workspace membership

`workspace update` uses the backend's full workspace configuration payload and modifies only the `admin` and `member` arrays. The payload file must contain `admin`, `member`, `description`, `owner`, `node_id`, `lark_group_ids`, `psms`, and `control_plane_regions`; a partial payload can clear unrelated configuration because the endpoint replaces the whole workspace.

```bash
bytedcli bytegate workspace update \
  --workspace-id <workspace-id> \
  --payload-file ./workspace.json \
  --add-admin demo-admin \
  --remove-member demo-member \
  --dry-run
```

Supported membership flags:

- `--add-admin <user>`
- `--remove-admin <user>`
- `--add-member <user>`
- `--remove-member <user>`

Each flag can be repeated or passed as a comma-separated list. Review the complete dry-run request, then rerun the same command with `--yes`.

## Create a gatekeeper

```bash
bytedcli bytegate gatekeeper create \
  --workspace-id <workspace-id> \
  --name demo_gate \
  --description 'demo gatekeeper description' \
  --category Feature \
  --admin demo-user \
  --dry-run
```

The name may contain only digits, lowercase letters, underscores, and dots. The description must contain at least 10 characters. Review the preview, then rerun the exact command with `--yes`.

`--category` accepts one of `Test`, `Feature`, `BugFix`, `KillSwitch`, `Security`, `Configuration`, `Documentation`, `CodeCleanup`, `Refactoring`, `Build`, `Release`, `Dependency`, `Tooling` and defaults to `Feature`.

`--admin` can be repeated or passed as a comma-separated list. If it is omitted, the current operator is used as the sole initial admin.

## Delete a gatekeeper

`gatekeeper delete` uses `--gatekeeper-id`, reads the current gatekeeper to validate the target, and creates a deletion ticket when submitted. Deletion completes only after that ticket is approved.

```bash
bytedcli bytegate gatekeeper delete \
  --workspace-id <workspace-id> \
  --gatekeeper-id <gatekeeper-id> \
  --dry-run
```

After reviewing the preview, rerun the same command with `--yes`, then approve the returned deletion ticket.

## Update a gatekeeper

Gatekeeper switches have three states:

| CLI status | Backend status | Meaning                                 |
| ---------- | -------------- | --------------------------------------- |
| `off`      | `0`            | Disabled                                |
| `gray`     | `1`            | Enabled for the configured scoped rules |
| `full`     | `2`            | Fully enabled                           |

`gatekeeper list` and `gatekeeper get` preserve the backend numeric `status` and also return `statusLabel` in JSON. Their text output shows the same readable labels; an unrecognized backend code is shown as `unknown` rather than guessed.

Use dedicated admin commands for the common add/remove workflow. They use `--gatekeeper-id`, read the current gatekeeper, and submit a full metadata update that preserves unchanged fields:

```bash
bytedcli bytegate gatekeeper admin add \
  --workspace-id <workspace-id> \
  --gatekeeper-id <gatekeeper-id> \
  --user demo-admin \
  --dry-run

bytedcli bytegate gatekeeper admin remove \
  --workspace-id <workspace-id> \
  --gatekeeper-id <gatekeeper-id> \
  --user demo-admin \
  --dry-run
```

`--user` can be repeated or passed as a comma-separated list.

```bash
bytedcli bytegate gatekeeper update \
  --workspace-id <workspace-id> \
  --gatekeeper-id <gatekeeper-id> \
  --status gray \
  --dry-run
```

`gatekeeper update` is the generic entry for optional metadata and switch changes: `--category`, `--description`, and `--status off|gray|full`. It also accepts incremental `--add-admin` / `--remove-admin` flags, but prefer `gatekeeper admin add/remove` for admin-only changes.

Review the preview, then rerun the same command with `--yes`. After submission, verify the result with `bytegate gatekeeper get` or `bytegate gatekeeper sync-status`, both with `--workspace-id`.

## Validate and update rules

`rule update` accepts a full backend rule payload through `--payload-file`. The file must be a JSON object and preserves fields not covered by list flags.

```bash
bytedcli bytegate gatekeeper rule validate \
  --workspace-id <workspace-id> \
  --gatekeeper-id <gatekeeper-id> \
  --payload-file ./rule.json

bytedcli bytegate gatekeeper rule update \
  --workspace-id <workspace-id> \
  --gatekeeper-id <gatekeeper-id> \
  --payload-file ./rule.json \
  --dry-run
```

`rule update` always calls backend validation before preview or submission. `--dry-run` performs validation and prints the final request but does not create a ticket. Submit only after reviewing that preview by rerunning the same command with `--yes`.

### List groups

ByteGate rules separate User and Device groups inside `white_list` and `black_list`:

```json
{
  "white_list": [
    { "list_type": "User", "list_values": [{ "type": "ID", "string_value": "demo-user-id" }] },
    { "list_type": "Device", "list_values": [{ "type": "ID", "string_value": "demo-device-id" }] }
  ],
  "black_list": [
    { "list_type": "User", "list_values": [{ "type": "ID", "string_value": "demo-user-id" }] }
  ]
}
```

Use type-specific flags so the same ID cannot be written into the wrong group:

- Add: `--whitelist-user`, `--whitelist-device`, `--blacklist-user`, `--blacklist-device`
- Remove exact ID: `--remove-whitelist-user`, `--remove-whitelist-device`, `--remove-blacklist-user`, `--remove-blacklist-device`
- Clear one group: `--whitelist-user-clear`, `--whitelist-device-clear`, `--blacklist-user-clear`, `--blacklist-device-clear`

Each ID option can be repeated or passed as a comma-separated list. For example:

```bash
bytedcli bytegate gatekeeper rule update \
  --workspace-id <workspace-id> \
  --gatekeeper-id <gatekeeper-id> \
  --payload-file ./rule.json \
  --whitelist-user demo-user-a,demo-user-b \
  --remove-blacklist-device demo-device-a \
  --dry-run
```

Clear flags remove only their named type-specific group. A clear flag cannot be combined with add or remove flags for the same list and type.

## Tickets and approval

```bash
bytedcli bytegate gatekeeper ticket list --workspace-id <workspace-id>
bytedcli bytegate gatekeeper ticket get --workspace-id <workspace-id> --ticket-id <ticket-id>

bytedcli bytegate gatekeeper ticket approve \
  --workspace-id <workspace-id> \
  --ticket-id <ticket-id> \
  --dry-run

bytedcli bytegate gatekeeper ticket reject \
  --workspace-id <workspace-id> \
  --ticket-id <ticket-id> \
  --comment 'wrong target' \
  --dry-run
```

Approval and rejection are intentionally separate from rule update. `rule update --yes` creates a ticket but does not approve or reject it. Review the ticket, then run the exact approval or rejection command with `--yes`.

## Safety rules

- Never run a ByteGate write command with `--yes` unless the user explicitly requested submission and the target, payload, or ticket ID has been confirmed.
- Do not auto-retry a failed write. Read back the workspace, gatekeeper, or ticket state and decide the next step from the actual response.
- Do not invent raw ByteGate HTTP calls, reuse browser curl examples, or store credentials in scripts.
- If authentication fails, run `bytedcli auth login`, then retry the original read or preview command.
- If command parameters are unclear, run `bytedcli bytegate --help` or the relevant nested `--help`; do not guess flag names.

## Troubleshooting

See `../../invocation.md` for global bytedcli invocation, JSON, proxy, and skill installation conventions. See `../../troubleshooting.md` for common authentication, command, and network diagnostics.
