---
name: bytedance-quantum
description: "Use Quantum platform capabilities including native bytedcli Link Skills commands and Link Skills MCP. Invoke for Quantum/Polestar link-debug tasks, real-time data, or event details."
---

# bytedcli Quantum

Use Quantum platform capabilities when the user needs to debug Polestar link or event data through an AI agent. Prefer the native `bytedcli quantum link ...` workflow command when shell execution is available. Link Skills MCP remains available as a Quantum-backed sub-capability packaged as `link-skills-mcp`; it exposes the lower-level three-step workflow over stdio.

## Platform And Ownership

- Polestar project entry: `https://quantum-sg.bytedance.net/`
- Polestar task-mgmt API base used by the MCP server: `https://quantum-sg.bytedance.net/api/polestar/task-mgmt/tasks/start`
- Quantum-backed Link Skills MCP source repository: maintained by the Quantum Link Skills platform owner; use the approved internal repository recorded in the MR context when reviewer evidence is needed.
- Quantum-backed Link Skills MCP package launch identifier: `link-skills-mcp==0.1.0`
- Quantum MCP sub-capability owner team: Quantum Link Skills platform owner
- bytedcli Quantum skill maintainer: bytedcli maintainers

## When To Use

- The user mentions Quantum, Polestar link-debug, Link Skills, `link-skills-mcp`, or the `link-skills` MCP server.
- The user asks to debug Polestar link/event data for a UID and time window.
- The user needs final event details for a UID and time window.

Do not use this skill for generic Codebase links, ByteLink/liveim diagnostics, Warlock captures, or unrelated URL parsing.

## Native CLI Workflow

Set `POLESTAR_BEARER_TOKEN` in the shell environment, or pass `--bearer-token` for one-off execution. The native Link Skills commands follow the Link Skills MCP route and send Quantum requests through Polestar PPE (`ppe_polestar`). Do not paste real bearer tokens into chat, committed files, examples, or logs.

Run the native bytedcli workflow with one command:

```bash
export POLESTAR_BEARER_TOKEN=<bearer-token>

bytedcli quantum link task start \
  --uid 123456789 \
  --start 2026-09-15T00:00:00Z \
  --end 2026-09-15T01:00:00Z \
  --limit 100
```

The command starts the Link debug task, queries realtime data with the returned `realtime_task_id`, fetches event detail for returned `data_id` values up to `--limit` (default `100`), and returns the final event array. Use `bytedcli --json quantum ...` when the caller needs machine-readable output. The JSON response returns stable fields such as `realtime_task_id`, `data_ids`, `events`, `next_event`, and `truncated`; text mode prints the endpoint, identifiers, counts, pagination state, and a compact event preview. If `truncated` is `true`, rerun with a narrower time window or a larger `--limit`.

## Link Skills MCP Setup

The recommended MCP client configuration launches the published package with `uvx`:

```json
{
  "name": "link-skills",
  "mcpServers": {
    "link-skills": {
      "command": "uvx",
      "args": ["--from", "link-skills-mcp==0.1.0", "link-skills-mcp"]
    }
  }
}
```

`POLESTAR_BEARER_TOKEN` is required by the MCP server, but it must be provided by the host environment or the MCP client's secret configuration. Do not place real bearer tokens in committed manifests, prompts, chat messages, or logs.

For local development against a checkout, use a path-based `uvx` launch:

```json
{
  "mcpServers": {
    "link-skills": {
      "command": "uvx",
      "args": ["--from", "/absolute/path/to/link-skills", "link-skills-mcp"],
      "env": { "POLESTAR_BEARER_TOKEN": "your_bearer_token_here" }
    }
  }
}
```

## Link Skills Tool Workflow

For bytedcli, call only the native workflow command:

1. `bytedcli quantum link task start`

For MCP-only hosts, call the MCP tools in this order because each step depends on identifiers from the previous response:

1. `start_task`
2. `get_rt_data`
3. `get_event`

### `start_task`

Creates a link-debug task for a UID and time window.

Required inputs:

- `uid`
- `start_time`
- `end_time`

Defaults:

- `space_id`: `30`
- `task_type`: `uid_debug`

The bytedcli command uses the returned `realtime_task_id` internally. For MCP-only hosts, use the returned `realtime_task_id` for `get_rt_data`.

### `get_rt_data`

Lists real-time event rows for a task.

Required inputs:

- `realtime_task_id`
- `uid`
- `start_time`
- `end_time`

Optional inputs:

- `space_id`
- `last_event`
- `filter`
- `filter_type`
- `tz`

The bytedcli command follows realtime-data pagination internally and fetches details for returned `data_id` values up to the configured `--limit`. For MCP-only hosts, use a returned `data_id` for `get_event`. If the response is paginated, pass the returned pagination cursor as `last_event` for the next MCP page.

### `get_event`

Fetches full event detail for a single event.

Required input:

- `data_id`

Default:

- `task_type`: `uid_debug`

## Agent Guidance

- Ask for the UID and the time window before starting the workflow if either is missing.
- Prefer the native `bytedcli quantum link task start` workflow command when the agent can run shell commands; use MCP when the host only exposes MCP tool calling.
- Check `truncated` and `next_event` in JSON output before claiming the result set is complete; when truncated, narrow the time window or raise `--limit`.
- Keep `POLESTAR_BEARER_TOKEN` hidden. If authentication fails or the variable is missing, ask the user to configure the token in the shell environment or MCP host secret environment.
- Treat returned `realtime_task_id` and `data_id` values as workflow state and reuse them exactly.
- Prefer concise summaries for chat responses, but keep raw JSON available when the user asks for exact event fields.
- If an API call returns an authorization error, retry only through bytedcli's or the MCP server's built-in refresh behavior; do not ask the user to paste tokens into chat.

## References

- `../../invocation.md`
- `../../troubleshooting.md`
