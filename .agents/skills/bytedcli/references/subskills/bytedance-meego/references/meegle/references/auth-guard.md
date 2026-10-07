# Authentication Guard

The official meegle profile is the single credential source for all MCP-backed bytedcli Meego commands.

Before running an official proxy command, inspect the official CLI state:

```bash
meegle auth status --format json
```

If it is unauthenticated, use the unified bytedcli entry point:

```bash
bytedcli meego login
```

That command checks or completes the tenant-scoped official profile. The same profile can be used directly with `meegle ... --profile bytedcli`. Do not use `bytedcli meego auth login`; the `auth` command group is intentionally not exposed through the proxy.
