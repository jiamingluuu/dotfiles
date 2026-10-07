# ByteCloud Supabase

这是 bytedcli 根路由中的精简入口；完整安装、认证和安全边界说明见 `skills/bytedance-supabase-companion/SKILL.md`。

Use this route when the user asks about ByteCloud Supabase, `bytedcli supabase`, projects, workspaces, branches, databases, Supabase services, or Supabase MCP.

The Supabase capability has two entry points:

1. Use `bytedcli supabase mcp serve` when an MCP client needs the native Supabase MCP tools.
2. Use `bytedcli mcp` with `list_commands` and `run_command` when the agent is already connected to the shared bytedcli MCP server and needs ordinary Supabase CLI commands.

## Bootstrap

1. Use the built-in Supabase Companion; no plugin installation is required:

```bash
bytedcli supabase --help
```

2. Authenticate through the bytedcli host. Supabase does not maintain a second login command:

```bash
bytedcli auth login
```

3. Read runtime help before selecting a command:

```bash
bytedcli supabase --help
bytedcli supabase <command> --help
```

## Native MCP

Configure an MCP client with:

```json
{
  "mcpServers": {
    "supabase": {
      "command": "bytedcli",
      "args": ["supabase", "mcp", "serve"]
    }
  }
}
```

Do not run `supabase mcp serve` through the shared `bytedcli mcp` `run_command` tool. The native MCP server owns the JSON-RPC stdio stream and must be started directly.

## Shared MCP

When using the shared bytedcli MCP server, discover and run ordinary CLI commands:

```text
list_commands(domain="supabase")
run_command(command="supabase projects list --format json")
```

The shared proxy is a compatibility path. Prefer the native Supabase MCP entry point when native Supabase tool schemas are required.

## Authentication and flags

`--site` is a host global option and must precede `supabase`. Project and workspace identifiers should be passed explicitly using the flags documented by the current runtime help.

The companion injects the host authentication state into the downstream process. Do not copy JWTs into commands, MCP configuration, Skill output, or logs.
