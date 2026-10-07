# Dashboard operation through an Argos agent session

Use `argos run` for Argos dashboard and folder administration, Grafana or Metrics-FE imports, and dashboard creation from Metrics SDK declarations. The Argos server provides the `dashboard-operation` skill when the current control plane and project support it.

## Invocation

```bash
# Read-only example
bytedcli --site cn argos run \
  --prompt "Use dashboard-operation to list my CN dashboard folders. Do not modify anything."

# Write example with an explicit preview gate
bytedcli --site cn argos run \
  --prompt "Use dashboard-operation to prepare a dashboard named sample-service Metrics in sample-team folder. Preview the proposed change and do not apply it until I confirm."
```

No local skill path is required. If the server or project does not provide the capability, preserve the agent/server error and explain that dashboard operation is unavailable in that session.

For a manual CN verification, run the read-only example with global `--json`. The check passes when the session succeeds, returns the requested folder result, and reports an empty `files_modified` array. A missing-skill or missing-tool response means that the current session does not provide the capability.

## Session-only boundary

The dashboard skill and its MCP tools execute inside the Argos agent session. They are not direct `bytedcli argos tool <name>` commands and do not belong to the user-callable tool catalog. Consequently, `bytedcli argos tool list` is not an availability check for this capability.

## Safety

- State the target site/region, dashboard, and folder explicitly.
- Keep read-only requests read-only. For writes, request a preview and confirmation when the intended mutation is ambiguous.
- Follow the server-provided skill's validation, V1 migration, identity matching, and dry-run requirements.
- Treat the server-provided `dashboard-operation` skill as the source of truth for its exact tools, scripts, dependencies, and supported chart types.
