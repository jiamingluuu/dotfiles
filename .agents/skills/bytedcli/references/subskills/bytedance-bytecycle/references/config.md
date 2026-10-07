# Config delivery boundary

`config_delivery` covers TCC / WCC / Config Platform change orders and execution pipelines. It is **not** wrapped by `bytedcli bytecycle` today because the field schemas depend on TCC/WCC SDKs and are not safely derivable from swagger alone.

Do not expose config delivery request details to agents. Agents should not use unwrapped fallbacks for this scenario, guess payloads, or ask users to provide copied request bodies for execution.

## Agent guidance

- If the user asks for config delivery operations, explain that `bytedcli bytecycle` does not currently wrap this scenario.
- Prefer an existing dedicated CLI/domain for the underlying platform (for example TCC/WCC/config platform tooling) when available.
- Do not use unwrapped config delivery write operations.
- Do not list or suggest private config delivery request paths in skill output.

## Adding support

If this scenario needs first-class support, add wrapped commands and typed payload builders in code after collecting reviewed product requirements and representative payload fixtures. Keep request paths and payload schema details in implementation or test fixtures, not in agent-facing skill guidance.
