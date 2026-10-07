---
name: bytedance-vertex
description: "Use Vertex registry-driven bytedcli commands. Invoke for Vertex platform operation logs and other registry-discovered Vertex actions."
---

# bytedcli Vertex

## How to invoke bytedcli

Use an installed `bytedcli` by default:

```bash
bytedcli <command> [options]
```

Fallback only when the environment cannot install the CLI globally:

```bash
NPM_CONFIG_REGISTRY=http://bnpm.byted.org npx -y @bytedance-dev/bytedcli@latest <command> [options]
```

## When to use

- Vertex platform actions exposed by the CLI registry.
- Operation log queries and any other Vertex module/action shown by `vertex --help`.
- User provides a Vertex console context and needs a browser-free CLI equivalent.

## Command discovery

Vertex is registry-driven. Do not assume a static subcommand list.

```bash
bytedcli vertex --help
bytedcli vertex <module> <action> --help
```

`vertex --help` loads the current registry and lists available module/action pairs. `vertex <module> <action> --help` shows that action's flags, required markers, types, choices, defaults, and descriptions.

## Execution

Dynamic actions use:

```bash
bytedcli vertex <module> <action> --flag value
```

Example:

```bash
bytedcli --site cn vertex operation-log list \
  --operation-type read \
  --start-time 1787728920000 \
  --end-time 1787815320000
```

Use global `--json` before `vertex` when stable machine-readable output is needed:

```bash
bytedcli --json --site cn vertex operation-log list --operation-type read --start-time 1787728920000 --end-time 1787815320000
```

## Registry and cache

- Registry is fetched from Vertex and cached locally by `site + origin`.
- Use `--refresh` to bypass cache and force a fresh registry fetch:

```bash
bytedcli vertex --refresh --help
bytedcli vertex operation-log list --refresh --help
```

- For local or PPE debugging, override the registry/action origin with `BYTEDCLI_VERTEX_BASE_URL`:

```bash
BYTEDCLI_VERTEX_BASE_URL=http://127.0.0.1:3000 bytedcli vertex --refresh --help
```

## Agent guidance

- Always inspect `vertex --help` or action-level `--help` before inventing parameters.
- Prefer action-level help for required fields, types, choices, defaults, and descriptions.
- Keep `--json` as a global option before `vertex`; do not pass it as a business flag.
- If a user asks to refresh command metadata, add `--refresh`.
- If registry loading fails, report the registry failure rather than guessing static commands.
- Do not call deprecated static forms such as `vertex schema`, `vertex module`, `vertex capability`, or `vertex invoke`.

## References

- `../../invocation.md`
- `../../troubleshooting.md`
