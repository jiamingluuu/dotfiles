# ByteCloud PostgreSQL

这是 bytedcli 根路由中的精简入口；完整 PostgreSQL 命令契约以 `bytedcli postgresql --help` 为准。

Use this route when the user asks about ByteCloud PostgreSQL, `bytedcli postgresql`, projects, PostgreSQL workspaces, branches, computes, databases, roles, operations, BytePG connections, or PostgreSQL MCP.

## Bootstrap

1. Use the built-in PostgreSQL Companion:

```bash
bytedcli postgresql --help
bytedcli postgresql --version
```

2. Authenticate through the bytedcli host. PostgreSQL reuses the host ByteCloud Auth session:

```bash
bytedcli auth login
```

3. Read runtime help before selecting a command:

```bash
bytedcli postgresql --help
bytedcli postgresql <command> --help
```

## Native MCP

When an MCP client needs PostgreSQL tools, start the native server directly:

```json
{
  "mcpServers": {
    "postgresql": {
      "command": "bytedcli",
      "args": ["postgresql", "mcp", "serve"]
    }
  }
}
```

Do not run `postgresql mcp serve` through the shared `bytedcli mcp` `run_command` tool. The native MCP server owns the JSON-RPC stdio stream and must be started directly.

The native MCP server exposes PostgreSQL control-plane resource tools. BytePG connection strings and SQL execution remain CLI commands and are not exposed as MCP tools.

## Shared MCP

When using the shared bytedcli MCP server, discover and run ordinary PostgreSQL commands:

```text
list_commands(domain="postgresql")
run_command(command="postgresql projects list --output json")
```

The Companion injects the host authentication state into the downstream process. Do not copy JWTs into commands, MCP configuration, Skill output, or logs.
